from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('data_management.urls')),
   # path('api/', include('waf_analysis.urls')),
    path('api/', include('rule_analysis.urls')),
    path('api/', include('false_positive_reduction.urls')),
    path('api/threshold_tuning/', threshold_tuning_view),
 
    path('', include('threshold_tuning.urls')),
    path('api/', include('threshold_tuning.urls')),


]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
