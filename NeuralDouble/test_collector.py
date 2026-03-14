from listener.blaze_dom_listener import start_listener
import time

history = []


def process_result(color):

    history.insert(0, color)

    if len(history) > 20:
        history.pop()

    print("📜 Histórico atual:", history)


class Engine:

    def process_result(self, color):

        process_result(color)


print("🧪 Testando coletor...")

engine = Engine()

start_listener(engine)

# mantém script rodando
while True:
    time.sleep(1)
