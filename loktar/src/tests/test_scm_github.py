from github import GithubException
from mock import MagicMock
import pytest

from loktar.exceptions import SCMError
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
        def __init__(self, fail):
            self.fail = fail

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


class fakePR(object):
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


@pytest.mark.parametrize("fail", [
    {"status": 201, "exc": False},
    {"status": 400, "exc": False},
    {"status": 201, "exc": True}
])
def test_github(mock_github_obj, fail):

    def fake(fail, *args, **kwargs):
        return fakePR(fail)

    mock_github = mock_github_obj
    mock_github.return_value = fake(fail)

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
    if fail["status"] != 201 or fail["exc"] is True:
        with pytest.raises(SCMError) as excinfo:
            scm.set_tag_and_release("tag_name", "tag_message", "release_name", "patch_note", "commit_id")

            if fail["status"] != 201:
                assert str(excinfo) == "SCMError: The tag or the release can't be created"
    else:
        response = scm.set_tag_and_release("tag_name", "tag_message", "release_name", "patch_note", "commit_id")

        assert response.has_key("status")
        assert response["status"] == "201 Created"


def test_fetch_github_file(mocker):
    mocker.patch("loktar.scm.requests")
    mocker.patch("loktar.scm.StringIO")

    fetch_github_file("https://github.com/foo/bar/titi", "MY_AWESOME_TOKEN")
