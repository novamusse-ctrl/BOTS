import os
from flask import Flask, request
import telebot
from google import genai

# Inicializar cliente moderno de Google GenAI
client = None
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
  client = genai.Client(api_key=API_KEY)

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

# Configurar webhooks automáticamente al arrancar
for name, token in BOT_TOKENS.items():
  if token:
    try:
      bot = telebot.TeleBot(token)
      bot.remove_webhook()
      webhook_url = f"{DOMAIN}/webhook/{name}"
      bot.set_webhook(url=webhook_url)
      bots[name] = bot
      print(f"Webhook configurado para: {name}")
    except Exception as e:
      print(f"Error en {name}: {e}")


@app.route("/")
def home():
  return "Servidor de bots activo y actualizado."


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
      if message and client:
        user_text = message.text if message.text else ""
        if user_text:
          print(f"Mensaje recibido en {bot_name}: {user_text}")
          prompt_personalizado = (
              "Eres Alessia Valli Moretti, una modelo e influencer digital"
              " exclusiva. Respondes siempre en español de forma coqueta,"
              " atractiva, cercana y exclusiva, manteniéndote siempre en tu"
              " personaje de modelo. Mensaje del usuario:"
              f" {user_text}"
          )

          # Llamada con la API moderna de google-genai
          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=prompt_personalizado
          )

          bots[bot_name].reply_to(message, response.text)
          print("¡Respuesta enviada de vuelta a Telegram con éxito!")
    except Exception as e:
      print(f"Error procesando el mensaje: {e}")

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
