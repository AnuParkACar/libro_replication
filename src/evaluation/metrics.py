"""
Evaluation metrics for LIBRO replication.
Implements acc@k, wef@k, and other metrics from the paper.
"""

from typing import List, Dict, Tuple
import numpy as np
from collections import defaultdict

class EvaluationMetrics:
    """Calculate evaluation metrics for bug reproduction."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        pass
    
    def calculate_brt_rate(self, results: Dict[str, Dict]) -> float:
        """
        Calculate Bug Reproduction Test (BRT) rate.
        
        BRT rate = (# bugs with ≥1 BRT) / (total bugs)
        
        Args:
            results: Dict mapping bug_id to result dict
            
        Returns:
            BRT rate as float between 0 and 1
        """
        total_bugs = len(results)
        bugs_with_brt = sum(1 for r in results.values() 
                           if r.get('metrics', {}).get('num_brt', 0) > 0)
        
        return bugs_with_brt / total_bugs if total_bugs > 0 else 0
    
    def calculate_acc_at_k(self, results: Dict[str, Dict], k: int) -> Tuple[int, float]:
        """
        Calculate acc@k: number of bugs with BRT in top-k ranked tests.
        
        Args:
            results: Dict mapping bug_id to result dict with 'ranking'
            k: Top-k threshold
            
        Returns:
            Tuple of (count, precision)
            count: Number of bugs with BRT in top-k
            precision: count / number of bugs with ranking
        """
        count = 0
        bugs_with_ranking = 0
        
        for bug_id, result in results.items():
            ranking = result.get('ranking', [])
            
            if not ranking:
                continue
            
            bugs_with_ranking += 1
            
            # Check if any test in top-k is a BRT
            top_k = ranking[:k]
            for test in top_k:
                if test.get('classification') == 'BRT':
                    count += 1
                    break
        
        precision = count / bugs_with_ranking if bugs_with_ranking > 0 else 0
        
        return count, precision
    
    def calculate_wef_at_k(self, results: Dict[str, Dict], k: int) -> Dict[str, float]:
        """
        Calculate wef@k: wasted effort at k.
        
        wef = number of non-BRT tests inspected before first BRT
        
        Args:
            results: Dict mapping bug_id to result dict with 'ranking'
            k: Consider top-k tests
            
        Returns:
            Dict with 'total', 'average', 'median' wasted effort
        """
        wef_values = []
        
        for bug_id, result in results.items():
            ranking = result.get('ranking', [])
            
            if not ranking:
                continue
            
            # Calculate wasted effort for this bug
            wef = 0
            found_brt = False
            
            for i, test in enumerate(ranking[:k]):
                if test.get('classification') == 'BRT':
                    found_brt = True
                    break
                else:
                    wef += 1
            
            # If no BRT found in top-k, wef is k
            if not found_brt:
                wef = k
            
            wef_values.append(wef)
        
        if not wef_values:
            return {'total': 0, 'average': 0, 'median': 0}
        
        return {
            'total': sum(wef_values),
            'average': np.mean(wef_values),
            'median': np.median(wef_values)
        }
    
    def calculate_all_metrics(self, results: Dict[str, Dict], 
                             k_values: List[int] = [1, 3, 5]) -> Dict:
        """
        Calculate all metrics for the results.
        
        Args:
            results: Complete results dict
            k_values: List of k values to calculate metrics for
            
        Returns:
            Dict with all metrics
        """
        metrics = {
            'brt_rate': self.calculate_brt_rate(results),
            'total_bugs': len(results),
            'bugs_reproduced': sum(1 for r in results.values() 
                                  if r.get('metrics', {}).get('num_brt', 0) > 0),
            'total_brt': sum(r.get('metrics', {}).get('num_brt', 0) 
                           for r in results.values()),
            'acc_at_k': {},
            'wef_at_k': {}
        }
        
        # Calculate acc@k and wef@k for each k
        for k in k_values:
            count, precision = self.calculate_acc_at_k(results, k)
            metrics['acc_at_k'][f'acc@{k}'] = {
                'count': count,
                'precision': precision
            }
            
            wef = self.calculate_wef_at_k(results, k)
            metrics['wef_at_k'][f'wef@{k}'] = wef
        
        return metrics
    
    def compare_to_baseline(self, libro_results: Dict[str, Dict],
                           baseline_results: Dict[str, Dict],
                           k_values: List[int] = [1, 3, 5]) -> Dict:
        """
        Compare LIBRO results to baseline (e.g., random).
        
        Args:
            libro_results: Results from LIBRO
            baseline_results: Results from baseline
            k_values: K values to compare
            
        Returns:
            Comparison dict
        """
        libro_metrics = self.calculate_all_metrics(libro_results, k_values)
        baseline_metrics = self.calculate_all_metrics(baseline_results, k_values)
        
        comparison = {
            'libro': libro_metrics,
            'baseline': baseline_metrics,
            'improvements': {}
        }
        
        # Calculate improvements
        for k in k_values:
            acc_key = f'acc@{k}'
            libro_acc = libro_metrics['acc_at_k'][acc_key]['precision']
            baseline_acc = baseline_metrics['acc_at_k'][acc_key]['precision']
            
            improvement = libro_acc - baseline_acc
            improvement_pct = (improvement / baseline_acc * 100) if baseline_acc > 0 else 0
            
            comparison['improvements'][acc_key] = {
                'absolute': improvement,
                'percentage': improvement_pct
            }
        
        return comparison
