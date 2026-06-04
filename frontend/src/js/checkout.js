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

    // payment U-04: khóa nút, hiện trạng thái "đang xử lý"
    const btn = document.getElementById('btnPlace');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang xử lý thanh toán...';
    document.getElementById('alertBox').className = 'alert d-none';

    const body = { shipping_address: address };
    // Demo nhánh lỗi (payment U-02): gửi cờ sandbox simulate=fail
    if (document.getElementById('simulateFail')?.checked) body.simulate = 'fail';

    try {
        // U-04: timeout phía client để không treo vô hạn nếu xử lý lâu
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 15000);
        let res;
        try {
            res = await fetch(`${ORDER_URL}/orders/`, {
                method: 'POST',
                headers: authHeader(),
                body: JSON.stringify(body),
                signal: ctrl.signal,
            });
        } finally {
            clearTimeout(tid);
        }
        const data = await res.json();
        const order = data.id ? data : data.order;  // 503 trả {error, order:{...}}

        // U-07: payment-service sập (503) → báo thân thiện, giỏ KHÔNG mất
        if (res.status === 503) {
            showAlert(`Hệ thống thanh toán đang bận, vui lòng thử lại sau ít phút. (Đơn #${order?.id || '—'} chưa thanh toán)`, 'warning');
            return;
        }
        if (!res.ok && !order) {
            throw new Error(data.error || `Lỗi ${res.status}`);
        }

        // order U-04 / payment U-01: thành công → trang xác nhận đơn
        if (['PAID', 'SHIPPED', 'DELIVERED'].includes(order.status)) {
            window.location.href = `order-detail.html?id=${order.id}&new=1`;
        } else {
            // order U-05 / payment U-02: thất bại → báo lỗi rõ, KHÔNG hiện "đang giao", có lối thử lại
            showAlert(
                `<i class="fas fa-times-circle me-1"></i><strong>Thanh toán không thành công.</strong> ` +
                `Đơn #${order.id} chưa được thanh toán. ` +
                `<a href="order-detail.html?id=${order.id}" class="alert-link">Xem đơn</a> hoặc thử lại bên dưới.`,
                'danger',
            );
        }
    } catch (err) {
        // U-07: lỗi mạng/timeout giữa chừng → không mất giỏ
        const msg = err.name === 'AbortError' ? 'Yêu cầu quá thời gian, vui lòng thử lại' : err.message;
        showAlert(msg, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check me-2"></i>Xác nhận đặt hàng';
    }
}

function showAlert(html, type) {
    const el = document.getElementById('alertBox');
    el.className = `alert alert-${type}`;
    el.innerHTML = html;
}

// #1: điền sẵn địa chỉ mặc định của khách (vẫn cho sửa)
async function prefillAddress() {
    try {
        const profile = await api.getProfile();
        const addrs = profile.addresses || [];
        const def = addrs.find(a => a.is_default) || addrs[0];
        if (def) {
            const parts = [def.street, def.ward, def.district, def.city].filter(Boolean);
            const box = document.getElementById('shippingAddress');
            if (box && !box.value.trim()) box.value = parts.join(', ');
        }
    } catch { /* không có địa chỉ cũng không sao */ }
}

document.getElementById('checkoutForm').addEventListener('submit', placeOrder);
document.addEventListener('DOMContentLoaded', () => {
    loadCart();
    prefillAddress();
});
