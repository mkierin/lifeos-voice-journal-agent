import os
import json
import random
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

try:
    import whisper
    whisper_available = True
except ImportError:
    whisper_available = False
    whisper = None

from .vector_store import VectorStore
from .llm_client import LLMClient, JournalDeps
from .config import CATEGORIES, get_setting, update_setting

load_dotenv()

def is_ffmpeg_available():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=stderr=subprocess.DEVNULL)
        return True
    except (FileNotFoundError, Exception):
        return False

ffmpeg_available = is_ffmpeg_available()

if whisper_available:
    try:
        whisper_model = whisper.load_model("base")
    except Exception:
        whisper_available = False
        whisper_model = None
else:
    whisper_model = None

vector_store = VectorStore()
llm_client = LLMClient()

FEEDBACK_PHRASES = [
    "Got it, looking into that...",
    "On it!",
    "Checking your journal...",
    "Thinking...",
    "Got you, one sec...",
    "Processing that...",
    "Let me see...",
    "Searching your entries..."
]

def get_random_feedback():
    return random.choice(FEEDBACK_PHRASES)

def get_result_data(result):
    """Safely get data from pydantic-ai result"""
    if hasattr(result, 'data'):
        return result.data
    if hasattr(result, 'output'):
        return result.output
    return str(result)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    # Quick acknowledgment
    status_msg = await update.message.reply_text(get_random_feedback())
    
    try:
        os.makedirs("data", exist_ok=True)
        voice_file = await update.message.voice.get_file()
        audio_path = f"data/{update.message.message_id}.ogg"
        await voice_file.download_to_drive(audio_path)
        
        # Use local whisper if available AND ffmpeg is present, else fallback to OpenAI API
        if whisper_available and whisper_model and ffmpeg_available:
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: whisper_model.transcribe(audio_path))
            text = result["text"].strip()
        else:
            try:
                text = await llm_client.transcribe(audio_path)
            except Exception as api_err:
                error_msg = "Transcription failed. "
                if not (whisper_available and ffmpeg_available):
                    error_msg += "Requires ffmpeg. "
                await status_msg.edit_text(error_msg)
                raise api_err
        
        # Generate context-aware response using agent with tools
        deps = JournalDeps(
            vector_store=vector_store, 
            user_id=update.message.from_user.id,
            current_date=datetime.now().strftime("%Y-%m-%d %A")
        )
        prompt = f"User just said (via voice): \"{text}\". Please save this appropriately and provide a brief response."
        
        await status_msg.edit_text(get_random_feedback())
        response = await llm_client.agent.run(prompt, deps=deps)
        
        # Final reply without Markdown bolding
        # Voice messages can be extra concise, just the reply
        reply = get_result_data(response)
        await status_msg.edit_text(reply)
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text queries and entries"""
    if await handle_prompt_update(update, context):
        return

    query = update.message.text
    
    # Send quick feedback
    await update.message.reply_chat_action("typing")
    feedback = await update.message.reply_text(get_random_feedback())

    # Let the agent handle the query
    deps = JournalDeps(
        vector_store=vector_store, 
        user_id=update.message.from_user.id,
        current_date=datetime.now().strftime("%Y-%m-%d %A")
    )
    
    try:
        # CRITICAL: Use await run(), NEVER run_sync()
        result = await llm_client.agent.run(query, deps=deps)
        await feedback.edit_text(get_result_data(result))
    except Exception as e:
        await feedback.edit_text(f"Sorry, ran into an issue: {str(e)}")

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome = """Welcome to your Voice Journal!

Send voice or text to journal your thoughts.
Categories like goals, ideas, and fitness are tracked automatically.

Commands:
/settings - Edit bot settings
/stats - View your stats
/recent - See recent entries
"""
    await update.message.reply_text(welcome)

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    recent = vector_store.get_recent_entries(update.message.from_user.id, limit=100)
    
    category_counts = {}
    for entry in recent:
        cat = entry.payload.get("type", "general")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    stats = "Your Journal Stats\n\n"
    stats += f"Total entries: {len(recent)}\n\n"
    stats += "Types:\n"
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        stats += f"- {cat}: {count}\n"
    
    await update.message.reply_text(stats)

async def handle_recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent entries"""
    recent = vector_store.get_recent_entries(update.message.from_user.id, limit=5)
    
    if not recent:
        await update.message.reply_text("No entries yet. Start journaling!")
        return
    
    message = "Recent Entries:\n\n"
    for entry in recent:
        timestamp = entry.payload["timestamp"][:10]
        text = entry.payload["text"][:100] + "..." if len(entry.payload["text"]) > 100 else entry.payload["text"]
        cat = entry.payload.get("type", "general")
        message += f"{timestamp} [{cat}]\n{text}\n\n"
    
    await update.message.reply_text(message)

# --- SETTINGS COMMAND ---

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the settings menu"""
    await show_settings_menu(update)

async def show_settings_menu(update: Update):
    llm_provider = get_setting("llm_provider")
    temp = get_setting("temperature")
    tokens = get_setting("max_tokens")
    
    text = f"Settings\n\n"
    text += f"LLM Provider: {llm_provider.upper()}\n"
    text += f"Temperature: {temp}\n"
    text += f"Max Tokens: {tokens}\n\n"
    text += "Select a setting to edit:"
    
    keyboard = [
        [
            InlineKeyboardButton("Switch LLM Provider", callback_data="set_provider"),
        ],
        [
            InlineKeyboardButton("Adjust Temperature", callback_data="set_temp"),
            InlineKeyboardButton("Adjust Max Tokens", callback_data="set_tokens"),
        ],
        [
            InlineKeyboardButton("Edit System Prompt", callback_data="set_prompt"),
        ],
        [InlineKeyboardButton("Close", callback_data="close_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "set_provider":
        current = get_setting("llm_provider")
        new = "openai" if current == "deepseek" else "deepseek"
        update_setting("llm_provider", new)
        await show_settings_menu(update)
        
    elif query.data == "set_temp":
        keyboard = [
            [InlineKeyboardButton("0.3 (More Factual)", callback_data="temp_0.3")],
            [InlineKeyboardButton("0.7 (Balanced)", callback_data="temp_0.7")],
            [InlineKeyboardButton("1.0 (Creative)", callback_data="temp_1.0")],
            [InlineKeyboardButton("Back", callback_data="back_to_settings")]
        ]
        await query.edit_message_text("Select Temperature:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("temp_"):
        temp = float(query.data.split("_")[1])
        update_setting("temperature", temp)
        await show_settings_menu(update)
        
    elif query.data == "set_tokens":
        keyboard = [
            [InlineKeyboardButton("100", callback_data="tokens_100"), InlineKeyboardButton("300", callback_data="tokens_300")],
            [InlineKeyboardButton("500", callback_data="tokens_500"), InlineKeyboardButton("1000", callback_data="tokens_1000")],
            [InlineKeyboardButton("Back", callback_data="back_to_settings")]
        ]
        await query.edit_message_text("Select Max Tokens:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("tokens_"):
        tokens = int(query.data.split("_")[1])
        update_setting("max_tokens", tokens)
        await show_settings_menu(update)
        
    elif query.data == "set_prompt":
        context.user_data["awaiting_prompt"] = True
        await query.edit_message_text("Send the new System Prompt. Current is:\n\n" + get_setting("system_prompt"))
        
    elif query.data == "back_to_settings":
        await show_settings_menu(update)
        
    elif query.data == "close_settings":
        await query.delete_message()

async def handle_prompt_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text message when awaiting a new prompt"""
    if context.user_data.get("awaiting_prompt"):
        new_prompt = update.message.text
        update_setting("system_prompt", new_prompt)
        context.user_data["awaiting_prompt"] = False
        await update.message.reply_text("System Prompt updated!")
        await show_settings_menu(update)
        return True
    return False
