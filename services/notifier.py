import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db.connection import db

logger = logging.getLogger(__name__)

class NotifierService:
    def __init__(self, bot_application):
        self.app = bot_application

    async def notify_candidates_of_new_jd(self, jd_id, jd_title, matches):
        """
        Notify candidates whose profiles match a newly posted JD.
        """
        for match in matches:
            user_id = match['user_id']
            score = match['score']
            
            text = (
                f"🎯 **New Job Match!**\n\n"
                f"A new position for **{jd_title}** has been posted that matches your profile.\n"
                f"Match Score: {score:.2f}\n\n"
                f"Are you interested?"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("Interested ✅", callback_data=f"match_interest_{jd_id}"),
                    InlineKeyboardButton("Not Interested ❌", callback_data=f"match_not_interest_{jd_id}")
                ]
            ]
            
            try:
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")

    async def notify_employer_of_new_candidate(self, candidate_user_id, matches):
        """
        Notify employers when a new candidate matches their active JDs.
        """
        for match in matches:
            # Note: This would require a reverse mapping or query to find the employer's user_id
            # For simplicity, we can log it or implement a specific 'match found' notification
            pass

# We will initialize this in main.py
notifier = None
