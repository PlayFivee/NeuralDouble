from config.settings import INITIAL_BANKROLL, BET_SIZE

class BankrollManager:

    def __init__(self):
        self.balance = INITIAL_BANKROLL
        self.bet_size = BET_SIZE

    def win(self):

        self.balance += self.bet_size
        print("WIN | saldo:", self.balance)

    def loss(self):

        self.balance -= self.bet_size
        print("LOSS | saldo:", self.balance)