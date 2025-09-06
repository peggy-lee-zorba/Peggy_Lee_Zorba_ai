from flask import Flask, render_template, request, jsonify, session
import requests
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-2025")
app.permanent_session_lifetime = timedelta(hours=1)

# Конфигурация AI — через OpenRouter.ai
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "qwen/qwen3-coder:free"  # или "qwen/qwen1.5-72b-chat"

# Авторизация
VALID_USERNAME = os.getenv("APP_USERNAME", "analyst")
VALID_PASSWORD = os.getenv("APP_PASSWORD", "securepass")

# ========================
# Функция для получения курсов валют (только 10 основных)
# ========================
def get_exchange_rates(base='USD'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            # Выбираем 10 основных валют
            top_currencies = ['EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'CHF', 'RUB', 'INR', 'BRL']
            filtered_rates = {curr: rates[curr] for curr in top_currencies if curr in rates}
            return filtered_rates
    except Exception as e:
        print(f"Ошибка получения курсов: {e}")
    # Заглушка на случай ошибки
    return {
        "EUR": 0.92, "GBP": 0.79, "JPY": 155.3, "CNY": 7.25,
        "CAD": 1.37, "AUD": 1.52, "CHF": 0.89, "RUB": 92.5,
        "INR": 83.4, "BRL": 5.12
    }

# ========================
# Роуты
# ========================
@app.route("/")
def index():
    rates = get_exchange_rates()
    is_authorized = "user" in session
    return render_template("index.html", rates=rates, is_authorized=is_authorized)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        session["user"] = username
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Неверный логин или пароль"}), 401

@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "API key missing"}), 500

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://peggy-lee-zorba-ai.onrender.com",  # ЗАМЕНИ НА СВОЙ!
        "X-Title": "Test App",
    }

    data = {
        "model": "qwen/qwen3-coder:free",
        "messages": [{"role": "user", "content": "Привет, ты работаешь?"}],
    }

    try:
        response = requests.post(AI_ENDPOINT, json=data, headers=headers, timeout=30)
        print("Статус:", response.status_code)
        print("Ответ:", response.text)  # 👈 Важно для дебага!
        response.raise_for_status()
        result = response.json()
        return jsonify({"reply": result["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": f"OpenRouter Error: {str(e)} | Response: {response.text if 'response' in locals() else 'No response'}"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)