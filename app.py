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

# Configurar y verificar webhooks al arrancar
for name, token in BOT_TOKENS.items():
  if token:
    bot = telebot.TeleBot(token)
    try:
      bot.remove_webhook()
      webhook_url = f"{DOMAIN}/webhook/{name}"
      res = bot.set_webhook(url=webhook_url)
      print(f"👉 [HOOK OK] Webhook configurado para {name}: {res}")
    except Exception as e:
      print(f"❌ [ERROR HOOK] Falló {name}: {e}")
    bots[name] = bot


@app.route("/")
def home():
  return "Bots de Telegram operando con Webhooks al 100%."


@app.route("/webhook/<bot_name>", methods=["POST"])
def receive_update(bot_name):
  print(
      f"🔔 ¡ALERTA! Telegram mandó una petición al bot: {bot_name}"
  )  # Este chivato debe salir en Render sí o sí
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
        print(f"💬 Mensaje recibido de usuario: {user_text}")
        if user_text:
          prompt_personalizado = (
              "Eres Alessia Valli Moretti, una modelo e influencer digital"
              " exclusiva. Respondes siempre en español de forma coqueta,"
              " atractiva, cercana y exclusiva, manteniéndote siempre en tu"
              " personaje de modelo. Mensaje del usuario:"
              f" {user_text}"
          )
          response = model.generate_content(prompt_personalizado)
          bots[bot_name].reply_to(message, response.text)
          print("✨ ¡Respuesta enviada de vuelta a Telegram con éxito!")
    except Exception as e:
      print(f"❌ Error procesando el mensaje: {e}")

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
