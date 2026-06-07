const ORDER_URL = 'http://localhost:8004';

function orderHeaders() {
    return { 'Authorization': `Bearer ${api.getToken()}` };
}

const STATUS_LABEL = {
    PENDING:        { text: 'Chờ thanh toán', cls: 'warning'   },
    PAID:           { text: 'Đã thanh toán',  cls: 'info'      },
    SHIPPED:        { text: 'Đang giao',       cls: 'primary'   },
    DELIVERED:      { text: 'Đã giao',         cls: 'success'   },
    PAYMENT_FAILED: { text: 'TT thất bại',     cls: 'danger'    },
    CANCELLED:      { text: 'Đã hủy',          cls: 'secondary' },
};

function statusBadge(s) {
    const { text, cls } = STATUS_LABEL[s] || { text: s, cls: 'secondary' };
    return `<span class="badge bg-${cls}">${text}</span>`;
}

async function loadOrders() {
    if (!api.isLoggedIn()) { window.location.href = '/login.html'; return; }

    const el = document.getElementById('orderList');
    el.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';

    try {
        const res = await fetch(`${ORDER_URL}/orders/`, { headers: orderHeaders() });
        if (res.status === 401) { window.location.href = '/login.html'; return; }
        const orders = await res.json();

        if (!orders.length) {
            el.innerHTML = `
                <div class="text-center py-5">
                    <div style="font-size:3rem">📋</div>
                    <h5 class="mt-3">Chưa có đơn hàng nào</h5>
                    <a href="products.html" class="btn btn-primary mt-2">Mua sắm ngay</a>
                </div>`;
            return;
        }

        el.innerHTML = orders.map(o => `
            <div class="card mb-3 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>#${o.id}</strong>
                            <span class="ms-3">${statusBadge(o.status)}</span>
                            ${o.payment_error ? `<div class="text-danger small mt-1">${o.payment_error}</div>` : ''}
                        </div>
                        <div class="text-end">
                            <div class="fw-bold text-primary">${formatPrice(o.total_price)}</div>
                            <div class="text-muted small">${formatDate(o.created_at)}</div>
                        </div>
                    </div>
                    <div class="text-muted small mt-2">
                        ${o.recipient_name ? `<i class="fas fa-user me-1"></i>${o.recipient_name}` : ''}
                        ${o.phone ? `&nbsp;·&nbsp;<i class="fas fa-phone me-1"></i>${o.phone}` : ''}
                        ${(o.recipient_name || o.phone) ? '<br>' : ''}
                        <i class="fas fa-map-pin me-1"></i>${o.shipping_address}
                        &nbsp;·&nbsp; ${o.items.length} sản phẩm
                    </div>
                    <div class="mt-2">
                        <a href="order-detail.html?id=${o.id}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye me-1"></i>Chi tiết
                        </a>
                    </div>
                </div>
            </div>`).join('');
    } catch (e) {
        el.innerHTML = `<div class="alert alert-warning">${e.message} <button class="btn btn-sm btn-warning ms-2" onclick="loadOrders()">Thử lại</button></div>`;
    }
}

document.addEventListener('DOMContentLoaded', loadOrders);
