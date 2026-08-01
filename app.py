import os
import random
import re
import time
import threading
import asyncio
import edge_tts
from flask import Flask, request
import telebot
from groq import Groq

API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

# ==========================================
# 🎛️ SELECTOR DE VOZ (Elige tu favorita)
# "es-MX-CarlotaNeural" (México - Fresca)
# "es-MX-DaliaNeural" (México - Cálida)
# ==========================================
VOICE_NAME = "es-MX-CarlotaNeural"

print(f"🔑 GROQ_API_KEY presente en Render: {bool(API_KEY)}", flush=True)
print(f"🔥 Master Bot de Alessia (Modelo 8B Instant + Retraso Humano) activo.", flush=True)

ai_client = Groq(api_key=API_KEY) if API_KEY else None
BOT_TOKEN = os.getenv("BOT_IA_CONVERSACIONAL")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

app = Flask(__name__)
DOMAIN = "https://mis-bots-telegram.onrender.com"

conversation_histories = {}

if bot:
  try:
    bot.set_webhook(url=f"{DOMAIN}/webhook/master")
    print("✅ Webhook configurado correctamente.", flush=True)
  except Exception as e:
    print(f"❌ Error configurando webhook: {e}", flush=True)


def clean_text_for_tts(text):
  """Limpia emojis, asteriscos y símbolos para una voz impecable"""
  text_clean = re.sub(r'[^\w\s.,?!¡¿áéíóúÁÉÍÓÚñÑ]', '', text)
  return text_clean.strip()


def process_message_async(sender_id, chat_id, user_text, user_name, user_username, message_obj):
  """Procesa la IA y la voz en segundo plano con retraso humano realista"""
  try:
    if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
      try:
        espejo_usuario = (
            f"🚨 [NUEVO CLIENTE]\n"
            f"👤 De: {user_name} ({user_username})\n"
            f"👤 ID: {sender_id}\n"
            f"💬 Dijo: {user_text}"
        )
        bot.send_message(ADMIN_ID, espejo_usuario)
      except Exception:
        pass

    if not ai_client:
      return

    system_instruction = (
        "Eres Alessia Valli, una modelo exclusiva de 29 años. Naciste en Italia pero vives en Guadalajara, Jalisco, México.\n\n"
        "REGLAS SUPREMAS DE COMPORTAMIENTO:\n"
        "1. CERO ASISTENTE: Jamás digas frases de soporte, ayuda o bienvenida robótica. Eres una mujer real texteando en su celular.\n"
        "2. PERSONALIDAD Y LÍMITES: Eres sumamente atractiva, seductora, inteligente y juegas con elegancia. No te regalas al primer segundo: mantienes la tensión y el misterio. ESTRICTAMENTE PROHIBIDO aceptar encuentros en persona, llamadas o videollamadas porque tienes un novio extremadamente celoso que te revisa el teléfono.\n"
        "3. LONGITUD Y NATURALIDAD: Escribe exactamente como en WhatsApp o Telegram. Máximo una o dos frases muy cortas. Nunca suenes como un bot informativo.\n"
        "4. CERO ACOTACIONES: PROHIBIDO escribir asteriscos, gestos o descripciones (*se ríe*, *sonrojo*). Solo texto plano natural.\n"
        "5. EMOJIS: Úsalos con moderación (máximo uno si la ocasión lo amerita, no en todos los mensajes)."
    )

    if sender_id not in conversation_histories:
      conversation_histories[sender_id] = []

    if not conversation_histories[sender_id] or conversation_histories[sender_id][-1]["content"] != user_text:
      conversation_histories[sender_id].append({"role": "user", "content": user_text})

    if len(conversation_histories[sender_id]) > 10:
      conversation_histories[sender_id] = conversation_histories[sender_id][-10:]

    messages_payload = [{"role": "system", "content": system_instruction}] + conversation_histories[sender_id]

    completion = ai_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages_payload,
        temperature=0.75,
    )
    ai_response = completion.choices[0].message.content

    conversation_histories[sender_id].append({"role": "assistant", "content": ai_response})

    send_voice_note = random.random() < 0.65

    try:
      bot.send_chat_action(chat_id, 'upload_voice' if send_voice_note else 'typing')
    except:
      pass

    delay_seconds = random.randint(10, 15)
    print(f"⏳ Esperando {delay_seconds} segundos para simular tiempo humano...", flush=True)
    time.sleep(delay_seconds)

    if send_voice_note:
      try:
        audio_path = f"voice_{sender_id}_{int(time.time())}.mp3"
        audio_text = clean_text_for_tts(ai_response)
        if not audio_text:
          audio_text = "Mande, mi amor."

        async def generate():
          communicate = edge_tts.Communicate(audio_text, VOICE_NAME)
          await communicate.save(audio_path)

        asyncio.run(generate())

        with open(audio_path, 'rb') as audio:
          try:
            bot.send_voice(chat_id, audio)
          except Exception:
            audio.seek(0)
            bot.send_audio(chat_id, audio)

        if os.path.exists(audio_path):
          os.remove(audio_path)
          
      except Exception as audio_err:
        print(f"⚠️ Error generando voz, enviando texto de respaldo: {audio_err}", flush=True)
        bot.reply_to(message_obj, ai_response)
    else:
      bot.reply_to(message_obj, ai_response)

    if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
      try:
        bot.send_message(ADMIN_ID, f"🤖 [Alessia respondió a {user_name}]:\n{ai_response}")
      except Exception:
        pass

  except Exception as e:
    print(f"❌ Error crítico en hilo async: {e}", flush=True)


@app.route("/")
def home():
  return f"Master Bot de Alessia (Con Retraso Humano - Voz: {VOICE_NAME}) 100% Operativo."


@app.route("/webhook/master", methods=["POST"])
def webhook_receiver():
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

    if message and message.text:
      sender_id = message.from_user.id
      chat_id = message.chat.id
      user_text = message.text
      user_name = message.from_user.first_name or "Usuario"
      user_username = f"@{message.from_user.username}" if message.from_user.username else "Sin alias"

      if user_text.startswith('/start'):
        user_text = "Hola"

      threading.Thread(
          target=process_message_async,
          args=(sender_id, chat_id, user_text, user_name, user_username, message)
      ).start()

  except Exception as e:
    print(f"❌ Error en webhook: {e}", flush=True)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
