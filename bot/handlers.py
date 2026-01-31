import os
import whisper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .vector_store import VectorStore
from .llm_client import LLMClient
from .config import CATEGORIES, get_setting, update_setting

whisper_model = whisper.load_model("base")
vector_store = VectorStore()
llm_client = LLMClient()

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    await update.message.reply_text("🎙️ Transcribing your voice message...")
    
    voice_file = await update.message.voice.get_file()
    audio_path = f"data/{update.message.message_id}.ogg"
    await voice_file.download_to_drive(audio_path)
    
    result = whisper_model.transcribe(audio_path)
    text = result["text"].strip()
    
    categories = llm_client.classify_categories(text, CATEGORIES)
    
    vector_store.add_entry(
        text=text,
        categories=categories,
        user_id=update.message.from_user.id
    )
    
    context_results = vector_store.search(
        query=text,
        user_id=update.message.from_user.id,
        limit=3
    )
    
    context_text = "\n".join([f"- {r.payload['text']}" for r in context_results[:3]])
    
    prompt = f"""Previous related entries:
{context_text}

User just said: "{text}"

Provide a brief, helpful response (2-3 sentences max)."""
    
    response = llm_client.generate(prompt)
    
    await update.message.reply_text(
        f"📝 *Transcribed:*\n{text}\n\n"
        f"🏷️ *Categories:* {', '.join(categories)}\n\n"
        f"💡 *Response:*\n{response}",
        parse_mode="Markdown"
    )
    
    if os.path.exists(audio_path):
        os.remove(audio_path)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text queries"""
    query = update.message.text
    
    category_filter = None
    if ":" in query:
        parts = query.split(":", 1)
        potential_category = parts[0].strip().lower()
        if potential_category in CATEGORIES:
            category_filter = [potential_category]
            query = parts[1].strip()
    
    results = vector_store.search(
        query=query,
        user_id=update.message.from_user.id,
        categories=category_filter,
        limit=5
    )
    
    if not results:
        await update.message.reply_text("No relevant entries found. Start journaling with voice messages!")
        return
    
    context_text = "\n".join([f"- {r.payload['text']}" for r in results])
    
    prompt = f"""User's relevant journal entries:
{context_text}

User asks: "{query}"

Provide a helpful, personalized answer based on their entries."""
    
    response = llm_client.generate(prompt)
    await update.message.reply_text(response)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome = """👋 Welcome to your Voice Journal!

🎙️ Send voice messages to journal your thoughts
💬 Ask questions to search your entries
🏷️ Use "category: question" for filtered search

*Commands:*
/settings - Edit bot settings (LLM, prompt, etc.)
/stats - View your stats
/recent - See recent entries
"""
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    recent = vector_store.get_recent_entries(update.message.from_user.id, limit=100)
    
    category_counts = {}
    for entry in recent:
        for cat in entry.payload.get("categories", []):
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    stats = f"""📊 *Your Journal Stats*

Total entries: {len(recent)}

*Categories:*
"""
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        stats += f"• {cat}: {count}\n"
    
    await update.message.reply_text(stats, parse_mode="Markdown")

async def handle_recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent entries"""
    recent = vector_store.get_recent_entries(update.message.from_user.id, limit=5)
    
    if not recent:
        await update.message.reply_text("No entries yet. Start journaling!")
        return
    
    message = "📝 *Recent Entries:*\n\n"
    for entry in recent:
        timestamp = entry.payload["timestamp"][:10]
        text = entry.payload["text"][:100] + "..." if len(entry.payload["text"]) > 100 else entry.payload["text"]
        cats = ", ".join(entry.payload.get("categories", []))
        message += f"*{timestamp}* ({cats})\n{text}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# --- SETTINGS COMMAND ---

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the settings menu"""
    await show_settings_menu(update)

async def show_settings_menu(update: Update):
    llm_provider = get_setting("llm_provider")
    temp = get_setting("temperature")
    tokens = get_setting("max_tokens")
    
    text = f"""⚙️ *Settings*

*LLM Provider:* {llm_provider.upper()}
*Temperature:* {temp}
*Max Tokens:* {tokens}

Select a setting to edit:"""
    
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
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

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
        await query.edit_message_text("Please send the new System Prompt as a text message. Current prompt is:\n\n" + get_setting("system_prompt"))
        
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
        await update.message.reply_text("✅ System Prompt updated!")
        await show_settings_menu(update)
        return True
    return False
