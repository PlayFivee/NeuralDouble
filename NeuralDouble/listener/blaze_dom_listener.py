from playwright.sync_api import sync_playwright
import threading
import time


def number_to_color(n):

    if n == 0:
        return "white"

    if 1 <= n <= 7:
        return "red"

    return "black"


def start_listener(engine):

    def run():

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)

            page = browser.new_page()

            print("🌐 Abrindo Blaze Double...")

            page.goto(
                "https://blaze.bet.br/pt/games/double",
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("⏳ Aguardando histórico carregar...")

            page.wait_for_selector("div[class*=recent]")

            print("🎧 Listener DOM ativo")

            last_number = None

            while True:

                try:

                    numbers = page.evaluate("""
                    () => {

                        const results = []

                        const nodes = document.querySelectorAll(
                            'div[class*="recent"] div[class*="entry"]'
                        )

                        nodes.forEach(el => {

                            const txt = el.innerText.trim()

                            if (/^\\d+$/.test(txt)) {

                                results.push(parseInt(txt))

                            }

                            if (el.innerHTML.includes("svg")) {

                                results.push(0)

                            }

                        })

                        return results
                    }
                    """)

                    if not numbers:
                        return

                    # o primeiro é o resultado mais recente
                    number = numbers[0]

                    if number != last_number:

                        last_number = number

                        color = number_to_color(number)

                        print("🎲 Resultado:", color)

                        engine.process_result(color)

                except Exception as e:

                    print("Erro no listener:", e)

                time.sleep(0.01)


    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
