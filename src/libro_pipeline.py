"""Main LIBRO pipeline orchestrator - Complete implementation."""

from pathlib import Path
from typing import List, Dict
import json
import logging
import tempfile
import time

from src.model_manager import ModelManager
from src.core.prompt_builder import PromptBuilder
from src.core.test_generator import TestGenerator
from src.core.test_processor import TestProcessor
from src.core.test_executor import TestExecutor
from src.core.test_ranker import TestRanker
from src.utils.config import Config

logger = logging.getLogger(__name__)

class LIBROPipeline:
    """Main pipeline for LIBRO replication."""
    
    def __init__(self, config_path: str = "config/default_config.yaml"):
        """Initialize pipeline with configuration."""
        self.config = Config(config_path)
        self._setup_logging()
        
        # Initialize components
        self.model_manager = None
        self.prompt_builder = PromptBuilder(
            num_examples=self.config.get("prompt.num_examples"),
            examples_file=self.config.get("prompt.examples_file", 
                                         "data/examples/manual_examples.json")
        )
        self.test_generator = None
        self.test_processor = TestProcessor(
            defects4j_path=self.config.get("defects4j.path")
        )
        self.test_executor = TestExecutor(
            defects4j_path=self.config.get("defects4j.path")
        )
        self.test_ranker = TestRanker(
            agreement_threshold=self.config.get("ranking.agreement_threshold")
        )
        
        self.logger = logging.getLogger(__name__)
    
    def load_model(self, model_key: str = None):
        """Load the LLM model."""
        model_key = model_key or self.config.get("model.primary")
        cache_dir = self.config.get("model.cache_dir")
        
        self.logger.info(f"Loading model: {model_key}")
        self.model_manager = ModelManager(model_key, cache_dir)
        self.model_manager.load()
        
        self.test_generator = TestGenerator(
            model_manager=self.model_manager,
            cache_dir=self.config.get("generation.cache_dir", "cache/generations")
        )
        self.logger.info("Model loaded successfully")
    
    def run_on_bug(self, bug_info: Dict, work_dir: Path = None) -> Dict:
        """
        Run full pipeline on a single bug.
        
        Args:
            bug_info: Dict with project, bug_id, title, description
            work_dir: Working directory for checkouts
            
        Returns:
            Dict with results including BRTs, rankings, metrics
        """
        bug_id = f"{bug_info['project']}-{bug_info['bug_id']}"
        self.logger.info(f"=" * 80)
        self.logger.info(f"Processing {bug_id}")
        self.logger.info(f"=" * 80)
        
        start_time = time.time()
        
        results = {
            "bug_id": bug_id,
            "project": bug_info['project'],
            "bug_number": bug_info['bug_id'],
            "generated_tests": [],
            "injected_tests": [],
            "fib_tests": [],
            "brt_tests": [],
            "ranking": [],
            "metrics": {},
            "errors": []
        }
        
        try:
            # Step 1: Construct prompt
            self.logger.info("Step 1: Constructing prompt...")
            prompt = self.prompt_builder.construct_prompt(
                bug_info,
                current_project=bug_info['project']
            )
            
            # Step 2: Generate test candidates
            self.logger.info("Step 2: Generating test candidates...")
            n_samples = self.config.get("generation.samples_per_bug")
            candidates = self.test_generator.generate_tests(prompt, n_samples, bug_id)
            results["generated_tests"] = candidates
            self.logger.info(f"  Generated {len(candidates)} test candidates")
            
            if not candidates:
                self.logger.warning("  No tests generated, skipping")
                return results
            
            # Step 3-5: Process, inject, and execute tests
            self.logger.info("Step 3: Processing and injecting tests...")
            
            # Use temporary directory for checkouts
            if work_dir is None:
                work_dir = Path(tempfile.mkdtemp(prefix=f"libro_{bug_id}_"))
            
            # Checkout buggy version for processing
            checkout_dir = work_dir / f"{bug_info['project']}_{bug_info['bug_id']}_buggy"
            checkout_result = self._checkout_bug(
                bug_info['project'], 
                bug_info['bug_id'], 
                'buggy',
                checkout_dir
            )
            
            if not checkout_result:
                self.logger.error("  Failed to checkout project")
                results["errors"].append("checkout_failed")
                return results
            
            # Process each generated test
            fib_tests = []
            
            for i, test_dict in enumerate(candidates):
                test_id = f"test_{i}"
                self.logger.info(f"  Processing test {i+1}/{len(candidates)}...")
                
                try:
                    # Find host class
                    host_result = self.test_processor.find_host_class(
                        test_dict['test_code'],
                        checkout_dir
                    )
                    
                    if not host_result:
                        self.logger.warning(f"    Could not find host class")
                        continue
                    
                    host_class, similarity = host_result
                    
                    # Inject test
                    injection_result = self.test_processor.inject_test(
                        test_code=test_dict['test_code'],
                        host_class_path=host_class,
                        project_path=checkout_dir,
                        test_id=test_id
                    )
                    
                    if not injection_result['success']:
                        self.logger.warning(f"    Injection failed: {injection_result['error']}")
                        continue
                    
                    results["injected_tests"].append({
                        "test_id": test_id,
                        "test_code": test_dict['test_code'],
                        "host_class": Path(host_class).name,
                        "similarity": similarity,
                        "modified_class": injection_result['modified_class_path']
                    })
                    
                    # Execute test on both versions
                    self.logger.info(f"    Executing test on both versions...")
                    
                    # Extract class and method name
                    test_class = self._extract_class_name(injection_result['modified_class_path'])
                    test_method = self._extract_method_name(test_dict['test_code'])
                    
                    if not test_class or not test_method:
                        self.logger.warning(f"    Could not extract test identifiers")
                        continue
                    
                    exec_result = self.test_executor.execute_on_both_versions(
                        project=bug_info['project'],
                        bug_id=bug_info['bug_id'],
                        test_class=test_class,
                        test_method=test_method,
                        work_dir=work_dir
                    )
                    
                    # Store execution results
                    test_dict['execution'] = exec_result
                    test_dict['test_id'] = test_id
                    test_dict['classification'] = self.test_executor.classify_test(
                        exec_result['buggy_result'],
                        exec_result['fixed_result']
                    )
                    
                    # Check if it's a FIB (Fails In Buggy)
                    if exec_result['buggy_result'].get('failed'):
                        test_dict['error_type'] = exec_result['buggy_result'].get('error_type')
                        test_dict['error_message'] = exec_result['buggy_result'].get('error_message')
                        fib_tests.append(test_dict)
                        
                        # Check if it's a BRT
                        if exec_result['is_brt']:
                            results["brt_tests"].append(test_dict)
                            self.logger.info(f"    ✓ BRT FOUND!")
                
                except Exception as e:
                    self.logger.error(f"    Error processing test {i}: {e}")
                    continue
            
            results["fib_tests"] = fib_tests
            self.logger.info(f"  FIB tests: {len(fib_tests)}")
            self.logger.info(f"  BRT tests: {len(results['brt_tests'])}")
            
            # Step 6: Rank and select
            if fib_tests:
                self.logger.info("Step 4: Ranking and selecting tests...")
                ranking = self.test_ranker.select_and_rank(fib_tests, bug_info)
                results["ranking"] = ranking
                self.logger.info(f"  Ranked tests: {len(ranking)}")
            
            # Compute metrics
            total_time = time.time() - start_time
            results["metrics"] = {
                "total_time": total_time,
                "num_generated": len(candidates),
                "num_injected": len(results["injected_tests"]),
                "num_fib": len(fib_tests),
                "num_brt": len(results["brt_tests"]),
                "has_brt": len(results["brt_tests"]) > 0
            }
            
            self.logger.info(f"Completed in {total_time:.1f}s")
        
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def _checkout_bug(self, project: str, bug_id: str, version: str, 
                     checkout_dir: Path) -> bool:
        """Checkout a bug version."""
        import subprocess
        
        version_suffix = 'b' if version == 'buggy' else 'f'
        
        result = subprocess.run(
            ['defects4j', 'checkout', '-p', project, '-v', f'{bug_id}{version_suffix}',
             '-w', str(checkout_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return result.returncode == 0
    
    def _extract_class_name(self, file_path: str) -> str:
        """Extract class name from file path."""
        # Get file name without .java
        file_name = Path(file_path).stem
        
        # Remove any suffix (like _test_0)
        class_name = re.sub(r'_test_\d+$', '', file_name)
        
        return class_name
    
    def _extract_method_name(self, test_code: str) -> str:
        """Extract method name from test code."""
        match = re.search(r'public\s+void\s+(test\w+)\s*\(', test_code)
        if match:
            return match.group(1)
        return None
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = self.config.get("logging.level")
        log_file = self.config.get("logging.file")
        
        # Create logs directory if needed
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

import re
