#!/usr/bin/env python3
"""Test complete injection pipeline."""

import sys
sys.path.append('.')

import subprocess
import tempfile
from pathlib import Path
import logging

from src.core.test_processor import TestProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def checkout_bug(project, bug_id, work_dir):
    """Checkout a bug for testing."""
    bug_dir = work_dir / f"{project}_{bug_id}_buggy"
    
    result = subprocess.run(
        ["defects4j", "checkout", "-p", project, "-v", f"{bug_id}b", "-w", str(bug_dir)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    return bug_dir

def test_injection_pipeline():
    """Test complete injection pipeline."""
    
    print("=" * 80)
    print("Testing Injection Pipeline")
    print("=" * 80)
    
    # Sample test code with typical patterns
    sample_tests = [
        {
            "name": "Simple assertion test",
            "code": """public void testGeneratedExample1() {
        String input = "";
        assertFalse(NumberUtils.isNumber(input));
    }"""
        },
        {
            "name": "Test with NaN",
            "code": """public void testGeneratedExample2() {
        assertFalse(MathUtils.equals(Double.NaN, Double.NaN));
    }"""
        },
        {
            "name": "Test with multiple assertions",
            "code": """@Test
    public void testGeneratedExample3() {
        assertTrue(true);
        assertEquals(1, 1);
        assertNotNull("test");
    }"""
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Test on Lang-1
        print("\n1. Checking out Lang-1...")
        project_dir = checkout_bug("Lang", "1", work_dir)
        
        if not project_dir:
            print("✗ Failed to checkout project")
            return
        
        print(f"✓ Project checked out")
        
        # Initialize processor
        processor = TestProcessor(defects4j_path="defects4j")
        
        # Test each sample
        for i, test_sample in enumerate(sample_tests, 1):
            print(f"\n{'=' * 80}")
            print(f"Test {i}: {test_sample['name']}")
            print(f"{'=' * 80}")
            
            test_code = test_sample['code']
            
            # Find host class
            print("\n  Step 1: Finding host class...")
            result = processor.find_host_class(test_code, project_dir)
            
            if not result:
                print("  ✗ Could not find host class")
                continue
            
            host_class, score = result
            print(f"  ✓ Host class: {Path(host_class).name} (score: {score:.3f})")
            
            # Inject test
            print("\n  Step 2: Injecting test...")
            injection_result = processor.inject_test(
                test_code=test_code,
                host_class_path=host_class,
                project_path=project_dir,
                test_id=f"sample{i}"
            )
            
            if injection_result['success']:
                print(f"  ✓ Injection successful")
                print(f"    Modified file: {Path(injection_result['modified_class_path']).name}")
                print(f"    Added imports: {len(injection_result['added_imports'])}")
                
                if injection_result['added_imports']:
                    print("    Imports added:")
                    for imp in injection_result['added_imports']:
                        print(f"      - {imp}")
                
                # Show the modified class (last 30 lines)
                print("\n  Step 3: Verifying modified class (last 30 lines)...")
                with open(injection_result['modified_class_path'], 'r') as f:
                    lines = f.readlines()
                    print(f"    Total lines: {len(lines)}")
                    for i, line in enumerate(lines[-30:], len(lines)-29):
                        print(f"    {i:3d} │ {line.rstrip()}")
            else:
                print(f"  ✗ Injection failed: {injection_result['error']}")
    
    print("\n" + "=" * 80)
    print("✓ Injection pipeline test complete")
    print("=" * 80)

if __name__ == "__main__":
    test_injection_pipeline()
