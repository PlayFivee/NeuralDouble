from core.event_queue import event_queue
from core.history_manager import add_result, get_history
from strategies.example_strategy import check


def start_worker():

    print("Worker iniciado")

    while True:

        result = event_queue.get()

        color = add_result(result)

        history = get_history()

        signal = check(history)

        print("Rodada:", color)

        if signal:
            print("SINAL:", signal)