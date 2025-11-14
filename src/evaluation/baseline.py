"""
Random baseline for comparison.
Generates random rankings of tests for comparison with LIBRO.
"""

import random
from typing import Dict, List
import copy

class RandomBaseline:
    """Generate random baseline rankings for comparison."""
    
    def __init__(self, seed: int = 42):
        """
        Initialize random baseline.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
    
    def generate_random_ranking(self, results: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Generate random ranking for each bug.
        
        Takes LIBRO results and randomly shuffles the rankings.
        
        Args:
            results: LIBRO results with rankings
            
        Returns:
            New results dict with random rankings
        """
        random_results = copy.deepcopy(results)
        
        for bug_id, result in random_results.items():
            ranking = result.get('ranking', [])
            
            if ranking:
                # Randomly shuffle the ranking
                random.shuffle(ranking)
                result['ranking'] = ranking
        
        return random_results
    
    def run_multiple_trials(self, results: Dict[str, Dict], 
                          n_trials: int = 100) -> List[Dict[str, Dict]]:
        """
        Run multiple random baseline trials.
        
        Args:
            results: LIBRO results
            n_trials: Number of random trials
            
        Returns:
            List of random result dicts
        """
        random_trials = []
        
        for i in range(n_trials):
            # Use different seed for each trial
            random.seed(self.seed + i)
            random_result = self.generate_random_ranking(results)
            random_trials.append(random_result)
        
        return random_trials
    
    def aggregate_trials(self, trials: List[Dict[str, Dict]], 
                        k_values: List[int] = [1, 3, 5]) -> Dict:
        """
        Aggregate metrics across multiple trials.
        
        Args:
            trials: List of trial results
            k_values: K values for metrics
            
        Returns:
            Aggregated metrics with mean and std
        """
        from src.evaluation.metrics import EvaluationMetrics
        
        metrics_calculator = EvaluationMetrics()
        
        # Calculate metrics for each trial
        all_metrics = []
        for trial in trials:
            trial_metrics = metrics_calculator.calculate_all_metrics(trial, k_values)
            all_metrics.append(trial_metrics)
        
        # Aggregate
        aggregated = {
            'n_trials': len(trials),
            'brt_rate': {
                'mean': sum(m['brt_rate'] for m in all_metrics) / len(all_metrics),
                'std': 0  # Will calculate below
            },
            'acc_at_k': {},
            'wef_at_k': {}
        }
        
        # Aggregate acc@k
        for k in k_values:
            acc_key = f'acc@{k}'
            precisions = [m['acc_at_k'][acc_key]['precision'] for m in all_metrics]
            
            aggregated['acc_at_k'][acc_key] = {
                'mean': sum(precisions) / len(precisions),
                'std': (sum((p - sum(precisions)/len(precisions))**2 for p in precisions) / len(precisions)) ** 0.5
            }
        
        # Aggregate wef@k
        for k in k_values:
            wef_key = f'wef@{k}'
            averages = [m['wef_at_k'][wef_key]['average'] for m in all_metrics]
            
            aggregated['wef_at_k'][wef_key] = {
                'mean': sum(averages) / len(averages),
                'std': (sum((a - sum(averages)/len(averages))**2 for a in averages) / len(averages)) ** 0.5
            }
        
        return aggregated
