#!/usr/bin/env python3
"""
Ablation studies: Test impact of different components.
"""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from src.evaluation.metrics import EvaluationMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_sampling_budget(results: Dict[str, Dict]):
    """Analyze impact of number of samples generated."""
    
    print("\n" + "="*80)
    print("Ablation 1: Sampling Budget (n)")
    print("="*80)
    
    # Simulate different sampling budgets by subsampling
    metrics_calc = EvaluationMetrics()
    
    n_values = [1, 3, 5, 10, 15, 20]
    reproduction_rates = []
    
    for n in n_values:
        # Create subset with first n tests
        subset_results = {}
        
        for bug_id, result in results.items():
            subset_result = result.copy()
            
            # Subsample generated tests
            generated = result.get('generated_tests', [])[:n]
            fib = result.get('fib_tests', [])[:n]
            brt = result.get('brt_tests', [])[:n]
            ranking = result.get('ranking', [])[:n]
            
            subset_result['generated_tests'] = generated
            subset_result['fib_tests'] = fib
            subset_result['brt_tests'] = brt
            subset_result['ranking'] = ranking
            subset_result['metrics'] = {
                'num_generated': len(generated),
                'num_fib': len(fib),
                'num_brt': len(brt),
                'has_brt': len(brt) > 0
            }
            
            subset_results[bug_id] = subset_result
        
        # Calculate metrics
        rate = metrics_calc.calculate_brt_rate(subset_results)
        reproduction_rates.append(rate * 100)
        
        print(f"  n={n:2d}: {rate*100:5.1f}% reproduction rate")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(n_values, reproduction_rates, marker='o', linewidth=2, markersize=8)
    plt.xlabel('Number of Samples (n)', fontsize=12)
    plt.ylabel('Bug Reproduction Rate (%)', fontsize=12)
    plt.title('Impact of Sampling Budget on Reproduction Rate', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Expected logarithmic trend line
    if len(n_values) > 3:
        # Fit logarithmic curve
        log_n = np.log(n_values)
        coeffs = np.polyfit(log_n, reproduction_rates, 1)
        trend_line = coeffs[0] * log_n + coeffs[1]
        plt.plot(n_values, trend_line, '--', color='red', alpha=0.5, 
                label=f'Log trend: y={coeffs[0]:.1f}·ln(x)+{coeffs[1]:.1f}')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig('results/ablation_sampling_budget.png', dpi=300)
    print(f"\n✓ Plot saved to: results/ablation_sampling_budget.png")
    
    return {
        'n_values': n_values,
        'reproduction_rates': reproduction_rates
    }

def analyze_agreement_threshold(results: Dict[str, Dict]):
    """Analyze impact of agreement threshold for selection."""
    
    print("\n" + "="*80)
    print("Ablation 2: Agreement Threshold")
    print("="*80)
    
    from src.core.test_ranker import TestRanker
    
    thresholds = [1, 2, 3, 5, 10]
    precision_values = []
    recall_values = []
    
    for threshold in thresholds:
        ranker = TestRanker(agreement_threshold=threshold)
        
        selected_bugs = 0
        selected_with_brt = 0
        total_with_brt = 0
        
        for bug_id, result in results.items():
            fib_tests = result.get('fib_tests', [])
            brt_tests = result.get('brt_tests', [])
            
            if not fib_tests:
                continue
            
            total_with_brt += 1 if brt_tests else 0
            
            # Try to select with this threshold
            bug_report = {'title': '', 'description': ''}
            ranking = ranker.select_and_rank(fib_tests, bug_report)
            
            if ranking:  # Bug was selected
                selected_bugs += 1
                if brt_tests:
                    selected_with_brt += 1
        
        precision = selected_with_brt / selected_bugs if selected_bugs > 0 else 0
        recall = selected_with_brt / total_with_brt if total_with_brt > 0 else 0
        
        precision_values.append(precision)
        recall_values.append(recall)
        
        print(f"  Threshold={threshold:2d}: Precision={precision*100:5.1f}%, "
              f"Recall={recall*100:5.1f}%, Selected={selected_bugs}/{len(results)}")
    
    # Plot precision-recall curve
    plt.figure(figsize=(10, 6))
    plt.plot(recall_values, precision_values, marker='o', linewidth=2, markersize=8)
    
    for i, t in enumerate(thresholds):
        plt.annotate(f'T={t}', (recall_values[i], precision_values[i]),
                    textcoords="offset points", xytext=(5,5), fontsize=9)
    
    plt.xlabel('Recall', fontsize=12)
    plt.ylabel('Precision', fontsize=12)
    plt.title('Precision-Recall Trade-off for Agreement Threshold', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    
    plt.tight_layout()
    plt.savefig('results/ablation_threshold.png', dpi=300)
    print(f"\n✓ Plot saved to: results/ablation_threshold.png")
    
    return {
        'thresholds': thresholds,
        'precision': precision_values,
        'recall': recall_values
    }

def analyze_prompt_examples(results_by_config: Dict[str, Dict]):
    """
    Analyze impact of number of examples in prompt.
    
    Note: This requires results from multiple runs with different configs.
    If not available, will show placeholder.
    """
    
    print("\n" + "="*80)
    print("Ablation 3: Number of Prompt Examples")
    print("="*80)
    
    if len(results_by_config) < 2:
        print("  ⚠️  Need multiple configurations to compare")
        print("  Run evaluation with 0, 1, 2 examples separately")
        return None
    
    metrics_calc = EvaluationMetrics()
    
    example_counts = []
    reproduction_rates = []
    
    for config_name, results in results_by_config.items():
        # Extract number of examples from config name
        n_examples = int(config_name.split('_')[-1])
        example_counts.append(n_examples)
        
        rate = metrics_calc.calculate_brt_rate(results)
        reproduction_rates.append(rate * 100)
        
        print(f"  Examples={n_examples}: {rate*100:5.1f}% reproduction rate")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.bar(example_counts, reproduction_rates, edgecolor='black', alpha=0.7)
    plt.xlabel('Number of Examples in Prompt', fontsize=12)
    plt.ylabel('Bug Reproduction Rate (%)', fontsize=12)
    plt.title('Impact of Few-Shot Examples', fontsize=14)
    plt.xticks(example_counts)
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/ablation_examples.png', dpi=300)
    print(f"\n✓ Plot saved to: results/ablation_examples.png")
    
    return {
        'example_counts': example_counts,
        'reproduction_rates': reproduction_rates
    }

def main():
    """Run ablation studies."""
    
    print("="*80)
    print("ABLATION STUDIES")
    print("="*80)
    
    # Load results
    results_file = Path("results/ghrb_evaluation/final_results.json")
    if not results_file.exists():
        results_file = Path("results/day3_batch/final_results.json")
    
    if not results_file.exists():
        print("❌ Results file not found!")
        return
    
    with open(results_file) as f:
        results = json.load(f)
    
    print(f"Loaded results for {len(results)} bugs")
    
    # Run ablations
    sampling_results = analyze_sampling_budget(results)
    threshold_results = analyze_agreement_threshold(results)
    
    # Save ablation results
    ablation_report = {
        'sampling_budget': sampling_results,
        'agreement_threshold': threshold_results
    }
    
    output_file = Path("results/ablation_report.json")
    with open(output_file, 'w') as f:
        json.dump(ablation_report, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ ABLATION STUDIES COMPLETE")
    print("="*80)
    print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
