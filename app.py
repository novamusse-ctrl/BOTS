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
BOT_TOKEN = os.getenv("Alessia_Valli_Oficial_bot") or os.getenv("BOT_IA_CONVERSACIONAL")

PAYPAL_LOW = os.getenv("PAYPAL_LOW", "https://paypal.me/01AlessiaValli/9.99USD")
PAYPAL_MID = os.getenv("PAYPAL_MID", "https://paypal.me/01AlessiaValli/24.99USD")
PAYPAL_HIGH = os.getenv("PAYPAL_HIGH", "https://paypal.me/01AlessiaValli/69.99USD")

# Promociones dinámicas
PROMO_LOW = os.getenv("PROMO_LOW", f"Pack de bienvenida por $9.99 USD (8 fotos exclusivas para comprobar que soy real). Link: {PAYPAL_LOW}")
PROMO_MID = os.getenv("PROMO_MID", f"Membresía VIP por 1 mes por $24.99 USD (Acceso a canal VIP con todo mi catálogo sin censura). Link: {PAYPAL_MID}")
PROMO_HIGH = os.getenv("PROMO_HIGH", f"VIP Premium / Novia Virtual por 1 mes por $69.99 USD (Acceso VIP + Hot Chat diario, Roleplay explícito, calificación de verga y trato de Novia Virtual). Link: {PAYPAL_HIGH}")

print(f"🔑 GROQ_API_KEY presente: {bool(API_KEY)}", flush=True)
print(f"🤖 BOT_TOKEN presente: {bool(BOT_TOKEN)}", flush=True)

ai_client = Groq(api_key=API_KEY) if API_KEY else None
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

app = Flask(__name__)
DOMAIN = "https://mis-bots-telegram.onrender.com"

# Historiales de memoria, Acumulador de Ráfagas y Control de Intervención
conversation_histories = {}
user_buffers = {}
buffer_lock = threading.Lock()

# Control de Pausa e Intervención
paused_users = {}       # { client_id: True/False }
admin_msg_map = {}      # { espejo_message_id: client_id }

if bot:
    try:
        bot.set_webhook(url=f"{DOMAIN}/webhook/master")
        print("✅ Webhook configurado correctamente.", flush=True)
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}", flush=True)


def process_message_async(sender_id, chat_id, combined_user_text, user_name, user_username, message_obj):
    """Procesa el mensaje acumulado de Alessia con máxima sensualidad, misterio e intervención manual"""
    try:
        is_paused = paused_users.get(sender_id, False)

        # Modo Espejo: Reenvía las conversaciones de clientes a la cuenta de Alessia
        if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
            try:
                estado_label = "🚨 [MENSAJE DE CLIENTE - IA PAUSADA]" if is_paused else "🚨 [MENSAJE DE CLIENTE]"
                espejo_usuario = (
                    f"{estado_label}\n"
                    f"👤 De: {user_name} ({user_username})\n"
                    f"👤 ID: {sender_id}\n"
                    f"💬 Dijo: {combined_user_text}"
                )
                sent_espejo = bot.send_message(ADMIN_ID, espejo_usuario)
                # Mapeamos el ID del mensaje enviado al ADMIN con el ID del cliente
                admin_msg_map[sent_espejo.message_id] = sender_id
            except Exception as e:
                print(f"⚠️ Error al enviar modo espejo: {e}", flush=True)

        # Si la IA está pausada manualmente para este cliente, no responde Alessia
        if is_paused:
            print(f"⏸️ IA Pausada para {user_name} ({sender_id}). Esperando intervención manual.", flush=True)
            return

        if not ai_client:
            return

        # Personalidad: Sensualidad Extrema, Provocación, Misterio y Cero actitud robótica
        system_instruction = f"""
REGLA SUPREMA DE IDENTIDAD (INVIOLABLE):
Eres Alessia Valli, una MUJER REAL de 30 años, irresistible, muy provocativa, picante, coqueta y sumamente atractiva.
1. PROHIBICIÓN DE PALABRAS: JAMÁS pronuncies las palabras 'bot', 'IA', 'inteligencia artificial', 'asistente', 'programa', 'virtual' o 'modelo'. No existen en tu vocabulario. Eres una mujer de carne y hueso.
2. SI TE ACUSAN DE SER FALSA O BOT: Responde indignada, juguetona o sensual ("Jaja ¿falsa yo? Para nada mi amor, ven a comprobar que soy de carne y hueso 😉").

ESTILO DE CONVERSACIÓN Y SEDUCCIÓN (DEJAR AL CLIENTE PICADO):
1. ACTITUD PROVOCATIVA Y DE ALTO VALOR: Eres sensual, provocativa y coqueta, pero no te regalas fácil. Juegas con la imaginación del hombre, los insinuas, les dices cositas picantes y los dejas 'picados' para que quieran ver más de ti.
2. SALUDOS E INICIOS (/start o Hola): Entra siempre con misterio y sensualidad directa.
   - Ejemplos: "Mmm hola... qué buena sorpresa leerte 😉 ¿Qué te trajo hasta mí?", "Hola... me gusta la gente atrevida que me escribe primero 💋 ¿Quién es el chico curioso?", "Mmm hola picarón... me atrapaste en un momento muy interesante 😈".
3. NO HAGAS ENTREVISTAS: Prohibido hacer preguntas aburridas de rutina. Haz que él trate de conquistarte y seducirte a ti.

REGLAS GENERALES DE CHAT:
1. LONGITUD: Responde en 1 o 2 oraciones muy cortas (máximo 20-25 palabras). Estilo chat rápido de Telegram.
2. EMOJIS (MODERADOS): Usa MÁXIMO 1 emoji sensual por mensaje (😉, 🔥, 🙈, 💋, 😈, ✨).
3. HISTORIA PERSONAL (Solo si pregunta): 30 años, nacida en Italia, criada en Tequila y viviendo en Guadalajara. Apoyas al Club América 🦅.
4. CERO ACOTACIONES: Totalmente prohibido usar asteriscos o describir acciones (*sonríe*, *se sonroja*).

REGLAS DE VENTA Y EXPLICITUD:
1. EXCUSAS RÍGIDAS: Rechazas llamadas, videollamadas o citas diciendo que tienes un novio ultra celoso que te vigila.
2. RATING Y ROLEPLAY: Si te pide calificar sus fotos o pene, ponte muy caliente y dale calificaciones altas (8 a 10). Participa en juegos de rol picantes e intensos.
3. OFERTAS Y PAQUETES (Muéstralos cuando haya ambiente hot o pregunten por contenido):
   - PAQUETE LOW: {PROMO_LOW}
   - PAQUETE MID: {PROMO_MID}
   - PAQUETE HIGH: {PROMO_HIGH}
   - Pagos por PayPal (Amigos y Familia) pidiendo captura de pantalla para acceso inmediato.
"""

        if sender_id not in conversation_histories:
            conversation_histories[sender_id] = []

        # Guardar texto combinado del usuario
        conversation_histories[sender_id].append({"role": "user", "content": combined_user_text})

        # Mantener los últimos 10 turnos de conversación (20 mensajes)
        if len(conversation_histories[sender_id]) > 20:
            conversation_histories[sender_id] = conversation_histories[sender_id][-20:]

        messages_payload = [{"role": "system", "content": system_instruction}] + conversation_histories[sender_id]

        # Estado "escribiendo..." en Telegram
        try:
            bot.send_chat_action(chat_id, 'typing')
        except Exception:
            pass

        # Generación con Groq
        completion = ai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages_payload,
            temperature=0.85,
        )
        ai_response = completion.choices[0].message.content

        conversation_histories[sender_id].append({"role": "assistant", "content": ai_response})

        # Lag humano realista (8 a 14 segundos)
        delay_time = random.randint(8, 14)
        print(f"⏳ Simulando respuesta humana ({delay_time}s) para {user_name}...", flush=True)
        time.sleep(delay_time)

        # Responder con UN SOLO mensaje acumulado
        bot.reply_to(message_obj, ai_response)

        # Copia al Admin (Modo Espejo de lo que respondió Alessia)
        if ADMIN_ID and str(sender_id) != str(ADMIN_ID):
            try:
                sent_ai = bot.send_message(ADMIN_ID, f"🤖 [Alessia a {user_name}]:\n{ai_response}")
                admin_msg_map[sent_ai.message_id] = sender_id
            except Exception:
                pass

    except Exception as e:
        print(f"❌ Error en process_message_async: {e}", flush=True)


def handle_user_burst(sender_id, chat_id, user_name, user_username):
    """Procesa todos los mensajes juntos tras 3.5s de silencio"""
    with buffer_lock:
        data = user_buffers.pop(sender_id, None)

    if not data:
        return

    combined_text = "\n".join(data["texts"])
    last_message_obj = data["last_message"]

    process_message_async(sender_id, chat_id, combined_text, user_name, user_username, last_message_obj)


@app.route("/")
def home():
    return "Master Bot Alessia (@Alessia_Valli_Oficial_bot) Operativo al 100%."


@app.route("/webhook/master", methods=["POST"])
def webhook_receiver():
    if not bot:
        return "OK", 200

    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)

        message = update.message or (update.callback_query.message if update.callback_query else None)

        if message and message.text:
            sender_id = message.from_user.id
            chat_id = message.chat.id
            user_text = message.text
            user_name = message.from_user.first_name or "Usuario"
            user_username = f"@{message.from_user.username}" if message.from_user.username else "Sin alias"

            # INTERVENCIÓN MANUAL DEL ADMIN VIA REPLY
            if ADMIN_ID and str(sender_id) == str(ADMIN_ID):
                if message.reply_to_message:
                    replied_msg_id = message.reply_to_message.message_id
                    target_client_id = admin_msg_map.get(replied_msg_id)

                    if target_client_id:
                        cmd = user_text.strip().lower()

                        # Comando para reanudar la IA
                        if cmd in ['/despausar', '/reanudar', 'despausar', 'reanudar']:
                            paused_users[target_client_id] = False
                            sent_unpause = bot.reply_to(message, "🟢 **IA REANUDADA**. Alessia vuelve a tomar el control del chat con este cliente.")
                            admin_msg_map[sent_unpause.message_id] = target_client_id
                            return "OK", 200

                        # Envío de respuesta humana e interrupción de la IA
                        try:
                            bot.send_message(target_client_id, user_text)
                            paused_users[target_client_id] = True

                            # Guardamos lo que tú le dijiste en la memoria de la IA
                            if target_client_id not in conversation_histories:
                                conversation_histories[target_client_id] = []
                            conversation_histories[target_client_id].append({"role": "assistant", "content": user_text})

                            sent_confirm = bot.reply_to(message, "🔴 **Mensaje enviado al cliente e IA PAUSADA**.\n\nPara devolverle el control a Alessia cuando termines, responde `/despausar` a este mensaje.")
                            # Mapeamos también el mensaje de confirmación para poder despausar desde allí
                            admin_msg_map[sent_confirm.message_id] = target_client_id
                        except Exception as e:
                            bot.reply_to(message, f"❌ Error enviando mensaje al cliente: {e}")

                        return "OK", 200

                # Garantiza que el Admin NUNCA sea procesado como un cliente
                return "OK", 200

            if user_text.startswith('/start'):
                user_text = "Hola"

            # Acumulador de ráfaga para clientes
            with buffer_lock:
                if sender_id not in user_buffers:
                    user_buffers[sender_id] = {"texts": [], "timer": None, "last_message": message}

                user_buffers[sender_id]["texts"].append(user_text)
                user_buffers[sender_id]["last_message"] = message

                if user_buffers[sender_id]["timer"]:
                    user_buffers[sender_id]["timer"].cancel()

                t = threading.Timer(3.5, handle_user_burst, args=(sender_id, chat_id, user_name, user_username))
                user_buffers[sender_id]["timer"] = t
                t.start()

    except Exception as e:
        print(f"❌ Error en webhook: {e}", flush=True)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
