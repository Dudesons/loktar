import pytest


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    def mockreturn(*args, **kwargs):
        return True

    monkeypatch.setattr("time.sleep", lambda x: mockreturn)
