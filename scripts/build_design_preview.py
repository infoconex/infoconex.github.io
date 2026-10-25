#!/usr/bin/env python3
"""Generate unindexed Preview C examples without touching production project pages."""
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design-preview" / "modern-case-study"
projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
by_slug = {urlparse(p["url"]).path.strip("/").split("/")[-1]: p for p in projects}
EXAMPLES = ("isolated-dotnet-sdk", "ai-flywheel-spec", "coding-blog")
# Presentation hints live here; project copy, relationships and article URLs remain in projects.json.
PRESENTATION = {
 "isolated-dotnet-sdk": {"kind": "Software utility", "tagline": "Exact SDK versions. No system-wide changes.", "details": [("Interfaces", "PowerShell · Bash"), ("Platforms", "Windows · Linux · macOS")]},
 "ai-flywheel-spec": {"kind": "Methodology / specification", "tagline": "A loop repeats. A flywheel compounds.", "details": []},
 "coding-blog": {"kind": "Technical publication", "tagline": "Practical engineering, documented.", "details": []},
}

def esc(v):
    return html.escape(str(v), quote=True)

def external_link(url, label, css=""):
    return f'<a class="{css}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'

def paragraphs(values):
    return "".join(f"<p>{esc(v)}</p>" for v in values if v)

def render(project, slug):
    study = project["caseStudy"]
    info = PRESENTATION[slug]
    name = project["name"]
    details = info["details"] + [("Category", project["category"])]
    details_html = "".join(f'<div class="detail"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k,v in details if v)
    github = project["url"]
    docs = project.get("website")
    code_cta = external_link(github, "View source code ↗", "side-action primary")
    doc_cta = external_link(docs, "Read documentation ↗" if slug != "coding-blog" else "Visit publication ↗", "side-action secondary") if docs else ""
    actions = code_cta + doc_cta
    hero_visuals = {
        "isolated-dotnet-sdk": '<div class="visual-window"><div class="window-dots"><i></i><i></i><i></i></div><div class="visual-rows"><span>✓ Install exact SDK versions</span><span>✓ Verify installation</span><span>✓ Audit SDK inventory</span><span>✓ Remove when finished</span></div></div>',
        "ai-flywheel-spec": '<div class="visual-window"><div class="visual-heading">EVIDENCE-DRIVEN LIFECYCLE</div><div class="visual-rows"><span>01 Execute and observe</span><span>02 Evaluate evidence</span><span>03 Validate improvement</span><span>04 Reuse supported learning</span></div></div>',
        "coding-blog": '<div class="visual-window editorial"><div class="visual-heading">FIELD NOTES / ENGINEERING</div><div class="visual-rows"><span>Architecture &amp; design</span><span>.NET &amp; developer tooling</span><span>Experiments &amp; lessons</span></div></div>',
    }
    hero_visual = hero_visuals[slug]
    stages = [
      ("problem", "01 / Why", "The problem", study.get("problem"), study.get("problemDetails", [])),
      ("solution", "02 / What", "The solution", study.get("solution"), study.get("solutionDetails", [])),
      ("audience", "03 / Who", "Who it's for", project.get("audience"), study.get("audienceDetails", [])),
    ]
    sections = []
    for sid,num,title,opening,extra in stages:
        if opening:
            sections.append(f'<section id="{sid}" class="section"><span class="kicker">{num}</span><h2>{title}</h2><p>{esc(opening)}</p>{paragraphs(extra)}</section>')
    steps = "".join(
        f'<div class="step"><b>{i:02d}</b><div><h3>{esc(feature)}</h3>{paragraphs(study.get("workflowDetails", [])[i-1] if i <= len(study.get("workflowDetails", [])) else [])}</div></div>'
        for i,feature in enumerate(project.get("highlights", []),1))
    if steps:
        sections.append(f'<section id="workflow" class="section"><span class="kicker">04 / How</span><h2>{"How the publication works" if slug=="coding-blog" else "How it works"}</h2><div class="steps">{steps}</div></section>')
    decisions = "".join(f'<li><strong>{esc(x)}</strong>{paragraphs(study.get("decisionDetails", [])[i] if i < len(study.get("decisionDetails", [])) else [])}</li>' for i,x in enumerate(study.get("decisions", [])))
    if decisions:
        sections.append(f'<section id="decisions" class="section"><span class="kicker">05 / Engineering perspective</span><h2>Design decisions</h2><ul class="decisions">{decisions}</ul></section>')
    if study.get("status"):
        sections.append(f'<section id="status" class="section"><span class="kicker">06 / Current state</span><h2>Current state</h2><p>{esc(study["status"])}</p>{paragraphs(study.get("statusDetails", []))}</section>')
    related = [x for x in project.get("related", []) if x["slug"] in by_slug]
    if related:
        links = "".join(f'<a class="resource" href="/projects/{esc(x["slug"])}/"><strong>{esc(by_slug[x["slug"]]["name"])} ↗</strong><span>{esc(x["relationship"])}</span></a>' for x in related)
        sections.append(f'<section id="related" class="section"><span class="kicker">Explore further</span><h2>Related projects</h2><div class="resources">{links}</div></section>')
    articles = project.get("articles", [])
    articles_card = '<div class="card"><h2>Related articles</h2>' + "".join(
        external_link(x["url"], x["title"]+" ↗", "article") + f'<p class="article-desc">{esc(x["description"])}</p>' for x in articles) + '</div>' if articles else ""
    toc = "".join(f'<a href="#{sid}">{esc(title)}</a>' for sid,title in
        [("problem","The problem"),("solution","The solution"),("audience","Who it\'s for"),("workflow","How it works"),("decisions","Design decisions"),("status","Current state"),("related","Related projects")]
        if any(f'id="{sid}"' in x for x in sections))
    details_card = f'<div class="card"><h2>Project details</h2><div class="side-actions">{actions}</div><dl>{details_html}</dl></div>' if details_html else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>Preview C · {esc(name)} | infoconex</title>
<link rel="stylesheet" href="../preview-c.css"></head><body>
<div class="notice"><div class="wrap"><span>Preview C · Unindexed design experiment</span><nav><a href="/projects/{esc(slug)}/">Existing page</a><a href="/design-preview/modern-case-study/">Other examples</a></nav></div></div>
<header class="header"><div class="wrap"><a class="brand" href="/"><span class="logo">i.</span> infoconex</a><nav><a href="/#projects">All projects</a>{external_link("https://github.com/infoconex","GitHub ↗")}</nav></div></header>
<div class="wrap"><div class="crumb"><a href="/#projects">All projects</a><span> / </span>{esc(name)}</div>
<section class="hero"><div class="hero-copy"><p class="eyebrow">{esc(info["kind"])} · {esc(project["category"])}</p><h1>{esc(name)}</h1><p class="tagline">{esc(info["tagline"])}</p><p class="hero-description">{esc(project["seoDescription"])}</p></div><div class="hero-visual" aria-label="Illustration of project themes">{hero_visual}</div></section>
<div class="layout"><main>{"".join(sections)}</main><aside class="sidebar" aria-label="Project context">{details_card}
<div class="card"><h2>On this page</h2><nav class="toc">{toc}</nav></div>{articles_card}</aside></div></div>
<footer class="footer"><div class="wrap"><span>© infoconex · Design experiment</span><a href="/projects/{esc(slug)}/">View current page ↗</a></div></footer></body></html>'''

def main():
    for slug in EXAMPLES:
        assert slug in by_slug
        path = OUT / slug / "index.html"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(render(by_slug[slug],slug),encoding="utf-8")
    # Keep Preview C's original index as an experiment homepage so old links remain valid.
    index = OUT / "index.html"
    links = "".join(f'<li><a href="./{s}/">{esc(by_slug[s]["name"])}</a></li>' for s in EXAMPLES)
    index.write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow,noarchive"><title>Preview C examples · infoconex</title><link rel="stylesheet" href="preview-c.css"></head><body><div class="wrap"><div class="directory"><p class="eyebrow">Design Preview C · Not indexed</p><h1>Modern Engineering Case Study</h1><p>Three project types generated from the same data-driven layout. Production pages are unchanged.</p><ul>{links}</ul><p><a href="/#projects">Return to existing projects ↗</a></p></div></div></body></html>',encoding="utf-8")
    for slug in EXAMPLES:
        page = (OUT / slug / "index.html").read_text(encoding="utf-8")
        project = by_slug[slug]
        assert 'name="robots" content="noindex,nofollow,noarchive"' in page
        assert page.count('class="side-action primary"') == 1, "Exactly one primary CTA required"
        assert '<div class="buttons">' not in page, "Hero actions should be omitted"
        assert page.count('class="side-action secondary"') == (1 if project.get("website") else 0)
        assert page.count('View source code ↗') == 1, "Source action repeated"
        assert ('Read documentation ↗' in page) == bool(project.get("website") and slug != "coding-blog")
        assert ('Visit publication ↗' in page) == (slug == "coding-blog")
        assert ('id="related"' in page) == bool(project.get("related")), "Related project section must be conditional"
        assert ('Related articles</h2>' in page) == bool(project.get("articles")), "Articles card must be conditional"
        for item in project.get("articles", []):
            assert esc(item["url"]) in page, "Missing article"
        for item in project.get("related", []):
            assert f'/projects/{item["slug"]}/' in page, "Missing related project"
    print("Generated and checked Preview C examples:",", ".join(EXAMPLES))
if __name__=="__main__":
    main()
