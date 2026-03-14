class StrategyEngine:

    def __init__(self, telegram):

        self.telegram = telegram

        self.history = []

        self.waiting_result = False
        self.current_signal = None

        self.gale = 0
        self.max_gale = 2

        self.wins = 0
        self.loss = 0
        self.whites = 0


    def process_result(self, color):

        self.history.insert(0, color)

        if len(self.history) > 20:
            self.history.pop()

        print("📜 Histórico:", self.history)

        if self.waiting_result:
            self.check_result(color)

        if not self.waiting_result:
            self.analyze()


    # ==============================
    # ANALISE DAS ESTRATÉGIAS
    # ==============================

    def analyze(self):

        history = [c for c in self.history if c != "white"]

        if len(history) < 4:
            return

        a = history[0]
        b = history[1]
        c = history[2]
        d = history[3]

        # ==========================
        # Estratégia 1
        # QUEBRA DE SEQUÊNCIA
        # ==========================

        if a == b == c:

            print("🎯 Estratégia: Break Streak")

            if a == "red":
                self.send_signal("black")

            if a == "black":
                self.send_signal("red")

            return

        # ==========================
        # Estratégia 2
        # ALTERNÂNCIA
        # red black red black
        # ==========================

        if a != b and b != c and c != d:

            print("🎯 Estratégia: Alternation")

            if a == "red":
                self.send_signal("black")

            else:
                self.send_signal("red")

            return

        # ==========================
        # Estratégia 3
        # DUPLA REPETIÇÃO
        # red red black black
        # ==========================

        if a == b and c == d and a != c:

            print("🎯 Estratégia: Double Repeat")

            self.send_signal(a)

            return


    # ==============================
    # ENVIO DE SINAL
    # ==============================

    def send_signal(self, color):

        self.current_signal = color
        self.waiting_result = True
        self.gale = 0

        last = self.history[0]

        if last == "red":
            last_text = "🔴 RED"

        elif last == "black":
            last_text = "⚫ BLACK"

        else:
            last_text = "⚪ WHITE"


        msg = (
            "🚨 ENTRADA CONFIRMADA\n\n"
            "🎰 Blaze Double\n\n"
            f"📊 Último resultado: {last_text}\n\n"
            f"🎯 Apostar em: {'🔴 RED' if color == 'red' else '⚫ BLACK'}\n\n"
            "🛡 Proteção: ⚪ White\n"
            "🎲 Até 2 Gales"
        )

        print("📡 SINAL ENVIADO")

        self.telegram.send(msg)


    # ==============================
    # CHECAR RESULTADO
    # ==============================

    def check_result(self, color):

        if color == "white":

            print("⚪ WHITE HIT")

            self.telegram.send("⚪ WHITE HIT")

            self.whites += 1
            self.wins += 1

            self.send_score()

            self.reset()

            return


        if color == self.current_signal:

            print("✅ WIN")

            self.telegram.send("✅ WIN")

            self.wins += 1

            self.send_score()

            self.reset()

            return


        if self.gale < self.max_gale:

            self.gale += 1

            print("⚠️ GALE", self.gale)

            self.telegram.send(
                f"⚠️ GALE {self.gale}\nManter entrada em {'🔴 RED' if self.current_signal == 'red' else '⚫ BLACK'}"
            )

            return


        print("❌ RED")

        self.telegram.send("❌ RED")

        self.loss += 1

        self.send_score()

        self.reset()


    # ==============================
    # PLACAR
    # ==============================

    def send_score(self):

        total = self.wins + self.loss

        if total == 0:
            accuracy = 0
        else:
            accuracy = round((self.wins / total) * 100)

        msg = (
            "🏆 PLACAR DO BOT\n\n"
            f"✅ Wins: {self.wins}\n"
            f"⚪ Whites: {self.whites}\n"
            f"❌ Reds: {self.loss}\n\n"
            f"📈 Assertividade: {accuracy}%"
        )

        print(msg)

        self.telegram.send(msg)


    # ==============================
    # RESET
    # ==============================

    def reset(self):

        self.waiting_result = False
        self.current_signal = None
        self.gale = 0
