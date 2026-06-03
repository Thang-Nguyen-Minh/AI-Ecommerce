const ORDER_URL  = 'http://localhost:8004';
const CART_URL   = 'http://localhost:8003';
const PROD_URL   = window.PRODUCT_API_URL || 'http://localhost:8002';

let cartItems = [];
let productCache = {};

function authHeader() {
    return { Authorization: `Bearer ${api.getToken()}`, 'Content-Type': 'application/json' };
}

async function fetchProduct(id) {
    if (productCache[id]) return productCache[id];
    const r = await fetch(`${PROD_URL}/products/${id}/`);
    if (!r.ok) return null;
    productCache[id] = await r.json();
    return productCache[id];
}

async function loadCart() {
    if (!api.isLoggedIn()) { window.location.href = '/login.html'; return; }

    try {
        const r = await fetch(`${CART_URL}/cart/`, { headers: { Authorization: `Bearer ${api.getToken()}` } });
        if (!r.ok) throw new Error(`cart-service lỗi ${r.status}`);
        const cart = await r.json();
        cartItems = cart.items || [];

        // U-02: giỏ trống → disable nút đặt
        const btnPlace = document.getElementById('btnPlace');
        if (!cartItems.length) {
            document.getElementById('cartPreview').innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="fas fa-shopping-cart fa-2x mb-2"></i>
                    <p>Giỏ hàng trống</p>
                    <a href="products.html" class="btn btn-sm btn-primary">Thêm sản phẩm</a>
                </div>`;
            btnPlace.disabled = true;
            btnPlace.textContent = 'Giỏ hàng trống';
            document.getElementById('totalBox').innerHTML = '';
            return;
        }

        await Promise.all(cartItems.map(i => fetchProduct(i.product_id)));

        let total = 0;
        const rows = cartItems.map(item => {
            const p = productCache[item.product_id];
            const price = p ? parseFloat(p.price) : 0;
            const line = price * item.quantity;
            total += line;
            return `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div class="small">
                    <div class="fw-500">${p?.name || '#' + item.product_id}</div>
                    <div class="text-muted">${item.quantity} × ${formatPrice(price)}</div>
                </div>
                <div class="fw-bold">${formatPrice(line)}</div>
            </div>`;
        });

        document.getElementById('cartPreview').innerHTML = rows.join('');
        // U-03: tổng tiền tính đúng Σ thành tiền
        document.getElementById('totalBox').innerHTML = `
            <div class="d-flex justify-content-between fw-bold mt-2 pt-2 border-top">
                <span>Tổng cộng</span>
                <span class="text-primary">${formatPrice(total)}</span>
            </div>`;
        btnPlace.disabled = false;
        btnPlace.innerHTML = '<i class="fas fa-check me-2"></i>Xác nhận đặt hàng';
    } catch (e) {
        // U-07: service lỗi → thông báo thân thiện
        document.getElementById('cartPreview').innerHTML = `
            <div class="alert alert-warning py-2">
                <i class="fas fa-exclamation-triangle me-1"></i>${e.message}
                <button class="btn btn-sm btn-warning ms-2" onclick="loadCart()">Thử lại</button>
            </div>`;
    }
}

async function placeOrder(e) {
    e.preventDefault();
    const address = document.getElementById('shippingAddress').value.trim();
    if (!address) { showAlert('Vui lòng nhập địa chỉ giao hàng', 'warning'); return; }

    showLoading('btnPlace');
    document.getElementById('alertBox').className = 'alert d-none';

    try {
        const res = await fetch(`${ORDER_URL}/orders/`, {
            method: 'POST',
            headers: authHeader(),
            body: JSON.stringify({ shipping_address: address }),
        });
        const order = await res.json();

        if (!res.ok && !order.id) {
            throw new Error(order.error || `Lỗi ${res.status}`);
        }

        // U-04: thanh toán thành công → chuyển sang trang xác nhận
        // U-05: thất bại → báo lỗi, có lối thử lại
        if (['PAID', 'SHIPPED', 'DELIVERED'].includes(order.status)) {
            window.location.href = `order-detail.html?id=${order.id}&new=1`;
        } else {
            const errMsg = order.payment_error || 'Đặt hàng thất bại';
            showAlert(`${errMsg} — <a href="order-detail.html?id=${order.id}">Xem đơn #${order.id}</a>`, 'danger');
        }
    } catch (e) {
        // U-07: service lỗi giữa chừng → không mất giỏ
        showAlert(e.message, 'danger');
    } finally {
        hideLoading('btnPlace', '<i class="fas fa-check me-2"></i>Xác nhận đặt hàng');
    }
}

function showAlert(html, type) {
    const el = document.getElementById('alertBox');
    el.className = `alert alert-${type}`;
    el.innerHTML = html;
}

document.getElementById('checkoutForm').addEventListener('submit', placeOrder);
document.addEventListener('DOMContentLoaded', loadCart);
