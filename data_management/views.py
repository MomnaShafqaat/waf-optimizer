from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UploadedFile
from .serializers import UploadedFileSerializer

class UploadedFileViewSet(viewsets.ModelViewSet):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    parser_classes = (MultiPartParser, FormParser)  
