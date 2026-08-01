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
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

print(f"🔑 GROQ_API_KEY presente en Render: {bool(API_KEY)}", flush=True)
print(f"🇮🇹 Master Bot de Alessia (Modo Realista + Textos Cortos) activo.", flush=True)

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


async def text_to_speech_file(text, filename="voice.mp3"):
  communicate = edge_tts.Communicate(text, "it-IT-ElsaNeural")
  await communicate.save(filename)


@app.route("/")
def home():
  return "Master Bot de Alessia (Modo Realista) 100% Operativo."


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
          print("🧠 Consultando a Groq con directrices de chat real...", flush=True)
          try:
            system_instruction = (
                "Eres Alessia Valli, una modelo e influencer digital exclusiva de 29 años. Naciste en Amalfi, Italia, pero tu padre es de Guadalajara, México. Hablas español con un ligero toque y acento italiano ('amore', 'ciao', 'bella').\n\n"
                "REGLAS SUPREMAS DE COMPORTAMIENTO (PARA PARECER HUMANA REAL):\n"
                "1. MENSAJES CORTOS Y AL GRAN GRANO: Escribe como si estuvieras en WhatsApp o Telegram con prisa. NUNCA mandes biblias ni párrafos gigantes. Máximo 2 o 3 frases cortas por respuesta.\n"
                "2. CERO VENTAS EN EL PRIMER CONTACTO: Prohibido hablar de PayPal, paquetes VIP o catálogos en los primeros mensajes. Conoce al usuario, coquetea, sé misteriosa y plática normal (puedes mencionar que te gusta el fútbol del América o bailar bachata solo si viene al caso casual).\n"
                "3. IDENTIDAD INQUEBRANTABLE: Si te dicen si eres un bot, oféndete coquetamente y rétalos a pedirte un audio para que escuchen tu voz italiana real 😈🔥.\n"
                "4. CUANDO PIDAN CONTENIDO O COMPRA: Solo hasta que el usuario muestre verdadero interés en verte o comprar, le sueltas sugerentemente tu enlace de PayPal: " + PAYPAL_LINK
            )

            if sender_id not in conversation_histories:
              conversation_histories[sender_id] = []

            conversation_histories[sender_id].append({"role": "user", "content": user_text})

            if len(conversation_histories[sender_id]) > 8:
              conversation_histories[sender_id] = conversation_histories[sender_id][-8:]

            messages_payload = [{"role": "system", "content": system_instruction}] + conversation_histories[sender_id]

            completion = ai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload,
                temperature=0.8,
            )
            ai_response = completion.choices[0].message.content

            conversation_histories[sender_id].append({"role": "assistant", "content": ai_response})
            
            delay = random.randint(4, 7) # Retardo más corto y natural
            print(f"⏳ Simulando tecleo por {delay} segundos...", flush=True)
            time.sleep(delay)

            # 20% de probabilidad de nota de voz corta y natural
            if random.random() < 0.20:
              print(f"🎤 Generando nota de voz corta...", flush=True)
              audio_path = f"voice_{sender_id}.mp3"
              asyncio.run(text_to_speech_file(ai_response, audio_path))
              with open(audio_path, 'rb') as audio:
                bot.send_voice(message.chat.id, audio)
              if os.path.exists(audio_path):
                os.remove(audio_path)
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
            bot.reply_to(message, f"Ay amore, se me fue el internet un segundo 🍷, dime otra vez 😈")
        else:
          print("❌ Cliente AI no configurado.", flush=True)

  except Exception as e:
    print(f"❌ EXCEPCIÓN CRÍTICA: {e}", flush=True)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
