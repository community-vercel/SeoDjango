from django.urls import path, include  # instead of 'url' from django.conf.urls
from .import views
from .views import ProfessionalWebCrawlAPIView, WebsiteViewSet,WebsiteViewSets,CrawlHistoryAPIView

urlpatterns = [
    # path('websites/<int:pk>/verify/', verify_website, name='website-verify'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('add-websites/', views.add_website, name='add_website'),
    path('get-websites/', views.get_websites, name='get_websites'),
    path('update-websites/<int:website_id>/', views.update_website, name='update_website'),
    path('get-websites/<int:website_id>/', views.get_website, name='get_website'),
    path('delete-websites/<int:website_id>/', views.delete_website, name='delete_website'),
    path('crawl-websites/<int:website_id>/crawl/', ProfessionalWebCrawlAPIView.as_view(), name='web-crawl'),
    path('seo-websites/<int:pk>/lighthouse/', WebsiteViewSet.as_view({'get': 'lighthouse'}), name='website-lighthouse'),
    path('audit-websites/<int:pk>/audit/', WebsiteViewSets.as_view({'get': 'seo_audit'}), name='seo_audit'),
    path('crawl-history/<int:website_id>/', views.get_history, name='crawl-history'),
    path('seo-dashwebsites/<int:website_id>/', views.get_latest_lighthouse_reports, name='delete_website'),

    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('dj_rest_auth.urls')),  # Ensure this is dj_rest_auth
    path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
]
