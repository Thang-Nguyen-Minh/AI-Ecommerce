const ORDER_URL = 'http://localhost:8004';
const PRODUCT_URL = window.PRODUCT_API_URL || 'http://localhost:8002';

const STATUS_LABEL = {
    PENDING:        { text: 'Chờ thanh toán', cls: 'warning',   icon: 'fa-clock'          },
    PAID:           { text: 'Đã thanh toán',  cls: 'info',      icon: 'fa-check-circle'   },
    SHIPPED:        { text: 'Đang giao',       cls: 'primary',   icon: 'fa-truck'          },
    DELIVERED:      { text: 'Đã giao',         cls: 'success',   icon: 'fa-check-double'   },
    PAYMENT_FAILED: { text: 'Thanh toán thất bại', cls: 'danger', icon: 'fa-times-circle' },
    CANCELLED:      { text: 'Đã hủy',          cls: 'secondary', icon: 'fa-ban'            },
};

async function loadOrderDetail() {
    if (!api.isLoggedIn()) { window.location.href = '/login.html'; return; }
    const id = new URLSearchParams(window.location.search).get('id');
    if (!id) { document.getElementById('detail').innerHTML = '<div class="alert alert-danger">Thiếu order ID</div>'; return; }

    try {
        const res = await fetch(`${ORDER_URL}/orders/${id}`, {
            headers: { Authorization: `Bearer ${api.getToken()}` },
        });
        if (res.status === 401) { window.location.href = '/login.html'; return; }
        if (res.status === 403) { document.getElementById('detail').innerHTML = '<div class="alert alert-danger">Bạn không có quyền xem đơn này.</div>'; return; }
        if (res.status === 404) { document.getElementById('detail').innerHTML = '<div class="alert alert-warning">Không tìm thấy đơn hàng.</div>'; return; }
        const order = await res.json();
        render(order);
    } catch (e) {
        document.getElementById('detail').innerHTML = `<div class="alert alert-warning">${e.message}</div>`;
    }
}

async function render(order) {
    const s = STATUS_LABEL[order.status] || { text: order.status, cls: 'secondary', icon: 'fa-question' };

    // Fetch product names
    const names = {};
    await Promise.all(order.items.map(async item => {
        try {
            const r = await fetch(`${PRODUCT_URL}/products/${item.product_id}/`);
            if (r.ok) { const p = await r.json(); names[item.product_id] = p.name; }
        } catch {}
    }));

    const itemRows = order.items.map(item => `
        <tr>
            <td>${names[item.product_id] || `Sản phẩm #${item.product_id}`}</td>
            <td class="text-center">${item.quantity}</td>
            <td class="text-end">${formatPrice(item.unit_price)}</td>
            <td class="text-end fw-bold">${formatPrice(parseFloat(item.unit_price) * item.quantity)}</td>
        </tr>`).join('');

    document.getElementById('detail').innerHTML = `
        <div class="card shadow-sm mb-4">
            <div class="card-header d-flex justify-content-between align-items-center">
                <strong>Đơn hàng #${order.id}</strong>
                <span class="badge bg-${s.cls} fs-6"><i class="fas ${s.icon} me-1"></i>${s.text}</span>
            </div>
            <div class="card-body">
                ${order.payment_error ? `<div class="alert alert-danger py-2"><i class="fas fa-exclamation-triangle me-1"></i>${order.payment_error}</div>` : ''}
                <div class="row gy-2 mb-3">
                    <div class="col-sm-6">
                        <div class="text-muted small">Địa chỉ giao hàng</div>
                        <div>${order.shipping_address}</div>
                    </div>
                    <div class="col-sm-6">
                        <div class="text-muted small">Ngày đặt</div>
                        <div>${formatDate(order.created_at)}</div>
                    </div>
                </div>
                <table class="table table-sm">
                    <thead class="table-light">
                        <tr><th>Sản phẩm</th><th class="text-center">SL</th><th class="text-end">Đơn giá</th><th class="text-end">Thành tiền</th></tr>
                    </thead>
                    <tbody>${itemRows}</tbody>
                    <tfoot>
                        <tr class="fw-bold">
                            <td colspan="3" class="text-end">Tổng cộng</td>
                            <td class="text-end text-primary fs-5">${formatPrice(order.total_price)}</td>
                        </tr>
                    </tfoot>
                </table>
                <div class="mt-3 d-flex gap-2">
                    <a href="orders.html" class="btn btn-outline-secondary btn-sm">← Danh sách đơn</a>
                    ${['PENDING','PAYMENT_FAILED'].includes(order.status) ? `<a href="checkout.html" class="btn btn-primary btn-sm">Đặt lại</a>` : ''}
                </div>
            </div>
        </div>`;
}

document.addEventListener('DOMContentLoaded', loadOrderDetail);
