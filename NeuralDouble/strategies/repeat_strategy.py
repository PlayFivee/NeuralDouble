from strategies.base_strategy import BaseStrategy

class RepeatStrategy(BaseStrategy):

    name = "repeat"

    def analyze(self, history):

        if len(history) < 2:
            return None

        if history[0] == history[1]:
            return history[0]

        return None