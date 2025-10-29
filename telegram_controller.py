from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, MessageHandler, filters
import asyncio
from dotenv import load_dotenv
import os
from text_generator import call_response

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
BOT_USERNAME = "@LookCitiBot"
longitude = None
latitude = None

#text generator
async def generate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: #ai intergration test
    await update.message.reply_text(call_response().text)

#button creation and option handling
async def start_buttons(update: Update, context: CallbackContext):
    keyboard = [
        [
        KeyboardButton("Test 1"), KeyboardButton("Test 2") #row 1
        ],
        [
        KeyboardButton("give location?", request_location=True), KeyboardButton("secret option") #row 2
        ]
    ]
    reply_menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) #i noticed a bug when using the menu on mobile, so i might need to fix that
    await update.message.reply_text("Please choose options listed below:", reply_markup=reply_menu)
    
async def button_handling(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "secret option":
        print("user has used secret option")
        await update.message.reply_text('thighs🤤🤤🤤')
    else:
        await update.message.reply_text(f"im gonna touch you in this way: {text}")

async def location_handling(update: Update, context: CallbackContext):
    global location
    location = update.message.location
    if location is None:
        print("location not found")
        await update.message.reply_text(f"Location not identified, please, enable gps in settings or try again later.")
    else:
        print(location)
        global latitude, longitude
        latitude = location.latitude
        longitude = location.longitude
        await update.message.reply_text(f"Location found, latitude={latitude}, longitude={longitude}")



#if run from this file
if __name__ == '__main__':
    print("Starting bot...")
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start_buttons)) #also MessageHandler exists
    app.add_handler(CommandHandler("ai", generate_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handling))
    app.add_handler(MessageHandler(filters.LOCATION & ~filters.COMMAND, location_handling))

    print("Polling...")
    app.run_polling()