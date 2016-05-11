import datetime
import sys


class Log(object):
    def __init__(self):
        self.color = {
            "warning": "\033[93m",
            "error": "\033[91m",
            "end": "\033[0m",
        }

    def info(self, msg):
        self._print_console(msg, "info")

    def error(self, msg):
        self._print_console(msg, "error")

    def warning(self, msg):
        self._print_console(msg, "warning")

    def _print_console(self, msg, log_level):
        """Print a regular message to console"""
        if log_level == 'info':
            begin = ''
            end = ''
        elif log_level == 'error':
            begin = self.color["error"]
            end = self.color["end"]
        else:
            begin = self.color["warning"]
            end = self.color["end"]

        sys.stdout.write("{0}[{1}] {2}{3}\n".format(begin,
                                                    datetime.datetime.now(),
                                                    msg,
                                                    end))
        sys.stdout.flush()
