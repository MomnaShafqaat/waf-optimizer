from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ThresholdSuggestion
import pandas as pd
import numpy as np
import os
from supabase import create_client
from dotenv import load_dotenv
from io import StringIO

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

@api_view(['POST'])
def threshold_tuning_view(request):
    """
    Threshold Tuning API - Uses selected file from Supabase
    """
    try:
        # Get the selected filename from request
        selected_filename = request.data.get('filename')
        
        if not selected_filename:
            return Response(
                {"error": "No filename provided. Please select a file for analysis."},
                status=400
            )
        
        # Download file directly from Supabase storage (waf-log-files bucket)
        try:
            file_content = supabase.storage.from_("waf-log-files").download(selected_filename)
            
            if not file_content:
                return Response(
                    {"error": f"File '{selected_filename}' not found in Supabase storage"},
                    status=400
                )
                
        except Exception as e:
            return Response(
                {"error": f"Failed to download file from Supabase: {str(e)}"},
                status=400
            )
        
        # Read CSV from downloaded content
        try:
            # Convert bytes to string for pandas
            if isinstance(file_content, bytes):
                csv_content = file_content.decode('utf-8')
            else:
                csv_content = str(file_content)
            
            df = pd.read_csv(StringIO(csv_content))
            
        except Exception as e:
            return Response(
                {"error": f"Failed to parse CSV file: {str(e)}"},
                status=400
            )

        # Validate required columns
        if "anomaly_score" not in df.columns:
            return Response({"error": "Missing 'anomaly_score' column in CSV"}, status=400)

        if "action" not in df.columns:
            return Response({"error": "Missing 'action' column in CSV"}, status=400)

        # Process the data
        df["actual_label"] = df["action"].apply(
            lambda x: 1 if str(x).lower() in ["blocked", "denied", "intercepted"] else 0
        )
        df["score"] = df["anomaly_score"].astype(float)

        # Find optimal threshold
        best_threshold, best_accuracy = 0, 0
        for th in np.arange(0, 20.0, 1.0):
            df["predicted"] = (df["score"] >= th).astype(int)
            TP = ((df["actual_label"] == 1) & (df["predicted"] == 1)).sum()
            TN = ((df["actual_label"] == 0) & (df["predicted"] == 0)).sum()
            FP = ((df["actual_label"] == 0) & (df["predicted"] == 1)).sum()
            FN = ((df["actual_label"] == 1) & (df["predicted"] == 0)).sum()

            acc = (TP + TN) / (TP + TN + FP + FN + 1e-6)
            if acc > best_accuracy:
                best_accuracy, best_threshold = acc, th

        suggestion = ThresholdSuggestion.objects.create(value=best_threshold)

        return Response({
            "message": "Threshold tuning completed successfully.",
            "file_used": selected_filename,
            "best_threshold": round(best_threshold, 2),
            "accuracy": round(best_accuracy, 3),
            "records_tested": len(df),
            "saved_id": suggestion.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)

# ... (keep the other functions the same)
@api_view(['POST'])
def delete_threshold_suggestion(request, suggestion_id):
    """Delete a threshold suggestion"""
    try:
        suggestion = ThresholdSuggestion.objects.get(id=suggestion_id)
        suggestion.delete()
        return Response({"message": f"Suggestion {suggestion_id} deleted successfully."})
    except ThresholdSuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def list_threshold_suggestions(request):
    """List all threshold suggestions"""
    suggestions = ThresholdSuggestion.objects.all().order_by('-created_at')
    data = [
        {
            "id": s.id,
            "value": s.value,
            "approved": s.approved,
            "applied": s.applied,
            "created_at": s.created_at,
        }
        for s in suggestions
    ]
    return Response({"suggestions": data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def approve_threshold_suggestion(request, suggestion_id):
    """Approve and apply selected threshold"""
    try:
        suggestion = ThresholdSuggestion.objects.get(id=suggestion_id)
        suggestion.approved = True
        suggestion.applied = True
        suggestion.save()
        return Response({"message": f"Suggestion {suggestion_id} approved successfully."})

    except ThresholdSuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found."}, status=status.HTTP_404_NOT_FOUND)