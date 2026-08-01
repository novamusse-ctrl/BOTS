import os
import random
import re
import time
import traceback
from gtts import gTTS
from flask import Flask, request
import telebot
from groq import Groq

API_KEY = os.getenv("GROQ_API_KEY")
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://paypal.me/tu-enlace")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

print(f"🔑 GROQ_API_KEY presente en Render: {bool(API_KEY)}", flush=True)
print(f"🔥 Master Bot de Alessia (Voz Latina Natural + Filtro Audio) activo.", flush=True)

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

conversation_histories = {}

if bot:
  try:
    webhook_url = f"{DOMAIN}/webhook/master"
    bot.set_webhook(url=webhook_url)
    print("✅ Webhook del Master Bot configurado correctamente.", flush=True)
  except Exception as e:
    print(f"❌ Error configurando webhook: {e}", flush=True)


def clean_text_for_tts(text):
  """Limpia emojis, asteriscos y descripciones para que la voz no lea basura"""
  # Elimina todo lo que no sea texto estándar, acentos o puntuación básica
  text_clean = re.sub(r'[^\w\s.,?!¡¿áéíóúÁÉÍÓÚñÑ]', '', text)
  return text_clean.strip()


def generate_voice_google(text, filename="voice.mp3"):
  """Genera nota de voz con acento latino natural (México) y texto limpio"""
  audio_text = clean_text_for_tts(text)
  if not audio_text:
    audio_text = "Mande, mi amor."
  # tld='com.mx' otorga la tonada y acento natural de mujer latina
  tts = gTTS(text=audio_text, lang='es', tld='com.mx', slow=False)
  tts.save(filename)


@app.route("/")
def home():
  return "Master Bot de Alessia (Voz Latina Natural) 100% Operativo."


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

      # Modo Intervención Admin
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

      if user_text:
        print(f"💬 Mensaje de {user_name}: '{user_text}'", flush=True)

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
          print("🧠 Consultando a Groq con restricciones estrictas de voz y texto...", flush=True)
          try:
            system_instruction = (
                "Eres Alessia Valli, una modelo exclusiva de 29 años. Naciste en Italia pero vives en Guadalajara, Jalisco, México.\n\n"
                "REGLAS SUPREMAS DE COMPORTAMIENTO:\n"
                "1. CERO ASISTENTE: Jamás digas frases de soporte técnico ni de ayuda. Eres una mujer real.\n"
                "2. PERSONALIDAD Y LÍMITES: Eres coqueta, sensual y caliente por chat, te encanta juguetear. PERO ESTRICTAMENTE PROHIBIDO aceptar encuentros en persona, llamadas telefónicas o videollamadas. Tienes un novio celoso que te revisa el celular. Si te insisten, recházalo de inmediato con excusas de los celos de tu novio.\n"
                "3. RESPUESTAS ULTRA CORTAS Y SUTILES: Escribe exactamente como en WhatsApp o Telegram. Máximo una frase muy corta. NUNCA des respuestas de párrafos largos.\n"
                "4. CERO ACOTACIONES NI DESCRIPCIONES: PROHIBIDO escribir asteriscos, gestos o descripciones (como *se sonroja*, 'sonrisa', 'cara sonrojada', 'guiño'). Escribe únicamente lo que hablas de forma natural.\n"
                "5. REACCIÓN A EMOJIS: Si el usuario te manda solo emojis, respóndele únicamente con otro emoji o una palabra corta acompañada de un emoji. Jamás respondas párrafos a un emoji.\n"
                "6. EMOJIS AL 50%: Usa emojis con moderación (máximo uno de vez en cuando, no en todos los mensajes)."
            )

            if sender_id not in conversation_histories:
              conversation_histories[sender_id] = []

            conversation_histories[sender_id].append({"role": "user", "content": user_text})

            if len(conversation_histories[sender_id]) > 10:
              conversation_histories[sender_id] = conversation_histories[sender_id][-10:]

            messages_payload = [{"role": "system", "content": system_instruction}] + conversation_histories[sender_id]

            completion = ai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload,
                temperature=0.8,
            )
            ai_response = completion.choices[0].message.content

            conversation_histories[sender_id].append({"role": "assistant", "content": ai_response})
            
            delay = random.randint(2, 4)
            print(f"⏳ Simulando tecleo por {delay} segundos...", flush=True)
            time.sleep(delay)

            # 50% de probabilidad de nota de voz con acento natural latino
            if random.random() < 0.50:
              print(f"🎤 Generando y enviando nota de voz con acento natural...", flush=True)
              audio_path = f"voice_{sender_id}.mp3"
              try:
                generate_voice_google(ai_response, audio_path)
                with open(audio_path, 'rb') as audio:
                  try:
                    bot.send_voice(message.chat.id, audio)
                  except Exception as e_voice:
                    print(f"⚠️ send_voice falló ({e_voice}), usando send_audio...", flush=True)
                    audio.seek(0)
                    bot.send_audio(message.chat.id, audio)
                if os.path.exists(audio_path):
                  os.remove(audio_path)
                print("🚀 ¡Nota de voz enviada con éxito!", flush=True)
              except Exception as audio_err:
                print(f"❌ Error crítico en audio, enviando texto: {audio_err}", flush=True)
                bot.reply_to(message, ai_response)
            else:
              print(f"✨ Enviando texto corto...", flush=True)
              bot.reply_to(message, ai_response)
            
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
            fallback_options = [
                "Me dejas sin palabras 😉",
                "Uy, así me encantas 🔥",
                "Cuidado con lo que dices 😈",
                "Me tocas fibras sensibles 💋"
            ]
            bot.reply_to(message, random.choice(fallback_options))
        else:
          print("❌ Cliente AI no configurado.", flush=True)

  except Exception as e:
    print(f"❌ EXCEPCIÓN CRÍTICA: {e}", flush=True)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
