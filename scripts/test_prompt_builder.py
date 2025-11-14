#!/usr/bin/env python3
"""Test prompt builder with different configurations."""

import sys
sys.path.append('.')

from src.core.prompt_builder import PromptBuilder
import json

def test_no_examples():
    """Test prompt without examples."""
    print("=" * 80)
    print("TEST 1: No Examples")
    print("=" * 80)
    
    builder = PromptBuilder(num_examples=0)
    
    bug_report = {
        "title": "NaN in equals methods",
        "description": """In MathUtils, some "equals" methods will return true if both arguments are NaN. This contradicts the IEEE standard."""
    }
    
    prompt = builder.construct_prompt(bug_report)
    print(prompt)
    print("\nStats:", builder.get_prompt_stats(prompt))

def test_with_manual_examples():
    """Test prompt with manual examples."""
    print("\n" + "=" * 80)
    print("TEST 2: With Manual Examples")
    print("=" * 80)
    
    builder = PromptBuilder(
        num_examples=2,
        examples_file="data/examples/manual_examples.json"
    )
    
    bug_report = {
        "title": "Bug in string parsing",
        "description": """The parseString method fails to handle escaped quotes correctly."""
    }
    
    prompt = builder.construct_prompt(bug_report)
    print(prompt)
    print("\nStats:", builder.get_prompt_stats(prompt))

def test_with_stack_trace():
    """Test prompt with stack trace."""
    print("\n" + "=" * 80)
    print("TEST 3: With Stack Trace")
    print("=" * 80)
    
    builder = PromptBuilder(num_examples=1, 
                           examples_file="data/examples/manual_examples.json")
    
    bug_report = {
        "title": "NullPointerException in parser",
        "description": "Parser crashes when input is null.",
        "stack_trace": """java.lang.NullPointerException
    at com.example.Parser.parse(Parser.java:42)
    at com.example.Main.main(Main.java:10)"""
    }
    
    prompt = builder.construct_prompt(bug_report, include_stack_trace=True)
    print(prompt)
    print("\nStats:", builder.get_prompt_stats(prompt))

def main():
    test_no_examples()
    test_with_manual_examples()
    test_with_stack_trace()
    
    print("\n" + "=" * 80)
    print("✓ All prompt builder tests completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
