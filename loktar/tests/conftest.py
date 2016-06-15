import pytest


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    def mockreturn(*args, **kwargs):
        return True

    monkeypatch.setattr("time.sleep", lambda x: mockreturn)

@pytest.fixture(autouse=True)
def no_exit(monkeypatch):
    monkeypatch.setattr("sys.exit", lambda x: False if x else True)