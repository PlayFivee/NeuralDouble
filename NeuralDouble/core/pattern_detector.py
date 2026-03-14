class PatternDetector:

    def detect(self, history):

        if len(history) < 10:
            return "neutral"

        last10 = history[:10]

        red = last10.count("red")
        black = last10.count("black")

        # =========================
        # Tendência forte
        # =========================

        if red >= 7:
            return "red_trend"

        if black >= 7:
            return "black_trend"

        # =========================
        # Alternância
        # =========================

        alternations = 0

        for i in range(len(last10) - 1):

            if last10[i] != last10[i + 1]:
                alternations += 1

        if alternations >= 7:
            return "alternating"

        # =========================
        # Blocos
        # =========================

        pairs = 0

        for i in range(0, len(last10) - 1, 2):

            if last10[i] == last10[i + 1]:
                pairs += 1

        if pairs >= 3:
            return "blocks"

        return "neutral"