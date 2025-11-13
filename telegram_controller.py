from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, MessageHandler, CallbackQueryHandler, filters
import asyncio
import random
import os
import logging
from dotenv import load_dotenv
from text_generator import call_response #???
from foliumconf.map_gen import generate_map, find_closest #???

load_dotenv()
logging.basicConfig(level=logging.INFO, filename='logs.log', filemode="w",
                    format="%(asctime)s - %(levelname)s - %(message)s")
for name in ["telegram", "telegram.bot", "telegram.ext", "httpx", "urllib3"]:
    logging.getLogger(name).setLevel(logging.WARNING)

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
        KeyboardButton("О Боте"), KeyboardButton("secret option") #row 1
        ],
        [
        KeyboardButton("Показать ближайшие интересные места", request_location=True), KeyboardButton("Места (manual)") #row 2
        ]
    ]
    reply_menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Please choose options listed below:", reply_markup=reply_menu)
    
async def button_handling(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "secret option":
        logging.info("user has used secret option")
        await update.message.reply_text('thighs🤤🤤🤤')
    elif text == "О Боте":
        await update.message.reply_text(f"Nothing here yet... however you can check our github:\nhttps://github.com/nerdmad/LookCiti")
    elif text == "Места (manual)":
        await update.message.reply_text(f'Switching to manual mode...\nPlease, type in your location in this format:\n"latitude=xx.xxxxx longitude=yy.yyyyy" (decimal points are not required)')
    
    elif text.startswith("latitude="):
        global latitude, longitude
        text = update.message.text
        text = text.replace('latitude=', '')
        text = text.replace('longitude=', '')
        location = text.split(' ')
        logging.info(location)
        latitude, longitude = float(location[0]), float(location[1])
        await update.message.reply_text(f"Location found, latitude={latitude}, longitude={longitude}. Generating map, please wait...")
        generate_map(latitude, longitude)
        await update.message.reply_photo('foliumconf/img.png')
        await update.message.reply_text(f'Interactive version is here: {public_url}')
        #output phase
        global name_list
        name_list = find_closest(latitude, longitude, 'list')
        if len(name_list) == 0:
            await update.message.reply_text("Nothing found. Maybe you used VPN or misspelled latitude/longitude?")
        else:
            keyboard = []
            for i in range(len(name_list)): #auto-constructing buttons for an upcoming message
                keyboard.append([])
                keyboard[i].append(InlineKeyboardButton(name_list[i], callback_data=str(i)))
            global reply_menu
            reply_menu = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(find_closest(latitude, longitude, 'ans'), reply_markup=reply_menu)
    
    elif text == 'teto':
        gen_num = random.randint(1, 200)
        if gen_num <= 4:
            await update.message.reply_video(random.choice(os.getenv('VID').split(' ')))
        elif 4 < gen_num < 20:
            await update.message.reply_animation(random.choice(os.getenv('GIF').split(' ')))
        elif 20 < gen_num <= 200:
            await update.message.reply_photo(random.choice(os.getenv('LST').split(' ')))
    

async def location_handling(update: Update, context: CallbackContext):
    global location, latitude, longitude
    location = update.message.location
    if location == None:
        await update.message.reply_text('Automatic location reading failed. Maybe, you forgot to enable GPS in settings?')
    else:
        #map phase
        logging.info(location)
        latitude = location.latitude
        longitude = location.longitude
        await update.message.reply_text(f"Location found, latitude={latitude}, longitude={longitude}. Generating map, please wait...")
        generate_map(latitude, longitude)
        await update.message.reply_photo('foliumconf/img.png')
        await update.message.reply_text(f'Interactive version is here: {public_url}')
        #output phase
        global name_list
        name_list = find_closest(latitude, longitude, 'list')
        if len(name_list) == 0:
            await update.message.reply_text("Nothing found. Maybe you used VPN?")
        else:
            keyboard = []
            for i in range(len(name_list)): #auto-constructing buttons for an upcoming message
                keyboard.append([])
                keyboard[i].append(InlineKeyboardButton(name_list[i], callback_data=str(i)))
            reply_menu = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(find_closest(latitude, longitude, 'ans'), reply_markup=reply_menu) #showing the closest options and making the user choose

async def text_button_handling(update: Update, context: CallbackContext):
    global return_button
    query = update.callback_query
    await query.answer()
    if query.data == 'back':
        await query.edit_message_text(find_closest(latitude, longitude, 'ans'), reply_markup=reply_menu)
    else:
        chosen_name = name_list[int(query.data)]
        await query.edit_message_text('Текст генерируется, пожалуйста, подождите...')
        keyboard = [[InlineKeyboardButton('Назад', callback_data='back')]]
        return_button = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Сгенерированный текст по описанию места:\n\n{call_response(prompt=chosen_name)}", reply_markup=return_button)


#if run from this file
if __name__ == '__main__':
    logging.info("Starting bot...")
    app = ApplicationBuilder().token(API_TOKEN).read_timeout(30).write_timeout(30).build()
    from foliumconf.ngrok_launch import public_url #running script

    app.add_handler(CommandHandler("start", hello)) #also MessageHandler exists
    app.add_handler(CommandHandler("buttons", start_buttons))
    app.add_handler(CommandHandler("ai", generate_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handling))
    app.add_handler(MessageHandler(filters.LOCATION & ~filters.COMMAND, location_handling))
    app.add_handler(CallbackQueryHandler(text_button_handling))
    
    logging.info("Polling...")
    app.run_polling()