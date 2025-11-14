#!/usr/bin/env python3
"""
Run LIBRO evaluation on GHRB dataset.
Designed to work both locally and in Google Colab.
"""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path
import tempfile
import time

from src.libro_pipeline import LIBROPipeline
from src.core.batch_processor import BatchProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ghrb_evaluation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run evaluation on GHRB dataset."""
    
    print("=" * 80)
    print("GHRB DATASET EVALUATION")
    print("=" * 80)
    
    # Load GHRB bug reports
    ghrb_file = Path("data/GHRB/bug_reports.json")
    
    if not ghrb_file.exists():
        print(f"✗ GHRB bug reports not found at: {ghrb_file}")
        print(f"\nPlease run setup first:")
        print(f"  python3 scripts/setup_ghrb_complete.py")
        print(f"  python3 scripts/extract_ghrb_bugs_enhanced.py")
        return
    
    with open(ghrb_file) as f:
        bug_reports = json.load(f)
    
    print(f"\n✓ Loaded {len(bug_reports)} GHRB bug reports")
    
    # Show what we're testing
    print("\nBugs to evaluate:")
    for i, bug in enumerate(bug_reports[:5], 1):
        print(f"  {i}. {bug['project']} #{bug['issue_number']}: {bug['title'][:50]}...")
    if len(bug_reports) > 5:
        print(f"  ... and {len(bug_reports) - 5} more")
    
    # Initialize pipeline
    print("\n" + "=" * 80)
    print("Initializing Pipeline")
    print("=" * 80)
    
    pipeline = LIBROPipeline()
    
    # Load model
    print("\nLoading model (this may take 5-10 minutes)...")
    model_name = "starcoder2-3b"  # or "deepseek-coder-7b" for faster testing
    
    try:
        pipeline.load_model(model_name)
        print(f"✓ Model {model_name} loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print("\nTrying smaller model: deepseek-coder-7b")
        pipeline.load_model("deepseek-coder-7b")
    
    # Initialize batch processor
    print("\n" + "=" * 80)
    print("Starting Batch Processing")
    print("=" * 80)
    
    batch_processor = BatchProcessor(
        pipeline=pipeline,
        output_dir="results/ghrb_evaluation"
    )
    
    # Estimate time
    estimated_time = len(bug_reports) * 3  # ~3 minutes per bug
    print(f"\nProcessing {len(bug_reports)} bugs")
    print(f"Estimated time: {estimated_time} minutes ({estimated_time/60:.1f} hours)")
    print("Progress is saved after each bug - you can resume if interrupted\n")
    
    # Process bugs
    start_time = time.time()
    results = batch_processor.process_bugs(bug_reports)
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 80)
    print("GHRB EVALUATION COMPLETE")
    print("=" * 80)
    
    stats_file = Path("results/ghrb_evaluation/statistics.json")
    if stats_file.exists():
        with open(stats_file) as f:
            stats = json.load(f)
        
        print(f"\n📊 Results:")
        print(f"  Bugs evaluated: {stats['total_bugs']}")
        print(f"  Bugs reproduced: {stats['bugs_reproduced']} ({stats['reproduction_rate']*100:.1f}%)")
        print(f"  Total BRTs: {stats['total_brt']}")
        print(f"  Total time: {elapsed_time/60:.1f} minutes")
        
        # Per-project breakdown
        print(f"\n📊 Per-Project Results:")
        for project, pstats in sorted(stats.get('project_breakdown', {}).items()):
            rate = pstats['with_brt'] / pstats['total'] * 100 if pstats['total'] > 0 else 0
            print(f"  {project:20s}: {pstats['with_brt']}/{pstats['total']} ({rate:.1f}%)")
        
        # Compare to paper
        paper_rate = 32.2  # From LIBRO paper on GHRB
        diff = stats['reproduction_rate']*100 - paper_rate
        print(f"\n📈 Comparison to LIBRO paper:")
        print(f"  Paper (with Codex): 32.2%")
        print(f"  Our replication: {stats['reproduction_rate']*100:.1f}%")
        print(f"  Difference: {diff:+.1f}%")
        
        print(f"\n💾 Results saved to: results/ghrb_evaluation/")
        print(f"  - final_results.json")
        print(f"  - statistics.json")
        print(f"  - SUMMARY.md")
    
    print("=" * 80)

if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    main()
