from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from django.template.loader import render_to_string
from store.models import Product, ProductImage, Category, SiteSettings, FlashSale
from .forms import ProductForm, CategoryForm, SiteSettingsForm, FlashSaleForm
from orders.models import Order


# ─── DRY Helpers ───────────────────────────────────────────────────────

def _handle_form(request, form_class, template, success_url, success_msg,
                 instance=None, title='', extra_context=None, files=False):
    """Reusable handler for add/edit form views. Eliminates repetitive CRUD code."""
    form_kwargs = {'instance': instance} if instance else {}
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES if files else None, **form_kwargs)
        if form.is_valid():
            form.save()
            messages.success(request, success_msg)
            return redirect(success_url)
    else:
        form = form_class(**form_kwargs)
    context = {'form': form, 'title': title}
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)


def _handle_delete(request, model_class, pk, success_url, type_name):
    """Reusable handler for delete views — supports both HTMX and regular requests."""
    obj = get_object_or_404(model_class, pk=pk)
    if request.method == 'POST':
        name = str(obj)
        obj.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Trigger': '{"showMessage": "' + f'{type_name} \\"{name}\\" deleted!' + '", "refreshTable": "true"}',
                    'HX-Redirect': success_url,
                }
            )
        messages.success(request, f'{type_name} "{name}" deleted!')
        return redirect(success_url)
    return render(request, 'dashboard/confirm_delete.html', {
        'obj': obj, 'type': type_name, 'back_url': success_url,
    })


# ─── Dashboard Home ───────────────────────────────────────────────────

@staff_member_required
def dashboard_home(request):
    from decimal import Decimal
    from orders.models import OrderItem

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    recent_orders = Order.objects.all()[:10]

    # Valid orders for financial calculations
    valid_orders = Order.objects.filter(status__in=['processing', 'shipped', 'delivered'])

    # Net Revenue
    net_revenue = valid_orders.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

    # Net Expense (Sum of cost * quantity for all OrderItems of valid orders)
    net_expense = OrderItem.objects.filter(order__in=valid_orders).aggregate(
        total=Sum(F('product__cost') * F('quantity'))
    )['total'] or Decimal('0.00')

    # Net Profit
    net_profit = net_revenue - net_expense

    # Profit Margin
    profit_margin = round((net_profit / net_revenue) * 100, 1) if net_revenue > 0 else Decimal('0.0')

    # Most Selling Product
    most_sold_product = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity', filter=Q(orderitem__order__in=valid_orders))
    ).filter(total_sold__gt=0).order_by('-total_sold').first()

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'net_revenue': net_revenue,
        'net_expense': net_expense,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'most_sold_product': most_sold_product,
    }
    return render(request, 'dashboard/index.html', context)



# ─── Store Settings ───────────────────────────────────────────────────

@staff_member_required
def dashboard_settings(request):
    settings_obj = SiteSettings.load()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store settings updated successfully!')
            return redirect('dashboard:settings')
    else:
        form = SiteSettingsForm(instance=settings_obj)
    return render(request, 'dashboard/settings.html', {'form': form, 'settings_obj': settings_obj})


# ─── Products ─────────────────────────────────────────────────────────

@staff_member_required
def dashboard_products(request):
    products = Product.objects.select_related('category').all()
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    if request.headers.get('HX-Request') and request.GET.get('partial'):
        return render(request, 'dashboard/partials/product_table.html', {'products': products})
    return render(request, 'dashboard/products.html', {'products': products, 'query': query})


@staff_member_required
def dashboard_low_stock(request):
    """View listing products with low stock (stock <= 2)."""
    products = Product.objects.select_related('category').filter(stock__lte=2)
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    context = {
        'products': products,
        'query': query,
        'is_low_stock': True,
        'title': 'Low Stock Alerts',
    }
    return render(request, 'dashboard/products.html', context)


@staff_member_required
def dashboard_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            # Handle extra images
            for img in request.FILES.getlist('extra_images'):
                ProductImage.objects.create(product=product, image=img)
            messages.success(request, 'Product added successfully!')
            return redirect('dashboard:products')
    else:
        form = ProductForm()
    return render(request, 'dashboard/product_form.html', {'form': form, 'title': 'Add Product'})


@staff_member_required
def dashboard_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            # Delete checked images
            delete_ids = request.POST.getlist('delete_images')
            if delete_ids:
                ProductImage.objects.filter(id__in=delete_ids, product=product).delete()
            # Handle new extra images
            for img in request.FILES.getlist('extra_images'):
                ProductImage.objects.create(product=product, image=img)
            messages.success(request, f'Product "{product.name}" updated!')
            return redirect('dashboard:products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/product_form.html', {
        'form': form, 'title': 'Edit Product', 'product': product,
    })


@staff_member_required
def dashboard_product_delete(request, pk):
    return _handle_delete(request, Product, pk, 'dashboard:products', 'Product')


# ─── Categories ───────────────────────────────────────────────────────

@staff_member_required
def dashboard_categories(request):
    categories = Category.objects.annotate(product_count=Count('products')).all()
    query = request.GET.get('q', '').strip()
    if query:
        categories = categories.filter(name__icontains=query)
    if request.headers.get('HX-Request') and request.GET.get('partial'):
        return render(request, 'dashboard/partials/category_table.html', {'categories': categories})
    return render(request, 'dashboard/categories.html', {'categories': categories, 'query': query})


@staff_member_required
def dashboard_category_add(request):
    return _handle_form(
        request, CategoryForm, 'dashboard/category_form.html',
        'dashboard:categories', 'Category added successfully!',
        title='Add Category', files=True,
    )


@staff_member_required
def dashboard_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return _handle_form(
        request, CategoryForm, 'dashboard/category_form.html',
        'dashboard:categories', f'Category "{category.name}" updated!',
        instance=category, title='Edit Category', files=True,
        extra_context={'category': category},
    )


@staff_member_required
def dashboard_category_delete(request, pk):
    return _handle_delete(request, Category, pk, 'dashboard:categories', 'Category')


# ─── Flash Sales ──────────────────────────────────────────────────────

@staff_member_required
def dashboard_flash_sales(request):
    flash_sales = FlashSale.objects.prefetch_related('products').all()
    if request.headers.get('HX-Request') and request.GET.get('partial'):
        return render(request, 'dashboard/partials/flash_sale_table.html', {'flash_sales': flash_sales})
    return render(request, 'dashboard/flash_sales.html', {'flash_sales': flash_sales})


@staff_member_required
def dashboard_flash_sale_add(request):
    return _handle_form(
        request, FlashSaleForm, 'dashboard/flash_sale_form.html',
        'dashboard:flash_sales', 'Flash sale created!',
        title='Create Flash Sale',
    )


@staff_member_required
def dashboard_flash_sale_edit(request, pk):
    sale = get_object_or_404(FlashSale, pk=pk)
    return _handle_form(
        request, FlashSaleForm, 'dashboard/flash_sale_form.html',
        'dashboard:flash_sales', f'Flash sale "{sale.title}" updated!',
        instance=sale, title='Edit Flash Sale',
        extra_context={'sale': sale},
    )


@staff_member_required
def dashboard_flash_sale_delete(request, pk):
    return _handle_delete(request, FlashSale, pk, 'dashboard:flash_sales', 'Flash Sale')


# ─── Orders Management ───────────────────────────────────────────────

@staff_member_required
def dashboard_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    query = request.GET.get('q', '').strip()
    if query:
        order_q = Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
        if query.isdigit():
            order_q |= Q(id=int(query))
        orders = orders.filter(order_q).distinct()
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
        'query': query,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/partials/order_table.html', context)
    return render(request, 'dashboard/orders.html', context)


@staff_member_required
def dashboard_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            if request.headers.get('HX-Request'):
                return render(request, 'dashboard/partials/order_status.html', {
                    'order': order, 'status_choices': Order.STATUS_CHOICES,
                })
            messages.success(request, f'Order #{order.id} status changed to {order.get_status_display()}.')
            return redirect('dashboard:order_detail', pk=order.pk)
    return render(request, 'dashboard/order_detail.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    })


@staff_member_required
def dashboard_profile(request):
    user = request.user
    from accounts.forms import UserUpdateForm, ProfileUpdateForm
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your admin profile has been updated successfully!')
            return redirect('dashboard:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=user.profile)

    return render(request, 'dashboard/profile.html', {
        'user': user,
        'user_form': user_form,
        'profile_form': profile_form,
    })


@staff_member_required
def dashboard_users(request):
    """View to list all store users with their spending stats and status."""
    from django.contrib.auth.models import User
    
    users = User.objects.annotate(
        total_spent=Sum('orders__total_price', filter=Q(orders__status__in=['processing', 'shipped', 'delivered'])),
        order_count=Count('orders', distinct=True)
    ).order_by('-date_joined')
    
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # Most purchased user (highest total_spent)
    most_purchased_user = User.objects.annotate(
        total_spent=Sum('orders__total_price', filter=Q(orders__status__in=['processing', 'shipped', 'delivered']))
    ).filter(total_spent__gt=0).order_by('-total_spent').first()

    context = {
        'users': users,
        'query': query,
        'most_purchased_user': most_purchased_user,
    }
    return render(request, 'dashboard/users.html', context)


@staff_member_required
def dashboard_user_detail(request, pk):
    """View user details including profile information and all order history."""
    from django.contrib.auth.models import User
    user_obj = get_object_or_404(User, pk=pk)
    user_orders = user_obj.orders.all().prefetch_related('items__product')
    
    # Financial metrics for this specific user
    from decimal import Decimal
    valid_orders = user_orders.filter(status__in=['processing', 'shipped', 'delivered'])
    total_spent = valid_orders.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    
    context = {
        'user_obj': user_obj,
        'user_orders': user_orders,
        'total_spent': total_spent,
    }
    return render(request, 'dashboard/user_detail.html', context)


@staff_member_required
def dashboard_user_toggle_status(request, pk):
    """View to toggle user active status (disable/enable user account)."""
    from django.contrib.auth.models import User
    user_obj = get_object_or_404(User, pk=pk)
    
    if user_obj == request.user:
        messages.error(request, "You cannot disable your own admin account.")
        return redirect('dashboard:user_detail', pk=pk)
    
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    
    status_str = "activated" if user_obj.is_active else "disabled"
    messages.success(request, f'User account "{user_obj.username}" has been successfully {status_str}.')
    return redirect('dashboard:user_detail', pk=pk)


@staff_member_required
def dashboard_user_delete(request, pk):
    """View to handle deleting a user account."""
    from django.contrib.auth.models import User
    from django.urls import reverse
    user_obj = get_object_or_404(User, pk=pk)
    
    if user_obj == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('dashboard:users')
    
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'User account "{username}" has been deleted successfully.')
        return redirect('dashboard:users')
        
    return render(request, 'dashboard/confirm_delete.html', {
        'obj': user_obj,
        'type': 'User Account',
        'back_url': reverse('dashboard:users'),
    })


@staff_member_required
def dashboard_reviews(request):
    """View to list and manage customer reviews globally."""
    from store.models import Review
    reviews = Review.objects.select_related('user', 'product').all()
    
    query = request.GET.get('q', '').strip()
    if query:
        reviews = reviews.filter(
            Q(user__username__icontains=query) |
            Q(product__name__icontains=query) |
            Q(comment__icontains=query)
        )
        
    context = {
        'reviews': reviews,
        'query': query,
    }
    return render(request, 'dashboard/reviews.html', context)


@staff_member_required
def dashboard_review_delete(request, pk):
    """View to delete a customer review."""
    from store.models import Review
    from django.urls import reverse
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        product_name = review.product.name
        reviewer = review.user.username
        review.delete()
        messages.success(request, f'Review by "{reviewer}" on "{product_name}" has been deleted successfully.')
        return redirect('dashboard:reviews')
        
    return render(request, 'dashboard/confirm_delete.html', {
        'obj': review,
        'type': 'Customer Review',
        'back_url': reverse('dashboard:reviews'),
    })



