#!/usr/bin/env python3
"""
Helper to view and manually enhance bug reports.
"""

import json
import sys
from pathlib import Path

def view_report(project, bug_id):
    """View a bug report."""
    with open("data/bugs/bug_reports.json") as f:
        reports = json.load(f)
    
    report = None
    for r in reports:
        if r['project'] == project and str(r['bug_id']) == str(bug_id):
            report = r
            break
    
    if not report:
        print(f"Bug {project}-{bug_id} not found")
        return
    
    print(f"Project: {report['project']}")
    print(f"Bug ID: {report['bug_id']}")
    print(f"Title: {report['title']}")
    print(f"URL: {report['report_url']}")
    print(f"\nDescription:\n{report['description']}")
    
    if report['report_url']:
        print(f"\nOpen in browser: {report['report_url']}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python view_bug_report.py <project> <bug_id>")
        print("Example: python view_bug_report.py Lang 1")
        sys.exit(1)
    
    project = sys.argv[1]
    bug_id = sys.argv[2]
    
    view_report(project, bug_id)

if __name__ == "__main__":
    main()
