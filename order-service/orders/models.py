from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING',         'Chờ thanh toán'),
        ('PAID',            'Đã thanh toán'),
        ('SHIPPED',         'Đang giao'),
        ('DELIVERED',       'Đã giao'),
        ('PAYMENT_FAILED',  'Thanh toán thất bại'),
        ('CANCELLED',       'Đã hủy'),
    ]
    # BR-8: valid transitions enforced in views
    VALID_TRANSITIONS = {
        'PENDING':        ['PAID', 'PAYMENT_FAILED', 'CANCELLED'],
        'PAID':           ['SHIPPED', 'CANCELLED'],
        'SHIPPED':        ['DELIVERED'],
        'DELIVERED':      [],
        'PAYMENT_FAILED': ['CANCELLED'],
        'CANCELLED':      [],
    }

    user_id          = models.IntegerField()               # BR-1: from JWT
    total_price      = models.DecimalField(max_digits=14, decimal_places=2)  # BR-3: server-computed
    status           = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    shipping_address = models.TextField()
    recipient_name   = models.CharField(max_length=100, blank=True, default='')
    phone            = models.CharField(max_length=20, blank=True, default='')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)  # chốt giá lúc đặt

    class Meta:
        db_table = 'order_item'
