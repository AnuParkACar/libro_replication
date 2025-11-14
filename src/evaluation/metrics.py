"""Evaluation metrics for LIBRO replication."""

import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class EvaluationMetrics:
    """Calculate evaluation metrics for test generation."""
    
    @staticmethod
    def accuracy_at_k(rankings: List[Dict], k: int = 1) -> float:
        """
        Calculate accuracy@k: proportion of bugs with BRT in top-k.
        
        Args:
            rankings: List of ranking results per bug
            k: Top-k threshold
            
        Returns:
            Accuracy@k as proportion (0.0 to 1.0)
        """
        if not rankings:
            return 0.0
        
        bugs_with_brt_in_topk = 0
        total_bugs = len(rankings)
        
        for ranking in rankings:
            # Check if any test in top-k is a BRT
            top_k_tests = ranking.get('ranked_tests', [])[:k]
            
            for test in top_k_tests:
                if test.get('is_brt', False):
                    bugs_with_brt_in_topk += 1
                    break  # Count bug once
        
        return bugs_with_brt_in_topk / total_bugs if total_bugs > 0 else 0.0
    
    @staticmethod
    def wasted_effort(rankings: List[Dict]) -> float:
        """
        Calculate wasted effort: average rank of first BRT.
        
        Lower is better. Minimum is 1.0 (BRT at rank 1).
        Only calculated for bugs that have BRTs.
        
        Args:
            rankings: List of ranking results per bug
            
        Returns:
            Average rank of first BRT
        """
        first_brt_ranks = []
        
        for ranking in rankings:
            ranked_tests = ranking.get('ranked_tests', [])
            
            # Find rank of first BRT (1-indexed)
            for rank, test in enumerate(ranked_tests, start=1):
                if test.get('is_brt', False):
                    first_brt_ranks.append(rank)
                    break
        
        if not first_brt_ranks:
            return float('inf')  # No BRTs found
        
        return np.mean(first_brt_ranks)
    
    @staticmethod
    def wasted_effort_median(rankings: List[Dict]) -> float:
        """Calculate median wasted effort."""
        first_brt_ranks = []
        
        for ranking in rankings:
            ranked_tests = ranking.get('ranked_tests', [])
            
            for rank, test in enumerate(ranked_tests, start=1):
                if test.get('is_brt', False):
                    first_brt_ranks.append(rank)
                    break
        
        if not first_brt_ranks:
            return float('inf')
        
        return np.median(first_brt_ranks)
    
    @staticmethod
    def reproduction_rate(results: Dict[str, Dict]) -> float:
        """
        Calculate bug reproduction rate.
        
        Args:
            results: Dict mapping bug_id to results
            
        Returns:
            Proportion of bugs with at least one BRT
        """
        if not results:
            return 0.0
        
        bugs_with_brt = sum(
            1 for r in results.values()
            if r.get('metrics', {}).get('has_brt', False)
        )
        
        return bugs_with_brt / len(results)
    
    @staticmethod
    def calculate_all_metrics(results: Dict[str, Dict], 
                             k_values: List[int] = [1, 3, 5, 10]) -> Dict:
        """
        Calculate all evaluation metrics.
        
        Args:
            results: Dict mapping bug_id to results with rankings
            k_values: List of k values for acc@k
            
        Returns:
            Dict with all metrics
        """
        # Extract rankings (only for bugs with BRTs)
        rankings = []
        for bug_id, result in results.items():
            if result.get('metrics', {}).get('has_brt', False):
                rankings.append({
                    'bug_id': bug_id,
                    'ranked_tests': result.get('ranking', [])
                })
        
        metrics = {
            'reproduction_rate': EvaluationMetrics.reproduction_rate(results),
            'bugs_reproduced': len(rankings),
            'total_bugs': len(results),
        }
        
        # Calculate acc@k for different k values
        for k in k_values:
            metrics[f'acc@{k}'] = EvaluationMetrics.accuracy_at_k(rankings, k)
        
        # Calculate wasted effort
        if rankings:
            metrics['wasted_effort_mean'] = EvaluationMetrics.wasted_effort(rankings)
            metrics['wasted_effort_median'] = EvaluationMetrics.wasted_effort_median(rankings)
        else:
            metrics['wasted_effort_mean'] = float('inf')
            metrics['wasted_effort_median'] = float('inf')
        
        return metrics
    
    @staticmethod
    def calculate_per_project_metrics(results: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate metrics per project."""
        per_project = {}
        
        # Group by project
        for bug_id, result in results.items():
            project = result.get('project', bug_id.split('-')[0])
            
            if project not in per_project:
                per_project[project] = {}
            
            per_project[project][bug_id] = result
        
        # Calculate metrics for each project
        project_metrics = {}
        for project, project_results in per_project.items():
            project_metrics[project] = EvaluationMetrics.calculate_all_metrics(
                project_results
            )
        
        return project_metrics


class RandomBaseline:
    """Random baseline for comparison."""
    
    @staticmethod
    def random_ranking(tests: List[Dict], seed: int = 42) -> List[Dict]:
        """Randomly shuffle tests."""
        np.random.seed(seed)
        shuffled = tests.copy()
        np.random.shuffle(shuffled)
        return shuffled
    
    @staticmethod
    def evaluate_random_baseline(results: Dict[str, Dict], 
                                 num_trials: int = 100) -> Dict:
        """
        Evaluate random baseline with multiple trials.
        
        Args:
            results: Results dict with rankings
            num_trials: Number of random trials
            
        Returns:
            Dict with average metrics across trials
        """
        logger.info(f"Evaluating random baseline ({num_trials} trials)...")
        
        all_trial_metrics = []
        
        for trial in range(num_trials):
            # Create random rankings
            trial_results = {}
            
            for bug_id, result in results.items():
                trial_result = result.copy()
                
                # Randomly shuffle ranking if exists
                if 'ranking' in result and result['ranking']:
                    trial_result['ranking'] = RandomBaseline.random_ranking(
                        result['ranking'],
                        seed=42 + trial
                    )
                
                trial_results[bug_id] = trial_result
            
            # Calculate metrics for this trial
            trial_metrics = EvaluationMetrics.calculate_all_metrics(trial_results)
            all_trial_metrics.append(trial_metrics)
        
        # Average across trials
        averaged_metrics = {}
        
        # Get all metric keys from first trial
        metric_keys = all_trial_metrics[0].keys()
        
        for key in metric_keys:
            values = [m[key] for m in all_trial_metrics if m[key] != float('inf')]
            
            if values:
                averaged_metrics[key] = np.mean(values)
                averaged_metrics[f'{key}_std'] = np.std(values)
            else:
                averaged_metrics[key] = float('inf')
                averaged_metrics[f'{key}_std'] = 0.0
        
        return averaged_metrics
