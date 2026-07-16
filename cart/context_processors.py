def cart_context(request):
    """Makes cart item count available in all templates for the navbar badge."""
    cart = request.session.get('cart', {})
    cart_items_count = sum(item.get('quantity', 0) for item in cart.values())
    return {'cart_items_count': cart_items_count}
