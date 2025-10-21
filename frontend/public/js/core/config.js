/**
 * ⚙️ Application Configuration
 * Centralized configuration for the entire application
 * Single source of truth for all settings
 */

const AppConfig = {
    // API Configuration
    api: {
        baseUrl: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? 'http://localhost:5000' 
            : window.location.origin,
        timeout: 30000, // 30 seconds
        retries: 3,
        retryDelay: 1000, // 1 second
        endpoints: {
            // Auth endpoints
            login: '/api/login',
            register: '/api/register',
            logout: '/api/logout',
            checkAuth: '/api/check-auth',
            
            // Movie endpoints
            movies: '/api/movies',
            movieDetail: '/api/movies/:id',
            
            // User endpoints
            favorites: '/api/favorites',
            watchHistory: '/api/watch-history',
            
            // Other endpoints
            genres: '/api/genres',
            search: '/api/search'
        }
    },

    // Storage Configuration
    storage: {
        prefix: 'cgv_',
        ttl: {
            user: 86400,        // 24 hours
            session: 3600,      // 1 hour
            cache: 300,         // 5 minutes
            temp: 60            // 1 minute
        },
        keys: {
            user: 'currentUser',
            token: 'authToken',
            preferences: 'userPreferences',
            cache: 'dataCache'
        }
    },

    // UI Configuration
    ui: {
        // Toast notifications
        toast: {
            duration: 3000,     // 3 seconds
            position: 'top-right',
            maxVisible: 5,
            animations: true
        },
        
        // Pagination
        pagination: {
            itemsPerPage: 20,
            maxPages: 10
        },
        
        // Scroll
        scroll: {
            smooth: true,
            offset: 80 // navbar height
        },
        
        // Animations
        animations: {
            duration: 300,
            easing: 'ease-in-out'
        }
    },

    // Feature Flags
    features: {
        autoRefresh: true,
        refreshInterval: 120000,    // 2 minutes
        socialLogin: true,
        comments: true,
        ratings: true,
        watchHistory: true,
        recommendations: true
    },

    // Cache Configuration
    cache: {
        enabled: true,
        maxSize: 100,               // Max cached items
        ttl: 300000                 // 5 minutes
    },

    // Logging Configuration
    logging: {
        enabled: true,
        level: 'info',              // 'debug', 'info', 'warn', 'error'
        console: true,
        remote: false
    },

    // Validation Rules
    validation: {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        password: {
            minLength: 6,
            maxLength: 50,
            requireUppercase: false,
            requireLowercase: false,
            requireNumbers: false,
            requireSpecialChars: false
        },
        username: {
            minLength: 3,
            maxLength: 30,
            pattern: /^[a-zA-Z0-9_]+$/
        }
    },

    // Error Messages
    messages: {
        errors: {
            network: 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.',
            timeout: 'Yêu cầu quá lâu. Vui lòng thử lại.',
            unauthorized: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
            forbidden: 'Bạn không có quyền truy cập tính năng này.',
            notFound: 'Không tìm thấy dữ liệu yêu cầu.',
            serverError: 'Lỗi server. Vui lòng thử lại sau.',
            validation: 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.'
        },
        success: {
            login: 'Đăng nhập thành công!',
            logout: 'Đăng xuất thành công!',
            register: 'Đăng ký thành công!',
            saved: 'Đã lưu thành công!',
            deleted: 'Đã xóa thành công!',
            updated: 'Đã cập nhật thành công!'
        }
    },

    // Development/Production Mode
    isDevelopment: window.location.hostname === 'localhost' || 
                   window.location.hostname === '127.0.0.1',

    // Version
    version: '2.0.0',
    buildDate: '2025-10-14'
};

// Freeze config to prevent modifications
Object.freeze(AppConfig);
Object.freeze(AppConfig.api);
Object.freeze(AppConfig.storage);
Object.freeze(AppConfig.ui);
Object.freeze(AppConfig.features);
Object.freeze(AppConfig.cache);
Object.freeze(AppConfig.logging);
Object.freeze(AppConfig.validation);
Object.freeze(AppConfig.messages);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppConfig;
}

console.log(`✓ Config loaded - v${AppConfig.version} (${AppConfig.isDevelopment ? 'DEV' : 'PROD'})`);
