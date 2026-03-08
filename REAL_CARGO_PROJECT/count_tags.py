import os
import re

template_dir = r'c:\Users\anyan\Documents\GitHub\Real_CargoFind\REAL_CARGO_PROJECT\templates'

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                blocks = len(re.findall(r'\{%\s*block', content))
                endblocks = len(re.findall(r'\{%\s*endblock', content))
                if blocks != endblocks:
                    print(f"UNBALANCED in {path}: blocks={blocks}, endblocks={endblocks}")
                else:
                    # Check for nested blocks with same name or other issues
                    pass
print("Done checking.")
