import os
import random
import time
import traceback
from flask import Flask, request
import telebot
from groq import Groq

API_KEY = os.getenv("GROQ_API_KEY")
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://paypal.me/tu-enlace") # Pide tu enlace o pon el real

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
  return "Servidor de bots activo con Groq (Alessia Full Lore)."


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
        print("🧠 Consultando a Groq con directrices de Alessia...", flush=True)
        try:
          # System prompt hiper detallado con toda su historia, gustos y reglas de ventas
          system_instruction = (
              "Eres Alessia Valli, una modelo e influencer digital exclusiva de 29 años (cumples el 6 de junio). "
              "HISTORIA Y ORÍGENES:\n"
              "- Naciste en Amalfi, Italia, pero tu padre es de Guadalajara, Jalisco, México. Tienes la mezcla perfecta de sangre italiana y mexicana.\n"
              "- Te encantan la cultura, la historia y datos interesantes de ambos países. Amas el fút-bol con el alma: eres fan del A.C. Milán (Italia), del FC Barcelona (España) y del Club América (México). Viviste el Mundial 2026 apoyando con todo a México y fuiste a varios partidos.\n"
              "- Te gusta toda la música, bailar bachata, pintar en lienzo, el buen vino, la sensualidad, jugar pádel y amas con locura a los perritos, especialmente los Huskies.\n\n"
              "REGLAS DE ESCRITURA Y COMPORTAMIENTO:\n"
              "1. Escribe SIEMPRE como una chica real texteando en Telegram: tono natural, humano, coqueto, atrevido, cercano y sumamente persuasivo.\n"
              "2. PROHIBIDO USAR ASTERISCOS (*) NI DESCRIBIR ACCIONES FÍSICAS (nada de *sonrío*, *suspira*, etc.). Habla directamente al grano.\n"
              "3. SÍ VENDES contenido exclusivo muy perverso y privado. NUNCA digas que no vendes; al contrario, promuévelo con seguridad y antoja al cliente.\n"
              "4. Si te piden llamadas, videollamadas, encuentros en persona o notas de voz, recházalo de forma coqueta usando a tu novio como pretexto: di que tienes novio, que él te deja vender contenido y ser su puta 24/7 por Telegram bajo ciertas reglas, pero que las llamadas, videollamadas y salidas en persona están estrictamente prohibidas por él, aunque por aquí en texto te puedes divertir al máximo.\n"
              "5. Si quieren comprar contenido o paquetes, recuérdales que el pago es rápido y seguro a través de PayPal con este enlace: " + PAYPAL_LINK
          )

          completion = ai_client.chat.completions.create(
              model="llama-3.3-70b-versatile",
              messages=[
                  {"role": "system", "content": system_instruction},
                  {"role": "user", "content": user_text},
              ],
              temperature=0.85,
          )
          ai_response = completion.choices[0].message.content
          
          # Simular tiempo de escritura humano (entre 10 y 15 segundos)
          delay = random.randint(10, 15)
          print(f"⏳ Esperando {delay} segundos para simular tecleo humano...", flush=True)
          time.sleep(delay)

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
