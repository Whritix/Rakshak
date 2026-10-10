import os
import re

dist_dir = 'frontend/dist'
network_calls = []

# Check for fetch, XMLHttpRequest, Leaflet tileLayer with external urls, etc.
patterns = [
    re.compile(r'fetch\([\'"]https?://'),
    re.compile(r'tileLayer\([\'"]https?://'),
    re.compile(r'src=[\'"]https?://'),
    re.compile(r'href=[\'"]https?://'),
]

for root, dirs, files in os.walk(dist_dir):
    for f in files:
        if f.endswith(('.html', '.js', '.css')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                for pat in patterns:
                    for m in pat.finditer(content):
                        network_calls.append((f, m.group()))

print(f"Network request calls to external endpoints: {len(network_calls)}")
for f, call in network_calls:
    print(f"  {f}: {call}")
