from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadedFileViewSet
from . import views

router = DefaultRouter()
router.register(r'files', UploadedFileViewSet, basename='uploadedfile')

urlpatterns = [
    path('', include(router.urls)), 
    path('files/delete/<int:file_id>/', views.delete_file, name='delete_file'), 
]
