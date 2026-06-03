from django.db.models import Count, Q
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Book, Category, Electronics, Fashion, Product
from .serializers import (
    CategorySerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class IsAdminOrStaffOrReadOnly(permissions.BasePermission):
    """Cho phép xem công khai, chỉ admin/staff mới được chỉnh sửa."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        role = getattr(user, "role", None)
        return role in ("admin", "staff") or user.is_staff or user.is_superuser


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(product_count=Count("products")).all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    lookup_field = "pk"
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method in permissions.SAFE_METHODS:
            queryset = queryset.filter(is_active=True)
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    permission_classes = [IsAdminOrStaffOrReadOnly]  # BR-6: staff/admin mới được ghi
    filterset_fields = ["category", "product_type", "is_featured", "is_active"]
    search_fields = ["name", "sku", "description", "short_description", "category__name"]
    ordering_fields = ["created_at", "price", "rating", "sold_count", "name", "stock"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.method in permissions.SAFE_METHODS:
            queryset = queryset.filter(is_active=True)

        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        in_stock = self.request.query_params.get("in_stock")
        featured = self.request.query_params.get("featured")
        category_slug = self.request.query_params.get("category_slug")

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if in_stock in ("1", "true", "True"):
            queryset = queryset.filter(stock__gt=0)
        if featured in ("1", "true", "True"):
            queryset = queryset.filter(is_featured=True)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def featured(self, request):
        products = self.get_queryset().filter(is_featured=True)[:8]
        serializer = ProductListSerializer(products, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def stats(self, request):
        data = {
            "total": Product.objects.count(),
            "active": Product.objects.filter(is_active=True).count(),
            "out_of_stock": Product.objects.filter(stock=0).count(),
            "categories": Category.objects.filter(is_active=True).count(),
        }
        return Response(data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return Response({
        "service": "product-service",
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "version": "1.0.0",
    })


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def seed_demo_products(request):
    """Tạo dữ liệu demo để frontend có sản phẩm hiển thị ngay."""

    categories_data = [
        {
            "name": "Sách",
            "description": "Sách kỹ năng, lập trình và kinh doanh",
            "image": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=800",
        },
        {
            "name": "Điện tử",
            "description": "Laptop, tai nghe, phụ kiện công nghệ",
            "image": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800",
        },
        {
            "name": "Thời trang",
            "description": "Quần áo, giày dép và phụ kiện",
            "image": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=800",
        },
    ]

    categories = {}
    for item in categories_data:
        category, _ = Category.objects.update_or_create(
            name=item["name"],
            defaults={
                "description": item["description"],
                "image": item["image"],
                "is_active": True,
            },
        )
        categories[item["name"]] = category

    products_data = [
        {
            "name": "Clean Code - Nghệ thuật viết code sạch",
            "sku": "BOOK-CLEAN-CODE",
            "short_description": "Sách kinh điển về kỹ thuật viết mã nguồn dễ đọc, dễ bảo trì.",
            "description": "Clean Code giúp lập trình viên nâng cao chất lượng code, giảm lỗi và tăng khả năng bảo trì dự án.",
            "price": 250000,
            "compare_at_price": 320000,
            "stock": 35,
            "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=900",
            "category": categories["Sách"],
            "product_type": "book",
            "rating": 4.8,
            "sold_count": 120,
            "is_featured": True,
        },
        {
            "name": "Laptop Ultrabook Pro 14",
            "sku": "ELEC-LAPTOP-PRO14",
            "short_description": "Laptop mỏng nhẹ, hiệu năng tốt cho học tập và làm việc.",
            "description": "Màn hình 14 inch, RAM 16GB, SSD 512GB, pin lâu, phù hợp sinh viên và dân văn phòng.",
            "price": 18990000,
            "compare_at_price": 21990000,
            "stock": 12,
            "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900",
            "category": categories["Điện tử"],
            "product_type": "electronics",
            "rating": 4.7,
            "sold_count": 48,
            "is_featured": True,
        },
        {
            "name": "Tai nghe Bluetooth Bass+",
            "sku": "ELEC-HEADPHONE-BASS",
            "short_description": "Tai nghe không dây chống ồn, âm bass mạnh.",
            "description": "Tai nghe Bluetooth pin 30 giờ, hỗ trợ chống ồn chủ động, âm thanh rõ nét.",
            "price": 1290000,
            "compare_at_price": 1690000,
            "stock": 50,
            "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900",
            "category": categories["Điện tử"],
            "product_type": "electronics",
            "rating": 4.5,
            "sold_count": 210,
            "is_featured": True,
        },
        {
            "name": "Áo khoác Basic Unisex",
            "sku": "FASH-JACKET-BASIC",
            "short_description": "Áo khoác unisex đơn giản, dễ phối đồ.",
            "description": "Chất liệu cotton pha polyester, form rộng thoải mái, phù hợp đi học, đi chơi.",
            "price": 390000,
            "compare_at_price": 520000,
            "stock": 80,
            "image": "https://images.unsplash.com/photo-1520975954732-35dd22299614?w=900",
            "category": categories["Thời trang"],
            "product_type": "fashion",
            "rating": 4.4,
            "sold_count": 95,
            "is_featured": False,
        },
        {
            "name": "Balo Laptop Minimal",
            "sku": "GEN-BALO-MINIMAL",
            "short_description": "Balo laptop chống sốc, thiết kế tối giản.",
            "description": "Balo có ngăn laptop 15.6 inch, chống nước nhẹ, nhiều ngăn tiện dụng.",
            "price": 450000,
            "compare_at_price": 590000,
            "stock": 40,
            "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900",
            "category": categories["Thời trang"],
            "product_type": "general",
            "rating": 4.6,
            "sold_count": 76,
            "is_featured": True,
        },
        {
            "name": "Bàn phím cơ RGB TKL",
            "sku": "ELEC-KEYBOARD-RGB",
            "short_description": "Bàn phím cơ layout TKL, đèn RGB, switch êm.",
            "description": "Bàn phím cơ phù hợp gaming và lập trình, keycap bền, có nhiều chế độ LED.",
            "price": 890000,
            "compare_at_price": 1190000,
            "stock": 25,
            "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=900",
            "category": categories["Điện tử"],
            "product_type": "electronics",
            "rating": 4.6,
            "sold_count": 133,
            "is_featured": False,
        },
    ]

    detail_data = {
        "BOOK-CLEAN-CODE":      ("book",        {"author": "Robert C. Martin", "publisher": "Prentice Hall", "isbn": "978-0132350884"}),
        "ELEC-LAPTOP-PRO14":   ("electronics",  {"brand": "UltraBook", "warranty_months": 24, "model": "Pro 14 2024"}),
        "ELEC-HEADPHONE-BASS": ("electronics",  {"brand": "BassTech", "warranty_months": 12, "model": "Bass+"}),
        "FASH-JACKET-BASIC":   ("fashion",      {"size": "M", "color": "Đen", "material": "Cotton pha Polyester"}),
        "GEN-BALO-MINIMAL":    ("fashion",      {"size": "One Size", "color": "Xám", "material": "Vải chống nước"}),
        "ELEC-KEYBOARD-RGB":   ("electronics",  {"brand": "MechKeys", "warranty_months": 12, "model": "TKL-RGB"}),
    }

    created = 0
    updated = 0
    for item in products_data:
        sku = item["sku"]
        product, was_created = Product.objects.update_or_create(
            sku=sku,
            defaults={**item, "is_active": True},
        )
        # Tạo kèm detail record (BR-4, BR-5)
        if sku in detail_data:
            pt, detail = detail_data[sku]
            if pt == "book":
                Book.objects.update_or_create(product=product, defaults=detail)
            elif pt == "electronics":
                Electronics.objects.update_or_create(product=product, defaults=detail)
            elif pt == "fashion":
                Fashion.objects.update_or_create(product=product, defaults=detail)
        if was_created:
            created += 1
        else:
            updated += 1

    return Response(
        {
            "message": "Đã tạo/cập nhật dữ liệu demo Product Service.",
            "categories": len(categories),
            "created": created,
            "updated": updated,
            "total_products": Product.objects.count(),
        },
        status=status.HTTP_201_CREATED,
    )