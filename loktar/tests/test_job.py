from mock import MagicMock
import pytest

from loktar.exceptions import CIJobFail
from loktar.job import build_params_to_context
from loktar.job import ci_downstream
from loktar.job import context_to_build_params
from loktar.job import job_manager
from loktar.job import launch_jobs
from loktar.job import launch_queue


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    mocker.patch('time.sleep')


@pytest.fixture
def jenkins_obj(mocker):
    jenkins_mock = mocker.patch('jenkins.Jenkins').return_value
    return jenkins_mock


@pytest.fixture
def jenkinsapi_obj(mocker):
    jenkins_mock = mocker.patch('loktar.job.Jenkins').return_value
    return jenkins_mock


@pytest.fixture
def mock_call_to_func_from_job_manager(mocker):
    launch_job_mock = mocker.patch('loktar.job.launch_jobs', autospec=True)
    return launch_job_mock


def test_ci_downstream(jenkins_obj):
    jenkins_obj.build_job.return_value = ''

    ci_downstream(
        {
            'host': '',
            'user': '',
            'password': ''
        },
        'toto', 'test', {})


def test_job_manager(jenkinsapi_obj, mocker, mock_call_to_func_from_job_manager):
    mocker.patch('loktar.job.define_job_status_on_github_commit')
    ci_config = {
        'host': 'localhost',
        'user': 'user',
        'password': 'password'
    }
    component = [['my_firstlib'], ['microservice_depending on_my_firstlib']]
    component_id = 'component_id'
    git_branch = 'master'
    commit_id = 'commit_id'
    committer = 'committer'
    test_env_path = '/tmp'
    map_pkg = [{'pkg_name': 'my_firstlib', 'pkg_type': 'wheel'}]
    job_manager(ci_config,
                component,
                component_id,
                map_pkg,
                git_branch,
                commit_id,
                committer,
                test_env_path)


@pytest.mark.parametrize('jenkins_fail, new_pr', [(True, False), (False, True), (False, False)])
@pytest.mark.parametrize('type_build', ['test', 'build'])
def test_launch_jobs(mocker, jenkins_fail, new_pr, type_build):
    actual_number_lvl = 0
    commit_id = 'commit_id'
    committer = 'committer'
    component_id = 'component_id'
    git_branch = 'master'
    map_pkg = [{'pkg_name': 'my_firstlib', 'pkg_type': 'wheel'}]

    mock_scm = mocker.patch('loktar.job.Github').return_value
    if new_pr:
        mock_scm.get_pull_request.return_value.head.sha = 'new_commit'
    else:
        mock_scm.get_pull_request.return_value.head.sha = 'commit_id'

    mocker.patch('time.sleep')
    queue_item = MagicMock()
    # Is in queue at first iteration, is building at the second
    queue_item.is_running.side_effect = (False, True)
    # The underlying build stops after one iteration
    queue_item.get_build.return_value.is_running.return_value = False
    build = MagicMock()
    # Is building at any iteration
    build.is_running.return_value = True
    # The underlying build stops after one iteration
    build.get_build.return_value.is_running.return_value = False
    mocker.patch('loktar.job.is_good', return_value=not jenkins_fail)
    mocker.patch('loktar.job.launch_queue', side_effect=(queue_item, build))
    jenkins_instance = MagicMock()
    mock_queue = MagicMock()
    jenkins_instance.get_queue.return_value = mock_queue

    # First lib is queue_item, second lib is build
    lvl = ['my_firstlib', 'my_secondlib']
    number_level_component = 3
    test_env_path = '/tmp'
    if jenkins_fail or new_pr:
        with pytest.raises(CIJobFail):
            launch_jobs(actual_number_lvl,
                        jenkins_instance,
                        commit_id,
                        committer,
                        component_id,
                        git_branch,
                        lvl,
                        number_level_component,
                        type_build,
                        test_env_path,
                        map_pkg)
        assert mock_queue.delete_item.call_args_list != []
    else:
        launch_jobs(actual_number_lvl,
                    jenkins_instance,
                    commit_id,
                    committer,
                    component_id,
                    git_branch,
                    lvl,
                    number_level_component,
                    type_build,
                    test_env_path,
                    map_pkg)


@pytest.mark.parametrize('type_build', ['test', 'artifact', 'artifactmaster'])
def test_launch_queue(jenkinsapi_obj, type_build):
    jenkins_instance = jenkinsapi_obj
    actual_number_lvl = 0
    commit_id = 'commit_id'
    committer = 'committer'
    component_id = 'component_id'
    git_branch = 'master'
    dep = 'my_firstlib'
    number_level_component = 3
    test_env_path = '/tmp'

    launch_queue(actual_number_lvl,
                 jenkins_instance,
                 commit_id,
                 committer,
                 component_id,
                 dep,
                 git_branch,
                 number_level_component,
                 type_build,
                 test_env_path)


@pytest.mark.parametrize('package,type_build', [('The Package', 'Is a Test'),
                                                ('swagger-rest-microservice', 'Is-a-Test'),
                                                ('swagger-rest-microservice', 'Is a Test'),
                                                ('my_client_claims', 'Is a Test')])
def test_context_to_build_params_reverse(package, type_build):
    context = build_params_to_context(package, type_build)
    assert context_to_build_params(context) == (package, type_build)


def test_context_to_build_fail():
    with pytest.raises(ValueError):
        context_to_build_params('Some context')
