const CART_URL = 'http://localhost:8003';

let cartData = null;
let productCache = {};  // cache product info để hiển thị tên, ảnh, giá

// ── Helpers ───────────────────────────────────────────
function cartHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${api.getToken()}`,
    };
}

async function cartFetch(path, options = {}) {
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 10000);
    try {
        const res = await fetch(`${CART_URL}${path}`, { ...options, signal: ctrl.signal });
        clearTimeout(tid);
        return res;
    } catch (e) {
        clearTimeout(tid);
        if (e.name === 'AbortError') throw new Error('Yêu cầu quá thời gian, vui lòng thử lại');
        throw new Error('Không kết nối được đến máy chủ');
    }
}

async function fetchProductInfo(productId) {
    if (productCache[productId]) return productCache[productId];
    try {
        const res = await fetch(`${window.PRODUCT_API_URL}/products/${productId}/`);
        if (!res.ok) return null;
        const p = await res.json();
        productCache[productId] = p;
        return p;
    } catch {
        return null;
    }
}

// ── Load cart ─────────────────────────────────────────
async function loadCart() {
    if (!api.isLoggedIn()) {
        // U-08: chưa đăng nhập → chuyển tới login
        renderLoginRequired();
        return;
    }

    document.getElementById('cartBody').innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary"></div>
            <p class="text-muted mt-3">Đang tải giỏ hàng...</p>
        </div>`;

    try {
        const res = await cartFetch('/cart/', { headers: cartHeaders() });
        if (res.status === 401) { renderLoginRequired(); return; }
        if (!res.ok) throw new Error(`Lỗi ${res.status}`);
        cartData = await res.json();
        await renderCart();
        // U-01: cập nhật badge ngay sau khi load
        const total = (cartData?.items || []).reduce((s, i) => s + i.quantity, 0);
        updateCartBadge(total);
    } catch (e) {
        // U-09: lỗi service → thông báo thân thiện
        document.getElementById('cartBody').innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Không tải được giỏ hàng.</strong> ${e.message}
                <button class="btn btn-sm btn-outline-warning ms-3" onclick="loadCart()">Thử lại</button>
            </div>`;
        document.getElementById('cartSummary').innerHTML = '';
    }
}

// ── Render ────────────────────────────────────────────
async function renderCart() {
    const items = cartData?.items || [];

    if (items.length === 0) {
        // U-06: giỏ rỗng
        document.getElementById('cartBody').innerHTML = `
            <div class="text-center py-5">
                <div style="font-size:4rem">🛒</div>
                <h4 class="mt-3">Giỏ hàng trống</h4>
                <p class="text-muted">Hãy thêm sản phẩm vào giỏ để tiếp tục mua sắm.</p>
                <a href="products.html" class="btn btn-primary mt-2">
                    <i class="fas fa-arrow-left me-2"></i>Tiếp tục mua sắm
                </a>
            </div>`;
        document.getElementById('cartSummary').innerHTML = '';
        return;
    }

    // Fetch product info song song
    await Promise.all(items.map(item => fetchProductInfo(item.product_id)));

    let totalAmount = 0;
    const rows = items.map(item => {
        const p = productCache[item.product_id];
        const name = p?.name || `Sản phẩm #${item.product_id}`;
        const price = p ? parseFloat(p.price) : 0;
        const img = p?.image || 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=100';
        const stock = p?.stock ?? 999;
        const lineTotal = price * item.quantity;
        totalAmount += lineTotal;

        return `
        <tr id="row-${item.product_id}">
            <td>
                <div class="d-flex align-items-center gap-3">
                    <img src="${img}" style="width:56px;height:56px;object-fit:cover;border-radius:8px" alt="">
                    <div>
                        <div class="fw-500">${name}</div>
                        <div class="text-muted small">${formatPrice(price)}</div>
                    </div>
                </div>
            </td>
            <td style="width:160px">
                <div class="input-group input-group-sm">
                    <button class="btn btn-outline-secondary" onclick="changeQty(${item.product_id}, ${item.quantity - 1}, ${stock})" ${item.quantity <= 1 ? 'disabled' : ''}>−</button>
                    <input type="number" class="form-control text-center qty-input"
                        value="${item.quantity}" min="1" max="${stock}"
                        onchange="changeQty(${item.product_id}, parseInt(this.value)||1, ${stock})"
                        style="width:50px">
                    <button class="btn btn-outline-secondary" onclick="changeQty(${item.product_id}, ${item.quantity + 1}, ${stock})" ${item.quantity >= stock ? 'disabled' : ''}>+</button>
                </div>
                ${stock < 5 ? `<div class="text-danger small mt-1">Còn ${stock} sp</div>` : ''}
            </td>
            <td class="fw-bold text-primary" id="line-${item.product_id}">${formatPrice(lineTotal)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="removeItem(${item.product_id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>`;
    });

    document.getElementById('cartBody').innerHTML = `
        <table class="table align-middle">
            <thead class="table-light">
                <tr><th>Sản phẩm</th><th>Số lượng</th><th>Thành tiền</th><th></th></tr>
            </thead>
            <tbody>${rows.join('')}</tbody>
        </table>`;

    // Summary
    document.getElementById('cartSummary').innerHTML = `
        <div class="card shadow-sm">
            <div class="card-body">
                <h5 class="mb-3">Tóm tắt đơn hàng</h5>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">${items.length} sản phẩm</span>
                    <strong id="totalDisplay">${formatPrice(totalAmount)}</strong>
                </div>
                <hr>
                <div class="d-flex justify-content-between mb-3">
                    <strong>Tổng cộng</strong>
                    <strong class="text-primary fs-5" id="grandTotal">${formatPrice(totalAmount)}</strong>
                </div>
                <a href="checkout.html" class="btn btn-primary w-100 mb-2">
                    <i class="fas fa-credit-card me-2"></i>Thanh toán
                </a>
                <a href="products.html" class="btn btn-outline-secondary w-100">
                    <i class="fas fa-arrow-left me-2"></i>Tiếp tục mua sắm
                </a>
            </div>
        </div>`;
}

// ── Actions ───────────────────────────────────────────
async function changeQty(productId, newQty, stock) {
    // U-03: chặn giá trị không hợp lệ ở UI
    if (newQty < 1) {
        showAlert('Số lượng tối thiểu là 1', 'warning');
        await renderCart();
        return;
    }
    // U-02: chặn vượt tồn kho ở UI trước khi gọi API
    if (newQty > stock) {
        showAlert(`Chỉ còn ${stock} sản phẩm trong kho`, 'warning');
        await renderCart();
        return;
    }

    try {
        const res = await cartFetch('/cart/update', {
            method: 'PATCH',
            headers: cartHeaders(),
            body: JSON.stringify({ product_id: productId, quantity: newQty }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Lỗi ${res.status}`);
        }
        cartData = await res.json();
        await renderCart();  // U-04: cập nhật tổng tiền ngay
        const total = (cartData?.items || []).reduce((s, i) => s + i.quantity, 0);
        updateCartBadge(total);
    } catch (e) {
        showAlert(e.message, 'danger');
        await renderCart();
    }
}

async function removeItem(productId) {
    try {
        const res = await cartFetch('/cart/remove', {
            method: 'DELETE',
            headers: cartHeaders(),
            body: JSON.stringify({ product_id: productId }),
        });
        if (!res.ok) throw new Error(`Lỗi ${res.status}`);
        cartData = await res.json();
        await renderCart();  // U-05: cập nhật ngay sau khi xóa
        const total = (cartData?.items || []).reduce((s, i) => s + i.quantity, 0);
        updateCartBadge(total);
    } catch (e) {
        showAlert(e.message, 'danger');
    }
}

// ── Hàm thêm vào giỏ gọi từ trang products ───────────
async function addToCartFromProduct(productId, quantity = 1) {
    if (!api.isLoggedIn()) {
        // U-08: chưa đăng nhập → redirect
        window.location.href = '/login.html';
        return false;
    }
    const res = await cartFetch('/cart/add', {
        method: 'POST',
        headers: cartHeaders(),
        body: JSON.stringify({ product_id: productId, quantity }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Lỗi ${res.status}`);
    }
    return res.json();
}

// ── Login required screen ─────────────────────────────
function renderLoginRequired() {
    document.getElementById('cartBody').innerHTML = `
        <div class="text-center py-5">
            <div style="font-size:4rem">🔐</div>
            <h4 class="mt-3">Bạn chưa đăng nhập</h4>
            <p class="text-muted">Đăng nhập để xem và quản lý giỏ hàng của bạn.</p>
            <a href="/login.html" class="btn btn-primary mt-2">
                <i class="fas fa-sign-in-alt me-2"></i>Đăng nhập
            </a>
        </div>`;
    document.getElementById('cartSummary').innerHTML = '';
}

// ── Init ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadCart);
