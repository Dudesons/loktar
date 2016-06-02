from loktar.plugin import ComplexPlugin


def run(*args, **kwargs):
    Make(args[0]).run()


class Make(ComplexPlugin):
        def __init__(self, package_info):
            ComplexPlugin.__init__(self, package_info,
                                   {
                                       "command": {
                                           "run": "make ci",
                                           "clean": "make clean"
                                       }
                                   })
            self.timeline = {
                60: self.get_results,
            }

        def run(self):
            self._run(self.timeline)

        def get_results(self):
            print 'ToDo'

