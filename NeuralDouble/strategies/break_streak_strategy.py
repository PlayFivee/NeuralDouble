from strategies.base_strategy import BaseStrategy

class BreakStreakStrategy(BaseStrategy):

    name = "break_streak"

    def analyze(self, history):

        if len(history) < 3:
            return None

        last3 = history[:3]

        if all(c == "red" for c in last3):
            return "black"

        if all(c == "black" for c in last3):
            return "red"

        return None