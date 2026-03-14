history = []


def convert_color(roll):

    if roll == 0:
        return "white"
    elif roll <= 7:
        return "red"
    else:
        return "black"


def add_result(result):

    color = convert_color(result["roll"])

    history.insert(0, color)
    history[:] = history[:20]

    return color


def get_history():
    return history.copy()