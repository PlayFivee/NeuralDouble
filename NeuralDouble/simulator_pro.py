import random
from strategies.strategy_selector import analyze

ROUNDS = 50000


def generate_spin(history):

    if not history:
        return random.choice(["red", "black"])

    last = history[0]

    r = random.random()

    # branco
    if r < 0.05:
        return "white"

    # repetir cor (streak)
    if r < 0.55:
        return last

    # alternância
    if last == "red":
        return "black"

    if last == "black":
        return "red"

    return random.choice(["red", "black"])


history = []

signals = 0
wins = 0
losses = 0

stats_by_strategy = {}


for i in range(ROUNDS):

    spin = generate_spin(history)

    history.insert(0, spin)

    if len(history) > 50:
        history.pop()

    signal = analyze(history)

    if signal:

        strategy_name = signal["strategy"]
        bet = signal["bet"]

        signals += 1

        if strategy_name not in stats_by_strategy:
            stats_by_strategy[strategy_name] = {
                "signals": 0,
                "wins": 0,
                "losses": 0
            }

        stats_by_strategy[strategy_name]["signals"] += 1

        next_spin = generate_spin(history)

        if bet == next_spin:

            wins += 1
            stats_by_strategy[strategy_name]["wins"] += 1

        else:

            losses += 1
            stats_by_strategy[strategy_name]["losses"] += 1


print("\n===== RESULTADO GERAL =====")

print("Rodadas simuladas:", ROUNDS)
print("Sinais:", signals)
print("Wins:", wins)
print("Losses:", losses)

if signals > 0:
    print("Winrate:", round((wins / signals) * 100, 2), "%")


print("\n===== ESTATÍSTICAS POR ESTRATÉGIA =====")

for name, data in stats_by_strategy.items():

    s = data["signals"]
    w = data["wins"]
    l = data["losses"]

    winrate = (w / s) * 100 if s > 0 else 0

    print("\nEstratégia:", name)
    print("Sinais:", s)
    print("Wins:", w)
    print("Losses:", l)
    print("Winrate:", round(winrate, 2), "%")
