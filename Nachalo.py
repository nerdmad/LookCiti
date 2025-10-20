import logging
import math
import requests
from dataclasses import dataclass
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

@dataclass
class Attraction:
    id: str
    name: str
    description: str
    lat: float
    lon: float
    category: str

user_states = {}

@dataclass
class UserState:
    current_attractions: list = None
    current_quest: list = None
    current_attraction_index: int = 0
    waiting_for_photo: bool = False

def find_nearby_attractions(user_lat, user_lon, radius=2000):
    try:
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        overpass_query = f"""
        [out:json];
        (
          node["tourism"~"museum|gallery|attraction|zoo|aquarium"](around:{radius},{user_lat},{user_lon});
          node["historic"~"monument|castle|memorial"](around:{radius},{user_lat},{user_lon});
          node["amenity"~"fountain|theatre"](around:{radius},{user_lat},{user_lon});
          way["tourism"~"museum|gallery|attraction|zoo|aquarium"](around:{radius},{user_lat},{user_lon});
          way["historic"~"monument|castle|memorial"](around:{radius},{user_lat},{user_lon});
          way["amenity"~"fountain|theatre"](around:{radius},{user_lat},{user_lon});
        );
        out center 10;
        """
        
        response = requests.post(overpass_url, data=overpass_query)
        data = response.json()
        
        attractions = []
        for element in data['elements']:
            if 'tags' in element and 'name' in element['tags']:
                name = element['tags']['name']
                
                if 'lat' in element and 'lon' in element:
                    lat = element['lat']
                    lon = element['lon']
                elif 'center' in element:
                    lat = element['center']['lat']
                    lon = element['center']['lon']
                else:
                    continue
                
                description = ""
                if 'tourism' in element['tags']:
                    category = element['tags']['tourism']
                    description = f"Место для туристов: {category}"
                elif 'historic' in element['tags']:
                    category = element['tags']['historic']
                    description = f"Историческое место: {category}"
                elif 'amenity' in element['tags']:
                    category = element['tags']['amenity']
                    description = f"Объект: {category}"
                else:
                    category = "attraction"
                    description = "Интересное место"
                
                attraction_id = f"{element['type']}_{element['id']}"
                
                attractions.append(Attraction(
                    id=attraction_id,
                    name=name,
                    description=description,
                    lat=lat,
                    lon=lon,
                    category=category
                ))
        
        return attractions[:8]
        
    except Exception as e:
        logger.error(f"Ошибка при поиске достопримечательностей: {e}")
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = UserState()
    
    keyboard = [
        [KeyboardButton("📍 Отправить геолокацию", request_location=True)],
        [KeyboardButton("ℹ️ О боте")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🏛️ Добро пожаловать в Тур-квест!\n\nОтправьте свою геолокацию, чтобы найти интересные места рядом с вами и начать увлекательное путешествие!",
        reply_markup=reply_markup
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    location = update.message.location
    user_lat = location.latitude
    user_lon = location.longitude
    
    await update.message.reply_text("🔍 Ищу достопримечательности рядом с вами...")
    
    attractions = find_nearby_attractions(user_lat, user_lon)
    
    if not attractions:
        await update.message.reply_text(
            "😔 К сожалению, в радиусе 2 км не найдено достопримечательностей. Попробуйте отправить локацию в другом месте!",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    user_states[user_id].current_attractions = attractions
    
    attractions_text = "🏆 Найдены достопримечательности рядом с вами:\n\n"
    for i, attr in enumerate(attractions, 1):
        distance = calculate_distance(user_lat, user_lon, attr.lat, attr.lon)
        attractions_text += f"{i}. {attr.name}\n"
        attractions_text += f"   📍 {distance:.1f} км от вас\n"
        attractions_text += f"   📖 {attr.description}\n\n"
    
    keyboard = [[InlineKeyboardButton("🚀 Начать Тур-квест", callback_data="start_quest")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(attractions_text, reply_markup=reply_markup)

async def start_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = user_states[user_id]
    
    if not user_state.current_attractions:
        await query.edit_message_text("Ошибка: не найдены достопримечательности")
        return
    
    user_state.current_quest = user_state.current_attractions.copy()
    user_state.current_attraction_index = 0
    
    await show_next_attraction(query, context, user_id)

async def show_next_attraction(query, context, user_id):
    user_state = user_states[user_id]
    
    if user_state.current_attraction_index >= len(user_state.current_quest):
        await query.edit_message_text(
            "🎉 Поздравляем! Вы завершили все пункты Тур-квеста!\n\nВы посетили самые интересные места в этом районе. Надеемся, вам понравилось путешествие! 🏛️✨"
        )
        return
    
    current_attr = user_state.current_quest[user_state.current_attraction_index]
    
    keyboard = [
        [InlineKeyboardButton("✅ Я тут!", callback_data="arrived")],
        [InlineKeyboardButton("⏭️ Пропустить точку", callback_data="skip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎯 Точка {user_state.current_attraction_index + 1}/{len(user_state.current_quest)}\n\n🏛️ {current_attr.name}\n📖 {current_attr.description}\n\nНаправляйтесь к этой достопримечательности. Когда доберетесь, нажмите 'Я тут!'",
        reply_markup=reply_markup
    )

async def handle_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = user_states[user_id]
    
    user_state.waiting_for_photo = True
    
    await query.edit_message_text(
        "📸 Отлично! Вы на месте!\n\nТеперь сделайте фотографию этой достопримечательности и отправьте её в чат, чтобы подтвердить посещение!"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state = user_states.get(user_id)
    
    if not user_state or not user_state.waiting_for_photo:
        await update.message.reply_text("Пожалуйста, сначала начните квест или отметьтесь на месте!")
        return
    
    user_state.waiting_for_photo = False
    user_state.current_attraction_index += 1
    
    import random
    praise_messages = [
        "📸 Отличный кадр! Вы настоящий фотограф!",
        "🎨 Прекрасная фотография! Видно, что вы умеете выбирать ракурс!",
        "🌟 Великолепно! Эта фотография передает всю красоту места!",
        "📷 Замечательно! Вы хорошо справились с заданием!"
    ]
    praise = random.choice(praise_messages)
    
    if user_state.current_attraction_index < len(user_state.current_quest):
        next_text = f"\n\n{praise}\n\nПереходим к следующей точке!"
        
        keyboard = [
            [InlineKeyboardButton("➡️ Следующая точка", callback_data="next_attraction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(next_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            f"{praise}\n\n🎉 Поздравляем! Вы завершили весь Тур-квест! Вы посетили все запланированные достопримечательности. Надеемся, вам понравилось приключение! 🏛️"
        )

async def skip_attraction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = user_states[user_id]
    
    user_state.current_attraction_index += 1
    await show_next_attraction(query, context, user_id)

async def next_attraction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    await show_next_attraction(query, context, user_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "ℹ️ О боте":
        await update.message.reply_text(
            "🏛️ Тур-квест - это интерактивный гид по достопримечательностям!\n\nКак это работает:\n1. 📍 Отправляете свою геолокацию\n2. 🏆 Бот находит интересные места рядом\n3. 🚀 Начинаете квест и посещаете точки\n4. 📸 Делаете фото для подтверждения\n5. 🎉 Получаете похвалу и переходите дальше!\n\nНачните свое приключение - отправьте геолокацию!"
        )
    else:
        await update.message.reply_text(
            "Используйте кнопки ниже или отправьте геолокацию, чтобы начать Тур-квест!",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("📍 Отправить геолокацию", request_location=True)],
                [KeyboardButton("ℹ️ О боте")]
            ], resize_keyboard=True)
        )

def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_handler(CallbackQueryHandler(start_quest, pattern="^start_quest$"))
    application.add_handler(CallbackQueryHandler(handle_arrival, pattern="^arrived$"))
    application.add_handler(CallbackQueryHandler(skip_attraction, pattern="^skip$"))
    application.add_handler(CallbackQueryHandler(next_attraction, pattern="^next_attraction$"))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == 'main':
    main()