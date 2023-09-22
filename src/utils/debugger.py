from pprint import pprint


class Debug:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def __call__(self, *args, **kwargs):
        if self.enabled:
            for item in args:
                pprint(item, **kwargs)

    def warn(self, *args):
        if self.enabled:
            self.__call__(["\033[93m" + str(arg) + "\033[0m" for arg in args])

    def err(self, *args):
        if self.enabled:
            self.__call__(["\033[91m" + str(arg) + "\033[0m" for arg in args])

    def on(self):
        self.enabled = True

    def off(self):
        self.enabled = False

    def switch(self):
        self.enabled = not self.enabled
