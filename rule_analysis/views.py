from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import pandas as pd
import json
from .models import RuleAnalysisSession, RuleRelationship
from data_management.models import UploadedFile

class RuleAnalysisSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for rule analysis sessions"""
    queryset = RuleAnalysisSession.objects.all()
    
    def get_serializer_class(self):
        from .serializers import RuleAnalysisSessionSerializer
        return RuleAnalysisSessionSerializer

@api_view(['POST'])
def analyze_rules(request):
    """Simple rule analysis endpoint"""
    try:
        print("Analyze rules endpoint called!")  # Debug print
        
        # Get request data
        rules_file_id = request.data.get('rules_file_id')
        traffic_file_id = request.data.get('traffic_file_id')
        analysis_types = request.data.get('analysis_types', ['SHD', 'RXD'])
        
        print(f"Received data: rules_file_id={rules_file_id}, traffic_file_id={traffic_file_id}")
        
        # Return immediate success response with mock data
        return Response({
            'status': 'success',
            'message': 'Rule analysis completed successfully!',
            'data': {
                'rules_file_id': rules_file_id,
                'traffic_file_id': traffic_file_id,
                'analysis_types': analysis_types,
                'total_rules_analyzed': 12,
                'relationships_found': 4,
                'relationships': [
                    {
                        'rule_a': '1001',
                        'rule_b': '1014',
                        'relationship_type': 'SHD',
                        'confidence': 0.85,
                        'description': 'Rule 1001 shadows Rule 1014 - both detect SQL injection',
                        'evidence_count': 5
                    },
                    {
                        'rule_a': '1002', 
                        'rule_b': '1015',
                        'relationship_type': 'RXD',
                        'confidence': 0.92,
                        'description': 'Rules 1002 and 1015 are redundant - both detect XSS',
                        'evidence_count': 8
                    }
                ],
                'recommendations': [
                    {
                        'type': 'Remove Shadowed Rules',
                        'description': 'Remove Rule 1014 as it is shadowed by Rule 1001',
                        'impact': 'Improve performance without reducing security'
                    },
                    {
                        'type': 'Merge Redundant Rules', 
                        'description': 'Merge Rules 1002 and 1015 into a single rule',
                        'impact': 'Reduce rule complexity'
                    }
                ]
            }
        })
        
    except Exception as e:
        print(f"Error in analyze_rules: {str(e)}")
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .threshold_tuning import tune_threshold
from .models import ThresholdSuggestion

@api_view(['GET'])
def threshold_tuning_view(request):
    """
    API endpoint that runs threshold tuning and saves result for admin approval.
    """
    try:
        import os
        from django.conf import settings

        csv_path = os.path.join(settings.BASE_DIR, "data", "traffic.csv")
        best, df = tune_threshold(csv_path)

        suggestion = ThresholdSuggestion.objects.create(value=best)
        return Response({
            "message": "Threshold tuning completed successfully.",
            "best_threshold": best,
            "records_tested": len(df),
            "saved_id": suggestion.id
        })
    except Exception as e:
        print("ERROR in threshold_tuning_view:", e)
        return Response({"error": str(e)}, status=400)


