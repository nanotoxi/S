import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.connection import db

logger = logging.getLogger(__name__)

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    candidate = await db.fetchrow(
        "SELECT resume_structured, visible FROM candidates WHERE user_id = $1", 
        user_id
    )
    
    if not candidate:
        await update.message.reply_text("You haven't uploaded a resume yet. Use /upload_resume to get started!")
        return
        
    data = candidate['resume_structured']
    personal = data.get('personal', {})
    skills = data.get('skills', {}).get('technical', [])
    
    status = "Visible 🟢" if candidate['visible'] else "Hidden 🔴"
    
    text = (
        f"👤 **Your Profile**\n\n"
        f"**Name:** {personal.get('name', 'N/A')}\n"
        f"**Email:** {personal.get('email', 'N/A')}\n"
        f"**Status:** {status}\n\n"
        f"**Top Skills:** {', '.join(skills[:5]) if skills else 'N/A'}\n\n"
        "What would you like to do?"
    )
    
    keyboard = [
        [InlineKeyboardButton("Toggle Visibility 👁‍🗨", callback_data="toggle_visibility")],
        [InlineKeyboardButton("Update Resume 📄", callback_data="update_resume_start")],
        [InlineKeyboardButton("Delete Profile 🗑", callback_data="confirm_delete_profile")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def my_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    jds = await db.fetch(
        """
        SELECT jd.id, jd.title, jd.status, 
        (SELECT COUNT(*) FROM matches WHERE jd_id = jd.id) as match_count
        FROM job_descriptions jd
        JOIN employers e ON jd.employer_id = e.id
        WHERE e.user_id = $1
        ORDER BY jd.created_at DESC
        """,
        user_id
    )
    
    if not jds:
        await update.message.reply_text("You haven't posted any jobs yet. Use /post_job to start hiring!")
        return
        
    text = "💼 **Your Job Postings**\n\n"
    keyboard = []
    
    for jd in jds:
        status_icon = "🟢" if jd['status'] == 'active' else "🔴"
        text += f"{status_icon} **{jd['title']}** ({jd['match_count']} matches)\n"
        keyboard.append([InlineKeyboardButton(f"Manage {jd['title']}", callback_data=f"manage_jd_{jd['id']}")])
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def profile_actions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "toggle_visibility":
        await db.execute(
            "UPDATE candidates SET visible = NOT visible WHERE user_id = $1", 
            user_id
        )
        await query.edit_message_text("Visibility updated! Use /my_profile to see current status.")
    
    elif query.data == "confirm_delete_profile":
        keyboard = [[
            InlineKeyboardButton("Yes, Delete 🗑", callback_data="delete_profile_final"),
            InlineKeyboardButton("Cancel", callback_data="cancel_delete")
        ]]
        await query.edit_message_text("Are you sure you want to delete your profile? This cannot be undone.", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "delete_profile_final":
        await db.execute("DELETE FROM candidates WHERE user_id = $1", user_id)
        await query.edit_message_text("Your profile has been deleted. 🫡")
