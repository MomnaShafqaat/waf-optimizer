# rule_analysis/hit_count_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
from .hit_counter import RuleHitCounter
from .models import RulePerformance
from data_management.models import UploadedFile

@api_view(['POST'])
def update_rule_hit_counts(request):
    """
    FR03-01, FR03-02 & FR03-03: Complete performance profiling
    """
    try:
        # Handle empty request body gracefully
        if not request.data:
            traffic_file_id = None
        else:
            traffic_file_id = request.data.get('traffic_file_id')
        
        print(f"Request data: {request.data}")
        print(f"Traffic file ID: {traffic_file_id}")
        
        # Use mock data for testing - DEFINE THIS VARIABLE
        mock_traffic_data = pd.DataFrame([
            {'rule_id': '1001', 'timestamp': '2024-01-15 10:30:00', 'action': 'blocked'},
            {'rule_id': '1001', 'timestamp': '2024-01-15 10:31:00', 'action': 'blocked'},
            {'rule_id': '1002', 'timestamp': '2024-01-15 10:32:00', 'action': 'blocked'},
            {'rule_id': '1003', 'timestamp': '2024-01-15 10:33:00', 'action': 'blocked'},
            {'rule_id': '1001', 'timestamp': '2024-01-15 10:34:00', 'action': 'blocked'},
            {'rule_id': '1005', 'timestamp': '2024-01-15 10:35:00', 'action': 'blocked'},
            {'rule_id': '-', 'timestamp': '2024-01-15 10:36:00', 'action': 'passed'},
            {'rule_id': '1003', 'timestamp': '2024-01-15 10:37:00', 'action': 'blocked'},
        ])
        
        hit_counter = RuleHitCounter()
        
        # FR03-01: Update hit counts
        hit_result = hit_counter.process_traffic_logs(mock_traffic_data)
        
        # FR03-02: Calculate performance metrics
        total_requests = hit_result['total_requests_processed']
        metrics_result = hit_counter.calculate_performance_metrics(total_requests)
        
        # FR03-03: Flag inefficient rules
        flagged_rules = hit_counter.flag_inefficient_rules()
        
        return Response({
            'status': 'success',
            'message': 'Complete rule performance profiling completed',
            'summary': {
                'total_requests': total_requests,
                'rules_triggered': hit_result['rules_triggered'],
                'hits_updated': len(hit_result['hit_summary']),
                'metrics_calculated': len(metrics_result),
                'rules_flagged': {
                    'rarely_used': len(flagged_rules['rarely_used']),
                    'redundant': len(flagged_rules['redundant']),
                    'high_performance': len(flagged_rules['high_performance'])
                }
            },
            'hit_details': hit_result['hit_summary'],
            'performance_metrics': metrics_result,
            'flagged_rules': flagged_rules  # NEW: FR03-03 data
        })
        
    except Exception as e:
        return Response({'error': f'Update failed: {str(e)}'}, status=500)

@api_view(['GET'])
def get_hit_count_dashboard(request):
    """
    Get complete performance dashboard with FR03-01, FR03-02, FR03-03
    """
    try:
        hit_counter = RuleHitCounter()
        
        # Get basic stats
        hit_stats = hit_counter.get_rule_hit_stats()
        total_hits = sum(rule['hit_count'] for rule in hit_stats)
        total_rules = len(hit_stats)
        avg_hits_per_rule = total_hits / total_rules if total_rules > 0 else 0
        
        # Get performance metrics
        rules_with_metrics = RulePerformance.objects.all().values(
            'rule_id', 'hit_count', 'match_frequency', 'effectiveness_ratio',
            'is_rarely_used', 'is_redundant', 'is_high_performance'  # NEW: FR03-03 flags
        )
        
        # Enhanced top rules with metrics and flags
        top_rules = []
        for rule in rules_with_metrics.order_by('-hit_count')[:5]:
            flags = []
            if rule['is_rarely_used']:
                flags.append('Rarely Used')
            if rule['is_redundant']:
                flags.append('Redundant')
            if rule['is_high_performance']:
                flags.append('High Performer')
                
            top_rules.append({
                'rule_id': rule['rule_id'],
                'hit_count': rule['hit_count'],
                'match_frequency': f"{rule['match_frequency']:.2%}",
                'effectiveness_ratio': f"{rule['effectiveness_ratio']:.0%}",
                'flags': flags  # NEW: FR03-03 flags
            })
        
        # Get flagged rules summary
        flagged_summary = {
            'rarely_used': RulePerformance.objects.filter(is_rarely_used=True).count(),
            'redundant': RulePerformance.objects.filter(is_redundant=True).count(),
            'high_performance': RulePerformance.objects.filter(is_high_performance=True).count()
        }
        
        return Response({
            'summary': {
                'total_rules_tracked': total_rules,
                'total_hits_recorded': total_hits,
                'average_hits_per_rule': round(avg_hits_per_rule, 2),
                'flagged_rules_summary': flagged_summary  # NEW: FR03-03 summary
            },
            'top_performing_rules': top_rules,
            'all_rules': list(rules_with_metrics)
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_rule_hit_details(request, rule_id):
    """
    Get detailed hit information for a specific rule
    """
    try:
        hit_counter = RuleHitCounter()
        rule_stats = hit_counter.get_rule_hit_stats(rule_id)
        
        if not rule_stats:
            return Response({'error': f'Rule {rule_id} not found'}, status=404)
            
        # Get performance metrics for this specific rule
        try:
            rule_with_metrics = RulePerformance.objects.get(rule_id=rule_id)
            performance_data = {
                'match_frequency': f"{rule_with_metrics.match_frequency:.2%}",
                'effectiveness_ratio': f"{rule_with_metrics.effectiveness_ratio:.0%}",
                'average_evaluation_time': rule_with_metrics.average_evaluation_time,
                'flags': {
                    'is_rarely_used': rule_with_metrics.is_rarely_used,
                    'is_redundant': rule_with_metrics.is_redundant,
                    'is_high_performance': rule_with_metrics.is_high_performance
                }
            }
        except RulePerformance.DoesNotExist:
            performance_data = {}
            
        return Response({
            'rule_id': rule_stats['rule_id'],
            'hit_count': rule_stats['hit_count'],
            'last_triggered': rule_stats['last_triggered'],
            'performance_metrics': performance_data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)