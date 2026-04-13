from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from core.views import sell_car_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Website pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('index.html', TemplateView.as_view(template_name='index.html')),
    path('shop/', TemplateView.as_view(template_name='shop.html'), name='shop'),
    path('shop.html', TemplateView.as_view(template_name='shop.html')),
    path('shop/index.html', RedirectView.as_view(url='/shop/', permanent=False)),
    path('car/<int:listing_id>/', TemplateView.as_view(template_name='car-detail.html'), name='car_detail'),
    path('sell-car/', sell_car_page, name='sell_car'),
    path('sell-car.html', sell_car_page),
    path('sell-car/index.html', RedirectView.as_view(url='/sell-car/', permanent=False)),
    path('spare-parts/', TemplateView.as_view(template_name='spare-parts.html'), name='spare_parts'),
    path('spare-parts.html', TemplateView.as_view(template_name='spare-parts.html')),
    path('spare-parts/index.html', RedirectView.as_view(url='/spare-parts/', permanent=False)),
    path('checkout/', TemplateView.as_view(template_name='checkout.html'), name='checkout'),
    path('assess-damage/', TemplateView.as_view(template_name='assess-damage.html'), name='assess_damage'),
    path('assess-damage.html', TemplateView.as_view(template_name='assess-damage.html')),
    path('assess-damage/index.html', RedirectView.as_view(url='/assess-damage/', permanent=False)),
    path('damage-detection/', TemplateView.as_view(template_name='damage-detection.html'), name='damage_detection'),
    path('damage-detection.html', TemplateView.as_view(template_name='damage-detection.html')),
    path('damage-detection/index.html', RedirectView.as_view(url='/damage-detection/', permanent=False)),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('about.html', TemplateView.as_view(template_name='about.html')),
    path('about/index.html', RedirectView.as_view(url='/about/', permanent=False)),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('contact.html', TemplateView.as_view(template_name='contact.html')),
    path('contact/index.html', RedirectView.as_view(url='/contact/', permanent=False)),
    path('help/', TemplateView.as_view(template_name='help.html'), name='help'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('warranty/', TemplateView.as_view(template_name='warranty.html'), name='warranty'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('privacy.html', TemplateView.as_view(template_name='privacy.html')),
    path('privacy/index.html', RedirectView.as_view(url='/privacy/', permanent=False)),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('terms.html', TemplateView.as_view(template_name='terms.html')),
    path('terms/index.html', RedirectView.as_view(url='/terms/', permanent=False)),
    path('cookie-policy/', TemplateView.as_view(template_name='cookie-policy.html'), name='cookie_policy'),
    path('cookie-policy.html', TemplateView.as_view(template_name='cookie-policy.html')),
    path('cookie-policy/index.html', RedirectView.as_view(url='/cookie-policy/', permanent=False)),
    # Login and Signup pages
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('login.html', TemplateView.as_view(template_name='login.html')),
    path('login/index.html', RedirectView.as_view(url='/login/', permanent=False)),
    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('signup.html', TemplateView.as_view(template_name='signup.html')),
    path('signup/index.html', RedirectView.as_view(url='/signup/', permanent=False)),
    path('account/', TemplateView.as_view(template_name='account.html'), name='account'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('settings/', TemplateView.as_view(template_name='settings.html'), name='settings'),
    path('orders/', TemplateView.as_view(template_name='orders.html'), name='orders'),
    path('account.html', TemplateView.as_view(template_name='account.html')),
    path('account/index.html', RedirectView.as_view(url='/account/', permanent=False)),
    
    # Admin Analytics Dashboard
    path('analytics/', TemplateView.as_view(template_name='admin-analytics.html'), name='analytics'),
    
    # Profit Analysis Dashboard
    path('profit-analysis/', TemplateView.as_view(template_name='profit-analysis.html'), name='profit_analysis'),
    
    # OAuth Test Page
    path('oauth-test/', TemplateView.as_view(template_name='oauth-test.html'), name='oauth_test'),

    # Admin and (optional) API
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]

# Serve uploaded media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
