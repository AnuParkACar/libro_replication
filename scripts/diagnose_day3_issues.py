
import sys
sys.path.append('.')

import json
from pathlib import Path
import subprocess
import tempfile

def check_bug_descriptions():
    """Check if bug reports have meaningful descriptions."""
    print("=" * 80)
    print("1. CHECKING BUG DESCRIPTIONS")
    print("=" * 80)
    
    with open('data/bugs/bug_reports.json') as f:
        bugs = json.load(f)
    
    issues = []
    
    for i, bug in enumerate(bugs[:10]):
        bug_id = f"{bug['project']}-{bug['bug_id']}"
        desc = bug.get('description', '')
        
        print(f"\n{bug_id}:")
        print(f"  Title: {bug.get('title', 'N/A')[:70]}")
        print(f"  Description length: {len(desc)} chars")
        print(f"  Report URL: {bug.get('report_url', 'N/A')}")
        print(f"  Report ID: {bug.get('report_id', 'N/A')}")
        
        if len(desc) < 30:
            issues.append(f"{bug_id}: Description too short ({len(desc)} chars)")
            print(f"  ⚠️  Description: '{desc}'")
        else:
            print(f"  ✓ Description: {desc[:100]}...")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} bugs with insufficient descriptions:")
        for issue in issues:
            print(f"    {issue}")
        return False
    else:
        print(f"\n✓ All bugs have adequate descriptions")
        return True

def check_execution_results():
    """Check execution results from last run."""
    print("\n" + "=" * 80)
    print("2. CHECKING EXECUTION RESULTS")
    print("=" * 80)
    
    progress_file = Path('results/day3_batch/progress.json')
    
    if not progress_file.exists():
        print("⚠️  No progress file found. Run batch processing first.")
        return
    
    with open(progress_file) as f:
        results = json.load(f)
    
    print(f"\nAnalyzing {len(results)} processed bugs...")
    
    compilation_errors = 0
    execution_errors = 0
    all_passed = 0
    no_execution_data = 0
    
    for bug_id, result in results.items():
        print(f"\n{bug_id}:")
        
        # Check if we have injection data
        injected = result.get('injected_tests', [])
        print(f"  Injected tests: {len(injected)}")
        
        if not injected:
            print(f"  ⚠️  No tests were injected!")
            continue
        
        # Check first injected test's execution
        for i, test in enumerate(result.get('fib_tests', []) + result.get('brt_tests', [])):
            if 'execution' in test:
                exec_data = test['execution']
                
                buggy = exec_data.get('buggy_result', {})
                fixed = exec_data.get('fixed_result', {})
                
                print(f"  Test {i}:")
                print(f"    Buggy - Compiled: {buggy.get('compiled')}, "
                      f"Passed: {buggy.get('passed')}, Failed: {buggy.get('failed')}")
                print(f"    Fixed - Compiled: {fixed.get('compiled')}, "
                      f"Passed: {fixed.get('passed')}, Failed: {fixed.get('failed')}")
                
                if not buggy.get('compiled'):
                    print(f"    ⚠️  Compilation error (buggy): {buggy.get('error_message', 'Unknown')[:100]}")
                    compilation_errors += 1
                elif buggy.get('error_type'):
                    print(f"    ⚠️  Execution error: {buggy.get('error_type')}")
                    execution_errors += 1
                elif buggy.get('passed'):
                    print(f"    ⚠️  Test PASSED on buggy (should FAIL!)")
                    all_passed += 1
                
                break
        else:
            # No execution data found
            print(f"  ⚠️  No execution data found!")
            no_execution_data += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Compilation errors: {compilation_errors}")
    print(f"  Execution errors: {execution_errors}")
    print(f"  Tests passing on buggy: {all_passed}")
    print(f"  No execution data: {no_execution_data}")
    
    if all_passed > 0:
        print(f"\n⚠️  MAIN ISSUE: {all_passed} tests are passing on buggy version!")
        print("     This means tests are not triggering the bugs.")
        print("     Likely causes:")
        print("     1. Bug descriptions are not detailed enough")
        print("     2. Tests are too generic")
        print("     3. Wrong classes/methods being tested")

def test_single_bug_manually():
    """Manually test a single bug end-to-end."""
    print("\n" + "=" * 80)
    print("3. MANUAL END-TO-END TEST")
    print("=" * 80)
    
    from src.libro_pipeline import LIBROPipeline
    
    # Test on Lang-1 with a known-good bug description
    bug_report = {
        "project": "Lang",
        "bug_id": "1",
        "title": "NumberUtils.createNumber throws NumberFormatException for '2.'",
        "description": """The method NumberUtils.createNumber(String) throws a NumberFormatException 
        when trying to parse the string '2.' (a number with a trailing decimal point). 
        The expected behavior is to handle this gracefully and return a valid number.
        The bug is in the NumberUtils class, specifically the createNumber method.
        Test case: NumberUtils.createNumber("2.") should work but throws exception."""
    }
    
    print("\nTesting with detailed bug report:")
    print(f"  {bug_report['title']}")
    print(f"  Description: {bug_report['description'][:200]}...")
    
    # Initialize pipeline
    print("\nInitializing pipeline...")
    pipeline = LIBROPipeline()
    
    print("Loading model...")
    pipeline.load_model("starcoder2-7b")
    
    print("Running pipeline...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        results = pipeline.run_on_bug(bug_report, work_dir=work_dir)
    
    # Check results
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"  Generated tests: {results['metrics']['num_generated']}")
    print(f"  Injected tests: {results['metrics']['num_injected']}")
    print(f"  FIB tests: {results['metrics']['num_fib']}")
    print(f"  BRT tests: {results['metrics']['num_brt']}")
    
    if results['metrics']['num_brt'] > 0:
        print("\n✓ SUCCESS! Found BRT with detailed description")
        
        # Show the BRT
        brt = results['brt_tests'][0]
        print("\nBRT Test Code:")
        print(brt['test_code'])
    else:
        print("\n⚠️  Still no BRT found even with detailed description")
        
        if results['fib_tests']:
            print("\nFIB tests found (fail on buggy but also fail on fixed):")
            for test in results['fib_tests'][:2]:
                print(f"\n  Test code:")
                print(f"  {test['test_code'][:200]}...")
                print(f"  Error: {test.get('error_type')}")
        
        if results['generated_tests']:
            print("\nSample generated test:")
            print(results['generated_tests'][0]['test_code'][:300])

def check_defects4j():
    """Check if Defects4J is working properly."""
    print("\n" + "=" * 80)
    print("4. CHECKING DEFECTS4J INSTALLATION")
    print("=" * 80)
    
    # Check if defects4j command exists
    result = subprocess.run(['which', 'defects4j'], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Defects4J command not found!")
        print("   Install with: cpanm --installdeps . && ./init.sh")
        return False
    
    print(f"✓ Defects4J found at: {result.stdout.strip()}")
    
    # Try to get bug info
    print("\nTesting Defects4J info command...")
    result = subprocess.run(
        ['defects4j', 'info', '-p', 'Lang', '-b', '1'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✓ Defects4J info command working")
        print(f"  Output: {result.stdout[:200]}...")
    else:
        print("❌ Defects4J info command failed")
        print(f"  Error: {result.stderr[:200]}")
        return False
    
    # Try to checkout a bug
    print("\nTesting Defects4J checkout...")
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir) / "test_checkout"
        
        result = subprocess.run(
            ['defects4j', 'checkout', '-p', 'Lang', '-v', '1b', '-w', str(work_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✓ Defects4J checkout working")
            print(f"  Checked out to: {work_dir}")
            
            # Try to compile
            print("\nTesting compilation...")
            compile_result = subprocess.run(
                ['defects4j', 'compile'],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if compile_result.returncode == 0:
                print("✓ Compilation working")
            else:
                print("❌ Compilation failed")
                print(f"  Error: {compile_result.stderr[:200]}")
        else:
            print("❌ Defects4J checkout failed")
            print(f"  Error: {result.stderr[:200]}")
            return False
    
    return True

def main():
    print("=" * 80)
    print("DIAGNOSING DAY 3 ISSUES")
    print("=" * 80)
    
    # Check 1: Bug descriptions
    print("\nRunning diagnostics...\n")
    descriptions_ok = check_bug_descriptions()
    
    # Check 2: Defects4J
    defects4j_ok = check_defects4j()
    
    # Check 3: Execution results
    check_execution_results()
    
    # Check 4: Manual test (only if other checks pass)
    if descriptions_ok and defects4j_ok:
        test_single_bug_manually()
    
    # Final recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if not descriptions_ok:
        print("\n1. ⚠️  FIX BUG DESCRIPTIONS:")
        print("   Run: python3 scripts/extract_bug_info_complete.py")
        print("   This will fetch real bug descriptions from JIRA/GitHub")
    
    if not defects4j_ok:
        print("\n2. ⚠️  FIX DEFECTS4J:")
        print("   Ensure Defects4J is properly installed")
        print("   Run: cd defects4j && cpanm --installdeps . && ./init.sh")
    
    print("\n3. After fixing, rerun batch processing:")
    print("   python3 scripts/day3_batch_run.py")

if __name__ == "__main__":
    main()
