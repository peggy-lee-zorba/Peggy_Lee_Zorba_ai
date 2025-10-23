// Модальное окно авторизации
const modal = document.getElementById("loginModal");
const btn = document.getElementById("signInBtn");
const span = document.getElementsByClassName("close")[0];

if (btn) btn.onclick = function() { modal.style.display = "block"; }
if (span) span.onclick = function() { modal.style.display = "none"; }

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Отправка формы авторизации
async function submitLogin() {
    const username = document.getElementById("username")?.value;
    const password = document.getElementById("password")?.value;
    const errorDiv = document.getElementById("loginError");

    if (!username || !password) {
        if (errorDiv) errorDiv.textContent = "Заполните все поля";
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
            const aiSection = document.getElementById("aiSection");
            const signInBtn = document.getElementById("signInBtn");
            if (aiSection) aiSection.style.display = "block";
            if (signInBtn) signInBtn.style.display = "none";
        } else {
            if (errorDiv) errorDiv.textContent = result.error;
        }
    } catch (err) {
        if (errorDiv) errorDiv.textContent = "Ошибка соединения";
    }
}

// Отправка запроса к ИИ
async function askAI() {
    const input = document.getElementById("userInput")?.value;
    if (!input?.trim()) return alert("Введите вопрос!");

    const btn = event.target;
    const resDiv = document.getElementById("aiResponse");

    if (!btn || !resDiv) return;

    btn.disabled = true;
    btn.classList.add('loading');
    btn.innerText = "⏳ Думаю...";

    resDiv.innerHTML = "<p>Обрабатываю запрос...</p>";

    try {
        const response = await fetch("/ask-ai", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: input })
        });

        const result = await response.json();

        if (response.ok) {
            // Сохраняем форматирование: переносы строк, списки и т.д.
            resDiv.innerHTML = `<p><strong>🤖 Ответ Qwen:</strong></p><div class="ai-content">${result.reply.replace(/\n/g, '<br>')}</div>`;
        } else {
            resDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (err) {
        resDiv.innerHTML = `<p class="error">❌ Ошибка сети</p>`;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('loading');
            btn.innerText = "Отправить запрос";
        }
    }
}