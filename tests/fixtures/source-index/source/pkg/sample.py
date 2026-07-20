DEFAULT_RATE = 24000


class SampleConfig:
    model_type = "sample"

    def __init__(self, width=16):
        self.width = width

    def describe(self):
        def closure():
            self.NOT_CONFIG = 1
        closure()
        return self.width


def build(config: SampleConfig):
    LOCAL_ONLY = 99
    return config.describe()


class DuplicateNames:
    @property
    def value(self):
        return 1

    @value.setter
    def value(self, new_value):
        self.current = new_value

    def overloaded(self, value: int):
        return value

    def overloaded(self, value: str):
        return value
