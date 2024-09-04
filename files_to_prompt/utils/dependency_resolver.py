import ast
import os


def extract_imports(file_path):
    """
    Extracts import statements from a given Python file.
    Returns a list of modules that are imported.
    """
    with open(file_path, "r") as file:
        tree = ast.parse(file.read(), filename=file_path)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            # Handle relative imports (from . import something)
            module = node.module if node.module else ""
            imports.append(module)

    return imports


def resolve_import(module_name, project_root):
    """
    Given a module name, resolve it to a file path within the project.
    Handles both absolute and relative imports.
    """
    module_path = module_name.replace(".", os.sep) + ".py"
    for root, dirs, files in os.walk(project_root):
        if os.path.exists(os.path.join(root, module_path)):
            return os.path.join(root, module_path)
    return None


def collect_dependencies(file_path, project_root, collected_files=None):
    """
    Recursively collect all the dependencies of a given Python file.
    """
    if collected_files is None:
        collected_files = set()

    if file_path in collected_files:
        return collected_files  # Avoid infinite recursion

    collected_files.add(file_path)

    imports = extract_imports(file_path)
    for module in imports:
        module_file = resolve_import(module, project_root)
        if module_file and os.path.exists(module_file):
            collect_dependencies(module_file, project_root, collected_files)

    return collected_files
