class TrendAnalyzer:

    def get_trend(self, history):

        if len(history) < 12:
            return None

        last = history[:12]

        red = last.count("red")
        black = last.count("black")

        if red >= 8:
            return "red"

        if black >= 8:
            return "black"

        return None