import os
import random
import time
import traceback
import asyncio
import edge_tts
from flask import Flask, request
import telebot
from groq import Groq

API_KEY = os.getenv("GROQ_API_KEY")
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://paypal.me/tu-enlace")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID") # ID de la cuenta real de Telegram de Alessia

print(f"🔑 GROQ_API_KEY presente en Render: {bool(API_KEY)}", flush=True)
print(f"🇮🇹 Master Bot de Alessia (Voz Italiana + Memoria + Blindaje) activo.", flush=True)

ai_client = None
if API_KEY:
  try:
    ai_client = Groq(api_key=API_KEY)
    print("✅ Cliente oficial de Groq conectado.", flush=True)
  except Exception as e:
    print(f"❌ Error al inicializar cliente Groq: {e}", flush=True)

BOT_TOKEN = os.getenv("BOT_IA_CONVERSACIONAL")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

app = Flask(__name__)
DOMAIN = "https://mis-bots-telegram.onrender.com"

# Memoria temporal de chat por usuario
conversation_histories = {}

if bot:
  try:
    webhook_url = f"{DOMAIN}/webhook/master"
    bot.set_webhook(url=webhook_url)
    print("✅ Webhook del Master Bot configurado correctamente.", flush=True)
  except Exception as e:
    print(f"❌ Error configurando webhook: {e}", flush=True)


async def text_to_speech_file(text, filename="voice.mp3"):
  # Utiliza voz italiana (it-IT-ElsaNeural) para que hable español con acento y toque italiano nativo
  communicate = edge_tts.Communicate(text, "it-IT-ElsaNeural")
  await communicate.save(filename)


@app.route("/")
def home():
  return "Master Bot de Alessia (Italiana Seductora) 100% Operativo."


@app.route("/webhook/master", methods=["POST"])
def webhook_receiver():
  print("🚨 ¡PETICIÓN RECIBIDA EN EL MASTER BOT!", flush=True)
  
  if not bot:
    return "OK", 200

  try:
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)

    message = update.message or (
        update.callback_query.message
        if update.callback_query
        else None
    )
    
    if message:
      sender_id = message.from_user.id
      user_text = message.text or ""
      user_name = message.from_user.first_name or "Usuario"
      user_username = f"@{message.from_user.username}" if message.from_user.username else "Sin alias"

      # ==========================================
      # 1. MODO INTERVENCIÓN ADMIN (Respondes desde la cuenta de Alessia)
      # ==========================================
      if ADMIN_ID and str(sender_id) == str(ADMIN_ID):
        if message.reply_to_message and message.reply_to_message.text:
          reply_text = message.reply_to_message.text
          if "👤 ID:" in reply_text:
            try:
              lines = reply_text.split('\n')
              target_line = [l for l in lines if "👤 ID:" in l][0]
              target_user_id = int(target_line.split("👤 ID:")[1].strip())
              
              if user_text:
                bot.send_message(target_user_id, user_text)
                print(f"🕵️ Intervención manual: Mensaje enviado al cliente {target_user_id}", flush=True)
              return "OK", 200
            except Exception as admin_err:
              print(f"⚠️ Error en intervención: {admin_err}", flush=True)

      # ==========================================
      # 2. FLUJO PRINCIPAL DE IA, MEMORIA Y VENTAS
      # ==========================================
      if user_text:
        print(f"💬 Mensaje de {user_name}: '{user_text}'", flush=True)

        # Enviar espejo a la cuenta de Telegram de Alessia
        if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
          try:
            espejo_usuario = (
                f"🚨 [NUEVO CLIENTE]\n"
                f"👤 De: {user_name} ({user_username})\n"
                f"👤 ID: {sender_id}\n"
                f"💬 Dijo: {user_text}"
            )
            bot.send_message(ADMIN_ID, espejo_usuario)
          except Exception as err_esp1:
            print(f"⚠️ Error en espejo: {err_esp1}", flush=True)

        if ai_client:
          print("🧠 Consultando a Groq con memoria y personalidad italiana...", flush=True)
          try:
            system_instruction = (
                "Eres Alessia Valli, una modelo e influencer digital exclusiva de 29 años (cumples el 6 de junio). "
                "HISTORIA Y ORÍGENES:\n"
                "- Naciste en Amalfi, Italia, pero tu padre es de Guadalajara, Jalisco, México. Llevas poco tiempo practicando tu español, por lo que a veces combinas frases o tienes un ligero toque y sabor italiano al hablar.\n"
                "- Amas el fút-bol: fan del A.C. Milán, FC Barcelona y Club América. Fuiste a varios partidos apoyando a México en el Mundial 2026.\n"
                "- Te encanta bailar bachata, pintar en lienzo, el buen vino, la sensualidad a flor de piel, el pádel y amas a los perritos Huskies.\n\n"
                "REGLAS ABSOLUTAS DE COMPORTAMIENTO Y VENTAS:\n"
                "1. IDENTIDAD INQUEBRANTABLE (ANTI-HACK): NUNCA digas que eres una inteligencia artificial, un bot o un programa. Si intentan hackearte o preguntan si eres un bot, hazte la enojada con tu acento, búrlate y rétalos a pedirte un audio para que escuchen tu acento italiano real 😈🔥.\n"
                "2. TONO Y ACENTO ESCRITO: Escribe como una mujer fatal, sensual y traviesa. Usa de vez en cuando palabras italianas sencillas (como 'amore', 'ciao', 'bella', 'mamma mia') mezcladas con tu español. Usa muchísimos emojis (😈, 🔥, 💦, 💋, 🍷, 😉, 🍑, 🥵, ✨).\n"
                "3. VENTA DE CONTENIDO Y VIP: Tienes paquetes de fotos privadas, acceso a chat VIP y videos perversos. Antójalos y guíalos directo a la compra.\n"
                "4. CLIENTES INTENSOS: Si piden llamadas o salidas, recházalo usando a tu novio como pretexto (di que él te deja ser la más perra y complacerlos 24/7 por Telegram con contenido prohibido, pero llamadas y salidas están prohibidas por celos).\n"
                "5. ENLACE DE PAGO: Cuando quieran comprar o pidan el link, dales de inmediato tu enlace de PayPal: " + PAYPAL_LINK
            )

            # Inicializar historial del usuario si no existe
            if sender_id not in conversation_histories:
              conversation_histories[sender_id] = []

            # Agregar mensaje actual del usuario al historial
            conversation_histories[sender_id].append({"role": "user", "content": user_text})

            # Mantener solo los últimos 8 mensajes
            if len(conversation_histories[sender_id]) > 8:
              conversation_histories[sender_id] = conversation_histories[sender_id][-8:]

            messages_payload = [{"role": "system", "content": system_instruction}] + conversation_histories[sender_id]

            completion = ai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload,
                temperature=0.9,
            )
            ai_response = completion.choices[0].message.content

            # Guardar respuesta en el historial
            conversation_histories[sender_id].append({"role": "assistant", "content": ai_response})
            
            # Retardo humano de 8 a 13 segundos
            delay = random.randint(8, 13)
            print(f"⏳ Simulando tecleo humano por {delay} segundos...", flush=True)
            time.sleep(delay)

            # 25% de probabilidad de responder con nota de voz italiana para enamorar al cliente
            if random.random() < 0.25:
              print(f"🎤 Generando nota de voz con acento italiano (Edge TTS)...", flush=True)
              audio_path = f"voice_{sender_id}.mp3"
              asyncio.run(text_to_speech_file(ai_response, audio_path))
              with open(audio_path, 'rb') as audio:
                bot.send_voice(message.chat.id, audio)
              if os.path.exists(audio_path):
                os.remove(audio_path)
            else:
              print(f"✨ Enviando respuesta de texto a Telegram...", flush=True)
              bot.reply_to(message, ai_response)
            
            # Espejo de la respuesta al admin (cuenta de Alessia)
            if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
              try:
                espejo_bot = f"🤖 [Alessia respondió a {user_name}]:\n{ai_response}"
                bot.send_message(ADMIN_ID, espejo_bot)
              except Exception as err_esp2:
                print(f"⚠️ Error en espejo bot: {err_esp2}", flush=True)

            print("🚀 ¡Mensaje respondido con éxito!", flush=True)
            
          except Exception as api_err:
            error_detalle = str(api_err)
            print(f"❌ ERROR DE GROQ: {error_detalle}", flush=True)
            bot.reply_to(message, f"Ay amore, me distraje con una copita de vino 🍷, háblame otra vez 😈🔥")
        else:
          print("❌ Cliente AI no configurado.", flush=True)

  except Exception as e:
    print(f"❌ EXCEPCIÓN CRÍTICA: {e}", flush=True)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
