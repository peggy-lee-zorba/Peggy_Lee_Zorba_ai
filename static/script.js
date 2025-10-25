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
async function askAI(event) {
    const input = document.getElementById("userInput")?.value;
    if (!input?.trim()) return alert("Введите вопрос!");

    const btn = event.target;
    const resDiv = document.getElementById("aiResponse");
    const warningBanner = document.getElementById("contextWarning");

    if (!btn || !resDiv) return;

    btn.disabled = true;
    btn.innerText = "⏳ Думаю...";
    btn.classList.add('loading');

    // Скрываем предыдущее предупреждение
    if (warningBanner) {
        warningBanner.style.display = "none";
    }

    resDiv.innerHTML = "<p>Обрабатываю запрос...</p>";

    try {
        const response = await fetch("/ask-ai", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: input })
        });

        const result = await response.json();

        if (response.ok) {
            // Сохраняем форматирование
            resDiv.innerHTML = `<p><strong>🤖 Ответ DeepSeek:</strong></p><div class="ai-content">${result.reply.replace(/\n/g, '<br>')}</div>`;
            
            // Показываем предупреждение, если контекст был очищен
            if (result.context_warning && warningBanner) {
                warningBanner.style.display = "block";
            }
            
            // Обновляем информацию о контексте
            updateContextInfo(result.context_size);
            
        } else {
            resDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (err) {
        resDiv.innerHTML = `<p class="error">❌ Ошибка сети</p>`;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Отправить запрос";
            btn.classList.remove('loading');
        }
    }
}

// Очистка контекста разговора
async function clearContext() {
    if (!confirm("Очистить историю разговора? Весь контекст будет потерян.")) {
        return;
    }

    try {
        const response = await fetch("/clear-context", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message || "Контекст очищен!");
            updateContextInfo(0);
            
            // Скрываем предупреждение
            const warningBanner = document.getElementById("contextWarning");
            if (warningBanner) {
                warningBanner.style.display = "none";
            }
        } else {
            alert("Ошибка при очистке контекста");
        }
    } catch (err) {
        console.error("Clear context error:", err);
        alert("Ошибка соединения");
    }
}

// Обновление информации о контексте
async function updateContextInfo(contextSize = null) {
    const contextInfo = document.getElementById("contextInfo");
    if (!contextInfo) return;

    try {
        let size, percentage;
        
        if (contextSize !== null) {
            size = contextSize;
            percentage = Math.min(100, Math.round((size / 16) * 100));
        } else {
            const response = await fetch("/context-info");
            const data = await response.json();
            
            if (response.ok) {
                size = data.context_size;
                percentage = data.percentage;
            } else {
                return;
            }
        }

        const sizeElement = document.getElementById("contextSize");
        const progressElement = document.getElementById("contextProgress");
        
        if (sizeElement) sizeElement.textContent = size;
        if (progressElement) progressElement.style.width = percentage + '%';
        
        // Меняем цвет прогресс-бара в зависимости от заполненности
        if (percentage > 80) {
            progressElement.style.background = '#EF4444';
        } else if (percentage > 60) {
            progressElement.style.background = '#F59E0B';
        } else {
            progressElement.style.background = '#10B981';
        }
        
        contextInfo.style.display = 'block';
        
    } catch (err) {
        console.error("Context info error:", err);
    }
}

// Показываем индикатор контекста если пользователь авторизован
document.addEventListener('DOMContentLoaded', function() {
    const contextInfo = document.getElementById('contextInfo');
    const aiSection = document.getElementById('aiSection');
    
    if (contextInfo && aiSection.style.display !== 'none') {
        updateContextInfo();
    }
});