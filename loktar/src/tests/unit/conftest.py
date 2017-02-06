from github import GithubException
from mock import MagicMock
import pytest
from uuid import uuid4


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


class Release(object):
    def __init__(self, fail):
        if fail["status"] == 201 and fail["exc"] is False:
            self.raw_headers = {
                "status": "201 Created"
            }
        else:
            if fail["status"] == 400:
                self.raw_headers = {
                    "status": "400 blabla"
                }
            else:
                raise GithubException("", "")


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
            return Release(self.fail)


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


class FakeElasticSearch(object):
    def __init__(self, *args, **kwargs):
        self.runs = list()

    def index(self, *args, **kwargs):
        run_id = str(uuid4())
        self.runs.append({
            u'_type': kwargs.get("doc_type"),
            u'_source': kwargs.get("body"),
            u'_index': kwargs.get("index"),
            u'_version': 1,
            u'found': True,
            u'_id': run_id
        })

        return {
            u'_type': kwargs.get("type"),
            u'created': True,
            u'_shards': {
                u'successful': 1,
                u'failed': 0,
                u'total': 2
            },
            u'_version': 1,
            u'_index': kwargs.get("index"),
            u'_id': run_id
        }

    def get(self, *args, **kwargs):
        for run in self.runs:
            if run["_id"] == kwargs.get("id"):
                return run

    def search(self, *args, **kwargs):
        return {
            u'hits': {
                u'hits': self.runs,
                u'total': len(self.runs),
                u'max_score': 1.0
            },
            u'_shards': {u'successful': 5, u'failed': 0, u'total': 5},
            u'took': 89,
            u'timed_out': False
        }
