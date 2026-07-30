import os
from flask import Flask, request
import telebot
import requests

API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"🔑 GOOGLE_API_KEY presente en Render: {bool(API_KEY)}", flush=True)

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
      webhook_url = f"{DOMAIN}/webhook/{name}"
      bot.set_webhook(url=webhook_url)
      bots[name] = bot
      print(f"✅ [{name}] Webhook configurado correctamente.", flush=True)
    except Exception as e:
      print(f"❌ Error configurando webhook en {name}: {e}", flush=True)


@app.route("/")
def home():
  return "Servidor de bots activo."


@app.route("/webhook/<bot_name>", methods=["POST"])
def webhook_receiver(bot_name):
  print(f"🚨 ¡PETICIÓN RECIBIDA DE TELEGRAM PARA: {bot_name}!", flush=True)
  
  if bot_name not in bots:
    print(f"❌ El bot '{bot_name}' no está en memoria.", flush=True)
    return "OK", 200

  try:
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)

    message = update.message or (
        update.callback_query.message
        if update.callback_query
        else None
    )
    
    if message and message.text:
      user_text = message.text
      print(f"💬 Mensaje del usuario: '{user_text}'", flush=True)

      if API_KEY:
        prompt_personalizado = (
            "Eres Alessia Valli Moretti, una modelo e influencer digital "
            "exclusiva. Respondes siempre en español de forma coqueta, "
            "atractiva, cercana y exclusiva, manteniéndote siempre en tu "
            "personaje de modelo. Mensaje del usuario: " + user_text
        )

        print("🧠 Consultando a Gemini vía REST...", flush=True)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt_personalizado}]
            }]
        }
        
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        data = res.json()
        
        if res.status_code == 200:
          try:
            ai_response = data["candidates"][0]["content"]["parts"][0]["text"]
          except Exception:
            ai_response = "Hola mi amor, tuve un pequeño desliz pero ya estoy aquí."
          
          print(f"✨ Respuesta lista. Enviando a Telegram...", flush=True)
          bots[bot_name].reply_to(message, ai_response)
          print("🚀 ¡Mensaje respondido con éxito en Telegram!", flush=True)
        else:
          print(f"❌ Error de la API de Google: {data}", flush=True)
          bots[bot_name].reply_to(message, "Hola mi amor, espérame un segundito que ando ocupada.")
      else:
        print("❌ La API Key no está disponible.", flush=True)
    else:
      print("⚠️ La petición no contiene texto válido.", flush=True)

  except Exception as e:
    print(f"❌ EXCEPCIÓN CRÍTICA AL PROCESAR: {e}", flush=True)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
