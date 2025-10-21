/**
 * 🔐 Authentication Module
 * Centralized authentication management
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.authCallbacks = [];
        this.initPromise = this.init(); // Keep track of the init promise
    }

    async init() {
        // Check auth status with the server
        await this.checkAuthStatus();
        // Notify listeners AFTER checking
        this.notifyAuthChange();
    }

    /**
     * Check authentication status with the server
     */
    async checkAuthStatus() {
        try {
            const result = await api.get(AppConfig.api.endpoints.checkAuth);
            if (result.authenticated) {
                this.currentUser = result.user;
                smartStorage.set(AppConfig.storage.keys.user, result.user, AppConfig.storage.ttl.user);
                logger.info('User is authenticated', { user: result.user.email });
            } else {
                this.currentUser = null;
                smartStorage.remove(AppConfig.storage.keys.user);
            }
        } catch (error) {
            logger.warn('Auth check failed, assuming logged out.', error);
            this.currentUser = null;
            smartStorage.remove(AppConfig.storage.keys.user);
        }
    }

    /**
     * Register auth state change callback
     */
    onAuthStateChange(callback) {
        this.authCallbacks.push(callback);
        // Immediately call with current state
        // callback(this.currentUser);
    }

    /**
     * Notify all callbacks of auth state change
     */
    notifyAuthChange() {
        this.authCallbacks.forEach(callback => {
            try {
                callback(this.currentUser);
            } catch (error) {
                logger.error('Error in auth callback', error);
            }
        });
    }

    /**
     * Login user
     */
    async login(email, password) {
        try {
            logger.info('Attempting login', { email });

            const response = await api.post(AppConfig.api.endpoints.login, {
                email,
                password
            });

            // Check if API returned success
            if (!response.success) {
                throw new Error(response.error || 'Đăng nhập thất bại');
            }

            const userData = response.data;
            this.currentUser = userData;
            
            // Store user with TTL
            smartStorage.set(
                AppConfig.storage.keys.user,
                userData,
                AppConfig.storage.ttl.user
            );

            logger.info('Login successful', { user: userData.email });
            this.notifyAuthChange();

            return { success: true, user: userData };
        } catch (error) {
            logger.error('Login failed', error);
            return {
                success: false,
                error: error.message || 'Email hoặc mật khẩu không đúng'
            };
        }
    }

    /**
     * Register user
     */
    async register(name, email, password) {
        try {
            logger.info('Attempting registration', { email });

            const response = await api.post(AppConfig.api.endpoints.register, {
                name,
                email,
                password
            });

            // Check if API returned success
            if (!response.success) {
                throw new Error(response.error || 'Đăng ký thất bại');
            }

            const userData = response.data;
            this.currentUser = userData;
            
            // Store user with TTL
            smartStorage.set(
                AppConfig.storage.keys.user,
                userData,
                AppConfig.storage.ttl.user
            );

            logger.info('Registration successful', { user: userData.email });
            this.notifyAuthChange();

            return { success: true, user: userData };

        } catch (error) {
            logger.error('Registration failed', error);
            return {
                success: false,
                error: error.message || 'Đăng ký thất bại'
            };
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            logger.info('Logging out', { user: this.currentUser?.email });

            // Call logout API to clear server session (POST method)
            await api.post(AppConfig.api.endpoints.logout);

            // Clear local user data
            this.currentUser = null;
            smartStorage.remove(AppConfig.storage.keys.user);

            logger.info('Logout successful');
            this.notifyAuthChange();

            return { success: true };
        } catch (error) {
            // Even if API fails, clear local data
            this.currentUser = null;
            smartStorage.remove(AppConfig.storage.keys.user);
            this.notifyAuthChange();
            logger.error('Logout failed but local data cleared', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Check if user is logged in
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }

    /**
     * Get current user
     */
    getUser() {
        return this.currentUser;
    }

    /**
     * Get current user (alias)
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Update user profile
     */
    updateUser(updates) {
        if (!this.currentUser) return;

        this.currentUser = {
            ...this.currentUser,
            ...updates
        };

        smartStorage.set(
            AppConfig.storage.keys.user,
            this.currentUser,
            AppConfig.storage.ttl.user
        );

        this.notifyAuthChange();
        logger.info('User updated', updates);
    }

    /**
     * Require authentication (redirect to login if not authenticated)
     */
    async requireAuth(redirectUrl = '/login.html', message = 'Vui lòng đăng nhập để tiếp tục!') {
        await this.initPromise; // Ensure initial auth check is complete
        if (!this.isAuthenticated()) {
            notifications.loginRequired(message);
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 2000);
            return false;
        }
        return true;
    }

    /**
     * Check if user has premium subscription
     */
    isPremium() {
        return this.currentUser?.subscription === 'premium' || 
               this.currentUser?.subscription === 'vip';
    }

    /**
     * OAuth login (Facebook, Google, LinkedIn)
     */
    async oauthLogin(provider) {
        try {
            logger.info('OAuth login attempt', { provider });

            // Open OAuth popup
            const width = 600;
            const height = 700;
            const left = (window.screen.width - width) / 2;
            const top = (window.screen.height - height) / 2;
            
            const popup = window.open(
                `${AppConfig.api.baseUrl}/api/auth/${provider}`,
                'oauth',
                `width=${width},height=${height},top=${top},left=${left}`
            );

            // Wait for OAuth callback
            return new Promise((resolve, reject) => {
                const handleMessage = (event) => {
                    if (event.origin !== window.location.origin) return;

                    const { success, user, error } = event.data;

                    if (success && user) {
                        this.currentUser = user;
                        smartStorage.set(
                            AppConfig.storage.keys.user,
                            user,
                            AppConfig.storage.ttl.user
                        );
                        this.notifyAuthChange();
                        logger.info('OAuth login successful', { provider });
                        resolve({ success: true, user });
                    } else {
                        logger.error('OAuth login failed', { provider, error });
                        reject(new Error(error || 'OAuth login failed'));
                    }

                    window.removeEventListener('message', handleMessage);
                    if (popup) popup.close();
                };

                window.addEventListener('message', handleMessage);

                // Check if popup closed
                const checkPopup = setInterval(() => {
                    if (popup && popup.closed) {
                        clearInterval(checkPopup);
                        window.removeEventListener('message', handleMessage);
                        reject(new Error('OAuth popup closed'));
                    }
                }, 1000);
            });
        } catch (error) {
            logger.error('OAuth login error', error);
            throw error;
        }
    }
}

// Create global auth manager instance
const auth = new AuthManager();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AuthManager, auth };
}

console.log('✓ Authentication Module loaded');
