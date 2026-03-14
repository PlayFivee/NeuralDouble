from strategies.base_strategy import BaseStrategy

class DoubleRepeatStrategy(BaseStrategy):

    name = "double_repeat"

    def analyze(self, history):

        if len(history) < 4:
            return None

        h = history[:4]

        if h[0] == h[1] and h[2] == h[3]:
            return h[0]

        return None