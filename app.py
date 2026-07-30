import os
from flask import Flask, request
import telebot
import google.generativeai as genai

# Configuración de Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
  genai.configure(api_key=GOOGLE_API_KEY)
  model = genai.GenerativeModel("gemini-1.5-flash")

# Diccionario de tus bots
BOT_TOKENS = {
    "conversacional": os.getenv("BOT_IA_CONVERSACIONAL"),
    "elite": os.getenv("BOT_MEMBRESIA_ELITE"),
    "blur_elite": os.getenv("BOT_CHAT_BLUR_ELITE"),
    "normal": os.getenv("BOT_MEMBRESIA_NORMAL"),
    "blur_normal": os.getenv("BOT_CHAT_BLUR_NORMAL"),
}

bots = {}
app = Flask(__name__)

# Inicializar bots y configurar webhooks automáticos hacia Render
DOMAIN = "https://mis-bots-telegram.onrender.com"

for name, token in BOT_TOKENS.items():
  if token:
    bot = telebot.TeleBot(token)
    try:
      bot.remove_webhook()
      webhook_url = f"{DOMAIN}/webhook/{name}"
      bot.set_webhook(url=webhook_url)
    except Exception as e:
      print(f"Error configurando webhook para {name}: {e}")
    bots[name] = bot


@app.route("/")
def home():
  return "Bots de Telegram operando con Webhooks al 100%."


@app.route("/webhook/<bot_name>", methods=["POST"])
def receive_update(bot_name):
  if bot_name in bots and request.headers.get("content-type") == (
      "application/json"
  ):
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)

    # Procesar mensaje según el bot que corresponda
    message = update.message or update.callback_query.message
    if message and GOOGLE_API_KEY:
      try:
        user_text = update.message.text if update.message else ""
        if user_text:
          prompt_personalizado = (
              "Eres Alessia Valli Moretti, una modelo e influencer digital"
              " exclusiva. Respondes siempre en español de forma coqueta,"
              " atractiva, cercana y exclusiva, manteniéndote siempre en tu"
              " personaje de modelo. Mensaje del usuario:"
              f" {user_text}"
          )
          response = model.generate_content(prompt_personalizado)
          bots[bot_name].reply_to(update.message, response.text)
      except Exception as e:
        print(f"Error generando respuesta con Gemini: {e}")

    return "", 200
  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
