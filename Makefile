# ═══════════════════════════════════════════════════
#  Makefile — ecom-final
#  Dùng: make <target>
# ═══════════════════════════════════════════════════

.PHONY: help build-base build up down logs ps clean rebuild
.PHONY: logs-user logs-product logs-order logs-ai
.PHONY: shell-user shell-product migrate

# ── Màu sắc terminal ──
GREEN  = \033[0;32m
YELLOW = \033[1;33m
NC     = \033[0m

help:
	@echo ""
	@echo "$(GREEN)ecom-final — Lệnh quản lý$(NC)"
	@echo "────────────────────────────────────"
	@echo "  $(YELLOW)make build-base$(NC)   Build base images (chạy 1 lần đầu)"
	@echo "  $(YELLOW)make build$(NC)        Build tất cả service images"
	@echo "  $(YELLOW)make up$(NC)           Khởi động toàn hệ thống"
	@echo "  $(YELLOW)make down$(NC)         Tắt toàn hệ thống"
	@echo "  $(YELLOW)make logs$(NC)         Xem logs realtime"
	@echo "  $(YELLOW)make ps$(NC)           Xem trạng thái containers"
	@echo "  $(YELLOW)make clean$(NC)        Xóa containers + volumes"
	@echo "  $(YELLOW)make rebuild$(NC)      Clean + build-base + up"
	@echo ""

# ── Bước 1: Build base images (chỉ cần chạy 1 lần) ──
build-base:
	@echo "$(GREEN)🔨 Building Django base image...$(NC)"
	docker build -t ecom-django-base:latest ./base-images/django-base/
	@echo "$(GREEN)🔨 Building AI base image (có thể mất 10-15 phút lần đầu)...$(NC)"
	docker build -t ecom-ai-base:latest ./base-images/ai-base/
	@echo "$(GREEN)✅ Base images built successfully!$(NC)"

# ── Bước 2: Build service images (nhanh vì dùng base) ──
build:
	docker-compose build

# ── Khởi động ──
up:
	@echo "$(GREEN)🚀 Khởi động ecom-final...$(NC)"
	docker-compose up -d
	@echo ""
	@echo "$(GREEN)✅ Hệ thống đang chạy!$(NC)"
	@echo "  🌐 Frontend:    http://localhost"
	@echo "  📡 API Health:  http://localhost/health"
	@echo "  🔷 Neo4j UI:    http://localhost:7474"
	@echo ""

# ── Tắt ──
down:
	docker-compose down

# ── Logs ──
logs:
	docker-compose logs -f --tail=50

# ── Trạng thái ──
ps:
	docker-compose ps

# ── Xóa sạch ──
clean:
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)✅ Đã xóa containers và volumes$(NC)"

# ── Rebuild hoàn toàn ──
rebuild: clean build-base build up

# ── Lệnh tiện ích cho từng service ──
logs-user:
	docker-compose logs -f user-service

logs-product:
	docker-compose logs -f product-service

logs-order:
	docker-compose logs -f order-service

logs-ai:
	docker-compose logs -f ai-service

shell-user:
	docker exec -it ecom-user-service python manage.py shell

shell-product:
	docker exec -it ecom-product-service python manage.py shell

migrate:
	docker-compose exec user-service     python manage.py migrate
	docker-compose exec product-service  python manage.py migrate
	docker-compose exec cart-service     python manage.py migrate
	docker-compose exec order-service    python manage.py migrate
	docker-compose exec payment-service  python manage.py migrate
	docker-compose exec shipping-service python manage.py migrate
