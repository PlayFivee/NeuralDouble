class BaseStrategy:

    name = "base"

    def analyze(self, history):
        raise NotImplementedError