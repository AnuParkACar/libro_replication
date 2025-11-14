#!/usr/bin/env python3
"""
Dry run: Test generation on 5 bugs to verify pipeline.
"""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path

from src.model_manager import ModelManager
from src.core.prompt_builder import PromptBuilder
from src.core.test_generator import TestGenerator
from src.core.batch_processor import BatchProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dry_run.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run generation on 5 bugs."""
    
    # Load bug reports
    with open("data/bugs/bug_reports.json") as f:
        all_bug_reports = json.load(f)
    
    # Select first 5 bugs
    bug_reports = all_bug_reports[:5]
    
    logger.info(f"Dry run with {len(bug_reports)} bugs:")
    for bug in bug_reports:
        logger.info(f"  - {bug['project']}-{bug['bug_id']}: {bug['title']}")
    
    # Initialize components
    logger.info("Initializing model...")
    model_manager = ModelManager(
        model_key="deepseek-coder-7b",  # Start with smaller model for testing
        cache_dir="models/deepseek-coder-7b"
    )
    model_manager.load()
    
    logger.info("Initializing prompt builder...")
    prompt_builder = PromptBuilder(
        num_examples=2,
        examples_file="data/examples/manual_examples.json"
    )
    
    logger.info("Initializing test generator...")
    test_generator = TestGenerator(
        model_manager=model_manager,
        cache_dir="cache/generations"
    )
    
    logger.info("Initializing batch processor...")
    batch_processor = BatchProcessor(
        prompt_builder=prompt_builder,
        test_generator=test_generator,
        output_dir="results/dry_run"
    )
    
    # Process bugs
    logger.info("Starting generation...")
    results = batch_processor.process_bugs(
        bug_reports=bug_reports,
        n_samples=10
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print("DRY RUN RESULTS")
    print("=" * 80)
    
    for bug_id, tests in results.items():
        print(f"\n{bug_id}:")
        print(f"  Generated: {len(tests)} tests")
        if tests:
            print(f"  First test preview:")
            print("  " + "-" * 40)
            print("  " + tests[0]['test_code'][:200].replace('\n', '\n  '))
            if len(tests[0]['test_code']) > 200:
                print("  ...")
    
    print("\n" + "=" * 80)
    print("✓ Dry run completed successfully")
    print("Results saved to: results/dry_run/")
    print("=" * 80)

if __name__ == "__main__":
    main()
