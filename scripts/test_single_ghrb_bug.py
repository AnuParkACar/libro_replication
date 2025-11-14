#!/usr/bin/env python3
"""Quick test on a single GHRB bug."""

import sys
sys.path.append('.')

import json
from pathlib import Path
import logging

from src.libro_pipeline import LIBROPipeline

logging.basicConfig(level=logging.INFO)

def main():
    # Load GHRB bugs
    with open("data/GHRB/bug_reports.json") as f:
        bugs = json.load(f)
    
    # Test on first bug
    test_bug = bugs[0]
    
    print("=" * 80)
    print(f"Testing on: {test_bug['project']} #{test_bug['issue_number']}")
    print(f"Title: {test_bug['title']}")
    print(f"Description: {test_bug['description'][:100]}...")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = LIBROPipeline()
    pipeline.load_model("starcoder2-3b")
    
    # Run on single bug
    results = pipeline.run_on_bug(test_bug)
    
    # Show results
    print("\n📊 Results:")
    print(f"  Generated: {results['metrics']['num_generated']}")
    print(f"  Injected: {results['metrics']['num_injected']}")
    print(f"  FIB: {results['metrics']['num_fib']}")
    print(f"  BRT: {results['metrics']['num_brt']}")
    
    if results['brt_tests']:
        print("\n✅ BRT FOUND!")
        print("\nTest code:")
        print(results['brt_tests'][0]['test_code'])

if __name__ == "__main__":
    main()
