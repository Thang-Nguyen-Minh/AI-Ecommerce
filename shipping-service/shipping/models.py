from django.db import models


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Shipping',   'Shipping'),
        ('Delivered',  'Delivered'),
    ]
    # BR-2: chỉ tiến theo thứ tự, không nhảy cóc, không lùi
    VALID_TRANSITIONS = {
        'Processing': ['Shipping'],
        'Shipping':   ['Delivered'],
        'Delivered':  [],
    }

    order_id   = models.IntegerField(unique=True)   # BR-4: mỗi đơn một phiếu
    address    = models.TextField()
    status     = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipment'
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment(order={self.order_id}, {self.status})"
