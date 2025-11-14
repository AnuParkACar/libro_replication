"""Test execution on buggy and fixed versions with BRT classification."""

import subprocess
from typing import Dict, Optional, Tuple
from pathlib import Path
import re
import logging
import time

logger = logging.getLogger(__name__)

class TestExecutor:
    """Executes tests on Defects4J projects."""
    
    def __init__(self, defects4j_path: str):
        """
        Initialize test executor.
        
        Args:
            defects4j_path: Path to Defects4J installation
        """
        self.defects4j_path = Path(defects4j_path)
    
    def execute_on_both_versions(self, project: str, bug_id: str,
                                 test_class: str, test_method: str,
                                 work_dir: Path, timeout: int = 120) -> Dict:
        """
        Execute test on both buggy and fixed versions.
        
        Args:
            project: Project name (e.g., "Lang")
            bug_id: Bug ID
            test_class: Test class name
            test_method: Test method name
            work_dir: Working directory for checkouts
            timeout: Execution timeout
            
        Returns:
            Dict with buggy_result, fixed_result, is_brt
        """
        logger.info(f"Executing {test_class}::{test_method} on {project}-{bug_id}")
        
        # Checkout buggy version
        logger.info("  Checking out buggy version...")
        buggy_dir = self._checkout_version(project, bug_id, "buggy", work_dir)
        if not buggy_dir:
            return {
                'buggy_result': {'error': 'checkout_failed'},
                'fixed_result': {'error': 'checkout_failed'},
                'is_brt': False
            }
        
        # Checkout fixed version
        logger.info("  Checking out fixed version...")
        fixed_dir = self._checkout_version(project, bug_id, "fixed", work_dir)
        if not fixed_dir:
            return {
                'buggy_result': {'error': 'checkout_failed'},
                'fixed_result': {'error': 'checkout_failed'},
                'is_brt': False
            }
        
        # Execute on buggy version
        logger.info("  Executing on buggy version...")
        buggy_result = self.execute_test(test_class, test_method, buggy_dir, timeout)
        
        # Execute on fixed version
        logger.info("  Executing on fixed version...")
        fixed_result = self.execute_test(test_class, test_method, fixed_dir, timeout)
        
        # Determine if it's a BRT
        is_brt = self.is_bug_reproducing(buggy_result, fixed_result)
        
        logger.info(f"  Result: {'BRT ✓' if is_brt else 'Not BRT ✗'}")
        
        return {
            'buggy_result': buggy_result,
            'fixed_result': fixed_result,
            'is_brt': is_brt
        }
    
    def _checkout_version(self, project: str, bug_id: str, 
                         version: str, work_dir: Path) -> Optional[Path]:
        """Checkout a specific version of a bug."""
        version_suffix = 'b' if version == 'buggy' else 'f'
        checkout_dir = work_dir / f"{project}_{bug_id}_{version}"
        
        # Remove if exists
        if checkout_dir.exists():
            subprocess.run(['rm', '-rf', str(checkout_dir)], capture_output=True)
        
        result = subprocess.run(
            ['defects4j', 'checkout', '-p', project, '-v', f'{bug_id}{version_suffix}',
             '-w', str(checkout_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            logger.error(f"    Checkout failed: {result.stderr[:200]}")
            return None
        
        return checkout_dir
    
    def execute_test(self, test_class: str, test_method: str,
                    project_path: Path, timeout: int = 60) -> Dict[str, any]:
        """
        Execute a single test method.
        
        Args:
            test_class: Fully qualified test class name
            test_method: Test method name
            project_path: Path to checked out project
            timeout: Execution timeout in seconds
            
        Returns:
            Dict with keys: compiled, passed, failed, error_type, error_message, 
                           stdout, stderr, execution_time
        """
        result = {
            "compiled": False,
            "passed": False,
            "failed": False,
            "error_type": None,
            "error_message": None,
            "stdout": "",
            "stderr": "",
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            # First, compile the project
            logger.debug(f"    Compiling...")
            compile_result = subprocess.run(
                ["defects4j", "compile"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if compile_result.returncode != 0:
                result["error_type"] = "CompilationError"
                result["error_message"] = self._extract_compilation_error(compile_result.stderr)
                result["stderr"] = compile_result.stderr
                logger.debug(f"    ✗ Compilation failed")
                return result
            
            result["compiled"] = True
            logger.debug(f"    ✓ Compiled successfully")
            
            # Execute test
            test_spec = f"{test_class}::{test_method}"
            logger.debug(f"    Running test: {test_spec}")
            
            test_result = subprocess.run(
                ["defects4j", "test", "-t", test_spec],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            result["stdout"] = test_result.stdout
            result["stderr"] = test_result.stderr
            result["execution_time"] = time.time() - start_time
            
            # Parse result
            if self._is_test_passed(test_result):
                result["passed"] = True
                logger.debug(f"    ✓ Test passed")
            else:
                result["failed"] = True
                result["error_type"], result["error_message"] = self._parse_failure(
                    test_result.stdout + test_result.stderr
                )
                logger.debug(f"    ✗ Test failed: {result['error_type']}")
        
        except subprocess.TimeoutExpired:
            result["error_type"] = "Timeout"
            result["error_message"] = f"Test execution exceeded {timeout}s"
            result["execution_time"] = timeout
            logger.debug(f"    ✗ Timeout")
        
        except Exception as e:
            result["error_type"] = "ExecutionError"
            result["error_message"] = str(e)
            result["execution_time"] = time.time() - start_time
            logger.debug(f"    ✗ Execution error: {e}")
        
        return result
    
    def is_bug_reproducing(self, buggy_result: Dict, fixed_result: Dict) -> bool:
        """
        Determine if test is a Bug Reproducing Test (BRT).
        
        A test is BRT if:
        - It compiles on both versions
        - It fails on buggy version
        - It passes on fixed version
        
        Args:
            buggy_result: Execution result on buggy version
            fixed_result: Execution result on fixed version
            
        Returns:
            True if test is a BRT
        """
        return (
            buggy_result.get("compiled", False) and
            fixed_result.get("compiled", False) and
            buggy_result.get("failed", False) and
            fixed_result.get("passed", False)
        )
    
    def classify_test(self, buggy_result: Dict, fixed_result: Dict) -> str:
        """
        Classify test result into categories.
        
        Returns:
            One of: BRT, FIB (Fails In Buggy), PIB (Passes In Buggy),
                   COMPILATION_ERROR, EXECUTION_ERROR
        """
        if not buggy_result.get("compiled"):
            return "COMPILATION_ERROR_BUGGY"
        
        if not fixed_result.get("compiled"):
            return "COMPILATION_ERROR_FIXED"
        
        buggy_failed = buggy_result.get("failed", False)
        fixed_passed = fixed_result.get("passed", False)
        
        if buggy_failed and fixed_passed:
            return "BRT"  # Bug Reproducing Test
        elif buggy_failed:
            return "FIB"  # Fails In Buggy (but also fails in fixed)
        elif not buggy_failed:
            return "PIB"  # Passes In Buggy (doesn't trigger bug)
        else:
            return "UNKNOWN"
    
    def _is_test_passed(self, test_result: subprocess.CompletedProcess) -> bool:
        """Determine if test passed from Defects4J output."""
        stdout = test_result.stdout
        stderr = test_result.stderr
        
        # Defects4J success indicators
        if "OK" in stdout:
            return True
        
        if test_result.returncode == 0:
            return True
        
        # Check for failure indicators
        failure_indicators = [
            "FAILED", "FAIL", "FAILURES", "AssertionError",
            "junit.framework.AssertionFailedError"
        ]
        
        combined_output = stdout + stderr
        if any(indicator in combined_output for indicator in failure_indicators):
            return False
        
        # Default to success if no clear failure
        return test_result.returncode == 0
    
    def _extract_compilation_error(self, stderr: str) -> str:
        """Extract meaningful compilation error message."""
        lines = stderr.split('\n')
        
        # Look for error lines
        errors = []
        for line in lines:
            if 'error:' in line.lower():
                errors.append(line.strip())
        
        if errors:
            return '; '.join(errors[:3])  # First 3 errors
        
        return stderr[:200]  # First 200 chars as fallback
    
    def _parse_failure(self, output: str) -> Tuple[str, str]:
        """Parse error type and message from test output."""
        # Common patterns
        error_patterns = [
            (r'(AssertionError|AssertionFailedError)', r'(AssertionError[^\n]+)'),
            (r'(NullPointerException)', r'(NullPointerException[^\n]+)'),
            (r'(IllegalArgumentException)', r'(IllegalArgumentException[^\n]+)'),
            (r'(ArrayIndexOutOfBoundsException)', r'(ArrayIndexOutOfBoundsException[^\n]+)'),
            (r'(\w+Exception)', r'(\w+Exception[^\n]+)')
        ]
        
        for type_pattern, msg_pattern in error_patterns:
            type_match = re.search(type_pattern, output)
            if type_match:
                error_type = type_match.group(1)
                
                # Try to get full message
                msg_match = re.search(msg_pattern, output)
                if msg_match:
                    error_msg = msg_match.group(1)[:200]  # Limit length
                else:
                    error_msg = error_type
                
                return error_type, error_msg
        
        # Check for assertion failures
        if 'expected' in output.lower() and 'but was' in output.lower():
            match = re.search(r'expected:<([^>]+)>\s+but\s+was:<([^>]+)>', output, re.IGNORECASE)
            if match:
                return "AssertionError", f"expected:<{match.group(1)}> but was:<{match.group(2)}>"
        
        return "UnknownError", output[:200]
