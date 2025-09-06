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
            document.getElementById("signInBtn").style.display = "none"; // скрываем кнопку входа
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