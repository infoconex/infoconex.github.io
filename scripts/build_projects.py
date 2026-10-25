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

def external_links_new_tab(markup):
    """Open off-site links separately without changing internal navigation."""
    def update(match):
        tag = match.group(0)
        href_match = re.search(r'\bhref="([^"]+)"', tag)
        if not href_match:
            return tag
        href = html.unescape(href_match.group(1))
        parsed = urlparse(href)
        if parsed.scheme not in ("https", "http") or parsed.hostname == "infoconex.github.io":
            return tag
        # Preserve the existing label and other attributes; normalize attributes.
        tag = re.sub(r'\s+target="[^"]*"', "", tag)
        tag = re.sub(r'\s+rel="[^"]*"', "", tag)
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'
    return re.sub(r'<a\b[^>]*>', update, markup)


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
write(homepage, external_links_new_tab(source))

ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
root = ET.Element("urlset", xmlns=ns)
# Only include lastmod when an explicitly maintained date is available.
# Never use a build timestamp or the shared catalog's Git modification time.
ET.SubElement(ET.SubElement(root, "url"), "loc").text = BASE + "/"
for project, slug in zip(projects, slugs):
    entry = ET.SubElement(root, "url")
    ET.SubElement(entry, "loc").text = f"{BASE}/projects/{slug}/"
    if project.get("lastmod"):
        ET.SubElement(entry, "lastmod").text = project["lastmod"]
ET.indent(root, space="  ")
write(ROOT / "pages-sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n")

project_by_slug = dict(zip(slugs, projects))

for project, slug in zip(projects, slugs):
    name, desc, category, github = (project[key] for key in ("name", "description", "category", "url"))
    canonical = f"{BASE}/projects/{slug}/"
    docs = project.get("website")
    if docs:
        assert urlparse(docs).scheme == "https" and urlparse(docs).netloc, "Invalid website URL"

    study = project.get("caseStudy", {})
    problem = study.get("problem", project.get("overview", desc))
    solution = study.get("solution", project.get("overview", desc))
    decisions = study.get("decisions", project.get("highlights", []))
    status = study.get("status", "Consult the repository for the latest implementation status.")
    audience = project.get("audience", "Developers interested in this project.")
    highlights = project.get("highlights", [])
    assert all(isinstance(item, str) for item in highlights + decisions)

    def links(primary_docs=False):
        source_link = f'<a class="case-btn case-primary" href="{e(github)}">View source code ↗</a>'
        docs_link = (f'<a class="case-btn case-outline" href="{e(docs)}">Read documentation ↗</a>' if docs else "")
        if primary_docs and docs:
            return (f'<a class="case-btn case-primary" href="{e(docs)}">Read documentation ↗</a>'
                    f'<a class="case-btn case-outline" href="{e(github)}">View source code ↗</a>')
        return source_link + docs_link

    def paragraphs(values):
        return "".join(f"<p>{e(value)}</p>" for value in values if value)

    problem_details = paragraphs(study.get("problemDetails", []))
    solution_details = paragraphs(study.get("solutionDetails", []))
    audience_details = paragraphs(study.get("audienceDetails", []))
    status_details = paragraphs(study.get("statusDetails", []))
    detailed_steps = study.get("workflowDetails", [])
    detailed_decisions = study.get("decisionDetails", [])
    capabilities = "".join(
        f'<div class="case-step"><span class="case-step-number">{i}</span><div><h3>{e(item)}</h3>{paragraphs(detailed_steps[i - 1]) if i <= len(detailed_steps) else ""}</div></div>'
        for i, item in enumerate(highlights, 1)
    )
    decision_items = "".join(f'<li><strong>{e(item)}</strong>{paragraphs(detailed_decisions[i]) if i < len(detailed_decisions) else str()}</li>' for i, item in enumerate(decisions))
    docs_aside = (f'<a href="{e(docs)}">Read documentation ↗</a>' if docs else "")
    related_items = project.get("related", [])
    article_items = project.get("articles", [])
    related_cards = "".join(
        f'<a class="case-resource-card" href="/projects/{e(item["slug"])}/"><h3>{e(project_by_slug[item["slug"]]["name"])} ↗</h3><span>{e(item["relationship"])}</span><p>{e(project_by_slug[item["slug"]]["description"])}</p></a>'
        for item in related_items
    )
    article_cards = "".join(
        f'<a class="case-resource-card" href="{e(item["url"])}"><h3>{e(item["title"])} ↗</h3><p>{e(item["description"])}</p></a>'
        for item in article_items
    )
    articles_section = (f'<section class="case-section" id="articles"><span class="case-kicker">07 / Deeper reading</span><h2>Related articles</h2><p>Engineering context and lessons behind this project.</p><div class="case-resource-grid">{article_cards}</div></section>') if article_cards else ""
    related_number = "08" if article_cards else "07"
    related_section = (f'<section class="case-section" id="related"><span class="case-kicker">{related_number} / Explore further</span><h2>Related projects</h2><p>Explore other projects and how they connect to this work.</p><div class="case-resource-grid">{related_cards}</div></section>') if related_cards else ""
    optional_toc = ('<a href="#articles">Related articles</a>' if article_cards else "") + ('<a href="#related">Related projects</a>' if related_cards else "")
    schema = {
        "@context": "https://schema.org", "@type": "WebPage",
        "name": name, "description": desc, "url": canonical,
        "isPartOf": {"@type": "WebSite", "name": "infoconex", "url": BASE + "/"},
        "about": {"@type": "SoftwareSourceCode", "name": name, "description": desc, "codeRepository": github}
    }
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
<main class="case-shell"><div class="container case-columns"><div class="case-main">
<section class="case-hero" aria-labelledby="project-title">
<p class="eyebrow">{e(category)}</p><h1 id="project-title">{e(name)}</h1><p class="case-lead">{e(desc)}</p>
<div class="case-ctas">{links()}</div>
</section>
<article>
<section class="case-section" id="problem"><span class="case-kicker">01 / Why</span><h2>The problem</h2><p>{e(problem)}</p>{problem_details}</section>
<section class="case-section" id="solution"><span class="case-kicker">02 / What</span><h2>The solution</h2><p>{e(solution)}</p>{solution_details}</section>
<section class="case-section" id="audience"><span class="case-kicker">03 / Who</span><h2>Who it's for</h2><p>{e(audience)}</p>{audience_details}</section>
<section class="case-section" id="workflow"><span class="case-kicker">04 / How</span><h2>How it works</h2><p>Key capabilities and concepts. See the project documentation or source code for implementation details.</p><div class="case-steps">{capabilities}</div></section>
<section class="case-section" id="decisions"><span class="case-kicker">05 / Engineering perspective</span><h2>Design decisions that matter</h2><ul class="case-bullets">{decision_items}</ul></section>
<section class="case-section" id="status"><span class="case-kicker">06 / Current state</span><h2>Explore the implementation</h2><p>{e(status)}</p>{status_details}<div class="case-related"><h3>Go deeper</h3><p>Use the project links to explore the source and available documentation.</p><div class="case-ctas">{links(primary_docs=True)}</div></div></section>
{articles_section}
{related_section}
</article></div>
<aside class="case-aside" aria-label="On this page"><h2>On this page</h2>
<nav class="case-toc" aria-label="Project sections"><a href="#problem">The problem</a><a href="#solution">The solution</a><a href="#audience">Who it's for</a><a href="#workflow">How it works</a><a href="#decisions">Design decisions</a><a href="#status">Current state</a>{optional_toc}</nav>
<div class="case-rule"></div><div class="case-aside-links"><a href="{e(github)}">View source code ↗</a>{docs_aside}</div>
<div class="case-rule"></div><nav class="case-aside-links" aria-label="Site navigation"><a href="/#projects">All projects</a><a href="https://github.com/infoconex">GitHub ↗</a></nav>
</aside></div></main>
<footer class="site-footer"><div class="container footer-inner"><span>© infoconex</span><nav aria-label="Footer navigation"><a href="/#projects">All projects</a><a href="https://github.com/infoconex">GitHub ↗</a></nav></div></footer>
</body></html>'''
    write(ROOT / "projects" / slug / "index.html", external_links_new_tab(content))
print(f"Generated homepage, sitemap and {len(projects)} project pages.")
