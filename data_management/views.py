from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import UploadedFile

class UploadedFileViewSet(viewsets.ModelViewSet):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    parser_classes = (MultiPartParser, FormParser)

@api_view(['DELETE'])
def delete_file(request, file_id):
    """Delete a file by ID"""
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    # Optional: also delete the actual file from storage
    file_path = file_obj.file.path
    file_obj.delete()

    # Remove file from filesystem if needed
    import os
    if os.path.exists(file_path):
        os.remove(file_path)

    return Response({"message": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT)