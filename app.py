from flask import Flask, render_template_string, request, jsonify, session
import requests
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-2025")
app.permanent_session_lifetime = timedelta(hours=1)

# Конфигурация AI
AI_API_KEY = os.getenv("AI_API_KEY")
AI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Авторизация
VALID_USERNAME = os.getenv("APP_USERNAME", "analyst")
VALID_PASSWORD = os.getenv("APP_PASSWORD", "securepass")

# ========================
# HTML + CSS + JS — всё встроено в Python!
# ========================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Business Analytics Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            color: #2c3e50;
        }
        .btn {
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn:hover {
            background: #2980b9;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .ai-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-top: 30px;
            display: none;
        }
        .ai-section h2 {
            margin-top: 0;
            color: #8e44ad;
        }
        textarea {
            width: 100%;
            height: 80px;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            resize: vertical;
        }
        button {
            padding: 10px 20px;
            background: #8e44ad;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #732d91;
        }
        #aiResponse {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #8e44ad;
            border-radius: 5px;
        }
        .error {
            color: #e74c3c;
            margin-top: 10px;
        }
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .modal-content {
            background-color: #fefefe;
            margin: 15% auto;
            padding: 30px;
            border: 1px solid #888;
            width: 350px;
            border-radius: 10px;
            text-align: center;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: #000;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Business Analytics Dashboard</h1>
        <button id="signInBtn" class="btn">🔐 Sign In</button>
    </div>

    <div class="grid">
        <div class="card">
            <h3>💱 Курсы валют (USD)</h3>
            <table>
                <tr><th>Валюта</th><th>Курс</th></tr>
                {% for curr, rate in rates.items() %}
                <tr><td>{{ curr }}</td><td>{{ "%.4f"|format(rate) }}</td></tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h3>🌤️ Погода (заглушка)</h3>
            <p><strong>Город:</strong> Москва</p>
            <p><strong>Температура:</strong> +18°C</p>
            <p><strong>Описание:</strong> Облачно</p>
        </div>
    </div>

    <!-- Блок ИИ — изначально скрыт -->
    <div id="aiSection" class="ai-section">
        <h2>🤖 Задайте вопрос ИИ-ассистенту</h2>
        <textarea id="userInput" placeholder="Например: Как повлияет рост доллара на рынок?"></textarea>
        <button onclick="askAI()">Отправить запрос</button>
        <div id="aiResponse"></div>
    </div>

    <!-- Модальное окно авторизации -->
    <div id="loginModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h3>🔐 Вход для аналитиков</h3>
            <p>Регистрация отключена. Только для авторизованных пользователей.</p>
            <input type="text" id="username" placeholder="Логин" required>
            <input type="password" id="password" placeholder="Пароль" required>
            <button onclick="submitLogin()">Войти</button>
            <div id="loginError" class="error"></div>
        </div>
    </div>

    <script>
        // Модальное окно авторизации
        const modal = document.getElementById("loginModal");
        const btn = document.getElementById("signInBtn");
        const span = document.getElementsByClassName("close")[0];

        btn.onclick = function() {
            modal.style.display = "block";
        }

        span.onclick = function() {
            modal.style.display = "none";
        }

        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }

        // Отправка формы авторизации
        async function submitLogin() {
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            const errorDiv = document.getElementById("loginError");

            if (!username || !password) {
                errorDiv.textContent = "Заполните все поля";
                return;
            }

            try {
                const response = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const result = await response.json();

                if (result.success) {
                    modal.style.display = "none";
                    document.getElementById("aiSection").style.display = "block";
                    document.getElementById("signInBtn").style.display = "none";
                } else {
                    errorDiv.textContent = result.error;
                }
            } catch (err) {
                errorDiv.textContent = "Ошибка соединения";
            }
        }

        // Отправка запроса к ИИ
        async function askAI() {
            const input = document.getElementById("userInput").value;
            if (!input.trim()) return alert("Введите вопрос!");

            const btn = event.target;
            btn.disabled = true;
            btn.innerText = "⏳ Думаю...";

            const resDiv = document.getElementById("aiResponse");
            resDiv.innerHTML = "<p>Обрабатываю запрос...</p>";

            try {
                const response = await fetch("/ask-ai", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: input })
                });

                const result = await response.json();

                if (response.ok) {
                    resDiv.innerHTML = `<p><strong>🤖 Ответ ИИ:</strong><br>${result.reply}</p>`;
                } else {
                    resDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
                }
            } catch (err) {
                resDiv.innerHTML = `<p class="error">❌ Ошибка сети</p>`;
            } finally {
                btn.disabled = false;
                btn.innerText = "Отправить запрос";
            }
        }
    </script>
</body>
</html>
'''

# ========================
# Функция для получения курсов валют
# ========================
def get_exchange_rates(base='USD'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('rates', {})
    except:
        pass
    return {}

# ========================
# Роуты
# ========================
@app.route("/")
def index():
    rates = get_exchange_rates()
    # Если API не ответил — показываем заглушку
    if not rates:
        rates = {"EUR": 0.92, "RUB": 92.5, "GBP": 0.79, "JPY": 155.3, "CNY": 7.25}

    is_authorized = "user" in session
    return render_template_string(HTML_TEMPLATE, rates=rates, is_authorized=is_authorized)

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

    if not AI_API_KEY:
        return jsonify({"error": "AI API key not configured"}), 500

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
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)