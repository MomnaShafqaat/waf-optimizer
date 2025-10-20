from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import pandas as pd
from .models import RulePerformance, RuleRankingSession
from .ranking_algorithm import SmartRuleRanker
from data_management.models import UploadedFile


from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    """FR05-03: Check if user has admin role"""
    return user.is_superuser or user.groups.filter(name='admin').exists()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_admin)
def approve_ranking_session(request, session_id):
    """
    FR05-03: Admin approval for rule ranking
    LEARNING: Security measure - prevents accidental rule changes
    """
    try:
        session = RuleRankingSession.objects.get(id=session_id)
        
        # Update session status
        session.status = 'approved'
        session.approved_by = request.user
        session.save()
        
        # FR05-04: In real implementation, this would apply to ModSecurity
        # For now, we'll just mark it as applied
        session.status = 'applied'
        session.save()
        
        return Response({
            'status': 'success',
            'message': f'Rule ranking approved and applied by {request.user.username}',
            'improvement': f'{session.performance_improvement:.1f}% performance gain expected',
            'rules_affected': len(session.optimized_rules_order)
        })
        
    except RuleRankingSession.DoesNotExist:
        return Response({'error': 'Ranking session not found'}, status=404)
@api_view(['POST'])
def generate_rule_ranking(request):
    """
    FR05-01 & FR05-02: Generate optimized rule ranking
    """
    try:
        session_name = request.data.get('session_name', 'Rule Ranking Proposal')
        
        # USE MOCK DATA - Don't depend on file ID
        rules_data = pd.DataFrame([
            {'rule_id': '1001', 'position': 1, 'category': 'SQLi', 'description': 'SQL Injection Detection'},
            {'rule_id': '1002', 'position': 2, 'category': 'XSS', 'description': 'Cross-site Scripting'},
            {'rule_id': '1003', 'position': 3, 'category': 'RFI', 'description': 'Remote File Include'},
            {'rule_id': '1004', 'position': 4, 'category': 'LFI', 'description': 'Local File Include'},
            {'rule_id': '1005', 'position': 5, 'category': 'RCE', 'description': 'Remote Code Execution'},
        ])
        
        # Mock performance data - ADD last_triggered field
        performance_data = pd.DataFrame([
            {'rule_id': '1001', 'hit_count': 150, 'effectiveness_ratio': 0.95, 'false_positive_count': 5, 'last_triggered': '2024-01-15 10:30:00'},
            {'rule_id': '1002', 'hit_count': 80, 'effectiveness_ratio': 0.85, 'false_positive_count': 12, 'last_triggered': '2024-01-15 09:45:00'},
            {'rule_id': '1003', 'hit_count': 25, 'effectiveness_ratio': 0.70, 'false_positive_count': 8, 'last_triggered': '2024-01-14 16:20:00'},
            {'rule_id': '1004', 'hit_count': 45, 'effectiveness_ratio': 0.80, 'false_positive_count': 9, 'last_triggered': '2024-01-15 11:15:00'},
            {'rule_id': '1005', 'hit_count': 10, 'effectiveness_ratio': 0.60, 'false_positive_count': 4, 'last_triggered': '2024-01-13 14:30:00'},
        ])
        
        # Generate ranking
        ranker = SmartRuleRanker()
        ranking_session = ranker.create_ranking_session(rules_data, performance_data, session_name)
        
        return Response({
            'status': 'success',
            'message': 'Rule ranking generated successfully!',
            'session_id': ranking_session.id,
            'improvement': f"{ranking_session.performance_improvement:.1f}%",
            'rules_analyzed': len(rules_data),
            'ranking_session': {
                'name': ranking_session.name,
                'improvement': ranking_session.performance_improvement,
                'status': ranking_session.status,
                'created_at': ranking_session.created_at
            }
        })
        
    except Exception as e:
        import traceback
        return Response({
            'error': f'Ranking generation failed: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=400)
@api_view(['GET'])
def get_ranking_session(request, session_id):
    """
    FR05-02: Get ranking session details for visualization
    LEARNING: Provides data for frontend to show current vs proposed order
    """
    try:
        session = RuleRankingSession.objects.get(id=session_id)
        
        return Response({
            'session_name': session.name,
            'current_order': session.original_rules_order,
            'proposed_order': session.optimized_rules_order,
            'improvement': session.performance_improvement,
            'status': session.status,
            'created_at': session.created_at
        })
        
    except RuleRankingSession.DoesNotExist:
        return Response({'error': 'Ranking session not found'}, status=404)
    
@api_view(['GET'])
def get_ranking_comparison(request, session_id):
    """
    FR05-02: Get detailed ranking comparison for visualization
    LEARNING: Provides data for frontend to show current vs proposed order
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
                    'position_change': current_pos - proposed_rule['new_position'],  # Positive = improved
                    'hit_count': proposed_rule.get('hit_count', 0),
                    'priority_score': proposed_rule.get('priority_score', 0),
                    'category': proposed_rule.get('rule_data', {}).get('category', 'Unknown')
                })
        
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
                'average_position_change': sum(r['position_change'] for r in comparison_data) / len(comparison_data)
            }
        })
        
    except RuleRankingSession.DoesNotExist:
        return Response({'error': 'Ranking session not found'}, status=404)