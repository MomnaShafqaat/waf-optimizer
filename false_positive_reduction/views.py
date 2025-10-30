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
def render_whitelist_suggestions():
    """FR04-02: Whitelist Suggestions"""
    st.subheader("📝 Whitelist Suggestions")
    st.write("Generate intelligent whitelist patterns to reduce false positives")
    
    if st.session_state.files_data:
        files_data = st.session_state.files_data
        rules_files = [f for f in files_data if f['file_type'] == 'rules']
        traffic_files = [f for f in files_data if f['file_type'] == 'traffic']

        if rules_files and traffic_files:
            st.markdown("### False Positive Data Selection")
            col1, col2 = st.columns(2)
            with col1:
                selected_rules_for_fp = st.selectbox(
                    "Select Rules File:",
                    options=rules_files,
                    format_func=lambda x: x['file'].split('/')[-1],
                    key="suggestions_rules_select"
                )
            with col2:
                selected_traffic_for_fp = st.selectbox(
                    "Select Traffic File:",
                    options=traffic_files,
                    format_func=lambda x: x['file'].split('/')[-1],
                    key="suggestions_traffic_select"
                )

            # In a real scenario, you'd fetch the actual false positives based on the selected files
            # For now, we use mock data, but the idea is that 'selected_fp' would come from
            # a previous false positive detection run using the selected rules/traffic files.
            
            # This part needs to be dynamically populated by a prior run of False Positive Detection
            # For demonstration, we'll keep the mock data for selecting a false positive ID.
            # In a production app, you would likely store the false positives detected
            # in session_state after render_false_positive_detection runs.
            false_positives = st.session_state.get('detected_false_positives', [
                {"id": 1, "rule_id": "1001", "false_positive_rate": 0.15, "status": "detected"},
                {"id": 2, "rule_id": "1002", "false_positive_rate": 0.22, "status": "analyzing"},
                {"id": 3, "rule_id": "1003", "false_positive_rate": 0.18, "status": "detected"},
            ])
            
            if false_positives:
                st.markdown("### Suggestion Settings")
                col1, col2 = st.columns(2)
                with col1:
                    selected_fp = st.selectbox(
                        "Select Detected False Positive:",
                        options=false_positives,
                        format_func=lambda x: f"Rule {x['rule_id']} ({x['false_positive_rate']:.1%} FP Rate)",
                        key="fp_select"
                    )
                with col2:
                    suggestion_types = st.multiselect(
                        "Suggestion Types:",
                        options=["ip_whitelist", "path_whitelist", "user_agent_whitelist", "parameter_whitelist"],
                        default=["ip_whitelist", "path_whitelist"],
                        key="suggestion_types"
                    )
                
                if st.button("💡 Generate Suggestions", type="primary", key="generate_suggestions"):
                    if selected_fp and suggestion_types:
                        with st.spinner("Generating whitelist suggestions..."):
                            response = generate_whitelist_suggestions_api(selected_fp['id'], suggestion_types)
                            
                            if response and response.status_code == 200:
                                result = response.json()
                                st.success(f"✅ {result['message']}")
                                
                                # Display suggestions
                                suggestions = result['data']['suggestions']
                                if suggestions:
                                    st.subheader("🎯 Generated Suggestions")
                                    for suggestion in suggestions:
                                        with st.expander(f"{suggestion['type'].replace('_', ' ').title()} - {suggestion['estimated_reduction']:.0f}% Reduction"):
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.write(f"**Description:** {suggestion['description']}")
                                                st.write(f"**Risk Assessment:** {suggestion['risk_assessment'].title()}")
                                            with col2:
                                                st.write(f"**Estimated Reduction:** {suggestion['estimated_reduction']:.0f}%")
                                                st.write(f"**Type:** {suggestion['type'].replace('_', ' ').title()}")
                            else:
                                st.error("❌ Suggestion generation failed")
                    else:
                        st.warning("Please select a false positive and suggestion types")
            else:
                st.info("No false positives detected yet. Run detection first.")
        else:
            st.warning("Please upload both Rules and Traffic files to get whitelist suggestions.")
    else:
        st.error("No uploaded files found in session.")

@api_view(['POST'])
def render_learning_mode():
    """FR04-03: Learning Mode"""
    st.subheader("🧠 Learning Mode")
    st.write("Enable adaptive learning to understand normal traffic patterns")
    
    if st.session_state.files_data:
        files_data = st.session_state.files_data
        rules_files = [f for f in files_data if f['file_type'] == 'rules']
        traffic_files = [f for f in files_data if f['file_type'] == 'traffic']

        if rules_files and traffic_files:
            st.markdown("### File Selection")
            col1, col2 = st.columns(2)
            with col1:
                selected_rules_for_learning = st.selectbox(
                    "Select Rules File for Learning:",
                    options=rules_files,
                    format_func=lambda x: x['file'].split('/')[-1],
                    key="learning_rules_select"
                )
            with col2:
                selected_traffic_for_learning = st.selectbox(
                    "Select Traffic File for Learning:",
                    options=traffic_files,
                    format_func=lambda x: x['file'].split('/')[-1],
                    key="learning_traffic_select"
                )
            
            st.markdown("### Learning Settings")
            col1, col2 = st.columns(2)
            with col1:
                learning_duration = st.slider("Learning Duration (hours):", 1, 72, 24)
            with col2:
                sample_size = st.number_input("Traffic Sample Size:", 100, 10000, 1000)
            
            if st.button("🚀 Start Learning Mode", type="primary", key="start_learning"):
                rules_file_id = selected_rules_for_learning['id']
                traffic_file_id = selected_traffic_for_learning['id']

                with st.spinner("Starting learning mode analysis..."):
                    response = start_learning_mode_api(rules_file_id, traffic_file_id, learning_duration, sample_size)
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                        
                        # Display learning results
                        data = result['data']
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Learning Session ID", data['learning_session_id'])
                        with col2:
                            st.metric("Patterns Learned", data['patterns_learned'])
                        with col3:
                            st.metric("Accuracy Score", f"{data['accuracy_score']:.1%}")
                        with col4:
                            st.metric("Status", data['status'].title())
                        
                        # Store learning session for status checking
                        st.session_state.current_learning_session = data['learning_session_id']
                    else:
                        st.error("❌ Learning mode start failed")
        else:
            st.warning("Please upload both Rules and Traffic files to start learning mode.")
    else:
        st.error("No uploaded files found in session.")
    
    # Show learning status if active
    if hasattr(st.session_state, 'current_learning_session'):
        st.subheader("📊 Learning Status")
        learning_session_id = st.session_state.current_learning_session
        
        if st.button("🔄 Refresh Learning Status", key="refresh_learning"):
            with st.spinner("Checking learning status..."):
                response = get_learning_mode_status_api(learning_session_id)
                
                if response and response.status_code == 200:
                    status_data = response.json()['data']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", status_data['status'].title())
                    with col2:
                        st.metric("Patterns Learned", status_data['patterns_learned'])
                    with col3:
                        st.metric("Accuracy", f"{status_data['accuracy_score']:.1%}")
                    
                    # Show learned patterns
                    if status_data.get('normal_traffic_patterns'):
                        with st.expander("View Learned Patterns"):
                            patterns = status_data['normal_traffic_patterns']
                            st.write("**User Agents:**")
                            for ua in patterns.get('user_agents', [])[:3]:
                                st.write(f"- {ua}")
                            st.write("**Common Paths:**")
                            for path in patterns.get('common_paths', [])[:5]:
                                st.write(f"- {path}")
                else:
                    st.error("❌ Failed to retrieve learning status.")

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
def render_whitelist_export():
    """FR04-04: Whitelist Export"""
    st.subheader("📤 Export Whitelist")
    st.write("Export suggested whitelist patterns as CSV file")
    
    if st.session_state.files_data:
        files_data = st.session_state.files_data
        rules_files = [f for f in files_data if f['file_type'] == 'rules']
        traffic_files = [f for f in files_data if f['file_type'] == 'traffic']

        if rules_files and traffic_files:
            st.markdown("### Export Scope")
            col1, col2 = st.columns(2)
            with col1:
                selected_rules_for_export = st.selectbox(
                    "Select Rules File for Export Context:",
                    options=rules_files,
                    format_func=lambda x: x['file'].split('/')[-1],
                    key="export_rules_select"
                )
            with col2:
                selected_traffic_for_export = st.selectbox(
                    "Select Traffic File for Export Context:",
                    options=traffic_files,
                    format_func=lambda x: x['file'].split('/')[-1],
                    key="export_traffic_select"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                export_name = st.text_input("Export Filename:", "waf_whitelist.csv", key="export_filename")
            with col2:
                include_patterns = st.multiselect(
                    "Include Pattern Types:",
                    options=["ip_whitelist", "path_whitelist", "user_agent_whitelist", "parameter_whitelist"],
                    default=["ip_whitelist", "path_whitelist"],
                    key="export_patterns"
                )
            
            if st.button("📥 Export CSV", type="primary", key="export_csv"):
                rules_file_id = selected_rules_for_export['id']
                traffic_file_id = selected_traffic_for_export['id'] # Pass traffic_file_id for context if needed by backend

                if include_patterns:
                    with st.spinner("Generating CSV export..."):
                        response = export_whitelist_csv_api(rules_file_id, export_name, include_patterns, traffic_file_id)
                        
                        if response and response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            
                            # Display export results
                            data = result['data']
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Export ID", data['export_id'])
                            with col2:
                                st.metric("Total Patterns", data['total_patterns'])
                            with col3:
                                st.metric("File Size", f"{data['file_size_bytes']} bytes")
                            with col4:
                                st.metric("Status", "Completed")
                            
                            # Provide download link
                            st.info(f"📁 File saved as: {data['file_name']}")
                            st.markdown(f"**Download URL:** `{data['download_url']}`")
                        else:
                            st.error("❌ CSV export failed")
                else:
                    st.warning("Please select at least one pattern type to export.")
        else:
            st.warning("Please upload both Rules and Traffic files to export whitelists.")
    else:
        st.error("No uploaded files found in session.")

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