import pytest

from loktar.notifications import define_job_status_on_github_commit


@pytest.mark.parametrize("state", ["pending", "success", "error", "failure", 'unknown status'])
@pytest.mark.parametrize("description", [None, "my awesome description", "a"*144])
@pytest.mark.parametrize("commit_id", ["4dq4d56q4dq65s", None])
def test_define_job_status_on_github_commit(mocker, commit_id, state, description):
    class Commit(object):
        def __init__(self, *args, **kwargs):
            pass

        def create_status(self, *args, **kwargs):
            return True

    class FakeRepo(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_commit(self, *args, **kwargs):
            return Commit()

    class FakeOrga(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_repo(self, *args, **kwargs):
            return FakeRepo()

    class FakeGithub(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_organization(self, *args, **kwargs):
            return FakeOrga()

    mocker.patch("loktar.notifications.Github", side_effect=FakeGithub)
    define_job_status_on_github_commit(commit_id,
                                       state,
                                       "www.example.com",
                                       "SUPER JOB ...",
                                       description)
