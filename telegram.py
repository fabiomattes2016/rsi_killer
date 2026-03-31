import httpx
import os
from dotenv import load_dotenv


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message: str):
    """
    Envia uma mensagem para um chat do Telegram usando a API do Telegram.

    Esta função utiliza o token e ID do chat configurados nas variáveis de ambiente para enviar uma mensagem de texto para o Telegram.

    Parâmetros:
    - message (str): A mensagem de texto a ser enviada. Suporta formatação HTML.

    Retorna:
    - None
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    with httpx.Client() as client:
        client.post(url, json=payload)