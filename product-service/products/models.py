from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Danh mục sản phẩm."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    image = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products_category"
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Sản phẩm chung cho hệ thống e-commerce."""

    PRODUCT_TYPE_CHOICES = [
        ("general", "General"),
        ("book", "Book"),
        ("electronics", "Electronics"),
        ("fashion", "Fashion"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    sku = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True, default="")
    short_description = models.CharField(max_length=300, blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.URLField(blank=True, default="")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    product_type = models.CharField(max_length=30, choices=PRODUCT_TYPE_CHOICES, default="general")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    sold_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.IntegerField(null=True, blank=True, help_text="ID user admin/staff tạo sản phẩm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_product"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["product_type"]),
            models.Index(fields=["is_active", "is_featured"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round((1 - float(self.price) / float(self.compare_at_price)) * 100)
        return 0

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Book(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="book_detail")
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255, blank=True, default="")
    isbn = models.CharField(max_length=30, blank=True, default="")
    pages = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=80, blank=True, default="Tiếng Việt")

    class Meta:
        db_table = "products_book"

    def __str__(self):
        return f"{self.product.name} - {self.author}"


class Electronics(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="electronics_detail")
    brand = models.CharField(max_length=120)
    warranty_months = models.PositiveIntegerField(default=12)
    model = models.CharField(max_length=120, blank=True, default="")
    specifications = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "products_electronics"

    def __str__(self):
        return f"{self.brand} {self.product.name}"


class Fashion(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="fashion_detail")
    brand = models.CharField(max_length=120, blank=True, default="")
    size = models.CharField(max_length=30)
    color = models.CharField(max_length=60)
    material = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        db_table = "products_fashion"

    def __str__(self):
        return f"{self.product.name} - {self.size}/{self.color}"