#!/usr/bin/env python3
"""
Select ~30 bugs from Lang and Jsoup for initial evaluation.
Criteria: Has bug report, builds successfully.
"""

import subprocess
import json
import csv
from pathlib import Path

def check_bug_validity(project, bug_id, work_dir):
    """Check if bug can be checked out and compiled."""
    bug_work_dir = f"{work_dir}/{project}_{bug_id}_buggy"
    
    try:
        # Checkout buggy version
        result = subprocess.run(
            ["defects4j", "checkout", "-p", project, "-v", f"{bug_id}b", "-w", bug_work_dir],
            capture_output=True,
            timeout=60,
            text=True
        )
        if result.returncode != 0:
            return False, f"checkout_failed: {result.stderr[:100]}"
        
        # Try to compile
        result = subprocess.run(
            ["defects4j", "compile"],
            cwd=bug_work_dir,
            capture_output=True,
            timeout=300,  # 5 minute timeout
            text=True
        )
        
        success = result.returncode == 0
        return success, "ok" if success else f"compile_failed: {result.stderr[:100]}"
        
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {str(e)}"
    finally:
        # Cleanup
        subprocess.run(["rm", "-rf", bug_work_dir], capture_output=True)

def parse_defects4j_csv(filepath):
    """
    Parse Defects4J query output CSV (no header).
    Expected format: bug_id,report_id,report_url
    """
    bugs = []
    with open(filepath) as f:
        # Use csv.reader since there's no header
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                bugs.append({
                    "bug_id": row[0],
                    "report_id": row[1],
                    "report_url": row[2]
                })
    return bugs

def main():
    data_dir = Path("data/bugs")
    work_dir = Path("data/temp_checkout")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    selected_bugs = []
    
    # Process Lang bugs (target: 20 bugs)
    print("=" * 80)
    print("Processing Lang bugs...")
    print("=" * 80)
    
    lang_bugs = parse_defects4j_csv(data_dir / "lang_bugs_raw.csv")
    print(f"Found {len(lang_bugs)} Lang bugs in total")
    
    for i, bug in enumerate(lang_bugs[:40]):  # Check first 40 to get ~20 valid
        bug_id = bug['bug_id']
        print(f"[{i+1}/40] Checking Lang-{bug_id}... ", end="", flush=True)
        
        valid, reason = check_bug_validity("Lang", bug_id, str(work_dir))
        print(reason)
        
        if valid:
            selected_bugs.append({
                "project": "Lang",
                "bug_id": bug_id,
                "report_id": bug.get('report_id', ''),
                "report_url": bug.get('report_url', '')
            })
            print(f"  ✓ Added Lang-{bug_id} (total Lang bugs: {len([b for b in selected_bugs if b['project'] == 'Lang'])})")
            
        if len([b for b in selected_bugs if b['project'] == 'Lang']) >= 20:
            print(f"\n✓ Reached target of 20 Lang bugs")
            break
    
    # Process Jsoup bugs (target: 10 bugs)
    print("\n" + "=" * 80)
    print("Processing Jsoup bugs...")
    print("=" * 80)
    
    jsoup_bugs = parse_defects4j_csv(data_dir / "jsoup_bugs_raw.csv")
    print(f"Found {len(jsoup_bugs)} Jsoup bugs in total")
    
    for i, bug in enumerate(jsoup_bugs[:20]):  # Check first 20 to get ~10 valid
        bug_id = bug['bug_id']
        print(f"[{i+1}/20] Checking Jsoup-{bug_id}... ", end="", flush=True)
        
        valid, reason = check_bug_validity("Jsoup", bug_id, str(work_dir))
        print(reason)
        
        if valid:
            selected_bugs.append({
                "project": "Jsoup",
                "bug_id": bug_id,
                "report_id": bug.get('report_id', ''),
                "report_url": bug.get('report_url', '')
            })
            print(f"  ✓ Added Jsoup-{bug_id} (total Jsoup bugs: {len([b for b in selected_bugs if b['project'] == 'Jsoup'])})")
            
        if len([b for b in selected_bugs if b['project'] == 'Jsoup']) >= 10:
            print(f"\n✓ Reached target of 10 Jsoup bugs")
            break
    
    # Save selected bugs
    output_file = data_dir / "selected_bugs.json"
    with open(output_file, 'w') as f:
        json.dump(selected_bugs, f, indent=2)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Selected {len(selected_bugs)} bugs:")
    print(f"  - Lang: {len([b for b in selected_bugs if b['project'] == 'Lang'])}")
    print(f"  - Jsoup: {len([b for b in selected_bugs if b['project'] == 'Jsoup'])}")
    print(f"  - Saved to: {output_file}")
    print("=" * 80)
    
    # Cleanup temp directory
    subprocess.run(["rm", "-rf", str(work_dir)])

if __name__ == "__main__":
    main()
