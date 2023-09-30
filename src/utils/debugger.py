from pprint import pprint


class Debug:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def __call__(self, *args, **kwargs):
        if self.enabled:
            for item in args:
                pprint(item, **kwargs)
            print()

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

    def x(self, *args, **kwargs):
        pass

    def on(self, *args, **kwargs):
        self.enabled = True
        self(*args, **kwargs)

    def off(self):
        self.enabled = False

    def switch(self):
        self.enabled = not self.enabled
