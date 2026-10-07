import argparse
import ast
import os
import sys

# standard python libs 
STD_LIB_MODULES = set(sys.builtin_module_names) | {
    "abc", "argparse", "ast", "asyncio", "base64", "collections", "contextlib",
    "csv", "datetime", "decimal", "functools", "glob", "hashlib", "http", "io",
    "json", "logging", "math", "os", "pathlib", "pickle", "random", "re", "shutil",
    "socket", "sqlite3", "string", "sys", "threading", "time", "typing", "unittest",
    "urllib", "uuid", "xml"
}

DOCKERFILE_TEMPLATE = """# 
FROM python:{python_version}-slim

# took /app so we dont mix it up with linux files
WORKDIR /app


COPY {requirements_file} .
RUN pip install --no-cache-dir -r {requirements_file}


COPY . .


CMD ["python", "{entry_point}"]
"""

def detect_imports_from_file(entry_file: str) -> set[str]:
    imports = set()
    with open(entry_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=entry_file)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                pkg = alias.name.split('.')[0]
                if pkg not in STD_LIB_MODULES:
                    imports.add(pkg)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                pkg = node.module.split('.')[0]
                if pkg not in STD_LIB_MODULES:
                    imports.add(pkg)
    return imports

def main():
    parser = argparse.ArgumentParser(description="generates a dockerfile based on ur python script.")
    parser.add_argument("--entry", required=True, help="path to ur entryfile(z. B. main.py)")
    parser.add_argument("--python-version", default="3.11", help="Python Version of ur project (Standard: 3.11)")
    
    args = parser.parse_args()
    entry_file = args.entry
    
    if not os.path.exists(entry_file):
        print(f"Error: File '{entry_file}' was not found!")
        sys.exit(1)

    project_dir = os.path.dirname(os.path.abspath(entry_file)) or "."
    requirements_path = os.path.join(project_dir, "requirements.txt")

    if not os.path.exists(requirements_path):
        print("Error: 'requirements.txt' not found. Analyzing imports in the file...")
        detected_packages = detect_imports_from_file(entry_file)
        
        if detected_packages:
            with open(requirements_path, "w", encoding="utf-8") as f:
                for pkg in sorted(detected_packages):
                    f.write(f"{pkg}\n")
            print(f"'requirements.txt' created with the following packages: {', '.join(detected_packages)}")
        else:
            with open(requirements_path, "w", encoding="utf-8") as f:
                f.write("")
            print("No external dependencies detected. Empty 'requirements.txt' created.")

    # 2. Dockerfile erstellen
    dockerfile_content = DOCKERFILE_TEMPLATE.format(
        python_version=args.python_version,
        requirements_file="requirements.txt",
        entry_point=os.path.basename(entry_file)
    )

    dockerfile_path = os.path.join(project_dir, "Dockerfile")
    with open(dockerfile_path, "w", encoding="utf-8") as f:
        f.write(dockerfile_content)

    print(f"Success! 'Dockerfile' was created in the folder '{project_dir}'.")

if __name__ == "__main__":
    main()