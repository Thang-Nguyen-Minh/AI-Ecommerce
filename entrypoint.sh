#!/bin/sh
# ═══════════════════════════════════════════════════
#  entrypoint.sh — dùng chung cho tất cả Django service
#  Đặt tại: ecom-final/entrypoint.sh
# ═══════════════════════════════════════════════════
set -e

echo ""
echo "╔══════════════════════════════════╗"
echo "║  Starting: $SERVICE_NAME"
echo "╚══════════════════════════════════╝"

# ── Chờ Database sẵn sàng ────────────────────────
echo "⏳ Đang chờ DB ($DB_HOST:$DB_PORT)..."
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    printf '.'
    sleep 2
done
echo ""
echo "✅ DB sẵn sàng!"

# ── Chờ Redis (nếu cần) ──────────────────────────
if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed 's|redis://||' | cut -d: -f1)
    echo "⏳ Đang chờ Redis ($REDIS_HOST)..."
    until nc -z "$REDIS_HOST" 6379 2>/dev/null; do
        printf '.'
        sleep 2
    done
    echo ""
    echo "✅ Redis sẵn sàng!"
fi

# ── Kiểm tra manage.py có tồn tại không ──────────
if [ ! -f "manage.py" ]; then
    echo ""
    echo "⚠️  CẢNH BÁO: manage.py không tìm thấy!"
    echo "   Điều này là bình thường nếu bạn đang setup lần đầu."
    echo "   Hãy tạo Django project bằng: django-admin startproject"
    echo ""
    echo "🔄 Đang chờ 30 giây cho manage.py được thêm..."
    sleep 30
    
    if [ ! -f "manage.py" ]; then
        echo "❌ Vẫn không tìm thấy manage.py. Thoát."
        exit 1
    fi
fi

# ── Cài thư viện đặc thù (nếu có) ────────────────
if [ -f "requirements.txt" ]; then
    # Chỉ install nếu requirements.txt không rỗng
    LINES=$(grep -v '^\s*#' requirements.txt | grep -v '^\s*$' | wc -l)
    if [ "$LINES" -gt "0" ]; then
        echo "📦 Cài thư viện đặc thù..."
        pip install -q -r requirements.txt
    fi
fi

# ── Django Migrations ────────────────────────────
echo "🔄 Chạy migrate..."
python manage.py migrate --noinput || true

# ── Tạo dữ liệu demo (chỉ chạy 1 lần) ───────────
if [ -f "fixtures/initial_data.json" ]; then
    echo "📥 Load dữ liệu demo..."
    python manage.py loaddata fixtures/initial_data.json --ignore 2>/dev/null || true
fi

# ── Chạy setup script nếu có ─────────────────────
if [ -f "setup_demo.py" ]; then
    echo "⚙️  Chạy setup demo..."
    python setup_demo.py || true
fi

echo ""
echo "🚀 $SERVICE_NAME đang chạy tại http://0.0.0.0:8000"
echo ""

exec python manage.py runserver 0.0.0.0:8000
