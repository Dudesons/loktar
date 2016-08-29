import pytest
from slacker import Error

from loktar.exceptions import NotificationError
from loktar.notifications import define_job_status_on_github_commit
from loktar.notifications import send_message_to_slack


class FakeSlackMessageResponse(object):
    def __init__(self, chan, msg, *args, **kwargs):
        self.successful = True if msg != "Epic Fail" else False
        self.body = {
            "channel": chan,
            "message": {
                "bot_id": "BOT ID",
                "sbtype": "bot_message",
                "text": msg,
                "ts": "1468242279.000003",
                "type": "message",
                "username": "bot"
            },
            "ok": True,
            "ts": "1468242279.000003"
        }


class FakeSlackChan(object):
    def __init__(self, *args, **kwargs):
        pass

    def post_message(self, chan, msg, *args, **kwargs):
        if chan is None or msg is None:
            raise Error

        return FakeSlackMessageResponse(chan, msg)


class FakeSlack(object):
    def __init__(self, *args, **kwargs):
        self.chat = FakeSlackChan()


@pytest.mark.parametrize("state", ["pending", "success", "error", "failure", 'unknown status'])
@pytest.mark.parametrize("description", [None, "my awesome description", "a"*144])
@pytest.mark.parametrize("commit_id", ["4dq4d56q4dq65s", None])
def test_define_job_status_on_github_commit(mocker, commit_id, state, description):
    class Commit(object):
        def __init__(self, *args, **kwargs):
            pass

        def create_status(self, *args, **kwargs):
            return True

    class FakeRepo(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_commit(self, *args, **kwargs):
            return Commit()

    class FakeOrga(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_repo(self, *args, **kwargs):
            return FakeRepo()

    class FakeGithub(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_organization(self, *args, **kwargs):
            return FakeOrga()

    mocker.patch("loktar.notifications.Github", side_effect=FakeGithub)
    define_job_status_on_github_commit(commit_id,
                                       state,
                                       "www.example.com",
                                       "SUPER JOB ...",
                                       description)


@pytest.mark.parametrize("message", [None, "I am the best", "Epic Fail"])
@pytest.mark.parametrize("channel", ["fap chan", None])
def test_send_message_to_slack(mocker, message, channel):
    mocker.patch("loktar.notifications.Slacker", side_effect=FakeSlack)

    # One of the parameters are not set
    if message is None or channel is None:
        with pytest.raises(NotificationError):
            send_message_to_slack(message, channel=channel, token="Imba Token")
    else:
        # the message sent to slack fail ....
        if message == "Epic Fail":
            with pytest.raises(NotificationError):
                send_message_to_slack(message, channel=channel, token="Imba Token")
        # All is good
        else:
            r = send_message_to_slack(message, channel=channel, token="Imba Token")
            assert r["message"]["text"] == message
            assert r["channel"] == channel