"""Multi-model evaluation runner for ablation studies."""

import json
from pathlib import Path
from typing import List, Dict
import logging
import time

from src.libro_pipeline import LIBROPipeline
from src.core.batch_processor import BatchProcessor
from src.evaluation.metrics import EvaluationMetrics, RandomBaseline
from src.evaluation.visualizations import Visualizer

logger = logging.getLogger(__name__)

class MultiModelRunner:
    """Run evaluation across multiple models."""
    
    SUPPORTED_MODELS = {
        "starcoder2-3b": "bigcode/starcoder2-3b",
        "starcoder2-7b": "bigcode/starcoder2-7b",
        "codellama-7b": "codellama/CodeLlama-7b-hf",
        "deepseek-coder-7b": "deepseek-ai/deepseek-coder-7b-base-v1.5"
    }
    
    def __init__(self, output_dir: str = "results/multi_model"):
        """Initialize multi-model runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_model_evaluation(self, model_key: str, bugs: List[Dict],
                            resume: bool = True) -> Dict:
        """
        Run evaluation for a single model.
        
        Args:
            model_key: Model identifier (e.g., "starcoder2-7b")
            bugs: List of bugs to process
            resume: Whether to resume from existing progress
            
        Returns:
            Dict with results and metrics
        """
        logger.info(f"{'=' * 80}")
        logger.info(f"Evaluating model: {model_key}")
        logger.info(f"{'=' * 80}")
        
        # Create model-specific output directory
        model_output_dir = self.output_dir / model_key
        model_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for existing results
        results_file = model_output_dir / "results.json"
        
        if resume and results_file.exists():
            logger.info(f"Loading existing results for {model_key}")
            with open(results_file) as f:
                results = json.load(f)
            
            logger.info(f"  Found {len(results)} existing bug results")
        else:
            # Initialize pipeline
            logger.info("Initializing pipeline...")
            pipeline = LIBROPipeline()
            
            # Load model
            logger.info(f"Loading model: {model_key}")
            pipeline.load_model(model_key)
            
            # Run batch processing
            logger.info(f"Processing {len(bugs)} bugs...")
            batch_processor = BatchProcessor(
                pipeline=pipeline,
                output_dir=str(model_output_dir)
            )
            
            results = batch_processor.process_bugs(bugs)
            
            # Save results
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to: {results_file}")
        
        # Calculate metrics
        logger.info("Calculating metrics...")
        metrics = EvaluationMetrics.calculate_all_metrics(results)
        
        # Save metrics
        metrics_file = model_output_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to: {metrics_file}")
        
        return {
            'model': model_key,
            'results': results,
            'metrics': metrics
        }
    
    def run_multi_model_evaluation(self, bugs: List[Dict],
                                   models: List[str] = None,
                                   resume: bool = True) -> Dict[str, Dict]:
        """
        Run evaluation across multiple models.
        
        Args:
            bugs: List of bugs to process
            models: List of model keys to evaluate (default: all supported)
            resume: Whether to resume from existing progress
            
        Returns:
            Dict mapping model_key to results and metrics
        """
        if models is None:
            models = list(self.SUPPORTED_MODELS.keys())
        
        logger.info(f"Running multi-model evaluation")
        logger.info(f"  Models: {', '.join(models)}")
        logger.info(f"  Bugs: {len(bugs)}")
        
        all_results = {}
        
        for model_key in models:
            try:
                model_results = self.run_model_evaluation(
                    model_key=model_key,
                    bugs=bugs,
                    resume=resume
                )
                
                all_results[model_key] = model_results
                
                # Log summary
                metrics = model_results['metrics']
                logger.info(f"\n{model_key} Summary:")
                logger.info(f"  Reproduction Rate: {metrics['reproduction_rate']*100:.1f}%")
                logger.info(f"  Acc@1: {metrics.get('acc@1', 0)*100:.1f}%")
                logger.info(f"  Wasted Effort: {metrics.get('wasted_effort_mean', float('inf')):.2f}")
                
            except Exception as e:
                logger.error(f"Failed to evaluate {model_key}: {e}")
                continue
        
        # Save combined results
        combined_file = self.output_dir / "combined_results.json"
        with open(combined_file, 'w') as f:
            # Don't save full results (too large), just metrics
            combined = {
                model: {
                    'metrics': data['metrics'],
                    'num_bugs': len(data['results'])
                }
                for model, data in all_results.items()
            }
            json.dump(combined, f, indent=2)
        
        logger.info(f"\nCombined results saved to: {combined_file}")
        
        return all_results
    
    def evaluate_with_baseline(self, bugs: List[Dict],
                              model_key: str = "starcoder2-7b",
                              num_random_trials: int = 100) -> Dict:
        """
        Evaluate model against random baseline.
        
        Args:
            bugs: List of bugs
            model_key: Model to evaluate
            num_random_trials: Number of random baseline trials
            
        Returns:
            Dict with model and baseline metrics
        """
        logger.info(f"Evaluating {model_key} with random baseline")
        
        # Get model results
        model_results = self.run_model_evaluation(model_key, bugs, resume=True)
        
        # Evaluate random baseline
        logger.info("Evaluating random baseline...")
        baseline_metrics = RandomBaseline.evaluate_random_baseline(
            model_results['results'],
            num_trials=num_random_trials
        )
        
        # Save baseline metrics
        baseline_file = self.output_dir / model_key / "baseline_metrics.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_metrics, f, indent=2)
        
        logger.info(f"Baseline metrics saved to: {baseline_file}")
        
        return {
            'model_metrics': model_results['metrics'],
            'baseline_metrics': baseline_metrics
        }
    
    def create_visualizations(self, all_results: Dict[str, Dict]):
        """Create visualizations for all models."""
        logger.info("Creating visualizations...")
        
        visualizer = Visualizer(output_dir=str(self.output_dir / "visualizations"))
        
        # Extract metrics for each model
        metrics_dict = {
            model: data['metrics']
            for model, data in all_results.items()
        }
        
        # Create comparison plots
        visualizer.plot_model_comparison(metrics_dict)
        
        # Per-project metrics (for first model)
        first_model = next(iter(all_results.keys()))
        first_results = all_results[first_model]['results']
        
        project_metrics = EvaluationMetrics.calculate_per_project_metrics(
            first_results
        )
        
        visualizer.plot_per_project_metrics(project_metrics, 'reproduction_rate')
        visualizer.plot_per_project_metrics(project_metrics, 'acc@1')
        
        logger.info("Visualizations complete!")
