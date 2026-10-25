#!/usr/bin/env python3
"""Regenerate static, crawlable project content from projects.json.

Usage: python scripts/build_projects.py
Requires only Python's standard library.
"""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://infoconex.github.io"
projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
assert isinstance(projects, list) and projects
assert all(isinstance(p.get("order"), int) and p.get("name") and p.get("description") and p.get("category") for p in projects)
projects.sort(key=lambda p: (p["order"], p["name"].casefold()))
slugs = [urlparse(p["url"]).path.rstrip("/").split("/")[-1] for p in projects]
assert len(set(slugs)) == len(slugs), "Duplicate repository slugs"
assert all(re.fullmatch(r"[a-zA-Z0-9._-]+", s) for s in slugs), "Invalid repository slug"
assert all(urlparse(p["url"]).netloc == "github.com" for p in projects)

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")

def e(value):
    return html.escape(value, quote=True)

homepage = ROOT / "index.html"
source = homepage.read_text(encoding="utf-8")
cards = "\n          ".join(
    f'<a class="project-card" data-order="{p["order"]}" href="/projects/{slug}/">'
    f'<div class="card-top"><span class="card-tag">{e(p["category"])}</span>'
    f'<span class="card-arrow" aria-hidden="true">↗</span></div>'
    f'<h3>{e(p["name"])}</h3><p>{e(p["description"])}</p></a>'
    for p, slug in zip(projects, slugs)
)
source, n = re.subn(
    r'(?<=<div id="project-grid" class="project-grid">)[\s\S]*?(?=\n        </div><p id="no-results")',
    "\n          " + cards,
    source,
    count=1,
)
assert n == 1, "Could not locate homepage project grid"
site_schema = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebSite", "name": "infoconex", "url": BASE + "/"},
        {"@type": "CollectionPage", "name": "infoconex open-source projects", "url": BASE + "/",
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/projects/{slug}/", "name": p["name"]}
             for i, (p, slug) in enumerate(zip(projects, slugs))
         ]}},
    ],
}
source, n = re.subn(
    r'(<script type="application/ld\+json">)[\s\S]*?(</script>)',
    lambda m: m[1] + json.dumps(site_schema, ensure_ascii=False).replace("<", "\\u003c") + m[2],
    source, count=1,
)
assert n == 1, "Could not locate homepage structured data"
write(homepage, source)

ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
root = ET.Element("urlset", xmlns=ns)
for path in ["/"] + [f"/projects/{slug}/" for slug in slugs]:
    ET.SubElement(ET.SubElement(root, "url"), "loc").text = BASE + path
ET.indent(root, space="  ")
write(ROOT / "pages-sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n")

for project, slug in zip(projects, slugs):
    name, desc, category, github = (project[key] for key in ("name", "description", "category", "url"))
    canonical = f"{BASE}/projects/{slug}/"
    docs = project.get("website")
    if docs:
        assert urlparse(docs).scheme == "https" and urlparse(docs).netloc, "Invalid website URL"
    schema = {"@context": "https://schema.org", "@type": "WebPage", "name": name,
              "description": desc, "url": canonical,
              "isPartOf": {"@type": "WebSite", "name": "infoconex", "url": BASE + "/"},
              "about": {"@type": "SoftwareSourceCode", "name": name, "description": desc, "codeRepository": github}}
    extra = f'<a class="primary-link secondary-link" href="{e(docs)}">Read published documentation ↗</a>' if docs else ""
    content = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#252F3A"><meta name="description" content="{e(desc)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="infoconex"><meta property="og:title" content="{e(name)} | infoconex"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{e(name)} | infoconex"><meta name="twitter:description" content="{e(desc)}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../../styles.css">
<title>{e(name)} | infoconex open-source projects</title><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")}</script>
</head><body>
<header class="site-header"><div class="container header-inner"><a class="brand" href="/"><span class="brand-mark">i<span>.</span></span> infoconex</a><nav aria-label="Main navigation"><a href="/#projects">All projects</a><a href="https://github.com/infoconex">GitHub ↗</a></nav></div></header>
<main class="container detail-page">
<p class="eyebrow">{e(category)}</p><h1>{e(name)}</h1><p class="intro">{e(desc)}</p>
<section aria-labelledby="explore-title"><h2 id="explore-title">Explore this project</h2><p>Explore the source code, project documentation, and implementation details.</p><div class="detail-links"><a class="primary-link" href="{e(github)}">View GitHub repository ↗</a>{extra}</div></section>
<p class="return-link"><a href="/#projects">← Back to all projects</a></p></main>
<footer class="site-footer"><div class="container footer-inner"><span>© infoconex</span><div><a href="https://github.com/infoconex">GitHub</a><a href="/sitemap.xml">Sitemap</a></div></div></footer>
</body></html>'''
    write(ROOT / "projects" / slug / "index.html", content)
print(f"Generated homepage, sitemap and {len(projects)} project pages.")
