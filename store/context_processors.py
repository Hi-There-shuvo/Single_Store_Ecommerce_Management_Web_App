from .models import SiteSettings


def site_settings(request):
    """Makes store settings available in all templates."""
    try:
        settings = SiteSettings.load()
    except Exception:
        settings = None

    # Calculate low stock count for staff/admin users (threshold is 2)
    low_stock_count = 0
    if request.user.is_authenticated and request.user.is_staff:
        from .models import Product
        low_stock_count = Product.objects.filter(stock__lte=2).count()

    return {
        'site_settings': settings,
        'low_stock_count': low_stock_count,
    }
