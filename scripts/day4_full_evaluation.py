#!/usr/bin/env python3
"""
Day 4: Complete evaluation pipeline.

This script runs the full evaluation including:
1. Single model evaluation
2. Multi-model ablation study
3. Baseline comparison
4. Visualization generation
"""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path
import argparse
import time

from src.evaluation.multi_model_runner import MultiModelRunner
from src.evaluation.metrics import EvaluationMetrics
from src.evaluation.visualizations import Visualizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/day4_evaluation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run Day 4 evaluation pipeline")
    parser.add_argument('--models', nargs='+', 
                       default=["starcoder2-3b", "starcoder2-7b", "deepseek-coder-7b"],
                       help="Models to evaluate")
    parser.add_argument('--num-bugs', type=int, default=30,
                       help="Number of bugs to evaluate")
    parser.add_argument('--skip-processing', action='store_true',
                       help="Skip batch processing (use existing results)")
    parser.add_argument('--skip-baseline', action='store_true',
                       help="Skip baseline comparison")
    parser.add_argument('--baseline-trials', type=int, default=100,
                       help="Number of random baseline trials")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DAY 4: COMPLETE EVALUATION PIPELINE")
    print("=" * 80)
    
    # Load bug reports
    print("\n📂 Loading bug reports...")
    with open("data/bugs/bug_reports.json") as f:
        all_bugs = json.load(f)
    
    bugs_to_process = all_bugs[:args.num_bugs]
    
    print(f"  Selected {len(bugs_to_process)} bugs for evaluation")
    
    # Initialize runner
    runner = MultiModelRunner(output_dir="results/day4_evaluation")
    
    # Phase 1: Multi-model evaluation
    if not args.skip_processing:
        print("\n" + "=" * 80)
        print("PHASE 1: MULTI-MODEL EVALUATION")
        print("=" * 80)
        print(f"\nEvaluating models: {', '.join(args.models)}")
        print(f"⚠️  Estimated time: {len(args.models) * 2}-{len(args.models) * 4} hours\n")
        
        start_time = time.time()
        
        all_results = runner.run_multi_model_evaluation(
            bugs=bugs_to_process,
            models=args.models,
            resume=True
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Multi-model evaluation complete in {elapsed/3600:.2f} hours")
    else:
        print("\n⏭️  Skipping batch processing (using existing results)")
        
        # Load existing results
        all_results = {}
        for model in args.models:
            results_file = Path(f"results/day4_evaluation/{model}/results.json")
            metrics_file = Path(f"results/day4_evaluation/{model}/metrics.json")
            
            if results_file.exists() and metrics_file.exists():
                with open(results_file) as f:
                    results = json.load(f)
                with open(metrics_file) as f:
                    metrics = json.load(f)
                
                all_results[model] = {
                    'model': model,
                    'results': results,
                    'metrics': metrics
                }
                print(f"  ✓ Loaded {model}")
    
    # Phase 2: Baseline comparison
    if not args.skip_baseline and all_results:
        print("\n" + "=" * 80)
        print("PHASE 2: BASELINE COMPARISON")
        print("=" * 80)
        
        # Use first model for baseline comparison
        primary_model = args.models[0]
        print(f"\nComparing {primary_model} to random baseline...")
        print(f"Running {args.baseline_trials} random trials...\n")
        
        comparison = runner.evaluate_with_baseline(
            bugs=bugs_to_process,
            model_key=primary_model,
            num_random_trials=args.baseline_trials
        )
        
        # Display comparison
        print("\n" + "=" * 80)
        print("BASELINE COMPARISON RESULTS")
        print("=" * 80)
        
        model_metrics = comparison['model_metrics']
        baseline_metrics = comparison['baseline_metrics']
        
        print(f"\n{'Metric':<25} {'LIBRO':<15} {'Random':<15} {'Improvement'}")
        print("=" * 70)
        
        for metric in ['reproduction_rate', 'acc@1', 'acc@3', 'acc@5', 'wasted_effort_mean']:
            libro_val = model_metrics.get(metric, 0)
            random_val = baseline_metrics.get(metric, 0)
            
            if 'rate' in metric or 'acc@' in metric:
                improvement = (libro_val - random_val) / random_val * 100 if random_val > 0 else 0
                print(f"{metric:<25} {libro_val*100:>6.1f}%        {random_val*100:>6.1f}%        +{improvement:>6.1f}%")
            else:
                if libro_val != float('inf') and random_val != float('inf'):
                    improvement = (random_val - libro_val) / random_val * 100 if random_val > 0 else 0
                    print(f"{metric:<25} {libro_val:>6.2f}         {random_val:>6.2f}         +{improvement:>6.1f}%")
    
    # Phase 3: Visualizations
    if all_results:
        print("\n" + "=" * 80)
        print("PHASE 3: VISUALIZATION GENERATION")
        print("=" * 80)
        
        runner.create_visualizations(all_results)
        
        print("\n✓ Visualizations complete!")
        print(f"  Location: results/day4_evaluation/visualizations/")
    
    # Final summary
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    
    if all_results:
        print("\n📊 Final Results Summary:\n")
        print(f"{'Model':<25} {'Repro%':<10} {'Acc@1':<10} {'Acc@3':<10} {'WEF':<10}")
        print("=" * 70)
        
        for model, data in sorted(all_results.items()):
            metrics = data['metrics']
            repro = metrics['reproduction_rate'] * 100
            acc1 = metrics.get('acc@1', 0) * 100
            acc3 = metrics.get('acc@3', 0) * 100
            wef = metrics.get('wasted_effort_mean', float('inf'))
            
            wef_str = f"{wef:.2f}" if wef != float('inf') else "N/A"
            
            print(f"{model:<25} {repro:>6.1f}%    {acc1:>6.1f}%    {acc3:>6.1f}%    {wef_str:>6}")
    
    print("\n📁 All results saved to: results/day4_evaluation/")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
