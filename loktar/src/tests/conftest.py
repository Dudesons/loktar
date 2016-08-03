from github import GithubException
from mock import MagicMock
import pytest


class File(object):

        def __init__(self, name):
            self.filename = name


class Commit(object):
        files = [File("toto"), File("toto"), File("lulu")]
        sha = 'sha'

        def __init__(self, *args, **kwargs):

            class Commit_(object):
                message = 'message'

            self.commit = Commit_()

        def get_statuses(self):
            return ['status1', 'status2']


class PullRequestPart(object):
        ref = 'branch'
        sha = 'commitsha'


class IssueComment(object):
        body = 'existing comment'


class PullRequest(object):
        head = PullRequestPart()
        number = 565

        def __init__(self, *args, **kwargs):
            pass

        def get_commits(self):
            # Mocking a paginated list
            m = MagicMock(reversed=[Commit(), Commit()])

            def one_element():
                yield Commit()
                yield Commit()
            m.__iter__.side_effect = one_element
            return m

        def get_issue_comments(self):
            return [IssueComment()]

        def create_issue_comment(self, comment):
            return comment

        def get_files(self):
            return [File("toto"), File("toto"), File("lulu")]


class Repository(object):
        def __init__(self, fail):
            self.fail = fail

        def get_pulls(self, state=None):
            return [
                PullRequest(),
                PullRequest()
            ]

        def get_pull(self, state=None):
            if self.fail["exc"] is False:
                return PullRequest()
            else:
                raise AssertionError

        def get_commit(self, sha):
            if self.fail["exc"] is False:
                return Commit()
            else:
                raise AssertionError

        def commit(self, sha):
            return Commit()

        def create_git_tag_and_release(self, tag_name, tag_message, release_name, patch_note, commit_id, type_object="commit"):
            if self.fail["status"] == 201 and self.fail["exc"] is False:
                return {
                    "status": "201 Created"
                }
            else:
                if self.fail["status"] == 400:
                    return {
                        "status": "400 blabla"
                    }
                else:
                    raise GithubException("", "")


class FakeGithubRepo(object):
        def __init__(self, fail):
            self.fail = fail

        def get_organization(self, *args, **kwargs):
            mock_get_repo = MagicMock()
            mock_get_repo.get_repo.return_value = Repository(self.fail)
            return mock_get_repo


@pytest.fixture
def mock_github_obj(mocker):
    github_mock = mocker.patch('loktar.scm.GitHub')

    return github_mock


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    def mockreturn(*args, **kwargs):
        return True

    monkeypatch.setattr("time.sleep", lambda x: mockreturn)


@pytest.fixture(autouse=True)
def no_exit(monkeypatch):
    monkeypatch.setattr("sys.exit", lambda x: False if x else True)
