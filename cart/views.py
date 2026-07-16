from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from store.models import Product
from .cart import Cart


def cart_detail(request):
    """View the shopping cart."""
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


from django.http import HttpResponse, HttpResponseForbidden

@require_POST
def cart_add(request, product_id):
    """Add a product to the cart."""
    if request.user.is_authenticated and request.user.is_staff:
        return HttpResponseForbidden('Admin users cannot add items to cart.')
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    
    if request.headers.get('HX-Request'):
        cart_items_count = len(cart)
        return HttpResponse(
            f'<span class="cart-badge" id="cart-badge">{cart_items_count}</span>',
            headers={
                'HX-Trigger': '{"showMessage": "Product added to cart!"}'
            }
        )

    return redirect('cart:cart_detail')


def cart_remove(request, product_id):
    """Remove a product from the cart."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')
