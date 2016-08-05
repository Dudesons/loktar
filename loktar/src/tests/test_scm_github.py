import pytest

from conftest import FakeGithubRepo

from loktar.exceptions import SCMError
from loktar.scm import fetch_github_file
from loktar.scm import Github


@pytest.mark.parametrize("fail", [
    {"status": 201, "exc": False},
    {"status": 400, "exc": False},
    {"status": 201, "exc": True}
])
def test_github(mock_github_obj, fail):

    def fake(fail, *args, **kwargs):
        return FakeGithubRepo(fail)

    mock_github = mock_github_obj
    mock_github.return_value = fake(fail)
    mock_github.self.pull_requests_cache.return_value = {42}

    scm = Github("toto", "titi")

    scm.search_pull_request_id("branch")
    if fail["exc"] is False:
        pr_info = scm.get_pull_request(42)
        assert pr_info.head.ref == "branch"
        assert pr_info.head.sha == "commitsha"
        assert pr_info.number == 565
        assert pr_info.get_issue_comments()[0].body == "existing comment"

        scm.get_pull_request(42, use_cache=False)

        commit_messages = scm.get_commit_message_modified_files_on_pull_request(42)
        scm.get_pull_requests()
        scm.get_pull_requests(use_cache=True)
        assert commit_messages == {'message': ['toto', 'toto', 'lulu', 'toto', 'toto', 'lulu']}
        assert scm.create_pull_request_comment(42, 'comment') == 'comment'
        assert scm.create_pull_request_comment(42, 'existing comment', check_unique=True) is None
        assert scm.get_git_branch_from_pull_request(42) == 'branch'
        last_commit, statuses = scm.get_last_statuses_from_pull_request(42)
        assert statuses == ['status1', 'status2']
        scm.get_last_commits_from_pull_request(42)
    else:
        with pytest.raises(SCMError):
            scm.get_pull_request(42)

        with pytest.raises(SCMError):
            scm.get_commit_message_modified_files_on_pull_request(42)

    if fail["status"] != 201 or fail["exc"] is True:
        with pytest.raises(SCMError) as excinfo:
            scm.set_tag_and_release("tag_name", "tag_message", "release_name", "patch_note", "commit_id")

            if fail["status"] != 201:
                assert str(excinfo) == "SCMError: The tag or the release can't be created"
    else:
        response = scm.set_tag_and_release("tag_name", "tag_message", "release_name", "patch_note", "commit_id")

        assert response.raw_headers.has_key("status")
        assert response.raw_headers["status"] == "201 Created"


def test_fetch_github_file(mocker):
    mocker.patch("loktar.scm.requests")
    mocker.patch("loktar.scm.StringIO")

    fetch_github_file("https://github.com/foo/bar/titi", "MY_AWESOME_TOKEN")
