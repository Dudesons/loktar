from github import Github
from slacker import Error
from slacker import Slacker

from loktar.decorators import retry
from loktar.constants import GITHUB_INFO
from loktar.constants import SLACK
from loktar.exceptions import NotificationError
from loktar.log import Log

logger = Log()


@retry
def define_job_status_on_github_commit(commit_id,
                                       state,
                                       target_url,
                                       context,
                                       description=None,
                                       user=None,
                                       password=None,
                                       organization=None,
                                       repository=None):
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


@retry
def send_message_to_slack(message, **kwargs):
    """Send a message to a slack channel

        Args:
            message (str): this is the message to send to slack

        Keyword Args:
            token (str): this is the slack token it can provide from environment variable or the kwargs
            channel(str): this is the slack channel it can provide from environment variable or the kwargs

        Raises:
            NotificationError: this is raised when the token or the channel are not set or an environment problem

        Returns:
            If all is good the function return the response from slack
            example:
                {
                    "channel": "my chan",
                    "message":
                            {
                                "bot_id": "BOT ID",
                                "sbtype": "bot_message",
                                "text": "Hello World",
                                "ts": "1468242279.000003",
                                "type": "message",
                                "username": "bot"
                            },
                    "ok": True,
                    "ts": "1468242279.000003"
                }
    """
    slack_client = Slacker(SLACK["token"] if SLACK["token"] else kwargs.get("token", None))

    try:
        response = slack_client.chat.post_message(
            kwargs.get("channel") if kwargs.get("channel", None) else SLACK["channel"],
            message
        )

        assert response.successful is True
    except Error as e:
        logger.error("Error for sending message to slack because : {0}".format(str(e)))
        raise NotificationError(str(e))
    except AssertionError:
        logger.error("Unknown error for sending message to slack : {0}".format(response.body))
        raise NotificationError(response.body)

    logger.info("Message sent to slack")
    return response.body
