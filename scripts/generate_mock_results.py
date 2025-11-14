#!/usr/bin/env python3
"""
Generate mock results with realistic FIBs and BRTs for testing selection & ranking.

This simulates what would happen if dependency resolution worked properly.
"""

import json
import random
from pathlib import Path
from typing import Dict, List
import numpy as np

class MockResultGenerator:
    """Generate realistic mock results for LIBRO pipeline testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Realistic error types observed in Defects4J
        self.error_types = [
            "AssertionError",
            "NullPointerException", 
            "IllegalArgumentException",
            "IndexOutOfBoundsException",
            "NumberFormatException",
            "ClassCastException"
        ]
        
        # Common assertion failures
        self.assertion_messages = [
            "expected:<true> but was:<false>",
            "expected:<null> but was:<[value]>",
            "expected:<0> but was:<1>",
            "Arrays differ at element [0]",
            "expected not null",
        ]
    
    def generate_test_code(self, test_id: int, complexity: str = "simple") -> str:
        """Generate realistic test code."""
        if complexity == "simple":
            return f"""public void testGenerated{test_id}() {{
    String input = "test";
    assertFalse(StringUtils.isEmpty(input));
    assertEquals(4, input.length());
}}"""
        elif complexity == "medium":
            return f"""public void testGenerated{test_id}() {{
    NumberUtils utils = new NumberUtils();
    double result = utils.createNumber("2.0");
    assertNotNull(result);
    assertEquals(2.0, result, 0.001);
}}"""
        else:  # complex
            return f"""public void testGenerated{test_id}() {{
    List<String> items = Arrays.asList("a", "b", "c");
    Iterator<String> iter = items.iterator();
    assertTrue(iter.hasNext());
    assertEquals("a", iter.next());
    assertEquals("b", iter.next());
}}"""
    
    def generate_execution_result(self, is_brt: bool, is_fib: bool) -> Dict:
        """Generate realistic execution result."""
        
        if is_brt:
            # BRT: fails on buggy, passes on fixed
            return {
                "buggy_result": {
                    "compiled": True,
                    "passed": False,
                    "failed": True,
                    "error_type": random.choice(self.error_types),
                    "error_message": random.choice(self.assertion_messages),
                    "execution_time": random.uniform(0.01, 0.5)
                },
                "fixed_result": {
                    "compiled": True,
                    "passed": True,
                    "failed": False,
                    "error_type": None,
                    "error_message": None,
                    "execution_time": random.uniform(0.01, 0.5)
                },
                "is_brt": True
            }
        elif is_fib:
            # FIB: fails on buggy, also fails on fixed (not BRT)
            error_type = random.choice(self.error_types)
            error_msg = random.choice(self.assertion_messages)
            return {
                "buggy_result": {
                    "compiled": True,
                    "passed": False,
                    "failed": True,
                    "error_type": error_type,
                    "error_message": error_msg,
                    "execution_time": random.uniform(0.01, 0.5)
                },
                "fixed_result": {
                    "compiled": True,
                    "passed": False,
                    "failed": True,
                    "error_type": error_type,
                    "error_message": error_msg,
                    "execution_time": random.uniform(0.01, 0.5)
                },
                "is_brt": False
            }
        else:
            # Passing test (not interesting)
            return {
                "buggy_result": {
                    "compiled": True,
                    "passed": True,
                    "failed": False,
                    "error_type": None,
                    "error_message": None,
                    "execution_time": random.uniform(0.01, 0.5)
                },
                "fixed_result": {
                    "compiled": True,
                    "passed": True,
                    "failed": False,
                    "error_type": None,
                    "error_message": None,
                    "execution_time": random.uniform(0.01, 0.5)
                },
                "is_brt": False
            }
    
    def generate_bug_results(self, bug_id: str, num_tests: int = 20,
                            brt_probability: float = 0.15,
                            fib_probability: float = 0.25) -> Dict:
        """
        Generate results for a single bug.
        
        Args:
            bug_id: Bug identifier (e.g., "Lang-1")
            num_tests: Number of tests to generate
            brt_probability: Probability that a test is a BRT
            fib_probability: Probability that a test is a FIB (given not BRT)
            
        Returns:
            Dict with bug results including generated tests, FIBs, BRTs, ranking
        """
        project, bug_num = bug_id.split('-')
        
        generated_tests = []
        fib_tests = []
        brt_tests = []
        
        # Generate tests
        for i in range(num_tests):
            test_id = f"test_{i}"
            
            # Decide if this test is BRT, FIB, or passing
            rand = random.random()
            is_brt = rand < brt_probability
            is_fib = not is_brt and rand < (brt_probability + fib_probability)
            
            # Generate test code
            complexity = random.choice(["simple", "simple", "medium", "complex"])
            test_code = self.generate_test_code(i, complexity)
            
            # Generate execution results
            execution = self.generate_execution_result(is_brt, is_fib)
            
            test_dict = {
                "test_id": test_id,
                "test_code": test_code,
                "execution": execution,
                "classification": "BRT" if is_brt else ("FIB" if is_fib else "PASS"),
                "is_brt": is_brt
            }
            
            if is_brt or is_fib:
                test_dict["error_type"] = execution["buggy_result"]["error_type"]
                test_dict["error_message"] = execution["buggy_result"]["error_message"]
            
            generated_tests.append(test_dict)
            
            if is_brt:
                brt_tests.append(test_dict)
                fib_tests.append(test_dict)  # BRTs are also FIBs
            elif is_fib:
                fib_tests.append(test_dict)
        
        # Generate ranking (would come from TestRanker in real pipeline)
        ranking = self._generate_ranking(fib_tests)
        
        return {
            "bug_id": bug_id,
            "project": project,
            "bug_number": bug_num,
            "generated_tests": generated_tests,
            "injected_tests": [{"test_id": t["test_id"]} for t in generated_tests],
            "fib_tests": fib_tests,
            "brt_tests": brt_tests,
            "ranking": ranking,
            "metrics": {
                "num_generated": len(generated_tests),
                "num_injected": len(generated_tests),
                "num_fib": len(fib_tests),
                "num_brt": len(brt_tests),
                "has_brt": len(brt_tests) > 0,
                "total_time": random.uniform(60, 300)
            }
        }
    
    def _generate_ranking(self, fib_tests: List[Dict]) -> List[Dict]:
        """Generate realistic ranking for FIB tests."""
        if not fib_tests:
            return []
        
        # Group by error type (simulating output clustering)
        error_groups = {}
        for test in fib_tests:
            error_key = test["error_type"]
            if error_key not in error_groups:
                error_groups[error_key] = []
            error_groups[error_key].append(test)
        
        # Rank: larger groups first, BRTs tend to be in larger groups
        ranked = []
        for error_type, tests in sorted(error_groups.items(), 
                                       key=lambda x: -len(x[1])):
            # Within group, BRTs tend to come first
            brt_tests = [t for t in tests if t["is_brt"]]
            non_brt_tests = [t for t in tests if not t["is_brt"]]
            
            # Add with some randomness
            group_ranked = brt_tests + non_brt_tests
            random.shuffle(group_ranked)
            
            # But ensure at least one BRT is early if it exists
            if brt_tests and random.random() < 0.7:
                # Move a BRT to front of this group
                brt = random.choice(brt_tests)
                group_ranked.remove(brt)
                group_ranked.insert(0, brt)
            
            ranked.extend(group_ranked)
        
        # Add ranking scores
        for i, test in enumerate(ranked):
            test["rank"] = i + 1
            test["rank_score"] = 1.0 - (i / len(ranked))
        
        return ranked
    
    def generate_batch_results(self, num_bugs: int = 30,
                               tests_per_bug: int = 20,
                               reproduction_rate: float = 0.25) -> Dict[str, Dict]:
        """
        Generate results for multiple bugs.
        
        Args:
            num_bugs: Number of bugs to simulate
            tests_per_bug: Tests generated per bug
            reproduction_rate: Target proportion of bugs with BRTs
            
        Returns:
            Dict mapping bug_id to results
        """
        results = {}
        
        # Decide which bugs will have BRTs
        num_reproduced = int(num_bugs * reproduction_rate)
        bug_indices = list(range(num_bugs))
        random.shuffle(bug_indices)
        reproduced_indices = set(bug_indices[:num_reproduced])
        
        for i in range(num_bugs):
            bug_id = f"Lang-{i+1}"
            
            if i in reproduced_indices:
                # This bug will have BRTs
                brt_prob = random.uniform(0.10, 0.25)  # 10-25% of tests are BRTs
                fib_prob = random.uniform(0.15, 0.30)  # Additional FIBs
            else:
                # This bug will NOT have BRTs
                brt_prob = 0.0
                fib_prob = random.uniform(0.10, 0.25)  # Some FIBs but no BRTs
            
            results[bug_id] = self.generate_bug_results(
                bug_id=bug_id,
                num_tests=tests_per_bug,
                brt_probability=brt_prob,
                fib_probability=fib_prob
            )
        
        return results


def main():
    """Generate mock results and save to files."""
    
    print("=" * 80)
    print("GENERATING MOCK RESULTS FOR SELECTION & RANKING TESTING")
    print("=" * 80)
    
    generator = MockResultGenerator(seed=42)
    
    # Generate different scenarios
    scenarios = [
        {
            "name": "realistic",
            "num_bugs": 30,
            "tests_per_bug": 20,
            "reproduction_rate": 0.25,
            "description": "Realistic scenario (25% reproduction, n=20)"
        },
        {
            "name": "optimistic", 
            "num_bugs": 30,
            "tests_per_bug": 30,
            "reproduction_rate": 0.35,
            "description": "Optimistic scenario (35% reproduction, n=30)"
        },
        {
            "name": "small",
            "num_bugs": 10,
            "tests_per_bug": 15,
            "reproduction_rate": 0.20,
            "description": "Small sample (10 bugs, 20% reproduction)"
        }
    ]
    
    output_dir = Path("results/mock_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for scenario in scenarios:
        print(f"\n{'=' * 80}")
        print(f"Generating: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"{'=' * 80}")
        
        results = generator.generate_batch_results(
            num_bugs=scenario['num_bugs'],
            tests_per_bug=scenario['tests_per_bug'],
            reproduction_rate=scenario['reproduction_rate']
        )
        
        # Calculate statistics
        total_bugs = len(results)
        bugs_with_brt = sum(1 for r in results.values() if r['metrics']['has_brt'])
        total_tests = sum(r['metrics']['num_generated'] for r in results.values())
        total_fibs = sum(r['metrics']['num_fib'] for r in results.values())
        total_brts = sum(r['metrics']['num_brt'] for r in results.values())
        
        print(f"\n📊 Statistics:")
        print(f"  Total bugs: {total_bugs}")
        print(f"  Bugs reproduced: {bugs_with_brt} ({bugs_with_brt/total_bugs*100:.1f}%)")
        print(f"  Total tests generated: {total_tests}")
        print(f"  Total FIB tests: {total_fibs}")
        print(f"  Total BRT tests: {total_brts}")
        print(f"  Avg tests per bug: {total_tests/total_bugs:.1f}")
        print(f"  Avg BRTs per reproduced bug: {total_brts/bugs_with_brt:.1f}")
        
        # Save results
        output_file = output_dir / f"{scenario['name']}_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Saved to: {output_file}")
        
        # Show sample bug
        sample_bug = next(iter(results.values()))
        if sample_bug['metrics']['has_brt']:
            print(f"\n📝 Sample reproduced bug: {sample_bug['bug_id']}")
            print(f"  FIB tests: {sample_bug['metrics']['num_fib']}")
            print(f"  BRT tests: {sample_bug['metrics']['num_brt']}")
            print(f"  First BRT rank: {next((t['rank'] for t in sample_bug['ranking'] if t['is_brt']), 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✓ Mock results generated successfully!")
    print("=" * 80)
    
    print("\nUse these results to test:")
    print("  1. Selection and ranking algorithms")
    print("  2. Evaluation metrics (acc@k, wef)")  
    print("  3. Visualization generation")
    print("  4. Multi-model comparison")
    
    print(f"\nResults location: {output_dir}/")

if __name__ == "__main__":
    main()
