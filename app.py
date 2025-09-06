from flask import Flask, render_template, request, jsonify, session
import requests
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-dev-key-2025")
app.permanent_session_lifetime = timedelta(hours=1)

# Конфигурация AI
AI_API_KEY = os.getenv("AI_API_KEY")
AI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Авторизация (в продакшене — вынести в БД или .env)
VALID_USERNAME = os.getenv("APP_USERNAME", "analyst")
VALID_PASSWORD = os.getenv("APP_PASSWORD", "securepass")

@app.route("/")
def index():
    # Всегда показываем главную страницу
    # Состояние авторизации передаём в шаблон
    is_authorized = "user" in session
    return render_template("index.html", is_authorized=is_authorized)

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
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.7
    }

    try:
        response = requests.post(AI_ENDPOINT, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": ai_reply})
    except Exception as e:
        return jsonify({"error": f"Ошибка ИИ: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))