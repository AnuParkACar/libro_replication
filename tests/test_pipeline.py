"""Unit tests for pipeline components."""

import unittest
from src.core.prompt_builder import PromptBuilder

class TestPromptBuilder(unittest.TestCase):
    """Test prompt construction."""
    
    def setUp(self):
        self.builder = PromptBuilder(num_examples=0)
    
    def test_basic_prompt(self):
        """Test basic prompt construction."""
        bug_report = {
            "title": "NaN equals bug",
            "description": "MathUtils.equals returns true for NaN"
        }
        
        prompt = self.builder.construct_prompt(bug_report)
        
        self.assertIn("NaN equals bug", prompt)
        self.assertIn("public void test", prompt)
        self.assertIn("```java", prompt)
    
    def test_prompt_with_stack_trace(self):
        """Test prompt with stack trace."""
        bug_report = {
            "title": "NPE in parser",
            "description": "Parser throws NPE",
            "stack_trace": "NullPointerException at line 42"
        }
        
        prompt = self.builder.construct_prompt(bug_report, include_stack_trace=True)
        
        self.assertIn("Stack Trace", prompt)
        self.assertIn("NullPointerException", prompt)

if __name__ == '__main__':
    unittest.main()
