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
PROJECT_ICON_PATHS = {
    "coding-blog": "M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z",
    "isolated-dotnet-sdk": "m4 17 6-6-6-6 M12 19h8",
    "copy-github-repo": "M8 4H5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3 M9 9h10a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z",
    "ai-flywheel-spec": "M4 7h6 M14 7h6 M7 4v6 M17 4v6 M4 17h6 M14 17h6 M7 14v6 M17 14v6 M10 7l4 10",
    "ai-flywheel-framework": "M12 2 4 7v10l8 5 8-5V7l-8-5Z M4 7l8 5 8-5 M12 12v10",
    "ai-flywheel-cli": "M4 17 10 11 4 5 M12 19h8",
    "ai-flywheel-cli-python": "M8 8 4 12l4 4 M16 8l4 4-4 4 M14 4l-4 16",
    "ai-flywheel-framework-testing": "M9 3h6 M10 3v7l-5 8a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-8V3 M8 15h8",
    "nuget-publication-cooldown-poc": "M12 2 3 7v10l9 5 9-5V7l-9-5Z M3 7l9 5 9-5 M12 12v10 M8 16h3"
}
def project_icon(slug):
    path = PROJECT_ICON_PATHS.get(slug)
    return (f'<span class="project-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{e(path)}"/></svg></span>') if path else ""

cards = "\n          ".join(
    f'<a class="project-card" data-order="{p["order"]}" href="/projects/{slug}/">'
    f'<div class="card-top"><span class="card-identity">{project_icon(slug)}<span class="card-tag">{e(p["category"])}</span></span>'
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
    seo_description = project["seoDescription"]
    seo_title = f"{name} | infoconex"
    share_image = f"{BASE}/assets/social/{slug}.png"
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

    source_action = f'<a class="case-side-action case-primary" href="{e(github)}">View source code ↗</a>'
    documentation_action = (f'<a class="case-side-action case-outline" href="{e(docs)}">{"Visit publication" if slug == "coding-blog" else "Read documentation"} ↗</a>' if docs else "")
    actions = source_action + documentation_action
    kind = "Technical publication" if slug == "coding-blog" else ("Methodology / specification" if slug == "ai-flywheel-spec" else "Engineering project")
    tagline = {"isolated-dotnet-sdk": "Exact SDK versions. No system-wide changes.", "ai-flywheel-spec": "A loop repeats. A flywheel compounds.", "coding-blog": "Practical engineering, documented."}.get(slug, project.get("overview", desc))
    visual = "".join(f'<span>{e(line)}</span>' for line in project.get("highlights", [])[:3])
    platform_info = {"isolated-dotnet-sdk": [("Interfaces", "PowerShell · Bash"), ("Platforms", "Windows · Linux · macOS")], "copy-github-repo": [("Interface", "PowerShell")], "ai-flywheel-cli": [("Interface", ".NET CLI")], "ai-flywheel-cli-python": [("Interface", "Python CLI")]}.get(slug, [])
    detail_rows = "".join(f'<div class="case-detail"><dt>{e(key)}</dt><dd>{e(value)}</dd></div>' for key,value in [("Category",category)] + platform_info)

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
    optional_toc = ('<a href="#articles"><span class="case-toc-number">07</span>Related articles</a>' if article_cards else "") + (f'<a href="#related"><span class="case-toc-number">{related_number}</span>Related projects</a>' if related_cards else "")
    schema = {
        "@context": "https://schema.org", "@graph": [
            {"@type": "WebPage", "name": name, "description": seo_description, "url": canonical,
             "isPartOf": {"@type": "WebSite", "name": "infoconex", "url": BASE + "/"},
             "about": {"@type": "SoftwareSourceCode", "name": name, "description": desc,
                       "codeRepository": github, "url": github}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Projects", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": name, "item": canonical}
            ]}
        ]
    }
    content = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#252F3A"><meta name="description" content="{e(seo_description)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="infoconex"><meta property="og:title" content="{e(seo_title)}"><meta property="og:description" content="{e(seo_description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{share_image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(name)} social preview">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(seo_title)}"><meta name="twitter:description" content="{e(seo_description)}"><meta name="twitter:image" content="{share_image}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../../styles.css">
<title>{e(seo_title)}</title><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")}</script>
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){{
        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    }})(window, document, "clarity", "script", "z340egz0ho");
</script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QQP7ZQK7ZK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-QQP7ZQK7ZK');
</script>
</head><body>
<header class="site-header"><div class="container header-inner"><a class="brand" href="/"><span class="brand-mark">i<span>.</span></span> infoconex</a><nav aria-label="Main navigation"><a href="/#projects">All projects</a><a href="https://github.com/infoconex">GitHub ↗</a></nav></div></header>
<main class="case-shell"><div class="container"><nav class="case-breadcrumb" aria-label="Breadcrumb"><a href="/#projects">All projects</a><span> / </span>{e(name)}</nav><div class="case-columns"><div class="case-main">
<section class="case-hero" aria-labelledby="project-title">
<div class="case-hero-copy"><p class="eyebrow">{e(kind)} · {e(category)}</p><h1 id="project-title">{e(name)}</h1><p class="case-tagline">{e(tagline)}</p><p class="case-lead">{e(seo_description)}</p></div>
<div class="case-hero-visual" aria-label="Project capabilities"><span class="case-visual-label">KEY THEMES</span>{visual}</div>
</section>
<article>
<section class="case-section" id="problem"><span class="case-kicker">01 / Why</span><h2>The problem</h2><p>{e(problem)}</p>{problem_details}</section>
<section class="case-section" id="solution"><span class="case-kicker">02 / What</span><h2>The solution</h2><p>{e(solution)}</p>{solution_details}</section>
<section class="case-section" id="audience"><span class="case-kicker">03 / Who</span><h2>Who it's for</h2><p>{e(audience)}</p>{audience_details}</section>
<section class="case-section" id="workflow"><span class="case-kicker">04 / How</span><h2>How it works</h2><p>Key capabilities and concepts. See the project documentation or source code for implementation details.</p><div class="case-steps">{capabilities}</div></section>
<section class="case-section" id="decisions"><span class="case-kicker">05 / Engineering perspective</span><h2>Design decisions that matter</h2><ul class="case-bullets">{decision_items}</ul></section>
<section class="case-section" id="status"><span class="case-kicker">06 / Current state</span><h2>Explore the implementation</h2><p>{e(status)}</p>{status_details}</section>
{articles_section}
{related_section}
</article></div>
<aside class="case-aside" aria-label="Project context">
<div class="case-side-card"><h2>Project details</h2><div class="case-side-actions">{actions}</div><dl>{detail_rows}</dl></div>
<div class="case-side-card"><h2>On this page</h2><nav class="case-toc" aria-label="Project sections"><a href="#problem"><span class="case-toc-number">01</span>The problem</a><a href="#solution"><span class="case-toc-number">02</span>The solution</a><a href="#audience"><span class="case-toc-number">03</span>Who it's for</a><a href="#workflow"><span class="case-toc-number">04</span>How it works</a><a href="#decisions"><span class="case-toc-number">05</span>Design decisions</a><a href="#status"><span class="case-toc-number">06</span>Current state</a>{optional_toc}</nav></div>
</aside></div></div></main>
<footer class="site-footer"><div class="container footer-inner"><span>© infoconex</span><nav aria-label="Footer navigation"><a href="/#projects">All projects</a><a href="https://github.com/infoconex">GitHub ↗</a></nav></div></footer>
<script src="../../project-scrollspy.js" defer></script></body></html>'''
    write(ROOT / "projects" / slug / "index.html", external_links_new_tab(content))
print(f"Generated homepage, sitemap and {len(projects)} project pages.")
