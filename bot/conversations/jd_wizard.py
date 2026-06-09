import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from services.llm import llm_service
from services.embedder import embedder
from services.rag import rag_engine
import services.notifier as notifier_module
from db.connection import db

logger = logging.getLogger(__name__)

(
    COMPANY_NAME,
    ROLE_TITLE,
    EMPLOYMENT_TYPE,
    LOCATION,
    EXPERIENCE,
    RESPONSIBILITIES,
    SKILLS,
    CONFIRM_JD
) = range(8)

async def start_jd_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Let's create a Job Description! 📝\nWhat is the **Company Name**?")
    context.user_data['jd_data'] = {}
    return COMPANY_NAME

async def handle_company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['jd_data']['company_name'] = update.message.text
    await update.message.reply_text("Got it. What is the **Job Title** or Role?")
    return ROLE_TITLE

async def handle_role_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['jd_data']['title'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Full-time", callback_data="Full-time"), InlineKeyboardButton("Part-time", callback_data="Part-time")],
        [InlineKeyboardButton("Contract", callback_data="Contract"), InlineKeyboardButton("Internship", callback_data="Internship")]
    ]
    await update.message.reply_text("What is the **Employment Type**?", reply_markup=InlineKeyboardMarkup(keyboard))
    return EMPLOYMENT_TYPE

async def handle_employment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['jd_data']['employment_type'] = query.data
    await query.edit_message_text(f"Selected: {query.data}. What is the **Location** (e.g., Remote, Hybrid, or City)?")
    return LOCATION

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['jd_data']['location'] = update.message.text
    await update.message.reply_text("How many **years of experience** are required?")
    return EXPERIENCE

async def handle_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['jd_data']['experience'] = update.message.text
    await update.message.reply_text("Briefly list the key **Responsibilities** (you can send them as bullet points).")
    return RESPONSIBILITIES

async def handle_responsibilities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['jd_data']['responsibilities'] = update.message.text
    await update.message.reply_text("What are the **Must-have Skills**?")
    return SKILLS

async def handle_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['jd_data']['skills'] = update.message.text
    await update.message.reply_text("Generating your professional JD now... ⏳")
    
    full_jd = await llm_service.generate_jd(context.user_data['jd_data'])
    context.user_data['full_jd'] = full_jd
    
    keyboard = [[InlineKeyboardButton("Approve ✅", callback_data="approve_jd"), InlineKeyboardButton("Cancel ❌", callback_data="cancel_jd")]]
    await update.message.reply_text(f"**Draft Job Description:**\n\n{full_jd}", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_JD

async def confirm_jd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "approve_jd":
        user_id = query.from_user.id
        
        # Generate embedding
        embedding_list = embedder.get_embedding(context.user_data['full_jd'])
        embedding_str = str(embedding_list) if embedding_list else None
        
        employer_row = await db.fetchrow("SELECT id FROM employers WHERE user_id = $1", user_id)
        
        if not employer_row:
            # Create employer profile if missing (simplified)
            employer_id = await db.fetchval(
                "INSERT INTO employers (user_id, company_name) VALUES ($1, $2) RETURNING id",
                user_id, context.user_data['jd_data']['company_name']
            )
        else:
            employer_id = employer_row['id']

        jd_id = await db.fetchval(
            """
            INSERT INTO job_descriptions (employer_id, title, full_jd, structured_jd, embedding, status)
            VALUES ($1, $2, $3, $4, $5, 'active')
            RETURNING id
            """,
            employer_id, context.user_data['jd_data']['title'], context.user_data['full_jd'], 
            json.dumps(context.user_data['jd_data']), embedding_str
        )

        # Proactive Matching
        matches = await rag_engine.find_matching_candidates(embedding_str, limit=10)
        if matches and notifier_module.notifier:
            await notifier_module.notifier.notify_candidates_of_new_jd(
                jd_id, context.user_data['jd_data']['title'], matches
            )
        
        await query.edit_message_text("Success! Your JD is now live and I've notified matching candidates. 🚀")
    else:
        await query.edit_message_text("JD generation cancelled.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("JD Wizard cancelled.")
    return ConversationHandler.END

jd_wizard_handler = ConversationHandler(
    entry_points=[CommandHandler("post_job", start_jd_wizard)],
    states={
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_company_name)],
        ROLE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role_title)],
        EMPLOYMENT_TYPE: [CallbackQueryHandler(handle_employment_type)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location)],
        EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_experience)],
        RESPONSIBILITIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_responsibilities)],
        SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_skills)],
        CONFIRM_JD: [CallbackQueryHandler(confirm_jd)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
