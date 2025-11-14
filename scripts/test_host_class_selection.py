#!/usr/bin/env python3
"""Test host class selection on real Defects4J projects."""

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
        logger.error(f"Failed to checkout {project}-{bug_id}")
        return None
    
    return bug_dir

def test_host_class_selection():
    """Test host class selection on a sample bug."""
    
    print("=" * 80)
    print("Testing Host Class Selection")
    print("=" * 80)
    
    # Sample test code
    sample_test = """
    public void testEqualsWithNaN() {
        assertFalse(MathUtils.equals(Double.NaN, Double.NaN));
        assertFalse(MathUtils.equals(Float.NaN, Float.NaN));
    }
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Checkout Lang-1
        print("\n1. Checking out Lang-1...")
        project_dir = checkout_bug("Lang", "1", work_dir)
        
        if not project_dir:
            print("✗ Failed to checkout project")
            return
        
        print(f"✓ Project checked out to: {project_dir}")
        
        # Initialize processor
        print("\n2. Initializing test processor...")
        processor = TestProcessor(defects4j_path="defects4j")
        
        # Find host class
        print("\n3. Finding host class...")
        result = processor.find_host_class(sample_test, project_dir)
        
        if result:
            host_class, score = result
            print(f"✓ Found host class: {Path(host_class).name}")
            print(f"  Similarity score: {score:.3f}")
            
            # Show some context from the file
            print(f"\n4. Host class preview:")
            with open(host_class, 'r') as f:
                lines = f.readlines()
                print(f"  File: {host_class}")
                print(f"  Lines: {len(lines)}")
                print(f"  First 20 lines:")
                for i, line in enumerate(lines[:20], 1):
                    print(f"    {i:3d} │ {line.rstrip()}")
        else:
            print("✗ Could not find suitable host class")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_host_class_selection()
