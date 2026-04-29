import requests
from settings import KP_HEADERS
from models import User, History


def fetch_from_kp(url, params, user_id, cmd_name):
    user, _ = User.get_or_create(vk_id=str(user_id))
    History.create(user=user, command=cmd_name, query_text=params.get('query'))

    try:
        response = requests.get(url, headers=KP_HEADERS, params=params, timeout=10)
        if response.status_code != 200:
            return f"Ошибка API: {response.status_code}", None

        data = response.json()
        if 'docs' in data and isinstance(data['docs'], list) and len(data['docs']) > 0:
            movie = data['docs'][0]
        elif isinstance(data, dict) and 'id' in data:
            movie = data
        else:
            return "Ничего не нашлось 😕", None

        name = movie.get('name') or movie.get('alternativeName') or "Без названия"
        rating = movie.get('rating', {}).get('kp') or movie.get('rating', {}).get('imdb') or 0
        desc = movie.get('description', 'Без описания')[:300]

        poster_data = movie.get('poster') or {}
        photo_url = poster_data.get('url')

        text = f"🎬 {name}\n⭐ Рейтинг: {rating}\n\n📝 {desc}..."
        return text, photo_url
    except Exception as e:
        print(f"Ошибка API: {e}")
        return "Произошла ошибка при обработке данных 😕", None
