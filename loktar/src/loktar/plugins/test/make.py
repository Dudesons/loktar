from loktar.plugin import SimplePlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        Make(args[0], args[1]).run()
    except IndexError:
        print(Make.__init__.__doc__)
        raise


class Make(SimplePlugin):
        def __init__(self, artifact_info, remote):
            """Plugin for launching test from a make file with make ci & make clean

                Args:
                    artifact_info (dict): Contains information about the package to execute inside the plugin
                    remote (bool): Define if the plugin will be execute in remote or not

            """
            SimplePlugin.__init__(self, artifact_info,
                                  {
                                      "command": {
                                          "run": "make ci",
                                          "clean": "make clean"
                                      }
                                  },
                                  remote=remote)

        def run(self):
            self._base_run()
            self._base_clean()
