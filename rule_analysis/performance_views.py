from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import pandas as pd
from .models import RulePerformance, PerformanceSnapshot
from .performance_analyzer import RulePerformanceProfiler
from data_management.models import UploadedFile

@api_view(['POST'])
def analyze_rule_performance(request):
    """
    FR03: Analyze rule performance from traffic data
    """
    try:
        traffic_file_id = request.data.get('traffic_file_id')
        snapshot_name = request.data.get('snapshot_name', 'Performance Analysis')
        
        # Get traffic file
        traffic_file = UploadedFile.objects.get(id=traffic_file_id)
        
        # For now, use mock traffic data - replace with actual file processing
        traffic_data = pd.DataFrame([
            {'rule_id': '1001', 'timestamp': '2024-01-15 10:30:00', 'action': 'blocked', 'false_positive': False},
            {'rule_id': '1001', 'timestamp': '2024-01-15 10:31:00', 'action': 'blocked', 'false_positive': False},
            {'rule_id': '1002', 'timestamp': '2024-01-15 10:32:00', 'action': 'blocked', 'false_positive': True},
            {'rule_id': '1003', 'timestamp': '2024-01-15 10:33:00', 'action': 'blocked', 'false_positive': False},
            {'rule_id': '1004', 'timestamp': '2024-01-15 10:34:00', 'action': 'blocked', 'false_positive': False},
            {'rule_id': '1005', 'timestamp': '2024-01-15 10:35:00', 'action': 'passed', 'false_positive': False},
        ])
        
        # Mock rules data
        rules_data = pd.DataFrame([
            {'rule_id': '1001', 'category': 'SQLi', 'complexity': 'high'},
            {'rule_id': '1002', 'category': 'XSS', 'complexity': 'medium'},
            {'rule_id': '1003', 'category': 'RFI', 'complexity': 'low'},
            {'rule_id': '1004', 'category': 'LFI', 'complexity': 'medium'},
            {'rule_id': '1005', 'category': 'RCE', 'complexity': 'high'},
        ])
        
        # Analyze performance
        profiler = RulePerformanceProfiler()
        performance_data = profiler.analyze_traffic_data(rules_data, traffic_data)
        
        # Save to database
        results = profiler.save_performance_data(performance_data, snapshot_name)
        
        return Response({
            'status': 'success',
            'message': 'Rule performance analysis completed successfully!',
            'snapshot_id': results['snapshot_id'],
            'analysis_summary': {
                'total_rules_analyzed': results['total_rules_analyzed'],
                'rarely_used_rules': results['rarely_used_rules'],
                'redundant_rules': results['redundant_rules'],
                'high_performance_rules': results['high_performance_rules']
            },
            'performance_data': performance_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Performance analysis failed: {str(e)}'
        }, status=400)

@api_view(['GET'])
def get_performance_snapshot(request, snapshot_id):
    """
    Get performance analysis results
    """
    try:
        snapshot = PerformanceSnapshot.objects.get(id=snapshot_id)
        
        # Get detailed rule performance data
        rule_performance = RulePerformance.objects.all().values()
        
        return Response({
            'snapshot_name': snapshot.snapshot_name,
            'summary_metrics': {
                'total_rules': snapshot.total_rules,
                'rarely_used_rules': snapshot.rarely_used_count,
                'redundant_rules': snapshot.redundant_count,
                'high_performance_rules': snapshot.high_performance_count,
                'average_hit_count': snapshot.average_hit_count
            },
            'rule_performance': list(rule_performance),
            'created_at': snapshot.created_at
        })
        
    except PerformanceSnapshot.DoesNotExist:
        return Response({'error': 'Performance snapshot not found'}, status=404)

@api_view(['GET'])
def get_rule_performance_dashboard(request):
    """
    Get overall performance dashboard data
    """
    try:
        # Get all performance data
        rules = RulePerformance.objects.all()
        
        # Calculate overall metrics
        total_rules = rules.count()
        rarely_used = rules.filter(is_rarely_used=True).count()
        redundant = rules.filter(is_redundant=True).count()
        high_perf = rules.filter(is_high_performance=True).count()
        
        # Performance statistics
        if total_rules > 0:
            avg_hit_count = sum(r.hit_count for r in rules) / total_rules
            avg_effectiveness = sum(r.effectiveness_ratio for r in rules) / total_rules
        else:
            avg_hit_count = 0
            avg_effectiveness = 0
        
        return Response({
            'overview_metrics': {
                'total_rules_monitored': total_rules,
                'rarely_used_rules': rarely_used,
                'redundant_rules': redundant,
                'high_performance_rules': high_perf,
                'average_hit_count': round(avg_hit_count, 2),
                'average_effectiveness': f"{avg_effectiveness:.1%}"
            },
            'performance_breakdown': {
                'efficiency_score': self.calculate_efficiency_score(rules),
                'optimization_opportunities': rarely_used + redundant,
                'top_performers': self.get_top_performers(rules)
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

def calculate_efficiency_score(self, rules):
    """Calculate overall WAF efficiency score"""
    if not rules:
        return 0
    
    total_score = 0
    for rule in rules:
        # Score based on hit count and effectiveness
        hit_score = min(rule.hit_count / 100, 1.0)  # Normalize hit count
        effectiveness_score = rule.effectiveness_ratio
        total_score += (hit_score * 0.6 + effectiveness_score * 0.4)
    
    return round((total_score / len(rules)) * 100, 1)

def get_top_performers(self, rules, limit=5):
    """Get top performing rules"""
    scored_rules = []
    for rule in rules:
        score = (rule.hit_count * 0.6 + rule.effectiveness_ratio * 100 * 0.4)
        scored_rules.append({
            'rule_id': rule.rule_id,
            'hit_count': rule.hit_count,
            'effectiveness': f"{rule.effectiveness_ratio:.1%}",
            'performance_score': round(score, 1)
        })
    
    return sorted(scored_rules, key=lambda x: x['performance_score'], reverse=True)[:limit]

@api_view(['GET'])
def get_ranking_comparison(request, session_id):
    """
    FR05-02: Get detailed ranking comparison with FR03 insights
    """
    try:
        session = RuleRankingSession.objects.get(id=session_id)
        
        # Prepare comparison data
        comparison_data = []
        for current_rule in session.original_rules_order:
            rule_id = current_rule['rule_id']
            current_pos = current_rule['position']
            
            # Find in proposed order
            proposed_rule = next(
                (r for r in session.optimized_rules_order if r['rule_id'] == rule_id), 
                None
            )
            
            if proposed_rule:
                comparison_data.append({
                    'rule_id': rule_id,
                    'current_position': current_pos,
                    'proposed_position': proposed_rule['new_position'],
                    'position_change': current_pos - proposed_rule['new_position'],
                    'hit_count': proposed_rule.get('hit_count', 0),
                    'priority_score': proposed_rule.get('priority_score', 0),
                    'category': proposed_rule.get('rule_data', {}).get('category', 'Unknown'),
                    'is_high_performance': proposed_rule.get('is_high_performance', False),
                    'is_rarely_used': proposed_rule.get('is_rarely_used', False)
                })
        
        # ADD FR03 INSIGHTS
        fr03_insights = {
            'performance_metrics_used': [
                'hit_count',
                'effectiveness_ratio', 
                'match_frequency',
                'efficiency_flags'
            ],
            'total_rules_with_performance_data': RulePerformance.objects.count(),
            'high_performance_rules_prioritized': len([r for r in comparison_data if r.get('is_high_performance', False)]),
            'rarely_used_rules_demoted': len([r for r in comparison_data if r.get('is_rarely_used', False) and r['position_change'] < 0])
        }
        
        return Response({
            'session_name': session.name,
            'improvement': session.performance_improvement,
            'status': session.status,
            'total_rules': len(comparison_data),
            'comparison_data': comparison_data,
            'summary': {
                'rules_moved_up': len([r for r in comparison_data if r['position_change'] > 0]),
                'rules_moved_down': len([r for r in comparison_data if r['position_change'] < 0]),
                'rules_unchanged': len([r for r in comparison_data if r['position_change'] == 0]),
                'average_position_change': sum(r['position_change'] for r in comparison_data) / len(comparison_data) if comparison_data else 0
            },
            'fr03_insights': fr03_insights  # NEW: FR03 integration insights
        })
        
    except RuleRankingSession.DoesNotExist:
        return Response({'error': 'Ranking session not found'}, status=404)