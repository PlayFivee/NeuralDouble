import requests

TOKEN = "8678928317:AAHp72fPtBGNcpAyz-aYCdXNzoRt7_cKKUk"
CHAT_ID = "-1003811489628"


def send_message(text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:
        requests.post(url, data=data)
    except:
        print("Erro ao enviar Telegram")