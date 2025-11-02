from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import os
from datetime import timedelta, datetime

app = Flask(__name__)

# Критическая проверка наличия секретного ключа
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
if not FLASK_SECRET_KEY:
    raise ValueError(
        "❌ FLASK_SECRET_KEY не установлен! "
        "Установите переменную окружения в Render.com: "
        "Dashboard → Environment → Add Secret File/Variable"
    )
app.secret_key = FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=1)


# Установка безопасных cookie
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Конфигурация контекста
MAX_CONTEXT_MESSAGES = 6  # Максимальное количество пар сообщений (user + assistant)
MAX_CONTEXT_LENGTH = 16000  # Максимальная длина контекста в символах

# Конфигурация AI — через OpenRouter.ai
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError(
        "❌ OPENROUTER_API_KEY не установлен! "
        "Получите ключ на https://openrouter.ai/keys и установите в Environment"
    )

AI_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "deepseek/deepseek-chat")

# Авторизация
VALID_USERNAME = os.getenv("APP_USERNAME", "analyst")
VALID_PASSWORD = os.getenv("APP_PASSWORD", "securepass")

# ========================
# Функция для получения курсов валют (только 10 основных)
# ========================
def get_exchange_rates(base='USD'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    
    # Маппинг валют к флагам
    currency_flags = {
        'EUR': '🇪🇺',  # Европейский союз
        'GBP': '🇬🇧',  # Великобритания
        'JPY': '🇯🇵',  # Япония
        'CNY': '🇨🇳',  # Китай
        'CAD': '🇨🇦',  # Канада
        'AUD': '🇦🇺',  # Австралия
        'CHF': '🇨🇭',  # Швейцария
        'RUB': '🇷🇺',  # Россия
        'INR': '🇮🇳',  # Индия
        'BRL': '🇧🇷',  # Бразилия
    }
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            top_currencies = ['EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'CHF', 'RUB', 'INR', 'BRL']
            filtered_rates = {
                curr: {'rate': rates[curr], 'flag': currency_flags.get(curr, '🏳️')} 
                for curr in top_currencies if curr in rates
            }
            return filtered_rates
    except Exception as e:
        print(f"Ошибка получения курсов: {e}")
    
    # Fallback данные с флагами
    return {
        "EUR": {'rate': 0.92, 'flag': '🇪🇺'},
        "GBP": {'rate': 0.79, 'flag': '🇬🇧'},
        "JPY": {'rate': 155.3, 'flag': '🇯🇵'},
        "CNY": {'rate': 7.25, 'flag': '🇨🇳'},
        "CAD": {'rate': 1.37, 'flag': '🇨🇦'},
        "AUD": {'rate': 1.52, 'flag': '🇦🇺'},
        "CHF": {'rate': 0.89, 'flag': '🇨🇭'},
        "RUB": {'rate': 92.5, 'flag': '🇷🇺'},
        "INR": {'rate': 83.4, 'flag': '🇮🇳'},
        "BRL": {'rate': 5.12, 'flag': '🇧🇷'},
    }

# ========================
# Функция для получения погоды через Open-Meteo (без API ключа)
# ========================
def get_weather_by_city_name(city='St. Petersburg'):
    """
    Получает координаты города и затем погоду
    Использует Open-Meteo API - без регистрации!
    """
    # Маппинг популярных городов к координатам
    city_coords = {
        'saint petersburg': {'lat': 59.9343, 'lon': 30.3351, 'name': 'Санкт-Петербург'},
        'moscow': {'lat': 55.7558, 'lon': 37.6173, 'name': 'Москва'},
        'london': {'lat': 51.5074, 'lon': -0.1278, 'name': 'Лондон'},
        'new york': {'lat': 40.7128, 'lon': -74.0060, 'name': 'Нью-Йорк'},
        'paris': {'lat': 48.8566, 'lon': 2.3522, 'name': 'Париж'},
        'berlin': {'lat': 52.5200, 'lon': 13.4050, 'name': 'Берлин'},
        'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'name': 'Токио'},
        'beijing': {'lat': 39.9042, 'lon': 116.4074, 'name': 'Пекин'},
        'kannelyarvi': {'lat': 29.363512, 'lon': 60.339142, 'name': 'Каннельярви'},
    }
    
    city_lower = city.lower()
    
    # Проверяем, есть ли город в нашей базе
    if city_lower in city_coords:
        coords = city_coords[city_lower]
    else:
        # По умолчанию Москва
        coords = city_coords['moscow']
    
    return get_weather(coords['lat'], coords['lon'], coords['name'])


def get_weather(lat=55.7558, lon=37.6173, city_name='Санкт-Петербург'):
    """
    Получает погоду по координатам через Open-Meteo API
    БЕЗ РЕГИСТРАЦИИ И API КЛЮЧА!
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature',
        'timezone': 'auto'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data['current']
            
            # Маппинг кодов погоды к описаниям и emoji
            weather_codes = {
                0: {'desc': 'Ясно', 'emoji': '☀️'},
                1: {'desc': 'Преимущественно ясно', 'emoji': '🌤️'},
                2: {'desc': 'Переменная облачность', 'emoji': '⛅'},
                3: {'desc': 'Облачно', 'emoji': '☁️'},
                45: {'desc': 'Туман', 'emoji': '🌫️'},
                48: {'desc': 'Изморозь', 'emoji': '🌫️'},
                51: {'desc': 'Легкая морось', 'emoji': '🌦️'},
                53: {'desc': 'Морось', 'emoji': '🌦️'},
                55: {'desc': 'Сильная морось', 'emoji': '🌧️'},
                61: {'desc': 'Небольшой дождь', 'emoji': '🌧️'},
                63: {'desc': 'Дождь', 'emoji': '🌧️'},
                65: {'desc': 'Сильный дождь', 'emoji': '⛈️'},
                71: {'desc': 'Небольшой снег', 'emoji': '🌨️'},
                73: {'desc': 'Снег', 'emoji': '❄️'},
                75: {'desc': 'Сильный снег', 'emoji': '❄️'},
                77: {'desc': 'Снежные зерна', 'emoji': '❄️'},
                80: {'desc': 'Небольшой ливень', 'emoji': '🌦️'},
                81: {'desc': 'Ливень', 'emoji': '⛈️'},
                82: {'desc': 'Сильный ливень', 'emoji': '⛈️'},
                85: {'desc': 'Снегопад', 'emoji': '🌨️'},
                86: {'desc': 'Сильный снегопад', 'emoji': '❄️'},
                95: {'desc': 'Гроза', 'emoji': '⛈️'},
                96: {'desc': 'Гроза с градом', 'emoji': '⛈️'},
                99: {'desc': 'Гроза с крупным градом', 'emoji': '⛈️'},
            }
            
            weather_code = current['weather_code']
            weather_info = weather_codes.get(weather_code, {'desc': 'Неизвестно', 'emoji': '🌤️'})
            
            weather_data = {
                'city': city_name,
                'temp': round(current['temperature_2m']),
                'feels_like': round(current['apparent_temperature']),
                'description': weather_info['desc'],
                'humidity': current['relative_humidity_2m'],
                'wind_speed': round(current['wind_speed_10m'], 1),
                'emoji': weather_info['emoji'],
                'icon_code': str(weather_code)
            }
            
            return weather_data
            
    except Exception as e:
        print(f"❌ Ошибка получения погоды: {e}")
    
    # Fallback данные
    return {
        'city': city_name,
        'temp': 18,
        'feels_like': 16,
        'description': 'Облачно',
        'humidity': 65,
        'wind_speed': 3.5,
        'emoji': '☁️',
        'icon_code': '3'
    }

# ========================
# Роуты
# ========================
@app.route("/")
def index():
    if "blocked_until" in session:
        blocked_until = datetime.fromisoformat(session["blocked_until"])
        if datetime.now() < blocked_until:
            remaining_time = (blocked_until - datetime.now()).total_seconds() / 60
            return render_template(
                "login.html", 
                error=f"⛔ Доступ заблокирован. Попробуйте через {int(remaining_time)} минут."
            )
        else:
            # Блокировка истекла - очищаем
            session.pop("blocked_until", None)
            session.pop("login_attempts", None)
    city = request.args.get('city', 'St. Petersburg')
    rates = get_exchange_rates()
    weather = get_weather_by_city_name(city)  # Добавляем погоду
    is_authorized = "user" in session
    return render_template("index.html", rates=rates, weather=weather, is_authorized=is_authorized)

@app.route("/login", methods=["GET", "POST"])
def login():
    # Проверка блокировки
    if "blocked_until" in session:
        blocked_until = datetime.fromisoformat(session["blocked_until"])
        if datetime.now() < blocked_until:
            return render_template("login.html", error="⛔ Доступ заблокирован. Попробуйте через 30 минут.")

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        username = data.get("username")
        password = data.get("password")

        # Инициализируем счётчик попыток
        if "login_attempts" not in session:
            session["login_attempts"] = 0

        # Проверяем логин/пароль
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session.pop("login_attempts", None)
            session.pop("blocked_until", None)
            session["user"] = username
            if request.is_json:
                return jsonify({"success": True})
            else:
                return redirect(url_for("index"))

        else:
            session["login_attempts"] += 1

            if session["login_attempts"] >= 3:
                # Блокируем на 30 минут
                block_time = datetime.now() + timedelta(minutes=30)
                session["blocked_until"] = block_time.isoformat()
                session.pop("login_attempts", None)
                error_msg = "🔒 Слишком много попыток. Доступ заблокирован на 30 минут."
            else:
                remaining = 3 - session["login_attempts"]
                error_msg = f"Неверный логин или пароль. Осталось попыток: {remaining}"

            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 401
            else:
                return render_template("login.html", error=error_msg)

    # GET запрос — показываем форму
    return render_template("login.html")

# Хранилище для rate limiting (в production используйте Redis)
from collections import defaultdict
from time import time

request_timestamps = defaultdict(list)
MAX_AI_REQUESTS_PER_HOUR = 20

def check_rate_limit(user_id):
    """Проверка лимита запросов (20 в час)"""
    now = time()
    hour_ago = now - 3600
    
    # Очищаем старые запросы
    request_timestamps[user_id] = [
        ts for ts in request_timestamps[user_id] if ts > hour_ago
    ]
    
    # Проверяем лимит
    if len(request_timestamps[user_id]) >= MAX_AI_REQUESTS_PER_HOUR:
        return False
    
    # Добавляем текущий запрос
    request_timestamps[user_id].append(now)
    return True

@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not check_rate_limit(session["user"]):
        return jsonify({
            "error": "⏱️ Превышен лимит запросов (20 в час). Попробуйте позже."
        }), 429

    if not OPENROUTER_API_KEY:
        return jsonify({"error": "OpenRouter API key missing"}), 500

    if not OPENROUTER_API_KEY:
        return jsonify({"error": "OpenRouter API key missing"}), 500

    # Инициализируем историю сообщений в сессии
    if "message_history" not in session:
        session["message_history"] = []

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_URL", "https://business-analytics-dashboard.com"),
        "X-Title": "Business Analytics Dashboard",
    }

    # Системный промпт для бизнес-аналитики
    system_prompt = """Ты - AI ассистент для бизнес-аналитики. Ты помогаешь с:
- Анализом финансовых данных и курсов валют
- Бизнес-прогнозированием и аналитикой
- Интерпретацией экономических тенденций
- Советами по бизнес-решениям

Отвечай профессионально, но доступно. Используй данные, когда они доступны.
Форматируй ответы четко с использованием заголовков и списков где уместно."""

    # Проверяем, не превышен ли лимит контекста
    context_warning = False
    current_context_size = sum(len(msg["content"]) for msg in session["message_history"])
    
    if len(session["message_history"]) >= MAX_CONTEXT_MESSAGES * 2:
        context_warning = True
        # Автоматически очищаем старые сообщения, оставляя первые 2 и последние 4
        _cleanup_message_history(session["message_history"])

    # Добавляем новое сообщение пользователя в историю
    session["message_history"].append({"role": "user", "content": user_message})
    
    # Подготавливаем сообщения для отправки
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(session["message_history"])
    
    data = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        response = requests.post(AI_ENDPOINT, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            ai_reply = result["choices"][0]["message"]["content"]
            
            # Добавляем ответ AI в историю
            session["message_history"].append({"role": "assistant", "content": ai_reply})
            
            # Очищаем старую историю, если превышен лимит
            _cleanup_message_history(session["message_history"])
            
            session.modified = True
            
            return jsonify({
                "reply": ai_reply, 
                "context_warning": context_warning,
                "context_size": len(session["message_history"])
            })
        else:
            return jsonify({"error": "Invalid response format from AI"}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "AI request timeout"}), 504
    except requests.exceptions.RequestException as e:
        error_detail = response.text if 'response' in locals() else 'No response'
        return jsonify({"error": f"OpenRouter Error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def _cleanup_message_history(message_history):
    """Очищает историю сообщений при превышении лимита"""
    if len(message_history) > MAX_CONTEXT_MESSAGES * 2:
        # Оставляем первые 2 сообщения (начало разговора) и последние сообщения
        important_messages = message_history[:2]
        recent_messages = message_history[-(MAX_CONTEXT_MESSAGES * 2 - 2):]
        message_history.clear()
        message_history.extend(important_messages + recent_messages)
    
    # Дополнительная оптимизация по длине
    total_length = sum(len(msg["content"]) for msg in message_history)
    while total_length > MAX_CONTEXT_LENGTH and len(message_history) > 4:
        # Удаляем самые старые сообщения (кроме первых двух)
        if len(message_history) > 2:
            removed_msg = message_history.pop(2)
            total_length -= len(removed_msg["content"])
        else:
            break

@app.route("/clear-context", methods=["POST"])
def clear_context():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Очищаем историю сообщений
    if "message_history" in session:
        session.pop("message_history")
    
    session.modified = True
    return jsonify({"success": True, "message": "Контекст очищен"})

@app.route("/context-info", methods=["GET"])
def context_info():
    """Возвращает информацию о текущем контексте"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    context_size = len(session.get("message_history", []))
    return jsonify({
        "context_size": context_size,
        "max_context": MAX_CONTEXT_MESSAGES * 2,
        "percentage": min(100, int((context_size / (MAX_CONTEXT_MESSAGES * 2)) * 100))
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
