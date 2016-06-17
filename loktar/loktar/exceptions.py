class CIJobFail(Exception):
    """Generic CI fail"""


class PrepareEnvFail(Exception):
    """Exception raised by a fail during environment preparation"""


class CITestFail(Exception):
    """Exception raised by a a fail during tests"""


class CITestUnknown(Exception):
    """Exception raised when the test is unknown"""


class CIBuildPackageFail(Exception):
    """Exception raised when the build fails"""


class CIPackageUnknown(Exception):
    """Exception raised when the package is unknown"""


class HTTPErrorCode(Exception):
    """Exception raised by a failed call on Failed HTTP Requests"""


class GitHubAPIFail(Exception):
    """Exception raised by a failed call on Github API"""


class JobIdUnknown(Exception):
    """Exception raised by a job id unknown"""


class PullRequestCollision(Exception):
    """Exception raised by a failed call on Github API"""


class FailDrawDepGraph(Exception):
    """Exception raised by a failed call on internal gplot function"""


class ForbiddenTimelineKey(Exception):
    """Exception raised by conflict key in complex plugin"""


class SimplePluginErrorConfiguration(Exception):
    """Exception raised by configuration error in simple plugin"""


class ImportPluginError(Exception):
    """Exception raised by if the plugin doesn't exist"""


class UnknownStorageMethod(Exception):
    """Exception raised by if the storage method doesn't exist"""
