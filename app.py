from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import os
from datetime import timedelta, datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-2025")
app.permanent_session_lifetime = timedelta(hours=1)

# Конфигурация AI — через OpenRouter.ai
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "qwen/qwen3-coder:free"

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
            top_currencies = ['EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'CHF', 'RUB', 'INR', 'BRL']
            filtered_rates = {curr: rates[curr] for curr in top_currencies if curr in rates}
            return filtered_rates
    except Exception as e:
        print(f"Ошибка получения курсов: {e}")
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
    if "blocked_until" in session:
        blocked_until = datetime.fromisoformat(session["blocked_until"])
        if datetime.now() < blocked_until:
            return render_template("login.html", error="⛔ Доступ заблокирован. Попробуйте через 30 минут.")

    rates = get_exchange_rates()
    is_authorized = "user" in session
    return render_template("index.html", rates=rates, is_authorized=is_authorized)

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

@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if not OPENROUTER_API_KEY:
        return jsonify({"error": "API key missing"}), 500

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://peggy-lee-zorba-ai.onrender.com",
        "X-Title": "Business Analytics AI Proxy",
    }

    user_message = request.json.get("message", "Привет, ты работаешь?")

    data = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": user_message}],
    }

    try:
        response = requests.post(AI_ENDPOINT, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return jsonify({"reply": result["choices"][0]["message"]["content"]})
    except Exception as e:
        error_detail = response.text if 'response' in locals() else 'No response'
        return jsonify({"error": f"OpenRouter Error: {str(e)} | Response: {error_detail}"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)