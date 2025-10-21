/**
 * 📝 Logger Module
 * Centralized logging system with levels and formatting
 */

class Logger {
    constructor(config = {}) {
        this.config = config;
        this.levels = {
            debug: 0,
            info: 1,
            warn: 2,
            error: 3
        };
        this.currentLevel = this.levels[config.level || 'info'];
        this.enabled = config.enabled !== false;
    }

    _log(level, message, data = null) {
        if (!this.enabled || this.levels[level] < this.currentLevel) return;

        const timestamp = new Date().toISOString();
        const emoji = {
            debug: '🔍',
            info: 'ℹ️',
            warn: '⚠️',
            error: '❌'
        }[level];

        const logMessage = `${emoji} [${timestamp}] [${level.toUpperCase()}] ${message}`;

        if (this.config.console) {
            const logFn = console[level] || console.log;
            if (data) {
                logFn(logMessage, data);
            } else {
                logFn(logMessage);
            }
        }

        // TODO: Send to remote logging service if enabled
        if (this.config.remote) {
            this._sendToRemote(level, message, data);
        }
    }

    debug(message, data) {
        this._log('debug', message, data);
    }

    info(message, data) {
        this._log('info', message, data);
    }

    warn(message, data) {
        this._log('warn', message, data);
    }

    error(message, data) {
        this._log('error', message, data);
    }

    _sendToRemote(level, message, data) {
        // TODO: Implement remote logging
        // Example: Send to analytics service, error tracking, etc.
    }
}

/**
 * 🛠️ Utility Functions
 * Common helper functions used across the application
 */

const Utils = {
    /**
     * Debounce function execution
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function execution
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Deep clone object
     */
    clone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj);
        if (obj instanceof Array) return obj.map(item => Utils.clone(item));
        
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = Utils.clone(obj[key]);
            }
        }
        return clonedObj;
    },

    /**
     * Format date to readable string
     */
    formatDate(date, format = 'DD/MM/YYYY') {
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        
        const formats = {
            'DD/MM/YYYY': `${day}/${month}/${year}`,
            'MM/DD/YYYY': `${month}/${day}/${year}`,
            'YYYY-MM-DD': `${year}-${month}-${day}`
        };
        
        return formats[format] || formats['DD/MM/YYYY'];
    },

    /**
     * Format number with thousands separator
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Truncate string with ellipsis
     */
    truncate(str, length, suffix = '...') {
        if (!str || str.length <= length) return str;
        return str.substring(0, length) + suffix;
    },

    /**
     * Validate email
     */
    validateEmail(email) {
        return AppConfig.validation.email.test(email);
    },

    /**
     * Validate password
     */
    validatePassword(password) {
        const rules = AppConfig.validation.password;
        if (password.length < rules.minLength) return false;
        if (password.length > rules.maxLength) return false;
        if (rules.requireUppercase && !/[A-Z]/.test(password)) return false;
        if (rules.requireLowercase && !/[a-z]/.test(password)) return false;
        if (rules.requireNumbers && !/\d/.test(password)) return false;
        if (rules.requireSpecialChars && !/[!@#$%^&*]/.test(password)) return false;
        return true;
    },

    /**
     * Generate unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    /**
     * Parse query string
     */
    parseQuery(queryString) {
        const params = new URLSearchParams(queryString);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    },

    /**
     * Build query string
     */
    buildQuery(params) {
        return Object.keys(params)
            .filter(key => params[key] !== undefined && params[key] !== null)
            .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
            .join('&');
    },

    /**
     * Sleep/delay function
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Retry function with exponential backoff
     */
    async retry(fn, options = {}) {
        const {
            retries = 3,
            delay = 1000,
            backoff = 2
        } = options;

        let lastError;
        for (let i = 0; i < retries; i++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error;
                if (i < retries - 1) {
                    await Utils.sleep(delay * Math.pow(backoff, i));
                }
            }
        }
        throw lastError;
    },

    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    /**
     * Smooth scroll to element
     */
    scrollTo(element, offset = 0) {
        const targetPosition = element.offsetTop - offset;
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    },

    /**
     * Get cookie value
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    /**
     * Set cookie
     */
    setCookie(name, value, days = 7) {
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
    },

    /**
     * Delete cookie
     */
    deleteCookie(name) {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
    },

    /**
     * Sanitize HTML to prevent XSS
     */
    sanitizeHTML(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    },

    /**
     * Escape special characters for regex
     */
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
};

// Create global logger instance
const logger = new Logger(AppConfig.logging);

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Logger, Utils, logger };
}

console.log('✓ Core utilities loaded');
