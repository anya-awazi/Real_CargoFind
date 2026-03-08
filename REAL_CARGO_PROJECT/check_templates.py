import jinja2
import os

template_dir = r'c:\Users\anyan\Documents\GitHub\Real_CargoFind\REAL_CARGO_PROJECT\templates'
loader = jinja2.FileSystemLoader(template_dir)
env = jinja2.Environment(loader=loader)

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            rel_path = os.path.relpath(os.path.join(root, file), template_dir).replace('\\', '/')
            try:
                source = env.loader.get_source(env, rel_path)[0]
                env.parse(source)
                print(f"OK: {rel_path}")
            except jinja2.TemplateSyntaxError as e:
                print(f"ERROR in {rel_path}: {e}")
            except Exception as e:
                import traceback
                print(f"OTHER ERROR in {rel_path}: {e}")
                traceback.print_exc()
