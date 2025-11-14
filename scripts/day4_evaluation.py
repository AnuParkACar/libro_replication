#!/usr/bin/env python3
"""
Day 4: Complete evaluation with metrics and baseline comparison.
"""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns

from src.evaluation.metrics import EvaluationMetrics
from src.evaluation.baseline import RandomBaseline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_results(results_file: str) -> dict:
    """Load results from file."""
    with open(results_file) as f:
        return json.load(f)

def print_metrics_table(metrics: dict, title: str = "Metrics"):
    """Print metrics in a nice table format."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    
    # Overall metrics
    print(f"\n📊 Overall:")
    print(f"  Total bugs: {metrics['total_bugs']}")
    print(f"  Bugs reproduced: {metrics['bugs_reproduced']} ({metrics['brt_rate']*100:.1f}%)")
    print(f"  Total BRTs: {metrics['total_brt']}")
    
    # acc@k metrics
    print(f"\n🎯 Accuracy Metrics:")
    acc_data = []
    for k_name, k_metrics in metrics['acc_at_k'].items():
        acc_data.append([
            k_name,
            k_metrics['count'],
            f"{k_metrics['precision']*100:.1f}%"
        ])
    
    print(tabulate(acc_data, headers=['Metric', 'Count', 'Precision'], tablefmt='grid'))
    
    # wef@k metrics
    print(f"\n⏱️  Wasted Effort:")
    wef_data = []
    for k_name, k_metrics in metrics['wef_at_k'].items():
        wef_data.append([
            k_name,
            f"{k_metrics['average']:.2f}",
            f"{k_metrics['median']:.1f}",
            k_metrics['total']
        ])
    
    print(tabulate(wef_data, headers=['Metric', 'Average', 'Median', 'Total'], tablefmt='grid'))

def create_comparison_visualizations(libro_metrics: dict, 
                                    baseline_metrics: dict,
                                    output_dir: Path):
    """Create comparison visualizations."""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # acc@k comparison
    ax1 = axes[0]
    k_values = [1, 3, 5]
    libro_acc = [libro_metrics['acc_at_k'][f'acc@{k}']['precision'] * 100 
                for k in k_values]
    baseline_acc = [baseline_metrics['acc_at_k'][f'acc@{k}']['mean'] * 100 
                   for k in k_values]
    
    x = range(len(k_values))
    width = 0.35
    
    ax1.bar([i - width/2 for i in x], libro_acc, width, label='LIBRO', color='steelblue')
    ax1.bar([i + width/2 for i in x], baseline_acc, width, label='Random', color='coral')
    
    ax1.set_xlabel('k')
    ax1.set_ylabel('Precision (%)')
    ax1.set_title('acc@k Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'@{k}' for k in k_values])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # wef@k comparison
    ax2 = axes[1]
    libro_wef = [libro_metrics['wef_at_k'][f'wef@{k}']['average'] 
                for k in k_values]
    baseline_wef = [baseline_metrics['wef_at_k'][f'wef@{k}']['mean'] 
                   for k in k_values]
    
    ax2.bar([i - width/2 for i in x], libro_wef, width, label='LIBRO', color='steelblue')
    ax2.bar([i + width/2 for i in x], baseline_wef, width, label='Random', color='coral')
    
    ax2.set_xlabel('k')
    ax2.set_ylabel('Wasted Effort (tests)')
    ax2.set_title('wef@k Comparison (lower is better)')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'@{k}' for k in k_values])
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    plot_file = output_dir / "comparison_plots.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Plots saved to: {plot_file}")
    
    plt.show()

def main():
    """Run complete evaluation."""
    
    print("="*80)
    print("DAY 4: COMPREHENSIVE EVALUATION")
    print("="*80)
    
    # Load results
    results_file = Path("results/ghrb_evaluation/final_results.json")
    
    if not results_file.exists():
        results_file = Path("results/day3_batch/final_results.json")
    
    if not results_file.exists():
        print("❌ Results file not found!")
        print("Please run the evaluation first:")
        print("  python3 scripts/run_ghrb_evaluation.py")
        return
    
    print(f"\nLoading results from: {results_file}")
    results = load_results(results_file)
    
    print(f"✓ Loaded results for {len(results)} bugs")
    
    # Initialize evaluators
    metrics_calc = EvaluationMetrics()
    baseline = RandomBaseline(seed=42)
    
    # Calculate LIBRO metrics
    print("\n" + "="*80)
    print("Step 1: Calculate LIBRO Metrics")
    print("="*80)
    
    k_values = [1, 3, 5]
    libro_metrics = metrics_calc.calculate_all_metrics(results, k_values)
    
    print_metrics_table(libro_metrics, "LIBRO Results")
    
    # Generate random baseline
    print("\n" + "="*80)
    print("Step 2: Generate Random Baseline")
    print("="*80)
    
    print("Running 100 random trials...")
    random_trials = baseline.run_multiple_trials(results, n_trials=100)
    baseline_metrics = baseline.aggregate_trials(random_trials, k_values)
    
    print("\n📊 Random Baseline (100 trials, mean ± std):")
    
    # Print baseline results
    for k in k_values:
        acc_key = f'acc@{k}'
        mean = baseline_metrics['acc_at_k'][acc_key]['mean'] * 100
        std = baseline_metrics['acc_at_k'][acc_key]['std'] * 100
        print(f"  {acc_key}: {mean:.1f}% ± {std:.1f}%")
    
    print("\n  Wasted Effort:")
    for k in k_values:
        wef_key = f'wef@{k}'
        mean = baseline_metrics['wef_at_k'][wef_key]['mean']
        std = baseline_metrics['wef_at_k'][wef_key]['std']
        print(f"  {wef_key}: {mean:.2f} ± {std:.2f}")
    
    # Compare
    print("\n" + "="*80)
    print("Step 3: Comparison")
    print("="*80)
    
    print("\n📈 LIBRO vs Random Baseline:")
    
    comparison_data = []
    for k in k_values:
        acc_key = f'acc@{k}'
        
        libro_acc = libro_metrics['acc_at_k'][acc_key]['precision'] * 100
        baseline_acc = baseline_metrics['acc_at_k'][acc_key]['mean'] * 100
        improvement = libro_acc - baseline_acc
        
        comparison_data.append([
            acc_key,
            f"{libro_acc:.1f}%",
            f"{baseline_acc:.1f}%",
            f"+{improvement:.1f}%"
        ])
    
    print(tabulate(comparison_data, 
                  headers=['Metric', 'LIBRO', 'Random', 'Improvement'],
                  tablefmt='grid'))
    
    # wef comparison
    print("\n  Wasted Effort Reduction:")
    for k in k_values:
        wef_key = f'wef@{k}'
        
        libro_wef = libro_metrics['wef_at_k'][wef_key]['average']
        baseline_wef = baseline_metrics['wef_at_k'][wef_key]['mean']
        reduction = baseline_wef - libro_wef
        reduction_pct = (reduction / baseline_wef * 100) if baseline_wef > 0 else 0
        
        print(f"  {wef_key}: {reduction:.2f} tests saved ({reduction_pct:.1f}% reduction)")
    
    # Create visualizations
    print("\n" + "="*80)
    print("Step 4: Create Visualizations")
    print("="*80)
    
    output_dir = results_file.parent
    create_comparison_visualizations(libro_metrics, baseline_metrics, output_dir)
    
    # Save comprehensive report
    print("\n" + "="*80)
    print("Step 5: Save Report")
    print("="*80)
    
    report = {
        'libro_metrics': libro_metrics,
        'baseline_metrics': baseline_metrics,
        'k_values': k_values
    }
    
    report_file = output_dir / "evaluation_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Report saved to: {report_file}")
    
    # Final summary
    print("\n" + "="*80)
    print("✅ EVALUATION COMPLETE")
    print("="*80)
    
    print(f"\n📊 Summary:")
    print(f"  BRT Rate: {libro_metrics['brt_rate']*100:.1f}%")
    print(f"  Best acc@1: {libro_metrics['acc_at_k']['acc@1']['precision']*100:.1f}%")
    print(f"  Improvement over random: +{comparison_data[0][3]}")
    
    # Compare to paper
    print(f"\n📈 Comparison to LIBRO Paper:")
    print(f"  Paper (GHRB with Codex): 32.2%")
    print(f"  Our replication: {libro_metrics['brt_rate']*100:.1f}%")
    
    print(f"\n💾 All results saved to: {output_dir}/")

if __name__ == "__main__":
    # Install tabulate if needed
    try:
        import tabulate
    except ImportError:
        print("Installing tabulate...")
        import subprocess
        subprocess.run(["pip", "install", "tabulate"], check=True)
        import tabulate
    
    main()
