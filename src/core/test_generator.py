"""Test generation using LLM with robust parsing and error handling."""

from typing import List, Dict, Optional
import re
import logging
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)

class TestGenerator:
    """Generates test candidates using an LLM."""
    
    def __init__(self, model_manager, cache_dir: Optional[str] = None):
        """
        Initialize test generator.
        
        Args:
            model_manager: ModelManager instance
            cache_dir: Directory to cache generations (for reuse/debugging)
        """
        self.model = model_manager
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_tests(self, prompt: str, n_samples: int = 10,
                      bug_id: str = None) -> List[Dict[str, str]]:
        """
        Generate multiple test candidates from a prompt.
        
        Args:
            prompt: Formatted prompt string
            n_samples: Number of test samples to generate
            bug_id: Optional bug ID for caching
            
        Returns:
            List of dicts with keys: test_code, raw_output, sample_id
        """
        logger.info(f"Generating {n_samples} test candidates for bug {bug_id}")
        
        tests = []
        generation_times = []
        
        for i in range(n_samples):
            try:
                start_time = time.time()
                
                # Generate from model
                logger.debug(f"  Sample {i+1}/{n_samples}...")
                output = self.model.generate(
                    prompt,
                    max_tokens=256,
                    temperature=0.7,
                    stop_strings=["```"]
                )
                
                generation_time = time.time() - start_time
                generation_times.append(generation_time)
                
                # Extract test method
                test_code = self._extract_test_method(output, prompt)
                
                if test_code:
                    test_dict = {
                        "test_code": test_code,
                        "raw_output": output,
                        "sample_id": i,
                        "generation_time": generation_time,
                        "prompt_length": len(prompt)
                    }
                    tests.append(test_dict)
                    logger.debug(f"    ✓ Valid test extracted")
                else:
                    logger.debug(f"    ✗ Could not extract valid test")
            
            except Exception as e:
                logger.warning(f"  Sample {i} failed: {e}")
                continue
        
        # Cache if requested
        if self.cache_dir and bug_id:
            self._cache_generations(bug_id, tests, prompt)
        
        avg_time = sum(generation_times) / len(generation_times) if generation_times else 0
        logger.info(f"Generated {len(tests)}/{n_samples} valid tests (avg: {avg_time:.2f}s)")
        
        return tests
    
    def _extract_test_method(self, output: str, prompt: str) -> Optional[str]:
        """
        Extract test method from LLM output.
        
        The prompt ends with "public void test", and the LLM should
        complete the method. We extract everything after the prompt.
        """
        # Strategy 1: Remove the prompt prefix
        if prompt in output:
            generated = output[len(prompt):]
        else:
            # Strategy 2: Find the last occurrence of "public void test"
            matches = list(re.finditer(r'public\s+void\s+test', output, re.IGNORECASE))
            if matches:
                last_match = matches[-1]
                generated = output[last_match.start():]
            else:
                logger.debug("    Could not find 'public void test' in output")
                return None
        
        # Clean up the generated text
        generated = generated.strip()
        
        # Make sure we have the full method signature
        if not generated.startswith("public"):
            generated = "public void test" + generated
        
        # Extract just the method (handle multiple methods)
        method = self._extract_single_method(generated)
        
        if not method:
            logger.debug("    Could not extract complete method")
            return None
        
        # Validate the method
        if not self._validate_method(method):
            logger.debug("    Method validation failed")
            return None
        
        return method
    
    def _extract_single_method(self, code: str) -> Optional[str]:
        """Extract a single complete method from code."""
        # Find method start
        method_start = re.search(r'public\s+void\s+test\w*\s*\([^)]*\)', code)
        if not method_start:
            return None
        
        start_idx = method_start.start()
        
        # Find matching braces
        brace_count = 0
        in_method = False
        end_idx = start_idx
        
        for i in range(start_idx, len(code)):
            char = code[i]
            
            if char == '{':
                brace_count += 1
                in_method = True
            elif char == '}':
                brace_count -= 1
                if in_method and brace_count == 0:
                    end_idx = i + 1
                    break
        
        if brace_count != 0:
            # Unmatched braces
            return None
        
        return code[start_idx:end_idx].strip()
    
    def _validate_method(self, method: str) -> bool:
        """Basic validation of extracted method."""
        # Must have method signature
        if not re.search(r'public\s+void\s+test\w*\s*\([^)]*\)', method):
            return False
        
        # Must have braces
        if '{' not in method or '}' not in method:
            return False
        
        # Must have some content (at least 10 chars inside method body)
        body_match = re.search(r'\{(.+)\}', method, re.DOTALL)
        if not body_match or len(body_match.group(1).strip()) < 10:
            return False
        
        # Should not have obvious syntax errors
        if method.count('{') != method.count('}'):
            return False
        
        return True
    
    def _cache_generations(self, bug_id: str, tests: List[Dict], prompt: str):
        """Cache generated tests for later analysis."""
        cache_file = self.cache_dir / f"{bug_id}_generations.json"
        
        cache_data = {
            "bug_id": bug_id,
            "prompt": prompt,
            "num_tests": len(tests),
            "tests": tests
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.debug(f"  Cached generations to {cache_file}")
    
    def load_from_cache(self, bug_id: str) -> Optional[List[Dict]]:
        """Load previously generated tests from cache."""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{bug_id}_generations.json"
        if not cache_file.exists():
            return None
        
        with open(cache_file) as f:
            cache_data = json.load(f)
        
        logger.info(f"Loaded {len(cache_data['tests'])} tests from cache")
        return cache_data['tests']
