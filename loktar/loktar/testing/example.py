from loktar.testing.plugin import ComplexPlugin


class Example(ComplexPlugin):
    def __init__(self):
        ComplexPlugin.__init__(self, __file__.split(".")[0])
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
    test = Example()
    test.run()
