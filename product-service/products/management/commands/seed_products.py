from django.core.management.base import BaseCommand

from products.models import Book, Category, Electronics, Fashion, Product


class Command(BaseCommand):
    help = "Seed demo data for Product Service"

    def handle(self, *args, **options):
        self.stdout.write("\n🚀 Bắt đầu seed dữ liệu demo cho Product Service...")

        categories = self.create_categories()
        created_products, updated_products = self.create_products(categories)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Đã tạo/cập nhật {len(categories)} danh mục, "
                f"{created_products} sản phẩm mới, {updated_products} sản phẩm cập nhật."
            )
        )
        self.stdout.write(self.style.SUCCESS("🎉 Seed dữ liệu hoàn tất.\n"))

    def create_categories(self):
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

        return categories

    def create_products(self, categories):
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
                "detail": {
                    "model": Book,
                    "defaults": {
                        "author": "Robert C. Martin",
                        "publisher": "Prentice Hall",
                        "isbn": "9780132350884",
                        "pages": 464,
                        "language": "Tiếng Anh",
                    },
                },
            },
            {
                "name": "Design Patterns - Head First",
                "sku": "BOOK-DESIGN-PATTERNS",
                "short_description": "Sách học mẫu thiết kế phần mềm trực quan và dễ hiểu.",
                "description": "Tài liệu hữu ích cho lập trình viên muốn nắm vững các pattern thực chiến.",
                "price": 320000,
                "compare_at_price": 390000,
                "stock": 28,
                "image": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=900",
                "category": categories["Sách"],
                "product_type": "book",
                "rating": 4.7,
                "sold_count": 88,
                "is_featured": False,
                "detail": {
                    "model": Book,
                    "defaults": {
                        "author": "Eric Freeman",
                        "publisher": "O'Reilly Media",
                        "isbn": "9780596007126",
                        "pages": 694,
                        "language": "Tiếng Anh",
                    },
                },
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
                "detail": {
                    "model": Electronics,
                    "defaults": {
                        "brand": "NovaTech",
                        "warranty_months": 24,
                        "model": "UltraBook Pro 14",
                        "specifications": {"cpu": "Intel Core i7", "ram": "16GB", "storage": "512GB SSD"},
                    },
                },
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
                "detail": {
                    "model": Electronics,
                    "defaults": {
                        "brand": "SoundMax",
                        "warranty_months": 12,
                        "model": "Bass+ Wireless",
                        "specifications": {"battery": "30h", "noise_cancelling": True, "connectivity": "Bluetooth 5.3"},
                    },
                },
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
                "detail": {
                    "model": Electronics,
                    "defaults": {
                        "brand": "KeyForge",
                        "warranty_months": 18,
                        "model": "RGB TKL",
                        "specifications": {"switch": "Brown", "layout": "TKL", "lighting": "RGB"},
                    },
                },
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
                "detail": {
                    "model": Fashion,
                    "defaults": {
                        "brand": "UrbanWear",
                        "size": "M",
                        "color": "Đen",
                        "material": "Cotton",
                    },
                },
            },
            {
                "name": "Balo Laptop Minimal",
                "sku": "FASH-BAG-MINIMAL",
                "short_description": "Balo laptop chống sốc, thiết kế tối giản.",
                "description": "Balo có ngăn laptop 15.6 inch, chống nước nhẹ, nhiều ngăn tiện dụng.",
                "price": 450000,
                "compare_at_price": 590000,
                "stock": 40,
                "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900",
                "category": categories["Thời trang"],
                "product_type": "fashion",
                "rating": 4.6,
                "sold_count": 76,
                "is_featured": True,
                "detail": {
                    "model": Fashion,
                    "defaults": {
                        "brand": "Minimal Studio",
                        "size": "One Size",
                        "color": "Xám",
                        "material": "Polyester chống nước",
                    },
                },
            },
        ]

        created = 0
        updated = 0

        for item in products_data:
            detail = item.pop("detail")
            product, was_created = Product.objects.update_or_create(
                sku=item["sku"],
                defaults={**item, "is_active": True},
            )

            if was_created:
                created += 1
            else:
                updated += 1

            detail["model"].objects.update_or_create(
                product=product,
                defaults=detail["defaults"],
            )

        return created, updated