import os
import ast
from typing import List, Set

def generate_init_files(project_root: str = "src"):
    """Generate __init__.py files for all directories"""
    
    def find_exports(file_path: str) -> Set[str]:
        """Find exportable names from a Python file"""
        exports = set()
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    exports.add(node.name)
        except:
            pass
        return exports

    def create_init_content(directory: str, files: List[str]) -> str:
        """Create content for __init__.py"""
        exports = []
        relative_imports = []
        
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                module_name = file[:-3]
                file_exports = find_exports(os.path.join(directory, file))
                
                if file_exports:
                    relative_imports.append(f"from .{module_name} import {', '.join(file_exports)}")
                    exports.extend(file_exports)
        
        return "\n".join(relative_imports) + "\n\n__all__ = " + str(exports)

    for root, dirs, files in os.walk(project_root):
        # Create __init__.py in each directory
        init_path = os.path.join(root, "__init__.py")
        
        # Skip if __init__.py already exists
        if not os.path.exists(init_path):
            content = create_init_content(root, files)
            with open(init_path, 'w') as f:
                f.write(content)
            print(f"Created {init_path}")

if __name__ == "__main__":
    generate_init_files()