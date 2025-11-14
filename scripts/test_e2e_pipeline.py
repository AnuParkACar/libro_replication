#!/usr/bin/env python3
"""Test end-to-end pipeline on a single bug."""

import sys
sys.path.append('.')

import json
import logging
from pathlib import Path
import tempfile

from src.libro_pipeline import LIBROPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_e2e():
    """Test end-to-end pipeline."""
    
    print("=" * 80)
    print("End-to-End Pipeline Test")
    print("=" * 80)
    
    # Create a simple bug report for testing
    bug_report = {
        "project": "Lang",
        "bug_id": "1",
        "title": "NumberUtils.isNumber should return false for blank strings",
        "description": """The method NumberUtils.isNumber(String) returns true for blank strings. 
        According to the documentation, it should return false for blank strings like " " or ""."""
    }
    
    print(f"\nTesting on: {bug_report['project']}-{bug_report['bug_id']}")
    print(f"Title: {bug_report['title']}")
    
    # Initialize pipeline
    print("\n1. Initializing pipeline...")
    pipeline = LIBROPipeline()
    
    # Load model (use small model for testing)
    print("\n2. Loading model...")
    pipeline.load_model("deepseek-coder-7b")
    
    # Run pipeline
    print("\n3. Running pipeline...")
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        results = pipeline.run_on_bug(bug_report, work_dir=work_dir)
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"\n📊 Statistics:")
    print(f"  Generated tests: {results['metrics']['num_generated']}")
    print(f"  Injected tests: {results['metrics']['num_injected']}")
    print(f"  FIB tests: {results['metrics']['num_fib']}")
    print(f"  BRT tests: {results['metrics']['num_brt']}")
    print(f"  Total time: {results['metrics']['total_time']:.1f}s")
    
    if results['brt_tests']:
        print(f"\n✅ SUCCESS: Found {len(results['brt_tests'])} BRT(s)!")
        
        print("\n📝 First BRT:")
        brt = results['brt_tests'][0]
        print(f"  Classification: {brt['classification']}")
        print(f"  Test code:")
        for line in brt['test_code'].split('\n'):
            print(f"    {line}")
    else:
        print(f"\n⚠️  No BRTs found")
        
        if results['fib_tests']:
            print(f"\n📝 FIB tests found: {len(results['fib_tests'])}")
            print("  (These fail on buggy but also fail on fixed)")
    
    if results['errors']:
        print(f"\n❌ Errors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Save results
    output_file = Path("results/e2e_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    test_e2e()
