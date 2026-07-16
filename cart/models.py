from django.db import models
from django.conf import settings
from store.models import Product


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username if self.user else 'Guest'}"

    def get_total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    def get_total_price(self):
        return sum(item.get_total() for item in self.items.all())

    @property
    def total_price(self):
        return self.get_total_price()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart}"

    def get_total(self):
        return self.product.get_final_price() * self.quantity
