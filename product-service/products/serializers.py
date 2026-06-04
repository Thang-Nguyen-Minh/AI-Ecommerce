import uuid
from rest_framework import serializers

from .models import Book, Category, Electronics, Fashion, Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "is_active",
                  "product_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at", "product_count"]


# ── Detail serializers ────────────────────────────────
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["author", "publisher", "isbn", "pages", "language"]


class ElectronicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electronics
        fields = ["brand", "warranty_months", "model", "specifications"]


class FashionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fashion
        fields = ["brand", "size", "color", "material"]


# ── List serializer (GET /products/) ─────────────────
class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "sku", "short_description",
            "price", "compare_at_price", "stock", "image",
            "category", "category_name", "product_type",
            "rating", "sold_count", "is_active", "is_featured",
            "in_stock", "discount_percent", "created_at",
        ]


# ── Detail serializer (GET /products/<id>/) ──────────
class ProductDetailSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)
    book_detail = BookSerializer(read_only=True)
    electronics_detail = ElectronicsSerializer(read_only=True)
    fashion_detail = FashionSerializer(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "sku",
            "description", "short_description",
            "price", "compare_at_price", "stock", "image",
            "category", "category_detail", "product_type",
            "rating", "sold_count", "is_active", "is_featured",
            "in_stock", "discount_percent",
            "book_detail", "electronics_detail", "fashion_detail",
            "created_at", "updated_at",
        ]


# ── Create/Update serializer ──────────────────────────
class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    # Nhận category_id theo contract (maps tới FK category)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        error_messages={"does_not_exist": "Category với id={pk_value} không tồn tại."},  # BR-3
    )
    # Nhận type theo contract (maps tới product_type)
    type = serializers.ChoiceField(
        choices=["book", "electronics", "fashion", "general"],
        source="product_type",
        write_only=True,
        required=False,
    )
    # detail chung — được phân loại theo type khi validate
    detail = serializers.DictField(required=False, write_only=True, default=dict)

    # Giữ lại các nested field để response trả về đầy đủ
    book_detail = BookSerializer(read_only=True)
    electronics_detail = ElectronicsSerializer(read_only=True)
    fashion_detail = FashionSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "sku", "description", "short_description",
            "price", "compare_at_price", "stock", "image",
            "category_id", "category_name",
            "type", "product_type",
            "rating", "is_active", "is_featured",
            "detail",
            "book_detail", "electronics_detail", "fashion_detail",
        ]
        read_only_fields = ["id", "product_type"]
        extra_kwargs = {
            "sku": {"required": False},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("phải lớn hơn 0.")  # BR-2
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("không được âm.")  # BR-1
        return value

    def validate(self, attrs):
        product_type = attrs.get("product_type", getattr(self.instance, "product_type", "general"))
        detail = attrs.get("detail", {})

        detail_required_fields = {
            "book":        ["author"],
            "electronics": ["brand"],
            "fashion":     ["size", "color"],
        }
        required = detail_required_fields.get(product_type, [])
        missing = [f for f in required if not detail.get(f)]
        if missing and self.instance is None:
            raise serializers.ValidationError(
                {"detail": f"Loại {product_type} cần có: {', '.join(missing)}."}
            )
        return attrs

    def _auto_sku(self, product_type, name):
        prefix = {"book": "BK", "electronics": "EL", "fashion": "FA"}.get(product_type, "GN")
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def _save_detail(self, product, detail: dict):
        pt = product.product_type
        if pt == "book" and detail:
            Book.objects.update_or_create(product=product, defaults={
                "author":    detail.get("author", ""),
                "publisher": detail.get("publisher", ""),
                "isbn":      detail.get("isbn", ""),
                "pages":     detail.get("pages") or None,
                "language":  detail.get("language", "Tiếng Việt"),
            })
        elif pt == "electronics" and detail:
            Electronics.objects.update_or_create(product=product, defaults={
                "brand":          detail.get("brand", ""),
                "warranty_months": detail.get("warranty_months") or detail.get("warranty", 12),
                "model":          detail.get("model", ""),
                "specifications": detail.get("specifications", {}),
            })
        elif pt == "fashion" and detail:
            Fashion.objects.update_or_create(product=product, defaults={
                "brand":    detail.get("brand", ""),
                "size":     detail.get("size", ""),
                "color":    detail.get("color", ""),
                "material": detail.get("material", ""),
            })

    def create(self, validated_data):
        detail = validated_data.pop("detail", {})

        # Auto-generate SKU nếu không gửi lên
        if not validated_data.get("sku"):
            pt = validated_data.get("product_type", "general")
            validated_data["sku"] = self._auto_sku(pt, validated_data.get("name", ""))

        request = self.context.get("request")
        if request and getattr(request, "user", None) and request.user.is_authenticated:
            validated_data["created_by"] = request.user.id

        product = Product.objects.create(**validated_data)
        self._save_detail(product, detail)
        return product

    def update(self, instance, validated_data):
        detail = validated_data.pop("detail", {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if detail:
            self._save_detail(instance, detail)
        return instance
