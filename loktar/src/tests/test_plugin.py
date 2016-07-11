import pytest

from loktar.exceptions import CITestFail
from loktar.exceptions import ForbiddenTimelineKey
from loktar.exceptions import ImportPluginError
from loktar.exceptions import SimplePluginErrorConfiguration
from loktar.plugin import ComplexPlugin
from loktar.plugin import find_plugin


@pytest.fixture
def example_plugin():
    class Example(ComplexPlugin):
            def __init__(self, package_info):
                ComplexPlugin.__init__(self,
                                       package_info,
                                       {
                                           "command": {
                                               "run": None,
                                               "clean": "make clean"
                                           }
                                       })
                self.timeline = {
                    0: self.check_requirements,
                    80: self.parse
                }

            def run(self):
                self._run()

            def check_requirements(self):
                print("itit")

            def parse(self):
                print("tutu")

    return Example


@pytest.fixture()
def example_plugin_bad():
    class Example(ComplexPlugin):
            def __init__(self, package_info):
                ComplexPlugin.__init__(self,
                                       package_info,
                                       {
                                           "command": {
                                               "clean": "make clean"
                                           }
                                       })

            def run(self):
                self._run()

    return Example


@pytest.mark.parametrize("package_info", [{"pkg_name": "toto"}, {"pkg_name": "toto", "package_location": "/tmp"}])
def test_complex_plugin(mocker, example_plugin, package_info):
    mocker.patch("loktar.plugin.lcd")
    mocker.patch("loktar.plugin.exe")

    test = example_plugin(package_info)
    test.run()


def test_complex_plugin_fail_test_command(mocker, example_plugin):
    mocker.patch("loktar.plugin.lcd")
    mocker.patch("loktar.plugin.exe", return_value=False)

    with pytest.raises(CITestFail):
        test = example_plugin({"pkg_name": "toto"})
        test.run()


def test_complex_plugin_fail_simple_plugin_error_configuration(mocker, example_plugin_bad):
    mocker.patch("loktar.plugin.lcd")
    mocker.patch("loktar.plugin.exe")

    with pytest.raises(SimplePluginErrorConfiguration):
        test = example_plugin_bad({"pkg_name": "toto"})
        test.run()


def test_complex_plugin_fail_forbidden_timeline_key(mocker, example_plugin):
    mocker.patch("loktar.plugin.lcd")
    mocker.patch("loktar.plugin.exe")

    test = example_plugin({"pkg_name": "toto"})
    test.timeline[50] = lambda x: x
    with pytest.raises(ForbiddenTimelineKey):
        test.run()


def test_find_plugin(mocker):
    mocker.patch("loktar.plugin.importlib")
    find_plugin("foo", ["/tmp/bar", "/toto/tutu"])


def test_find_plugin_failed_on_first_import_but_find_a_plugin_in_plugin_path(mocker):
    def fake_import(*args, **kwargs):
        if "loktar" in args[0]:
            raise ImportError

    mocker.patch("loktar.plugin.importlib.import_module", side_effect=fake_import)
    find_plugin("foo", ["/tmp/bar", "/toto/tutu"])


def test_find_plugin_failed_on_all_import(mocker):
    def fake_import(*args, **kwargs):
        raise ImportError

    mocker.patch("loktar.plugin.importlib.import_module", side_effect=fake_import)
    with pytest.raises(ImportPluginError):
        find_plugin("foo", ["/tmp/bar", "/toto/tutu"])
