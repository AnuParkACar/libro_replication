#!/usr/bin/env python3
"""Extract real bug information from Defects4J."""

import subprocess
import json
import re
from pathlib import Path
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_bug_info(project: str, bug_id: str) -> dict:
    """Extract bug information from Defects4J."""
    logger.info(f"Extracting info for {project}-{bug_id}")
    
    bug_info = {
        "project": project,
        "bug_id": bug_id,
        "title": "",
        "description": "",
        "report_url": "",
        "report_id": "",
        "is_crash": False,
        "modified_classes": [],
        "test_trigger": ""
    }
    
    # Get bug properties
    result = subprocess.run(
        ["defects4j", "info", "-p", project, "-b", bug_id],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        logger.warning(f"  Failed to get info for {project}-{bug_id}")
        return bug_info
    
    output = result.stdout
    
    # Extract report URL/ID
    url_match = re.search(r'Report:\s*(.+)', output)
    if url_match:
        report = url_match.group(1).strip()
        bug_info["report_url"] = report
        # Extract ID from URL
        id_match = re.search(r'id=(\d+)', report)
        if id_match:
            bug_info["report_id"] = id_match.group(1)
    
    # Extract modified classes
    classes_section = re.search(r'Modified classes:.*?(?=\n\n|\Z)', output, re.DOTALL)
    if classes_section:
        classes = re.findall(r'  - (.+)', classes_section.group(0))
        bug_info["modified_classes"] = classes
    
    # Get more detailed info by checking out the bug
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir) / f"{project}_{bug_id}"
        
        checkout_result = subprocess.run(
            ["defects4j", "checkout", "-p", project, "-v", f"{bug_id}b", "-w", str(work_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if checkout_result.returncode != 0:
            logger.warning(f"  Failed to checkout {project}-{bug_id}")
            return bug_info
        
        # Get triggering tests
        trigger_result = subprocess.run(
            ["defects4j", "export", "-p", "tests.trigger"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if trigger_result.returncode == 0:
            trigger_tests = trigger_result.stdout.strip().split('\n')
            if trigger_tests:
                bug_info["test_trigger"] = trigger_tests[0]
        
        # Read commit message/patch info
        commit_db = work_dir / ".defects4j.build"
        if commit_db.exists():
            try:
                with open(commit_db) as f:
                    content = f.read()
                    # Extract any useful info
                    bug_info["has_build_file"] = True
            except:
                pass
        
        # Try to read bug-mining.json if exists
        bug_mining = work_dir / ".defects4j.metadata"
        if bug_mining.exists():
            try:
                with open(bug_mining) as f:
                    metadata = json.load(f)
                    if 'description' in metadata:
                        bug_info["description"] = metadata['description']
            except:
                pass
    
    # Construct description from available info
    if not bug_info["description"]:
        desc_parts = []
        
        if bug_info["modified_classes"]:
            desc_parts.append(f"Bug in classes: {', '.join(bug_info['modified_classes'][:3])}")
        
        if bug_info["test_trigger"]:
            desc_parts.append(f"Triggered by test: {bug_info['test_trigger']}")
        
        bug_info["description"] = ". ".join(desc_parts) if desc_parts else "Bug details not available"
    
    # Generate a better title
    if bug_info["modified_classes"]:
        main_class = bug_info["modified_classes"][0].split('.')[-1]
        bug_info["title"] = f"Bug in {main_class}"
    else:
        bug_info["title"] = f"Bug {project}-{bug_id}"
    
    logger.info(f"  ✓ Extracted: {bug_info['title']}")
    
    return bug_info

def get_defects4j_bugs(project: str, max_bugs: int = None) -> list:
    """Get list of bug IDs for a project."""
    result = subprocess.run(
        ["defects4j", "bids", "-p", project],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to get bugs for {project}")
        return []
    
    bug_ids = result.stdout.strip().split('\n')
    if max_bugs:
        bug_ids = bug_ids[:max_bugs]
    
    return bug_ids

def main():
    """Extract bug information for selected bugs."""
    
    print("=" * 80)
    print("EXTRACTING BUG INFORMATION FROM DEFECTS4J")
    print("=" * 80)
    
    # Projects to extract from
    projects_config = {
        "Lang": 30,    # Extract 30 Lang bugs
        "Math": 10,    # Extract 10 Math bugs
        "Time": 10,    # Extract 10 Time bugs
    }
    
    all_bugs = []
    
    for project, count in projects_config.items():
        print(f"\n{project}: Extracting {count} bugs...")
        
        # Get bug IDs
        bug_ids = get_defects4j_bugs(project, count)
        print(f"  Found {len(bug_ids)} bugs")
        
        # Extract info for each bug
        for bug_id in bug_ids:
            try:
                bug_info = get_bug_info(project, bug_id)
                all_bugs.append(bug_info)
            except Exception as e:
                logger.error(f"  Failed to extract {project}-{bug_id}: {e}")
                # Add placeholder
                all_bugs.append({
                    "project": project,
                    "bug_id": bug_id,
                    "title": f"Bug {project}-{bug_id}",
                    "description": f"Bug in project {project}",
                    "report_url": "",
                    "report_id": "",
                    "is_crash": False
                })
    
    # Save to file
    output_file = Path("data/bugs/bug_reports.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_bugs, f, indent=2)
    
    print(f"\n" + "=" * 80)
    print(f"✓ Extracted {len(all_bugs)} bug reports")
    print(f"✓ Saved to: {output_file}")
    print("=" * 80)
    
    # Print sample
    print("\nSample bug report:")
    print(json.dumps(all_bugs[0], indent=2))

if __name__ == "__main__":
    main()
