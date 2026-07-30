import os
import threading
from flask import Flask
import telebot
import google.generativeai as genai

# Configuración de la API de Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
  genai.configure(api_key=GOOGLE_API_KEY)
  model = genai.GenerativeModel("gemini-pro")

BOT_VARS = [
    "BOT_IA_CONVERSACIONAL",
    "BOT_MEMBRESIA_ELITE",
    "BOT_CHAT_BLUR_ELITE",
    "BOT_MEMBRESIA_NORMAL",
    "BOT_CHAT_BLUR_NORMAL",
]


def run_bot(var_name):
  token = os.getenv(var_name)
  if not token:
    return

  bot = telebot.TeleBot(token)
  try:
    bot.remove_webhook()
  except Exception:
    pass

  @bot.message_handler(func=lambda message: True)
  def handle_message(message):
    try:
      if GOOGLE_API_KEY:
        # Prompt de identidad para que responda como Alessia Valli Moretti
        prompt_personalizado = (
            "Eres Alessia Valli Moretti, una modelo e influencer digital"
            " exclusiva. Respondes siempre en español de forma coqueta,"
            " atractiva, cercana y exclusiva, manteniéndote siempre en tu"
            " personaje de modelo. Mensaje del usuario:"
            f" {message.text}"
        )
        response = model.generate_content(prompt_personalizado)
        bot.reply_to(message, response.text)
      else:
        bot.reply_to(message, "API Key de Gemini no configurada.")
    except Exception as e:
      print(f"Error en {var_name}: {e}")

  try:
    bot.infinity_polling(none_stop=True, interval=1, timeout=20)
  except Exception as e:
    print(f"Conflicto en bot {var_name}: {e}")


app = Flask(__name__)


@app.route("/")
def home():
  return "Bots de Telegram operando correctamente."


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.start()

  for var_name in BOT_VARS:
    t = threading.Thread(target=run_bot, args=(var_name,))
    t.start()
