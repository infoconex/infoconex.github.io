#!/usr/bin/env python3
"""Submit affected published project URLs to IndexNow after deployment."""
import argparse
import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

SITE = "https://projects.infoconex.com"
KEY = "dee2976b885148979d86df8b593b649e"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    with urllib.request.urlopen(SITE + "/sitemap.xml", timeout=30) as response:
        root = ET.fromstring(response.read())
    return {element.text.strip() for element in root.findall(".//{*}loc")
            if element.text and urlparse(element.text.strip()).netloc == urlparse(SITE).netloc}


def changed_urls(base, head, published):
    if not base or set(base) == {"0"}:
        return published
    result = subprocess.run(["git", "diff", "--name-only", base, head],
                            text=True, capture_output=True, check=True)
    paths = set(result.stdout.splitlines())
    if not paths:
        return set()
    # Generated pages and the catalog are interdependent. Small sitemap: prefer
    # a full refresh for any change that may affect generated HTML or page links.
    global_sources = {"projects.json", "index.html", "sitemap.xml",
                      "styles.css", "script.js", "project-scrollspy.js"}
    if paths & global_sources or any(path.startswith(("scripts/build_", "assets/", "projects/"))
                                     for path in paths):
        return published
    return set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    published = sitemap_urls()
    urls = published if args.all else changed_urls(
        os.environ.get("BASE_SHA", ""), os.environ.get("HEAD_SHA", "HEAD"), published)
    if not urls:
        print("IndexNow: no changed published pages to submit.")
        return
    payload = json.dumps({
        "host": urlparse(SITE).netloc,
        "key": KEY,
        "keyLocation": SITE + "/" + KEY + ".txt",
        "urlList": sorted(urls),
    }).encode("utf-8")
    request = urllib.request.Request(ENDPOINT, data=payload, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status not in (200, 202):
            raise RuntimeError("Unexpected IndexNow status: " + str(response.status))
        print(f"IndexNow: submitted {len(urls)} URLs, HTTP {response.status}.")


if __name__ == "__main__":
    main()
