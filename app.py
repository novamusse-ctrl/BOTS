import os
from flask import Flask, request
import telebot
from google import genai

client = None
API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"🔑 GOOGLE_API_KEY presente en Render: {bool(API_KEY)}")
if API_KEY:
  try:
    client = genai.Client(api_key=API_KEY)
  except Exception as e:
    print(f"❌ Error inicializando el cliente de GenAI: {e}")

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
  print(f"🤖 Token para '{name}' presente: {bool(token)}")
  if token:
    try:
      bot = telebot.TeleBot(token)
      webhook_url = f"{DOMAIN}/webhook/{name}"
      bot.set_webhook(url=webhook_url)
      bots[name] = bot
      info = bot.get_webhook_info()
      print(f"✅ [{name}] Webhook configurado correctamente. URL: {info.url}")
    except Exception as e:
      print(f"❌ Error configurando webhook en {name}: {e}")
  else:
    print(f"⚠️ ATENCIÓN: La variable de entorno para '{name}' está VACÍA en Render.")


@app.route("/")
def home():
  return "Servidor de bots activo."


@app.route("/webhook/<bot_name>", methods=["POST"])
def webhook_receiver(bot_name):
  print(f"\n----------------------------------------")
  print(f"🚨 PETICIÓN RECIBIDA DE TELEGRAM PARA: {bot_name}")
  print(f"Bots cargados en memoria: {list(bots.keys())}")

  if bot_name not in bots:
    print(f"❌ ERROR: El bot '{bot_name}' NO está registrado en el diccionario (Falta su token en las variables de Render).")
    return "OK", 200

  try:
    json_string = request.get_data().decode("utf-8")
    print(f"📦 Payload bruto de Telegram: {json_string[:300]}")
    update = telebot.types.Update.de_json(json_string)

    message = update.message or (
        update.callback_query.message
        if update.callback_query
        else None
    )
    
    if not message:
      print("⚠️ La actualización de Telegram no contiene un mensaje de texto plano.")
      return "OK", 200

    user_text = message.text or message.caption or ""
    print(f"💬 Texto extraído del usuario: '{user_text}'")

    if not user_text:
      print("⚠️ El mensaje llegó vacío o es un archivo multimedia sin texto.")
      return "OK", 200

    if not client:
      print("❌ ERROR CRÍTICO: El cliente de Gemini no está activo (Falta GOOGLE_API_KEY).")
      bots[bot_name].reply_to(message, "Error interno: Falta configurar la API Key de Google en el servidor.")
      return "OK", 200

    prompt_personalizado = (
        "Eres Alessia Valli Moretti, una modelo e influencer digital "
        "exclusiva. Respondes siempre en español de forma coqueta, "
        "atractiva, cercana y exclusiva, manteniéndote siempre en tu "
        "personaje de modelo. Mensaje del usuario: " + user_text
    )

    print("🧠 Generando respuesta con Gemini...")
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt_personalizado
    )
    print(f"✨ Respuesta generada: {response.text[:100]}...")

    bots[bot_name].reply_to(message, response.text)
    print("🚀 ¡Respuesta enviada de vuelta a Telegram con éxito!")

  except Exception as e:
    print(f"❌ EXCEPCIÓN AL PROCESAR EL MENSAJE: {e}")

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
