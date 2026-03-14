def unstable_pattern(history):

    if len(history) < 6:
        return False

    switches = 0

    for i in range(5):
        if history[i] != history[i+1]:
            switches += 1

    return switches >= 4


def trend_follow(history):

    if len(history) < 5:
        return None

    if "white" in history[:5]:
        return None

    last5 = history[:5]

    red = last5.count("red")
    black = last5.count("black")

    if red >= 4:
        return "red"

    if black >= 4:
        return "black"

    return None


def momentum_entry(history):

    if len(history) < 4:
        return None

    if "white" in history[:4]:
        return None

    if history[0] == history[1] and history[1] == history[2]:

        return history[0]

    return None


def micro_pullback(history):

    if len(history) < 4:
        return None

    if "white" in history[:4]:
        return None

    if history[0] == history[1] and history[2] != history[1]:

        return history[0]

    return None


STRATEGIES = {
    "trend_follow": trend_follow,
    "momentum_entry": momentum_entry,
    "micro_pullback": micro_pullback
}


def analyze(history):

    if not history:
        return []

    if unstable_pattern(history):
        return []

    signals = []

    for name, strategy in STRATEGIES.items():

        result = strategy(history)

        if result:

            signals.append({
                "strategy": name,
                "bet": result
            })

    return signals
