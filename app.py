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

# Tokens de tus 5 bots leídos de forma segura desde las variables de entorno de Render
TOKENS = [
    os.getenv("BOT_TOKEN_1"),
    os.getenv("BOT_TOKEN_2"),
    os.getenv("BOT_TOKEN_3"),
    os.getenv("BOT_TOKEN_4"),
    os.getenv("BOT_TOKEN_5"),
]


def run_bot(token):
  if not token:
    return
  bot = telebot.TeleBot(token)

  @bot.message_handler(func=lambda message: True)
  def handle_message(message):
    try:
      if GOOGLE_API_KEY:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
      else:
        bot.reply_to(
            message, "API Key de Gemini no configurada en el sistema."
        )
    except Exception as e:
      bot.reply_to(message, "Ocurrió un error al procesar tu solicitud.")

  bot.infinity_polling(none_stop=True)


# Servidor web requerido por Render para mantener el contenedor activo 24/7
app = Flask(__name__)


@app.route("/")
def home():
  return "Servicios de bots activos y operando correctamente."


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  # Levantar el servidor web en segundo plano
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.start()

  # Levantar cada bot de Telegram en su propio hilo de ejecución simultánea
  for token in TOKENS:
    if token:
      bot_thread = threading.Thread(target=run_bot, args=(token,))
      bot_thread.start()
