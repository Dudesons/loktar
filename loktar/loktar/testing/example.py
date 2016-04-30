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
        print "itit"

    def parse(self):
        print 'tutu'

if __name__ == "__main__":
    test = Example({'pkg_name': 'toto'})
    test.run()
