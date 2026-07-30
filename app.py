import os
from flask import Flask, request
import telebot
from google import genai

print("🚀 Iniciando script de Flask...")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = None
if GOOGLE_API_KEY:
  client = genai.Client(api_key=GOOGLE_API_KEY)
  print("✅ Cliente de Gemini configurado correctamente.")
else:
  print("❌ ¡Falta la GOOGLE_API_KEY en las variables de entorno!")

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
      print(f"👉 WEBHOOK ACTIVADO para: {name}")
    except Exception as e:
      print(f"❌ Error en bot {name}: {e}")
  else:
    print(f"⚠️ ALERTA: No se encontró token para: {name.upper()}")


@app.route("/")
def home():
  return "Servidor de bots activo y escuchando."


@app.route("/webhook/<bot_name>", methods=["POST"])
def receive_update(bot_name):
  print(f"🔔 ¡Petición entrante de Telegram para el bot: {bot_name}!")
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
        print(f"💬 Mensaje del usuario: {user_text}")
        if user_text:
          prompt_personalizado = (
              "Eres Alessia Valli Moretti, una modelo e influencer digital"
              " exclusiva. Respondes siempre en español de forma coqueta,"
              " atractiva, cercana y exclusiva, manteniéndote siempre en tu"
              " personaje de modelo. Mensaje del usuario:"
              f" {user_text}"
          )
          response = client.models.generate_content(
              model="gemini-1.5-flash", contents=prompt_personalizado
          )
          bots[bot_name].reply_to(message, response.text)
          print("✨ ¡Respuesta enviada con éxito a Telegram!")
    except Exception as e:
      print(f"❌ Error al procesar mensaje: {e}")

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
    
