from django.contrib import admin

from .models import Book, Category, Electronics, Fashion, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}


class BookInline(admin.StackedInline):
    model = Book
    extra = 0
    max_num = 1


class ElectronicsInline(admin.StackedInline):
    model = Electronics
    extra = 0
    max_num = 1


class FashionInline(admin.StackedInline):
    model = Fashion
    extra = 0
    max_num = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "sku",
        "category",
        "product_type",
        "price",
        "stock",
        "is_active",
        "is_featured",
        "created_at",
    ]
    list_filter = ["category", "product_type", "is_active", "is_featured"]
    search_fields = ["name", "sku", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BookInline, ElectronicsInline, FashionInline]