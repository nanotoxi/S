import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.connection import db

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Save or update user in DB
    await db.execute(
        """
        INSERT INTO users (id, username, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE
        SET username = $2, first_name = $3, last_name = $4, updated_at = now()
        """,
        user.id, user.username, user.first_name, user.last_name
    )

    keyboard = [
        [
            InlineKeyboardButton("I'm Hiring (Employer)", callback_data="type_employer"),
            InlineKeyboardButton("I'm Looking for Work (Candidate)", callback_data="type_candidate"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Hi {user.first_name}! Welcome to Sath Bot. 🤝\n\n"
        "I'm here to help you match with the best talent or the perfect job.\n\n"
        "To get started, please tell me: are you hiring or looking for work?",
        reply_markup=reply_markup
    )

async def user_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_type = "employer" if query.data == "type_employer" else "candidate"
    user_id = query.from_user.id
    
    await db.execute(
        "UPDATE users SET user_type = $1 WHERE id = $2",
        user_type, user_id
    )

    if user_type == "employer":
        await query.edit_message_text(
            "Great! You're set up as an Employer. 🏢\n\n"
            "Use /post_job to start creating a Job Description."
        )
    else:
        await query.edit_message_text(
            "Awesome! You're set up as a Candidate. 👨‍💻\n\n"
            "Use /upload_resume to get your profile ready."
        )
