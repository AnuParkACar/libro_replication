"""Visualization utilities for evaluation results."""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, List
import json

sns.set_style("whitegrid")
sns.set_palette("husl")

class Visualizer:
    """Create visualizations for evaluation results."""
    
    def __init__(self, output_dir: str = "results/visualizations"):
        """Initialize visualizer."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_accuracy_at_k(self, metrics_dict: Dict[str, Dict], 
                          k_values: List[int] = [1, 3, 5, 10],
                          title: str = "Accuracy@k"):
        """
        Plot accuracy@k comparison.
        
        Args:
            metrics_dict: Dict mapping model/method name to metrics
            k_values: List of k values
            title: Plot title
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for name, metrics in metrics_dict.items():
            acc_values = [metrics.get(f'acc@{k}', 0.0) for k in k_values]
            ax.plot(k_values, acc_values, marker='o', label=name, linewidth=2)
        
        ax.set_xlabel('k (top-k tests)', fontsize=12)
        ax.set_ylabel('Accuracy@k', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.0])
        
        plt.tight_layout()
        output_file = self.output_dir / "accuracy_at_k.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {output_file}")
    
    def plot_wasted_effort(self, metrics_dict: Dict[str, Dict],
                          title: str = "Wasted Effort Comparison"):
        """Plot wasted effort comparison."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = list(metrics_dict.keys())
        wef_values = [
            metrics_dict[name].get('wasted_effort_mean', float('inf'))
            for name in names
        ]
        
        # Filter out infinite values
        valid_indices = [i for i, v in enumerate(wef_values) if v != float('inf')]
        names = [names[i] for i in valid_indices]
        wef_values = [wef_values[i] for i in valid_indices]
        
        colors = sns.color_palette("husl", len(names))
        bars = ax.bar(names, wef_values, color=colors, alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel('Wasted Effort (lower is better)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_file = self.output_dir / "wasted_effort.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {output_file}")
    
    def plot_reproduction_rate(self, metrics_dict: Dict[str, Dict],
                              title: str = "Bug Reproduction Rate"):
        """Plot reproduction rate comparison."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = list(metrics_dict.keys())
        repro_rates = [
            metrics_dict[name].get('reproduction_rate', 0.0) * 100
            for name in names
        ]
        
        colors = sns.color_palette("husl", len(names))
        bars = ax.bar(names, repro_rates, color=colors, alpha=0.8)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel('Reproduction Rate (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim([0, 100])
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_file = self.output_dir / "reproduction_rate.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {output_file}")
    
    def plot_per_project_metrics(self, project_metrics: Dict[str, Dict],
                                 metric_name: str = 'reproduction_rate'):
        """Plot metrics broken down by project."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        projects = list(project_metrics.keys())
        metric_values = [
            project_metrics[p].get(metric_name, 0.0)
            for p in projects
        ]
        
        # Convert to percentage if it's a rate
        if 'rate' in metric_name or 'acc@' in metric_name:
            metric_values = [v * 100 for v in metric_values]
            ylabel = f'{metric_name} (%)'
        else:
            ylabel = metric_name
        
        colors = sns.color_palette("husl", len(projects))
        bars = ax.bar(projects, metric_values, color=colors, alpha=0.8)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(f'{metric_name} by Project', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=0)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_file = self.output_dir / f"{metric_name}_by_project.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {output_file}")
    
    def plot_model_comparison(self, model_results: Dict[str, Dict],
                            k_values: List[int] = [1, 3, 5, 10]):
        """Create comprehensive model comparison plots."""
        
        print("Creating model comparison visualizations...")
        
        # 1. Accuracy@k comparison
        self.plot_accuracy_at_k(
            model_results,
            k_values=k_values,
            title="Model Comparison: Accuracy@k"
        )
        
        # 2. Wasted effort comparison
        self.plot_wasted_effort(
            model_results,
            title="Model Comparison: Wasted Effort"
        )
        
        # 3. Reproduction rate comparison
        self.plot_reproduction_rate(
            model_results,
            title="Model Comparison: Bug Reproduction Rate"
        )
        
        # 4. Combined metrics heatmap
        self._plot_metrics_heatmap(model_results)
        
        print(f"\n✓ All visualizations saved to: {self.output_dir}")
    
    def _plot_metrics_heatmap(self, metrics_dict: Dict[str, Dict]):
        """Create heatmap of all metrics."""
        
        # Select key metrics
        metric_keys = ['reproduction_rate', 'acc@1', 'acc@3', 'acc@5', 
                      'wasted_effort_mean']
        
        # Create matrix
        models = list(metrics_dict.keys())
        data = []
        
        for model in models:
            row = []
            for metric in metric_keys:
                value = metrics_dict[model].get(metric, 0.0)
                if value == float('inf'):
                    value = 0.0
                row.append(value)
            data.append(row)
        
        # Normalize for visualization (except wasted effort which is inverse)
        data = np.array(data)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Custom colormap
        sns.heatmap(data, annot=True, fmt='.3f', 
                   xticklabels=metric_keys,
                   yticklabels=models,
                   cmap='YlOrRd', ax=ax,
                   cbar_kws={'label': 'Metric Value'})
        
        ax.set_title('Model Performance Heatmap', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_file = self.output_dir / "metrics_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {output_file}")
    
    def create_summary_report(self, metrics_dict: Dict[str, Dict],
                            baseline_metrics: Dict = None):
        """Create text summary report."""
        
        report_file = self.output_dir / "EVALUATION_SUMMARY.md"
        
        with open(report_file, 'w') as f:
            f.write("# LIBRO Evaluation Summary\n\n")
            
            # Overall results
            f.write("## Overall Results\n\n")
            
            for name, metrics in metrics_dict.items():
                f.write(f"### {name}\n\n")
                f.write(f"- **Reproduction Rate**: {metrics.get('reproduction_rate', 0)*100:.1f}%\n")
                f.write(f"- **Bugs Reproduced**: {metrics.get('bugs_reproduced', 0)}/{metrics.get('total_bugs', 0)}\n")
                f.write(f"- **Acc@1**: {metrics.get('acc@1', 0)*100:.1f}%\n")
                f.write(f"- **Acc@3**: {metrics.get('acc@3', 0)*100:.1f}%\n")
                f.write(f"- **Acc@5**: {metrics.get('acc@5', 0)*100:.1f}%\n")
                
                wef = metrics.get('wasted_effort_mean', float('inf'))
                if wef != float('inf'):
                    f.write(f"- **Wasted Effort**: {wef:.2f}\n")
                else:
                    f.write(f"- **Wasted Effort**: N/A\n")
                
                f.write("\n")
            
            # Baseline comparison
            if baseline_metrics:
                f.write("## Comparison to Random Baseline\n\n")
                f.write("| Metric | LIBRO | Random | Improvement |\n")
                f.write("|--------|-------|--------|-------------|\n")
                
                libro_metrics = next(iter(metrics_dict.values()))
                
                for metric in ['acc@1', 'acc@3', 'acc@5', 'wasted_effort_mean']:
                    libro_val = libro_metrics.get(metric, 0)
                    random_val = baseline_metrics.get(metric, 0)
                    
                    if libro_val != float('inf') and random_val != float('inf'):
                        if 'acc@' in metric:
                            improvement = (libro_val - random_val) / random_val * 100 if random_val > 0 else 0
                            f.write(f"| {metric} | {libro_val*100:.1f}% | {random_val*100:.1f}% | +{improvement:.1f}% |\n")
                        else:
                            improvement = (random_val - libro_val) / random_val * 100 if random_val > 0 else 0
                            f.write(f"| {metric} | {libro_val:.2f} | {random_val:.2f} | +{improvement:.1f}% |\n")
                
                f.write("\n")
        
        print(f"  ✓ Saved summary: {report_file}")
