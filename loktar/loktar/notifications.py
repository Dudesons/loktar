from github import Github

from loktar.decorators import retry
from loktar.environment import GITHUB_INFO
from loktar.log import Log


@retry
def define_job_status_on_github_commit(commit_id, state, target_url, context, description=None):
    """Define the status of a job on a Github commit.

    Args:
        commit_id (str or int): SHA or commit id.
        state: One of 'pending', 'success', 'error', 'failure'.
        target_url (str): the URL that can be clicked in the Pull Request.
        context: The header of the status.
        description (Optional[str]): Optional description. Defaults according to ``state``.

    """
    logger = Log()
    if commit_id is not None:
        connexion = Github(GITHUB_INFO['login']['user'], GITHUB_INFO['login']['password'])
        repository = connexion.get_organization(GITHUB_INFO['organization']).get_repo(GITHUB_INFO['repository'])

        if description is None:
            if state == 'pending':
                description = GITHUB_INFO['notification']['pending']
            elif state == 'success':
                description = GITHUB_INFO['notification']['success']
            elif state == 'error':
                description = GITHUB_INFO['notification']['error']
            elif state == 'failure':
                description = GITHUB_INFO['notification']['failure']
            else:
                description = GITHUB_INFO['notification']['unknown']

        # Maximum length for description is 140 characters
        if len(description) > 140:
            description = description[:140 - 3] + '...'

        repository.get_commit(sha=commit_id).create_status(state=state,
                                                           target_url=target_url,
                                                           description=description,
                                                           context=context)

        logger.info('The job status is: {0}'.format(state))
    else:
        logger.info('Notifcation on github off')
