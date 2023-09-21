from pprint import pprint


class Debug:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def __call__(self, *args, **kwargs):
        if self.enabled:
            for item in args:
                pprint(item, **kwargs)
    
    def warn(self, arg):
        if self.enabled:
            print("\033[93m" + arg + "\033[0m")

    def err(self, arg):
        if self.enabled:
            print("\033[91m" + arg + "\033[0m")

    def on(self):
        self.enabled = True

    def off(self):
        self.enabled = False

    def switch(self):
        self.enabled = not self.enabled
