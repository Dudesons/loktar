from github import Github as GitHub
import requests
import StringIO

from loktar.decorators import retry
from loktar.log import Log

logger = Log()


class Github(object):
    """Wrapper for the github3 library

    Args:
        login (str): login for GitHub
        password (str): password for GitHub
    """

    def __init__(self, login, password):
        self._connexion = GitHub(login, password)
        self._repository = self._connexion.get_organization('loktar-ci').get_repo('loktar_test')
        # Used for cache
        self.pull_requests_cache = {}
        self.logger = Log()

    @retry
    def search_pull_request_id(self, branch):
        """Look for an open pull request id given a branch

        Args:
            branch (str): name of the branch

        Returns:
            int or None: the id of the pull request or None
        """
        pr_id = None
        for pr in self.get_pull_requests(state='open'):
            self.logger.info('Looking at branch {0}'.format(pr.head.ref))
            if pr.head.ref == branch:
                self.logger.info('Found pull request {0} with id {1}'.format(pr, pr.number))
                pr_id = pr.number
                break
        return pr_id

    @retry
    def get_pull_requests(self, state='open', use_cache=False):
        """Get a pull request from the GitHub API

        Args:
            state (str): State of the pull request
            use_cache (Optional[bool]): If True, only return cached pull requests. Otherwise, make another request.

        Returns:
            a list of PullRequest instance
        """
        if use_cache and self.pull_requests_cache:
            pull_requests = self.pull_requests_cache
        else:
            pull_requests = self._repository.get_pulls(state=state)
            self._cache_pull_requests(pull_requests)
        return pull_requests

    def _cache_pull_requests(self, pull_requests=None):
        """Cache a list of pull requests

        Args:
            pull_requests (list of github.pullrequest.PullRequest)
        """
        for pull_request in pull_requests:
            self.pull_requests_cache[pull_request.number] = pull_request

    @retry
    def get_pull_request(self, pull_request_id, use_cache=True):
        """Get a pull request from the GitHub API

        Args:
            pull_request_id (int): ID of the pull request
            use_cache (Optional[bool]): If True, only return cached pull requests. Otherwise, make another request.
                If we cannot find the pull request in the cache, we make another request.

        Returns:
            a PullRequest instance
        """
        if use_cache and pull_request_id in self.pull_requests_cache:
            pull_request = self.pull_requests_cache[pull_request_id]
        else:
            pull_request = self._repository.get_pull(pull_request_id)
            self._cache_pull_requests([pull_request])
        return pull_request

    @retry
    def get_commit_message_modified_files_on_pull_request(self, pull_request_id):
        """Retrieve the commit messages from the pull request and associate the modified files for it.

        Args:
            pull_request_id (int): ID of the pull request

        Returns:
            dict of str: list: Comments of the commits linked to the pull request are keys, modified files are values.
        """
        pr = self.get_pull_request(pull_request_id)
        commits = pr.get_commits()
        # Return message: files
        dict_message_files = {}
        for commit in commits:
            dict_message_files.setdefault(commit.commit.message, [])
            dict_message_files[commit.commit.message].extend(map(lambda file_: file_.filename, commit.files))
        return dict_message_files

    @retry
    def get_git_branch_from_pull_request(self, pull_request_id):
        """Retrieve the branch name from the pull request id

        Args:
            pull_request_id (int): ID of the pull request

        Returns:
            A branch name
        """
        pr = self.get_pull_request(pull_request_id)
        return pr.head.ref

    @retry
    def get_last_statuses_from_pull_request(self, pull_request_id, exclude_head=True):
        """Get the statuses from a pull request ID.

        Args:
            pull_request_id (int): ID of the pull request
            exclude_head (bool): If True, skip the head commit

        Returns:
            a tuple of github.Commit, list of github.CommitStatus.CommitStatus: List of statuses.
                Empty if no status was found.
        """
        pr = self.get_pull_request(pull_request_id)
        for commit in pr.get_commits().reversed:
            if exclude_head and commit.sha == pr.head.sha:
                continue
            statuses = list(commit.get_statuses())
            if statuses:
                return commit, statuses
        return None, []

    @retry
    def get_last_commits_from_pull_request(self, pull_request_id, until_commit=None):
        """Get the commit from a pull request ID.

        Args:
            pull_request_id (int): ID of the pull request
            until_commit (github.Commit.Commit): Stop at a specific commit (will be excluded)

        Returns:
            list of github.Commit.Commit: the last commits
        """
        commits = []

        pr = self.get_pull_request(pull_request_id)
        for commit in pr.get_commits().reversed:
            if until_commit is not None and commit.sha == until_commit.sha:
                break
            commits.append(commit)
        return commits

    @retry
    def create_pull_request_comment(self, pull_request_id, comment, check_unique=False):
        """Create an issue comment on the pull request

        Args:
            pull_request_id (int): ID of the pull request
            comment (basestring): Comment text to post
            check_unique (bool): If True do not comment if it has already been posted.

        Returns:
            github.IssueComment.IssueComment: The comment that was created
        """
        pr = self.get_pull_request(pull_request_id)
        if check_unique:
            issue_comments = pr.get_issue_comments()
            for issue_comment in issue_comments:
                if issue_comment.body == comment:
                    return
        return pr.create_issue_comment(comment)


@retry
def fetch_github_file(url, token):
    """Fetch a file from GitHub

    Args:
        url (str): URL the file is at.
        token (str): Authorization token for GitHub.

    Returns:
        str: the raw content of the file.
    """
    logger = Log()
    headers = {
        'Authorization': 'token {0}'.format(str(token)),
        'Accept': 'application/vnd.github.v3.raw',
    }
    logger.info('Fetching file at {0}'.format(url))
    req = requests.get(url, headers=headers, allow_redirects=True)
    m_file = StringIO.StringIO()
    m_file.write(req.content)
    return m_file.getvalue()
