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

    // CART ENDPOINTS (cart-service: port 8003)
    _cartFetch(path, options = {}) {
        const url = `http://localhost:8003${path}`;
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 10000);
        return fetch(url, { ...options, signal: ctrl.signal })
            .finally(() => clearTimeout(tid));
    }

    _cartHeaders() {
        return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.getToken()}` };
    }

    async getCart() {
        const res = await this._cartFetch('/cart/', { headers: this._cartHeaders() });
        if (!res.ok) throw new Error(`Lỗi ${res.status}`);
        return res.json();
    }

    async addToCart(productId, quantity = 1) {
        const res = await this._cartFetch('/cart/add', {
            method: 'POST',
            headers: this._cartHeaders(),
            body: JSON.stringify({ product_id: productId, quantity }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Lỗi ${res.status}`);
        }
        return res.json();
    }

    async updateCartItem(productId, quantity) {
        const res = await this._cartFetch('/cart/update', {
            method: 'PATCH',
            headers: this._cartHeaders(),
            body: JSON.stringify({ product_id: productId, quantity }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Lỗi ${res.status}`);
        }
        return res.json();
    }

    async removeFromCart(productId) {
        const res = await this._cartFetch('/cart/remove', {
            method: 'DELETE',
            headers: this._cartHeaders(),
            body: JSON.stringify({ product_id: productId }),
        });
        if (!res.ok) throw new Error(`Lỗi ${res.status}`);
        return res.json();
    }

    // ORDER ENDPOINTS (order-service: port 8004)
    async getOrders() {
        const res = await fetch('http://localhost:8004/orders/', { headers: { Authorization: `Bearer ${this.getToken()}` } });
        if (!res.ok) throw new Error(`Lỗi ${res.status}`);
        return res.json();
    }

    async getOrder(orderId) {
        const res = await fetch(`http://localhost:8004/orders/${orderId}`, { headers: { Authorization: `Bearer ${this.getToken()}` } });
        if (!res.ok) throw new Error(`Lỗi ${res.status}`);
        return res.json();
    }

    async createOrder(shippingAddress) {
        const res = await fetch('http://localhost:8004/orders/', {
            method: 'POST',
            headers: { Authorization: `Bearer ${this.getToken()}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ shipping_address: shippingAddress }),
        });
        const data = await res.json();
        if (!res.ok && !data.id) throw new Error(data.error || `Lỗi ${res.status}`);
        return data;
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

/**
 * Render link đăng nhập/đăng xuất vào phần tử có id navAuthLinks.
 * Dùng trên các trang công khai (products, product-detail, index, cart).
 */
function renderNavAuth() {
    const el = document.getElementById('navAuthLinks');
    if (!el) return;
    if (api.isLoggedIn()) {
        const user = api.getCurrentUser();
        const isAdmin = user?.role === 'admin';
        el.innerHTML = `
            ${isAdmin ? '<li class="nav-item"><a class="nav-link" href="/admin/dashboard.html"><i class="fas fa-cog me-1"></i>Admin</a></li>' : ''}
            <li class="nav-item"><a class="nav-link" href="/profile.html"><i class="fas fa-user me-1"></i>Hồ sơ</a></li>
            <li class="nav-item"><a class="nav-link" href="#" onclick="api.logout().then(()=>location.reload()); return false;"><i class="fas fa-sign-out-alt me-1"></i>Đăng xuất</a></li>
        `;
    } else {
        el.innerHTML = `
            <li class="nav-item"><a class="nav-link" href="/login.html"><i class="fas fa-sign-in-alt me-1"></i>Đăng nhập</a></li>
        `;
    }
}

/**
 * Cập nhật badge số lượng trên icon giỏ hàng trong navbar.
 * U-01: gọi sau mỗi lần thêm/xóa/sửa giỏ.
 * @param {number|null} count - số item, null = không hiện badge
 */
async function updateCartBadge(count = null) {
    // Nếu không truyền count, fetch từ cart-service
    if (count === null && api.isLoggedIn()) {
        try {
            const cart = await api.getCart();
            count = (cart?.items || []).reduce((s, i) => s + i.quantity, 0);
        } catch {
            count = 0;
        }
    }

    document.querySelectorAll('.cart-badge').forEach(el => {
        if (count && count > 0) {
            el.textContent = count > 99 ? '99+' : count;
            el.style.display = 'inline-flex';
        } else {
            el.style.display = 'none';
        }
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, showAlert, hideAlert, showLoading, hideLoading, formatPrice, formatDate, renderNavAuth };
}
