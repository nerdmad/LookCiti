from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
from text_generator import call_response

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
BOT_USERNAME = "@LookCitiBot"

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('thighs🤤🤤🤤')

async def generate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(call_response().text)

if __name__ == '__main__':
    print("Starting bot...")
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd)) #also MessageHandler exists
    app.add_handler(CommandHandler("ai", generate_cmd))

    app.run_polling()