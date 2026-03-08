import jinja2
import os

template_dir = r'c:\Users\anyan\Documents\GitHub\Real_CargoFind\REAL_CARGO_PROJECT\templates'
loader = jinja2.FileSystemLoader(template_dir)
env = jinja2.Environment(loader=loader)

print(f"Checking templates in {template_dir}...")

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            # Convert absolute path to relative path for Jinja loader
            rel_path = os.path.relpath(os.path.join(root, file), template_dir).replace('\\', '/')
            try:
                env.get_template(rel_path)
                print(f"OK: {rel_path}")
            except jinja2.TemplateSyntaxError as e:
                print(f"SYNTAX ERROR in {rel_path}: {e}")
                print(f"  Line: {e.lineno}")
                print(f"  Message: {e.message}")
            except Exception as e:
                print(f"LOAD ERROR in {rel_path}: {e}")

print("Done.")
