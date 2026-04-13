from django.urls import path
from . import views
from .billing_views import (
    admin_analytics_view,
    profit_analysis_view,
    create_pos_bill,
    search_spare_parts,
    get_low_stock_items,
    get_sales_report,
    get_top_selling_products,
    get_daily_sales,
    get_profit_analysis,
)

urlpatterns = [
    # Admin Analytics Dashboard
    path('analytics/', admin_analytics_view, name='admin_analytics'),
    
    # Profit Analysis Dashboard
    path('profit-analysis/', profit_analysis_view, name='profit_analysis'),
    
    # Billing System APIs
    path('billing/pos/create/', create_pos_bill, name='create_pos_bill'),
    path('billing/spare-parts/search/', search_spare_parts, name='search_spare_parts'),
    path('billing/reports/sales/', get_sales_report, name='sales_report'),
    path('billing/reports/daily/', get_daily_sales, name='daily_sales'),
    path('billing/reports/top-products/', get_top_selling_products, name='top_products'),
    path('billing/low-stock/', get_low_stock_items, name='low_stock_items'),
    path('billing/profit-analysis/', get_profit_analysis, name='profit_analysis_api'),
    
    # Existing routes
    path('listings/', views.listings_view, name='listings'),
    path('listings/<int:listing_id>/', views.listing_detail_view, name='listing_detail'),
    path('listings/<int:listing_id>/images/', views.add_listing_images, name='add_listing_images'),
    path('contact/', views.contact_view, name='contact'),
    path('auth/signup/', views.signup_view, name='signup'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/google/start/', views.google_oauth_start, name='google_oauth_start'),
    path('auth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),
    # Uploads
    path('upload/', views.upload_image, name='upload_image'),
    # Price Prediction
    path('price/predict/', views.price_predict, name='price_predict'),
    # Profile API
    path('profile/me/', views.profile_me, name='profile_me'),
    path('account/me/', views.account_me, name='account_me'),
    # Activities
    path('activities/', views.my_activities, name='my_activities'),
    path('activities/log/', views.log_activity, name='log_activity'),
    # Orders API
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<int:order_id>/', views.order_detail_with_bill, name='order_detail_with_bill'),
    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    # E-Bill System
    path('bills/', views.my_bills, name='my_bills'),
    path('bills/generate/<int:order_id>/', views.generate_bill, name='generate_bill'),
    path('bills/download/<int:order_id>/', views.download_bill, name='download_bill'),
    path('bills/resend/<int:order_id>/', views.resend_bill_email, name='resend_bill_email'),
    # Chatbot
    path('chat/', views.chatbot_reply, name='chatbot_reply'),
    # Damage Detection (server-side proxy)
    path('damage/detect/', views.damage_detect, name='damage_detect'),
    # Spare parts API
    path('spareparts/', views.spareparts_view, name='spareparts'),
    # Test Drive Booking
    path('testdrive/book/', views.book_test_drive, name='book_test_drive'),
    # Service/Repair Booking
    path('service/book/', views.book_service_slot, name='book_service_slot'),
]
