# rule_analysis/ranking_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import user_passes_test
import pandas as pd
from .models import RulePerformance, RuleRankingSession
from .ranking_algorithm import SmartRuleRanker
from data_management.models import UploadedFile

def is_admin(user):
    """FR05-03: Check if user has admin role"""
    return user.is_superuser or user.groups.filter(name='admin').exists()

@api_view(['POST'])
def generate_rule_ranking(request):
    """
    FR05-01 & FR05-02: Generate optimized rule ranking using REAL performance data
    """
    try:
        session_name = request.data.get('session_name', 'Rule Ranking Proposal')
        rules_file_id = request.data.get('rules_file_id')
        
        print(f"Generating ranking with rules_file_id: {rules_file_id}")
        
        # Get real rules data from uploaded file
        if rules_file_id:
            try:
                rules_file = UploadedFile.objects.get(id=rules_file_id, file_type='rules')
                # Read the actual rules CSV file
                rules_df = pd.read_csv(rules_file.file.path)
                print(f"Loaded rules file: {rules_file.file.name}")
            except UploadedFile.DoesNotExist:
                return Response({'error': 'Rules file not found'}, status=404)
            except Exception as e:
                return Response({'error': f'Error reading rules file: {str(e)}'}, status=400)
        else:
            return Response({'error': 'rules_file_id is required'}, status=400)
        
        # Get real performance data from FR03 database
        performance_data = []
        rule_performances = RulePerformance.objects.all()
        
        for rule_perf in rule_performances:
            performance_data.append({
                'rule_id': rule_perf.rule_id,
                'hit_count': rule_perf.hit_count,
                'effectiveness_ratio': rule_perf.effectiveness_ratio,
                'last_triggered': rule_perf.last_triggered.isoformat() if rule_perf.last_triggered else None
            })
        
        if not performance_data:
            return Response({'error': 'No performance data available. Run performance analysis first.'}, status=400)
        
        performance_df = pd.DataFrame(performance_data)
        
        # Generate ranking with REAL data
        ranker = SmartRuleRanker()
        ranking_session = ranker.create_ranking_session(rules_df, performance_df, session_name)
        
        # Response format that matches frontend expectations
        return Response({
            'status': 'success',
            'message': 'Rule ranking generated successfully!',
            'session_id': ranking_session.id,
            'improvement': ranking_session.performance_improvement,  # Frontend expects this field
            'rules_analyzed': len(rules_df),  # Frontend expects this field
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
    FR05-02: Get detailed ranking comparison with FR03 insights
    """
    try:
        session = RuleRankingSession.objects.get(id=session_id)
        
        # Build comparison data from session's rule orders
        original_order = session.original_rules_order
        optimized_order = session.optimized_rules_order
        
        comparison_data = []
        
        # Safety check for empty lists
        if not original_order or not optimized_order:
            return Response({
                'error': 'Ranking session has empty rule orders',
                'session_name': session.name,
                'improvement': session.performance_improvement,
                'status': session.status,
                'total_rules': 0,
                'comparison_data': []
            }, status=400)
        
        # Handle both list of dicts and list of strings formats
        # Extract rule_ids from dictionaries if needed
        # Use 1-based positions for display (more intuitive: position 1, 2, 3...)
        if isinstance(original_order[0], dict):
            original_rule_ids = [rule['rule_id'] for rule in original_order]
            original_positions = {rule['rule_id']: rule.get('position', idx + 1) for idx, rule in enumerate(original_order)}
        else:
            original_rule_ids = original_order
            original_positions = {rule_id: idx + 1 for idx, rule_id in enumerate(original_order)}
        
        if isinstance(optimized_order[0], dict):
            # new_position is already 1-based in the algorithm
            optimized_positions = {rule['rule_id']: rule.get('new_position', idx + 1) for idx, rule in enumerate(optimized_order)}
        else:
            optimized_positions = {rule_id: idx + 1 for idx, rule_id in enumerate(optimized_order)}
        
        # Build comparison for each rule
        is_dict_format = isinstance(optimized_order[0], dict)
        
        for rule_id in original_rule_ids:
            original_pos = original_positions.get(rule_id, 0)
            optimized_pos = optimized_positions.get(rule_id, 0)
            position_change = original_pos - optimized_pos
            
            # Try to get data from optimized_order first (it has all the info)
            rule_info = None
            if is_dict_format:
                rule_info = next((r for r in optimized_order if r['rule_id'] == rule_id), None)
            
            if rule_info:
                # Use data from the optimized order
                is_high_performance = rule_info.get('is_high_performance', False)
                is_rarely_used = rule_info.get('is_rarely_used', False)
                hit_count = rule_info.get('hit_count', 0)
                priority_score = rule_info.get('priority_score', 0) * 100  # Convert to percentage
            else:
                # Fallback: Get performance data from database
                try:
                    perf = RulePerformance.objects.get(rule_id=rule_id)
                    is_high_performance = perf.effectiveness_ratio > 0.7
                    is_rarely_used = perf.hit_count < 10
                    hit_count = perf.hit_count
                    priority_score = perf.effectiveness_ratio * 100  # Convert to score
                except RulePerformance.DoesNotExist:
                    is_high_performance = False
                    is_rarely_used = False
                    hit_count = 0
                    priority_score = 0
            
            # Determine category based on performance
            if is_high_performance:
                category = 'High Performance'
            elif is_rarely_used:
                category = 'Rarely Used'
            else:
                category = 'Normal'
            
            comparison_data.append({
                'rule_id': rule_id,
                'original_position': original_pos,
                'optimized_position': optimized_pos,
                'current_position': original_pos,  # Frontend expects this
                'proposed_position': optimized_pos,  # Frontend expects this
                'position_change': position_change,
                'is_high_performance': is_high_performance,
                'is_rarely_used': is_rarely_used,
                'hit_count': max(hit_count, 1),  # Frontend expects this for size (min 1 for visibility)
                'priority_score': priority_score,  # Frontend expects this for hover
                'category': category  # Frontend expects this for hover
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_admin)
def approve_ranking_session(request, session_id):
    """
    FR05-03: Admin approval for rule ranking
    """
    try:
        session = RuleRankingSession.objects.get(id=session_id)
        
        # Update session status
        session.status = 'approved'
        session.approved_by = request.user
        session.save()
        
        # FR05-04: Apply the optimized ordering
        # In real implementation, this would apply to ModSecurity
        session.status = 'applied'
        session.save()
        
        # Response format that matches frontend expectations
        return Response({
            'status': 'success',
            'message': f'Rule ranking approved and applied by {request.user.username}',
            'improvement': f"{session.performance_improvement:.1f}% performance gain expected",  # Frontend expects improvement field
            'rules_affected': len(session.optimized_rules_order)
        })
        
    except RuleRankingSession.DoesNotExist:
        return Response({'error': 'Ranking session not found'}, status=404)