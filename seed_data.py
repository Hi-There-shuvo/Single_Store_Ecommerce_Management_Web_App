"""
Seed data script for SoloStore.
Run: python manage.py shell < seed_data.py
Or:  venv\Scripts\activate && python manage.py shell < seed_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'single_store_ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from store.models import SiteSettings, Category, Product, FlashSale

print("=== Seeding SoloStore Database ===")

# 1. Create SiteSettings
settings, created = SiteSettings.objects.get_or_create(pk=1, defaults={
    'store_name': 'SoloStore',
    'tagline': 'Your One-Stop Store',
    'email': 'info@SoloStore.com',
    'phone': '+880 1234-567890',
    'address': 'Dhaka, Bangladesh',
    'banner_title': 'Shop Smarter, Live Better',
    'banner_subtitle': 'Discover thousands of quality products — delivered fast, priced right.',
    'footer_text': 'Your trusted one-stop shop for quality products at amazing prices.',
    'copyright_text': '© 2026 SoloStore. All rights reserved.',
})
print(f"SiteSettings: {'Created' if created else 'Already exists'}")

# 2. Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@SoloStore.com', 'admin123')
    print("Superuser created: admin / admin123")
else:
    print("Superuser 'admin' already exists")

# 3. Categories
categories_data = [
    {'name': 'Electronics', 'slug': 'electronics', 'icon': '📱', 'description': 'Smartphones, laptops, gadgets and more'},
    {'name': 'Clothing', 'slug': 'clothing', 'icon': '👕', 'description': 'Fashion for men, women and kids'},
    {'name': 'Home & Kitchen', 'slug': 'home-kitchen', 'icon': '🏠', 'description': 'Furniture, appliances and decor'},
    {'name': 'Books', 'slug': 'books', 'icon': '📚', 'description': 'Best sellers, textbooks and more'},
    {'name': 'Sports', 'slug': 'sports', 'icon': '⚽', 'description': 'Sports gear and fitness equipment'},
    {'name': 'Beauty', 'slug': 'beauty', 'icon': '💄', 'description': 'Skincare, makeup and personal care'},
]

cats = {}
for cd in categories_data:
    cat, created = Category.objects.get_or_create(slug=cd['slug'], defaults=cd)
    cats[cd['slug']] = cat
    print(f"Category '{cat.name}': {'Created' if created else 'Exists'}")

# 4. Products
products_data = [
    {'category': 'electronics', 'name': 'Wireless Bluetooth Headphones', 'slug': 'wireless-bluetooth-headphones', 'price': 2500, 'stock': 50, 'featured': True, 'description': 'Premium noise-cancelling wireless headphones with 30-hour battery life.'},
    {'category': 'electronics', 'name': 'Smart Watch Pro', 'slug': 'smart-watch-pro', 'price': 8500, 'discount_price': 6999, 'stock': 30, 'featured': True, 'description': 'Track your fitness, receive notifications, and more with this premium smartwatch.'},
    {'category': 'electronics', 'name': 'USB-C Fast Charger', 'slug': 'usb-c-fast-charger', 'price': 800, 'stock': 100, 'description': '65W USB-C fast charger compatible with all devices.'},
    {'category': 'electronics', 'name': 'Portable Bluetooth Speaker', 'slug': 'portable-bluetooth-speaker', 'price': 3200, 'discount_percentage': 15, 'stock': 40, 'description': 'Waterproof portable speaker with deep bass and 12-hour playback.'},
    {'category': 'clothing', 'name': 'Classic Cotton T-Shirt', 'slug': 'classic-cotton-tshirt', 'price': 450, 'stock': 200, 'description': 'Comfortable 100% cotton t-shirt available in multiple colors.'},
    {'category': 'clothing', 'name': 'Denim Jacket', 'slug': 'denim-jacket', 'price': 2800, 'discount_price': 2200, 'stock': 25, 'featured': True, 'description': 'Stylish denim jacket perfect for casual outings.'},
    {'category': 'clothing', 'name': 'Running Shoes', 'slug': 'running-shoes', 'price': 3500, 'stock': 60, 'featured': True, 'description': 'Lightweight breathable running shoes with cushioned sole.'},
    {'category': 'clothing', 'name': 'Formal Shirt', 'slug': 'formal-shirt', 'price': 1200, 'discount_percentage': 20, 'stock': 80, 'description': 'Slim-fit formal shirt for office and events.'},
    {'category': 'home-kitchen', 'name': 'Stainless Steel Water Bottle', 'slug': 'stainless-steel-water-bottle', 'price': 650, 'stock': 150, 'description': 'Double-wall insulated water bottle, keeps drinks hot or cold for 24 hours.'},
    {'category': 'home-kitchen', 'name': 'Non-Stick Cookware Set', 'slug': 'non-stick-cookware-set', 'price': 4500, 'discount_price': 3800, 'stock': 20, 'featured': True, 'description': '5-piece non-stick cookware set for everyday cooking.'},
    {'category': 'home-kitchen', 'name': 'LED Desk Lamp', 'slug': 'led-desk-lamp', 'price': 1200, 'stock': 70, 'description': 'Adjustable LED desk lamp with 3 brightness levels and USB charging port.'},
    {'category': 'books', 'name': 'Python Programming Guide', 'slug': 'python-programming-guide', 'price': 600, 'stock': 90, 'description': 'Comprehensive guide to Python programming for beginners and intermediate developers.'},
    {'category': 'books', 'name': 'Web Development Handbook', 'slug': 'web-development-handbook', 'price': 750, 'discount_percentage': 10, 'stock': 45, 'description': 'Learn HTML, CSS, JavaScript and Django in one book.'},
    {'category': 'sports', 'name': 'Yoga Mat Premium', 'slug': 'yoga-mat-premium', 'price': 1500, 'stock': 55, 'description': 'Extra thick non-slip yoga mat with carrying strap.'},
    {'category': 'sports', 'name': 'Adjustable Dumbbells', 'slug': 'adjustable-dumbbells', 'price': 5500, 'discount_price': 4500, 'stock': 15, 'featured': True, 'description': 'Adjustable dumbbells from 2kg to 20kg for home workouts.'},
    {'category': 'beauty', 'name': 'Moisturizing Face Cream', 'slug': 'moisturizing-face-cream', 'price': 850, 'stock': 120, 'description': 'Hydrating face cream with SPF 30 protection for all skin types.'},
    {'category': 'beauty', 'name': 'Hair Care Gift Set', 'slug': 'hair-care-gift-set', 'price': 2200, 'discount_percentage': 25, 'stock': 35, 'featured': True, 'description': 'Complete hair care set including shampoo, conditioner, and serum.'},
    {'category': 'electronics', 'name': 'Wireless Mouse', 'slug': 'wireless-mouse', 'price': 950, 'stock': 75, 'description': 'Ergonomic wireless mouse with adjustable DPI and silent clicks.'},
    {'category': 'electronics', 'name': 'Webcam HD 1080p', 'slug': 'webcam-hd-1080p', 'price': 2800, 'stock': 0, 'description': 'Full HD webcam with built-in microphone for video calls.'},
    {'category': 'home-kitchen', 'name': 'Electric Kettle', 'slug': 'electric-kettle', 'price': 1800, 'stock': 45, 'description': '1.7L electric kettle with auto shut-off and boil-dry protection.'},
]

for pd in products_data:
    cat_slug = pd.pop('category')
    pd['category'] = cats[cat_slug]
    product, created = Product.objects.get_or_create(slug=pd['slug'], defaults=pd)
    print(f"Product '{product.name}': {'Created' if created else 'Exists'}")

# 5. Flash Sale
now = timezone.now()
flash_sale, created = FlashSale.objects.get_or_create(
    title='Weekend Mega Sale',
    defaults={
        'description': 'Massive discounts on selected electronics and fashion items!',
        'discount_percentage': 25,
        'start_date': now,
        'end_date': now + timedelta(days=3),
        'is_active': True,
        'banner_color': '#ff6584',
    }
)
if created:
    # Add some products to the flash sale
    flash_products = Product.objects.filter(
        slug__in=['wireless-bluetooth-headphones', 'smart-watch-pro', 'denim-jacket', 'running-shoes', 'portable-bluetooth-speaker']
    )
    flash_sale.products.set(flash_products)
    print(f"Flash Sale '{flash_sale.title}': Created with {flash_products.count()} products")
else:
    print(f"Flash Sale '{flash_sale.title}': Already exists")

print("\n=== Seeding Complete! ===")
print("Admin login: admin / admin123")
print("Run: python manage.py runserver")
