from github import Github

from loktar.decorators import retry
from loktar.environment import GITHUB_INFO
from loktar.log import Log


@retry
def define_job_status_on_github_commit(commit_id, state, target_url, context, description=None, user=None, password=None, organization=None, repository=None):
    """Define the status of a job on a Github commit.

    Args:
        commit_id (str or int): SHA or commit id.
        state: One of 'pending', 'success', 'error', 'failure'.
        target_url (str): the URL that can be clicked in the Pull Request.
        context: The header of the status.
        description (Optional[str]): Optional description. Defaults according to ``state``.
        user (str, None): the user who post the status
        password (str, None): the user password
        organization (str, None): the organization of the repository target
        repository (str, None): the repository target
    """
    logger = Log()
    if commit_id is not None:
        connexion = Github(GITHUB_INFO['login']['user'] if GITHUB_INFO['login']['user'] is not None else user,
                           GITHUB_INFO['login']['password']
                           if GITHUB_INFO['login']['password'] is not None else
                           password)

        repository = connexion.get_organization(GITHUB_INFO['organization']
                                                if GITHUB_INFO['organization'] is not None else
                                                organization)\
                              .get_repo(GITHUB_INFO['repository']
                                        if GITHUB_INFO['repository'] is not None else
                                        repository)

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
