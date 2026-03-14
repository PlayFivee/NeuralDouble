from strategies.base_strategy import BaseStrategy

class AlternationStrategy(BaseStrategy):

    name = "alternation"

    def analyze(self, history):

        if len(history) < 4:
            return None

        h = history[:4]

        if h == ["red","black","red","black"]:
            return "red"

        if h == ["black","red","black","red"]:
            return "black"

        return None