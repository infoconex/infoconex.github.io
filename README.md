# infoconex.github.io

A static, searchable directory of public engineering projects published at **https://infoconex.github.io/**.

## Publishing

In **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”). The `Build and deploy site` workflow generates, validates, and publishes the site from one run whenever `main` changes. Pull requests run build validation without deployment. No generated changes are pushed back to the repository.

## Pages and discovery

- `index.html` includes crawlable HTML links to all 9 project pages. Search filtering is progressive enhancement and does not remove links for visitors without JavaScript.
- `projects/<repo-name>/index.html` is a distinct indexable landing page with its own canonical URL, descriptive title, social metadata, and structured data. Some pages link to published documentation.
- `pages-sitemap.xml` lists the homepage and all project landing pages.
- `sitemap.xml` is the sitemap index, also referencing published Jekyll project sitemaps.
- `robots.txt` advertises the sitemap index.
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
- `pages-sitemap.xml`

To regenerate and validate locally:

```bash
python scripts/build_projects.py
python scripts/validate_seo.py
```

The GitHub Actions workflow generates these files in its checkout, validates them, then uploads the generated static site as a Pages artifact. **It does not commit generated files or trigger an additional push/deployment.** Pull requests validate without publishing. The site is deployed only after the build succeeds.

**Do not edit generated cards, landing pages, or the page sitemap directly:** the deployment generator will overwrite them in the published artifact. Keep project descriptions accurate and avoid claims of functionality that is still planned.

## Search indexing

1. Enable GitHub Pages and confirm the published site works.
2. Verify ownership in [Google Search Console](https://search.google.com/search-console/).
3. Submit `https://infoconex.github.io/sitemap.xml`.
4. Check coverage and indexing reports after Google crawls the site. Verification and submission must be completed in the appropriate Google account.

The sitemap URLs from other project sites are references, not proof of live deployment. Check their live status independently. Avoid submitting unverified links to search engines.

## Files

- `index.html`, `styles.css`, `script.js` — homepage and interactive filtering
- `projects.json` — authoritative project catalog, ordering, and descriptions
- `scripts/build_projects.py` — static HTML, JSON-LD, and sitemap generator
- `projects/*/index.html` — search-engine-readable project detail pages
- `pages-sitemap.xml` — local page URLs
- `sitemap.xml` — aggregate sitemap index
- `robots.txt` — crawler directions
- `scripts/validate_seo.py` — standard-library SEO integrity check

