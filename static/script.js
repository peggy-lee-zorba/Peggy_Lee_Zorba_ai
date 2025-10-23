// Modal Management
const modal = document.getElementById("loginModal");
const signInBtn = document.getElementById("signInBtn");
const userMenuBtn = document.getElementById("userMenuBtn");
const closeBtn = document.querySelector(".close");

// Show/Hide Modal
if (signInBtn) {
    signInBtn.onclick = () => {
        modal.classList.add('show');
        document.getElementById("username")?.focus();
    };
}

if (closeBtn) {
    closeBtn.onclick = closeModal;
}

function closeModal() {
    modal.classList.remove('show');
    document.getElementById("loginError").textContent = "";
}

// Close modal on backdrop click
window.onclick = (event) => {
    if (event.target === modal) {
        closeModal();
    }
};

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('show')) {
        closeModal();
    }
});

// Submit login with Enter key
document.getElementById("password")?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        submitLogin();
    }
});

// Snackbar notification system
function showSnackbar(message, type = 'error') {
    const snackbar = document.getElementById('snackbar');
    if (!snackbar) return;
    
    snackbar.textContent = message;
    snackbar.className = `snackbar ${type}`;
    snackbar.style.display = 'block';
    
    setTimeout(() => {
        snackbar.style.display = 'none';
    }, 4000);
}

// Login submission
async function submitLogin() {
    const username = document.getElementById("username")?.value.trim();
    const password = document.getElementById("password")?.value;
    const errorDiv = document.getElementById("loginError");
    const submitBtn = event?.target || document.querySelector('.modal-actions .btn');

    if (!username || !password) {
        if (errorDiv) errorDiv.textContent = "Заполните все поля";
        return;
    }

    // Show loading state
    const originalText = submitBtn?.innerHTML;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading"></span> Вход...';
    }

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();

        if (result.success) {
            closeModal();
            
            // Update UI for authenticated user
            const aiSection = document.getElementById("aiSection");
            if (aiSection) aiSection.style.display = "block";
            
            if (signInBtn) signInBtn.style.display = "none";
            if (userMenuBtn) {
                userMenuBtn.style.display = "block";
                const usernameSpan = document.getElementById("username");
                if (usernameSpan) usernameSpan.textContent = username;
            }
            
            showSnackbar(`Добро пожаловать, ${username}!`, 'success');
            
            // Clear form
            document.getElementById("username").value = "";
            document.getElementById("password").value = "";
        } else {
            if (errorDiv) errorDiv.textContent = result.error;
            showSnackbar(result.error, 'error');
        }
    } catch (err) {
        const errorMsg = "Ошибка соединения с сервером";
        if (errorDiv) errorDiv.textContent = errorMsg;
        showSnackbar(errorMsg, 'error');
        console.error('Login error:', err);
    } finally {
        // Restore button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}

// AI Assistant functionality
async function askAI() {
    const input = document.getElementById("userInput")?.value.trim();
    const resDiv = document.getElementById("aiResponse");
    const btn = event?.target.closest('button');
    
    if (!input) {
        showSnackbar("Введите вопрос для AI", 'error');
        document.getElementById("userInput")?.focus();
        return;
    }

    if (!btn || !resDiv) return;

    // Show loading state
    const originalBtnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Обработка...';
    
    resDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <span class="loading"></span>
            <span>Анализирую ваш вопрос...</span>
        </div>
    `;
    resDiv.style.display = 'block';

    try {
        const response = await fetch("/ask-ai", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: input })
        });

        const result = await response.json();

        if (response.ok) {
            // Format response with proper styling
            const formattedReply = result.reply
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>');
            
            resDiv.innerHTML = `
                <div style="display: flex; align-items: start; gap: 8px; margin-bottom: 8px;">
                    <span class="material-icons" style="color: var(--md-primary);">smart_toy</span>
                    <strong>Ответ AI:</strong>
                </div>
                <div class="ai-content">${formattedReply}</div>
            `;
        } else {
            resDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; color: var(--md-error);">
                    <span class="material-icons">error</span>
                    <span>${result.error || 'Произошла ошибка'}</span>
                </div>
            `;
            showSnackbar(result.error || 'Ошибка при обращении к AI', 'error');
        }
    } catch (err) {
        resDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px; color: var(--md-error);">
                <span class="material-icons">error</span>
                <span>Ошибка сети. Проверьте подключение.</span>
            </div>
        `;
        showSnackbar('Ошибка сети', 'error');
        console.error('AI request error:', err);
    } finally {
        // Restore button state
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalBtnText;
        }
    }
}

// Clear AI response
function clearAI() {
    const input = document.getElementById("userInput");
    const response = document.getElementById("aiResponse");
    
    if (input) input.value = "";
    if (response) {
        response.innerHTML = "";
        response.style.display = 'none';
    }
    
    if (input) input.focus();
}

// Animate currency rates on page load
function animateRates() {
    const rows = document.querySelectorAll('#ratesTable tr');
    
    rows.forEach((row, index) => {
        setTimeout(() => {
            row.style.opacity = '0';
            row.style.transform = 'translateX(-20px)';
            row.style.transition = 'opacity 0.4s, transform 0.4s';
            
            setTimeout(() => {
                row.style.opacity = '1';
                row.style.transform = 'translateX(0)';
            }, 50);
        }, index * 50);
    });
}

// Initialize animations on load
document.addEventListener('DOMContentLoaded', () => {
    animateRates();
    
    // Check if user is already logged in (from server-side session)
    // This would need to be passed from Flask template
    const isLoggedIn = {{ 'true' if is_authorized else 'false' }};
    if (isLoggedIn) {
        const aiSection = document.getElementById("aiSection");
        if (aiSection) aiSection.style.display = "block";
        if (signInBtn) signInBtn.style.display = "none";
        if (userMenuBtn) userMenuBtn.style.display = "block";
    }
});

// Add ripple effect to all buttons
document.querySelectorAll('.btn, .btn-text').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
});