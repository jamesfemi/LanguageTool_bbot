import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging so you can see errors on Render's dashboard
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# LanguageTool Free Public API endpoint
LT_API_URL = "https://api.languagetool.org/v2/check"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when a user sends /start"""
    await update.message.reply_text(
        "👋 Hello! I am your LanguageTool Grammar Assistant.\n\n"
        "Send me any text in English, Spanish, French, or German, and I will check it for spelling and grammar mistakes!"
    )

async def check_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming text and checks it using LanguageTool"""
    text_to_check = update.message.text
    
    # Don't check tiny messages or commands
    if len(text_to_check.strip()) < 2 or text_to_check.startswith('/'):
        return

    # Let the user know the bot is working
    await update.message.reply_chat_action(action="typing")

    try:
        # Request structure for LanguageTool API (auto-detects the language)
        payload = {
            "text": text_to_check,
            "language": "auto"
        }
        
        response = requests.post(LT_API_URL, data=payload)
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Sorry, I'm having trouble reaching the grammar checker right now.")
            return
            
        data = response.json()
        matches = data.get("matches", [])

        if not matches:
            await update.message.reply_text("✅ Perfect! No grammar or spelling mistakes detected.")
            return

        # Build a clean reply highlighting mistakes and corrections
        reply = "📝 **Found some areas to improve:**\n\n"
        for idx, match in enumerate(matches[:5], 1):  # Limit to top 5 errors to avoid huge texts
            message = match.get("message", "Issue found")
            replacements = [r.get("value") for r in match.get("replacements", [])[:3]]
            
            # Extract the specific word causing the issue
            offset = match.get("offset", 0)
            length = match.get("length", 0)
            error_text = text_to_check[offset:offset+length]

            reply += f"{idx}. ❌ **\"{error_text}\"**\n"
            reply += f"💡 *Issue:* {message}\n"
            if replacements:
                reply += f"✅ *Suggestions:* {', '.join(replacements)}\n"
            reply += "\n"

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error checking grammar: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your text.")

def main():
    # Grab the token from Environment Variables (set securely on Render)
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TOKEN:
        logger.error("No TELEGRAM_TOKEN found in environment variables!")
        return

    # Build and start the bot application
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_grammar))

    # Run via polling (ideal for free hosting instances)
    application.run_polling()

if __name__ == "__main__":
    main()
