import pytest

from loktar.exceptions import ImportPluginError
from loktar.strategy_run import strategy_runner


@pytest.mark.parametrize("package", [
    {"pkg_type": "foo", "test_type": "bar", "depends_on": ["intranet"], "dependencies_type": ["python"]},
    {"pkg_type": "foo2", "test_type": "no-test", "depends_on": ["intranet"], "dependencies_type": ["python"]}
])
@pytest.mark.parametrize("run_type", ["test", "artifact", "dependency"])
@pytest.mark.parametrize("remote", [True, False])
def test_strategy_run(mocker, package, run_type, remote):
    class Fake(object):
        @staticmethod
        def run(*args, **kwargs):
            print("This is an awesome plugin")
            Fake(args[0], args[1])

        @staticmethod
        def Plugin(*args, **kwargs):
            print("In another plugin")
            if run_type == "dependency":
                return {"database"}

        def __init__(self, *args, **kwargs):
            print("Inside of this awesome plugin")

    mocker.patch("loktar.strategy_run.find_plugin", return_value=Fake)
    strategy_runner(package, run_type, remote=remote)


@pytest.mark.parametrize("package", [
    {"pkg_type": "foo", "test_type": "bar", "depends_on": ["intranet"], "dependencies_type": ["python"]}
])
def test_strategy_run_fail_on_value_error_run_type(package):
    with pytest.raises(ValueError):
        strategy_runner(package, "foo")


@pytest.mark.parametrize("package", [
    {"pkg_type": "foo", "test_type": "bar", "depends_on": ["intranet"], "dependencies_type": ["python"]}
])
@pytest.mark.parametrize("run_type", ["test", "artifact", "dependency"])
def test_strategy_run_fail_on_find_plugin(mocker, package, run_type):
    def fake_import(*args, **kwargs):
        raise ImportPluginError("fake import")

    mocker.patch("loktar.strategy_run.find_plugin", side_effect=fake_import)
    with pytest.raises(ImportPluginError):
        strategy_runner(package, run_type)


@pytest.mark.parametrize("package", [
    {"pkg_type": "foo", "test_type": "artifact", "depends_on": ["intranet"], "dependencies_type": ["python"]}
])
@pytest.mark.parametrize("run_type", ["test", "artifact", "dependency"])
def test_strategy_run_fail_on_runner(mocker, package, run_type):
    class Fake(object):
        def __init__(self, *args, **kwargs):
            pass

        @staticmethod
        def run(self):
            raise Exception

        def Plugin(self, *args, **kwargs):
            raise Exception

    mocker.patch("loktar.strategy_run.find_plugin", return_value=Fake)

    with pytest.raises(Exception):
        strategy_runner(package, run_type, "my_custom_plugins_dir")
