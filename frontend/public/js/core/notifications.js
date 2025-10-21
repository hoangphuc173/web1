/**
 * 🔔 Notification System Module
 * Advanced toast notification system with queue, priorities, and animations
 */

class NotificationSystem {
    constructor(config = {}) {
        this.config = {
            duration: config.duration || 3000,
            position: config.position || 'top-right',
            maxVisible: config.maxVisible || 5,
            animations: config.animations !== false,
            ...config
        };
        
        this.queue = [];
        this.visible = [];
        this.container = null;
        this.init();
    }

    init() {
        // Create container if not exists
        if (!document.getElementById('toastContainer')) {
            this.container = document.createElement('div');
            this.container.id = 'toastContainer';
            this.container.className = `toast-container toast-${this.config.position}`;
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toastContainer');
        }
    }

    /**
     * Show notification
     */
    show(message, type = 'info', title = '', options = {}) {
        const notification = {
            id: Utils.generateId(),
            message,
            type,
            title,
            duration: options.duration || this.config.duration,
            priority: options.priority || 0,
            sticky: options.sticky || false,
            onClick: options.onClick,
            onClose: options.onClose
        };

        // Add to queue based on priority
        this.queue.push(notification);
        this.queue.sort((a, b) => b.priority - a.priority);

        // Process queue
        this.processQueue();

        return notification.id;
    }

    /**
     * Process notification queue
     */
    processQueue() {
        while (this.visible.length < this.config.maxVisible && this.queue.length > 0) {
            const notification = this.queue.shift();
            this.render(notification);
        }
    }

    /**
     * Render notification
     */
    render(notification) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${notification.type}`;
        toast.id = `toast-${notification.id}`;
        toast.setAttribute('data-toast-id', notification.id);

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        toast.innerHTML = `
            <i class="fas ${icons[notification.type]}"></i>
            <div class="toast-content">
                ${notification.title ? `<div class="toast-title">${Utils.sanitizeHTML(notification.title)}</div>` : ''}
                <div class="toast-message">${Utils.sanitizeHTML(notification.message)}</div>
            </div>
            <button class="toast-close" data-action="close">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add click handler
        if (notification.onClick) {
            toast.style.cursor = 'pointer';
            toast.addEventListener('click', (e) => {
                if (!e.target.closest('[data-action="close"]')) {
                    notification.onClick(notification);
                }
            });
        }

        // Add close button handler
        const closeBtn = toast.querySelector('[data-action="close"]');
        closeBtn.addEventListener('click', () => {
            this.close(notification.id);
        });

        // Add to container with animation
        this.container.appendChild(toast);
        this.visible.push(notification);

        if (this.config.animations) {
            requestAnimationFrame(() => {
                toast.classList.add('toast-show');
            });
        }

        // Auto close if not sticky
        if (!notification.sticky) {
            setTimeout(() => {
                this.close(notification.id);
            }, notification.duration);
        }

        logger.debug(`Notification shown: ${notification.type}`, { notification });
    }

    /**
     * Close notification
     */
    close(id) {
        const toast = document.querySelector(`[data-toast-id="${id}"]`);
        if (!toast) return;

        // Remove from visible array
        const index = this.visible.findIndex(n => n.id === id);
        if (index !== -1) {
            const notification = this.visible[index];
            this.visible.splice(index, 1);

            // Call onClose callback
            if (notification.onClose) {
                notification.onClose(notification);
            }
        }

        // Animate out and remove
        if (this.config.animations) {
            toast.classList.add('toast-hide');
            setTimeout(() => {
                toast.remove();
                this.processQueue(); // Process next in queue
            }, 300);
        } else {
            toast.remove();
            this.processQueue();
        }

        logger.debug(`Notification closed: ${id}`);
    }

    /**
     * Close all notifications
     */
    closeAll() {
        const ids = this.visible.map(n => n.id);
        ids.forEach(id => this.close(id));
        this.queue = [];
    }

    /**
     * Update notification
     */
    update(id, updates) {
        const notification = this.visible.find(n => n.id === id);
        if (!notification) return;

        Object.assign(notification, updates);

        const toast = document.querySelector(`[data-toast-id="${id}"]`);
        if (toast) {
            if (updates.message) {
                const messageEl = toast.querySelector('.toast-message');
                if (messageEl) {
                    messageEl.textContent = updates.message;
                }
            }
            if (updates.title) {
                const titleEl = toast.querySelector('.toast-title');
                if (titleEl) {
                    titleEl.textContent = updates.title;
                }
            }
            if (updates.type) {
                toast.className = `toast toast-${updates.type} toast-show`;
            }
        }
    }

    // Convenience methods
    success(message, title = 'Thành công', options = {}) {
        return this.show(message, 'success', title, options);
    }

    error(message, title = 'Lỗi', options = {}) {
        return this.show(message, 'error', title, options);
    }

    warning(message, title = 'Cảnh báo', options = {}) {
        return this.show(message, 'warning', title, options);
    }

    info(message, title = 'Thông tin', options = {}) {
        return this.show(message, 'info', title, options);
    }

    // Special notification: Login required
    loginRequired(message = 'Vui lòng đăng nhập để tiếp tục!', redirectDelay = 2000) {
        return this.warning(message, 'Yêu cầu đăng nhập', {
            duration: redirectDelay,
            priority: 10,
            onClick: () => {
                window.location.href = '/login.html';
            }
        });
    }

    // Special notification: Loading
    loading(message = 'Đang xử lý...', title = '') {
        const id = this.info(message, title, {
            sticky: true,
            priority: 5
        });
        return {
            id,
            update: (msg) => this.update(id, { message: msg }),
            close: () => this.close(id),
            success: (msg) => {
                this.close(id);
                return this.success(msg);
            },
            error: (msg) => {
                this.close(id);
                return this.error(msg);
            }
        };
    }
}

// Create global notification instance
const notifications = new NotificationSystem(AppConfig.ui.toast);

// Backward compatible functions
function showToast(message, type = 'info', title = '', duration = 3000) {
    return notifications.show(message, type, title, { duration });
}

function showSuccessToast(message, title = 'Thành công') {
    return notifications.success(message, title);
}

function showErrorToast(message, title = 'Lỗi') {
    return notifications.error(message, title);
}

function showWarningToast(message, title = 'Cảnh báo', duration = 5000) {
    return notifications.warning(message, title, { duration });
}

function showInfoToast(message, title = 'Thông tin') {
    return notifications.info(message, title);
}

function showLoginToast(message = 'Vui lòng đăng nhập để tiếp tục!') {
    return notifications.loginRequired(message);
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        NotificationSystem,
        notifications,
        showToast,
        showSuccessToast,
        showErrorToast,
        showWarningToast,
        showInfoToast,
        showLoginToast
    };
}

console.log('✓ Notification System loaded');
