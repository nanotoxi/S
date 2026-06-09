import logging
from telegram import BotCommand
from telegram.ext import Application

logger = logging.getLogger(__name__)

async def set_bot_commands(application: Application):
    """
    Sets the command menu in the Telegram app UI.
    """
    commands = [
        BotCommand("start", "Start the bot and choose your role"),
        BotCommand("post_job", "Post a new Job Description (Employer)"),
        BotCommand("upload_resume", "Upload your resume (Candidate)"),
        BotCommand("matches", "View top candidate matches (Employer)"),
        BotCommand("my_profile", "View/Edit your profile (Candidate)"),
        BotCommand("my_jobs", "Manage your job postings (Employer)"),
        BotCommand("cancel", "Cancel the current action")
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot command menu updated successfully.")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")
