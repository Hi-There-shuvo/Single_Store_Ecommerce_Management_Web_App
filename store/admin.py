from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import SiteSettings, Category, Product, ProductImage, FlashSale, NewsletterSubscriber, Review


# ---- Site Settings (Singleton) ----
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for store-wide settings. Only one instance allowed."""
    fieldsets = (
        ('Branding', {
            'fields': ('store_name', 'tagline', 'logo', 'favicon'),
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address'),
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url'),
            'classes': ('collapse',),
        }),
        ('Homepage Banner', {
            'fields': ('banner_title', 'banner_subtitle'),
        }),
        ('Footer', {
            'fields': ('footer_text', 'copyright_text'),
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        if SiteSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:50px;" />', obj.logo.url)
        return '-'
    logo_preview.short_description = 'Logo Preview'


# ---- Category ----
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'product_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_editable = ['icon']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


# ---- Product Image Inline ----
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'alt_text', 'order']


# ---- Product ----
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = [
        'name', 'category', 'price', 'discount_price', 'discount_percentage',
        'final_price_display', 'stock', 'available', 'featured', 'flash_sale_status'
    ]
    list_filter = ['available', 'featured', 'category', 'discount_percentage']
    list_editable = ['price', 'discount_price', 'discount_percentage', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 20
    actions = ['make_featured', 'remove_featured', 'set_discount_10', 'set_discount_20', 'set_discount_30', 'clear_discount']

    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description', 'details', 'image'),
        }),
        ('Pricing & Discounts', {
            'fields': ('price', 'discount_price', 'discount_percentage'),
            'description': 'Set a fixed discount price OR a percentage discount. If both are set, the lower price wins.',
        }),
        ('Inventory & Visibility', {
            'fields': ('stock', 'available', 'featured'),
        }),
    )

    def final_price_display(self, obj):
        final = obj.get_final_price()
        if final < obj.price:
            return format_html(
                '<span style="color:#43e97b;font-weight:bold;">৳{}</span> '
                '<span style="text-decoration:line-through;color:#888;">৳{}</span>',
                final, obj.price
            )
        return format_html('৳{}', obj.price)
    final_price_display.short_description = 'Final Price'

    def flash_sale_status(self, obj):
        if obj.is_on_flash_sale():
            sale = obj.get_active_flash_sale()
            return format_html(
                '<span style="background:#ff6584;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">🔥 {}</span>',
                sale.title
            )
        return '-'
    flash_sale_status.short_description = 'Flash Sale'

    @admin.action(description='⭐ Mark as Featured')
    def make_featured(self, request, queryset):
        queryset.update(featured=True)

    @admin.action(description='Remove Featured')
    def remove_featured(self, request, queryset):
        queryset.update(featured=False)

    @admin.action(description='💰 Set 10% Discount')
    def set_discount_10(self, request, queryset):
        queryset.update(discount_percentage=10)

    @admin.action(description='💰 Set 20% Discount')
    def set_discount_20(self, request, queryset):
        queryset.update(discount_percentage=20)

    @admin.action(description='💰 Set 30% Discount')
    def set_discount_30(self, request, queryset):
        queryset.update(discount_percentage=30)

    @admin.action(description='Clear All Discounts')
    def clear_discount(self, request, queryset):
        queryset.update(discount_price=None, discount_percentage=0)


# ---- Flash Sale ----
@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_percentage', 'start_date', 'end_date', 'is_active', 'status_display', 'product_count']
    list_filter = ['is_active', 'start_date', 'end_date']
    list_editable = ['is_active', 'discount_percentage']
    search_fields = ['title']
    filter_horizontal = ['products']
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'discount_percentage', 'banner_color'),
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active'),
            'description': 'Set the start and end date/time for the flash sale.',
        }),
        ('Products', {
            'fields': ('products',),
            'description': 'Select which products are included in this flash sale.',
        }),
    )

    def status_display(self, obj):
        if obj.is_currently_active:
            return mark_safe('<span style="background:#43e97b;color:#000;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;">LIVE</span>')
        elif obj.has_ended:
            return mark_safe('<span style="background:#888;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">Ended</span>')
        else:
            return mark_safe('<span style="background:#ffc107;color:#000;padding:2px 8px;border-radius:10px;font-size:11px;">Upcoming</span>')
    status_display.short_description = 'Status'

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


# ---- Newsletter Subscriber ----
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']
    list_per_page = 50


# ---- Product Reviews ----
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at']
    list_per_page = 30


# ---- Customize Admin Site ----
admin.site.site_header = 'SoloStore Administration'
admin.site.site_title = 'SoloStore Admin'
admin.site.index_title = 'Store Management Dashboard'

