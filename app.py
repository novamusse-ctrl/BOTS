import os
from flask import Flask, request
import telebot
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
  genai.configure(api_key=GOOGLE_API_KEY)
  model = genai.GenerativeModel("gemini-1.5-flash")

BOT_TOKENS = {
    "conversacional": os.getenv("BOT_IA_CONVERSACIONAL"),
    "elite": os.getenv("BOT_MEMBRESIA_ELITE"),
    "blur_elite": os.getenv("BOT_CHAT_BLUR_ELITE"),
    "normal": os.getenv("BOT_MEMBRESIA_NORMAL"),
    "blur_normal": os.getenv("BOT_CHAT_BLUR_NORMAL"),
}

bots = {}
app = Flask(__name__)
DOMAIN = "https://mis-bots-telegram.onrender.com"

for name, token in BOT_TOKENS.items():
  if token:
    try:
      bot = telebot.TeleBot(token)
      bot.remove_webhook()
      webhook_url = f"{DOMAIN}/webhook/{name}"
      bot.set_webhook(url=webhook_url)
      bots[name] = bot
    except Exception as e:
      print(f"Error en {name}: {e}")


@app.route("/")
def home():
  return "Servidor activo."


@app.route("/webhook/<bot_name>", methods=["POST"])
def webhook_receiver(bot_name):
  if bot_name in bots and request.is_json:
    try:
      json_string = request.get_data().decode("utf-8")
      update = telebot.types.Update.de_json(json_string)

      message = update.message or (
          update.callback_query.message
          if update.callback_query
          else None
      )
      if message and GOOGLE_API_KEY:
        user_text = message.text if message.text else ""
        if user_text:
          prompt_personalizado = (
              "Eres Alessia Valli Moretti, una modelo e influencer digital"
              " exclusiva. Respondes siempre en español de forma coqueta,"
              " atractiva, cercana y exclusiva, manteniéndote siempre en tu"
              " personaje de modelo. Mensaje del usuario:"
              f" {user_text}"
          )
          response = model.generate_content(prompt_personalizado)
          # Aquí usa el chat.id automático del usuario que mandó el mensaje
          bots[bot_name].reply_to(message, response.text)
    except Exception as e:
      print(f"Error procesando mensaje: {e}")

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
