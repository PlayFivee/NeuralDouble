import time


class RoundManager:

    def __init__(self):

        self.last_round = 0
        self.interval = 15


    def new_round(self):

        now = time.time()

        if now - self.last_round > self.interval:

            self.last_round = now
            return True

        return False
