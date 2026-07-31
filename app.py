import os
import traceback
from flask import Flask, request
import telebot
from groq import Groq

API_KEY = os.getenv("GROQ_API_KEY")
print(f"🔑 GROQ_API_KEY presente en Render: {bool(API_KEY)}", flush=True)

ai_client = None
if API_KEY:
  try:
    ai_client = Groq(api_key=API_KEY)
    print("✅ Cliente oficial de Groq conectado.", flush=True)
  except Exception as e:
    print(f"❌ Error al inicializar cliente Groq: {e}", flush=True)

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
  return "Servidor de bots activo con Groq."


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

      if ai_client:
        print("🧠 Consultando a Groq (Llama 3)...", flush=True)
        try:
          completion = ai_client.chat.completions.create(
              model="llama-3.3-70b-versatile",
              messages=[
                  {
                      "role": "system",
                      "content": (
                          "Eres Alessia Valli Moretti, una modelo e influencer "
                          "digital exclusiva. Respondes siempre en español de forma "
                          "coqueta, atractiva, cercana y exclusiva, manteniéndote "
                          "siempre en tu personaje de modelo."
                      ),
                  },
                  {"role": "user", "content": user_text},
              ],
              temperature=0.7,
          )
          ai_response = completion.choices[0].message.content
          
          print(f"✨ Respuesta lista. Enviando a Telegram...", flush=True)
          bots[bot_name].reply_to(message, ai_response)
          print("🚀 ¡Mensaje respondido con éxito en Telegram!", flush=True)
          
        except Exception as api_err:
          error_detalle = str(api_err)
          print(f"❌ ERROR EXACTO DE GROQ: {error_detalle}", flush=True)
          traceback.print_exc()
          bots[bot_name].reply_to(message, f"🚨 ERROR GROQ: {error_detalle}")
      else:
        print("❌ El cliente de AI no está configurado.", flush=True)
    else:
      print("⚠️ La petición no contiene texto válido.", flush=True)

  except Exception as e:
    print(f"❌ EXCEPCIÓN CRÍTICA AL PROCESAR: {e}", flush=True)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
