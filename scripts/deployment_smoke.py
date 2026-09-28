"""HTTP smoke checks. Set AXIA_SMOKE_ORIGIN to an explicitly chosen deployment."""
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

origin = os.environ.get("AXIA_SMOKE_ORIGIN", "").rstrip("/")
if not origin or urllib.parse.urlsplit(origin).scheme not in ("http", "https"):
    sys.exit("Set AXIA_SMOKE_ORIGIN to an explicit http(s) origin")
paths = ("/", "/about", "/our-mission", "/data-sources", "/disclaimer", "/robots.txt", "/sitemap.xml")
for path in paths:
    try:
        with urllib.request.urlopen(origin + path, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            body = response.read(1024 * 1024)
            if not body:
                raise RuntimeError("empty response")
            if path == "/robots.txt" and b"user-agent:" not in body.lower():
                raise RuntimeError("invalid robots response")
            if path == "/sitemap.xml" and b"<urlset" not in body:
                raise RuntimeError("invalid sitemap response")
        print(f"PASS {path}")
    except (urllib.error.URLError, RuntimeError) as exc:
        sys.exit(f"FAIL {path}: {exc}")
print("Public HTTP smoke checks passed; data-provider and browser parity are not covered.")
