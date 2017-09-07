import os

from mock import MagicMock
import networkx as nx
import pytest

from loktar.dependency import dependencies_layout
from loktar.dependency import dependency_graph_from_modified_artifacts
from loktar.dependency import gen_dependencies_level
from loktar.dependency import get_do_not_touch_artifacts
from loktar.dependency import get_excluded_deps
from loktar.dependency import get_artifact_requirements
from loktar.dependency import artifact_from_path
#from loktar.dependency import pull_request_information
from loktar.job import build_params_to_context

repo_path = '/repo/'


@pytest.fixture
def artifacts():
    return


def strategy_runner_deps(artifact_config, run_type, **kwargs):
    target = kwargs.get("basepath")

    if target == os.path.join(repo_path, 'some_dir', 'my_biglibrary'):
        return {'some_dep'}
    elif target == os.path.join(repo_path, 'some_artifact_dir', 'artifact1'):
        return {'my_smalllibrary', 'my_biglibrary'}
    elif target == os.path.join(repo_path, 'my_smalllibrary'):
        return {'my_biglibrary'}
    elif target == os.path.join(repo_path, 'artifact2'):
        return {'my_smalllibrary'}
    elif target == os.path.join(repo_path, 'artifact3'):
        return {'my_biglibrary'}


@pytest.mark.parametrize('path,artifact,expected', [
    ('some_dir/artifact/my_youtube_uploader/youtube_uploader.py',
     {'artifact_dir': 'some_dir', 'artifact_name': 'artifact'},
     'artifact'),
    ('artifact/my_youtube_uploader/youtube_uploader.py',
     {'artifact_name': 'artifact'},
     'artifact'),
    ('artifact',
     {'artifact_name': 'artifact'},
     'artifact'),
    ('tamere_en_slip/tamere_en_slip_lib/sextape.gropython',
     {'artifact_name': 'artifact'},
     None),
    ("artifact2/my_youtube_uploader/youtube_uploader.py",
     {"artifact_name": "artifact"},
     None),
    ("my_youtube_uploader/artifact2/youtube_uploader.py",
     {"artifact_name": "artifact"},
     None),
    ("some_dir/toto/my_youtube_uploader/artifact",
     {"artifact_dir": "some_dir", "artifact_name": "artifact"},
     None),
    ("some_dir/artifact2/my_youtube_uploader/artifact",
     {"artifact_dir": "some_dir", "artifact_name": "artifact"},
     None),
    ("some_dir/artifact2",
     {"artifact_dir": "some_dir", "artifact_name": "artifact"},
     None),
])
def test_artifact_from_path(path, artifact, expected):
    artifacts = {artifact['artifact_name']: artifact}
    assert artifact_from_path(path, artifacts) == expected


# def test_get_artifact_requirements(mocker):
#     l_repo_path = '/repo/'
#     artifacts = {'my_biglibrary': {'artifact_dir': 'some_dir', 'artifact_name': 'my_biglibrary', 'type': 'library'},
#                  'my_smalllibrary': {'artifact_name': 'my_smalllibrary', 'type': 'library'},
#                  'artifact1': {'artifact_name': 'artifact1', 'artifact_dir': 'some_artifact_dir'},
#                  'artifact2': {'artifact_name': 'artifact2'},
#                  'artifact3': {'artifact_name': 'artifact3'}}
#
#     mocker.patch('loktar.dependency.strategy_runner', side_effect=strategy_runner_deps)
#
#     artifact_name = 'artifact1'
#
#     requirements = get_artifact_requirements(artifact_name,
#                                              artifacts,
#                                              l_repo_path)
#     assert requirements == {'my_biglibrary', 'my_smalllibrary'}
#
#
# @pytest.mark.parametrize('exclude', [True, False])
# def test_dependency_graph_from_modified_artifact(mocker, exclude):
#     # We take the following example:
#     #             _ _ _ _ _ _ _ _ _ _ _ _ artifact1
#     #           /                         /
#     #          |          my_smalllibrary
#     #          |         /                \
#     #     (my_biglibrary)                 (artifact2)
#     #                    \
#     #                     (artifact3)
#     #
#     # artifacts surrounded by parentheses were modified. If my_biglibrary's dependencies are excluded, then
#     # there should be no link between artifact2 and my_biglibrary, ie the graph is {my_biglibrary -> artifact3,
#     # artifact2}.
#     # However if my_biglibrary's dependencies are _not_ excluded, the graph should be the same as above.
#
#     modified_artifact = {'my_biglibrary', 'artifact2', 'artifact3'}
#     artifacts = {'my_biglibrary': {'artifact_dir': 'some_dir', 'artifact_name': 'my_biglibrary'},
#                  'my_smalllibrary': {'artifact_name': 'my_smalllibrary'},
#                  'artifact1': {'artifact_name': 'artifact1', 'artifact_dir': 'some_artifact_dir'},
#                  'artifact2': {'artifact_name': 'artifact2'},
#                  'artifact3': {'artifact_name': 'artifact3'}}
#     exclude_dep_from_artifact = {'my_biglibrary'} if exclude else None
#
#     mocker.patch('loktar.dependency.strategy_runner', side_effect=strategy_runner_deps)
#
#     edges_list = dependency_graph_from_modified_artifacts(repo_path,
#                                                           artifacts,
#                                                           modified_artifact,
#                                                           exclude_dep_from_artifact).edges()
#     if exclude:
#         assert set(edges_list) == {('my_biglibrary', 'artifact3')}
#     else:
#         assert set(edges_list) == {('my_biglibrary', 'artifact3'), ('my_biglibrary', 'my_smalllibrary'),
#                                    ('my_smalllibrary', 'artifact1'), ('my_smalllibrary', 'artifact2'),
#                                    ('my_biglibrary', 'artifact1')}
#
#
# @pytest.mark.parametrize('cycle', [True, False])
# @pytest.mark.parametrize('draw', [True, False])
# def test_gen_dependencies_level(mocker, cycle, draw):
#     mocker.patch('loktar.dependency.Log')
#     mocker.patch('loktar.dependency.matplotlib')
#     mocker.patch('loktar.dependency.plt')
#     mocker.patch('loktar.dependency.local')
#     edges = [('A', 'B'),
#              ('B', 'C'),
#              ('A', 'C'),
#              ('A', 'E')]
#     if cycle:
#         edges += [('C', 'A')]
#     modified_artifact = {'A', 'B', 'D'}
#
#     directed_graph = nx.DiGraph(edges)
#     directed_graph.add_nodes_from(modified_artifact)
#
#     if cycle:
#         assert not gen_dependencies_level(directed_graph)[0]
#     else:
#         success, dependency_levels, name_graph_img = gen_dependencies_level(directed_graph, draw=draw)
#         assert success
#         assert dependency_levels == [[['A'], ['E', 'B'], ['C']], [['D']]]
#
#
# def test_dependency_layout():
#     dependencies_layout([[['A'], ['E', 'B'], ['C']], [['D']]])
#
#
# @pytest.mark.parametrize('exclude', [True, False])
# def test_get_excluded_deps(exclude):
#     artifacts = {
#         'A': {'exclude_dependencies_only_on_keywords': ['KEY', 'MOD']},
#         'B': {},
#         'C': {},
#         'D': {'exclude_dependencies_only_on_keywords': ['MOD']}
#     }
#     # Here the files are directly artifacts names thanks to the artifact_from_path mock
#     dict_message_files = {
#         'KEY: Some modification': ['A'],
#         'KEY/MOD: Some modification': ['A'],
#         'MOD: Some other modification': ['B'],
#     }
#
#     # A's dependencies should not be excluded if there is an important commit
#     if not exclude:
#         dict_message_files.update({
#             'IMPORTANT: Made a critical modification': ['A'],
#             'IMPORTANT/MOD: Made a critical modification': ['A']
#         })
#
#     modified_artifact = {'A', 'B'}
#
#     exclude_dep = get_excluded_deps(artifacts, dict_message_files, modified_artifact)
#     assert exclude_dep == {'A'} if exclude else exclude_dep == set()
#
#
# @pytest.mark.parametrize('include_root', [True, False])
# @pytest.mark.parametrize('rebuild', [True, False])
# def test_get_do_not_touch_artifacts(include_root, rebuild):
#     class Status(object):
#         def __init__(self, artifact, state, status_type='some type'):
#             self.raw_data = {'context': build_params_to_context(artifact, status_type)}
#             self.state = state
#
#     class FakePullRequest(object):
#         def __init__(self, *args, **kwargs):
#             class SHA(object):
#                 @property
#                 def sha(self):
#                     return 'sha'
#
#             self.head = SHA()
#
#     id_pr = 42
#
#     scm = MagicMock()
#     if include_root:
#         green_builds = {'A', 'B', 'C', 'D'}
#     else:
#         green_builds = {'B', 'C', 'D'}
#     red_builds = {'E'}
#
#     statuses = [Status(artifact, state)
#                 for artifact, state in (zip(green_builds, ['success'] * len(green_builds)) +
#                                         zip(red_builds, ['error'] * len(red_builds)))]
#
#     last_commit = MagicMock()
#     last_commit.sha = 'sha'
#     # This excludes C
#     last_commit.files = [MagicMock(filename='C')]
#     # last_status_commit = MagicMock()
#     scm.get_last_commits_from_pull_request.return_value = [last_commit]
#     scm.get_last_statuses_from_pull_request.return_value = last_commit, statuses
#     scm.get_pull_request.return_value = FakePullRequest()
#
#     modified_artifact = {'A': {}, 'B': {}, 'C': {}, 'D': {}, 'E': {}}
#     # Dependency graph used for this test:
#     #
#     # [A - red or green / unmodified]____[B - green / unmodified]____[C - green / modified]____[D - green / unmodified]
#     #  \___[E - red / unmodified]
#     edges = [('A', 'B'),
#              ('B', 'C'),
#              ('C', 'D'),
#              ('A', 'E')]
#
#     dep_graph = nx.DiGraph(edges)
#     dep_graph.add_nodes_from(modified_artifact)
#
#     # Here we should have do_not_touch_artifact set to {'A', 'B', 'D'} before going through the path check
#     # Since C is between B and D, D will be excluded and only A and B remain
#     do_not_touch_artifact = get_do_not_touch_artifacts(id_pr, modified_artifact, scm, dep_graph, rebuild)
#     if include_root and not rebuild:
#         assert do_not_touch_artifact == {'A', 'B'}
#     elif include_root and rebuild:
#         # In this case there are no modified artifact because there are
#         # no new commits. Since the root is included, this means A has
#         # a green build, and so do B, C, D. Since A -> B -> C -> D,
#         # we can safely ignore all these artifacts.
#         assert do_not_touch_artifact == {'A', 'B', 'C', 'D'}
#     else:
#         assert do_not_touch_artifact == set()
