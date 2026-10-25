#!/usr/bin/env python3
"""Check local SEO consistency without third-party packages or network access."""
import json
import re
from datetime import date
from urllib.parse import urlparse
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://infoconex.github.io"
projects = json.loads((ROOT / "projects.json").read_text())
paths = ["/"] + [f"/projects/{p['url'].rstrip('/').split('/')[-1]}/" for p in projects]
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

slugs = {p["url"].rstrip("/").split("/")[-1] for p in projects}
assert len(slugs) == len(projects), "Duplicate project slugs"
for project in projects:
    slug = project["url"].rstrip("/").split("/")[-1]
    seen = set()
    for item in project.get("related", []):
        target = item["slug"]
        assert target in slugs and target != slug, f"Invalid related project: {slug} -> {target}"
        assert target not in seen, f"Duplicate related project: {slug} -> {target}"
        assert isinstance(item.get("relationship"), str) and item["relationship"].strip(), f"Missing relationship: {slug}"
        seen.add(target)
    urls = set()
    for item in project.get("articles", []):
        parsed = urlparse(item["url"])
        assert parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password, f"Invalid article URL for {slug}"
        assert all(isinstance(item.get(key), str) and item[key].strip() for key in ("title", "description")), f"Incomplete article for {slug}"
        assert item["url"] not in urls, f"Duplicate article for {slug}"
        urls.add(item["url"])

for project in projects:
    source = project.get("socialSource")
    if source:
        parsed = urlparse(source)
        assert parsed.scheme == "https" and parsed.hostname == "raw.githubusercontent.com", "Social source must be a raw GitHub HTTPS URL"
        assert parsed.path.startswith("/infoconex/") and parsed.path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")), "Unapproved social source URL"

# Optional lastmod values must be real ISO dates and must not be future-dated.
for project in projects:
    if "lastmod" in project:
        value = project["lastmod"]
        assert isinstance(value, str) and len(value) == 10, "lastmod must be YYYY-MM-DD"
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError as exc:
            raise AssertionError(f"Invalid lastmod date: {value}") from exc
        assert parsed_date <= date.today(), f"Future lastmod date: {value}"

# Editorial checks are deliberately generous: Google has no fixed character limits.
titles = [p["name"] + " | infoconex" for p in projects]
descriptions = [p.get("seoDescription", "") for p in projects]
assert len(set(titles)) == len(titles), "Duplicate page titles"
assert len(set(descriptions)) == len(descriptions), "Duplicate SEO descriptions"
for p, title, desc in zip(projects, titles, descriptions):
    assert 15 <= len(title) <= 70, f"Review SEO title: {p['name']}"
    assert 70 <= len(desc) <= 170, f"Review SEO description: {p['name']}"
    assert desc.strip() == desc, f"SEO description whitespace: {p['name']}"

class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.anchor_fragments = []
        self.canonical = []
        self.titles = 0
        self.descriptions = 0
        self.title_text = ""
        self.meta = {}
        self.scripts = []
        self._in_title = False
        self._in_jsonld = False
        self._jsonld = ""
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            assert attrs["id"] not in self.ids, f"Duplicate HTML id: {attrs['id']}"
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if attrs["href"].startswith("#"):
                self.anchor_fragments.append(attrs["href"][1:])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs.get("href"))
        if tag == "title":
            self.titles += 1
            self._in_title = True
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._jsonld = ""
        if tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.meta[key] = attrs.get("content", "")
        if tag == "meta" and attrs.get("name") == "description":
            self.descriptions += 1

    def handle_data(self, data):
        if self._in_title:
            self.title_text += data
        if self._in_jsonld:
            self._jsonld += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_jsonld:
            self.scripts.append(json.loads(self._jsonld))
            self._in_jsonld = False

def html_path(url):
    return ROOT / (url.lstrip("/") + "index.html" if url != "/" else "index.html")

for url in paths:
    file = html_path(url)
    assert file.is_file(), f"Missing page: {file}"
    parser = Extract()
    parser.feed(file.read_text())
    assert file.read_text().count('https://www.clarity.ms/tag/') == 1, f"Clarity must appear exactly once: {file}"
    assert parser.canonical == [BASE + url], f"Canonical mismatch: {file}"
    assert parser.titles == 1 and parser.descriptions == 1, f"Missing metadata: {file}"
    if url != "/":
        slug = url.rstrip("/").split("/")[-1]
        project = next(p for p in projects if p["url"].endswith("/" + slug))
        title = project["name"] + " | infoconex"
        description = project["seoDescription"]
        share = BASE + "/assets/social/" + slug + ".png"
        assert parser.title_text == title, f"SEO title mismatch: {file}"
        for key in ("description", "og:description", "twitter:description"):
            assert parser.meta.get(key) == description, f"{key} mismatch: {file}"
        assert parser.meta.get("og:title") == title and parser.meta.get("twitter:title") == title
        assert parser.meta.get("og:image") == share and parser.meta.get("twitter:image") == share
        assert (ROOT / "assets" / "social" / (slug + ".png")).is_file(), f"Missing share image for {slug}"
        graphs = [node for document in parser.scripts for node in document.get("@graph", [document])]
        assert any(node.get("@type") == "BreadcrumbList" for node in graphs), f"Missing breadcrumbs: {file}"
        assert any(node.get("@type") == "WebPage" for node in graphs), f"Missing WebPage schema: {file}"
    if url != "/":
        markup = file.read_text(encoding="utf-8")
        assert 'class="case-hero"' in markup and 'class="case-side-actions"' in markup, f"Missing modern project layout: {file}"
        assert markup.count('View source code ↗') == 1, f"Duplicate source action: {file}"
        slug = url.rstrip("/").split("/")[-1]
        project = next(p for p in projects if p["url"].endswith("/" + slug))
        expected_docs = 1 if project.get("website") else 0
        assert markup.count('class="case-side-action case-outline"') == expected_docs, f"Incorrect documentation action: {file}"
        assert 'src="../../project-scrollspy.js"' in markup, f"Missing section tracker: {file}"
        assert ('id="articles"' in markup) == bool(project.get("articles")), f"Article section mismatch: {file}"
        assert ('id="related"' in markup) == bool(project.get("related")), f"Related section mismatch: {file}"
    for fragment in parser.anchor_fragments:
        assert fragment in parser.ids, f"Broken anchor #{fragment} in {file}"
    for href in parser.links:
        if href.startswith("/") and not href.startswith("//") and not href.startswith("/#"):
            target = href.split("#", 1)[0].split("?", 1)[0]
            if target.endswith("/"):
                assert html_path(target).is_file(), f"Broken local link: {href} in {file}"
            elif target not in {"/sitemap.xml"}:
                assert (ROOT / target.lstrip("/")).is_file(), f"Broken local link: {href} in {file}"
assert (ROOT / "assets/social/home.png").is_file(), "Missing homepage social image"
assert (ROOT / "project-scrollspy.js").is_file(), "Missing production section tracker"
home = Extract()
home.feed((ROOT / "index.html").read_text())
for url in paths[1:]:
    assert url in home.links, f"Homepage does not link to {url}"
tree = ET.parse(ROOT / "pages-sitemap.xml")
urls = [n.text for n in tree.findall(".//sm:loc", ns)]
assert set(urls) == {BASE + p for p in paths}, "Page sitemap differs from project pages"
for project in projects:
    slug = project["url"].rstrip("/").split("/")[-1]
    target = BASE + f"/projects/{slug}/"
    matches = [node for node in tree.findall(".//sm:url", ns) if node.findtext("sm:loc", namespaces=ns) == target]
    assert len(matches) == 1, f"Expected one sitemap entry for {slug}"
    lastmod = matches[0].findtext("sm:lastmod", namespaces=ns)
    assert lastmod == project.get("lastmod"), f"Incorrect lastmod for {slug}"
home_entry = [node for node in tree.findall(".//sm:url", ns) if node.findtext("sm:loc", namespaces=ns) == BASE + "/"]
assert len(home_entry) == 1 and home_entry[0].find("sm:lastmod", ns) is None, "Homepage must not have an unverified lastmod"

index = ET.parse(ROOT / "sitemap.xml")
indexes = [n.text for n in index.findall(".//sm:loc", ns)]
assert BASE + "/pages-sitemap.xml" in indexes, "Missing local sitemap in sitemap index"
robots = (ROOT / "robots.txt").read_text()
assert f"Sitemap: {BASE}/sitemap.xml" in robots, "robots.txt missing sitemap"
print(f"SEO validation passed: {len(paths)} pages, {len(indexes)} sitemap index entries")
