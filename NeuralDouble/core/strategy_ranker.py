class StrategyRanker:

    def __init__(self):

        self.stats = {}

        self.window = 200

        self.history = []

    def record_result(self, strategy, win):

        self.history.append((strategy, win))

        if len(self.history) > self.window:
            self.history.pop(0)

        self.recalculate()

    def recalculate(self):

        self.stats = {}

        for strategy, win in self.history:

            if strategy not in self.stats:

                self.stats[strategy] = {
                    "wins": 0,
                    "losses": 0
                }

            if win:
                self.stats[strategy]["wins"] += 1
            else:
                self.stats[strategy]["losses"] += 1

    def get_winrate(self, strategy):

        data = self.stats.get(strategy)

        if not data:
            return 0

        total = data["wins"] + data["losses"]

        if total == 0:
            return 0

        return data["wins"] / total
