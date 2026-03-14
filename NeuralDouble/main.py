from telegram_bot.telegram_bot import TelegramBot
from listener.blaze_dom_listener import start_listener
from engine.strategy_engine import StrategyEngine
import time


print("🚀 NeuralDouble iniciado")


# ==============================
# CONFIG TELEGRAM
# ==============================

TOKEN = "8678928317:AAHp72fPtBGNcpAyz-aYCdXNzoRt7_cKKUk"
CHAT_ID = "-1003811489628"


# ==============================
# INICIA TELEGRAM
# ==============================

telegram = TelegramBot(TOKEN, CHAT_ID)


# ==============================
# INICIA ENGINE
# ==============================

engine = StrategyEngine(telegram)


# ==============================
# INICIA LISTENER
# ==============================

start_listener(engine)

print("🎧 Listener iniciado")


# ==============================
# LOOP PARA MANTER BOT ATIVO
# ==============================

while True:
    time.sleep(1)
