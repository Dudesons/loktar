import os

import networkx as nx
import pytest

from loktar.dependency import dependency_graph_from_modified_packages
from loktar.dependency import gen_dependencies_level
from loktar.dependency import get_package_requirements
from loktar.dependency import package_from_path


repo_path = '/repo/'


def build_deps(command):
        if command == os.path.join(repo_path, 'some_dir', 'my_biglibrary'):
            return {'some_dep'}
        elif command == os.path.join(repo_path, 'some_pkg_dir', 'package1'):
            return {'my_smalllibrary, my_biglibrary'}
        elif command == os.path.join(repo_path, 'my_smalllibrary'):
            return {'my_biglibrary'}
        elif command == os.path.join(repo_path, 'package2'):
            return {'my_smalllibrary'}
        elif command == os.path.join(repo_path, 'package3'):
            return {'my_biglibrary'}

"""
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

    #import pdb
    #pdb.set_trace()
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
"""

@pytest.mark.parametrize('cycle', [True, False])
def test_gen_dependencies_level(mocker, cycle):
    mocker.patch('loktar.dependency.Log')
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
        success, dependency_levels, name_graph_img = gen_dependencies_level(directed_graph)
        assert success
        assert dependency_levels == [[['A'], ['E', 'B'], ['C']], [['D']]]
