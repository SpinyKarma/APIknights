from pprint import pprint


class Debug:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def __call__(self, *args, **kwargs):
        if self.enabled:
            for item in args:
                pprint(item, **kwargs)

    def warn(self, *args, **kwargs):
        self.__call__(
            *["\x1b[93m" + str(arg) + "\x1b[0m" for arg in args],
            **kwargs
        )

    def err(self, *args, **kwargs):
        self.__call__(
            *["\x1b[91m" + str(arg) + "\x1b[0m" for arg in args],
            **kwargs
        )

    def on(self):
        self.enabled = True

    def off(self):
        self.enabled = False

    def switch(self):
        self.enabled = not self.enabled
