import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.rag import rag_engine
from db.connection import db

logger = logging.getLogger(__name__)

async def view_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Get active JDs for this employer
    jds = await db.fetch(
        """
        SELECT jd.id, jd.title, jd.embedding 
        FROM job_descriptions jd
        JOIN employers e ON jd.employer_id = e.id
        WHERE e.user_id = $1 AND jd.status = 'active'
        """,
        user_id
    )
    
    if not jds:
        await update.message.reply_text("You don't have any active job descriptions. Use /post_job to create one.")
        return

    for jd in jds:
        matches = await rag_engine.find_matching_candidates(jd['embedding'], limit=5)
        
        if not matches:
            await update.message.reply_text(f"No matches found for **{jd['title']}** yet. ⏳")
            continue
            
        text = f"🔝 **Top Matches for {jd['title']}:**\n\n"
        for i, match in enumerate(matches, 1):
            name = match['resume_structured'].get('personal', {}).get('name', 'Candidate')
            text += f"{i}. {name} (Score: {match['score']:.2f})\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')

async def match_feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("match_interest_"):
        jd_id = int(data.split("_")[-1])
        await query.edit_message_text("Great! I've notified the employer of your interest. 🚀")
        # Save action to DB
        # user_id = query.from_user.id
        # ... logic to log interest ...
    elif data.startswith("match_not_interest_"):
        await query.edit_message_text("No problem! I'll keep looking for other opportunities.")
