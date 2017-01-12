from mock import MagicMock
import pytest

from conftest import FakeGithubRepo

from loktar.discovery import find_artifact_modified
from loktar.discovery import Github
from loktar.exceptions import PrepareEnvFail
from loktar.exceptions import SCMError


@pytest.mark.parametrize("git_branch", ["master", "killer-feature"])
@pytest.mark.parametrize("scm_type", ["github", "customscm"])
@pytest.mark.parametrize("ci_config", [{
  "packages": [
    {
      "artifact_type": "docker",
      "artifact_name": "pkg0",
      "pgk_dir": "dir0",
      "test_type": "make",
      "type": "service",
      "build_info": {
        "build_type": "url",
        "registry_type": "quay",
        "storage_type": "s3"
      }
    },
    {
      "artifact_type": "docker",
      "artifact_name": "pkg1",
      "test_type": "make",
      "type": "service",
      "build_info": {
        "build_type": "url",
        "registry_type": "quay",
        "storage_type": "s3"
      }
    },
    {
      "artifact_type": "whl",
      "artifact_name": "pkg2",
      "pgk_dir": "dir2/subdir2/",
      "test_type": "make",
      "type": "service"
    }
  ]
}])
@pytest.mark.parametrize("commit_id", ["commit_id"])
@pytest.mark.parametrize("pull_request_id", ["pull_request_id"])
@pytest.mark.parametrize("fail", [
    {"status": 201, "exc": False}
])
def test_find_artifact_modified(mock_github_obj, git_branch, scm_type, ci_config, commit_id, pull_request_id, fail):
    mock_github = mock_github_obj
    mock_github.return_value = FakeGithubRepo(fail)

    if scm_type == "customscm":
        with pytest.raises(PrepareEnvFail):
            find_artifact_modified(git_branch, scm_type, ci_config, commit_id=commit_id, pull_request_id=pull_request_id)
    else:
        find_artifact_modified(git_branch, scm_type, ci_config, commit_id=commit_id, pull_request_id=pull_request_id)


@pytest.mark.parametrize("git_branch", ["master", "killer-feature"])
@pytest.mark.parametrize("scm_type", ["github"])
@pytest.mark.parametrize("ci_config", [{
  "packages": [
    {
      "artifact_type": "docker",
      "artifact_name": "pkg0",
      "pgk_dir": "dir0",
      "test_type": "make",
      "type": "service",
      "build_info": {
        "build_type": "url",
        "registry_type": "quay",
        "storage_type": "s3"
      }
    },
    {
      "artifact_type": "docker",
      "artifact_name": "pkg1",
      "test_type": "make",
      "type": "service",
      "build_info": {
        "build_type": "url",
        "registry_type": "quay",
        "storage_type": "s3"
      }
    },
    {
      "artifact_type": "whl",
      "artifact_name": "pkg2",
      "pgk_dir": "dir2/subdir2/",
      "test_type": "make",
      "type": "service"
    }
  ]
}])
@pytest.mark.parametrize("commit_id", ["commit_id"])
@pytest.mark.parametrize("pull_request_id", ["pull_request_id"])
@pytest.mark.parametrize("fail", [
    {"status": 201, "exc": True}
])
def test_error_scm_find_artifact_modified(monkeypatch, mock_github_obj, git_branch,
                                          scm_type, ci_config, commit_id, pull_request_id, fail):

    def raiseSCMError(*args, **kwargs):
        raise SCMError("Epic scm error")

    mock_github = mock_github_obj
    mock_github.return_value = FakeGithubRepo(fail)

    monkeypatch.setattr(Github, "get_modified_files_from_commit", raiseSCMError)
    monkeypatch.setattr(Github, "get_modified_files_from_pull_request", raiseSCMError)

    with pytest.raises(SCMError):
        find_artifact_modified(git_branch, scm_type, ci_config, commit_id=commit_id, pull_request_id=pull_request_id)
