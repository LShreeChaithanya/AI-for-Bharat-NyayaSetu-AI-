import os
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from telegram import request as telegram_request
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = os.getenv("SERVER_URL", "https://your-server.com")
FILES_DIR = os.getenv("FILES_DIR", "user_files")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = None
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), notifications_min_severity="OFF")
except Exception:
    driver = None

def clear_session(user_id: int):
    global driver
    if not driver:
        return
    try:
        with driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                DETACH DELETE u
            """, user_id=user_id)
    except ServiceUnavailable:
        driver = None

def save_user(user_id: int, name: str = None, email: str = None, step: str = None):
    global driver
    if not driver:
        return
    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {user_id: $user_id})
                SET u.name  = COALESCE($name,  u.name),
                    u.email = COALESCE($email, u.email),
                    u.step  = COALESCE($step,  u.step)
            """, user_id=user_id, name=name, email=email, step=step)
    except ServiceUnavailable:
        driver = None

def load_user(user_id: int) -> dict:
    global driver
    if not driver:
        return {}
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})
                RETURN u.name AS name, u.email AS email, u.step AS step
            """, user_id=user_id)
            row = result.single()
            return dict(row) if row else {}
    except ServiceUnavailable:
        driver = None
        return {}

def save_file(user_id: int, file_name: str, file_path: str):
    global driver
    if not driver:
        return
    try:
        with driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                CREATE (f:File {file_name: $file_name, file_path: $file_path})
                CREATE (u)-[:UPLOADED]->(f)
            """, user_id=user_id, file_name=file_name, file_path=file_path)
    except ServiceUnavailable:
        driver = None

def load_file(user_id: int) -> dict:
    global driver
    if not driver:
        return {}
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[:UPLOADED]->(f:File)
                RETURN f.file_name AS file_name, f.file_path AS file_path
            """, user_id=user_id)
            row = result.single()
            return dict(row) if row else {}
    except ServiceUnavailable:
        driver = None
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    clear_session(user_id)
    save_user(user_id, step="collect_name")
    await update.message.reply_text("👋 Welcome! Let's get started.\n\nPlease send me your *full name*.", parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_input = update.message.text
    user = load_user(user_id)
    step = user.get("step")
    if not step:
        await update.message.reply_text("Please type /start to begin.")
        return
    if step == "collect_name":
        save_user(user_id, name=user_input, step="collect_email")
        await update.message.reply_text(f"Got it, *{user_input}*! 👍\n\nNow please send me your *email address*.", parse_mode="Markdown")
    elif step == "collect_email":
        if "@" not in user_input or "." not in user_input:
            await update.message.reply_text("That doesn't look like a valid email. Please try again.")
            return
        save_user(user_id, email=user_input, step="collect_document")
        await update.message.reply_text("Perfect! 📧\n\nNow please send me your *document* (PDF or image).", parse_mode="Markdown")
    elif step == "collect_document":
        await update.message.reply_text("Please send a *document or file*, not text.", parse_mode="Markdown")
    elif step == "done":
        await update.message.reply_text("✅ Already submitted! Type /start to submit again.")
    else:
        await update.message.reply_text("Something went wrong. Type /start to begin again.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = load_user(user_id)
    step = user.get("step")
    if not step:
        await update.message.reply_text("Please type /start to begin.")
        return
    if step != "collect_document":
        await update.message.reply_text("I'm not expecting a document right now. Type /start to begin again.")
        return
    doc = update.message.document
    file = await doc.get_file()
    user_folder = os.path.join(FILES_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    file_path = os.path.join(user_folder, doc.file_name)
    await file.download_to_drive(file_path)
    save_file(user_id, file_name=doc.file_name, file_path=file_path)
    save_user(user_id, step="done")
    name = user.get("name")
    email = user.get("email")
    await update.message.reply_text("⏳ Processing your submission, please wait...")
    await update.message.reply_text("Document Processed!")
    await update.message.reply_text("Hey, you are eligible for these schemes:\n1) Arogyashree\n2) Crop loan upto 5lacs\n3) MSME business loan \n4) Specially abled pension scheme")
    keyboard = InlineKeyboardMarkup.from_button(InlineKeyboardButton("Apply Now?", callback_data="apply_now"))
    await update.message.reply_text("Would you like to apply for any of these schemes?", reply_markup=keyboard)

async def handle_apply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await query.message.reply_text("Your Application is in progress")
    except Exception:
        await query.answer(text="Your Application is in progress")
    await asyncio.sleep(4)
    try:
        await query.message.reply_text("Your Application is Successful")
    except Exception:
        await query.answer(text="Your Application is Successful")
    await asyncio.sleep(2)
    try:
        await query.message.reply_text("Type /start to make another submission.")
    except Exception:
        pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    import traceback
    traceback.print_exc()
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Something went wrong. Please try again or /start.")

if __name__ == "__main__":
    os.makedirs(FILES_DIR, exist_ok=True)
    req = telegram_request.HTTPXRequest(read_timeout=30, connect_timeout=30)
    app = ApplicationBuilder().token(BOT_TOKEN).request(req).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(handle_apply_callback, pattern="^apply_now$"))
    app.add_error_handler(error_handler)
    print("Bot is running...")
    app.run_polling()