import requests
import threading


class TelegramBot:

    def __init__(self, token, chat_id):

        self.token = token
        self.chat_id = chat_id

        self.url = f"https://api.telegram.org/bot{token}/sendMessage"


    def send(self, message):

        # envia em thread para não bloquear
        thread = threading.Thread(
            target=self._send_request,
            args=(message,)
        )

        thread.daemon = True
        thread.start()


    def _send_request(self, message):

        try:

            requests.post(

                self.url,

                data={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },

                timeout=3
            )

        except Exception as e:

            print("Erro Telegram:", e)
