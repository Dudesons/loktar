from mock import MagicMock
import pytest

from loktar.scm import fetch_github_file
from loktar.scm import Github


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


class Repository(object):

        def get_pulls(self, state=None):
            return [
                PullRequest(),
                PullRequest()
            ]

        def get_pull(self, state=None):
            return PullRequest()

        def get_commit(self, sha):
            return Commit()

        def commit(self, sha):
            return Commit()


class fakePR(object):

        def get_organization(self, *args, **kwargs):
            mock_get_repo = MagicMock()
            mock_get_repo.get_repo.return_value = Repository()
            return mock_get_repo


@pytest.fixture
def mock_github_obj(mocker):
    github_mock = mocker.patch('loktar.scm.GitHub')

    return github_mock


def test_github(mock_github_obj):

    def fake(*args, **kwargs):
        return fakePR()

    mock_github = mock_github_obj
    mock_github.return_value = fake()

    scm = Github("toto", "titi")

    scm.search_pull_request_id("branch")
    pr_info = scm.get_pull_request(42)
    assert pr_info.head.ref == "branch"
    assert pr_info.head.sha == "commitsha"
    assert pr_info.number == 565
    assert pr_info.get_issue_comments()[0].body == "existing comment"

    commit_messages = scm.get_commit_message_modified_files_on_pull_request(42)
    scm.get_pull_requests()
    assert commit_messages == {'message': ['toto', 'toto', 'lulu', 'toto', 'toto', 'lulu']}
    assert scm.create_pull_request_comment(42, 'comment') == 'comment'
    assert scm.create_pull_request_comment(42, 'existing comment', check_unique=True) is None
    assert scm.get_git_branch_from_pull_request(42) == 'branch'
    last_commit, statuses = scm.get_last_statuses_from_pull_request(42)
    assert statuses == ['status1', 'status2']
    scm.get_last_commits_from_pull_request(42)


def test_fetch_github_file(mocker):
    mocker.patch("loktar.scm.requests")
    mocker.patch("loktar.scm.StringIO")

    fetch_github_file("https://github.com/foo/bar/titi", "MY_AWESOME_TOKEN")