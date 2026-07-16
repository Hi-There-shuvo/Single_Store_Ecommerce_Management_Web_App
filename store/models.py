from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class SiteSettings(models.Model):
    """Singleton model for store-wide settings. Admin manages everything here."""
    # Branding
    store_name = models.CharField(max_length=200, default='SoloStore')
    tagline = models.CharField(max_length=300, default='Your One-Stop Store')
    logo = models.ImageField(upload_to='branding/', blank=True, null=True)
    favicon = models.ImageField(upload_to='branding/', blank=True, null=True)

    # Contact Info
    email = models.EmailField(default='info@SoloStore.com')
    phone = models.CharField(max_length=30, default='+880 1234-567890')
    address = models.CharField(max_length=300, default='Dhaka, Bangladesh')

    # Social Links
    facebook_url = models.URLField(blank=True, default='')
    instagram_url = models.URLField(blank=True, default='')
    twitter_url = models.URLField(blank=True, default='')

    # Homepage Banner
    banner_title = models.CharField(max_length=200, default='Shop Smarter, Live Better')
    banner_subtitle = models.TextField(default='Discover thousands of quality products — delivered fast, priced right.')

    # Footer
    footer_text = models.CharField(max_length=500, default='Your trusted one-stop shop for quality products at amazing prices.')
    copyright_text = models.CharField(max_length=200, default='© 2026 SoloStore. All rights reserved.')

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
        # Enforce singleton — always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, default='📦',
                            help_text='Emoji or icon class for display')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    details = models.TextField(blank=True, default='',
                               help_text='Product details/specifications. Enter each detail on a new line. Each line will appear as a bullet point.')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Cost price of the product (for calculating expense and profit).")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                         help_text='Fixed discounted price. Leave blank for no discount.')
    discount_percentage = models.PositiveIntegerField(default=0, blank=True,
                                                       help_text='Percentage discount (0-100). Overridden by discount_price if set.')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.cost or self.cost == 0:
            from decimal import Decimal
            self.cost = self.price * Decimal('0.60')
        super().save(*args, **kwargs)

    def get_final_price(self):
        """Returns the best price considering discount_price, discount_percentage, and flash sales."""
        prices = [self.price]

        # Fixed discount price
        if self.discount_price:
            prices.append(self.discount_price)

        # Percentage discount
        if self.discount_percentage and self.discount_percentage > 0:
            pct_price = self.price * (100 - self.discount_percentage) / 100
            prices.append(pct_price)

        # Flash sale discount (best active flash sale)
        active_flash = self.flash_sales.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).order_by('-discount_percentage').first()
        if active_flash:
            flash_price = self.price * (100 - active_flash.discount_percentage) / 100
            prices.append(flash_price)

        return min(prices)

    def get_discount_display(self):
        """Returns the discount percentage to display."""
        if self.discount_price:
            if self.price > 0:
                return int(((self.price - self.discount_price) / self.price) * 100)
        if self.discount_percentage:
            return self.discount_percentage
        # Check flash sale
        active_flash = self.get_active_flash_sale()
        if active_flash:
            return active_flash.discount_percentage
        return 0

    def get_active_flash_sale(self):
        """Returns the current active flash sale for this product, if any."""
        return self.flash_sales.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()

    def is_on_flash_sale(self):
        return self.get_active_flash_sale() is not None

    def has_discount(self):
        return self.get_final_price() < self.price

    def get_details_list(self):
        """Returns the details field as a list of non-empty lines for bullet-point display."""
        if not self.details:
            return []
        return [line.strip() for line in self.details.splitlines() if line.strip()]

    def is_in_stock(self):
        return self.stock > 0

    def get_average_rating(self):
        """Calculates the average rating of all product reviews."""
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        total = sum(r.rating for r in reviews)
        return round(total / len(reviews), 1)

    def get_rating_stars(self):
        """Helper to return lists of stars to render in templates."""
        avg = self.get_average_rating()
        full_count = int(avg)
        half_count = 1 if (avg - full_count) >= 0.25 and (avg - full_count) < 0.75 else 0
        if (avg - full_count) >= 0.75:
            full_count += 1
            half_count = 0
        empty_count = 5 - (full_count + half_count)
        return {
            'full': [1] * full_count,
            'half': [1] * half_count,
            'empty': [1] * empty_count,
            'value': avg,
        }


class ProductImage(models.Model):
    """Additional images for a product. The main image stays on Product.image."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.product.name} (#{self.order})"

class FlashSale(models.Model):
    """Admin-managed flash sales with countdown timers."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_percentage = models.PositiveIntegerField(
        help_text='Discount percentage for all products in this flash sale (e.g. 30 = 30% off)'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    products = models.ManyToManyField(Product, related_name='flash_sales', blank=True)
    is_active = models.BooleanField(default=True)
    banner_color = models.CharField(max_length=7, default='#ff6584',
                                     help_text='Banner background color (hex code)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.discount_percentage}% off)"

    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    @property
    def has_ended(self):
        return timezone.now() > self.end_date

    @property
    def time_remaining(self):
        """Returns remaining time as a dict for the countdown timer."""
        if self.has_ended:
            return None
        delta = self.end_date - timezone.now()
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return None
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return {'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}


class NewsletterSubscriber(models.Model):
    """Model to store email addresses subscribed to the store's newsletter."""
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def __str__(self):
        return self.email


class Review(models.Model):
    """Model to store product reviews and ratings submitted by verified/registered users."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # One review per product per user

    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star review of {self.product.name}"


