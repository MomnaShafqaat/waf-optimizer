from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from supabase_client import supabase

@method_decorator(csrf_exempt, name='dispatch')
class UploadedFileViewSet(viewsets.ModelViewSet):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Upload file directly to Supabase Storage"""
        file_obj = request.FILES.get("file")
        file_type = request.data.get("file_type")

        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # FIX: Determine the correct Supabase bucket based on file type
            if file_type == 'rules':
                bucket_name = "waf-rule-files"
            elif file_type == 'traffic':
                bucket_name = "waf-log-files"
            else:
                return Response({"error": "Invalid file type. Use 'rules' or 'traffic'"}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Upload file content to the correct Supabase Storage bucket
            file_content = file_obj.read()
            supabase.storage.from_(bucket_name).upload(file_obj.name, file_content)

            # Save metadata in Django DB
            uploaded_file = UploadedFile.objects.create(
                filename=file_obj.name,
                file_type=file_type,
                file_size=file_obj.size,
                supabase_path=file_obj.name
            )

            serializer = self.get_serializer(uploaded_file)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@csrf_exempt
def delete_file(request, file_id):
    """Delete a file from Supabase Storage and Django DB by ID"""
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    try:
        # Determine the correct bucket for deletion based on file type
        if file_obj.file_type == 'rules':
            bucket_name = "waf-rule-files"
        elif file_obj.file_type == 'traffic':
            bucket_name = "waf-traffic-files"  # or "waf-log-files" if you renamed it
        else:
            bucket_name = "waf-csv-files"  # fallback

        # Delete from the correct Supabase bucket
        supabase.storage.from_(bucket_name).remove([file_obj.supabase_path])

        # Delete metadata from DB
        file_obj.delete()
        return Response({"message": "File deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@csrf_exempt
def delete_file_by_name(request):
    """Delete a file from Supabase Storage by filename (without database record)"""
    try:
        filename = request.data.get('filename')
        file_type = request.data.get('file_type')  # 'rules' or 'traffic'

        if not filename:
            return Response({"error": "filename is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not file_type:
            return Response({"error": "file_type is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine the correct bucket for deletion based on file type
        if file_type == 'rules':
            bucket_name = "waf-rule-files"
        elif file_type == 'traffic' or file_type == 'logs':  # Support both 'traffic' and 'logs' types
            bucket_name = "waf-traffic-files"  # or "waf-log-files" if you renamed it
        else:
            return Response({"error": f"Invalid file_type: {file_type}"}, status=status.HTTP_400_BAD_REQUEST)

        # Delete from the correct Supabase bucket
        result = supabase.storage.from_(bucket_name).remove([filename])
        
        # Check if deletion was successful
        if hasattr(result, 'error') and result.error:
            return Response({"error": f"Supabase deletion failed: {result.error.message}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Also try to delete from database if the file exists there
        try:
            file_obj = UploadedFile.objects.get(filename=filename, file_type=file_type)
            file_obj.delete()
            db_message = " and database record"
        except UploadedFile.DoesNotExist:
            db_message = " (Supabase-only file)"

        return Response({
            "message": f"File '{filename}' deleted successfully from {bucket_name}{db_message}"
        }, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)