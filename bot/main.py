import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .config import TELEGRAM_TOKEN
from .handlers import (
    handle_voice,
    handle_text,
    handle_start,
    handle_stats,
    handle_recent,
    handle_settings,
    handle_callback,
    handle_prompt_update,
    handle_reminders
)
from .reminder_scheduler import ReminderScheduler

# Configure logging to both console and file
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.error(f'Update "{update}" caused error "{context.error}"', exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("Sorry, I encountered an internal error. I've logged it for my human to check.")

async def message_handler(update, context):
    # Try handling as prompt update first
    if await handle_prompt_update(update, context):
        return
    # Otherwise handle as normal text query
    await handle_text(update, context)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Initialize reminder scheduler
    scheduler = ReminderScheduler(app.bot)
    scheduler.start()

    # Register error handler
    app.add_error_handler(error_handler)

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("stats", handle_stats))
    app.add_handler(CommandHandler("recent", handle_recent))
    app.add_handler(CommandHandler("settings", handle_settings))
    app.add_handler(CommandHandler("reminders", handle_reminders))

    app.add_handler(CallbackQueryHandler(handle_callback))

    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logging.info("🚀 Voice Journal Bot started!")
    app.run_polling()

if __name__ == '__main__':
    main()
