 // API Configuration
const API_BASE_URL = 'http://localhost:8001';  // User Service
const PRODUCT_API_URL = 'http://localhost:8002'; // Product Service
window.API_BASE_URL = API_BASE_URL;
window.PRODUCT_API_URL = PRODUCT_API_URL;
const API_TIMEOUT = 10000;

// Token Management
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
        this.timeout = API_TIMEOUT;
    }

    // Get headers with auth token
    getHeaders(contentType = 'application/json') {
        const headers = {
            'Content-Type': contentType,
        };
        
        const token = localStorage.getItem(TOKEN_KEY);
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    }

    // Generic fetch with timeout
    async fetch(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
            });
            
            clearTimeout(timeoutId);
            
            // Handle 401 - redirect to login
            if (response.status === 401) {
                this.logout();
                window.location.href = '/login.html';
                return null;
            }
            
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    // GET request
    async get(endpoint) {
        const response = await this.fetch(endpoint, {
            method: 'GET',
            headers: this.getHeaders(),
        });
        
        if (!response) return null;
        
        if (!response.ok) {
            throw new Error(`GET ${endpoint} failed: ${response.status}`);
        }
        
        return response.json();
    }

    // POST request
    async post(endpoint, data = {}) {
        const response = await this.fetch(endpoint, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });
        
        if (!response) return null;
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `POST ${endpoint} failed: ${response.status}`);
        }
        
        return response.json();
    }

    // PUT request
    async put(endpoint, data = {}) {
        const response = await this.fetch(endpoint, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });
        
        if (!response) return null;
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `PUT ${endpoint} failed: ${response.status}`);
        }
        
        return response.json();
    }

    // DELETE request
    async delete(endpoint) {
        const response = await this.fetch(endpoint, {
            method: 'DELETE',
            headers: this.getHeaders(),
        });
        
        if (!response) return null;
        
        if (!response.ok) {
            throw new Error(`DELETE ${endpoint} failed: ${response.status}`);
        }
        
        return response.status === 204 ? null : response.json();
    }

    // AUTH ENDPOINTS
    async register(email, fullName, password) {
        return this.post('/auth/register/', {
            email,
            full_name: fullName,
            password,
        });
    }

    async login(email, password) {
        const data = await this.post('/auth/login/', { email, password });
        if (data) {
            // Đảm bảo lấy token từ đúng cấu trúc response
            const accessToken = data.tokens?.access || data.access || data.token;
            const refreshToken = data.tokens?.refresh || data.refresh;
            if (accessToken) {
                this.setToken(accessToken, refreshToken);
                if (data.user) {
                    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
                }
            }
        }
        return data;
    }

    async logout() {
        try {
            const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
            if (refreshToken) {
                await this.post('/auth/logout/', { refresh: refreshToken });
            }
        } catch (error) {
            console.error('Logout error:', error);
        }
        
        this.clearToken();
        localStorage.removeItem(USER_KEY);
    }

    // TOKEN MANAGEMENT
    setToken(accessToken, refreshToken = null) {
        localStorage.setItem(TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        }
    }

    clearToken() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    }

    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    isLoggedIn() {
        return !!this.getToken();
    }

    getCurrentUser() {
        const user = localStorage.getItem(USER_KEY);
        return user ? JSON.parse(user) : null;
    }

    // USER ENDPOINTS
    async getProfile() {
        return this.get('/users/me/');
    }

    async updateProfile(fullName, phone = null, avatar = null) {
        const data = { full_name: fullName };
        if (phone) data.phone = phone;
        if (avatar) data.avatar = avatar;
        return this.put('/users/me/', data);
    }

    async changePassword(oldPassword, newPassword) {
        return this.post('/users/me/change-password/', {
            old_password: oldPassword,
            new_password: newPassword,
            new_password2: newPassword,
        });
    }

    // ADDRESS ENDPOINTS
    async getAddresses() {
        return this.get('/users/me/addresses/');
    }

    async addAddress(data) {
        return this.post('/users/me/addresses/', data);
    }

    async updateAddress(addressId, data) {
        return this.put(`/users/me/addresses/${addressId}/`, data);
    }

    async deleteAddress(addressId) {
        return this.delete(`/users/me/addresses/${addressId}/`);
    }

    async setDefaultAddress(addressId) {
        return this.post(`/users/me/addresses/${addressId}/set-default/`, {});
    }

    // PRODUCT ENDPOINTS
    async getProducts(page = 1, search = null, category = null) {
        let endpoint = `${PRODUCT_API_URL}/products/?page=${page}`;
        if (search) endpoint += `&search=${encodeURIComponent(search)}`;
        if (category) endpoint += `&category=${encodeURIComponent(category)}`;
        return fetch(endpoint).then((response) => {
            if (!response.ok) {
                throw new Error(`GET ${endpoint} failed: ${response.status}`);
            }
            return response.json();
        });
    }

    async getProduct(productId) {
        const endpoint = `${PRODUCT_API_URL}/products/${productId}/`;
        return fetch(endpoint).then((response) => {
            if (!response.ok) {
                throw new Error(`GET ${endpoint} failed: ${response.status}`);
            }
            return response.json();
        });
    }

    // CART ENDPOINTS
    async getCart() {
        return this.get('/cart/');
    }

    async addToCart(productId, quantity = 1) {
        return this.post('/cart/items/', { product_id: productId, quantity });
    }

    async updateCartItem(itemId, quantity) {
        return this.put(`/cart/items/${itemId}/`, { quantity });
    }

    async removeFromCart(itemId) {
        return this.delete(`/cart/items/${itemId}/`);
    }

    // ORDER ENDPOINTS
    async getOrders() {
        return this.get('/orders/');
    }

    async getOrder(orderId) {
        return this.get(`/orders/${orderId}/`);
    }

    async createOrder(data) {
        return this.post('/orders/', data);
    }

    // PAYMENT ENDPOINTS
    async processPayment(orderId, paymentMethod) {
        return this.post('/payments/', { order_id: orderId, payment_method: paymentMethod });
    }

    // ADMIN — USER MANAGEMENT
    async adminGetUsers() {
        return this.get('/users/');
    }

    async adminCreateUser(email, password, role, fullName = '') {
        return this.post('/users/', { email, password, role, full_name: fullName });
    }

    async adminGetUser(id) {
        return this.get(`/users/${id}/`);
    }

    async adminUpdateUser(id, data) {
        return this.put(`/users/${id}/`, data);
    }

    async adminToggleUser(id, isActive) {
        return this.put(`/users/${id}/`, { is_active: isActive });
    }

    async adminGetStats() {
        return this.get('/users/stats/');
    }

    // HEALTH CHECK
    async healthCheck() {
        return this.get('/users/health/');
    }
}

// Create global API instance
const api = new APIClient();

// Utility Functions
function showAlert(message, type = 'success', elementId = 'alertBox') {
    const alertBox = document.getElementById(elementId);
    if (!alertBox) return;
    
    alertBox.className = `alert alert-${type} d-block`;
    alertBox.textContent = message;
    alertBox.style.display = 'block';
    
    if (type === 'success') {
        setTimeout(() => {
            alertBox.style.display = 'none';
        }, 3000);
    }
}

function hideAlert(elementId = 'alertBox') {
    const alertBox = document.getElementById(elementId);
    if (alertBox) {
        alertBox.style.display = 'none';
    }
}

function showLoading(buttonId = 'btnSubmit') {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    }
}

function hideLoading(buttonId = 'btnSubmit', text = 'Submit') {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = text;
    }
}

function formatPrice(price) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
    }).format(price);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    }).format(new Date(date));
}

function redirectToLogin() {
    window.location.href = '/login.html';
}

function checkAuth() {
    if (!api.isLoggedIn()) {
        redirectToLogin();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, showAlert, hideAlert, showLoading, hideLoading, formatPrice, formatDate };
}
