let currentPage = 1;
let hasNextPage = false;
let hasPreviousPage = false;
let searchTimer = null;

const productListEl = document.getElementById('productList');
const searchInputEl = document.getElementById('searchInput');
const categoryFilterEl = document.getElementById('categoryFilter');
const typeFilterEl = document.getElementById('typeFilter');
const reloadBtnEl = document.getElementById('reloadBtn');
const prevPageBtnEl = document.getElementById('prevPageBtn');
const nextPageBtnEl = document.getElementById('nextPageBtn');
const pageInfoEl = document.getElementById('pageInfo');
const seedDemoBtnEl = document.getElementById('seedDemoBtn');
const totalProductsEl = document.getElementById('totalProducts');
const totalCategoriesEl = document.getElementById('totalCategories');

function escapeHtml(value) {
    const element = document.createElement('div');
    element.textContent = String(value ?? '');
    return element.innerHTML;
}

function normalizeListResponse(data) {
    if (Array.isArray(data)) {
        return {
            results: data,
            count: data.length,
            next: null,
            previous: null,
        };
    }

    return {
        results: data?.results || [],
        count: data?.count || 0,
        next: data?.next || null,
        previous: data?.previous || null,
    };
}

function getProductImage(product) {
    return product.image || 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900';
}

function getCategoryName(product) {
    return product.category_name || product.category_detail?.name || 'Chưa phân loại';
}

function renderRating(rating) {
    const value = Number(rating || 0);
    const fullStars = Math.round(value);
    let stars = '';

    for (let i = 1; i <= 5; i += 1) {
        stars += `<i class="${i <= fullStars ? 'fas' : 'far'} fa-star text-warning"></i>`;
    }

    return `<span class="small">${stars} <span class="text-muted ms-1">${value.toFixed(1)}</span></span>`;
}

function renderProductCard(product) {
    const price = formatPrice(product.price || 0);
    const compareAtPrice = product.compare_at_price ? formatPrice(product.compare_at_price) : '';
    const discount = product.discount_percent ? `<span class="badge bg-danger">-${product.discount_percent}%</span>` : '';
    const stockBadge = product.in_stock
        ? `<span class="badge bg-success">Còn ${product.stock}</span>`
        : '<span class="badge bg-secondary">Hết hàng</span>';

    return `
        <div class="col-sm-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm product-card">
                <div class="position-relative">
                    <img src="${escapeHtml(getProductImage(product))}" class="card-img-top" alt="${escapeHtml(product.name)}" style="height: 220px; object-fit: cover;">
                    <div class="position-absolute top-0 start-0 m-2 d-flex gap-2">
                        ${discount}
                        ${product.is_featured ? '<span class="badge bg-primary">Nổi bật</span>' : ''}
                    </div>
                </div>
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                        <span class="badge bg-light text-dark border">${escapeHtml(getCategoryName(product))}</span>
                        ${stockBadge}
                    </div>
                    <h5 class="card-title">${escapeHtml(product.name)}</h5>
                    <p class="card-text text-muted small flex-grow-1">${escapeHtml(product.short_description || product.description || 'Không có mô tả.')}</p>
                    <div class="mb-2">${renderRating(product.rating)} <span class="small text-muted ms-2">Đã bán ${product.sold_count || 0}</span></div>
                    <div class="mb-3">
                        <strong class="text-primary fs-5">${price}</strong>
                        ${compareAtPrice ? `<del class="text-muted small ms-2">${compareAtPrice}</del>` : ''}
                    </div>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary-custom text-white" onclick="handleAddToCart(${product.id})" ${product.in_stock ? '' : 'disabled'}>
                            <i class="fas fa-cart-plus me-2"></i>Thêm vào giỏ
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="viewProductDetail(${product.id})">
                            <i class="fas fa-eye me-1"></i>Xem chi tiết
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderProducts(products) {
    if (!products.length) {
        productListEl.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info text-center py-5">
                    <i class="fas fa-box-open fa-3x mb-3"></i>
                    <h5>Chưa có sản phẩm phù hợp</h5>
                    <p class="mb-0">Bạn có thể bấm "Tạo dữ liệu demo" để thêm sản phẩm mẫu.</p>
                </div>
            </div>
        `;
        return;
    }

    productListEl.innerHTML = products.map(renderProductCard).join('');
}

function setLoading(isLoading) {
    if (isLoading) {
        productListEl.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="text-muted mt-3">Đang tải sản phẩm...</p>
            </div>
        `;
    }

    reloadBtnEl.disabled = isLoading;
    prevPageBtnEl.disabled = isLoading || !hasPreviousPage;
    nextPageBtnEl.disabled = isLoading || !hasNextPage;
}

function buildProductQuery(page = 1) {
    const params = new URLSearchParams({ page });

    const search = searchInputEl.value.trim();
    const category = categoryFilterEl.value;
    const productType = typeFilterEl.value;

    if (search) params.set('search', search);
    if (category) params.set('category', category);
    if (productType) params.set('product_type', productType);

    return params.toString();
}

async function loadStats() {
    try {
        const stats = await fetch(`${window.PRODUCT_API_URL}/products/stats/`).then((response) => {
            if (!response.ok) {
                throw new Error(`GET ${window.PRODUCT_API_URL}/products/stats/ failed: ${response.status}`);
            }
            return response.json();
        });
        totalProductsEl.textContent = stats.total ?? '—';
        totalCategoriesEl.textContent = stats.categories ?? '—';
    } catch (error) {
        console.warn('Không tải được thống kê sản phẩm:', error);
    }
}

async function loadCategories() {
    try {
        const data = await fetch(`${window.PRODUCT_API_URL}/categories/`).then((response) => {
            if (!response.ok) {
                throw new Error(`GET ${window.PRODUCT_API_URL}/categories/ failed: ${response.status}`);
            }
            return response.json();
        });
        const normalized = normalizeListResponse(data);
        const currentValue = categoryFilterEl.value;

        categoryFilterEl.innerHTML = '<option value="">Tất cả danh mục</option>';
        normalized.results.forEach((category) => {
            categoryFilterEl.insertAdjacentHTML(
                'beforeend',
                `<option value="${category.id}">${escapeHtml(category.name)} (${category.product_count || 0})</option>`,
            );
        });

        categoryFilterEl.value = currentValue;
    } catch (error) {
        console.warn('Không tải được danh mục:', error);
    }
}

async function loadProducts(page = 1) {
    // Load products from public endpoint; no auth required for list view.
    currentPage = page;
    setLoading(true);

    try {
        const data = await fetch(`${window.PRODUCT_API_URL}/products/?${buildProductQuery(page)}`).then((response) => {
            if (!response.ok) {
                throw new Error(`GET ${window.PRODUCT_API_URL}/products/ failed: ${response.status}`);
            }
            return response.json();
        });
        const normalized = normalizeListResponse(data);

        hasNextPage = Boolean(normalized.next);
        hasPreviousPage = Boolean(normalized.previous);

        renderProducts(normalized.results || []);
        pageInfoEl.textContent = `Trang ${currentPage} • ${normalized.count} sản phẩm`;

        prevPageBtnEl.disabled = !hasPreviousPage;
        nextPageBtnEl.disabled = !hasNextPage;
    } catch (error) {
        productListEl.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <strong>Không tải được sản phẩm.</strong>
                    <div>${escapeHtml(error.message)}</div>
                    <hr>
                    <div class="small">Hãy kiểm tra Product Service đang chạy và endpoint <code>/products/</code> hoạt động.</div>
                </div>
            </div>
        `;
    } finally {
        setLoading(false);
    }
}

async function handleAddToCart(productId) {
    // U-08: chưa đăng nhập → chuyển đến trang đăng nhập
    if (!api.isLoggedIn()) {
        window.location.href = '/login.html';
        return;
    }

    try {
        await api.addToCart(productId, 1);
        showAlert('Đã thêm sản phẩm vào giỏ hàng!', 'success');
        updateCartBadge();  // U-01: tăng số badge
    } catch (error) {
        showAlert(`Không thêm được vào giỏ hàng: ${error.message}`, 'danger');
    }
}

function viewProductDetail(productId) {
    window.location.href = `product-detail.html?id=${productId}`;
}

async function seedDemoProducts() {
    seedDemoBtnEl.disabled = true;
    seedDemoBtnEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang tạo...';

    try {
        const result = await fetch(`${window.PRODUCT_API_URL}/products/seed-demo/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        }).then((response) => {
            if (!response.ok) {
                throw new Error(`POST ${window.PRODUCT_API_URL}/products/seed-demo/ failed: ${response.status}`);
            }
            return response.json();
        });
        showAlert(result.message || 'Đã tạo dữ liệu demo.', 'success');
        await loadCategories();
        await loadStats();
        await loadProducts(1);
    } catch (error) {
        showAlert(`Không tạo được demo: ${error.message}`, 'danger');
    } finally {
        seedDemoBtnEl.disabled = false;
        seedDemoBtnEl.innerHTML = '<i class="fas fa-database me-1"></i>Tạo dữ liệu demo';
    }
}

searchInputEl.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadProducts(1), 350);
});

categoryFilterEl.addEventListener('change', () => loadProducts(1));
typeFilterEl.addEventListener('change', () => loadProducts(1));
reloadBtnEl.addEventListener('click', () => {
    loadCategories();
    loadStats();
    loadProducts(currentPage);
});
prevPageBtnEl.addEventListener('click', () => {
    if (hasPreviousPage && currentPage > 1) loadProducts(currentPage - 1);
});
nextPageBtnEl.addEventListener('click', () => {
    if (hasNextPage) loadProducts(currentPage + 1);
});
seedDemoBtnEl.addEventListener('click', seedDemoProducts);

document.addEventListener('DOMContentLoaded', async () => {
    await loadCategories();
    await loadStats();
    await loadProducts(1);
    updateCartBadge();  // U-01: hiện badge ngay khi vào trang
});