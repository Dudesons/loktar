import os

from mock import MagicMock
import networkx as nx
import pytest

from loktar.dependency import dependency_graph_from_modified_packages
from loktar.dependency import dependencies_layout
from loktar.dependency import gen_dependencies_level
from loktar.dependency import get_do_not_touch_packages
from loktar.dependency import get_excluded_deps
from loktar.dependency import get_package_requirements
from loktar.dependency import pull_request_information
from loktar.dependency import package_from_path
from loktar.job import build_params_to_context

repo_path = '/repo/'


@pytest.fixture
def pacakges():
    return


def build_deps(command):
    if command == os.path.join(repo_path, 'some_dir', 'my_biglibrary'):
        return {'some_dep'}
    elif command == os.path.join(repo_path, 'some_pkg_dir', 'package1'):
        return {'my_smalllibrary', 'my_biglibrary'}
    elif command == os.path.join(repo_path, 'my_smalllibrary'):
        return {'my_biglibrary'}
    elif command == os.path.join(repo_path, 'package2'):
        return {'my_smalllibrary'}
    elif command == os.path.join(repo_path, 'package3'):
        return {'my_biglibrary'}


@pytest.mark.parametrize('path,package,expected', [
    (
            'some_dir/package/my_youtube_uploader/youtube_uploader.py',
            {'pkg_dir': 'some_dir', 'pkg_name': 'package'},
            'package'
    ),
    (
            'package/my_youtube_uploader/youtube_uploader.py',
            {'pkg_name': 'package'},
            'package'),
    (
            'package',
            {'pkg_name': 'package'},
            'package'
    ),
    (
            'tamere_en_slip/tamere_en_slip_lib/sextape.gropython',
            {'pkg_name': 'package'},
            None
    )
])
def test_package_from_path(path, package, expected):
    packages = {package['pkg_name']: package}
    assert package_from_path(path, packages) == expected


def test_get_package_requirements(mocker):
    repo_path = '/repo/'
    packages = {'my_biglibrary': {'pkg_dir': 'some_dir', 'pkg_name': 'my_biglibrary', 'type': 'library'},
                'my_smalllibrary': {'pkg_name': 'my_smalllibrary', 'type': 'library'},
                'package1': {'pkg_name': 'package1', 'pkg_dir': 'some_pkg_dir'},
                'package2': {'pkg_name': 'package2'},
                'package3': {'pkg_name': 'package3'}}

    mocker.patch('loktar.dependency.python_deps')
    mocker.patch('loktar.dependency.docker_deps')
    mocker.patch('loktar.dependency.deps', side_effect=build_deps)

    package_name = 'package1'

    requirements = get_package_requirements(package_name, packages, repo_path, restrict_requirements_types=['library'])
    assert requirements == {'my_biglibrary', 'my_smalllibrary'}


@pytest.mark.parametrize('exclude', [True, False])
def test_dependency_graph_from_modified_packages(mocker, exclude):
    # We take the following example:
    #             _ _ _ _ _ _ _ _ _ _ _ _ package1
    #           /                         /
    #          |          my_smalllibrary
    #          |         /                \
    #     (my_biglibrary)                 (package2)
    #                    \
    #                     (package3)
    #
    # Packages surrounded by parentheses were modified. If my_biglibrary's dependencies are excluded, then
    # there should be no link between package2 and my_biglibrary, ie the graph is {my_biglibrary -> package3,
    # package2}.
    # However if my_biglibrary's dependencies are _not_ excluded, the graph should be the same as above.

    modified_packages = {'my_biglibrary', 'package2', 'package3'}
    packages = {'my_biglibrary': {'pkg_dir': 'some_dir', 'pkg_name': 'my_biglibrary'},
                'my_smalllibrary': {'pkg_name': 'my_smalllibrary'},
                'package1': {'pkg_name': 'package1', 'pkg_dir': 'some_pkg_dir'},
                'package2': {'pkg_name': 'package2'},
                'package3': {'pkg_name': 'package3'}}
    exclude_dep_from_packages = {'my_biglibrary'} if exclude else None

    mocker.patch('loktar.dependency.deps', side_effect=build_deps)

    edges_list = dependency_graph_from_modified_packages(repo_path,
                                                         packages,
                                                         modified_packages,
                                                         exclude_dep_from_packages).edges()
    if exclude:
        assert set(edges_list) == {('my_biglibrary', 'package3')}
    else:
        assert set(edges_list) == {('my_biglibrary', 'package3'), ('my_biglibrary', 'my_smalllibrary'),
                                   ('my_smalllibrary', 'package1'), ('my_smalllibrary', 'package2'),
                                   ('my_biglibrary', 'package1')}


@pytest.mark.parametrize('cycle', [True, False])
@pytest.mark.parametrize('draw', [True, False])
def test_gen_dependencies_level(mocker, cycle, draw):
    mocker.patch('loktar.dependency.Log')
    mocker.patch('loktar.dependency.matplotlib')
    mocker.patch('loktar.dependency.plt')
    mocker.patch('loktar.dependency.local')
    edges = [('A', 'B'),
             ('B', 'C'),
             ('A', 'C'),
             ('A', 'E')]
    if cycle:
        edges += [('C', 'A')]
    modified_packages = {'A', 'B', 'D'}

    directed_graph = nx.DiGraph(edges)
    directed_graph.add_nodes_from(modified_packages)

    if cycle:
        assert not gen_dependencies_level(directed_graph)[0]
    else:
        success, dependency_levels, name_graph_img = gen_dependencies_level(directed_graph, draw=draw)
        assert success
        assert dependency_levels == [[['A'], ['E', 'B'], ['C']], [['D']]]


def test_dependency_layout():
    dependencies_layout([[['A'], ['E', 'B'], ['C']], [['D']]])

"""
@pytest.mark.parametrize('output_type', [None, "png", "dot"])
def test_gplot(mocker, output_type):
    mocker.patch("loktar.dependency.nx")
    from mock import Mock
    gplot(Mock(), [[['A'], ['E', 'B'], ['C']], [['D']]], output_type=output_type, save_path="/foobar")
"""

"""
@pytest.mark.parametrize("packages", [
    {
        'package': {'exclude_dependencies_only_on_keywords': ['CLN', 'BLD']},
        'package2': {'exclude_dependencies_only_on_keywords': []},
    }
])
@pytest.mark.parametrize("dict_message_files", [
    {'CLN/BLD: Cleaned some files. I do not care about dependencies': ['package/modified.py']},
    {'BUG: Fix an awesome bug': ['package/modified.py']}
])
@pytest.mark.parametrize("modified_packages", [{'package'}])
def test_get_excluded_deps(packages, dict_message_files, modified_packages):
    result = get_excluded_deps(packages, dict_message_files, modified_packages)
    if any("CLN" in i or "BLD" in i for i in dict_message_files.keys()):
        assert result == {"package"}
    else:
        assert result == set()
"""


@pytest.mark.parametrize('exclude', [True, False])
def test_get_excluded_deps(exclude):

    packages = {
        'A': {'exclude_dependencies_only_on_keywords': ['KEY', 'MOD']},
        'B': {},
        'C': {},
        'D': {'exclude_dependencies_only_on_keywords': ['MOD']}
    }
    # Here the files are directly packages names thanks to the package_from_path mock
    dict_message_files = {
        'KEY: Some modification': ['A'],
        'KEY/MOD: Some modification': ['A'],
        'MOD: Some other modification': ['B'],
    }

    # A's dependencies should not be excluded if there is an important commit
    if not exclude:
        dict_message_files.update({
            'IMPORTANT: Made a critical modification': ['A'],
            'IMPORTANT/MOD: Made a critical modification': ['A']
        })

    modified_packages = {'A', 'B'}

    exclude_dep = get_excluded_deps(packages, dict_message_files, modified_packages)
    assert exclude_dep == {'A'} if exclude else exclude_dep == set()


@pytest.mark.parametrize('include_root', [True, False])
@pytest.mark.parametrize('rebuild', [True, False])
def test_get_do_not_touch_packages(include_root, rebuild):
    class Status(object):
        def __init__(self, package, state, status_type='some type'):
            self.raw_data = {'context': build_params_to_context(package, status_type)}
            self.state = state

    class FakePullRequest(object):
        def __init__(self, *args, **kwargs):
            class SHA(object):
                @property
                def sha(self):
                    return 'sha'

            self.head = SHA()

    id_pr = 'id_pr'

    scm = MagicMock()
    if include_root:
        green_builds = {'A', 'B', 'C', 'D'}
    else:
        green_builds = {'B', 'C', 'D'}
    red_builds = {'E'}

    statuses = [Status(package, state)
                for package, state in (zip(green_builds, ['success'] * len(green_builds)) +
                                       zip(red_builds, ['error'] * len(red_builds)))]

    last_commit = MagicMock()
    last_commit.sha = 'sha'
    # This excludes C
    last_commit.files = [MagicMock(filename='C')]
    # last_status_commit = MagicMock()
    scm.get_last_commits_from_pull_request.return_value = [last_commit]
    scm.get_last_statuses_from_pull_request.return_value = last_commit, statuses
    scm.get_pull_request.return_value = FakePullRequest()

    modified_packages = {'A': {}, 'B': {}, 'C': {}, 'D': {}, 'E': {}}
    # Dependency graph used for this test:
    #
    # [A - red or green / unmodified]____[B - green / unmodified]____[C - green / modified]____[D - green / unmodified]
    #  \___[E - red / unmodified]
    edges = [('A', 'B'),
             ('B', 'C'),
             ('C', 'D'),
             ('A', 'E')]

    dep_graph = nx.DiGraph(edges)
    dep_graph.add_nodes_from(modified_packages)

    # Here we should have do_not_touch_packages set to {'A', 'B', 'D'} before going through the path check
    # Since C is between B and D, D will be excluded and only A and B remain
    do_not_touch_packages = get_do_not_touch_packages(id_pr, modified_packages, scm, dep_graph, rebuild)
    if include_root and not rebuild:
        assert do_not_touch_packages == {'A', 'B'}
    elif include_root and rebuild:
        # In this case there are no modified package because there are
        # no new commits. Since the root is included, this means A has
        # a green build, and so do B, C, D. Since A -> B -> C -> D,
        # we can safely ignore all these packages.
        assert do_not_touch_packages == {'A', 'B', 'C', 'D'}
    else:
        assert do_not_touch_packages == set()


def test_pull_request_information(mocker):
    mocker.patch('loktar.dependency.Github')
    mocker.patch('loktar.dependency.fetch_github_file')
    mocker.patch('loktar.dependency.json')
    mocker.patch('loktar.dependency.gen_dependencies_level', return_value=(True, ['lala']), autospec=True)
    pull_request_information(0, 'workspace')
    with pytest.raises(ValueError):
        pull_request_information(None, 'workspace')