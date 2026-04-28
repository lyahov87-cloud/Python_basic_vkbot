import os
import requests
import vk_api
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from peewee import SqliteDatabase, Model, CharField, DateTimeField, ForeignKeyField, TextField
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api import VkUpload

load_dotenv()

# --- БАЗА ДАННЫХ ---
db = SqliteDatabase('bot_history.db')


class User(Model):
    vk_id = CharField(unique=True)

    class Meta:
        database = db


class History(Model):
    user = ForeignKeyField(User, backref='history')
    command = CharField()
    query_text = TextField(null=True)
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db


db.connect()
db.create_tables([User, History])

# --- НАСТРОЙКИ API ---
VK_TOKEN = os.getenv('VK_TOKEN')
KP_TOKEN = os.getenv('KP_TOKEN')
HEADERS = {'X-API-KEY': KP_TOKEN, 'Accept': 'application/json'}

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
upload = VkUpload(vk_session)


# --- ФУНКЦИИ КИНО ---
# --- ФУНКЦИИ КИНО ---
def fetch_from_kp(url, params, user_id, cmd_name):
    user, _ = User.get_or_create(vk_id=str(user_id))
    History.create(user=user, command=cmd_name, query_text=params.get('query'))

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code != 200:
            return f"Ошибка API: {response.status_code}", None

        data = response.json()

        # УНИВЕРСАЛЬНАЯ ПРОВЕРКА:
        # Если в ответе есть список 'docs', берем первый элемент. Иначе берем сам корень.
        if 'docs' in data and isinstance(data['docs'], list) and len(data['docs']) > 0:
            movie = data['docs'][0]
        elif isinstance(data, dict) and 'id' in data:
            movie = data
        else:
            return "Ничего не нашлось 😕", None

        name = movie.get('name') or movie.get('alternativeName') or "Без названия"
        rating = movie.get('rating', {}).get('kp') or movie.get('rating', {}).get('imdb') or 0
        desc = movie.get('description', 'Без описания')[:300]

        # Постер (проверяем все возможные поля)
        poster_data = movie.get('poster') or {}
        photo_url = poster_data.get('url')

        text = f"🎬 {name}\n⭐ Рейтинг: {rating}\n\n📝 {desc}..."
        return text, photo_url
    except Exception as e:
        print(f"Ошибка: {e}")  # Это напечатается в консоли для тебя
        return "Произошла ошибка при обработке данных 😕", None

# --- КЛАВИАТУРА ---
def create_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🎲 Случайный фильм', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🔎 Поиск', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🔝 ТОП-10 по годам', color=VkKeyboardColor.PRIMARY) # Сюда нажали
    keyboard.add_line()
    keyboard.add_button('/history', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('/help', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def create_year_keyboard():
    keyboard = VkKeyboard(one_time=True) # Исчезнет после нажатия
    keyboard.add_button('2024', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('2023', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('2022', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('2021', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('2020', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

# --- ЦИКЛ БОТА ---
print("Бот успешно запущен и слушает сообщения...")
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        msg = event.text.lower().strip()
        uid = event.user_id
        attach = ""
        photo_url = None

        if msg in ['/help', 'начать', 'привет']:
            resp = "Я бот для поиска кино!\n/help - справка\n/history - история\n/🔝 топ-10 по годам\nПросто текст - поиск по названию\n🎲 Случайный фильм"

        elif msg == '/history':
            user, _ = User.get_or_create(vk_id=str(uid))
            hist = History.select().where(History.user == user).order_by(History.timestamp.desc()).limit(5)
            resp = "Последние запросы:\n" + "\n".join([f"{h.timestamp.strftime('%H:%M')} - {h.command}" for h in hist])

        elif msg == '🎲 случайный фильм':
            # Добавлен параметр notNullFields чтобы всегда был постер
            params = {'notNullFields': ['name', 'poster.url', 'description']}
            resp, photo_url = fetch_from_kp('https://api.poiskkino.dev/v1.4/movie/random', params, uid, '/random')


        elif msg == '🔝 топ-10 по годам':
            resp = "Выберите год, за который хотите увидеть лучшие фильмы:"
            vk.messages.send(
                user_id=uid,
                message=resp,
                keyboard=create_year_keyboard(),  # Отправляем спец-клавиатуру
                random_id=get_random_id()
            )
            continue  # Пропускаем стандартную отправку в конце цикла

        elif msg in ['2024', '2023', '2022', '2021', '2020']:
            # Фильтр: топ за выбранный год (рейтинг 7-10)
            params = {
                'year': msg,
                'rating.kp': '7-10',
                'limit': 1,
                'sortField': 'rating.kp',  # Сортируем по рейтингу
                'sortType': '-1',  # От большего к меньшему
                'notNullFields': ['name', 'poster.url']
            }
            resp, photo_url = fetch_from_kp('https://api.poiskkino.dev/v1.4/movie', params, uid, f'/top_{msg}')
            resp = f"⭐ Лучший фильм {msg} года:\n\n" + resp

        elif msg == 'назад':

             resp = "Возвращаемся в главное меню."

# Обычная отправка в конце цикла сама прикрепит главную клавиатуру


        elif msg == '🔎 поиск':
            resp = "Просто введите название фильма в чат!"

        else:
            resp, photo_url = fetch_from_kp('https://api.poiskkino.dev/v1.4/movie/search', {'query': event.text, 'limit': 1}, uid,
                                            '/search')

        # ЗАГРУЗКА ФОТО (Исправлено)
        if photo_url:
            try:
                img_res = requests.get(photo_url, timeout=5)
                if img_res.status_code == 200:
                    photo = upload.photo_messages(photos=BytesIO(img_res.content), peer_id=uid)[0]
                    attach = f"photo{photo['owner_id']}_{photo['id']}"
            except Exception as e:
                print(f"Ошибка загрузки фото: {e}")

        vk.messages.send(user_id=uid, message=resp, attachment=attach,
                         keyboard=create_keyboard(), random_id=get_random_id())
