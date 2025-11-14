#!/usr/bin/env python3
"""
Fetch bug reports from Defects4J metadata.
"""

import subprocess
import json
from pathlib import Path
import tempfile
import re

def get_bug_info(project, bug_id):
    """Get bug information from Defects4J."""
    result = subprocess.run(
        ["defects4j", "info", "-p", project, "-b", str(bug_id)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    info = {}
    for line in result.stdout.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    
    return info

def fetch_bug_report_from_checkout(project, bug_id):
    """Fetch bug report by checking out and reading metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir) / f"{project}_{bug_id}"
        
        # Checkout
        result = subprocess.run(
            ["defects4j", "checkout", "-p", project, "-v", f"{bug_id}b", 
             "-w", str(work_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return None
        
        # Look for .buginfo file
        buginfo_file = work_dir / ".defects4j" / "buginfo.properties"
        if not buginfo_file.exists():
            return None
        
        # Parse properties
        props = {}
        with open(buginfo_file) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    props[key.strip()] = value.strip()
        
        return props

def create_bug_report(project, bug_id, info_dict):
    """Create structured bug report from Defects4J info."""
    
    # Extract relevant fields
    report_id = info_dict.get('report.id', '')
    report_url = info_dict.get('report.url', '')
    
    # For title, use report ID if available
    title = f"Bug {project}-{bug_id}"
    if report_id:
        title = f"{report_id}: Bug in {project}"
    
    # Description - use URL for now, as actual text requires web scraping
    description = f"See bug report at: {report_url}" if report_url else "Bug report not available"
    
    # Check if it's a crash bug (has stack trace)
    is_crash = 'error' in str(info_dict).lower() or 'exception' in str(info_dict).lower()
    
    report = {
        "project": project,
        "bug_id": bug_id,
        "title": title,
        "description": description,
        "report_url": report_url,
        "report_id": report_id,
        "is_crash": is_crash
    }
    
    return report

def main():
    """Fetch bug reports for selected bugs."""
    
    # Load selected bugs
    with open("data/bugs/selected_bugs.json") as f:
        selected_bugs = json.load(f)
    
    print(f"Fetching bug reports for {len(selected_bugs)} bugs...")
    
    bug_reports = []
    failed_bugs = []
    
    for i, bug in enumerate(selected_bugs):
        project = bug['project']
        bug_id = bug['bug_id']
        
        print(f"[{i+1}/{len(selected_bugs)}] Fetching {project}-{bug_id}...", 
              end=" ", flush=True)
        
        # Try to get info
        info = get_bug_info(project, bug_id)
        
        if not info:
            # Try alternative method
            info = fetch_bug_report_from_checkout(project, bug_id)
        
        if info:
            report = create_bug_report(project, bug_id, info)
            bug_reports.append(report)
            print("✓")
        else:
            failed_bugs.append(f"{project}-{bug_id}")
            print("✗")
    
    # Save reports
    output_file = Path("data/bugs/bug_reports.json")
    with open(output_file, 'w') as f:
        json.dump(bug_reports, f, indent=2)
    
    print(f"\n✓ Fetched {len(bug_reports)} bug reports")
    print(f"  Saved to: {output_file}")
    
    if failed_bugs:
        print(f"\n✗ Failed to fetch {len(failed_bugs)} bugs:")
        for bug in failed_bugs:
            print(f"  - {bug}")

if __name__ == "__main__":
    main()
