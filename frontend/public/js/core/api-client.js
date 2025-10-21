/**
 * 🌐 API Client Module
 * Centralized HTTP client with interceptors, error handling, and retry logic
 */

class APIClient {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.api.baseUrl;
        this.timeout = config.api.timeout;
        this.interceptors = {
            request: [],
            response: [],
            error: []
        };
    }

    /**
     * Add request interceptor
     */
    addRequestInterceptor(fn) {
        this.interceptors.request.push(fn);
    }

    /**
     * Add response interceptor
     */
    addResponseInterceptor(fn) {
        this.interceptors.response.push(fn);
    }

    /**
     * Add error interceptor
     */
    addErrorInterceptor(fn) {
        this.interceptors.error.push(fn);
    }

    /**
     * Process request through interceptors
     */
    async _processRequest(url, options) {
        let processedOptions = { ...options };
        
        for (const interceptor of this.interceptors.request) {
            processedOptions = await interceptor(url, processedOptions);
        }
        
        return processedOptions;
    }

    /**
     * Process response through interceptors
     */
    async _processResponse(response) {
        let processedResponse = response;
        
        for (const interceptor of this.interceptors.response) {
            processedResponse = await interceptor(processedResponse);
        }
        
        return processedResponse;
    }

    /**
     * Process error through interceptors
     */
    async _processError(error) {
        let processedError = error;
        
        for (const interceptor of this.interceptors.error) {
            processedError = await interceptor(processedError);
        }
        
        return processedError;
    }

    /**
     * Make HTTP request with retry logic
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include', // Send cookies with requests
            ...options
        };

        try {
            // Process through request interceptors
            const processedOptions = await this._processRequest(url, defaultOptions);

            // Make request with retry
            const response = await Utils.retry(
                async () => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

                    try {
                        const res = await fetch(url, {
                            ...processedOptions,
                            signal: controller.signal
                        });
                        clearTimeout(timeoutId);
                        return res;
                    } catch (error) {
                        clearTimeout(timeoutId);
                        throw error;
                    }
                },
                {
                    retries: this.config.api.retries,
                    delay: this.config.api.retryDelay
                }
            );

            // Process through response interceptors
            const processedResponse = await this._processResponse(response);

            // Parse JSON if successful
            if (processedResponse.ok) {
                const data = await processedResponse.json();
                logger.info(`API Success: ${options.method || 'GET'} ${endpoint}`, {
                    status: processedResponse.status,
                    data
                });
                return data;
            } else {
                throw new APIError(
                    processedResponse.statusText,
                    processedResponse.status,
                    await processedResponse.json().catch(() => ({}))
                );
            }
        } catch (error) {
            // Process through error interceptors
            const processedError = await this._processError(error);
            
            logger.error(`API Error: ${options.method || 'GET'} ${endpoint}`, {
                error: processedError.message,
                status: processedError.status
            });

            throw processedError;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = Utils.buildQuery(params);
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * PATCH request
     */
    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, data = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }

    isNetworkError() {
        return this.status === 0 || this.message.includes('NetworkError');
    }

    isTimeout() {
        return this.message.includes('timeout') || this.message.includes('aborted');
    }

    isUnauthorized() {
        return this.status === 401;
    }

    isForbidden() {
        return this.status === 403;
    }

    isNotFound() {
        return this.status === 404;
    }

    isServerError() {
        return this.status >= 500;
    }

    getUserMessage() {
        if (this.isNetworkError()) return AppConfig.messages.errors.network;
        if (this.isTimeout()) return AppConfig.messages.errors.timeout;
        if (this.isUnauthorized()) return AppConfig.messages.errors.unauthorized;
        if (this.isForbidden()) return AppConfig.messages.errors.forbidden;
        if (this.isNotFound()) return AppConfig.messages.errors.notFound;
        if (this.isServerError()) return AppConfig.messages.errors.serverError;
        return this.data.error || this.message || AppConfig.messages.errors.validation;
    }
}

// Create global API client instance
const api = new APIClient(AppConfig);

// Add default request interceptor
api.addRequestInterceptor(async (url, options) => {
    // No longer sending token, session is handled by cookies
    return options;
});

// Add default response interceptor
api.addResponseInterceptor(async (response) => {
    // Can add global response processing here
    return response;
});

// Add default error interceptor
api.addErrorInterceptor(async (error) => {
    // Handle unauthorized errors globally
    if (error.isUnauthorized && error.isUnauthorized()) {
        // Clear user data and redirect to login
        smartStorage.remove('currentUser');
        
        // Show notification
        if (typeof showWarningToast !== 'undefined') {
            showWarningToast('Phiên đăng nhập đã hết hạn!', 'Yêu cầu đăng nhập');
        }
        
        // Redirect after delay
        setTimeout(() => {
            window.location.href = '/login.html';
        }, 2000);
    }
    
    return error;
});

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError, api };
}

console.log('✓ API Client loaded');
