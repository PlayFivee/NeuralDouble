class HistoryService:

    def __init__(self):
        self.history = []

    def add_result(self, result):

        self.history.insert(0, result)

        if len(self.history) > 50:
            self.history.pop()

    def get_history(self):
        return self.history
