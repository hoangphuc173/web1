# 🏗️ CGV STREAMING PLATFORM - MODERN ARCHITECTURE

## 📐 Kiến trúc hệ thống mới

### Tổng quan
Hệ thống được tổ chức thành các module độc lập, tái sử dụng được, và dễ bảo trì.

```
public/
├── core.js                      ← Bootstrap loader (load đầu tiên)
├── core/
│   ├── config.js               ← Cấu hình toàn hệ thống
│   ├── utils.js                ← Utility functions & Logger
│   ├── api-client.js           ← HTTP client với retry & interceptors
│   ├── notifications.js        ← Toast notification system
│   └── auth.js                 ← Authentication management
├── storage-manager.js          ← Reactive state management
├── streaming.js                ← Page-specific code
├── login.js                    ← Page-specific code
└── movie-detail.js             ← Page-specific code
```

---

## 🎯 Core Modules

### 1. Config Module (`core/config.js`)

**Chức năng**: Centralized configuration - Single source of truth

**Sử dụng**:
```javascript
// API endpoint
const loginUrl = AppConfig.api.endpoints.login;

// Storage TTL
const userTTL = AppConfig.storage.ttl.user;

// Feature flags
if (AppConfig.features.autoRefresh) {
    // Enable auto refresh
}

// Validation
const emailValid = AppConfig.validation.email.test(email);

// Messages
notifications.error(AppConfig.messages.errors.network);
```

**Cấu trúc**:
```javascript
AppConfig = {
    api: { baseUrl, timeout, endpoints },
    storage: { prefix, ttl, keys },
    ui: { toast, pagination, scroll },
    features: { autoRefresh, socialLogin },
    cache: { enabled, maxSize, ttl },
    logging: { enabled, level },
    validation: { email, password, username },
    messages: { errors, success }
}
```

---

### 2. Utils Module (`core/utils.js`)

**Chức năng**: Common utilities & Logger

**Logger**:
```javascript
logger.debug('Debug message', { data });
logger.info('Info message');
logger.warn('Warning message');
logger.error('Error message', error);
```

**Utilities**:
```javascript
// Debounce
const debouncedSearch = Utils.debounce(searchFn, 300);

// Throttle
const throttledScroll = Utils.throttle(scrollFn, 100);

// Clone
const cloned = Utils.clone(originalObject);

// Format
Utils.formatDate(new Date(), 'DD/MM/YYYY');
Utils.formatNumber(1000000); // "1,000,000"
Utils.truncate('Long text...', 20);

// Validate
Utils.validateEmail('test@example.com');
Utils.validatePassword('mypassword');

// Async
await Utils.sleep(1000);
await Utils.retry(asyncFn, { retries: 3 });

// DOM
Utils.isInViewport(element);
Utils.scrollTo(element, offset);

// Query
const params = Utils.parseQuery('?id=123&sort=name');
const query = Utils.buildQuery({ id: 123, sort: 'name' });
```

---

### 3. API Client (`core/api-client.js`)

**Chức năng**: Centralized HTTP client với retry logic, interceptors

**Sử dụng cơ bản**:
```javascript
// GET
const movies = await api.get('/api/movies', { page: 1, limit: 20 });

// POST
const result = await api.post('/api/login', { email, password });

// PUT
await api.put('/api/movies/123', { title: 'New Title' });

// DELETE
await api.delete('/api/movies/123');

// PATCH
await api.patch('/api/movies/123', { views: 100 });
```

**Error handling**:
```javascript
try {
    const data = await api.get('/api/movies');
} catch (error) {
    if (error instanceof APIError) {
        console.log(error.getUserMessage());
        
        if (error.isUnauthorized()) {
            // Handle unauthorized
        }
        if (error.isNetworkError()) {
            // Handle network error
        }
    }
}
```

**Interceptors**:
```javascript
// Request interceptor (auto-add auth token)
api.addRequestInterceptor(async (url, options) => {
    options.headers['X-Custom-Header'] = 'value';
    return options;
});

// Response interceptor
api.addResponseInterceptor(async (response) => {
    // Process response
    return response;
});

// Error interceptor (auto-redirect on 401)
api.addErrorInterceptor(async (error) => {
    if (error.isUnauthorized()) {
        // Redirect to login
    }
    return error;
});
```

---

### 4. Notifications (`core/notifications.js`)

**Chức năng**: Advanced toast system với queue, priorities

**Sử dụng**:
```javascript
// Basic
notifications.success('Đăng nhập thành công!');
notifications.error('Có lỗi xảy ra!');
notifications.warning('Cảnh báo!');
notifications.info('Thông tin');

// With options
notifications.show('Message', 'info', 'Title', {
    duration: 5000,
    priority: 10,
    sticky: false,
    onClick: () => console.log('Clicked'),
    onClose: () => console.log('Closed')
});

// Special: Login required
notifications.loginRequired();

// Special: Loading
const loading = notifications.loading('Đang tải...');
loading.update('Đang xử lý...');
loading.success('Hoàn thành!');
// or loading.error('Lỗi!');
// or loading.close();

// Update notification
const id = notifications.info('Processing...');
notifications.update(id, { 
    message: 'Almost done...',
    type: 'success' 
});

// Close specific
notifications.close(id);

// Close all
notifications.closeAll();
```

**Backward compatible**:
```javascript
showSuccessToast('Success!');
showErrorToast('Error!');
showWarningToast('Warning!');
showInfoToast('Info!');
showLoginToast();
```

---

### 5. Auth Module (`core/auth.js`)

**Chức năng**: Centralized authentication

**Login/Register**:
```javascript
// Login
const result = await auth.login(email, password);
if (result.success) {
    console.log('User:', result.user);
} else {
    console.error('Error:', result.error);
}

// Register
const result = await auth.register(name, email, password);

// OAuth
try {
    const result = await auth.oauthLogin('google'); // 'facebook', 'linkedin'
    console.log('User:', result.user);
} catch (error) {
    console.error('OAuth failed:', error);
}
```

**Logout**:
```javascript
await auth.logout();
```

**Check auth state**:
```javascript
if (auth.isAuthenticated()) {
    const user = auth.getUser();
}

if (auth.isPremium()) {
    // Show premium content
}
```

**Require auth**:
```javascript
// Redirect to login if not authenticated
if (!auth.requireAuth()) {
    return; // Will redirect
}
```

**Watch auth changes**:
```javascript
const unsubscribe = auth.onAuthStateChange((user) => {
    if (user) {
        console.log('User logged in:', user);
    } else {
        console.log('User logged out');
    }
});

// Later: unsubscribe()
```

**Update user**:
```javascript
auth.updateUser({ 
    name: 'New Name',
    avatar: 'new-avatar.jpg' 
});
```

---

### 6. Storage Manager (Reactive)

**Chức năng**: Smart storage với reactive updates

**Basic usage**:
```javascript
// Set với TTL
smartStorage.set('key', value, 3600); // 1 hour

// Get
const value = smartStorage.get('key', defaultValue);

// Remove
smartStorage.remove('key');

// Clear all
smartStorage.clear();

// Check exists
if (smartStorage.has('key')) { }
```

**Reactive updates**:
```javascript
// Watch for changes
const unsubscribe = smartStorage.watch('currentUser', (value) => {
    console.log('User changed:', value);
    updateUI(value);
});

// Later: unsubscribe()
```

---

## 📄 Cách sử dụng trong Pages

### Template chuẩn cho HTML:

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title</title>
    
    <!-- CSS -->
    <link rel="stylesheet" href="style.css">
    
    <!-- Core Bootstrap (QUAN TRỌNG: Load đầu tiên) -->
    <script src="core.js"></script>
</head>
<body>
    <!-- Content -->
    
    <!-- Page-specific script -->
    <script src="page-script.js"></script>
</body>
</html>
```

### Template chuẩn cho JavaScript:

```javascript
// page-script.js

/**
 * Initialize page
 */
initializePage('PageName', () => {
    // All core modules are loaded here
    
    // Use any core module
    logger.info('Page loaded');
    
    // Check auth
    if (!auth.isAuthenticated()) {
        notifications.loginRequired();
        return;
    }
    
    // Load data
    loadData();
    
    // Setup listeners
    setupEventListeners();
});

/**
 * Load data from API
 */
async function loadData() {
    try {
        const loading = notifications.loading('Đang tải dữ liệu...');
        
        const data = await api.get('/api/movies');
        
        loading.success('Tải dữ liệu thành công!');
        displayData(data);
    } catch (error) {
        notifications.error(
            error instanceof APIError 
                ? error.getUserMessage() 
                : 'Không thể tải dữ liệu'
        );
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Debounced search
    const searchInput = document.getElementById('search');
    searchInput.addEventListener('input', Utils.debounce((e) => {
        performSearch(e.target.value);
    }, 300));
    
    // Button clicks
    document.getElementById('btn').addEventListener('click', handleClick);
}
```

---

## 🎨 Best Practices

### 1. **Luôn load core.js trước**
```html
<script src="core.js"></script>
<script src="your-page.js"></script>
```

### 2. **Sử dụng initializePage()**
```javascript
initializePage('PageName', () => {
    // Your code here - all modules loaded
});
```

### 3. **Error handling với APIError**
```javascript
try {
    await api.get('/api/data');
} catch (error) {
    if (error instanceof APIError) {
        notifications.error(error.getUserMessage());
    }
}
```

### 4. **Logging everywhere**
```javascript
logger.info('Action performed', { data });
logger.error('Error occurred', error);
```

### 5. **Reactive updates**
```javascript
// Watch auth state
auth.onAuthStateChange((user) => {
    updateNavbar(user);
});

// Watch storage
smartStorage.watch('preferences', (prefs) => {
    applyPreferences(prefs);
});
```

### 6. **Debounce/Throttle events**
```javascript
// Search input
input.addEventListener('input', Utils.debounce(search, 300));

// Scroll
window.addEventListener('scroll', Utils.throttle(onScroll, 100));
```

### 7. **Config-driven code**
```javascript
if (AppConfig.features.autoRefresh) {
    setInterval(refresh, AppConfig.features.refreshInterval);
}
```

---

## 🚀 Migration từ code cũ

### Before:
```javascript
// Old way
const user = JSON.parse(sessionStorage.getItem('currentUser'));
alert('Success!');
fetch('http://localhost:5000/api/movies')
    .then(res => res.json())
    .then(data => console.log(data));
```

### After:
```javascript
// New way
const user = smartStorage.get('currentUser');
notifications.success('Success!');
const data = await api.get('/api/movies');
```

---

## 📊 Lợi ích

✅ **Consistency**: Code đồng nhất giữa các files  
✅ **Maintainability**: Dễ bảo trì và mở rộng  
✅ **Reusability**: Modules tái sử dụng được  
✅ **Type Safety**: Centralized config giảm lỗi  
✅ **Error Handling**: Xử lý lỗi thống nhất  
✅ **Logging**: Track errors và actions  
✅ **Performance**: Caching, debounce, throttle  
✅ **Reactive**: Auto-update UI when data changes  

---

**Version**: 2.0.0  
**Last Updated**: 14/10/2025
