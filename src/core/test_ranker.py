"""Test selection and ranking (Algorithm 2)."""

from typing import List, Dict
from collections import defaultdict
import re

class TestRanker:
    """Ranks and selects generated tests."""
    
    def __init__(self, agreement_threshold: int = 1):
        """
        Initialize ranker.
        
        Args:
            agreement_threshold: Minimum cluster size to show results (T_hr)
        """
        self.agreement_threshold = agreement_threshold
    
    def select_and_rank(self, fib_tests: List[Dict], 
                       bug_report: Dict[str, str]) -> List[Dict]:
        """
        Select and rank FIB tests (Algorithm 2).
        
        Args:
            fib_tests: List of tests that Failed In Buggy version
            bug_report: Original bug report dict
            
        Returns:
            Ordered list of selected tests (empty if below threshold)
        """
        # Cluster by failure output (Line 6)
        clusters = self._cluster_by_failure_output(fib_tests)
        
        # Check agreement threshold (Lines 8-10)
        max_cluster_size = max(len(c) for c in clusters.values()) if clusters else 0
        
        if max_cluster_size <= self.agreement_threshold:
            return []  # Don't show results
        
        # Remove syntactic duplicates (Line 11)
        unique_tests = self._remove_syntactic_duplicates(fib_tests)
        
        # Calculate ranking features
        cluster_sizes = {key: len(tests) for key, tests in clusters.items()}
        report_matches = self._match_with_report(unique_tests, bug_report)
        token_counts = {t['test_id']: len(t['test_code'].split()) 
                       for t in unique_tests}
        
        # Sort clusters by ranking heuristics (Line 16)
        sorted_clusters = sorted(
            clusters.items(),
            key=lambda x: (
                report_matches.get(x[0], 0),  # Report match (highest priority)
                cluster_sizes[x[0]],           # Cluster size
                -min(token_counts.get(t['test_id'], 999) for t in x[1])  # Brevity
            ),
            reverse=True
        )
        
        # Sort tests within clusters (Line 18)
        for cluster_key, tests in sorted_clusters:
            tests.sort(
                key=lambda t: (
                    report_matches.get(cluster_key, 0),
                    -token_counts.get(t['test_id'], 999)
                ),
                reverse=True
            )
        
        # Round-robin selection (Lines 19-22)
        ranking = []
        max_size = max(len(tests) for _, tests in sorted_clusters)
        
        for i in range(max_size):
            for cluster_key, tests in sorted_clusters:
                if i < len(tests):
                    ranking.append(tests[i])
        
        return ranking
    
    def _cluster_by_failure_output(self, fib_tests: List[Dict]) -> Dict[str, List]:
        """Cluster tests by error type and message."""
        clusters = defaultdict(list)
        
        for test in fib_tests:
            # Create cluster key from error type + message
            error_type = test.get('error_type', 'Unknown')
            error_msg = test.get('error_message', '')
            
            # Normalize error message (remove line numbers, memory addresses)
            normalized_msg = re.sub(r'\d+', '', error_msg)
            normalized_msg = re.sub(r'0x[0-9a-fA-F]+', '', normalized_msg)
            normalized_msg = normalized_msg[:100]  # First 100 chars
            
            cluster_key = f"{error_type}::{normalized_msg}"
            clusters[cluster_key].append(test)
        
        return dict(clusters)
    
    def _remove_syntactic_duplicates(self, tests: List[Dict]) -> List[Dict]:
        """Remove tests with identical code (Line 11)."""
        seen = set()
        unique = []
        
        for test in tests:
            # Normalize code (remove whitespace/comments)
            normalized = re.sub(r'\s+', '', test['test_code'])
            normalized = re.sub(r'//.*', '', normalized)
            
            if normalized not in seen:
                seen.add(normalized)
                unique.append(test)
        
        return unique
    
    def _match_with_report(self, tests: List[Dict], 
                          bug_report: Dict[str, str]) -> Dict[str, int]:
        """Calculate report matching scores (Line 12)."""
        # Extract keywords from bug report
        report_text = bug_report.get('description', '')
        report_keywords = set(re.findall(r'\w+', report_text.lower()))
        
        matches = {}
        for test in tests:
            test_text = test.get('test_code', '')
            test_error = test.get('error_message', '')
            
            test_keywords = set(re.findall(r'\w+', (test_text + test_error).lower()))
            
            # Count overlapping keywords
            overlap = len(report_keywords & test_keywords)
            matches[test['test_id']] = overlap
        
        return matches
