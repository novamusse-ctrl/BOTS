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

# Tokens leídos exactamente con los nombres que pusiste en Render
TOKENS = [
    os.getenv("BOT_IA_CONVERSACIONAL"),
    os.getenv("BOT_MEMBRESIA_ELITE"),
    os.getenv("BOT_CHAT_BLUR_ELITE"),
    os.getenv("BOT_MEMBRESIA_NORMAL"),
    os.getenv("BOT_CHAT_BLUR_NORMAL"),
]


def run_bot(token):
  if not token:
    return
  bot = telebot.TeleBot(token)

  # Limpiar cualquier webhook anterior para permitir el funcionamiento por polling
  try:
    bot.remove_webhook()
  except Exception:
    pass

  @bot.message_handler(func=lambda message: True)
  def handle_message(message):
    try:
      if GOOGLE_API_KEY:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
      else:
        bot.reply_to(message, "API Key de Gemini no configurada.")
    except Exception as e:
      bot.reply_to(message, "Ocurrió un error al procesar tu solicitud.")

  bot.infinity_polling(none_stop=True)


# Servidor web para mantener el servicio activo en Render
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

  for token in TOKENS:
    if token:
      bot_thread = threading.Thread(target=run_bot, args=(token,))
      bot_thread.start()
