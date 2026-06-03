from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet, health_check, seed_demo_products

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    # Standalone paths phải đứng TRƯỚC router để không bị products/<pk>/ nuốt
    path("products/health/", health_check, name="health-check"),
    path("products/seed-demo/", seed_demo_products, name="seed-demo-products"),
    path("", include(router.urls)),
]