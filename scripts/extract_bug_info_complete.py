#!/usr/bin/env python3
"""Extract complete bug information including actual issue tracker data."""

import subprocess
import json
import re
from pathlib import Path
import tempfile
import logging
from typing import Dict, List, Optional
import time
import requests
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_jira_issue(issue_url: str) -> Optional[Dict]:
    """Fetch JIRA issue details from Apache JIRA."""
    try:
        # Extract issue key from URL (e.g., LANG-1 from https://issues.apache.org/jira/browse/LANG-1)
        match = re.search(r'/browse/([A-Z]+-\d+)', issue_url)
        if not match:
            return None
        
        issue_key = match.group(1)
        
        # Apache JIRA REST API endpoint
        api_url = f"https://issues.apache.org/jira/rest/api/2/issue/{issue_key}"
        
        logger.info(f"  Fetching JIRA issue: {issue_key}")
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data['fields'].get('summary', ''),
                "description": data['fields'].get('description', ''),
                "issue_type": data['fields'].get('issuetype', {}).get('name', ''),
                "status": data['fields'].get('status', {}).get('name', ''),
                "priority": data['fields'].get('priority', {}).get('name', ''),
            }
        else:
            logger.warning(f"    Failed to fetch JIRA issue (status {response.status_code})")
            return None
    
    except Exception as e:
        logger.warning(f"    Error fetching JIRA: {e}")
        return None

def fetch_github_issue(issue_url: str) -> Optional[Dict]:
    """Fetch GitHub issue details."""
    try:
        # Extract owner, repo, and issue number from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', issue_url)
        if not match:
            return None
        
        owner, repo, issue_num = match.groups()
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"
        
        logger.info(f"  Fetching GitHub issue: {owner}/{repo}#{issue_num}")
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get('title', ''),
                "description": data.get('body', ''),
                "state": data.get('state', ''),
                "labels": [label['name'] for label in data.get('labels', [])],
            }
        else:
            logger.warning(f"    Failed to fetch GitHub issue (status {response.status_code})")
            return None
    
    except Exception as e:
        logger.warning(f"    Error fetching GitHub: {e}")
        return None

def extract_report_info(project: str, bug_id: str) -> Dict:
    """Extract report URL and ID from Defects4J info."""
    
    result = subprocess.run(
        ["defects4j", "info", "-p", project, "-b", bug_id],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    report_info = {
        "report_url": "",
        "report_id": "",
        "issue_tracker": ""
    }
    
    if result.returncode != 0:
        return report_info
    
    output = result.stdout
    
    # Extract report URL
    url_match = re.search(r'Report:\s*(.+)', output)
    if url_match:
        url = url_match.group(1).strip()
        report_info["report_url"] = url
        
        # Determine issue tracker type and extract ID
        if "issues.apache.org/jira" in url:
            report_info["issue_tracker"] = "JIRA"
            id_match = re.search(r'/browse/([A-Z]+-\d+)', url)
            if id_match:
                report_info["report_id"] = id_match.group(1)
        
        elif "github.com" in url:
            report_info["issue_tracker"] = "GitHub"
            id_match = re.search(r'/issues/(\d+)', url)
            if id_match:
                report_info["report_id"] = id_match.group(1)
        
        elif "sourceforge.net" in url:
            report_info["issue_tracker"] = "SourceForge"
            id_match = re.search(r'aid=(\d+)', url)
            if id_match:
                report_info["report_id"] = id_match.group(1)
        
        else:
            # Try to extract any ID-like pattern
            id_match = re.search(r'id[=:](\d+)', url, re.IGNORECASE)
            if id_match:
                report_info["report_id"] = id_match.group(1)
    
    return report_info

def get_modified_classes(project: str, bug_id: str) -> List[str]:
    """Extract list of modified classes."""
    
    result = subprocess.run(
        ["defects4j", "info", "-p", project, "-b", bug_id],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        return []
    
    output = result.stdout
    classes = re.findall(r'  - (.+)', output)
    
    return classes

def get_trigger_tests(project: str, bug_id: str, work_dir: Path) -> List[str]:
    """Get list of trigger tests."""
    
    result = subprocess.run(
        ["defects4j", "export", "-p", "tests.trigger"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        return []
    
    tests = result.stdout.strip().split('\n')
    return [t for t in tests if t]

def get_bug_info_complete(project: str, bug_id: str) -> Dict:
    """Extract complete bug information including issue tracker data."""
    
    logger.info(f"Processing {project}-{bug_id}")
    
    bug_info = {
        "project": project,
        "bug_id": bug_id,
        "title": "",
        "description": "",
        "report_url": "",
        "report_id": "",
        "issue_tracker": "",
        "is_crash": False,
        "modified_classes": [],
        "trigger_tests": [],
        "issue_data": None
    }
    
    try:
        # Step 1: Get report info
        report_info = extract_report_info(project, bug_id)
        bug_info.update(report_info)
        
        logger.info(f"  Report: {bug_info['report_id']} ({bug_info['issue_tracker']})")
        
        # Step 2: Get modified classes
        bug_info["modified_classes"] = get_modified_classes(project, bug_id)
        
        # Step 3: Checkout to get trigger tests
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir) / f"{project}_{bug_id}"
            
            checkout_result = subprocess.run(
                ["defects4j", "checkout", "-p", project, "-v", f"{bug_id}b", "-w", str(work_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if checkout_result.returncode == 0:
                bug_info["trigger_tests"] = get_trigger_tests(project, bug_id, work_dir)
        
        # Step 4: Fetch actual issue data from tracker
        if bug_info["report_url"]:
            time.sleep(1)  # Rate limiting
            
            if bug_info["issue_tracker"] == "JIRA":
                issue_data = fetch_jira_issue(bug_info["report_url"])
                if issue_data:
                    bug_info["issue_data"] = issue_data
                    bug_info["title"] = issue_data.get("title", "")
                    bug_info["description"] = issue_data.get("description", "")
                    # Check if it's a crash
                    if issue_data.get("issue_type") in ["Bug", "Exception"]:
                        bug_info["is_crash"] = "exception" in bug_info["description"].lower() or \
                                               "error" in bug_info["description"].lower()
            
            elif bug_info["issue_tracker"] == "GitHub":
                issue_data = fetch_github_issue(bug_info["report_url"])
                if issue_data:
                    bug_info["issue_data"] = issue_data
                    bug_info["title"] = issue_data.get("title", "")
                    bug_info["description"] = issue_data.get("description", "")
                    bug_info["is_crash"] = "bug" in [l.lower() for l in issue_data.get("labels", [])]
        
        # Step 5: Construct description if we didn't get one from issue tracker
        if not bug_info["description"] or len(bug_info["description"]) < 20:
            desc_parts = []
            
            if bug_info["title"]:
                desc_parts.append(bug_info["title"])
            
            if bug_info["modified_classes"]:
                classes_str = ", ".join([c.split('.')[-1] for c in bug_info["modified_classes"][:3]])
                desc_parts.append(f"Bug affects classes: {classes_str}")
            
            if bug_info["trigger_tests"]:
                test_name = bug_info["trigger_tests"][0].split("::")[-1]
                desc_parts.append(f"Failing test: {test_name}")
            
            bug_info["description"] = ". ".join(desc_parts) if desc_parts else f"Bug in {project}"
        
        # Clean up description (remove excessive whitespace, HTML tags, etc.)
        if bug_info["description"]:
            # Remove common JIRA formatting
            desc = bug_info["description"]
            desc = re.sub(r'\{code[^\}]*\}.*?\{code\}', '[code snippet]', desc, flags=re.DOTALL)
            desc = re.sub(r'\{quote\}.*?\{quote\}', '[quote]', desc, flags=re.DOTALL)
            desc = re.sub(r'\r\n|\r|\n', ' ', desc)
            desc = re.sub(r'\s+', ' ', desc)
            desc = desc[:1000]  # Limit length
            bug_info["description"] = desc.strip()
        
        # Set default title if we don't have one
        if not bug_info["title"]:
            if bug_info["modified_classes"]:
                main_class = bug_info["modified_classes"][0].split('.')[-1]
                bug_info["title"] = f"Bug in {main_class}"
            else:
                bug_info["title"] = f"Bug {project}-{bug_id}"
        
        logger.info(f"  ✓ Title: {bug_info['title'][:60]}...")
        logger.info(f"  ✓ Description: {len(bug_info['description'])} chars")
        
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        # Provide minimal fallback
        if not bug_info["title"]:
            bug_info["title"] = f"Bug {project}-{bug_id}"
        if not bug_info["description"]:
            bug_info["description"] = f"Bug in {project}, ID {bug_id}. See Defects4J for details."
    
    return bug_info

def main():
    """Extract complete bug information with issue tracker data."""
    
    print("=" * 80)
    print("EXTRACTING COMPLETE BUG INFORMATION")
    print("=" * 80)
    
    # Define bugs to extract (start with 30 for testing)
    bugs_config = [
        # Lang bugs (30 total)
        ("Lang", list(range(1, 31))),
        # Math bugs (10)
        ("Math", list(range(1, 11))),
        # Time bugs (10)
        ("Time", list(range(1, 11))),
    ]
    
    all_bugs = []
    
    for project, bug_ids in bugs_config:
        print(f"\n{'=' * 80}")
        print(f"Processing {project}: {len(bug_ids)} bugs")
        print(f"{'=' * 80}")
        
        for bug_id in bug_ids:
            try:
                bug_info = get_bug_info_complete(project, str(bug_id))
                all_bugs.append(bug_info)
                
                # Small delay to respect rate limits
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Failed {project}-{bug_id}: {e}")
                # Add minimal placeholder
                all_bugs.append({
                    "project": project,
                    "bug_id": str(bug_id),
                    "title": f"Bug {project}-{bug_id}",
                    "description": f"Bug in {project} project. Details not available.",
                    "report_url": "",
                    "report_id": "",
                    "issue_tracker": "",
                    "is_crash": False,
                    "modified_classes": [],
                    "trigger_tests": []
                })
    
    # Save to file
    output_file = Path("data/bugs/bug_reports.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_bugs, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'=' * 80}")
    print(f"✓ Extracted {len(all_bugs)} bug reports")
    print(f"✓ Saved to: {output_file}")
    
    # Statistics
    with_urls = sum(1 for b in all_bugs if b['report_url'])
    with_ids = sum(1 for b in all_bugs if b['report_id'])
    with_descriptions = sum(1 for b in all_bugs if len(b.get('description', '')) > 50)
    with_issue_data = sum(1 for b in all_bugs if b.get('issue_data'))
    
    print(f"\n📊 Statistics:")
    print(f"  Total bugs: {len(all_bugs)}")
    print(f"  With report URLs: {with_urls}")
    print(f"  With report IDs: {with_ids}")
    print(f"  With descriptions (>50 chars): {with_descriptions}")
    print(f"  With fetched issue data: {with_issue_data}")
    
    # By issue tracker
    trackers = {}
    for bug in all_bugs:
        tracker = bug.get('issue_tracker', 'Unknown')
        trackers[tracker] = trackers.get(tracker, 0) + 1
    
    print(f"\n📋 By Issue Tracker:")
    for tracker, count in sorted(trackers.items()):
        print(f"  {tracker}: {count}")
    
    # Show samples
    print(f"\n📝 Sample Bug Reports:\n")
    
    # Show first Lang bug
    lang_bug = next((b for b in all_bugs if b['project'] == 'Lang'), None)
    if lang_bug:
        print(f"Lang-{lang_bug['bug_id']}:")
        print(f"  Title: {lang_bug['title']}")
        print(f"  Report: {lang_bug['report_id']} ({lang_bug['issue_tracker']})")
        print(f"  URL: {lang_bug['report_url']}")
        print(f"  Description: {lang_bug['description'][:200]}...")
        print(f"  Modified classes: {', '.join(lang_bug['modified_classes'][:3])}")
        print()
    
    # Show first Math bug
    math_bug = next((b for b in all_bugs if b['project'] == 'Math'), None)
    if math_bug:
        print(f"Math-{math_bug['bug_id']}:")
        print(f"  Title: {math_bug['title']}")
        print(f"  Report: {math_bug['report_id']} ({math_bug['issue_tracker']})")
        print(f"  Description: {math_bug['description'][:200]}...")
        print()
    
    print("=" * 80)
    print("Ready to run: python3 scripts/day3_batch_run.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
