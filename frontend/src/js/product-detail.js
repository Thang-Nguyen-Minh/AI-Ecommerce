const productDetailEl = document.getElementById('productDetail');

function escapeHtml(value) {
    const element = document.createElement('div');
    element.textContent = String(value ?? '');
    return element.innerHTML;
}

function getProductIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

function getProductImage(product) {
    return product.image || 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=1200';
}

function getCategoryName(product) {
    return product.category_name || product.category_detail?.name || product.category?.name || 'Chưa phân loại';
}

function renderRating(rating) {
    const value = Number(rating || 0);
    const fullStars = Math.round(value);
    let stars = '';

    for (let i = 1; i <= 5; i += 1) {
        stars += `<i class="${i <= fullStars ? 'fas' : 'far'} fa-star text-warning"></i>`;
    }

    return `<span>${stars} <span class="text-muted ms-2">${value.toFixed(1)}</span></span>`;
}

function renderTypeDetail(product) {
    const b = product.book_detail;
    const e = product.electronics_detail;
    const f = product.fashion_detail;
    if (b) return `
        <dt class="col-sm-4">Tác giả</dt><dd class="col-sm-8">${escapeHtml(b.author || '—')}</dd>
        ${b.publisher ? `<dt class="col-sm-4">Nhà xuất bản</dt><dd class="col-sm-8">${escapeHtml(b.publisher)}</dd>` : ''}
        ${b.isbn ? `<dt class="col-sm-4">ISBN</dt><dd class="col-sm-8">${escapeHtml(b.isbn)}</dd>` : ''}
        ${b.pages ? `<dt class="col-sm-4">Số trang</dt><dd class="col-sm-8">${b.pages}</dd>` : ''}
        ${b.language ? `<dt class="col-sm-4">Ngôn ngữ</dt><dd class="col-sm-8">${escapeHtml(b.language)}</dd>` : ''}
    `;
    if (e) return `
        <dt class="col-sm-4">Thương hiệu</dt><dd class="col-sm-8">${escapeHtml(e.brand || '—')}</dd>
        ${e.model ? `<dt class="col-sm-4">Model</dt><dd class="col-sm-8">${escapeHtml(e.model)}</dd>` : ''}
        <dt class="col-sm-4">Bảo hành</dt><dd class="col-sm-8">${e.warranty_months || 0} tháng</dd>
    `;
    if (f) return `
        <dt class="col-sm-4">Kích cỡ</dt><dd class="col-sm-8">${escapeHtml(f.size || '—')}</dd>
        <dt class="col-sm-4">Màu sắc</dt><dd class="col-sm-8">${escapeHtml(f.color || '—')}</dd>
        ${f.material ? `<dt class="col-sm-4">Chất liệu</dt><dd class="col-sm-8">${escapeHtml(f.material)}</dd>` : ''}
        ${f.brand ? `<dt class="col-sm-4">Thương hiệu</dt><dd class="col-sm-8">${escapeHtml(f.brand)}</dd>` : ''}
    `;
    return '';
}

function renderProductDetail(product) {
    const price = formatPrice(product.price || 0);
    const compareAtPrice = product.compare_at_price ? formatPrice(product.compare_at_price) : '';
    const stockBadge = product.in_stock
        ? `<span class="badge bg-success fs-6">Còn hàng (${product.stock ?? 0})</span>`
        : '<span class="badge bg-secondary fs-6">Hết hàng</span>';

    productDetailEl.innerHTML = `
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm">
                <img src="${escapeHtml(getProductImage(product))}" class="card-img-top" alt="${escapeHtml(product.name)}" style="max-height: 520px; object-fit: cover;">
            </div>
        </div>

        <div class="col-lg-6">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start gap-3 mb-3">
                        <span class="badge bg-light text-dark border">${escapeHtml(getCategoryName(product))}</span>
                        ${stockBadge}
                    </div>

                    <h1 class="h2 fw-bold mb-3">${escapeHtml(product.name)}</h1>

                    <div class="mb-3">
                        ${renderRating(product.rating)}
                        <span class="text-muted ms-3">Đã bán ${product.sold_count || 0}</span>
                    </div>

                    <div class="mb-4">
                        <strong class="text-primary display-6">${price}</strong>
                        ${compareAtPrice ? `<del class="text-muted fs-5 ms-3">${compareAtPrice}</del>` : ''}
                        ${product.discount_percent ? `<span class="badge bg-danger ms-2">-${product.discount_percent}%</span>` : ''}
                    </div>

                    <p class="lead text-muted">${escapeHtml(product.short_description || product.description || 'Không có mô tả.')}</p>

                    <hr>

                    <dl class="row mb-4">
                        <dt class="col-sm-4">SKU</dt>
                        <dd class="col-sm-8">${escapeHtml(product.sku || '—')}</dd>

                        <dt class="col-sm-4">Loại sản phẩm</dt>
                        <dd class="col-sm-8">${escapeHtml(product.product_type || '—')}</dd>

                        <dt class="col-sm-4">Danh mục</dt>
                        <dd class="col-sm-8">${escapeHtml(getCategoryName(product))}</dd>

                        ${renderTypeDetail(product)}
                    </dl>

                    <div class="d-grid gap-2">
                        <button class="btn btn-primary-custom btn-lg text-white" onclick="handleAddToCart(${product.id})" ${product.in_stock ? '' : 'disabled'}>
                            <i class="fas fa-cart-plus me-2"></i>Thêm vào giỏ hàng
                        </button>
                        <a href="products.html" class="btn btn-outline-secondary">
                            <i class="fas fa-arrow-left me-2"></i>Quay lại danh sách
                        </a>
                    </div>
                </div>
            </div>
        </div>

        ${product.description ? `
            <div class="col-12">
                <div class="card border-0 shadow-sm">
                    <div class="card-body p-4">
                        <h2 class="h4 mb-3">Mô tả chi tiết</h2>
                        <p class="mb-0">${escapeHtml(product.description)}</p>
                    </div>
                </div>
            </div>
        ` : ''}
    `;
}

async function handleAddToCart(productId) {
    if (!api.isLoggedIn()) {
        showAlert('Bạn cần đăng nhập trước khi thêm sản phẩm vào giỏ hàng.', 'warning');
        return;
    }

    try {
        await api.addToCart(productId, 1);
        showAlert('Đã thêm sản phẩm vào giỏ hàng.', 'success');
    } catch (error) {
        showAlert(`Không thêm được vào giỏ hàng: ${error.message}`, 'danger');
    }
}

async function loadProductDetail() {
    const productId = getProductIdFromUrl();

    if (!productId) {
        productDetailEl.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    Không tìm thấy id sản phẩm trên URL.
                </div>
            </div>
        `;
        return;
    }

    try {
        const endpoint = `${window.PRODUCT_API_URL}/products/${encodeURIComponent(productId)}/`;
        const product = await fetch(endpoint).then((response) => {
            if (!response.ok) {
                throw new Error(`GET ${endpoint} failed: ${response.status}`);
            }
            return response.json();
        });

        renderProductDetail(product);
        api.aiTrackEvent(product.id, 'view');  // ghi hành vi xem → knowledge graph
    } catch (error) {
        productDetailEl.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <strong>Không tải được chi tiết sản phẩm.</strong>
                    <div>${escapeHtml(error.message)}</div>
                    <hr>
                    <div class="small">Hãy kiểm tra endpoint <code>http://localhost:8002/products/{id}/</code> hoạt động.</div>
                </div>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', loadProductDetail);