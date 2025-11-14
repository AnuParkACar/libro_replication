"""Test post-processing: injection and dependency resolution."""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
import logging
import subprocess
import javalang

logger = logging.getLogger(__name__)

class TestProcessor:
    """Processes generated tests for execution."""
    
    def __init__(self, defects4j_path: str):
        """
        Initialize test processor.
        
        Args:
            defects4j_path: Path to Defects4J installation
        """
        self.defects4j_path = Path(defects4j_path)
        
        # Common imports that should be added
        self.common_imports = {
            'junit3': [
                'import junit.framework.TestCase;',
                'import junit.framework.Test;',
                'import junit.framework.TestSuite;'
            ],
            'junit4': [
                'import org.junit.Test;',
                'import org.junit.Before;',
                'import org.junit.After;',
                'import static org.junit.Assert.*;'
            ],
            'junit5': [
                'import org.junit.jupiter.api.Test;',
                'import static org.junit.jupiter.api.Assertions.*;'
            ]
        }
    
    def find_host_class(self, test_code: str, project_path: Path) -> Optional[Tuple[str, float]]:
        """
        Find best matching test class for injection (Algorithm 1 line 1).
        
        Args:
            test_code: Generated test method code
            project_path: Path to checked out project
            
        Returns:
            Tuple of (best_match_path, similarity_score) or None
        """
        logger.info("Finding host class for test injection...")
        
        # Extract tokens from test code
        test_tokens = self._tokenize(test_code)
        
        if not test_tokens:
            logger.warning("Could not extract tokens from test code")
            return None
        
        # Find all test files
        test_files = self._find_test_files(project_path)
        
        if not test_files:
            logger.warning("No test files found in project")
            return None
        
        logger.info(f"Found {len(test_files)} test files to compare")
        
        best_match = None
        best_score = 0.0
        
        for test_file in test_files:
            try:
                # Read and tokenize test class
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    class_content = f.read()
                
                class_tokens = self._tokenize(class_content)
                
                if not class_tokens:
                    continue
                
                # Calculate similarity: |intersection| / |test_tokens| (Equation 1)
                intersection = set(test_tokens) & set(class_tokens)
                score = len(intersection) / len(test_tokens)
                
                if score > best_score:
                    best_score = score
                    best_match = test_file
                    logger.debug(f"  New best match: {test_file.name} (score: {score:.3f})")
            
            except Exception as e:
                logger.debug(f"  Error processing {test_file}: {e}")
                continue
        
        if best_match:
            logger.info(f"Selected host class: {best_match.name} (similarity: {best_score:.3f})")
            return str(best_match), best_score
        else:
            logger.warning("Could not find suitable host class")
            return None
    
    def inject_test(self, test_code: str, host_class_path: str, 
                   project_path: Path, test_id: str = "test") -> Dict[str, any]:
        """
        Inject test into host class with dependency resolution.
        
        Args:
            test_code: Test method code to inject
            host_class_path: Path to host test class
            project_path: Path to project root
            test_id: Unique identifier for this test
            
        Returns:
            Dict with keys: success, modified_class_path, added_imports, error
        """
        logger.info(f"Injecting test into {Path(host_class_path).name}")
        
        try:
            # Read host class
            with open(host_class_path, 'r', encoding='utf-8', errors='ignore') as f:
                class_content = f.read()
            
            # Resolve dependencies (Algorithm 1 lines 2-10)
            needed_imports = self._resolve_dependencies(test_code, class_content, project_path)
            
            # Add imports
            modified_content = self._add_imports(class_content, needed_imports)
            
            # Inject test method (before final closing brace)
            modified_content = self._inject_method(modified_content, test_code)
            
            # Write modified class to temporary location
            modified_path = Path(host_class_path).parent / f"{Path(host_class_path).stem}_{test_id}.java"
            with open(modified_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            logger.info(f"  ✓ Test injected successfully to {modified_path.name}")
            
            return {
                "success": True,
                "modified_class_path": str(modified_path),
                "original_class_path": host_class_path,
                "added_imports": needed_imports,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"  ✗ Injection failed: {e}")
            return {
                "success": False,
                "modified_class_path": None,
                "original_class_path": host_class_path,
                "added_imports": [],
                "error": str(e)
            }
    
    def _find_test_files(self, project_path: Path) -> List[Path]:
        """Find all test files in project."""
        test_files = []
        
        # Common test directories
        test_dirs = [
            project_path / 'src' / 'test' / 'java',
            project_path / 'test',
            project_path / 'tests',
            project_path / 'src' / 'test'
        ]
        
        for test_dir in test_dirs:
            if test_dir.exists():
                # Find all *Test.java files
                test_files.extend(test_dir.rglob('*Test.java'))
                test_files.extend(test_dir.rglob('Test*.java'))
        
        # Remove duplicates
        test_files = list(set(test_files))
        
        return test_files
    
    def _tokenize(self, code: str) -> List[str]:
        """Simple tokenization: split on non-alphanumeric characters."""
        # Extract identifiers (method names, class names, variable names)
        tokens = re.findall(r'\b[a-zA-Z_]\w*\b', code)
        
        # Filter out keywords
        java_keywords = {
            'public', 'private', 'protected', 'static', 'final', 'void',
            'class', 'interface', 'extends', 'implements', 'return',
            'if', 'else', 'for', 'while', 'do', 'switch', 'case',
            'break', 'continue', 'new', 'this', 'super', 'null',
            'true', 'false', 'try', 'catch', 'finally', 'throw', 'throws'
        }
        
        tokens = [t for t in tokens if t.lower() not in java_keywords]
        
        return tokens
    
    def _resolve_dependencies(self, test_code: str, host_class: str, 
                             project_path: Path) -> List[str]:
        """
        Resolve imports needed for test (Algorithm 1 lines 2-10).
        
        Args:
            test_code: Generated test code
            host_class: Existing host class content
            project_path: Project root path
            
        Returns:
            List of import statements to add
        """
        needed_imports = []
        
        # Get existing imports from host class
        existing_imports = self._extract_imports(host_class)
        
        # Detect JUnit version and add appropriate imports
        junit_version = self._detect_junit_version(host_class)
        
        # Add assertion imports if needed
        if self._has_assertions(test_code):
            if junit_version == 'junit4':
                if 'import static org.junit.Assert.*' not in existing_imports:
                    needed_imports.append('import static org.junit.Assert.*;')
            elif junit_version == 'junit5':
                if 'import static org.junit.jupiter.api.Assertions.*' not in existing_imports:
                    needed_imports.append('import static org.junit.jupiter.api.Assertions.*;')
        
        # Add @Test annotation import if needed
        if '@Test' in test_code:
            if junit_version == 'junit4':
                if 'import org.junit.Test' not in existing_imports:
                    needed_imports.append('import org.junit.Test;')
            elif junit_version == 'junit5':
                if 'import org.junit.jupiter.api.Test' not in existing_imports:
                    needed_imports.append('import org.junit.jupiter.api.Test;')
        
        # Extract referenced classes from test code
        referenced_classes = self._extract_referenced_classes(test_code)
        
        # Find imports for referenced classes
        for class_name in referenced_classes:
            # Skip if already imported or in java.lang
            if any(class_name in imp for imp in existing_imports):
                continue
            
            if class_name in ['String', 'Integer', 'Double', 'Float', 'Boolean', 
                             'Long', 'Short', 'Byte', 'Character', 'Object',
                             'Math', 'System']:
                continue  # java.lang classes
            
            # Try to find the class in project
            import_stmt = self._find_class_import(class_name, project_path)
            if import_stmt and import_stmt not in existing_imports:
                needed_imports.append(import_stmt)
        
        return needed_imports
    
    def _extract_imports(self, class_content: str) -> List[str]:
        """Extract existing import statements from class."""
        imports = []
        for line in class_content.split('\n'):
            line = line.strip()
            if line.startswith('import ') and line.endswith(';'):
                imports.append(line)
        return imports
    
    def _detect_junit_version(self, class_content: str) -> str:
        """Detect which JUnit version is used."""
        if 'org.junit.jupiter' in class_content:
            return 'junit5'
        elif 'org.junit.Test' in class_content or 'org.junit.Assert' in class_content:
            return 'junit4'
        elif 'junit.framework' in class_content:
            return 'junit3'
        else:
            # Default to junit4 (most common in Defects4J)
            return 'junit4'
    
    def _has_assertions(self, test_code: str) -> bool:
        """Check if test code contains assertions."""
        assertion_patterns = [
            r'\bassert\w+\s*\(',
            r'\bfail\s*\(',
            r'\bexpect\w+\s*\('
        ]
        
        for pattern in assertion_patterns:
            if re.search(pattern, test_code, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_referenced_classes(self, test_code: str) -> List[str]:
        """Extract class names referenced in test code."""
        referenced = set()
        
        # Pattern 1: new ClassName()
        for match in re.finditer(r'\bnew\s+([A-Z]\w+)\s*\(', test_code):
            referenced.add(match.group(1))
        
        # Pattern 2: ClassName.method()
        for match in re.finditer(r'\b([A-Z]\w+)\.', test_code):
            referenced.add(match.group(1))
        
        # Pattern 3: Type variable declarations
        for match in re.finditer(r'\b([A-Z]\w+)\s+\w+\s*=', test_code):
            referenced.add(match.group(1))
        
        return list(referenced)
    
    def _find_class_import(self, class_name: str, project_path: Path) -> Optional[str]:
        """
        Find import statement for a class in the project.
        
        Uses heuristic: find most common import for this class name.
        """
        # Search in source files
        import_candidates = []
        
        for java_file in project_path.rglob('*.java'):
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for import statements with this class name
                pattern = rf'import\s+([\w.]+\.{class_name})\s*;'
                matches = re.findall(pattern, content)
                import_candidates.extend(matches)
            
            except Exception:
                continue
        
        if not import_candidates:
            return None
        
        # Return most common import
        from collections import Counter
        most_common = Counter(import_candidates).most_common(1)
        
        if most_common:
            return f'import {most_common[0][0]};'
        
        return None
    
    def _add_imports(self, class_content: str, imports: List[str]) -> str:
        """Add import statements to class."""
        if not imports:
            return class_content
        
        # Find where to insert imports (after package declaration)
        lines = class_content.split('\n')
        insert_idx = 0
        
        # Find package declaration
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                insert_idx = i + 1
                break
        
        # Find last existing import
        last_import_idx = insert_idx
        for i in range(insert_idx, len(lines)):
            if lines[i].strip().startswith('import '):
                last_import_idx = i + 1
            elif lines[i].strip() and not lines[i].strip().startswith('import '):
                break
        
        # Insert new imports
        import_block = '\n'.join(imports)
        lines.insert(last_import_idx, import_block)
        
        return '\n'.join(lines)
    
    def _inject_method(self, class_content: str, test_method: str) -> str:
        """Inject test method into class (before final closing brace)."""
        # Find the last closing brace of the class
        # This is tricky - we need to find the closing brace that matches the class opening
        
        lines = class_content.split('\n')
        
        # Find class declaration
        class_start = -1
        for i, line in enumerate(lines):
            if re.search(r'\bclass\s+\w+', line):
                class_start = i
                break
        
        if class_start == -1:
            raise ValueError("Could not find class declaration")
        
        # Count braces to find matching closing brace
        brace_count = 0
        class_end = -1
        
        for i in range(class_start, len(lines)):
            brace_count += lines[i].count('{')
            brace_count -= lines[i].count('}')
            
            if brace_count == 0 and i > class_start:
                class_end = i
                break
        
        if class_end == -1:
            raise ValueError("Could not find class closing brace")
        
        # Insert test method before closing brace
        # Add proper indentation
        indented_method = '\n'.join('    ' + line for line in test_method.split('\n'))
        
        lines.insert(class_end, '\n' + indented_method + '\n')
        
        return '\n'.join(lines)
