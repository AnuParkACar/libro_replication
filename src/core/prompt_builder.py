"""Prompt construction for LLM queries."""

from typing import List, Dict, Optional
from pathlib import Path
import json
import random

class PromptBuilder:
    """Builds prompts for bug reproduction test generation."""
    
    def __init__(self, num_examples: int = 2, examples_file: str = None):
        """
        Initialize prompt builder.
        
        Args:
            num_examples: Number of few-shot examples to include
            examples_file: Path to examples JSON file
        """
        self.num_examples = num_examples
        self.examples = []
        
        if examples_file:
            self.load_examples(examples_file)
    
    def load_examples(self, examples_file: str):
        """Load few-shot examples from file."""
        examples_path = Path(examples_file)
        
        if not examples_path.exists():
            print(f"Warning: Examples file not found: {examples_file}")
            return
        
        with open(examples_path) as f:
            self.examples = json.load(f)
        
        print(f"Loaded {len(self.examples)} examples from {examples_file}")
    
    def select_examples(self, current_project: str = None, 
                       selection_method: str = "fixed") -> List[Dict]:
        """
        Select examples for the prompt.
        
        Args:
            current_project: Current project name (for same-project selection)
            selection_method: "fixed", "same_project", or "random"
            
        Returns:
            List of selected examples
        """
        if not self.examples or self.num_examples == 0:
            return []
        
        if selection_method == "same_project" and current_project:
            # Try to get examples from same project
            project_examples = [e for e in self.examples 
                              if e.get('project') == current_project]
            if len(project_examples) >= self.num_examples:
                return project_examples[:self.num_examples]
        
        if selection_method == "random":
            return random.sample(self.examples, 
                               min(self.num_examples, len(self.examples)))
        
        # Default: fixed (first N examples)
        return self.examples[:self.num_examples]
    
    def construct_prompt(self, bug_report: Dict[str, str], 
                        include_stack_trace: bool = False,
                        include_constructor: bool = False,
                        current_project: str = None) -> str:
        """
        Construct prompt from bug report.
        
        Args:
            bug_report: Dict with keys: title, description, stack_trace (optional)
            include_stack_trace: Whether to include stack trace
            include_constructor: Whether to include constructor info (unused for now)
            current_project: Project name for example selection
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # Add few-shot examples if configured
        selected_examples = self.select_examples(current_project)
        
        for example in selected_examples:
            prompt_parts.append(self._format_example(example))
            prompt_parts.append("")  # Blank line between examples
        
        # Add separator if we had examples
        if selected_examples:
            prompt_parts.append("---")
            prompt_parts.append("")
        
        # Add current bug report
        prompt_parts.append(f"# {bug_report['title']}")
        prompt_parts.append("## Description")
        prompt_parts.append(bug_report['description'])
        
        # Add stack trace if available and requested
        if include_stack_trace and 'stack_trace' in bug_report:
            prompt_parts.append("")
            prompt_parts.append("## Stack Trace")
            prompt_parts.append("```")
            prompt_parts.append(bug_report['stack_trace'])
            prompt_parts.append("```")
        
        # Add reproduction request
        prompt_parts.append("")
        prompt_parts.append("## Reproduction")
        prompt_parts.append(">Provide a self-contained example that reproduces this issue.")
        prompt_parts.append("```java")
        prompt_parts.append("public void test")
        
        return "\n".join(prompt_parts)
    
    def _format_example(self, example: Dict[str, str]) -> str:
        """Format a single example for the prompt."""
        parts = [
            f"# {example['title']}",
            "## Description",
            example['description'],
            "",
            "## Reproduction",
            ">Provide a self-contained example that reproduces this issue.",
            "```java",
            example['test'],
            "```"
        ]
        return "\n".join(parts)
    
    def get_prompt_stats(self, prompt: str) -> Dict[str, int]:
        """Get statistics about the prompt."""
        return {
            "total_length": len(prompt),
            "num_lines": len(prompt.split('\n')),
            "num_examples": self.num_examples,
            "approx_tokens": len(prompt.split())  # Rough approximation
        }
