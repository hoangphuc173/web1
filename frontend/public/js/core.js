/**
 * 🚀 CGV Streaming Platform - Core Bootstrap
 * Loads all core modules in the correct order
 * Version: 2.0.0
 */

(function() {
    'use strict';

    // Module loading order
    const modules = [
        'core/config.js',
        'storage-manager.js',
        'core/utils.js',
        'core/api-client.js',
        'core/notifications.js',
        'core/auth.js'
    ];

    let loadedModules = 0;
    const totalModules = modules.length;

    /**
     * Check if all modules are loaded
     */
    function checkAllModulesLoaded() {
        loadedModules++;
        
        if (loadedModules === totalModules) {
            console.log('%c✓ All core modules loaded successfully', 'color: #4CAF50; font-weight: bold; font-size: 14px;');
            console.log(`%c🚀 CGV Streaming Platform v${AppConfig.version} ready!`, 'color: #2196F3; font-weight: bold; font-size: 16px;');
            
            // Dispatch custom event when all modules loaded
            window.dispatchEvent(new CustomEvent('cgv:core:ready', {
                detail: {
                    version: AppConfig.version,
                    modules: modules
                }
            }));
        }
    }

    /**
     * Load script dynamically
     */
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = false; // Load in order
            script.onload = () => {
                console.log(`✓ Loaded: ${src}`);
                resolve();
            };
            script.onerror = () => {
                console.error(`✗ Failed to load: ${src}`);
                reject(new Error(`Failed to load ${src}`));
            };
            document.head.appendChild(script);
        });
    }

    /**
     * Load all modules
     */
    async function loadModules() {
        console.log('%c⏳ Loading CGV core modules...', 'color: #FF9800; font-weight: bold;');
        
        try {
            for (const module of modules) {
                await loadScript(module);
                checkAllModulesLoaded();
            }
        } catch (error) {
            console.error('%c✗ Failed to load core modules', 'color: #F44336; font-weight: bold;', error);
            
            // Show error notification if possible
            if (typeof showErrorToast !== 'undefined') {
                showErrorToast('Không thể tải hệ thống. Vui lòng tải lại trang.', 'Lỗi hệ thống');
            } else {
                alert('Không thể tải hệ thống. Vui lòng tải lại trang.');
            }
        }
    }

    // Start loading when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadModules);
    } else {
        loadModules();
    }

    // Global error handler
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        
        // Log to analytics if available
        if (typeof logger !== 'undefined') {
            logger.error('Unhandled error', {
                message: event.error?.message,
                stack: event.error?.stack
            });
        }
    });

    // Global unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        
        // Log to analytics if available
        if (typeof logger !== 'undefined') {
            logger.error('Unhandled promise rejection', {
                reason: event.reason
            });
        }
    });

})();

/**
 * Global initialization function
 * Call this in your page-specific scripts
 */
function initializePage(pageName, initFn) {
    // Wait for core modules to be ready
    window.addEventListener('cgv:core:ready', () => {
        console.log(`%c📄 Initializing page: ${pageName}`, 'color: #9C27B0; font-weight: bold;');
        
        try {
            initFn();
            console.log(`✓ Page ${pageName} initialized successfully`);
        } catch (error) {
            console.error(`✗ Failed to initialize page ${pageName}:`, error);
            
            if (typeof logger !== 'undefined') {
                logger.error(`Page initialization failed: ${pageName}`, error);
            }
            
            if (typeof notifications !== 'undefined') {
                notifications.error('Không thể khởi tạo trang. Vui lòng tải lại.', 'Lỗi');
            }
        }
    });
}
