from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ThresholdSuggestion
import pandas as pd
import numpy as np
import os


@api_view(['GET'])
def threshold_tuning_view(request):
    """
    Threshold Tuning API
    Reads data/traffic.csv → finds best threshold → saves to DB
    """
    try:
        file_path = os.path.join("data", "traffic.csv")
        if not os.path.exists(file_path):
            return Response({"error": "traffic.csv not found in data/"}, status=400)

        df = pd.read_csv(file_path)
        if "score" not in df.columns or "actual_label" not in df.columns:
            return Response({"error": "CSV must have 'score' and 'actual_label' columns"}, status=400)

        best_threshold, best_accuracy = 0, 0
        for th in np.arange(0, 1.0, 0.05):
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
            "best_threshold": round(best_threshold, 2),
            "accuracy": round(best_accuracy, 3),
            "records_tested": len(df),
            "saved_id": suggestion.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)


# 🔹 Add these below your existing function

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
    """Approve and optionally mark as applied"""
    try:
        suggestion = ThresholdSuggestion.objects.get(id=suggestion_id)
        suggestion.approved = True
        suggestion.save()
        return Response({"message": f"Suggestion {suggestion_id} approved successfully."})
    except ThresholdSuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found."}, status=status.HTTP_404_NOT_FOUND)

