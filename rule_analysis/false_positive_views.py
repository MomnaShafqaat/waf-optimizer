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
from .supabase_utils import get_file_as_dataframe
from supabase_client import supabase
import io

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
        if not traffic_file:
            return Response({'error': 'Traffic file not found in session'}, status=400)

        traffic_df = get_file_as_dataframe(traffic_file)

        # Normalize columns (safe access)
        for col in ['rule_id', 'action', 'http_status', 'client_ip', 'user_agent', 'request_uri', 'request_method', 'timestamp', 'rule_message']:
            if col not in traffic_df.columns:
                traffic_df[col] = None

        false_positives_detected = []

        # Find candidate rule IDs (skip '-' or empty)
        rule_ids = traffic_df['rule_id'].dropna().unique().tolist()
        rule_ids = [r for r in rule_ids if str(r).strip() and str(r).strip() != '-']

        for rule_id in rule_ids:
            hits = traffic_df[traffic_df['rule_id'].astype(str) == str(rule_id)].copy()
            total_hits = len(hits)
            if total_hits == 0:
                continue

            # Consider a request 'legitimate' if action != 'blocked' or http_status is 2xx
            def is_legitimate(row):
                try:
                    action = str(row.get('action') or '').lower()
                    status = str(row.get('http_status') or '')
                    if action and action != 'blocked':
                        return True
                    if status.startswith('2'):
                        return True
                except Exception:
                    return False
                return False

            legitimate_mask = hits.apply(is_legitimate, axis=1)
            legitimate_count = int(legitimate_mask.sum())
            false_positive_rate = legitimate_count / total_hits if total_hits > 0 else 0.0

            if false_positive_rate > float(threshold):
                # Collect sample blocked requests for context
                blocked_rows = hits[hits.apply(lambda r: (str(r.get('action') or '').lower() == 'blocked') or (str(r.get('http_status') or '').startswith('4') or str(r.get('http_status') or '').startswith('5')), axis=1)]
                sample_blocked = []
                for _, br in blocked_rows.head(5).iterrows():
                    sample_blocked.append({
                        'timestamp': str(br.get('timestamp')),
                        'ip_address': br.get('client_ip'),
                        'user_agent': br.get('user_agent'),
                        'request_path': br.get('request_uri'),
                        'request_method': br.get('request_method'),
                        'reason': br.get('rule_message') or 'Matched rule'
                    })

                # Derive common patterns from legitimate hits for possible whitelist suggestions
                legit_hits = hits[legitimate_mask]
                common_paths = legit_hits['request_uri'].dropna().astype(str).value_counts().head(5).index.tolist()
                common_user_agents = legit_hits['user_agent'].dropna().astype(str).value_counts().head(5).index.tolist()
                common_ips = legit_hits['client_ip'].dropna().astype(str).value_counts().head(5).index.tolist()

                fp_detection, created = FalsePositiveDetection.objects.get_or_create(
                    rule_id=str(rule_id),
                    session=session,
                    defaults={
                        'false_positive_count': legitimate_count,
                        'legitimate_request_count': legitimate_count,
                        'false_positive_rate': false_positive_rate,
                        'detection_method': detection_method,
                        'confidence_score': round(min(0.99, false_positive_rate), 2),
                        'blocked_requests': sample_blocked,
                        'request_patterns': {
                            'common_paths': common_paths,
                            'common_user_agents': common_user_agents,
                            'common_ips': common_ips
                        }
                    }
                )

                if not created:
                    fp_detection.false_positive_count = legitimate_count
                    fp_detection.legitimate_request_count = legitimate_count
                    fp_detection.false_positive_rate = false_positive_rate
                    fp_detection.detection_method = detection_method
                    fp_detection.confidence_score = round(min(0.99, false_positive_rate), 2)
                    fp_detection.blocked_requests = sample_blocked
                    fp_detection.request_patterns = {
                        'common_paths': common_paths,
                        'common_user_agents': common_user_agents,
                        'common_ips': common_ips
                    }
                    fp_detection.updated_at = datetime.now()
                    fp_detection.save()

                false_positives_detected.append({
                    'rule_id': str(rule_id),
                    'false_positive_count': legitimate_count,
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
                'total_rules_analyzed': len(rule_ids),
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
        
        # Real learning process: analyze the session's traffic file (from Supabase)
        traffic_file = session.traffic_file
        if not traffic_file:
            learning_session.status = 'failed'
            learning_session.save()
            return Response({'error': 'Traffic file not found in session'}, status=400)

        # Load traffic into DataFrame
        try:
            traffic_df = get_file_as_dataframe(traffic_file)
        except Exception as e:
            learning_session.status = 'failed'
            learning_session.error_message = str(e)
            learning_session.save()
            return Response({'error': f'Failed to load traffic file: {str(e)}'}, status=500)

        # Derive common patterns
        user_agents = traffic_df['user_agent'].dropna().astype(str).value_counts().head(20).index.tolist() if 'user_agent' in traffic_df.columns else []
        request_methods = traffic_df['request_method'].dropna().unique().tolist() if 'request_method' in traffic_df.columns else []
        common_paths = traffic_df['request_uri'].dropna().astype(str).value_counts().head(20).index.tolist() if 'request_uri' in traffic_df.columns else []

        # Top client IPs and simple /24 ranges for IPv4 addresses
        top_ips = traffic_df['client_ip'].dropna().astype(str).value_counts().head(20).index.tolist() if 'client_ip' in traffic_df.columns else []
        ip_ranges = []
        for ip in top_ips[:10]:
            if '.' in ip:
                parts = ip.split('.')
                if len(parts) == 4:
                    ip_ranges.append(f"{parts[0]}.{parts[1]}.{parts[2]}.0/24")
        ip_ranges = list(dict.fromkeys(ip_ranges))  # unique

        # Baseline metrics
        if 'request_size' in traffic_df.columns:
            avg_request_size = float(traffic_df['request_size'].dropna().mean())
            max_request_size = int(traffic_df['request_size'].dropna().quantile(0.99))
        else:
            # Fallback estimate using request_uri length
            uri_lengths = traffic_df['request_uri'].dropna().astype(str).apply(len) if 'request_uri' in traffic_df.columns else pd.Series([])
            avg_request_size = float(uri_lengths.mean()) if not uri_lengths.empty else 0
            max_request_size = int(uri_lengths.quantile(0.99)) if not uri_lengths.empty else 0

        avg_response_time = float(traffic_df['response_time'].dropna().mean()) if 'response_time' in traffic_df.columns else 0.0

        # Requests per minute across the traffic timeframe
        requests_per_minute = 0
        unique_users_per_hour = 0
        if 'timestamp' in traffic_df.columns:
            try:
                traffic_df['timestamp_parsed'] = pd.to_datetime(traffic_df['timestamp'], errors='coerce')
                time_span = (traffic_df['timestamp_parsed'].max() - traffic_df['timestamp_parsed'].min()).total_seconds() / 60.0
                total_requests = len(traffic_df)
                if time_span > 0:
                    requests_per_minute = total_requests / time_span
                # unique users per hour (approx)
                unique_ips = traffic_df.groupby(traffic_df['timestamp_parsed'].dt.floor('H'))['client_ip'].nunique()
                unique_users_per_hour = int(unique_ips.mean()) if not unique_ips.empty else 0
            except Exception:
                requests_per_minute = 0
                unique_users_per_hour = 0

        baseline_metrics = {
            'avg_request_size': avg_request_size,
            'avg_response_time': avg_response_time,
            'requests_per_minute': float(requests_per_minute),
            'unique_users_per_hour': int(unique_users_per_hour)
        }

        anomaly_thresholds = {
            'max_request_size': max_request_size,
            'max_response_time': int(traffic_df['response_time'].dropna().quantile(0.99)) if 'response_time' in traffic_df.columns else 0,
            'max_requests_per_minute': int(requests_per_minute * 3) if requests_per_minute > 0 else 0,
            'suspicious_user_agent_patterns': ['bot', 'crawler', 'scanner']
        }

        normal_patterns = {
            'user_agents': user_agents,
            'request_methods': request_methods,
            'common_paths': common_paths,
            'ip_ranges': ip_ranges
        }

        # Update learning session with derived data
        learning_session.normal_traffic_patterns = normal_patterns
        learning_session.baseline_metrics = baseline_metrics
        learning_session.anomaly_thresholds = anomaly_thresholds
        learning_session.patterns_learned = len(user_agents) + len(common_paths)
        learning_session.accuracy_score = 0.0  # unknown until validated
        learning_session.status = 'completed'
        learning_session.completed_at = datetime.now()
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
        
        # Create CSV file locally first
        df = pd.DataFrame(csv_data)
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        local_file_path = os.path.join(uploads_dir, export_name)
        df.to_csv(local_file_path, index=False)

        # Try to upload to Supabase storage and create UploadedFile
        download_url = None
        try:
            with open(local_file_path, 'rb') as f:
                file_bytes = f.read()

            bucket_name = 'waf-exports'
            supabase_path = f'whitelists/session_{session.id}/{export_name}'

            if supabase:
                try:
                    supabase.storage.from_(bucket_name).upload(supabase_path, file_bytes)
                except Exception:
                    # Attempt to overwrite existing file by removing first
                    try:
                        supabase.storage.from_(bucket_name).remove([supabase_path])
                    except Exception:
                        pass
                    supabase.storage.from_(bucket_name).upload(supabase_path, file_bytes)

                uploaded_file = UploadedFile.objects.create(
                    filename=export_name,
                    file_type='rules',
                    file_size=os.path.getsize(local_file_path),
                    supabase_path=supabase_path
                )

                export_record.file_path = supabase_path
                export_record.status = 'completed'
                export_record.total_patterns = len(csv_data)
                export_record.file_size_bytes = uploaded_file.file_size
                export_record.completed_at = datetime.now()
                export_record.save()

                download_url = f"/supabase/{bucket_name}/{supabase_path}"
            else:
                raise Exception('Supabase client not configured')

        except Exception as e:
            # Fall back to local file
            export_record.file_path = local_file_path
            export_record.status = 'completed' if os.path.exists(local_file_path) else 'failed'
            export_record.total_patterns = len(csv_data)
            export_record.file_size_bytes = os.path.getsize(local_file_path) if os.path.exists(local_file_path) else 0
            export_record.error_message = str(e)
            export_record.completed_at = datetime.now()
            export_record.save()
            download_url = f'/uploads/{export_name}'

        return Response({
            'status': 'success',
            'message': f'Whitelist CSV exported successfully as {export_name}',
            'data': {
                'export_id': export_record.id,
                'file_name': export_name,
                'file_path': export_record.file_path,
                'total_patterns': len(csv_data),
                'file_size_bytes': export_record.file_size_bytes,
                'download_url': download_url
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
