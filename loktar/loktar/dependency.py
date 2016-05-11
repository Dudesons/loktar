import copy
from fabric.api import lcd
from fabric.api import local
from itertools import product
import json
import networkx as nx
import numpy as np
import os
import re
import time
import urllib

from loktar.decorators import retry
from loktar.environment import GITHUB_INFO
from loktar.environment import GITHUB_TOKEN
from loktar.exceptions import CIJobFail
from loktar.exceptions import FailDrawDepGraph
from loktar.log import Log
from loktar.parser import parse_statuses
from loktar.scm import fetch_github_file
from loktar.scm import Github

logger = Log()


def docker_deps(basepath):
    """Get docker image dependencies.

    Args:
        basepath (str): Path to the package

    Returns:
        set: Dependencies names.
    """
    docker_file = os.path.join(basepath, 'Dockerfile')
    if os.path.exists(docker_file):
        with open(docker_file, 'r') as f:
            dockerfile = f.read()
        re_dockerfile = re.compile('FROM (.+)')
        docker_from = re_dockerfile.findall(dockerfile)
        assert len(docker_from) <= 1
        if docker_from:
            docker_from = docker_from[0]
            docker_image_name_tag = docker_from.rsplit('/', 1)[-1]
            docker_image_name = docker_image_name_tag.split(':', 1)[0]
            return {docker_image_name}
        else:
            return set()
    else:
        return set()


def python_deps(basepath):
    """Get python dependencies from requirements.txt and test_requirements.txt.

    Args:
        basepath (str): Path to the package

    Returns:
        set: Requirements names.
    """
    requirements = []

    requirements_file = os.path.join(basepath, 'requirements.txt')
    test_requirements_file = os.path.join(basepath, 'test_requirements.txt')
    app_requirements_file = os.path.join(basepath, 'app', 'requirements.txt')
    app_test_requirements_file = os.path.join(basepath, 'app', 'test_requirements.txt')

    for req_file in (requirements_file, test_requirements_file, app_requirements_file, app_test_requirements_file):
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                requirements.extend(f.readlines())

    requirements_names = set(filter(None, map(lambda x: re.split('==|>=|>|<=|<', x)[0], requirements)))
    return requirements_names


def deps(basepath):
    """Gather all dependencies for this package

    Args:
        basepath (str): Path to the package

    Returns:
        set: Dependencies names.
    """
    return python_deps(basepath) | docker_deps(basepath)


def get_excluded_deps(packages, dict_message_files, modified_packages):
    """Compute which package's dependencies should be ignored based on commit messages.

    This does not take into account modified dependencies of an package whose dependencies are excluded.
    We only need to know if an packages non-modified dependencies should be ignored or not, the rest is
    done in ``dependency_graph_from_modified_packages``.

    Args:
        packages (dict): all packages. Keys are packages names, values are directly taken from config.json
        dict_message_files (dict of str: list): Comments of the commits linked to the pull request are keys,
            modified files are values. If empty, the returned set is empty.
        modified_packages (set of str): names of the packages that were modified

    Returns:
        set of str: items are packages names whose dependencies must not be added to the dependency graph

    Examples:
        >>> get_excluded_deps({'package': {'exclude_dependencies_only_on_keywords': ['CLN', 'BLD']}},
        ... {'CLN/BLD: Cleaned some files. I do not care about dependencies': 'package/modified.py'},
        ... {'package'})
        {'package'}

        >>> get_excluded_deps({'package': {'exclude_dependencies_only_on_keywords': ['CLN', 'BLD']}},
        ... {'BUG: Fixed a serious bug! This should rebuild dependencies': 'package/modified.py'},
        ... {})
        {'package'}
    """

    if not dict_message_files:
        return set()

    # Packages whose dependencies should be ignored
    # Initialize to all of them and delete them one by one if some keywords are not exclusion keywords.
    exclude_dep = set(copy.deepcopy(modified_packages))

    for commit_message, modified_files in dict_message_files.items():
        for path in modified_files:
            package_name = package_from_path(path, packages)
            if package_name is None:
                continue
            # If we have set an exclude condition and this condition is matched
            elif 'exclude_dependencies_only_on_keywords' in packages[package_name]:
                keywords = {key.strip() for key in commit_message.split(':')[0].split('/')}
                keywords_exclude = set(packages[package_name]['exclude_dependencies_only_on_keywords'])
                # If there is a keyword that is not excluded
                if keywords - keywords_exclude:
                    exclude_dep -= {package_name}
            else:
                exclude_dep -= {package_name}
    return exclude_dep


def package_from_path(path, packages):
    """Get the name of an package from a path.

    Args:
        path: relative path starting with the potential package name (Example: serializers/http/)
        packages (dict): all packages. Keys are packages names, values are directly taken from config.json

    Returns:
        the package name or None if the path is not inside an package
    """
    for package_name, config in packages.iteritems():
        if 'pkg_dir' in config and path.startswith(os.path.join(config['pkg_dir'], package_name)):
            return package_name
        elif path.startswith(package_name):
            return package_name


def package_path(package):
    """Get the path of a package

    Args:
        package (dict): Package configuration

    Returns:
        str: The package path relative to the repository root.
    """
    if 'pkg_dir' in package:
        return os.path.join(package['pkg_dir'], package['pkg_name'])
    else:
        return package['pkg_name']


def graph_edges(packages_requirements, modified_packages, exclude_dep_from_packages):
        """Recursively find graph edges

        Args:
            packages_requirements (dict of list): Dictionary of package_name: requirements
            modified_packages (set): Package names that are considered modified
            exclude_dep_from_packages (set): Do not analyze the dependencies for the packages in this list

        Returns:
            list of tuple: Graph edges between packages.
        """
        if not modified_packages:
            return []

        edges_list = []
        next_modified_packages = set()
        packages_done = set()

        for package_name in packages_requirements:
            requirements = packages_requirements[package_name]
            # but whose dependencies are not excluded (iff this was not a modified package)
            modified_requirements = (requirements & modified_packages - exclude_dep_from_packages
                                     if package_name not in modified_packages
                                     else requirements & modified_packages)

            if modified_requirements:
                # Add the edges from the modified requirements towards this package
                edges = map(lambda x: (x, package_name), modified_requirements)
                edges_list.extend(edges)
                packages_done |= modified_requirements
                next_modified_packages |= {package_name}

        for package_name in packages_done:
            packages_requirements.pop(package_name, None)

        edges_list.extend(graph_edges(packages_requirements, next_modified_packages, exclude_dep_from_packages))
        return edges_list


def dependency_graph_from_modified_packages(repo_path,
                                            packages,
                                            modified_packages,
                                            exclude_dep_from_packages=None):
    """Parse requirement with a pattern for generating a dependencies graph

    Args:
        repo_path (str): this is the path where the repo to parse is
        packages (dict): all packages. Keys are packages names, values are directly taken from config.json
        modified_packages (set): This is a set a modified package
        exclude_dep_from_packages (Optional[set]): Do not analyze the dependencies for the packages in this list.
            Defaults to None.

    Returns:
        networkx.classes.digraph.DiGraph: The dependency graph.
    """
    if exclude_dep_from_packages is None:
        exclude_dep_from_packages = set()

    modified_packages = set(modified_packages)
    packages_requirements = {}

    # Go through all the packages
    for package_name in packages:
        requirements = get_package_requirements(package_name, packages, repo_path)
        if requirements:
            packages_requirements[package_name] = requirements

    edges_list = graph_edges(packages_requirements, modified_packages, exclude_dep_from_packages)

    directed_graph = nx.DiGraph(edges_list)
    directed_graph.add_nodes_from(modified_packages)

    return directed_graph


def get_package_requirements(package_name, packages, repo_path, restrict_requirements_types=None):
    """Get the requirements of a package

    Args:
        package_name (str): Name of the package to consider
        packages (dict): All packages. Keys are packages names, values are directly taken from config.json
        repo_path (str): This is the path where the repo to parse is
        restrict_requirements_types (Optional[list or None]): Restrict the requirements type to some type.
            Available types are: celery-microservice, library, swagger-rest-microservice, skeleton, docker.
            Defaults to None.

    Returns:
        set of str: List of requirements for this package
    """

    build_deps_path = os.path.join(repo_path, package_path(packages[package_name]))
    requirements = deps(build_deps_path) & set(packages.keys())

    if restrict_requirements_types is not None:
        packages_restricted = filter(lambda pkg: pkg.get('type') in restrict_requirements_types, packages.values())
        packages_restricted = set(map(lambda pkg: pkg['pkg_name'], packages_restricted))
        requirements = requirements & packages_restricted

    if not requirements:
        logger.info('No internal requirements found for package {0} in {1}'.format(package_name, build_deps_path))
    return requirements


def output_levels(graph):
    """Generate relationship level dependencies with a directed graph

    Args:
        graph (networkx.classes.digraph.DiGraph): Represent a directed graph

    Return:
        Return a list of dependencies level, top level to the lower level
    """
    top_sort = list(nx.topological_sort_recursive(graph))

    levels = [[] for _ in xrange(len(top_sort))]

    for level, node in enumerate(top_sort):
        potential_level = level
        # While we are not connected to this level we push the package down a level
        while all((level_node, node) not in graph.edges() for level_node in levels[potential_level]) \
                and potential_level >= 0:
            potential_level -= 1

        # Potential_level is now below the one where the node should go (where we are not connected)
        potential_level += 1
        levels[potential_level].append(node)
    levels = filter(None, levels)
    return levels


def get_directed_components(graph):
    """Generate a list a directed graph

    Args:
        graph (networkx.classes.digraph.DiGraph): Represent a directed graph

    Returns:
        List of networkx.classes.digraph.DiGraph
    """
    undirected_connected_components = list(nx.connected_component_subgraphs(graph.to_undirected()))
    directed_connected_components = [graph.subgraph(comp_G.nodes()) for comp_G in undirected_connected_components]
    return directed_connected_components


def dependencies_layout(dependencies_levels, scale=1):
    """Generate a layout for the dependencies graph

    Args:
        dependencies_levels: A list of list with dependencies levels
        scale (float): Scale factor for positions

    Returns:
        dict: A dictionary of positions keyed by node
    """
    pos_x = np.empty(shape=0)
    pos_y = np.empty(shape=0)

    nodes = []

    scale *= 3

    component_top = 0
    for component_i, component in enumerate(dependencies_levels):
        pos_packages_x = np.empty(shape=0)
        pos_packages_y = np.empty(shape=0)
        for level_i, level in enumerate(component):
            nodes.extend(level)
            pos_packages_x = np.concatenate((pos_packages_x, np.zeros(len(level)) + level_i * scale))
            pos_packages_y = np.concatenate((pos_packages_y,
                                             np.linspace(0, scale * len(level), len(level)) - scale * len(level) / 2.))
        # We put this component on top of the previous one, adding a 'scale' margin
        pos_packages_y += 3 * scale + component_top
        # We update the total height
        component_top = pos_packages_y.max()

        pos_x = np.concatenate((pos_x, pos_packages_x))
        pos_y = np.concatenate((pos_y, pos_packages_y))

    pos = np.vstack((pos_x, pos_y))

    # Since the layout has grown arbitrarily big, we rescale it and center it
    pos = dict(zip(nodes, pos.T))
    return pos


def gplot(graph, dependencies_levels, save_path=None, output_type=None):
    """Draw a the dependency graph

    Args:
        graph (networkx.classes.digraph.DiGraph): Represent a directed graph
        dependencies_levels: A list of list with dependencies levels
        save_path (str): The path where the file is saved
        output_type (str): The output file can be a dot file or a png
    """
    name_file = str(time.time()).replace(".", "_")

    final_path = "{0}/{1}.{2}".format(save_path, name_file, output_type)

    if output_type is not None and save_path is not None:
        logger.info("Storing {0}.{1} in {2}".format(name_file, output_type, save_path))

    if output_type == "png":
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        logger.info("Drawing the graph")
        plt.figure(figsize=(12, 14))
        nx.draw_networkx(graph, pos=dependencies_layout(dependencies_levels), edge_color='g', node_size=3000)
        plt.savefig(final_path)
        logger.info("The graph is drawn")
    elif output_type == "dot":
        logger.info("Generating dot file")
        nx.write_dot(graph, final_path)
        logger.info("The dot file is generated")
    elif output_type is None:
        logger.info("output type is {0}".format(output_type))
    else:
        logger.error("The output type is unknown")
        raise FailDrawDepGraph

    logger.info("The file {0} is stored".format(final_path))
    return name_file


def gen_dependencies_level(directed_graph, draw=False):
    """Generate dependencies levels

    Args:
        directed_graph (networkx.classes.digraph.DiGraph): Graph that represents relationship dependencies
        draw (Boolean): of the function generate an image of dependencies level

    Returns:
        a tuple of
          - a boolean: True or False
          - a list of list with dependencies levels
    """
    name_file = None
    try:
        assert nx.is_directed_acyclic_graph(directed_graph)
    except AssertionError:
        logger.error('A cycle has been detected in the graph.')
        return False, None,

    logger.info('Generating the dependency levels')

    dependencies_levels = [output_levels(comp) for comp in get_directed_components(directed_graph)]
    logger.info('The dependency levels have been generated')
    if draw:
        name_file = gplot(directed_graph, dependencies_levels, save_path='/home/pwned/ci_img', output_type='png')
        with lcd("/home/pwned/ci_img"):
            local("git checkout master")
            local("git fetch origin")
            local("git merge origin/master")
            local("git add .")
            local("git commit -m 'Add {0}'".format(name_file))
            local("git push origin")

    return True, dependencies_levels, name_file


def get_do_not_touch_packages(id_pr, packages, scm, dep_graph, rebuild=False):
    """Get packages that should not be touched (except if one of their dependencies was modified)

    These are packages which have only green builds, that were not modified in the last commits, and whose
    relationships between each other involve _only_ themselves.

    Args:
        id_pr: ID of the pull request
        packages (dict): all packages. Keys are packages names, values are directly taken from config.json
        scm (loktar_api.scm.Github): Internal Github instance
        dep_graph (networkx.classes.digraph.DiGraph): Graph that represents relationships between dependencies
        rebuild (bool): If True (default), skip the head commit

    Returns:
        set: Set of packages that should not be touched
    """

    if rebuild:  # If rebuild is True, we only consider the last commit's statuses
        last_status_commit, statuses = scm.get_last_statuses_from_pull_request(id_pr, exclude_head=False)
        pr = scm.get_pull_request(id_pr)
        if last_status_commit.sha == pr.head.sha:
            modified_packages_last_commits = set()
        else:
            raise CIJobFail('Cannot rebuild if no build was launched in the first place.')

    else:  # Otherwise, we get the last commit that has statuses before the last commit of the pull request
        last_status_commit, statuses = scm.get_last_statuses_from_pull_request(id_pr)
        last_commits = scm.get_last_commits_from_pull_request(id_pr, until_commit=last_status_commit)
        # Get the modified package in the last commit
        all_commit_files = [commit_file for commit in last_commits for commit_file in commit.files]
        modified_files = map(lambda file_: file_.filename, all_commit_files)
        modified_packages_last_commits = {package_from_path(path, packages) for path in modified_files}
        modified_packages_last_commits -= {None}

    green_builds, red_builds = parse_statuses(statuses)

    logger.info('Packages with green builds: {0}'.format(green_builds))
    logger.info('Packages with red builds: {0}'.format(red_builds))
    logger.info('Packages modified in the last commit: {0}'.format(modified_packages_last_commits))

    # Packages that should not be touched are package that got completely green builds
    # and that were not modified during the last commit
    do_not_touch_packages = green_builds - red_builds - modified_packages_last_commits

    if do_not_touch_packages:
        # In the following algorithm we use an augmented dep graph where we add a node which points to every other
        # node, and this node is added temporarily to do_not_touch_packages
        # This is used to avoid the case where the root(s) of the graph (set of nodes that are topologically less
        # than every other node) are not modified, then creating a path where there is an package not in
        # do_not_touch_packages and solving the corner case of the path algorithm.
        null_node = '__null__'
        augmented_dep_graph = copy.deepcopy(dep_graph)
        augmented_dep_graph.add_edges_from([(null_node, node) for node in augmented_dep_graph.nodes()])
        do_not_touch_packages |= {null_node}

        # TODO(Simplify the path check. Some packages are checked several times)

        # Now we check that for every path between packages in this list a path between them only contains packages
        # that should not be touched. If this is not the case we add the target package to have_path
        have_incomplete_path = set()
        for package_from, package_to in product(do_not_touch_packages, do_not_touch_packages):
            paths = nx.all_simple_paths(augmented_dep_graph, package_from, package_to)
            # We remove every 2-path containing the null node
            paths = filter(lambda path: not (len(path) == 2 and null_node in path), paths)
            for path in paths:
                # If there are packages in the path that are not in do_not_touch, add the target package to the set
                if set(path) - do_not_touch_packages:
                    have_incomplete_path |= {package_to}

        do_not_touch_packages -= have_incomplete_path
        do_not_touch_packages -= {null_node}

        logger.info('Packages that have an incomplete path directed to them: {0}'.format(have_incomplete_path))
    logger.info('Packages that should not be touched: {0}'.format(do_not_touch_packages))
    return do_not_touch_packages


@retry
def pull_request_information(id_pr, workspace):
    """Relevant information for packages from a pull request

    Args:
        id_pr: ID of the pull request
        workspace:

    Returns:
        tuple
    """
    scm = Github(GITHUB_INFO["login"]["user"], GITHUB_INFO["login"]["password"])

    if id_pr is not None:
        dict_message_files = scm.get_commit_message_modified_files_on_pull_request(id_pr)
        # Filter out Merge remote-tracking commits and Merge branch
        dict_message_files = {key: value for key, value in dict_message_files.iteritems()
                              if (not key.startswith('Merge remote-tracking branch') and
                                  not key.startswith('Merge branch'))}
        git_branch = scm.get_git_branch_from_pull_request(id_pr)
        config = json.loads(fetch_github_file('https://raw.githubusercontent.com/{0}/{1}/{2}/config.json'
                                              .format(GITHUB_INFO["organization"],
                                                      GITHUB_INFO["repository"],
                                                      urllib.quote(git_branch)),
                                              GITHUB_TOKEN))
        map_pkg = config["packages"]
        # Concatenate the lists that are values of dict_message_files
        git_diff = [item for _list in dict_message_files.values() for item in _list]
    else:
        logger.error("Pull request not found: #{0}".format(id_pr))
        raise ValueError('No PR #{0}'.format(id_pr))

    packages = {pkg["pkg_name"]: pkg for pkg in map_pkg}
    modified_packages = {package_from_path(path, packages) for path in git_diff} - {None}
    exclude_dep = get_excluded_deps(packages, dict_message_files, modified_packages)
    logger.info('The following packages\' dependencies will be ignored if unmodified: {0}'
                .format(exclude_dep))

    with lcd(os.path.join(workspace)):
        local("git checkout master")
        local("git fetch origin")
        local("git merge origin/master")
        local("git checkout {0}".format(git_branch))
        local("git merge origin/{}".format(git_branch))
        dep_graph = dependency_graph_from_modified_packages(workspace,
                                                            packages,
                                                            modified_packages,
                                                            exclude_dep)
    return config, dep_graph, modified_packages
