import logging
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
    handle_prompt_update
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def message_handler(update, context):
    # Try handling as prompt update first
    if await handle_prompt_update(update, context):
        return
    # Otherwise handle as normal text query
    await handle_text(update, context)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("stats", handle_stats))
    app.add_handler(CommandHandler("recent", handle_recent))
    app.add_handler(CommandHandler("settings", handle_settings))
    
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logging.info("🚀 Voice Journal Bot started!")
    app.run_polling()

if __name__ == '__main__':
    main()
