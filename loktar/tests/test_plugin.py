import pytest

from loktar.exceptions import CITestFail
from loktar.exceptions import ForbiddenTimelineKey
from loktar.exceptions import SimplePluginErrorConfiguration
from loktar.testing.plugin import ComplexPlugin


class Example(ComplexPlugin):
        def __init__(self, package_info):
            ComplexPlugin.__init__(self, package_info)
            self.timeline = {
                0: self.check_requirements,
                80: self.parse
            }

        def run(self):
            self._run(self.timeline)

        def check_requirements(self):
            print("itit")

        def parse(self):
            print('tutu')


def test_complex_plugin(mocker):
    mocker.patch('loktar.testing.plugin.lcd')
    mocker.patch('loktar.testing.plugin.exe')

    test = Example({'pkg_name': 'toto'})
    test.run()


def test_complex_plugin_fail_test_command(mocker):
    mocker.patch('loktar.testing.plugin.lcd')
    mocker.patch('loktar.testing.plugin.exe', return_value=False)

    with pytest.raises(CITestFail):
        test = Example({'pkg_name': 'toto'})
        test.run()


def test_complex_plugin_fail_simple_plugin_error_configuration(mocker):
    mocker.patch('loktar.testing.plugin.lcd')
    mocker.patch('loktar.testing.plugin.exe')
    mocker.patch('loktar.testing.plugin.yaml.load', return_value={'foo': 'bar'})

    with pytest.raises(SimplePluginErrorConfiguration):
        test = Example({'pkg_name': 'toto'})
        test.run()


def test_complex_plugin_fail_forbidden_timeline_key(mocker):
    mocker.patch('loktar.testing.plugin.lcd')
    mocker.patch('loktar.testing.plugin.exe')

    test = Example({'pkg_name': 'toto'})
    test.timeline[50] = lambda x: x
    with pytest.raises(ForbiddenTimelineKey):
        test.run()
