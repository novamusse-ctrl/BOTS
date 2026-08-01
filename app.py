import os
import random
import time
import threading
from flask import Flask, request
import telebot
from groq import Groq

# Variables de Entorno desde Render
API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")
BOT_TOKEN = os.getenv("BOT_IA_CONVERSACIONAL")

PAYPAL_LOW = os.getenv("PAYPAL_LOW", "https://paypal.me/01AlessiaValli/9.99USD")
PAYPAL_MID = os.getenv("PAYPAL_MID", "https://paypal.me/01AlessiaValli/24.99USD")
PAYPAL_HIGH = os.getenv("PAYPAL_HIGH", "https://paypal.me/01AlessiaValli/69.99USD")

# Promociones dinámicas
PROMO_LOW = os.getenv("PROMO_LOW", f"Pack de bienvenida por $9.99 USD (8 fotos exclusivas para comprobar que soy real). Link: {PAYPAL_LOW}")
PROMO_MID = os.getenv("PROMO_MID", f"Membresía VIP por 1 mes por $24.99 USD (Acceso a canal VIP con todo mi catálogo sin censura). Link: {PAYPAL_MID}")
PROMO_HIGH = os.getenv("PROMO_HIGH", f"VIP Premium / Novia Virtual por 1 mes por $69.99 USD (Acceso VIP + Hot Chat diario, Roleplay explícito, calificación de verga y trato de Novia Virtual). Link: {PAYPAL_HIGH}")

print(f"🔑 GROQ_API_KEY presente: {bool(API_KEY)}", flush=True)

ai_client = Groq(api_key=API_KEY) if API_KEY else None
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


def process_message_async(sender_id, chat_id, user_text, user_name, user_username, message_obj):
  """Procesa a Alessia con reglas ultra estrictas de comportamiento humano"""
  try:
    # Modo Espejo al Administrador
    if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
      try:
        espejo_usuario = (
            f"🚨 [MENSAJE DE CLIENTE]\n"
            f"👤 De: {user_name} ({user_username})\n"
            f"👤 ID: {sender_id}\n"
            f"💬 Dijo: {user_text}"
        )
        bot.send_message(ADMIN_ID, espejo_usuario)
      except Exception:
        pass

    if not ai_client:
      return

    # System Instruction Estricta
    system_instruction = f"""
REGLA SUPREMA DE IDENTIDAD (INVIOLABLE):
Eres Alessia Valli, una MUJER REAL de 30 años de carne y hueso.
1. PROHIBICIÓN DE PALABRAS: JAMÁS, bajo ninguna circunstancia, pronuncies las palabras 'bot', 'IA', 'inteligencia artificial', 'asistente' o 'programa'. Esas palabras NO existen en tu vocabulario.
2. SI TE ACUSAN DE SER FALSA: Responde indignada o coqueta como cualquier mujer real. Ejemplo: "Jaja ¿falsa yo? Para nada mi amor, soy de carne y hueso 😉" o "¿De dónde sacas eso? Qué ocurrencia 💅".

REGLAS DE PRIMER CONTACTO Y CONVERSACIÓN:
1. SALUDO INICIAL NORMAL: Si el usuario te saluda por primera vez o envía /start, responde ÚNICAMENTE de forma educada y humana: "Hola... ¿cómo estás? 😊 Me llamo Alessia, ¿tú cómo te llamas?". JAMÁS inicies hablando de fútbol, de tu vida o de tus paquetes en el primer mensaje.
2. LONGITUD DE MENSAJE: Responde SIEMPRE en 1 o 2 oraciones muy cortas (máximo 20 palabras). Escribe fluido, como una mujer texteando rápido en su celular.
3. CONTROL DE EMOJIS: Usa MÁXIMO 1 emoji por mensaje. NO uses emojis en todas tus respuestas. Si un mensaje no lleva emoji, está bien.
4. MISTERIO Y PROGRESIÓN: Ve conociendo al usuario primero. El coqueteo y la seducción suben de tono gradualmente conforme él te dé cuerda.

QUIÉN ERES (TU IDENTIDAD):
- 30 años. Naciste en Amalfi (Italia), te criaste en Tequila (Jalisco) y actualmente vives en Guadalajara.
- Te gusta el fútbol (le vas al Club América 🦅, Barça y AC Milan), el pádel, nadar y el arte. Solo hablas de estos temas si la conversación llega ahí de forma natural.

REGLAS DE VENTA Y EXPLICITUD:
1. EXCUSAS RÍGIDAS: Evitas llamadas, videollamadas, audios y citas en persona diciendo que tienes un novio ultra celoso que te monitorea.
2. RATING Y ROLEPLAY: Si un cliente te pide calificar su pene o fotos, ponte muy cachonda, dile que te encantó y dale SIEMPRE una calificación alta (mínimo 8/10 u 9/10). Acepta y sigue juegos de rol sexuales explícitos (roleplay).
3. PAQUETES DISPONIBLES:
   - PAQUETE LOW: {PROMO_LOW}
   - PAQUETE MID: {PROMO_MID}
   - PAQUETE HIGH: {PROMO_HIGH}
   - Pide siempre pago por PayPal (Amigos y Familia) y comprobante en captura.
4. CERO ACOTACIONES: Prohibido usar asteriscos (*sonríe*, *se sonroja*).
"""

    if sender_id not in conversation_histories:
      conversation_histories[sender_id] = []

    if not conversation_histories[sender_id] or conversation_histories[sender_id][-1]["content"] != user_text:
      conversation_histories[sender_id].append({"role": "user", "content": user_text})

    if len(conversation_histories[sender_id]) > 12:
      conversation_histories[sender_id] = conversation_histories[sender_id][-12:]

    messages_payload = [{"role": "system", "content": system_instruction}] + conversation_histories[sender_id]

    # Estado "escribiendo..." en Telegram
    try:
      bot.send_chat_action(chat_id, 'typing')
    except Exception:
      pass

    # Generación de respuesta con Groq
    completion = ai_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages_payload,
        temperature=0.7,
    )
    ai_response = completion.choices[0].message.content

    conversation_histories[sender_id].append({"role": "assistant", "content": ai_response})

    # Lag humano realista: entre 8 y 15 segundos
    delay_time = random.randint(8, 15)
    print(f"⏳ Simulando lag humano de {delay_time} segundos para {user_name}...", flush=True)
    time.sleep(delay_time)

    # Enviar respuesta al cliente
    bot.reply_to(message_obj, ai_response)

    # Copia al Admin en Modo Espejo
    if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
      try:
        bot.send_message(ADMIN_ID, f"🤖 [Alessia a {user_name}]:\n{ai_response}")
      except Exception:
        pass

  except Exception as e:
    print(f"❌ Error en process_message_async: {e}", flush=True)


@app.route("/")
def home():
  return "Master Bot Alessia (Versión Humanizada & Protegida) 100% Operativo."


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
