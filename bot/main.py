import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters,
    ContextTypes
)
from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers.start import start, user_type_callback
from bot.handlers.employer import view_matches, match_feedback_callback
from bot.handlers.candidate import my_profile, my_jobs, profile_actions_callback
from bot.conversations.resume_wizard import resume_wizard_handler
from bot.conversations.jd_wizard import jd_wizard_handler
from services.notifier import NotifierService
import services.notifier as notifier_module
from utils.set_commands import set_bot_commands
from db.connection import db

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    await db.connect()
    notifier_module.notifier = NotifierService(application)
    await set_bot_commands(application)
    logger.info("Bot started, DB connected, and commands set.")

async def post_stop(application):
    await db.disconnect()
    logger.info("Bot stopped and DB disconnected.")

async def global_debug_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if user:
        has_doc = bool(message.document) if message else False
        logger.info(f"DEBUG: Received update from {user.id} ({user.username}). Has document: {has_doc}")

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).read_timeout(30).connect_timeout(30).post_init(post_init).post_stop(post_stop).build()

    # Global debug handler - lowest priority (group -1)
    application.add_handler(MessageHandler(filters.ALL, global_debug_logger), group=-1)

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("matches", view_matches))
    application.add_handler(CommandHandler("my_profile", my_profile))
    application.add_handler(CommandHandler("my_jobs", my_jobs))
    application.add_handler(resume_wizard_handler)
    application.add_handler(jd_wizard_handler)
    application.add_handler(CallbackQueryHandler(profile_actions_callback, pattern="^(toggle_visibility|confirm_delete_profile|delete_profile_final|cancel_delete)"))
    application.add_handler(CallbackQueryHandler(match_feedback_callback, pattern="^match_"))
    application.add_handler(CallbackQueryHandler(user_type_callback, pattern="^type_"))

    application.run_polling()

if __name__ == '__main__':
    main()
