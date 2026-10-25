# infoconex.github.io (Projects Site)

A static, searchable directory of public engineering projects published at **https://projects.infoconex.com/**.

## Custom domain

The GitHub Pages domain is `projects.infoconex.com`. Set the custom domain in Settings → Pages, and point the DNS CNAME for `projects` to `infoconex.github.io`. The repository root `CNAME` is included in the Pages deployment artifact.

## Publishing

In **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”). The `Build and deploy site` workflow generates, validates, and publishes the site from one run whenever `main` changes. Pull requests run build validation without deployment. No generated changes are pushed back to the repository.

## Pages and discovery

- `index.html` includes crawlable HTML links to all 9 project pages. Search filtering is progressive enhancement and does not remove links for visitors without JavaScript.
- `projects/<repo-name>/index.html` is a distinct indexable landing page with its own canonical URL, descriptive title, social metadata, and structured data. Some pages link to published documentation.
- `sitemap.xml` lists the homepage and all project landing pages, with verified per-project `lastmod` dates where supplied.
- `robots.txt` advertises this site sitemap.
- The GitHub Actions workflow `.github/workflows/seo-validation.yml` checks HTML canonical metadata, internal links, sitemap entries, and consistency with `projects.json`.

## Maintain projects (single source of truth)

Edit **`projects.json`** to add projects, change descriptions, adjust the numeric `order` (lower numbers first), and optionally supply a `website` URL for published documentation. Only public repositories should be listed.

Example:

```json
{
  "name": "Example Tool",
  "category": "Developer Tools",
  "description": "A useful and specific description of what the tool does.",
  "url": "https://github.com/infoconex/example-tool",
  "order": 35,
  "website": "https://example.com/docs/"
}
```

The `scripts/build_projects.py` generator reads this catalog and updates:
- Static, search-engine-readable project cards in `index.html`
- JSON-LD project order on the homepage
- All `projects/<repo-name>/index.html` landing pages and their SEO metadata
- `sitemap.xml`

For project pages, maintain the optional `lastmod` field in `projects.json` as a real `YYYY-MM-DD` date **only when that project's substantive content changes**. The current dates are a baseline for the project-page content revised on October 24, 2026. Cosmetic styling, workflow-only changes, and redeployments do **not** justify updating these dates. New projects may omit `lastmod` until a meaningful date is established. The homepage deliberately omits `lastmod` rather than inventing one. `changefreq` and `priority` are intentionally excluded.

To regenerate and validate locally:

```bash
python -m pip install 'Pillow>=11,<13'
python scripts/build_projects.py
python scripts/build_social_images.py
python scripts/validate_seo.py
```

Each project has a concise, unique `seoDescription` in `projects.json` for HTML, Open Graph, and Twitter metadata. Visible project descriptions stay separate. Titles use `Project Name | infoconex`. The build generates 1200×630 PNG previews in `assets/social/`, adds BreadcrumbList JSON-LD, and validates the expected metadata and image files. Social images use Pillow and DejaVu Sans fonts.

The GitHub Actions workflow generates these files in its checkout, validates them, then uploads the generated static site as a Pages artifact. **It does not commit generated files or trigger an additional push/deployment.** Pull requests validate without publishing. The site is deployed only after the build succeeds.

**Do not edit generated cards, landing pages, or the page sitemap directly:** the deployment generator will overwrite them in the published artifact. Keep project descriptions accurate and avoid claims of functionality that is still planned.

## Search indexing

1. Enable GitHub Pages and confirm the published site works.
2. Verify ownership in [Google Search Console](https://search.google.com/search-console/).
3. Submit `https://projects.infoconex.com/sitemap.xml`.
4. Check coverage and indexing reports after Google crawls the site. Verification and submission must be completed in the appropriate Google account.

## Files

- `index.html`, `styles.css`, `script.js` — homepage and interactive filtering
- `projects.json` — authoritative project catalog, ordering, and descriptions
- `scripts/build_projects.py` — static HTML, JSON-LD, and sitemap generator
- `projects/*/index.html` — search-engine-readable project detail pages
- `sitemap.xml` — canonical sitemap for this site
- `robots.txt` — crawler directions
- `scripts/validate_seo.py` — standard-library SEO integrity check


## Repository images for social previews

The optional `socialSource` field in `projects.json` points to an explicit, approved image in an infoconex GitHub repository. The image build fetches it, checks basic resolution and size, and fits it into a 1200×630 PNG without cropping. If the source is unavailable or unsuitable, the generator uses its original Smoky Slate card. Currently configured for Copy GitHub Repo and AI Flywheel Specification. Isolated .NET SDK remains on the generated fallback until a suitable repository image can be confirmed. The image published at `assets/social/<slug>.png` is always served from this site rather than hotlinked.
