class LoktarException(Exception):
    def __init__(self, message, *args):
        Exception.__init__(self, message, *args)
        self.reason = message

    def __str__(self):
        return "{}: {}".format(type(self).__name__, self.reason)


class CIJobFail(LoktarException):
    """Generic CI fail"""


class PrepareEnvFail(LoktarException):
    """Exception raised by a fail during environment preparation"""


class CITestFail(LoktarException):
    """Exception raised by a a fail during tests"""


class CITestUnknown(LoktarException):
    """Exception raised when the test is unknown"""


class CIBuildPackageFail(LoktarException):
    """Exception raised when the build fails"""


class CIPackageUnknown(LoktarException):
    """Exception raised when the package is unknown"""


class HTTPErrorCode(LoktarException):
    """Exception raised by a failed call on Failed HTTP Requests"""


class GitHubAPIFail(LoktarException):
    """Exception raised by a failed call on Github API"""


class JobIdUnknown(LoktarException):
    """Exception raised by a job id unknown"""


class PullRequestCollision(LoktarException):
    """Exception raised by a failed call on Github API"""


class FailDrawDepGraph(LoktarException):
    """Exception raised by a failed call on internal gplot function"""


class ForbiddenTimelineKey(LoktarException):
    """Exception raised by conflict key in complex plugin"""


class SimplePluginErrorConfiguration(LoktarException):
    """Exception raised by configuration error in simple plugin"""


class ImportPluginError(LoktarException):
    """Exception raised by if the plugin doesn't exist"""


class UnknownStorageMethod(LoktarException):
    """Exception raised by if the storage method doesn't exist"""


class NotificationError(LoktarException):
    """Exception raised by if the storage method doesn't exist"""


class SCMError(LoktarException):
    """Exception raised when an error is encountered with scm system"""


class GuayError(LoktarException):
    """Exception raised when an error is encountered with Guay build system"""


class StorageProxyError(LoktarException):
    """Exception raised when an error is encountered with storage proxy system"""
