# Generated manually for Product Service.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("image", models.URLField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name_plural": "Categories",
                "db_table": "products_category",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(blank=True, max_length=280, unique=True)),
                ("sku", models.CharField(max_length=80, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("short_description", models.CharField(blank=True, default="", max_length=300)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("compare_at_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("stock", models.PositiveIntegerField(default=0)),
                ("image", models.URLField(blank=True, default="")),
                (
                    "product_type",
                    models.CharField(
                        choices=[
                            ("general", "General"),
                            ("book", "Book"),
                            ("electronics", "Electronics"),
                            ("fashion", "Fashion"),
                        ],
                        default="general",
                        max_length=30,
                    ),
                ),
                ("rating", models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ("sold_count", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("created_by", models.IntegerField(blank=True, help_text="ID user admin/staff tạo sản phẩm", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="products",
                        to="products.category",
                    ),
                ),
            ],
            options={
                "db_table": "products_product",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author", models.CharField(max_length=255)),
                ("publisher", models.CharField(blank=True, default="", max_length=255)),
                ("isbn", models.CharField(blank=True, default="", max_length=30)),
                ("pages", models.PositiveIntegerField(blank=True, null=True)),
                ("language", models.CharField(blank=True, default="Tiếng Việt", max_length=80)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="book_detail",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "db_table": "products_book",
            },
        ),
        migrations.CreateModel(
            name="Electronics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("brand", models.CharField(max_length=120)),
                ("warranty_months", models.PositiveIntegerField(default=12)),
                ("model", models.CharField(blank=True, default="", max_length=120)),
                ("specifications", models.JSONField(blank=True, default=dict)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="electronics_detail",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "db_table": "products_electronics",
            },
        ),
        migrations.CreateModel(
            name="Fashion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("brand", models.CharField(blank=True, default="", max_length=120)),
                ("size", models.CharField(max_length=30)),
                ("color", models.CharField(max_length=60)),
                ("material", models.CharField(blank=True, default="", max_length=120)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fashion_detail",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "db_table": "products_fashion",
            },
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["slug"], name="products_pr_slug_40cf83_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["sku"], name="products_pr_sku_45c491_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["product_type"], name="products_pr_product_bbb9f5_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["is_active", "is_featured"], name="products_pr_is_acti_9bd03f_idx"),
        ),
    ]