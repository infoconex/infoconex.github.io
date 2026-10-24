#!/usr/bin/env python3
"""Check local SEO consistency without third-party packages or network access."""
import json
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://infoconex.github.io"
projects = json.loads((ROOT / "projects.json").read_text())
paths = ["/"] + [f"/projects/{p['url'].rstrip('/').split('/')[-1]}/" for p in projects]
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.canonical = []
        self.titles = 0
        self.descriptions = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs.get("href"))
        if tag == "title":
            self.titles += 1
        if tag == "meta" and attrs.get("name") == "description":
            self.descriptions += 1

def html_path(url):
    return ROOT / (url.lstrip("/") + "index.html" if url != "/" else "index.html")

for url in paths:
    file = html_path(url)
    assert file.is_file(), f"Missing page: {file}"
    parser = Extract()
    parser.feed(file.read_text())
    assert parser.canonical == [BASE + url], f"Canonical mismatch: {file}"
    assert parser.titles == 1 and parser.descriptions == 1, f"Missing metadata: {file}"
    for href in parser.links:
        if href.startswith("/") and not href.startswith("//") and not href.startswith("/#"):
            target = href.split("#", 1)[0].split("?", 1)[0]
            if target.endswith("/"):
                assert html_path(target).is_file(), f"Broken local link: {href} in {file}"
            elif target not in {"/sitemap.xml"}:
                assert (ROOT / target.lstrip("/")).is_file(), f"Broken local link: {href} in {file}"
home = Extract()
home.feed((ROOT / "index.html").read_text())
for url in paths[1:]:
    assert url in home.links, f"Homepage does not link to {url}"
tree = ET.parse(ROOT / "pages-sitemap.xml")
urls = [n.text for n in tree.findall(".//sm:loc", ns)]
assert set(urls) == {BASE + p for p in paths}, "Page sitemap differs from project pages"
index = ET.parse(ROOT / "sitemap.xml")
indexes = [n.text for n in index.findall(".//sm:loc", ns)]
assert BASE + "/pages-sitemap.xml" in indexes, "Missing local sitemap in sitemap index"
robots = (ROOT / "robots.txt").read_text()
assert f"Sitemap: {BASE}/sitemap.xml" in robots, "robots.txt missing sitemap"
print(f"SEO validation passed: {len(paths)} pages, {len(indexes)} sitemap index entries")
