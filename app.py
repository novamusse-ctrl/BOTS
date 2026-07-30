import os
import threading
from flask import Flask
import telebot
import google.generativeai as genai

# Configuración de Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
  genai.configure(api_key=GOOGLE_API_KEY)
  model = genai.GenerativeModel("gemini-1.5-flash")

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
    print(f"Token no encontrado para {var_name}")
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
      print(f"Error procesando mensaje en {var_name}: {e}")

  print(f"Bot {var_name} iniciado correctamente.")
  while True:
    try:
      bot.infinity_polling(none_stop=True, interval=2, timeout=30)
    except Exception as e:
      print(f"Reconectando bot {var_name} por error: {e}")


app = Flask(__name__)


@app.route("/")
def home():
  return "Bots de Telegram operando al 100%."


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  # Iniciar servidor Flask en segundo plano
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.start()

  # Iniciar cada bot de Telegram en su propio hilo independiente
  for var_name in BOT_VARS:
    t = threading.Thread(target=run_bot, args=(var_name,))
    t.daemon = True
    t.start()
