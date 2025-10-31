from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, MessageHandler, filters
import asyncio
from dotenv import load_dotenv
import os
from text_generator import call_response
from foliumconf.map_gen import generate_map, find_closest
import random

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
BOT_USERNAME = "@LookCitiBot"
longitude = None
latitude = None

#text generator
async def generate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: #ai intergration test
    await update.message.reply_text(call_response())

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Добро пожаловать в бот LookCiti! Для начала работы напишите "/buttons".')

#button creation and option handling
async def start_buttons(update: Update, context: CallbackContext):
    keyboard = [
        [
        KeyboardButton("О Боте") #row 1
        ],
        [
        KeyboardButton("Показать ближайшие интересные места", request_location=True), KeyboardButton("secret option") #row 2
        ]
    ]
    reply_menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) #i noticed a bug when using the menu on mobile, so i might need to fix that
    await update.message.reply_text("Please choose options listed below:", reply_markup=reply_menu)
    
async def button_handling(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "secret option":
        print("user has used secret option")
        await update.message.reply_text('thighs🤤🤤🤤')
    elif text == "О Боте":
        await update.message.reply_text(f"Nothing here yet... however you can check our github:\nhttps://github.com/nerdmad/LookCiti")
    else:
        await update.message.reply_photo(random.choice(os.getenv("LST").split(' ')))
    

async def location_handling(update: Update, context: CallbackContext):
    global location
    location = update.message.location
    if location is None:
        await update.message.reply_text(f"Location not identified, please, enable gps in settings or try again later. Switching to default location...")
    else:
        print(location)
        global latitude, longitude
        latitude = location.latitude
        longitude = location.longitude
        await update.message.reply_text(f"Location found, latitude={latitude}, longitude={longitude}. Generating map, please wait...")
        generate_map(latitude, longitude)
        await update.message.reply_photo('foliumconf/img.png')
        await asyncio.sleep(2)
        await update.message.reply_text(find_closest(latitude, longitude))

#if run from this file
if __name__ == '__main__':
    print("Starting bot...")
    app = ApplicationBuilder().token(API_TOKEN).read_timeout(30).write_timeout(30).build()

    app.add_handler(CommandHandler("start", hello)) #also MessageHandler exists
    app.add_handler(CommandHandler("buttons", start_buttons))
    app.add_handler(CommandHandler("ai", generate_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handling))
    app.add_handler(MessageHandler(filters.LOCATION & ~filters.COMMAND, location_handling))

    print("Polling...")
    app.run_polling()