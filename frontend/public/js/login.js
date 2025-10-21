/**
 * Login/Register Page JavaScript - Fixed Version
 * Handles form switching animation and API calls
 */

// Function to clear login forms
function clearLoginForms() {
    const loginEmailInput = document.getElementById('loginEmail');
    const loginPasswordInput = document.getElementById('loginPassword');
    if (loginEmailInput) loginEmailInput.value = '';
    if (loginPasswordInput) loginPasswordInput.value = '';
    
    const regNameInput = document.getElementById('regName');
    const regEmailInput = document.getElementById('regEmail');
    const regPasswordInput = document.getElementById('regPassword');
    if (regNameInput) regNameInput.value = '';
    if (regEmailInput) regEmailInput.value = '';
    if (regPasswordInput) regPasswordInput.value = '';
    
    console.log('🧹 Login forms cleared');
}

// Get DOM elements
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

// Toggle between login and register forms
signUpButton.addEventListener('click', () => {
    container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
});

// Handle Login Form Submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const messageEl = document.getElementById('loginMessage');
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    
    messageEl.style.display = 'none';
    
    // Simple validation
    if (!email || !password) {
        showMessage(messageEl, 'Vui lòng nhập đầy đủ thông tin!', 'error');
        return;
    }
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Đang đăng nhập...';
    
    // Use the auth module to log in
    const result = await auth.login(email, password);
    
    if (result.success) {
        showMessage(messageEl, `✓ Đăng nhập thành công! Chào mừng ${result.user.name}`, 'success');
        
        // Redirect to streaming page after a short delay
        setTimeout(() => {
            window.location.href = 'streaming.html';
        }, 1500);
    } else {
        showMessage(messageEl, `✗ ${result.error}`, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Đăng nhập';
    }
});

// Handle Register Form Submission
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const messageEl = document.getElementById('registerMessage');
    const submitBtn = registerForm.querySelector('button[type="submit"]');
    
    messageEl.style.display = 'none';
    
    // Validation
    if (!name || !email || !password) {
        showMessage(messageEl, 'Vui lòng nhập đầy đủ thông tin!', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage(messageEl, 'Mật khẩu phải có ít nhất 6 ký tự!', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showMessage(messageEl, 'Email không hợp lệ!', 'error');
        return;
    }
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Đang đăng ký...';
    
    // Use the auth module to register
    const result = await auth.register(name, email, password);
    
    if (result.success) {
        showMessage(messageEl, '✓ Đăng ký thành công! Đang chuyển hướng...', 'success');
        
        // Clear form
        registerForm.reset();
        
        // Redirect to streaming page after 1.5 seconds
        setTimeout(() => {
            window.location.href = 'streaming.html';
        }, 1500);
    } else {
        showMessage(messageEl, `✗ ${result.error}`, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Đăng ký';
    }
});

// Helper: Show message
function showMessage(element, message, type) {
    element.className = `message ${type}`;
    element.textContent = message;
    element.style.display = 'block';
    
    // Auto-hide after 5 seconds for errors
    if (type === 'error') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

// Helper: Validate email
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ===== SOCIAL LOGIN HANDLERS =====

// Google Login
document.getElementById('loginGoogle')?.addEventListener('click', (e) => {
    e.preventDefault();
    handleSocialLogin('google');
});

document.getElementById('regGoogle')?.addEventListener('click', (e) => {
    e.preventDefault();
    handleSocialLogin('google');
});

// Facebook Login
document.getElementById('loginFacebook')?.addEventListener('click', (e) => {
    e.preventDefault();
    handleSocialLogin('facebook');
});

document.getElementById('regFacebook')?.addEventListener('click', (e) => {
    e.preventDefault();
    handleSocialLogin('facebook');
});

// LinkedIn Login (not implemented yet)
document.getElementById('loginLinkedin')?.addEventListener('click', (e) => {
    e.preventDefault();
    showMessage(document.getElementById('loginMessage'), 'LinkedIn login đang được phát triển...', 'error');
});

document.getElementById('regLinkedin')?.addEventListener('click', (e) => {
    e.preventDefault();
    showMessage(document.getElementById('registerMessage'), 'LinkedIn login đang được phát triển...', 'error');
});

// Handle Social Login
function handleSocialLogin(provider) {
    // Show loading message
    const messageEl = document.getElementById('loginMessage');
    showMessage(messageEl, `🔄 Đang kết nối với ${provider.charAt(0).toUpperCase() + provider.slice(1)}...`, 'success');
    
    // Open OAuth popup
    const width = 600;
    const height = 700;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    const popup = window.open(
        `${FLASK_API}/auth/${provider}`,
        `${provider}_login`,
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
    
    if (!popup) {
        showMessage(messageEl, '✗ Không thể mở cửa sổ OAuth. Vui lòng cho phép popup.', 'error');
        return;
    }
    
    // Listen for OAuth callback
    window.addEventListener('message', handleOAuthCallback);
    
    // Check if popup was closed
    const checkPopup = setInterval(() => {
        if (popup.closed) {
            clearInterval(checkPopup);
            window.removeEventListener('message', handleOAuthCallback);
            // Popup was closed without completing login
            if (typeof smartStorage !== 'undefined' && !smartStorage.has('currentUser')) {
                showMessage(messageEl, '✗ Đăng nhập bị hủy', 'error');
            }
        }
    }, 1000);
}

// Handle OAuth callback from popup
function handleOAuthCallback(event) {
    // Verify origin for security
    const allowedOrigins = [window.location.origin, FLASK_API, 'http://localhost:5000'];
    if (!allowedOrigins.includes(event.origin)) {
        console.warn('Rejected message from unauthorized origin:', event.origin);
        return;
    }
    
    const { success, user, error } = event.data;
    
    if (success && user) {
        // Store user data - use smartStorage if available
        if (typeof smartStorage !== 'undefined') {
            smartStorage.set('currentUser', user, 86400); // 24 hours
            console.log('✓ OAuth user saved to smartStorage');
        }
        
        const messageEl = document.getElementById('loginMessage');
        showMessage(messageEl, `✓ Đăng nhập thành công! Chào mừng ${user.name}`, 'success');
        
        // Redirect after successful login
        setTimeout(() => {
            window.location.href = 'streaming.html';
        }, 1500);
    } else if (error) {
        const messageEl = document.getElementById('loginMessage');
        showMessage(messageEl, `✗ ${error}`, 'error');
    }
}

// Check if user is already logged in - WAIT for modules to load first!
if (typeof initializePage !== 'undefined') {
    initializePage('login', async () => {
        console.log('🔍 Checking if user already logged in...');
        
        // Check if we just logged out (via URL parameter or session flag)
        const urlParams = new URLSearchParams(window.location.search);
        const justLoggedOut = urlParams.get('logout') === 'true';
        
        if (justLoggedOut) {
            console.log('ℹ️ Just logged out, clearing auth and showing login form');
            // Force clear any remaining auth data
            if (auth && auth.currentUser) {
                auth.currentUser = null;
            }
            clearLoginForms();
            // Remove logout parameter from URL
            window.history.replaceState({}, document.title, '/login.html');
            return;
        }
        
        // Wait for the initial authentication check to complete
        await auth.initPromise;
        
        if (auth.isAuthenticated()) {
            console.log('✅ User already logged in:', auth.getUser().email);
            // Small delay to avoid race condition with logout
            setTimeout(() => {
                window.location.href = 'streaming.html';
            }, 100);
        } else {
            console.log('ℹ️ No user logged in, showing login form');
            clearLoginForms();
        }
    });
} else {
    // Fallback for safety, though should not be needed if core.js is loaded
    console.warn('⚠️ core.js not loaded, using DOMContentLoaded fallback');
    window.addEventListener('DOMContentLoaded', () => {
        clearLoginForms();
    });
}
