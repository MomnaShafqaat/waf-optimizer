# false_positive_reduction/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import pandas as pd
import os
from datetime import datetime
from collections import Counter, defaultdict

from rule_analysis.models import RuleAnalysisSession
from .models import FalsePositiveDetection, WhitelistSuggestion, LearningModeSession, WhitelistExport
from .serializers import FalsePositiveDetectionSerializer


class FalsePositiveDetectionViewSet(viewsets.ModelViewSet):
    queryset = FalsePositiveDetection.objects.all()
    serializer_class = FalsePositiveDetectionSerializer

    def get_queryset(self):
        queryset = FalsePositiveDetection.objects.all()
        session_id = self.request.query_params.get('session_id', None)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset


@api_view(['POST'])
def detect_false_positives(request):
    """FR04-01: Detect rules that repeatedly block legitimate requests"""
    try:
        session_id = request.data.get('session_id')
        detection_method = request.data.get('detection_method', 'manual')
        threshold = request.data.get('false_positive_threshold', 0.1)

        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)

        session = get_object_or_404(RuleAnalysisSession, id=session_id)
        
        # Check if traffic file exists
        if not session.traffic_file or not os.path.exists(session.traffic_file.file.path):
            return Response({'error': 'Traffic file not found for this session'}, status=400)

        # Read actual traffic data
        traffic_df = pd.read_csv(session.traffic_file.file.path)
        
        # Analyze traffic for false positives
        false_positives_detected = []
        rules_analyzed = 0
        
        # Get rules from session (adjust based on your rule model)
        from rule_analysis.models import WAFRule  # Adjust import based on your models
        rules = WAFRule.objects.filter(session=session)
        
        for rule in rules:
            rules_analyzed += 1
            rule_id = rule.id if hasattr(rule, 'id') else rule.rule_id
            
            # Analyze traffic blocked by this rule
            blocked_requests = []
            legitimate_requests = []
            
            # Simple heuristic: check if URL patterns suggest legitimate traffic
            for idx, row in traffic_df.iterrows():
                is_blocked = analyze_rule_match(rule, row)
                is_legitimate = is_legitimate_traffic(row)
                
                if is_blocked:
                    blocked_requests.append({
                        'timestamp': str(row.get('timestamp', '')),
                        'src_ip': str(row.get('src_ip', '')),
                        'method': str(row.get('method', '')),
                        'url': str(row.get('url', ''))
                    })
                    
                    if is_legitimate:
                        legitimate_requests.append(row.to_dict())
            
            false_positive_count = len(legitimate_requests)
            total_blocked = len(blocked_requests)
            
            if total_blocked > 0:
                false_positive_rate = false_positive_count / total_blocked
            else:
                false_positive_rate = 0.0
            
            # Only record if exceeds threshold
            if false_positive_rate > threshold and false_positive_count > 0:
                # Extract patterns from blocked requests
                ips = [req['src_ip'] for req in blocked_requests]
                urls = [req['url'] for req in blocked_requests]
                methods = [req['method'] for req in blocked_requests]
                
                common_ips = [ip for ip, count in Counter(ips).most_common(5)]
                common_paths = list(set([url.split('?')[0] for url in urls]))[:5]
                common_methods = [method for method, count in Counter(methods).most_common(3)]
                
                request_patterns = {
                    'common_ips': common_ips,
                    'common_paths': common_paths,
                    'common_methods': common_methods,
                    'total_blocked': total_blocked
                }
                
                fp_detection, created = FalsePositiveDetection.objects.get_or_create(
                    rule_id=str(rule_id),
                    session=session,
                    defaults={
                        'false_positive_count': false_positive_count,
                        'legitimate_request_count': total_blocked,
                        'false_positive_rate': false_positive_rate,
                        'detection_method': detection_method,
                        'confidence_score': calculate_confidence_score(false_positive_rate, total_blocked),
                        'blocked_requests': blocked_requests[:20],  # Store sample
                        'request_patterns': request_patterns,
                        'status': 'detected'
                    }
                )
                
                if not created:
                    fp_detection.false_positive_count = false_positive_count
                    fp_detection.legitimate_request_count = total_blocked
                    fp_detection.false_positive_rate = false_positive_rate
                    fp_detection.blocked_requests = blocked_requests[:20]
                    fp_detection.request_patterns = request_patterns
                    fp_detection.confidence_score = calculate_confidence_score(false_positive_rate, total_blocked)
                    fp_detection.save()

                false_positives_detected.append({
                    'rule_id': str(rule_id),
                    'false_positive_count': false_positive_count,
                    'false_positive_rate': round(false_positive_rate, 4),
                    'status': fp_detection.status,
                    'detection_method': detection_method,
                    'confidence_score': fp_detection.confidence_score
                })

        return Response({
            'status': 'success',
            'message': f'False positive detection completed. Found {len(false_positives_detected)} rules with high false positive rates.',
            'data': {
                'session_id': session_id,
                'detection_method': detection_method,
                'threshold_used': threshold,
                'false_positives_detected': false_positives_detected,
                'total_rules_analyzed': rules_analyzed,
                'high_false_positive_rules': len(false_positives_detected)
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
def generate_whitelist_suggestions(request):
    """FR04-02: Suggest whitelisting patterns to reduce false positives"""
    try:
        false_positive_id = request.data.get('false_positive_id')
        suggestion_types = request.data.get('suggestion_types', ['ip_whitelist', 'path_whitelist'])
        
        if not false_positive_id:
            return Response({'error': 'false_positive_id is required'}, status=400)
        
        fp_detection = get_object_or_404(FalsePositiveDetection, id=false_positive_id)
        patterns = fp_detection.request_patterns
        
        suggestions = []
        
        # IP Whitelist Suggestions
        common_ips = patterns.get('common_ips', [])
        if 'ip_whitelist' in suggestion_types and common_ips:
            # Calculate potential reduction based on IP frequency
            estimated_reduction = min(60.0, len(common_ips) * 10)
            
            suggestion = WhitelistSuggestion.objects.create(
                false_positive=fp_detection,
                suggestion_type='ip_whitelist',
                pattern_description=f"Whitelist trusted IPs: {', '.join(common_ips[:5])}",
                pattern_conditions={'ip_addresses': common_ips},
                estimated_false_positive_reduction=estimated_reduction,
                security_risk_assessment=assess_ip_risk(common_ips),
                implementation_priority='high'
            )
            suggestions.append({
                'id': suggestion.id,
                'type': 'ip_whitelist',
                'description': suggestion.pattern_description,
                'estimated_reduction': suggestion.estimated_false_positive_reduction,
                'risk_assessment': suggestion.security_risk_assessment,
                'priority': suggestion.implementation_priority
            })

        # Path Whitelist Suggestions
        common_paths = patterns.get('common_paths', [])
        if 'path_whitelist' in suggestion_types and common_paths:
            estimated_reduction = min(50.0, len(common_paths) * 8)
            
            # Create regex pattern for paths
            escaped_paths = [path.replace('/', '\\/') for path in common_paths]
            regex_pattern = f"^({'|'.join(escaped_paths)})$"
            
            suggestion = WhitelistSuggestion.objects.create(
                false_positive=fp_detection,
                suggestion_type='path_whitelist',
                pattern_description=f"Whitelist legitimate paths: {', '.join(common_paths[:3])}",
                pattern_regex=regex_pattern,
                pattern_conditions={'paths': common_paths},
                estimated_false_positive_reduction=estimated_reduction,
                security_risk_assessment=assess_path_risk(common_paths),
                implementation_priority='medium'
            )
            suggestions.append({
                'id': suggestion.id,
                'type': 'path_whitelist',
                'description': suggestion.pattern_description,
                'estimated_reduction': suggestion.estimated_false_positive_reduction,
                'risk_assessment': suggestion.security_risk_assessment,
                'priority': suggestion.implementation_priority
            })

        # User Agent Whitelist
        if 'user_agent_whitelist' in suggestion_types and patterns.get('common_user_agents'):
            user_agents = patterns['common_user_agents'][:3]
            suggestion = WhitelistSuggestion.objects.create(
                false_positive=fp_detection,
                suggestion_type='user_agent_whitelist',
                pattern_description=f"Whitelist legitimate user agents",
                pattern_conditions={'user_agents': user_agents},
                estimated_false_positive_reduction=30.0,
                security_risk_assessment='medium',
                implementation_priority='low'
            )
            suggestions.append({
                'id': suggestion.id,
                'type': 'user_agent_whitelist',
                'description': suggestion.pattern_description,
                'estimated_reduction': suggestion.estimated_false_positive_reduction,
                'risk_assessment': suggestion.security_risk_assessment,
                'priority': suggestion.implementation_priority
            })

        return Response({
            'status': 'success',
            'message': f"Generated {len(suggestions)} whitelist suggestions for rule {fp_detection.rule_id}",
            'data': {
                'false_positive_id': false_positive_id,
                'rule_id': fp_detection.rule_id,
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
def start_learning_mode(request):
    """FR04-03: Learning Mode to track normal traffic behavior"""
    try:
        session_id = request.data.get('session_id')
        learning_duration_hours = request.data.get('learning_duration_hours', 24)
        traffic_sample_size = request.data.get('traffic_sample_size', 1000)
        
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        
        session = get_object_or_404(RuleAnalysisSession, id=session_id)

        learning_session = LearningModeSession.objects.create(
            name=f"Learning Mode - {session.name} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            session=session,
            learning_duration_hours=learning_duration_hours,
            traffic_sample_size=traffic_sample_size,
            status='active'
        )

        # Analyze traffic to learn patterns
        if session.traffic_file and os.path.exists(session.traffic_file.file.path):
            traffic_df = pd.read_csv(session.traffic_file.file.path)
            traffic_sample = traffic_df.head(traffic_sample_size)
            
            # Learn normal traffic patterns
            normal_patterns = learn_traffic_patterns(traffic_sample)
            baseline = calculate_baseline_metrics(traffic_sample)
            thresholds = calculate_anomaly_thresholds(baseline)
            
            learning_session.normal_traffic_patterns = normal_patterns
            learning_session.baseline_metrics = baseline
            learning_session.anomaly_thresholds = thresholds
            learning_session.patterns_learned = len(normal_patterns.get('common_paths', [])) + len(normal_patterns.get('common_ips', []))
            learning_session.accuracy_score = 0.85  # Initial estimate
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
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def get_learning_mode_status(request, learning_session_id):
    """Get status of learning mode session"""
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
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
def export_whitelist_csv(request):
    """FR04-04: Export suggested whitelists as CSV"""
    try:
        session_id = request.data.get('session_id')
        export_name = request.data.get('export_name', f'waf_whitelist_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        include_patterns = request.data.get('include_patterns', ['ip_whitelist', 'path_whitelist'])
        
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        
        session = get_object_or_404(RuleAnalysisSession, id=session_id)

        export_record = WhitelistExport.objects.create(
            session=session,
            export_name=export_name,
            include_patterns=include_patterns,
            status='generating'
        )

        # Get all approved/suggested whitelist patterns
        suggestions = WhitelistSuggestion.objects.filter(
            false_positive__session=session,
            suggestion_type__in=include_patterns,
            status__in=['suggested', 'approved']
        ).select_related('false_positive')

        csv_rows = []
        for s in suggestions:
            csv_rows.append({
                'rule_id': s.false_positive.rule_id,
                'suggestion_type': s.suggestion_type,
                'pattern_description': s.pattern_description,
                'pattern_regex': s.pattern_regex or '',
                'pattern_conditions': str(s.pattern_conditions),
                'estimated_reduction': s.estimated_false_positive_reduction,
                'security_risk': s.security_risk_assessment,
                'priority': s.implementation_priority,
                'status': s.status,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        df = pd.DataFrame(csv_rows)
        
        # Create uploads directory
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, export_name)
        
        df.to_csv(file_path, index=False)

        export_record.file_path = file_path
        export_record.status = 'completed'
        export_record.total_patterns = len(csv_rows)
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
                'total_patterns': len(csv_rows),
                'file_size_bytes': export_record.file_size_bytes,
                'download_url': f'/api/whitelist/download/{export_record.id}/'
            }
        })
    except Exception as e:
        export_record.status = 'failed'
        export_record.error_message = str(e)
        export_record.save()
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def download_whitelist_export(request, export_id):
    """Download exported whitelist CSV file"""
    try:
        export_record = get_object_or_404(WhitelistExport, id=export_id)
        
        if export_record.status != 'completed' or not export_record.file_path:
            return Response({'error': 'Export not ready or failed'}, status=400)
        
        if not os.path.exists(export_record.file_path):
            return Response({'error': 'Export file not found'}, status=404)
        
        with open(export_record.file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{export_record.export_name}"'
            return response
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def get_false_positive_dashboard(request):
    """Dashboard view for false positive analytics"""
    try:
        session_id = request.GET.get('session_id')
        
        if session_id:
            session = get_object_or_404(RuleAnalysisSession, id=session_id)
            false_positives = FalsePositiveDetection.objects.filter(session=session)
        else:
            false_positives = FalsePositiveDetection.objects.all()

        total_false_positives = false_positives.count()
        high_risk_rules = false_positives.filter(false_positive_rate__gt=0.2).count()
        resolved_cases = false_positives.filter(status='resolved').count()

        recent_false_positives = false_positives.order_by('-created_at')[:10]
        suggestions = WhitelistSuggestion.objects.filter(false_positive__in=false_positives)
        
        by_type = {}
        for s_type, label in WhitelistSuggestion._meta.get_field('suggestion_type').choices:
            by_type[s_type] = suggestions.filter(suggestion_type=s_type).count()

        return Response({
            'status': 'success',
            'data': {
                'summary': {
                    'total_false_positives': total_false_positives,
                    'high_risk_rules': high_risk_rules,
                    'resolved_cases': resolved_cases,
                    'resolution_rate': round((resolved_cases / total_false_positives * 100) if total_false_positives > 0 else 0, 2)
                },
                'recent_false_positives': [{
                    'id': fp.id,
                    'rule_id': fp.rule_id,
                    'false_positive_rate': round(fp.false_positive_rate, 4),
                    'false_positive_count': fp.false_positive_count,
                    'status': fp.status,
                    'detection_method': fp.detection_method,
                    'confidence_score': round(fp.confidence_score, 2),
                    'created_at': fp.created_at.strftime('%Y-%m-%d %H:%M:%S')
                } for fp in recent_false_positives],
                'suggestion_summary': {
                    'total_suggestions': suggestions.count(),
                    'approved_suggestions': suggestions.filter(status='approved').count(),
                    'implemented_suggestions': suggestions.filter(status='implemented').count(),
                    'by_type': by_type
                }
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


# Helper functions
def analyze_rule_match(rule, traffic_row):
    """Check if traffic matches rule conditions"""
    # Implement actual rule matching logic based on your rule structure
    # This is a placeholder
    return False


def is_legitimate_traffic(row):
    """Heuristic to determine if traffic is legitimate"""
    url = str(row.get('url', '')).lower()
    method = str(row.get('method', '')).upper()
    
    # Common legitimate patterns
    legitimate_paths = ['/api/', '/static/', '/admin/', '/health', '/status']
    legitimate_methods = ['GET', 'POST', 'PUT', 'DELETE']
    
    is_legitimate_path = any(path in url for path in legitimate_paths)
    is_legitimate_method = method in legitimate_methods
    
    # Additional checks
    has_suspicious_patterns = any(pattern in url for pattern in ['<script>', 'union select', '../', 'cmd='])
    
    return is_legitimate_path and is_legitimate_method and not has_suspicious_patterns


def calculate_confidence_score(false_positive_rate, sample_size):
    """Calculate confidence score based on FP rate and sample size"""
    if sample_size < 10:
        return 0.3
    elif sample_size < 50:
        confidence = 0.6
    elif sample_size < 100:
        confidence = 0.8
    else:
        confidence = 0.95
    
    # Adjust based on FP rate
    if false_positive_rate > 0.5:
        confidence *= 0.9
    
    return round(confidence, 2)


def assess_ip_risk(ips):
    """Assess security risk of whitelisting IPs"""
    # Simple heuristic: private IPs are lower risk
    private_ranges = ['192.168.', '10.', '172.16.', '127.']
    
    private_count = sum(1 for ip in ips if any(ip.startswith(pr) for pr in private_ranges))
    
    if private_count == len(ips):
        return 'low'
    elif private_count > len(ips) / 2:
        return 'medium'
    else:
        return 'high'


def assess_path_risk(paths):
    """Assess security risk of whitelisting paths"""
    sensitive_paths = ['/admin', '/config', '/database', '/backup']
    
    has_sensitive = any(any(sp in path.lower() for sp in sensitive_paths) for path in paths)
    
    return 'high' if has_sensitive else 'medium'


def learn_traffic_patterns(traffic_df):
    """Learn normal traffic patterns from sample"""
    patterns = {
        'common_ips': traffic_df['src_ip'].value_counts().head(10).index.tolist(),
        'common_paths': traffic_df['url'].apply(lambda x: str(x).split('?')[0]).value_counts().head(10).index.tolist(),
        'common_methods': traffic_df['method'].value_counts().to_dict(),
        'hourly_distribution': traffic_df.groupby(pd.to_datetime(traffic_df['timestamp']).dt.hour).size().to_dict() if 'timestamp' in traffic_df.columns else {}
    }
    return patterns


def calculate_baseline_metrics(traffic_df):
    """Calculate baseline metrics from traffic"""
    return {
        'total_requests': len(traffic_df),
        'unique_ips': traffic_df['src_ip'].nunique() if 'src_ip' in traffic_df.columns else 0,
        'unique_paths': traffic_df['url'].nunique() if 'url' in traffic_df.columns else 0,
        'avg_requests_per_ip': len(traffic_df) / traffic_df['src_ip'].nunique() if 'src_ip' in traffic_df.columns and traffic_df['src_ip'].nunique() > 0 else 0
    }


def calculate_anomaly_thresholds(baseline):
    """Calculate thresholds for anomaly detection"""
    return {
        'max_requests_per_ip': baseline.get('avg_requests_per_ip', 0) * 3,
        'max_requests_per_minute': baseline.get('total_requests', 0) / 60 * 2
    }