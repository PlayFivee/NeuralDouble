from core.pattern_detector import PatternDetector


class StrategyEngine:

    def __init__(self, telegram):

        self.telegram = telegram

        self.history = []

        self.detector = PatternDetector()

        self.waiting_result = False
        self.current_signal = None

        self.gale = 0
        self.max_gale = 2

        self.cooldown = 0
        self.cooldown_rounds = 2

        self.wins = 0
        self.loss = 0
        self.whites = 0


    def process_result(self, color):

        self.history.insert(0, color)

        if len(self.history) > 30:
            self.history.pop()

        print("📜 Histórico:", self.history)

        if self.cooldown > 0:
            self.cooldown -= 1

        if self.waiting_result:
            self.check_result(color)

        if not self.waiting_result and self.cooldown == 0:
            self.analyze()


    # =============================
    # ANALISE
    # =============================

    def analyze(self):

        history = [c for c in self.history if c != "white"]

        if len(history) < 6:
            return

        pattern = self.detector.detect(history)

        print("🧠 Padrão detectado:", pattern)

        a = history[0]
        b = history[1]
        c = history[2]
        d = history[3]

        # =========================
        # Alternância
        # =========================

        if pattern == "alternating":

            if a != b and b != c and c != d:

                print("🎯 Estratégia Alternation")

                if a == "red":
                    self.send_signal("black")
                else:
                    self.send_signal("red")

                return

        # =========================
        # Blocos
        # =========================

        if pattern == "blocks":

            if a == b and c == d and a != c:

                print("🎯 Estratégia Double Repeat")

                self.send_signal(a)

                return

        # =========================
        # Tendência
        # =========================

        if pattern == "red_trend":

            if a == b == c:

                print("🎯 Contra Tendência")

                self.send_signal("black")

                return

        if pattern == "black_trend":

            if a == b == c:

                print("🎯 Contra Tendência")

                self.send_signal("red")

                return


    # =============================
    # ENVIAR SINAL
    # =============================

    def send_signal(self, color):

        self.current_signal = color
        self.waiting_result = True

        self.cooldown = self.cooldown_rounds

        self.gale = 0

        msg = (
            "🚨 ENTRADA CONFIRMADA\n\n"
            f"🎯 Apostar em {'🔴 RED' if color == 'red' else '⚫ BLACK'}\n"
            "🛡 Proteção: WHITE\n"
            "🎲 Até 2 Gales"
        )

        print("📡 SINAL ENVIADO")

        self.telegram.send(msg)


    # =============================
    # RESULTADO
    # =============================

    def check_result(self, color):

        if color == "white":

            self.whites += 1
            self.wins += 1

            print("⚪ WHITE HIT")

            self.telegram.send("⚪ WHITE HIT")

            self.reset()

            return

        if color == self.current_signal:

            self.wins += 1

            print("✅ WIN")

            self.telegram.send("✅ WIN")

            self.reset()

            return

        if self.gale < self.max_gale:

            self.gale += 1

            print("⚠️ GALE", self.gale)

            self.telegram.send(
                f"⚠️ GALE {self.gale}\nManter entrada"
            )

            return

        print("❌ RED")

        self.loss += 1

        self.telegram.send("❌ RED")

        self.reset()


    def reset(self):

        self.waiting_result = False
        self.current_signal = None
        self.gale = 0
