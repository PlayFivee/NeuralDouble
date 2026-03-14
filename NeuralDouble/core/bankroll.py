bankroll = 100
bet_size = 2


def win():

    global bankroll
    bankroll += bet_size

    print("WIN | banca:", bankroll)


def loss():

    global bankroll
    bankroll -= bet_size

    print("LOSS | banca:", bankroll)