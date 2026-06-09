import logging
import os
import json
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from services.resume_parser import resume_parser
from services.llm import llm_service
from services.embedder import embedder
from db.connection import db

logger = logging.getLogger(__name__)

UPLOAD_RESUME, FILL_GAP = range(2)

async def start_resume_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} started resume upload wizard")
    await update.message.reply_text(
        "Please upload your resume (PDF or DOCX format). 📄\n"
        "I'll parse it and help you fill in any missing details."
    )
    return UPLOAD_RESUME

async def handle_resume_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received document/message in UPLOAD_RESUME state from user {update.effective_user.id}")
    
    if not update.message.document:
        await update.message.reply_text("Please upload your resume as a **file** (PDF or DOCX).")
        return UPLOAD_RESUME

    document = update.message.document
    file_name = document.file_name
    
    if not (file_name.lower().endswith('.pdf') or file_name.lower().endswith('.docx')):
        await update.message.reply_text("Please upload a PDF or DOCX file.")
        return UPLOAD_RESUME

    await update.message.reply_text("Received! Parsing your resume now... ⏳")
    
    file = await context.bot.get_file(document.file_id)
    file_path = f"temp_{document.file_id}_{file_name}"
    await file.download_to_drive(file_path)
    
    try:
        raw_text = resume_parser.extract_text(file_path)
        if not raw_text:
            await update.message.reply_text("Sorry, I couldn't extract text from this file. Please try a different version.")
            return ConversationHandler.END

        structured_json_str = await llm_service.parse_resume(raw_text)
        structured_data = json.loads(structured_json_str)
        context.user_data['temp_resume_data'] = structured_data
        context.user_data['temp_raw_text'] = raw_text

        # Gap Analysis
        gap_json_str = await llm_service.identify_resume_gaps(structured_data)
        gap_data = json.loads(gap_json_str)
        context.user_data['gaps'] = gap_data.get('gaps', [])
        
        if context.user_data['gaps']:
            gap = context.user_data['gaps'].pop(0)
            context.user_data['current_gap'] = gap
            await update.message.reply_text(
                f"I've analyzed your resume! To make it even better for employers, could you tell me:\n\n"
                f"👉 {gap['question']}"
            )
            return FILL_GAP
        else:
            return await finalize_profile(update, context)
            
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def handle_gap_fill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_answer = update.message.text
    answer_lower = raw_answer.strip().lower()
    gap = context.user_data.get('current_gap')
    field = gap.get('field', '').lower()
    
    # Detect if the user is saying they don't have it
    negative_indicators = ["no", "none", "don't have", "n/a", "na", "skip", "i don't have", "not available"]
    is_negative = any(indicator == answer_lower or f" {indicator} " in f" {answer_lower} " for indicator in negative_indicators)
    
    final_value = "Not Provided" if is_negative else raw_answer
    
    data = context.user_data['temp_resume_data']
    
    # Map back to the correct path in the JSON if possible
    if "linkedin" in field:
        data.setdefault('social', {})['linkedin'] = final_value
    elif "github" in field:
        data.setdefault('social', {})['github'] = final_value
    elif "instagram" in field:
        data.setdefault('social', {})['instagram'] = final_value
    elif "portfolio" in field:
        data.setdefault('social', {})['portfolio'] = final_value
    elif "summary" in field:
        data['summary'] = final_value
    else:
        # Generic enrichment storage
        if 'enrichment' not in data:
            data['enrichment'] = []
        data['enrichment'].append({"field": field, "answer": final_value})
    
    if context.user_data.get('gaps'):
        next_gap = context.user_data['gaps'].pop(0)
        context.user_data['current_gap'] = next_gap
        await update.message.reply_text(next_gap['question'])
        return FILL_GAP
    else:
        return await finalize_profile(update, context)

async def finalize_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = context.user_data['temp_raw_text']
    structured_data = context.user_data['temp_resume_data']
    
    # Generate embedding
    embedding_list = embedder.get_embedding(raw_text)
    embedding_str = str(embedding_list) if embedding_list else None

    # Save to DB
    user_id = update.effective_user.id
    await db.execute(
        """
        INSERT INTO candidates (user_id, resume_raw, resume_structured, embedding, profile_complete)
        VALUES ($1, $2, $3, $4, true)
        ON CONFLICT (user_id) DO UPDATE
        SET resume_raw = $2, resume_structured = $3, embedding = $4, updated_at = now()
        """,
        user_id, raw_text, json.dumps(structured_data), embedding_str
    )

    await update.message.reply_text(
        f"Done! I've updated your profile with the new details. ✨\n\n"
        "Your profile is now complete and active."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Upload cancelled.")
    return ConversationHandler.END

async def start_resume_upload_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} triggered resume upload directly.")
    return await handle_resume_document(update, context)

resume_wizard_handler = ConversationHandler(
    entry_points=[
        CommandHandler("upload_resume", start_resume_upload),
        MessageHandler(filters.Document.ALL | filters.ATTACHMENT, start_resume_upload_direct)
    ],
    states={
        UPLOAD_RESUME: [MessageHandler(filters.Document.ALL | filters.ATTACHMENT, handle_resume_document)],
        FILL_GAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gap_fill)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
    per_chat=True,
    per_user=True
)
