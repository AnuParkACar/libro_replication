"""N-ablation study: evaluate performance vs. number of generated tests."""

import json
from pathlib import Path
from typing import List, Dict
import logging
import copy

from src.libro_pipeline import LIBROPipeline
from src.core.batch_processor import BatchProcessor
from src.evaluation.metrics import EvaluationMetrics
from src.evaluation.visualizations import Visualizer
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class NAblationRunner:
    """Run ablation study varying n (number of test candidates)."""
    
    def __init__(self, output_dir: str = "results/n_ablation"):
        """Initialize n-ablation runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_n_ablation(self, bugs: List[Dict], 
                      model_key: str = "starcoder2-7b",
                      n_values: List[int] = [5, 10, 15, 20, 25, 30],
                      resume: bool = True) -> Dict[int, Dict]:
        """
        Run evaluation for different values of n.
        
        The strategy:
        1. Generate max(n_values) tests once for each bug
        2. For each n, use only the first n tests
        3. This simulates what would happen with different n values
        
        Args:
            bugs: List of bugs to evaluate
            model_key: Model to use
            n_values: List of n values to test
            resume: Whether to resume from existing results
            
        Returns:
            Dict mapping n -> results and metrics
        """
        logger.info(f"{'=' * 80}")
        logger.info(f"N-ABLATION STUDY: n ∈ {n_values}")
        logger.info(f"{'=' * 80}")
        
        max_n = max(n_values)
        
        # Step 1: Generate with max_n (or load existing)
        logger.info(f"\nStep 1: Generating {max_n} tests per bug")
        
        base_results_file = self.output_dir / f"{model_key}_n{max_n}_results.json"
        
        if resume and base_results_file.exists():
            logger.info(f"Loading existing results with n={max_n}")
            with open(base_results_file) as f:
                base_results = json.load(f)
        else:
            logger.info("Running batch processing to generate tests...")
            
            # Initialize pipeline with custom config for max_n
            pipeline = LIBROPipeline(config_path="config/default_config.yaml")
            
            # Update config for max_n - use the correct attribute
            pipeline.config.set('generation.samples_per_bug', max_n)
            
            logger.info(f"Set samples_per_bug = {max_n}")
            
            # Load model
            logger.info(f"Loading model: {model_key}")
            pipeline.load_model(model_key)
            
            # Run batch processing
            batch_processor = BatchProcessor(
                pipeline=pipeline,
                output_dir=str(self.output_dir / f"{model_key}_n{max_n}")
            )
            
            base_results = batch_processor.process_bugs(bugs)
            
            # Save base results
            with open(base_results_file, 'w') as f:
                json.dump(base_results, f, indent=2)
            
            logger.info(f"Base results saved to: {base_results_file}")
        
        # Step 2: For each n, simulate using only first n tests
        logger.info(f"\nStep 2: Simulating different n values")
        
        all_n_results = {}
        
        for n in sorted(n_values):
            logger.info(f"\nEvaluating with n={n}")
            
            # Create subset results using only first n tests
            n_results = self._create_subset_results(base_results, n)
            
            # Calculate metrics
            metrics = EvaluationMetrics.calculate_all_metrics(n_results)
            
            logger.info(f"  Reproduction rate: {metrics['reproduction_rate']*100:.1f}%")
            logger.info(f"  Acc@1: {metrics.get('acc@1', 0)*100:.1f}%")
            logger.info(f"  Acc@3: {metrics.get('acc@3', 0)*100:.1f}%")
            logger.info(f"  WEF: {metrics.get('wasted_effort_mean', float('inf')):.2f}")
            
            all_n_results[n] = {
                'n': n,
                'results': n_results,
                'metrics': metrics
            }
            
            # Save individual n results
            n_file = self.output_dir / f"{model_key}_n{n}_metrics.json"
            with open(n_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        
        # Save combined results
        combined_file = self.output_dir / f"{model_key}_n_ablation.json"
        combined_data = {
            str(n): {'metrics': data['metrics'], 'n': n}
            for n, data in all_n_results.items()
        }
        
        with open(combined_file, 'w') as f:
            json.dump(combined_data, f, indent=2)
        
        logger.info(f"\nN-ablation complete! Results saved to: {combined_file}")
        
        return all_n_results
    
    def _create_subset_results(self, base_results: Dict, n: int) -> Dict:
        """
        Create subset results using only first n tests.
        
        Args:
            base_results: Full results with all tests
            n: Number of tests to use
            
        Returns:
            New results dict with only first n tests
        """
        subset_results = {}
        
        for bug_id, result in base_results.items():
            subset_result = copy.deepcopy(result)
            
            # Limit generated tests
            if 'generated_tests' in subset_result:
                subset_result['generated_tests'] = subset_result['generated_tests'][:n]
            
            # Limit injected tests
            if 'injected_tests' in subset_result:
                subset_result['injected_tests'] = subset_result['injected_tests'][:n]
            
            # Limit FIB tests
            if 'fib_tests' in subset_result:
                subset_result['fib_tests'] = subset_result['fib_tests'][:n]
            
            # Limit BRT tests
            if 'brt_tests' in subset_result:
                subset_result['brt_tests'] = subset_result['brt_tests'][:n]
            
            # Limit ranking
            if 'ranking' in subset_result:
                subset_result['ranking'] = subset_result['ranking'][:n]
            
            # Update metrics
            if 'metrics' in subset_result:
                subset_result['metrics']['num_generated'] = len(subset_result.get('generated_tests', []))
                subset_result['metrics']['num_injected'] = len(subset_result.get('injected_tests', []))
                subset_result['metrics']['num_fib'] = len(subset_result.get('fib_tests', []))
                subset_result['metrics']['num_brt'] = len(subset_result.get('brt_tests', []))
                subset_result['metrics']['has_brt'] = subset_result['metrics']['num_brt'] > 0
            
            subset_results[bug_id] = subset_result
        
        return subset_results
    
    def plot_n_ablation(self, n_results: Dict[int, Dict], 
                       model_name: str = "Model"):
        """
        Create visualizations for n-ablation study.
        
        Args:
            n_results: Dict mapping n -> results and metrics
            model_name: Name for plot titles
        """
        logger.info("Creating n-ablation visualizations...")
        
        # Extract data
        n_values = sorted(n_results.keys())
        
        reproduction_rates = [
            n_results[n]['metrics']['reproduction_rate'] * 100
            for n in n_values
        ]
        
        acc1_values = [
            n_results[n]['metrics'].get('acc@1', 0) * 100
            for n in n_values
        ]
        
        acc3_values = [
            n_results[n]['metrics'].get('acc@3', 0) * 100
            for n in n_values
        ]
        
        acc5_values = [
            n_results[n]['metrics'].get('acc@5', 0) * 100
            for n in n_values
        ]
        
        wef_values = [
            n_results[n]['metrics'].get('wasted_effort_mean', float('inf'))
            for n in n_values
        ]
        wef_values = [v if v != float('inf') else None for v in wef_values]
        
        # Create 2x2 subplot
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Reproduction rate vs. n
        ax = axes[0, 0]
        ax.plot(n_values, reproduction_rates, marker='o', linewidth=2, markersize=8)
        ax.set_xlabel('n (number of test candidates)', fontsize=11)
        ax.set_ylabel('Reproduction Rate (%)', fontsize=11)
        ax.set_title(f'{model_name}: Reproduction Rate vs. n', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 100])
        
        # 2. Accuracy@k vs. n
        ax = axes[0, 1]
        ax.plot(n_values, acc1_values, marker='o', label='Acc@1', linewidth=2, markersize=8)
        ax.plot(n_values, acc3_values, marker='s', label='Acc@3', linewidth=2, markersize=8)
        ax.plot(n_values, acc5_values, marker='^', label='Acc@5', linewidth=2, markersize=8)
        ax.set_xlabel('n (number of test candidates)', fontsize=11)
        ax.set_ylabel('Accuracy@k (%)', fontsize=11)
        ax.set_title(f'{model_name}: Accuracy@k vs. n', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 100])
        
        # 3. Wasted effort vs. n
        ax = axes[1, 0]
        valid_wef = [(n, w) for n, w in zip(n_values, wef_values) if w is not None]
        if valid_wef:
            ns, ws = zip(*valid_wef)
            ax.plot(ns, ws, marker='o', linewidth=2, markersize=8, color='orange')
        ax.set_xlabel('n (number of test candidates)', fontsize=11)
        ax.set_ylabel('Wasted Effort (lower is better)', fontsize=11)
        ax.set_title(f'{model_name}: Wasted Effort vs. n', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 4. All metrics normalized
        ax = axes[1, 1]
        # Normalize all metrics to 0-1 scale
        norm_repro = [r / 100 for r in reproduction_rates]
        norm_acc1 = [a / 100 for a in acc1_values]
        norm_acc3 = [a / 100 for a in acc3_values]
        
        ax.plot(n_values, norm_repro, marker='o', label='Reproduction Rate', linewidth=2)
        ax.plot(n_values, norm_acc1, marker='s', label='Acc@1', linewidth=2)
        ax.plot(n_values, norm_acc3, marker='^', label='Acc@3', linewidth=2)
        ax.set_xlabel('n (number of test candidates)', fontsize=11)
        ax.set_ylabel('Normalized Score (0-1)', fontsize=11)
        ax.set_title(f'{model_name}: All Metrics vs. n', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        plt.tight_layout()
        
        output_file = self.output_dir / f"{model_name.lower().replace(' ', '_')}_n_ablation.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"  ✓ Saved: {output_file}")
        
        # Create summary table
        self._create_n_ablation_table(n_results, model_name)
    
    def _create_n_ablation_table(self, n_results: Dict[int, Dict], 
                                 model_name: str):
        """Create markdown table summarizing n-ablation results."""
        
        table_file = self.output_dir / f"{model_name.lower().replace(' ', '_')}_n_ablation_table.md"
        
        with open(table_file, 'w') as f:
            f.write(f"# N-Ablation Results: {model_name}\n\n")
            f.write("| n | Repro% | Acc@1 | Acc@3 | Acc@5 | WEF |\n")
            f.write("|---|--------|-------|-------|-------|-----|\n")
            
            for n in sorted(n_results.keys()):
                metrics = n_results[n]['metrics']
                
                repro = metrics['reproduction_rate'] * 100
                acc1 = metrics.get('acc@1', 0) * 100
                acc3 = metrics.get('acc@3', 0) * 100
                acc5 = metrics.get('acc@5', 0) * 100
                wef = metrics.get('wasted_effort_mean', float('inf'))
                
                wef_str = f"{wef:.2f}" if wef != float('inf') else "N/A"
                
                f.write(f"| {n} | {repro:.1f}% | {acc1:.1f}% | {acc3:.1f}% | "
                       f"{acc5:.1f}% | {wef_str} |\n")
            
            f.write("\n## Key Observations\n\n")
            f.write("- As n increases, reproduction rate typically stabilizes\n")
            f.write("- Acc@k generally improves with larger n (more chances to get BRT)\n")
            f.write("- Wasted effort may increase slightly with larger n\n")
            f.write("- Trade-off between cost (generating n tests) and benefit (higher acc@k)\n")
        
        logger.info(f"  ✓ Saved table: {table_file}")
