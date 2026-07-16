from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.order_list, name='order_list'),
    path('payment/success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment/cancel/<int:order_id>/', views.payment_cancel, name='payment_cancel'),
    path('payment/retry/<int:order_id>/', views.retry_payment, name='retry_payment'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
