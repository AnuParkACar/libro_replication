"""Batch processing with execution and BRT detection."""

import json
import logging
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import time

from src.libro_pipeline import LIBROPipeline

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Process multiple bugs with full pipeline."""
    
    def __init__(self, pipeline: LIBROPipeline,
                 output_dir: str = "results/batch"):
        """
        Initialize batch processor.
        
        Args:
            pipeline: LIBROPipeline instance
            output_dir: Directory to save results
        """
        self.pipeline = pipeline
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_bugs(self, bug_reports: List[Dict],
                    resume_from: str = None) -> Dict[str, Dict]:
        """
        Process multiple bug reports with full execution.
        
        Args:
            bug_reports: List of bug report dicts
            resume_from: Resume from a specific bug ID
            
        Returns:
            Dict mapping bug_id to results
        """
        logger.info(f"Processing {len(bug_reports)} bugs with full pipeline")
        
        results = {}
        start_processing = resume_from is None
        
        # Load existing results if resuming
        progress_file = self.output_dir / "progress.json"
        if progress_file.exists():
            with open(progress_file) as f:
                results = json.load(f)
            logger.info(f"Loaded {len(results)} existing results")
        
        # Process each bug
        for bug_report in tqdm(bug_reports, desc="Processing bugs"):
            bug_id = f"{bug_report['project']}-{bug_report['bug_id']}"
            
            # Skip if resuming and not reached resume point
            if not start_processing:
                if bug_id == resume_from:
                    start_processing = True
                else:
                    continue
            
            # Skip if already processed
            if bug_id in results:
                logger.info(f"Skipping {bug_id} (already processed)")
                continue
            
            try:
                logger.info(f"Processing {bug_id}")
                
                # Run full pipeline
                bug_results = self.pipeline.run_on_bug(bug_report)
                
                # Store results
                results[bug_id] = bug_results
                
                # Save progress after each bug
                self._save_progress(results)
                
                # Small delay
                time.sleep(2)
            
            except Exception as e:
                logger.error(f"Failed to process {bug_id}: {e}")
                results[bug_id] = {
                    "error": str(e),
                    "metrics": {"num_brt": 0, "has_brt": False}
                }
                self._save_progress(results)
                continue
        
        # Save final results with statistics
        self._save_final_results(results)
        
        return results
    
    def _save_progress(self, results: Dict):
        """Save progress to file."""
        progress_file = self.output_dir / "progress.json"
        with open(progress_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def _save_final_results(self, results: Dict):
        """Save final results with comprehensive statistics."""
        # Save raw results
        results_file = self.output_dir / "final_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Calculate statistics
        stats = self._calculate_statistics(results)
        
        stats_file = self.output_dir / "statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Create summary report
        self._create_summary_report(results, stats)
        
        logger.info(f"Final results saved to {results_file}")
        logger.info(f"Statistics: {stats}")
    
    def _calculate_statistics(self, results: Dict) -> Dict:
        """Calculate comprehensive statistics."""
        total_bugs = len(results)
        bugs_with_brt = sum(1 for r in results.values() 
                           if r.get('metrics', {}).get('has_brt', False))
        
        total_generated = sum(r.get('metrics', {}).get('num_generated', 0) 
                            for r in results.values())
        total_injected = sum(r.get('metrics', {}).get('num_injected', 0) 
                           for r in results.values())
        total_fib = sum(r.get('metrics', {}).get('num_fib', 0) 
                       for r in results.values())
        total_brt = sum(r.get('metrics', {}).get('num_brt', 0) 
                       for r in results.values())
        
        total_time = sum(r.get('metrics', {}).get('total_time', 0) 
                        for r in results.values())
        
        # Per-project breakdown
        project_stats = {}
        for bug_id, result in results.items():
            project = result.get('project', bug_id.split('-')[0])
            if project not in project_stats:
                project_stats[project] = {
                    'total': 0,
                    'with_brt': 0,
                    'total_brt': 0
                }
            
            project_stats[project]['total'] += 1
            if result.get('metrics', {}).get('has_brt'):
                project_stats[project]['with_brt'] += 1
                project_stats[project]['total_brt'] += result['metrics']['num_brt']
        
        return {
            'total_bugs': total_bugs,
            'bugs_reproduced': bugs_with_brt,
            'reproduction_rate': bugs_with_brt / total_bugs if total_bugs > 0 else 0,
            'total_generated': total_generated,
            'total_injected': total_injected,
            'total_fib': total_fib,
            'total_brt': total_brt,
            'avg_generated_per_bug': total_generated / total_bugs if total_bugs > 0 else 0,
            'avg_brt_per_bug': total_brt / total_bugs if total_bugs > 0 else 0,
            'total_time': total_time,
            'avg_time_per_bug': total_time / total_bugs if total_bugs > 0 else 0,
            'project_breakdown': project_stats
        }
    
    def _create_summary_report(self, results: Dict, stats: Dict):
        """Create human-readable summary report."""
        report_file = self.output_dir / "SUMMARY.md"
        
        with open(report_file, 'w') as f:
            f.write("# LIBRO Replication - Batch Processing Summary\n\n")
            
            f.write("## Overall Statistics\n\n")
            f.write(f"- **Total bugs processed**: {stats['total_bugs']}\n")
            f.write(f"- **Bugs reproduced**: {stats['bugs_reproduced']} "
                   f"({stats['reproduction_rate']*100:.1f}%)\n")
            f.write(f"- **Total BRTs found**: {stats['total_brt']}\n")
            f.write(f"- **Total time**: {stats['total_time']/60:.1f} minutes\n\n")
            
            f.write("## Test Generation\n\n")
            f.write(f"- **Tests generated**: {stats['total_generated']}\n")
            f.write(f"- **Tests injected**: {stats['total_injected']}\n")
            f.write(f"- **FIB tests**: {stats['total_fib']}\n")
            f.write(f"- **Avg per bug**: {stats['avg_generated_per_bug']:.1f}\n\n")
            
            f.write("## Per-Project Breakdown\n\n")
            f.write("| Project | Total | Reproduced | BRTs | Rate |\n")
            f.write("|---------|-------|------------|------|----- |\n")
            
            for project, pstats in sorted(stats['project_breakdown'].items()):
                rate = pstats['with_brt'] / pstats['total'] * 100 if pstats['total'] > 0 else 0
                f.write(f"| {project} | {pstats['total']} | {pstats['with_brt']} | "
                       f"{pstats['total_brt']} | {rate:.1f}% |\n")
            
            f.write("\n## Reproduced Bugs\n\n")
            
            for bug_id, result in sorted(results.items()):
                if result.get('metrics', {}).get('has_brt'):
                    num_brt = result['metrics']['num_brt']
                    f.write(f"- **{bug_id}**: {num_brt} BRT(s)\n")
        
        logger.info(f"Summary report saved to {report_file}")
