from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('data_management.urls')),  # uploaded files API
    path('api/', include('waf_analysis.urls')),    # rule relationships API
]
