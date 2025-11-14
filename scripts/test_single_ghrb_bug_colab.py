#!/usr/bin/env python3
"""
Test LIBRO on a single GHRB bug.
Optimized for Google Colab with minimal setup.
"""

import sys
sys.path.append('.')

import json
from pathlib import Path
import logging
import argparse

from src.libro_pipeline import LIBROPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_single_bug(bug_index: int = 0, model_name: str = "deepseek-coder-7b", 
                    n_samples: int = 5):
    """
    Test pipeline on a single GHRB bug.
    
    Args:
        bug_index: Index of bug to test (0-30)
        model_name: Model to use
        n_samples: Number of test samples to generate
    """
    
    # Load bugs
    bugs_file = Path("data/GHRB/bug_reports.json")
    
    if not bugs_file.exists():
        print("❌ Bug reports not found!")
        print("Please run: python3 scripts/extract_ghrb_bugs_enhanced.py")
        return
    
    with open(bugs_file) as f:
        bugs = json.load(f)
    
    if bug_index >= len(bugs):
        print(f"❌ Invalid bug index. Max: {len(bugs)-1}")
        return
    
    test_bug = bugs[bug_index]
    
    print("="*80)
    print(f"Testing Bug {bug_index + 1}/{len(bugs)}")
    print("="*80)
    print(f"\nProject: {test_bug['project']}")
    print(f"Issue: #{test_bug['issue_number']}")
    print(f"Title: {test_bug['title']}")
    print(f"\nDescription:")
    print(test_bug['description'][:200] + "...")
    print("="*80)
    
    # Initialize pipeline
    print("\n📦 Initializing pipeline...")
    pipeline = LIBROPipeline()
    
    # Load model
    print(f"\n🤖 Loading model: {model_name}")
    print("(This may take 5-10 minutes on first load)")
    
    try:
        pipeline.load_model(model_name)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return
    
    # Configure
    pipeline.config.set("generation.samples_per_bug", n_samples)
    
    # Run pipeline
    print(f"\n🚀 Running pipeline (generating {n_samples} test samples)...")
    print("Estimated time: 3-5 minutes\n")
    
    try:
        results = pipeline.run_on_bug(test_bug)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Display results
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)
    
    metrics = results['metrics']
    
    print(f"\n✨ Generation:")
    print(f"   Tests generated: {metrics['num_generated']}")
    print(f"   Tests injected: {metrics['num_injected']}")
    
    print(f"\n🧪 Execution:")
    print(f"   FIB tests: {metrics['num_fib']}")
    print(f"   BRT tests: {metrics['num_brt']}")
    
    print(f"\n⏱️  Performance:")
    print(f"   Total time: {metrics['total_time']:.1f}s")
    
    # Detailed results
    if metrics['num_brt'] > 0:
        print(f"\n✅ SUCCESS: Found {metrics['num_brt']} Bug Reproducing Test(s)!")
        
        for i, brt in enumerate(results['brt_tests'], 1):
            print(f"\n{'='*80}")
            print(f"BRT #{i}")
            print(f"{'='*80}")
            print(brt['test_code'])
            print(f"{'='*80}")
    else:
        print(f"\n⚠️  No BRTs found")
        
        if metrics['num_fib'] > 0:
            print(f"\n   But found {metrics['num_fib']} FIB test(s):")
            print("   (These fail on buggy version but also fail on fixed version)")
            
            # Show first FIB for debugging
            if results['fib_tests']:
                fib = results['fib_tests'][0]
                print(f"\n   First FIB test:")
                print(f"   Error: {fib.get('error_type', 'Unknown')}")
                print(f"   Message: {fib.get('error_message', 'No message')[:100]}")
        
        # Debugging info
        if metrics['num_generated'] > 0 and metrics['num_injected'] == 0:
            print(f"\n   ⚠️  Tests were generated but none could be injected")
            print(f"   This usually means:")
            print(f"   - Host class selection failed")
            print(f"   - Import resolution issues")
            
        if metrics['num_injected'] > 0 and metrics['num_fib'] == 0:
            print(f"\n   ⚠️  Tests were injected but none executed properly")
            print(f"   This usually means:")
            print(f"   - Compilation errors")
            print(f"   - Test doesn't trigger the bug")
    
    # Save results
    output_file = Path("results/single_bug_test.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Full results saved to: {output_file}")
    
    print("\n" + "="*80)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Test LIBRO on a single GHRB bug')
    parser.add_argument('--bug', type=int, default=0, 
                       help='Bug index to test (0-30, default: 0)')
    parser.add_argument('--model', type=str, default='deepseek-coder-7b',
                       choices=['starcoder2-15b', 'codellama-13b', 'deepseek-coder-7b'],
                       help='Model to use')
    parser.add_argument('--samples', type=int, default=5,
                       help='Number of test samples to generate (default: 5)')
    
    args = parser.parse_args()
    
    test_single_bug(args.bug, args.model, args.samples)

if __name__ == "__main__":
    main()
