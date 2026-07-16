from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),

    # Store Settings
    path('settings/', views.dashboard_settings, name='settings'),

    # Products
    path('products/', views.dashboard_products, name='products'),
    path('products/low-stock/', views.dashboard_low_stock, name='low_stock'),
    path('products/add/', views.dashboard_product_add, name='product_add'),
    path('products/<int:pk>/edit/', views.dashboard_product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.dashboard_product_delete, name='product_delete'),

    # Categories
    path('categories/', views.dashboard_categories, name='categories'),
    path('categories/add/', views.dashboard_category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.dashboard_category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.dashboard_category_delete, name='category_delete'),

    # Flash Sales
    path('flash-sales/', views.dashboard_flash_sales, name='flash_sales'),
    path('flash-sales/add/', views.dashboard_flash_sale_add, name='flash_sale_add'),
    path('flash-sales/<int:pk>/edit/', views.dashboard_flash_sale_edit, name='flash_sale_edit'),
    path('flash-sales/<int:pk>/delete/', views.dashboard_flash_sale_delete, name='flash_sale_delete'),

    # Orders
    path('orders/', views.dashboard_orders, name='orders'),
    path('orders/<int:pk>/', views.dashboard_order_detail, name='order_detail'),
    path('profile/', views.dashboard_profile, name='profile'),

    # Users / Customers
    path('users/', views.dashboard_users, name='users'),
    path('users/<int:pk>/', views.dashboard_user_detail, name='user_detail'),
    path('users/<int:pk>/toggle/', views.dashboard_user_toggle_status, name='user_toggle_status'),
    path('users/<int:pk>/delete/', views.dashboard_user_delete, name='user_delete'),

    # Reviews
    path('reviews/', views.dashboard_reviews, name='reviews'),
    path('reviews/<int:pk>/delete/', views.dashboard_review_delete, name='review_delete'),
]

