from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Product, Category, FlashSale, NewsletterSubscriber, Review


def home(request):
    """Homepage - shows flash sales, featured products, latest products, and categories."""
    featured_products = Product.objects.filter(featured=True, available=True)[:8]
    latest_products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()

    # Get active flash sales
    now = timezone.now()
    active_flash_sales = FlashSale.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).prefetch_related('products')

    # Get the primary flash sale (most recent active one) for the banner
    primary_flash_sale = active_flash_sales.first()
    flash_sale_products = []
    if primary_flash_sale:
        flash_sale_products = primary_flash_sale.products.filter(available=True)[:8]

    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
        'flash_sale': primary_flash_sale,
        'flash_sale_products': flash_sale_products,
    }
    return render(request, 'store/home.html', context)


def product_list(request):
    """All products with optional category filter and search."""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Search
    query = request.GET.get('q')
    if query:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(details__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    # Filter: on_sale
    on_sale = request.GET.get('sale')
    if on_sale:
        from django.db.models import Q
        products = products.filter(
            Q(discount_price__isnull=False) |
            Q(discount_percentage__gt=0) |
            Q(flash_sales__is_active=True,
              flash_sales__start_date__lte=timezone.now(),
              flash_sales__end_date__gte=timezone.now())
        ).distinct()

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    """Single product detail page with reviews and related products."""
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]

    flash_sale = product.get_active_flash_sale()
    
    # Get all reviews for this product
    reviews = product.reviews.all().select_related('user')
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    context = {
        'product': product,
        'related_products': related_products,
        'flash_sale': flash_sale,
        'reviews': reviews,
        'user_review': user_review,
    }
    return render(request, 'store/product_detail.html', context)


@require_POST
def subscribe_newsletter(request):
    """View to handle email newsletter subscriptions, supporting AJAX/HTMX."""
    email = request.POST.get('email', '').strip()
    if not email:
        message = "Please enter a valid email address."
        success = False
    else:
        try:
            validate_email(email)
            if NewsletterSubscriber.objects.filter(email=email).exists():
                message = "You are already subscribed to our newsletter!"
                success = True
            else:
                NewsletterSubscriber.objects.create(email=email)
                message = "Thank you for subscribing! Keep an eye on your inbox for exciting updates."
                success = True
        except ValidationError:
            message = "Please enter a valid email address."
            success = False

    if request.headers.get('HX-Request'):
        if success:
            return HttpResponse(
                f'<div class="newsletter-success"><i class="fas fa-check-circle"></i> {message}</div>'
            )
        else:
            return HttpResponse(
                f'<div class="newsletter-error"><i class="fas fa-exclamation-circle"></i> {message}</div>'
            )

    # Fallback for non-HTMX clients
    from django.contrib import messages
    from django.shortcuts import redirect
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect('store:home')


@login_required
@require_POST
def add_review(request, product_id):
    """View to handle submitting or updating a product review."""
    product = get_object_or_404(Product, id=product_id, available=True)
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not rating:
        from django.contrib import messages
        messages.error(request, "Please select a star rating.")
        return redirect('store:product_detail', slug=product.slug)

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        from django.contrib import messages
        messages.error(request, "Invalid rating value.")
        return redirect('store:product_detail', slug=product.slug)

    # Create or update the review
    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={'rating': rating, 'comment': comment}
    )

    from django.contrib import messages
    if created:
        messages.success(request, "Thank you! Your review has been submitted.")
    else:
        messages.success(request, "Your review has been updated successfully.")

    return redirect('store:product_detail', slug=product.slug)


