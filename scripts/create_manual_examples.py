#!/usr/bin/env python3
"""
Create manually curated examples for few-shot prompting.
"""

import json
from pathlib import Path

def create_manual_examples():
    """Create high-quality manual examples."""
    
    examples = [
        {
            "project": "Lang",
            "bug_id": "1",
            "title": "NumberUtils.isNumber(String) should return false for blank strings",
            "description": """The method NumberUtils.isNumber(String) in Apache Commons Lang returns true for blank strings (e.g., " "). According to the documentation, it should return false for blank strings.""",
            "test": """public void testIsNumberBlank() {
    assertFalse(NumberUtils.isNumber(" "));
    assertFalse(NumberUtils.isNumber(""));
    assertFalse(NumberUtils.isNumber("   "));
}"""
        },
        {
            "project": "Math",
            "bug_id": "63",
            "title": "NaN in equals methods",
            "description": """In MathUtils, some "equals" methods will return true if both arguments are NaN. Unless I'm mistaken, this contradicts the IEEE standard.""",
            "test": """public void testEqualsNaN() {
    assertFalse(MathUtils.equals(Double.NaN, Double.NaN));
    assertFalse(MathUtils.equals(Float.NaN, Float.NaN));
}"""
        }
    ]
    
    # Save
    output_dir = Path("data/examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "manual_examples.json", 'w') as f:
        json.dump(examples, f, indent=2)
    
    print(f"✓ Created {len(examples)} manual examples")
    print(f"  Saved to: {output_dir / 'manual_examples.json'}")

if __name__ == "__main__":
    create_manual_examples()
