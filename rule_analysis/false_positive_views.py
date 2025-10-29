from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from .models import (
    RuleAnalysisSession, FalsePositiveDetection, WhitelistSuggestion, 
    LearningModeSession, WhitelistExport
)
from data_management.models import UploadedFile

class FalsePositiveDetectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing false positive detections"""
    queryset = FalsePositiveDetection.objects.all()
    
    def get_serializer_class(self):
        from .serializers import FalsePositiveDetectionSerializer
        return FalsePositiveDetectionSerializer

@api_view(['POST'])
def detect_false_positives(request):
    """
    FR04-01: Detect rules that repeatedly block legitimate requests (false positives)
    """
    try:
        session_id = request.data.get('session_id')
        detection_method = request.data.get('detection_method', 'manual')
        threshold = request.data.get('false_positive_threshold', 0.1)  # 10% threshold
        
        session = get_object_or_404(RuleAnalysisSession, id=session_id)
        
        # Load traffic data to analyze false positives
        traffic_file = session.traffic_file
        traffic_df = pd.read_csv(traffic_file.file.path)
        
        # Mock analysis - in real implementation, this would analyze actual traffic
        false_positives_detected = []
        
        # Simulate false positive detection based on traffic patterns
        for rule_id in ['1001', '1002', '1003', '1005']:  # Sample rule IDs
            # Mock data for demonstration
            false_positive_count = 15
            legitimate_request_count = 100
            false_positive_rate = false_positive_count / legitimate_request_count
            
            if false_positive_rate > threshold:
                # Create or update false positive detection
                fp_detection, created = FalsePositiveDetection.objects.get_or_create(
                    rule_id=rule_id,
                    session=session,
                    defaults={
                        'false_positive_count': false_positive_count,
                        'legitimate_request_count': legitimate_request_count,
                        'false_positive_rate': false_positive_rate,
                        'detection_method': detection_method,
                        'confidence_score': 0.85,
                        'blocked_requests': [
                            {
                                'timestamp': '2024-01-15 10:30:00',
                                'ip_address': '192.168.1.100',
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                                'request_path': '/api/users/profile',
                                'request_method': 'GET',
                                'reason': 'Legitimate user profile request blocked'
                            }
                        ],
                        'request_patterns': {
                            'common_paths': ['/api/users/profile', '/api/dashboard'],
                            'common_user_agents': ['Mozilla/5.0 (Windows NT 10.0; Win64; x64)'],
                            'common_ips': ['192.168.1.100', '192.168.1.101']
                        }
                    }
                )
                
                if not created:
                    # Update existing detection
                    fp_detection.false_positive_count = false_positive_count
                    fp_detection.legitimate_request_count = legitimate_request_count
                    fp_detection.false_positive_rate = false_positive_rate
                    fp_detection.updated_at = datetime.now()
                    fp_detection.save()
                
                false_positives_detected.append({
                    'rule_id': rule_id,
                    'false_positive_count': false_positive_count,
                    'false_positive_rate': false_positive_rate,
                    'status': fp_detection.status,
                    'detection_method': detection_method
                })
        
        return Response({
            'status': 'success',
            'message': f'False positive detection completed. Found {len(false_positives_detected)} rules with high false positive rates.',
            'data': {
                'session_id': session_id,
                'detection_method': detection_method,
                'threshold_used': threshold,
                'false_positives_detected': false_positives_detected,
                'total_rules_analyzed': 4,
                'high_false_positive_rules': len(false_positives_detected)
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'False positive detection failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def generate_whitelist_suggestions(request):
    """
    FR04-02: Suggest whitelisting patterns or conditions to reduce false positives
    """
    try:
        false_positive_id = request.data.get('false_positive_id')
        suggestion_types = request.data.get('suggestion_types', ['ip_whitelist', 'path_whitelist'])
        
        fp_detection = get_object_or_404(FalsePositiveDetection, id=false_positive_id)
        
        suggestions = []
        
        # Generate suggestions based on detected patterns
        for suggestion_type in suggestion_types:
            if suggestion_type == 'ip_whitelist':
                # Suggest IP whitelist based on common legitimate IPs
                common_ips = fp_detection.request_patterns.get('common_ips', [])
                if common_ips:
                    suggestion = WhitelistSuggestion.objects.create(
                        false_positive=fp_detection,
                        suggestion_type='ip_whitelist',
                        pattern_description=f'Whitelist IP addresses: {", ".join(common_ips[:5])}',
                        pattern_conditions={'ip_addresses': common_ips[:5]},
                        estimated_false_positive_reduction=60.0,
                        security_risk_assessment='low',
                        implementation_priority='high'
                    )
                    suggestions.append({
                        'id': suggestion.id,
                        'type': suggestion_type,
                        'description': suggestion.pattern_description,
                        'estimated_reduction': suggestion.estimated_false_positive_reduction,
                        'risk_assessment': suggestion.security_risk_assessment
                    })
            
            elif suggestion_type == 'path_whitelist':
                # Suggest path whitelist based on common legitimate paths
                common_paths = fp_detection.request_patterns.get('common_paths', [])
                if common_paths:
                    suggestion = WhitelistSuggestion.objects.create(
                        false_positive=fp_detection,
                        suggestion_type='path_whitelist',
                        pattern_description=f'Whitelist paths: {", ".join(common_paths)}',
                        pattern_regex=f"^({'|'.join(common_paths)})$",
                        pattern_conditions={'paths': common_paths},
                        estimated_false_positive_reduction=40.0,
                        security_risk_assessment='medium',
                        implementation_priority='medium'
                    )
                    suggestions.append({
                        'id': suggestion.id,
                        'type': suggestion_type,
                        'description': suggestion.pattern_description,
                        'estimated_reduction': suggestion.estimated_false_positive_reduction,
                        'risk_assessment': suggestion.security_risk_assessment
                    })
        
        return Response({
            'status': 'success',
            'message': f'Generated {len(suggestions)} whitelist suggestions for rule {fp_detection.rule_id}',
            'data': {
                'false_positive_id': false_positive_id,
                'rule_id': fp_detection.rule_id,
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Whitelist suggestion generation failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def start_learning_mode(request):
    """
    FR04-03: Start Learning Mode to track and learn normal traffic behavior
    """
    try:
        session_id = request.data.get('session_id')
        learning_duration_hours = request.data.get('learning_duration_hours', 24)
        traffic_sample_size = request.data.get('traffic_sample_size', 1000)
        
        session = get_object_or_404(RuleAnalysisSession, id=session_id)
        
        # Create learning mode session
        learning_session = LearningModeSession.objects.create(
            name=f"Learning Mode - {session.name}",
            session=session,
            learning_duration_hours=learning_duration_hours,
            traffic_sample_size=traffic_sample_size,
            status='active'
        )
        
        # Mock learning process - in real implementation, this would analyze traffic
        # Simulate learning normal traffic patterns
        normal_patterns = {
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ],
            'request_methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'common_paths': [
                '/api/users/profile',
                '/api/dashboard',
                '/api/products',
                '/api/orders'
            ],
            'ip_ranges': ['192.168.1.0/24', '10.0.0.0/8']
        }
        
        baseline_metrics = {
            'avg_request_size': 1024,
            'avg_response_time': 150,
            'requests_per_minute': 50,
            'unique_users_per_hour': 25
        }
        
        anomaly_thresholds = {
            'max_request_size': 10000,
            'max_response_time': 5000,
            'max_requests_per_minute': 200,
            'suspicious_user_agent_patterns': ['bot', 'crawler', 'scanner']
        }
        
        # Update learning session with mock data
        learning_session.normal_traffic_patterns = normal_patterns
        learning_session.baseline_metrics = baseline_metrics
        learning_session.anomaly_thresholds = anomaly_thresholds
        learning_session.patterns_learned = len(normal_patterns['user_agents']) + len(normal_patterns['common_paths'])
        learning_session.accuracy_score = 0.92
        learning_session.save()
        
        return Response({
            'status': 'success',
            'message': 'Learning Mode started successfully',
            'data': {
                'learning_session_id': learning_session.id,
                'session_id': session_id,
                'learning_duration_hours': learning_duration_hours,
                'traffic_sample_size': traffic_sample_size,
                'patterns_learned': learning_session.patterns_learned,
                'accuracy_score': learning_session.accuracy_score,
                'status': learning_session.status
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Learning Mode start failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def get_learning_mode_status(request, learning_session_id):
    """
    Get the current status of a learning mode session
    """
    try:
        learning_session = get_object_or_404(LearningModeSession, id=learning_session_id)
        
        return Response({
            'status': 'success',
            'data': {
                'learning_session_id': learning_session.id,
                'name': learning_session.name,
                'status': learning_session.status,
                'patterns_learned': learning_session.patterns_learned,
                'accuracy_score': learning_session.accuracy_score,
                'started_at': learning_session.started_at,
                'completed_at': learning_session.completed_at,
                'normal_traffic_patterns': learning_session.normal_traffic_patterns,
                'baseline_metrics': learning_session.baseline_metrics,
                'anomaly_thresholds': learning_session.anomaly_thresholds
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get learning mode status: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def export_whitelist_csv(request):
    """
    FR04-04: Export suggested whitelists as a CSV file
    """
    try:
        session_id = request.data.get('session_id')
        export_name = request.data.get('export_name', 'waf_whitelist.csv')
        include_patterns = request.data.get('include_patterns', ['ip_whitelist', 'path_whitelist'])
        
        session = get_object_or_404(RuleAnalysisSession, id=session_id)
        
        # Create export record
        export_record = WhitelistExport.objects.create(
            session=session,
            export_name=export_name,
            include_patterns=include_patterns,
            status='generating'
        )
        
        # Get all whitelist suggestions for this session
        suggestions = WhitelistSuggestion.objects.filter(
            false_positive__session=session,
            suggestion_type__in=include_patterns,
            status__in=['suggested', 'approved']
        )
        
        # Prepare CSV data
        csv_data = []
        for suggestion in suggestions:
            csv_data.append({
                'rule_id': suggestion.false_positive.rule_id,
                'suggestion_type': suggestion.suggestion_type,
                'pattern_description': suggestion.pattern_description,
                'pattern_regex': suggestion.pattern_regex or '',
                'estimated_reduction': suggestion.estimated_false_positive_reduction,
                'security_risk': suggestion.security_risk_assessment,
                'priority': suggestion.implementation_priority,
                'status': suggestion.status,
                'created_at': suggestion.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create CSV file
        df = pd.DataFrame(csv_data)
        
        # Save to uploads directory
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        file_path = os.path.join(uploads_dir, export_name)
        df.to_csv(file_path, index=False)
        
        # Update export record
        export_record.file_path = file_path
        export_record.status = 'completed'
        export_record.total_patterns = len(csv_data)
        export_record.file_size_bytes = os.path.getsize(file_path)
        export_record.completed_at = datetime.now()
        export_record.save()
        
        return Response({
            'status': 'success',
            'message': f'Whitelist CSV exported successfully as {export_name}',
            'data': {
                'export_id': export_record.id,
                'file_name': export_name,
                'file_path': file_path,
                'total_patterns': len(csv_data),
                'file_size_bytes': export_record.file_size_bytes,
                'download_url': f'/uploads/{export_name}'
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'CSV export failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def get_false_positive_dashboard(request):
    """
    Get dashboard data for false positive management
    """
    try:
        session_id = request.GET.get('session_id')
        
        if session_id:
            session = get_object_or_404(RuleAnalysisSession, id=session_id)
            false_positives = FalsePositiveDetection.objects.filter(session=session)
        else:
            false_positives = FalsePositiveDetection.objects.all()
        
        # Calculate dashboard metrics
        total_false_positives = false_positives.count()
        high_risk_rules = false_positives.filter(false_positive_rate__gt=0.2).count()
        resolved_cases = false_positives.filter(status='resolved').count()
        
        # Get recent false positives
        recent_false_positives = false_positives.order_by('-created_at')[:10]
        
        # Get whitelist suggestions summary
        suggestions = WhitelistSuggestion.objects.filter(
            false_positive__in=false_positives
        )
        
        suggestion_summary = {
            'total_suggestions': suggestions.count(),
            'approved_suggestions': suggestions.filter(status='approved').count(),
            'implemented_suggestions': suggestions.filter(status='implemented').count(),
            'by_type': {}
        }
        
        for suggestion_type, _ in WhitelistSuggestion._meta.get_field('suggestion_type').choices:
            count = suggestions.filter(suggestion_type=suggestion_type).count()
            suggestion_summary['by_type'][suggestion_type] = count
        
        return Response({
            'status': 'success',
            'data': {
                'summary': {
                    'total_false_positives': total_false_positives,
                    'high_risk_rules': high_risk_rules,
                    'resolved_cases': resolved_cases,
                    'resolution_rate': (resolved_cases / total_false_positives * 100) if total_false_positives > 0 else 0
                },
                'recent_false_positives': [
                    {
                        'id': fp.id,
                        'rule_id': fp.rule_id,
                        'false_positive_rate': fp.false_positive_rate,
                        'status': fp.status,
                        'detection_method': fp.detection_method,
                        'created_at': fp.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    for fp in recent_false_positives
                ],
                'suggestion_summary': suggestion_summary
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get dashboard data: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
