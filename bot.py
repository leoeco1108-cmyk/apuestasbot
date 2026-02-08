import requests
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from datetime import date

# 🔑 Tokens
TELEGRAM_TOKEN = "8566985164:AAGBiTnkxM8-eu0IyKRNTQua6OwHUanMmQk"

# Clave de tu dashboard privado
DASHBOARD_API_KEY = "cd649a4b2a22ce2239272c6a896df036"

# URL base de tu dashboard
API_URL = "https://dashboard.api/v1"

# Headers para autenticación con tu dashboard
HEADERS = {
    "Authorization": f"Bearer {DASHBOARD_API_KEY}",
    "Content-Type": "application/json"
}

LEAGUES = {
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,  
    "Bundesliga": 78,
    "Champions": 2
}

# ⚙️ Sistema de suscripción
AUTHORIZED_USERS = set()  # aquí se guardan los UID autorizados
ADMIN_UID = 1690635477     # pon aquí tu propio UID de Telegram 

USER_IDS = {}
USER_PREFS = {}

# ⚽️ Obtener partidos de hoy en una liga desde tu dashboard
def get_today_matches(league_id):
    url = f"{API_URL}/fixtures"
    querystring = {
        "league": league_id,
        "season": "2024",
        "date": str(date.today())
    }
    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        response.raise_for_status()
        data = response.json()
        print("Respuesta del Dashboard:", data)  # Depuración

        matches = []
        if "response" in data and data["response"]:
            for m in data["response"]:
                home = m["teams"]["home"]["name"]
                away = m["teams"]["away"]["name"]
                fixture_id = m["fixture"]["id"]
                matches.append((fixture_id, f"{home} vs {away}"))
        return matches
    except Exception as e:
        print("Error al consultar el dashboard:", e)
        return []

# 📊 Analizar partido
def analyze_match(fixture_id):
    return f"📊 Análisis completo del partido {fixture_id}...\n✅ Apuesta segura simulada."

# 📲 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if user_id not in USER_IDS:
        USER_IDS[user_id] = str(user_id)
        USER_PREFS[user_id] = {"liga": None, "mercado": None}

    await update.message.reply_text(
        f"✨ Hola {user_name}, bienvenido al *Bot de Pronósticos de Fútbol* ⚽️\n\n"
        "📊 Aquí encontrarás análisis detallados y predicciones con alta precisión 🔥\n"
        "🏆 Explora tus ligas favoritas, descubre los partidos del día y recibe recomendaciones seguras.\n\n"
        "🚀 ¡Prepárate para apostar con inteligencia y estilo!\n"
        "👉 Usa /menu para ver todas las opciones disponibles."
    )

# 📲 Comando /userid
async def userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 Tu User ID es: {user_id}")

# 📲 Comando /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == ADMIN_UID:
        await update.message.reply_text(
            "📋 *Menú de Comandos (Admin)*:\n\n"
            "/start – Iniciar el bot\n"
            "/userid – Solicitar tu User ID\n"
            "/menu – Mostrar este menú\n"
            "/ligas – Ver ligas disponibles (solo suscritos)\n"
            "/autorizar <uid> – Autorizar un usuario\n"
            "/desautorizar <uid> – Quitar autorización\n"
        )
    else:
        await update.message.reply_text(
            "📋 *Menú de Comandos*:\n\n"
            "/start – Iniciar el bot\n"
            "/userid – Solicitar tu User ID\n"
            "/menu – Mostrar este menú\n"
            "/ligas – (Solo disponible para usuarios suscritos)\n"
        )

# 📲 Comando /autorizar (solo admin)
async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_UID:
        await update.message.reply_text("🚫 No tienes permisos para usar este comando.")
        return

    try:
        uid_to_add = int(context.args[0])
        AUTHORIZED_USERS.add(uid_to_add)
        await update.message.reply_text(f"✅ Usuario {uid_to_add} autorizado correctamente.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Uso correcto: /autorizar <uid>")

# 📲 Comando /desautorizar (solo admin)
async def desautorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_UID:
        await update.message.reply_text("🚫 No tienes permisos para usar este comando.")
        return

    try:
        uid_to_remove = int(context.args[0])
        if uid_to_remove in AUTHORIZED_USERS:
            AUTHORIZED_USERS.remove(uid_to_remove)
            await update.message.reply_text(f"❌ Usuario {uid_to_remove} desautorizado correctamente.")
        else:
            await update.message.reply_text("⚠️ Ese usuario no estaba autorizado.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Uso correcto: /desautorizar <uid>")

# 📲 Comando /ligas (solo suscritos)
async def ligas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("🚫 No tienes acceso a este comando. Comunícate con el administrador para suscribirte.")
        return

    matches = get_today_matches(39)  # ejemplo con Premier League
    if not matches:
        await update.message.reply_text("⚠️ No se encontraron partidos en el dashboard.")
        return

    keyboard = [[InlineKeyboardButton(match, callback_data=f"match_{fid}")]
                for fid, match in matches]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏆 Selecciona un partido:", reply_markup=reply_markup)

# 📲 Callback de botones (solo suscritos)
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.callback_query.edit_message_text("🚫 No tienes acceso a este comando. Comunícate con el administrador para suscribirte.")
        return

    query = update.callback_query
    await query.answer()

    if query.data.startswith("match_"):
        fixture_id = int(query.data.split("_")[1])
        prediction = analyze_match(fixture_id)
        await query.edit_message_text(text=prediction)

# 🚀 Configuración del bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("userid", userid))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("autorizar", autorizar))
    app.add_handler(CommandHandler("desautorizar", desautorizar))
    app.add_handler(CommandHandler("ligas", ligas))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

# 🔥 Ejecutar el bot
if __name__ == "__main__":
    main()
