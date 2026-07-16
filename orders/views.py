from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm
from stripe import StripeClient
import json

# Initialize Stripe client (v15+ pattern)
stripe_client = StripeClient(settings.STRIPE_SECRET_KEY)


@login_required
def order_create(request):
    """Checkout page - create an order from the cart."""
    if request.user.is_staff:
        messages.error(request, 'Admin users cannot place orders.')
        return redirect('store:home')
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:home')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()

            # Build line items for both DB and Stripe
            line_items = []
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                line_items.append({
                    'price_data': {
                        'currency': 'bdt',
                        'product_data': {
                            'name': item['product'].name,
                        },
                        'unit_amount': int(float(item['price']) * 100),
                    },
                    'quantity': item['quantity'],
                })

            cart.clear()

            # Route based on payment method
            if order.payment_method == 'online':
                try:
                    session = stripe_client.checkout.sessions.create(
                        params={
                            'payment_method_types': ['card'],
                            'line_items': line_items,
                            'mode': 'payment',
                            'metadata': {'order_id': str(order.id)},
                            'success_url': request.build_absolute_uri(
                                reverse('orders:payment_success', args=[order.id])
                            ) + '?session_id={CHECKOUT_SESSION_ID}',
                            'cancel_url': request.build_absolute_uri(
                                reverse('orders:payment_cancel', args=[order.id])
                            ),
                        }
                    )
                    # Save the Stripe session ID on the order
                    order.stripe_session_id = session.id
                    order.save()
                    return redirect(session.url, code=303)
                except Exception as e:
                    messages.error(request, f'Payment error: {str(e)}. Please try again.')
                    return redirect('orders:order_detail', order_id=order.id)
            else:
                # Cash on Delivery
                messages.success(request, f'Order #{order.id} placed! Pay on delivery.')
                return redirect('orders:order_detail', order_id=order.id)
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = OrderCreateForm(initial=initial)

    return render(request, 'orders/order_create.html', {
        'cart': cart,
        'form': form,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
def payment_success(request, order_id):
    """Handle return from Stripe after successful payment."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Verify payment with Stripe before marking as paid
    session_id = request.GET.get('session_id', '')
    if session_id and order.stripe_session_id:
        try:
            session = stripe_client.checkout.sessions.retrieve(order.stripe_session_id)
            if session.payment_status == 'paid' and session.id == order.stripe_session_id:
                order.paid = True
                order.status = 'processing'
                order.save()
                messages.success(request, f'Payment successful! Order #{order.id} has been confirmed.')
            else:
                messages.warning(request, 'Payment verification pending. We will update your order shortly.')
        except Exception:
            messages.warning(request, 'Payment verification pending. We will update your order shortly.')
    elif not order.paid:
        messages.info(request, 'Your order has been placed. Payment status will be updated shortly.')

    return redirect('orders:order_detail', order_id=order.id)


@login_required
def payment_cancel(request, order_id):
    """Handle return from Stripe when user cancels payment."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Don't cancel the order — let the user retry
    messages.warning(request, f'Payment was cancelled for Order #{order.id}. You can retry payment below.')
    return redirect('orders:order_detail', order_id=order.id)


@login_required
def retry_payment(request, order_id):
    """Create a new Stripe Checkout Session for an unpaid online order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.paid:
        messages.info(request, 'This order has already been paid.')
        return redirect('orders:order_detail', order_id=order.id)

    if order.payment_method != 'online':
        messages.warning(request, 'This order uses Cash on Delivery.')
        return redirect('orders:order_detail', order_id=order.id)

    # Build line items from existing order items
    line_items = []
    for item in order.items.all():
        line_items.append({
            'price_data': {
                'currency': 'bdt',
                'product_data': {
                    'name': item.product.name,
                },
                'unit_amount': int(item.price * 100),
            },
            'quantity': item.quantity,
        })

    try:
        session = stripe_client.checkout.sessions.create(
            params={
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'payment',
                'metadata': {'order_id': str(order.id)},
                'success_url': request.build_absolute_uri(
                    reverse('orders:payment_success', args=[order.id])
                ) + '?session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': request.build_absolute_uri(
                    reverse('orders:payment_cancel', args=[order.id])
                ),
            }
        )
        order.stripe_session_id = session.id
        order.save()
        return redirect(session.url, code=303)
    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('orders:order_detail', order_id=order.id)


@csrf_exempt
def stripe_webhook(request):
    """Stripe webhook endpoint for secure payment verification."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if webhook_secret:
        # Verify webhook signature if secret is configured
        try:
            from stripe import Webhook
            event = Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            return HttpResponse(status=400)
        except Exception:
            return HttpResponse(status=400)
    else:
        # No webhook secret configured — parse the event directly (dev mode)
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event.get('type') == 'checkout.session.completed':
        session_data = event['data']['object']
        session_id = session_data.get('id', '')

        try:
            order = Order.objects.get(stripe_session_id=session_id)
            if session_data.get('payment_status') == 'paid':
                order.paid = True
                order.status = 'processing'
                order.save()
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
def order_detail(request, order_id):
    """View a single order's details."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_list(request):
    """List all orders for the logged-in user."""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})
