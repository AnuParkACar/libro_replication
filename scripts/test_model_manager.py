#!/usr/bin/env python3
"""Test model manager functionality."""

import sys
sys.path.append('src')

from model_manager import ModelManager

def main():
    # Test with smallest model first
    print("Testing model manager with DeepSeek-Coder-7B...")
    
    manager = ModelManager(
        model_key="deepseek-coder-7b",
        cache_dir="models/deepseek-coder-7b"
    )
    
    manager.load()
    
    # Print model info
    info = manager.get_info()
    print("\nModel Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test generation
    test_prompt = '''# Bug: NaN equals issue
public void test'''
    
    print("\nGenerating from prompt...")
    result = manager.generate(test_prompt, max_tokens=100)
    print("\nGenerated:")
    print(result)

if __name__ == "__main__":
    main()
