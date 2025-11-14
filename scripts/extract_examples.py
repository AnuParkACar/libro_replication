#!/usr/bin/env python3
"""
Extract few-shot examples from Defects4J.
We'll use actual bug reports + developer-written tests as examples.
"""

import subprocess
import json
import re
from pathlib import Path
import tempfile

def checkout_bug(project, bug_id, work_dir):
    """Checkout a bug to temporary directory."""
    bug_dir = work_dir / f"{project}_{bug_id}"
    
    # Checkout buggy version
    result = subprocess.run(
        ["defects4j", "checkout", "-p", project, "-v", f"{bug_id}b", "-w", str(bug_dir)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    return bug_dir

def get_bug_report(project, bug_id):
    """Get bug report information from Defects4J."""
    result = subprocess.run(
        ["defects4j", "info", "-p", project, "-b", str(bug_id)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    # Parse output
    info = {}
    for line in result.stdout.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    
    return info

def get_trigger_test(project, bug_id, bug_dir):
    """Get the developer-written test that reveals the bug."""
    # Get list of triggering tests
    result = subprocess.run(
        ["defects4j", "export", "-p", "tests.trigger"],
        cwd=bug_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 or not result.stdout.strip():
        return None
    
    # Parse test class and method
    trigger_tests = result.stdout.strip().split('\n')
    if not trigger_tests:
        return None
    
    # Take first trigger test
    test_spec = trigger_tests[0].strip()
    if '::' not in test_spec:
        return None
    
    class_name, method_name = test_spec.split('::')
    
    # Find test file
    test_file = find_test_file(bug_dir, class_name)
    if not test_file:
        return None
    
    # Extract test method
    test_method = extract_method(test_file, method_name)
    
    return {
        "class": class_name,
        "method": method_name,
        "code": test_method,
        "file": str(test_file)
    }

def find_test_file(bug_dir, class_name):
    """Find Java file for test class."""
    # Convert class name to file path
    file_name = class_name.replace('.', '/') + '.java'
    
    # Search in common test directories
    search_dirs = [
        bug_dir / 'src' / 'test' / 'java',
        bug_dir / 'test',
        bug_dir / 'tests'
    ]
    
    for search_dir in search_dirs:
        if search_dir.exists():
            test_file = search_dir / file_name
            if test_file.exists():
                return test_file
            
            # Also try searching recursively
            for java_file in search_dir.rglob('*.java'):
                if java_file.name == class_name.split('.')[-1] + '.java':
                    return java_file
    
    return None

def extract_method(file_path, method_name):
    """Extract a specific method from a Java file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Simple pattern to find method
    # Look for: public/private void methodName() {
    pattern = rf'(public|private|protected)?\s+void\s+{method_name}\s*\([^)]*\)\s*\{{'
    
    match = re.search(pattern, content)
    if not match:
        return None
    
    # Extract method body
    start = match.start()
    brace_count = 0
    in_method = False
    end = start
    
    for i in range(start, len(content)):
        if content[i] == '{':
            brace_count += 1
            in_method = True
        elif content[i] == '}':
            brace_count -= 1
            if in_method and brace_count == 0:
                end = i + 1
                break
    
    method_code = content[start:end]
    
    # Clean up (remove extra indentation)
    lines = method_code.split('\n')
    if lines:
        # Find minimum indentation
        min_indent = float('inf')
        for line in lines[1:]:  # Skip first line
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        if min_indent != float('inf'):
            cleaned_lines = [lines[0]] + [line[min_indent:] if len(line) > min_indent else line 
                                          for line in lines[1:]]
            method_code = '\n'.join(cleaned_lines)
    
    return method_code.strip()

def create_example(project, bug_id):
    """Create a complete example from a bug."""
    print(f"Processing {project}-{bug_id}...", flush=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Checkout bug
        bug_dir = checkout_bug(project, bug_id, work_dir)
        if not bug_dir:
            print(f"  ✗ Failed to checkout")
            return None
        
        # Get bug report
        bug_info = get_bug_report(project, bug_id)
        if not bug_info:
            print(f"  ✗ Failed to get bug info")
            return None
        
        # Get trigger test
        test_info = get_trigger_test(project, bug_id, bug_dir)
        if not test_info or not test_info['code']:
            print(f"  ✗ Failed to extract test")
            return None
        
        # Get report URL and description
        report_url = bug_info.get('Report URL', '')
        
        # If we have a URL, try to fetch description (simplified)
        title = bug_info.get('Report', 'Bug Report')
        description = f"See bug report: {report_url}"
        
        # For demonstration, use simplified description
        # In practice, you might scrape the actual report
        
        example = {
            "project": project,
            "bug_id": bug_id,
            "title": title,
            "description": description,
            "report_url": report_url,
            "test": test_info['code'],
            "test_class": test_info['class'],
            "test_method": test_info['method']
        }
        
        print(f"  ✓ Example created")
        return example

def main():
    """Create few-shot example bank."""
    
    # Select specific bugs known to have good examples
    # These are hand-picked to be clear and simple
    example_bugs = [
        ("Lang", "1"),   # NumberUtils.isNumber should return false for blank strings
        ("Jsoup", "1"),  # HTML parsing issue
        ("Lang", "6"),   # String translation issue
        ("Math", "2"),   # Distribution calculation
    ]
    
    examples = []
    
    for project, bug_id in example_bugs:
        example = create_example(project, bug_id)
        if example:
            examples.append(example)
    
    # Save examples
    output_dir = Path("data/examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "few_shot_examples.json", 'w') as f:
        json.dump(examples, f, indent=2)
    
    print(f"\n✓ Created {len(examples)} examples")
    print(f"  Saved to: {output_dir / 'few_shot_examples.json'}")
    
    # Print first example for verification
    if examples:
        print("\nFirst example:")
        print(json.dumps(examples[0], indent=2))

if __name__ == "__main__":
    main()
