#!/usr/bin/env python3
"""
Day 4: Complete evaluation pipeline with n-ablation study.
"""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path
import argparse

from src.evaluation.multi_model_runner import MultiModelRunner
from src.evaluation.n_ablation_runner import NAblationRunner

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
    parser = argparse.ArgumentParser(description="Run Day 4 evaluation with n-ablation")
    parser.add_argument('--models', nargs='+', 
                       default=["starcoder2-3b", "starcoder2-7b"],
                       help="Models to evaluate")
    parser.add_argument('--num-bugs', type=int, default=10,
                       help="Number of bugs to evaluate")
    parser.add_argument('--n-values', nargs='+', type=int,
                       default=[5,10],
                       help="Values of n to test")
    parser.add_argument('--skip-multi-model', action='store_true',
                       help="Skip multi-model comparison")
    parser.add_argument('--skip-n-ablation', action='store_true',
                       help="Skip n-ablation study")
    parser.add_argument('--skip-baseline', action='store_true',
                       help="Skip baseline comparison")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DAY 4: COMPLETE EVALUATION WITH N-ABLATION")
    print("=" * 80)
    
    # Load bugs
    with open("data/bugs/bug_reports.json") as f:
        all_bugs = json.load(f)
    
    bugs_to_process = all_bugs[:args.num_bugs]
    
    print(f"\n📂 Evaluating on {len(bugs_to_process)} bugs")
    print(f"🤖 Models: {', '.join(args.models)}")
    print(f"🔢 N values: {args.n_values}")
    
    # Phase 1: N-Ablation Study
    if not args.skip_n_ablation:
        print("\n" + "=" * 80)
        print("PHASE 1: N-ABLATION STUDY")
        print("=" * 80)
        
        n_runner = NAblationRunner(output_dir="results/n_ablation")
        
        for model in args.models:
            print(f"\n{'─' * 80}")
            print(f"Running n-ablation for {model}")
            print(f"{'─' * 80}")
            
            n_results = n_runner.run_n_ablation(
                bugs=bugs_to_process,
                model_key=model,
                n_values=args.n_values,
                resume=True
            )
            
            # Create visualizations
            n_runner.plot_n_ablation(n_results, model_name=model)
            
            print(f"\n✓ N-ablation complete for {model}")
    
    # Phase 2: Multi-Model Comparison (with default n)
    if not args.skip_multi_model and len(args.models) > 1:
        print("\n" + "=" * 80)
        print("PHASE 2: MULTI-MODEL COMPARISON")
        print("=" * 80)
        
        runner = MultiModelRunner(output_dir="results/multi_model")
        
        all_results = runner.run_multi_model_evaluation(
            bugs=bugs_to_process,
            models=args.models,
            resume=True
        )
        
        runner.create_visualizations(all_results)
        
        print("\n✓ Multi-model comparison complete")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    
    print("\n📁 Results:")
    print("  - N-ablation: results/n_ablation/")
    print("  - Multi-model: results/multi_model/")
    print("  - Visualizations: results/*/visualizations/")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
