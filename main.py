import requests
from io import BytesIO
from vk_api.longpoll import VkEventType
from vk_api.utils import get_random_id

from settings import vk, longpoll, upload
from models import init_db, User, History
from api import fetch_from_kp
from utils import create_keyboard, create_year_keyboard

init_db()

print("Бот успешно запущен...")
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        msg = event.text.lower().strip()
        uid = event.user_id
        attach = ""
        photo_url = None
        resp = "Я тебя не понял. Напиши /help" # Значение по умолчанию

        # --- ЛОГИКА ОБРАБОТКИ ---
        if msg in ['/help', 'начать', 'привет']:
            resp = "Я бот для поиска кино!\n/help - справка\n/history - история\n/🔝 топ-10 по годам\n/Поиск по названию\n/🎲 Случайный фильм"

        elif msg == '/history':
            user, _ = User.get_or_create(vk_id=str(uid))
            hist = History.select().where(History.user == user).order_by(History.timestamp.desc()).limit(5)
            resp = "Последние запросы:\n" + "\n".join([f"{h.timestamp.strftime('%H:%M')} - {h.command}" for h in hist])

        elif msg == '🎲 случайный фильм':
            params = {'notNullFields': ['name', 'poster.url', 'description']}
            resp, photo_url = fetch_from_kp('https://api.poiskkino.dev/v1.4/movie/random', params, uid, '/random')

        elif msg == '🔝 топ-10 по годам':
            vk.messages.send(
                user_id=uid,
                message="Выберите год, за который хотите увидеть лучшие фильмы:",
                keyboard=create_year_keyboard(),
                random_id=get_random_id()
            )
            continue

        elif msg in ['2024', '2023', '2022', '2021', '2020']:
            params = {
                'year': msg,
                'rating.kp': '7-10',
                'limit': 1,
                'sortField': 'rating.kp',
                'sortType': '-1',
                'notNullFields': ['name', 'poster.url']
            }
            resp, photo_url = fetch_from_kp('https://api.poiskkino.dev/v1.4/movie', params, uid, f'/top_{msg}')
            resp = f"⭐ Лучший фильм {msg} года:\n\n" + resp

        elif msg == 'назад':
             resp = "Возвращаемся в главное меню."

        elif msg == '🔎 поиск':
            resp = "Просто введите название фильма в чат!"

        else:
            # Если это не команда, значит ищем по названию
            resp, photo_url = fetch_from_kp('https://api.poiskkino.dev/v1.4/movie/search',
                                            {'query': event.text, 'limit': 1}, uid, '/search')

        # --- ЗАГРУЗКА ФОТО ---
        if photo_url:
            try:
                img_res = requests.get(photo_url, timeout=5)
                if img_res.status_code == 200:
                    photo = upload.photo_messages(photos=BytesIO(img_res.content), peer_id=uid)[0]
                    attach = f"photo{photo['owner_id']}_{photo['id']}"
            except Exception as e:
                print(f"Ошибка загрузки фото: {e}")

        # --- ОТПРАВКА ---
        vk.messages.send(
            user_id=uid,
            message=resp,
            attachment=attach,
            keyboard=create_keyboard(),
            random_id=get_random_id()
        )
