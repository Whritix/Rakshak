import os
import re

dist_dir = 'frontend/dist'
external_urls = []
url_pattern = re.compile(r'https?://[^\s\"\'<>]+')

for root, dirs, files in os.walk(dist_dir):
    for f in files:
        if f.endswith(('.html', '.js', '.css', '.json', '.svg')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                matches = url_pattern.findall(content)
                for m in matches:
                    # Allow SVG namespaces (e.g. www.w3.org/2000/svg) and local loopback
                    if any(allowed in m for allowed in ['127.0.0.1', 'localhost', '0.0.0.0', 'w3.org']):
                        continue
                    external_urls.append((f, m))

print(f"Total dist files scanned. External non-local URLs found: {len(external_urls)}")
for f, u in external_urls:
    print(f"  {f}: {u}")
