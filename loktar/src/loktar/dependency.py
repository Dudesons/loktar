import copy
from fabric.api import lcd
from fabric.api import local
from itertools import product
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import os
import time
import re

from loktar.constants import DEPENDENDY_GRAPH
from loktar.exceptions import CIJobFail
from loktar.exceptions import FailDrawDepGraph
from loktar.log import Log
from loktar.parser import parse_statuses
from loktar.strategy_run import strategy_runner

logger = Log()


def get_excluded_deps(artifacts, dict_message_files, modified_artifacts):
    """Compute which artifact"s dependencies should be ignored based on commit messages.

    This does not take into account modified dependencies of an artifact whose dependencies are excluded.
    We only need to know if an artifacts non-modified dependencies should be ignored or not, the rest is
    done in ``dependency_graph_from_modified_artifacts``.

    Args:
        artifacts (dict): all artifacts. Keys are artifacts names, values are directly taken from config.json
        dict_message_files (dict of str: list): Comments of the commits linked to the pull request are keys,
            modified files are values. If empty, the returned set is empty.
        modified_artifacts (set of str): names of the artifacts that were modified

    Returns:
        set of str: items are artifacts names whose dependencies must not be added to the dependency graph

    Examples:
        >>> get_excluded_deps({"artifact": {"exclude_dependencies_only_on_keywords": ["CLN", "BLD"]}},
        ... {"CLN/BLD: Cleaned some files. I do not care about dependencies": "artifact/modified.py"},
        ... {"artifact"})
        {"artifact"}

        >>> get_excluded_deps({"artifact": {"exclude_dependencies_only_on_keywords": ["CLN", "BLD"]}},
        ... {"BUG: Fixed a serious bug! This should rebuild dependencies": "artifact/modified.py"},
        ... {})
        {"artifact"}
    """

    if not dict_message_files:
        return set()

    # artifacts whose dependencies should be ignored
    # Initialize to all of them and delete them one by one if some keywords are not exclusion keywords.
    exclude_dep = set(copy.deepcopy(modified_artifacts))
    for commit_message, modified_files in dict_message_files.items():
        for path in modified_files:
            artifact_name = artifact_from_path(path, artifacts)
            if artifact_name is None:
                continue
            # If we have set an exclude condition and this condition is matched
            elif "exclude_dependencies_only_on_keywords" in artifacts[artifact_name]:
                keywords = {key.strip() for key in commit_message.split(":")[0].split("/")}
                keywords_exclude = set(artifacts[artifact_name]["exclude_dependencies_only_on_keywords"])
                # If there is a keyword that is not excluded
                if keywords - keywords_exclude:
                    exclude_dep -= {artifact_name}
            else:
                exclude_dep -= {artifact_name}
    return exclude_dep


def artifact_from_path(path, artifacts):
    """Get the name of an artifact from a path.

    Args:
        path: relative path starting with the potential artifact name (Example: serializers/http/)
        artifacts (dict): all artifacts. Keys are artifacts names, values are directly taken from config.json

    Returns:
        the artifact name or None if the path is not inside an artifact
    """
    paths = path.split('/')

    for artifact_name, config in artifacts.iteritems():
        pattern0 = "^{}/?{}$".format(config.get("artifact_dir", ""), artifact_name)
        pattern1 = "^{}/?{}/.*$".format(config.get("artifact_dir", ""), artifact_name)
        regexp0 = re.compile(pattern0)
        regexp1 = re.compile(pattern1)

        if any([p == artifact_name and (regexp0.match(path) or regexp1.match(path)) for p in paths]):
            return artifact_name


def artifact_path(artifact):
    """Get the path of a artifact

    Args:
        artifact (dict): artifact configuration

    Returns:
        str: The artifact path relative to the repository root.
    """
    if "artifact_dir" in artifact:
        return os.path.join(artifact["artifact_dir"], artifact["artifact_name"])
    else:
        return artifact["artifact_name"]


def graph_edges(artifacts_requirements, modified_artifacts, exclude_dep_from_artifacts):
        """Recursively find graph edges

        Args:
            artifacts_requirements (dict of list): Dictionary of artifact_name: requirements
            modified_artifacts (set): artifact names that are considered modified
            exclude_dep_from_artifacts (set): Do not analyze the dependencies for the artifacts in this list

        Returns:
            list of tuple: Graph edges between artifacts.
        """
        if not modified_artifacts:
            return []

        edges_list = []
        next_modified_artifacts = set()
        artifacts_done = set()

        for artifact_name in artifacts_requirements:
            requirements = artifacts_requirements[artifact_name]
            # but whose dependencies are not excluded (iff this was not a modified artifact)
            modified_requirements = (requirements & modified_artifacts - exclude_dep_from_artifacts
                                     if artifact_name not in modified_artifacts
                                     else requirements & modified_artifacts)

            if modified_requirements:
                # Add the edges from the modified requirements towards this artifact
                edges = map(lambda x: (x, artifact_name), modified_requirements)
                edges_list.extend(edges)
                artifacts_done |= modified_requirements
                next_modified_artifacts |= {artifact_name}

        for artifact_name in artifacts_done:
            artifacts_requirements.pop(artifact_name, None)

        edges_list.extend(graph_edges(artifacts_requirements, next_modified_artifacts, exclude_dep_from_artifacts))
        return edges_list


def dependency_graph_from_modified_artifacts(repo_path,
                                             artifacts,
                                             modified_artifacts,
                                             exclude_dep_from_artifacts=None):
    """Parse requirement with a pattern for generating a dependencies graph

    Args:
        repo_path (str): this is the path where the repo to parse is
        artifacts (dict): all artifacts. Keys are artifacts names, values are directly taken from config.json
        modified_artifacts (set): This is a set a modified artifact
        exclude_dep_from_artifacts (Optional[set]): Do not analyze the dependencies for the artifacts in this list.
            Defaults to None.

    Returns:
        networkx.classes.digraph.DiGraph: The dependency graph.
    """
    if exclude_dep_from_artifacts is None:
        exclude_dep_from_artifacts = set()

    modified_artifacts = set(modified_artifacts)
    artifacts_requirements = {}

    # Go through all the artifacts
    for artifact_name in artifacts:
        requirements = get_artifact_requirements(artifact_name, artifacts, repo_path)
        if requirements:
            artifacts_requirements[artifact_name] = requirements

    edges_list = graph_edges(artifacts_requirements, modified_artifacts, exclude_dep_from_artifacts)

    directed_graph = nx.DiGraph(edges_list)
    directed_graph.add_nodes_from(modified_artifacts)

    return directed_graph


def get_artifact_requirements(artifact_name, artifacts, repo_path):
    """Get the requirements of a artifact

    Args:
        artifact_name (str): Name of the artifact to consider
        artifacts (dict): All artifacts. Keys are artifacts names, values are directly taken from config.json
        repo_path (str): This is the path where the repo to parse is

    Returns:
        set of str: List of requirements for this artifact
    """
    build_deps_path = os.path.join(repo_path, artifact_path(artifacts[artifact_name]))
    requirements = strategy_runner(artifacts[artifact_name], "dependency", basepath=build_deps_path)

    requirements &= set(artifacts.keys())

    if not requirements:
        logger.info("No internal requirements found for artifact {0} in {1}".format(artifact_name, build_deps_path))

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
        # While we are not connected to this level we push the artifact down a level
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
        pos_artifacts_x = np.empty(shape=0)
        pos_artifacts_y = np.empty(shape=0)
        for level_i, level in enumerate(component):
            nodes.extend(level)
            pos_artifacts_x = np.concatenate((pos_artifacts_x, np.zeros(len(level)) + level_i * scale))
            pos_artifacts_y = np.concatenate((pos_artifacts_y,
                                             np.linspace(0, scale * len(level), len(level)) - scale * len(level) / 2.))
        # We put this component on top of the previous one, adding a "scale" margin
        pos_artifacts_y += 3 * scale + component_top
        # We update the total height
        component_top = pos_artifacts_y.max()

        pos_x = np.concatenate((pos_x, pos_artifacts_x))
        pos_y = np.concatenate((pos_y, pos_artifacts_y))

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
        matplotlib.use("Agg")
        logger.info("Drawing the graph")
        plt.figure(figsize=(12, 14))
        nx.draw_networkx(graph, pos=dependencies_layout(dependencies_levels), edge_color="g", node_size=3000)
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
          - a string or None who represent the name of the image of the dep graph
    """
    name_file = None
    try:
        assert nx.is_directed_acyclic_graph(directed_graph)
    except AssertionError:
        logger.error("A cycle has been detected in the graph.")
        return False, None, None

    logger.info("Generating the dependency levels")

    dependencies_levels = [output_levels(comp) for comp in get_directed_components(directed_graph)]
    logger.info("The dependency levels have been generated")
    if draw:
        name_file = gplot(directed_graph, dependencies_levels, save_path=DEPENDENDY_GRAPH["repo"], output_type="png")
        with lcd(DEPENDENDY_GRAPH["repo"]):
            local("git checkout master")
            local("git fetch origin")
            local("git merge origin/master")
            local("git add .")
            local("git commit -m 'Add {0}'".format(name_file))
            local("git push origin")

    return True, dependencies_levels, name_file


def get_do_not_touch_artifacts(id_pr, artifacts, scm, dep_graph, rebuild=False):
    """Get artifacts that should not be touched (except if one of their dependencies was modified)

    These are artifacts which have only green builds, that were not modified in the last commits, and whose
    relationships between each other involve _only_ themselves.

    Args:
        id_pr: ID of the pull request
        artifacts (dict): all artifacts. Keys are artifacts names, values are directly taken from config.json
        scm (loktar_api.scm.Github): Internal Github instance
        dep_graph (networkx.classes.digraph.DiGraph): Graph that represents relationships between dependencies
        rebuild (bool): If True (default), skip the head commit

    Returns:
        set: Set of artifacts that should not be touched
    """

    if rebuild:  # If rebuild is True, we only consider the last commit"s statuses
        last_status_commit, statuses = scm.get_last_statuses_from_pull_request(int(id_pr), exclude_head=False)
        pr = scm.get_pull_request(int(id_pr))
        if last_status_commit.sha == pr.head.sha:
            modified_artifacts_last_commits = set()
        else:
            raise CIJobFail("Cannot rebuild if no build was launched in the first place.")

    else:  # Otherwise, we get the last commit that has statuses before the last commit of the pull request
        last_status_commit, statuses = scm.get_last_statuses_from_pull_request(int(id_pr))
        last_commits = scm.get_last_commits_from_pull_request(int(id_pr), until_commit=last_status_commit)
        # Get the modified artifact in the last commit
        all_commit_files = [commit_file for commit in last_commits for commit_file in commit.files]
        modified_files = map(lambda file_: file_.filename, all_commit_files)
        modified_artifacts_last_commits = {artifact_from_path(path, artifacts) for path in modified_files}
        modified_artifacts_last_commits -= {None}

    green_builds, red_builds = parse_statuses(statuses)

    logger.info("artifacts with green builds: {0}".format(green_builds))
    logger.info("artifacts with red builds: {0}".format(red_builds))
    logger.info("artifacts modified in the last commit: {0}".format(modified_artifacts_last_commits))

    # artifacts that should not be touched are artifact that got completely green builds
    # and that were not modified during the last commit
    do_not_touch_artifacts = green_builds - red_builds - modified_artifacts_last_commits

    if do_not_touch_artifacts:
        # In the following algorithm we use an augmented dep graph where we add a node which points to every other
        # node, and this node is added temporarily to do_not_touch_artifacts
        # This is used to avoid the case where the root(s) of the graph (set of nodes that are topologically less
        # than every other node) are not modified, then creating a path where there is an artifact not in
        # do_not_touch_artifacts and solving the corner case of the path algorithm.
        null_node = "__null__"
        augmented_dep_graph = copy.deepcopy(dep_graph)
        augmented_dep_graph.add_edges_from([(null_node, node) for node in augmented_dep_graph.nodes()])
        # Remove fake artifacts, to avoid error in the dependency graph manipulation
        do_not_touch_artifacts &= set(artifacts.keys())
        do_not_touch_artifacts |= {null_node}

        # TODO(Simplify the path check. Some artifacts are checked several times)

        # Now we check that for every path between artifacts in this list a path between them only contains artifacts
        # that should not be touched. If this is not the case we add the target artifact to have_path
        have_incomplete_path = set()
        for artifact_from, artifact_to in product(do_not_touch_artifacts, do_not_touch_artifacts):
            paths = nx.all_simple_paths(augmented_dep_graph, artifact_from, artifact_to)
            # We remove every 2-path containing the null node
            paths = filter(lambda path: not (len(path) == 2 and null_node in path), paths)
            for path in paths:
                # If there are artifacts in the path that are not in do_not_touch, add the target artifact to the set
                if set(path) - do_not_touch_artifacts:
                    have_incomplete_path |= {artifact_to}

        do_not_touch_artifacts -= have_incomplete_path
        do_not_touch_artifacts -= {null_node}

        logger.info("artifacts that have an incomplete path directed to them: {0}".format(have_incomplete_path))
    logger.info("artifacts that should not be touched: {0}".format(do_not_touch_artifacts))
    return do_not_touch_artifacts
