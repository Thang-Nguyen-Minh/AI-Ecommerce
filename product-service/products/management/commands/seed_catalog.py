"""
Seed ~50 sản phẩm đa dạng (Book / Electronics / Fashion) kèm bản ghi chi tiết.
Idempotent theo SKU. Chạy: python manage.py seed_catalog
"""
import random

from django.core.management.base import BaseCommand

from products.models import Book, Category, Electronics, Fashion, Product

IMG = {
    "book": [
        "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=900",
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=900",
        "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=900",
        "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=900",
    ],
    "electronics": [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900",
        "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=900",
        "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=900",
    ],
    "fashion": [
        "https://images.unsplash.com/photo-1520975954732-35dd22299614?w=900",
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900",
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=900",
        "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=900",
    ],
}

# ── Dữ liệu sinh sản phẩm ───────────────────────────────
BOOKS = [
    ("Lập trình Python cơ bản", "A. Nguyễn", "NXB Trẻ", 150000),
    ("Thuật toán & Cấu trúc dữ liệu", "T. Cormen", "MIT Press", 420000),
    ("Refactoring", "Martin Fowler", "Addison-Wesley", 510000),
    ("The Pragmatic Programmer", "A. Hunt", "Addison-Wesley", 480000),
    ("Domain-Driven Design", "Eric Evans", "Addison-Wesley", 560000),
    ("You Don't Know JS", "Kyle Simpson", "O'Reilly", 300000),
    ("Deep Learning", "Ian Goodfellow", "MIT Press", 690000),
    ("Nhà Giả Kim", "Paulo Coelho", "NXB Hội Nhà Văn", 90000),
    ("Đắc Nhân Tâm", "Dale Carnegie", "NXB Tổng Hợp", 110000),
    ("Tư Duy Nhanh và Chậm", "Daniel Kahneman", "NXB Thế Giới", 180000),
    ("Sapiens: Lược Sử Loài Người", "Y. N. Harari", "NXB Tri Thức", 220000),
    ("Atomic Habits", "James Clear", "Avery", 175000),
    ("Clean Architecture", "Robert C. Martin", "Prentice Hall", 430000),
    ("Designing Data-Intensive Apps", "M. Kleppmann", "O'Reilly", 620000),
    ("Cracking the Coding Interview", "G. McDowell", "CareerCup", 350000),
    ("Effective Java", "Joshua Bloch", "Addison-Wesley", 400000),
    ("Head First Design Patterns", "E. Freeman", "O'Reilly", 360000),
]

ELECTRONICS = [
    ("Laptop Gaming Strix 15", "ASUS", 'i7/16GB/RTX4060', 27990000),
    ("Laptop Văn Phòng Air 13", "Apple", 'M2/8GB/256GB', 24990000),
    ("Chuột không dây Ergo", "Logitech", 'MX Master 3S', 2390000),
    ("Bàn phím cơ Pro", "Keychron", 'K8 Hot-swap', 1890000),
    ("Tai nghe chống ồn QC", "Bose", 'QuietComfort 45', 6990000),
    ("Tai nghe True Wireless", "Sony", 'WF-1000XM5', 5990000),
    ("Màn hình 27 inch 2K", "Dell", 'S2722DC', 6490000),
    ("Webcam 1080p", "Logitech", 'C920', 1290000),
    ("Ổ cứng SSD 1TB", "Samsung", '980 Pro NVMe', 2790000),
    ("Sạc nhanh GaN 65W", "Anker", '735 Nano II', 890000),
    ("Loa Bluetooth di động", "JBL", 'Charge 5', 2990000),
    ("Đồng hồ thông minh", "Garmin", 'Forerunner 255', 7990000),
    ("Máy đọc sách", "Amazon", 'Kindle Paperwhite', 3290000),
    ("Bộ phát Wi-Fi 6", "TP-Link", 'Archer AX73', 2190000),
    ("Pin dự phòng 20.000mAh", "Xiaomi", 'Mi Power Bank 3', 690000),
    ("Camera an ninh", "Ezviz", 'C6N 1080p', 590000),
]

FASHION = [
    ("Áo thun cotton basic", "M", "Trắng", 150000),
    ("Áo sơ mi oxford", "L", "Xanh nhạt", 320000),
    ("Quần jeans slim fit", "31", "Xanh đậm", 450000),
    ("Quần kaki chinos", "32", "Be", 390000),
    ("Áo hoodie nỉ bông", "L", "Xám", 420000),
    ("Áo khoác dù 2 lớp", "XL", "Đen", 550000),
    ("Váy liền công sở", "M", "Đỏ đô", 480000),
    ("Chân váy xếp ly", "S", "Đen", 290000),
    ("Giày sneaker classic", "42", "Trắng", 890000),
    ("Giày chạy bộ nhẹ", "41", "Xám/Cam", 1190000),
    ("Dép quai ngang", "43", "Đen", 250000),
    ("Mũ lưỡi trai", "Free", "Navy", 150000),
    ("Thắt lưng da bò", "Free", "Nâu", 350000),
    ("Túi tote canvas", "Free", "Kem", 220000),
    ("Khăn len dệt kim", "Free", "Xám tiêu", 180000),
    ("Áo polo pique", "L", "Xanh rêu", 280000),
    ("Quần short thể thao", "M", "Đen", 190000),
]


class Command(BaseCommand):
    help = "Seed ~50 sản phẩm đa dạng (book/electronics/fashion)"

    def handle(self, *args, **options):
        cats = {
            "book": Category.objects.get_or_create(name="Sách", defaults={"is_active": True})[0],
            "electronics": Category.objects.get_or_create(name="Điện tử", defaults={"is_active": True})[0],
            "fashion": Category.objects.get_or_create(name="Thời trang", defaults={"is_active": True})[0],
        }
        created = 0

        def make(ptype, name, sku, price, detail_model, detail):
            nonlocal created
            stock = random.randint(8, 120)
            p, was_created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "short_description": name,
                    "description": f"{name} — sản phẩm chính hãng, chất lượng đảm bảo.",
                    "price": price,
                    "compare_at_price": round(price * 1.25),
                    "stock": stock,
                    "image": random.choice(IMG[ptype]),
                    "category": cats[ptype],
                    "product_type": ptype,
                    "rating": round(random.uniform(3.8, 5.0), 1),
                    "sold_count": random.randint(0, 400),
                    "is_featured": random.random() < 0.25,
                    "is_active": True,
                },
            )
            detail_model.objects.update_or_create(product=p, defaults=detail)
            if was_created:
                created += 1

        for i, (name, author, pub, price) in enumerate(BOOKS):
            make("book", name, f"BK-SEED-{i:03d}", price, Book,
                 {"author": author, "publisher": pub, "isbn": f"978{random.randint(10**9, 10**10 - 1)}",
                  "pages": random.randint(150, 800), "language": "Tiếng Việt"})

        for i, (name, brand, model, price) in enumerate(ELECTRONICS):
            make("electronics", name, f"EL-SEED-{i:03d}", price, Electronics,
                 {"brand": brand, "model": model, "warranty_months": random.choice([12, 18, 24, 36]),
                  "specifications": {"note": model}})

        for i, (name, size, color, price) in enumerate(FASHION):
            make("fashion", name, f"FA-SEED-{i:03d}", price, Fashion,
                 {"brand": "ecom-fashion", "size": size, "color": color, "material": "Cao cấp"})

        total = len(BOOKS) + len(ELECTRONICS) + len(FASHION)
        self.stdout.write(self.style.SUCCESS(
            f"✅ Seed xong: {total} sản phẩm ({created} mới). Tổng trong DB: {Product.objects.count()}"
        ))
