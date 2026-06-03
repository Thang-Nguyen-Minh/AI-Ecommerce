from django.db import models


class Cart(models.Model):
    # BR-1: mỗi user đúng một giỏ; user_id lấy từ JWT, không phải FK
    user_id = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_cart'

    def __str__(self):
        return f"Cart(user_id={self.user_id})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    # product_id là số tham chiếu sang product-service — không FK
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'cart_item'
        unique_together = [('cart', 'product_id')]  # BR-5: không trùng dòng

    def __str__(self):
        return f"CartItem(cart={self.cart_id}, product={self.product_id}, qty={self.quantity})"
