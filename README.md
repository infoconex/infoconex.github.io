# infoconex.github.io

A static, searchable directory of public engineering projects published at **https://infoconex.github.io/**.

## Publishing

In **Settings → Pages**, select **Deploy from a branch** and set **main / (root)**. This is a plain HTML site with no build dependencies.

## Pages and discovery

- `index.html` includes crawlable HTML links to all 9 project pages. Search filtering is progressive enhancement and does not remove links for visitors without JavaScript.
- `projects/<repo-name>/index.html` is a distinct indexable landing page with its own canonical URL, descriptive title, social metadata, and structured data. Some pages link to published documentation.
- `pages-sitemap.xml` lists the homepage and all project landing pages.
- `sitemap.xml` is the sitemap index, also referencing published Jekyll project sitemaps.
- `robots.txt` advertises the sitemap index.
- The GitHub Actions workflow `.github/workflows/seo-validation.yml` checks HTML canonical metadata, internal links, sitemap entries, and consistency with `projects.json`.

## Add or edit a project

Use orders 10, 20, 30, etc., leaving room to insert new projects between existing ones. Both `order` in `projects.json` and `data-order` in `index.html` should agree. The homepage sorts by `data-order` when JavaScript is available; its committed HTML retains a crawlable initial order.\n\nThere is **no automatic GitHub repository discovery** and project cards are **intentionally not built from JavaScript**. When adding a project:

1. Add or edit its entry in `projects.json` (public repositories only), including a numeric `order` field (lower values appear first).
2. Add a crawlable project card linking to `/projects/<repo-name>/` in `index.html`, with matching `data-order`. Keep the static card order aligned with numeric order for non-JavaScript visitors and crawlers.
3. Create or update `projects/<repo-name>/index.html` with original, helpful project details, canonical URL, and metadata.
4. Add the new canonical URL to `pages-sitemap.xml`.
5. Run `python scripts/validate_seo.py` before committing. CI runs this automatically.

Where possible, link to both the GitHub source and its hosted documentation. Avoid duplicating a whole README just for SEO.

## Search indexing

1. Enable GitHub Pages and confirm the published site works.
2. Verify ownership in [Google Search Console](https://search.google.com/search-console/).
3. Submit `https://infoconex.github.io/sitemap.xml`.
4. Check coverage and indexing reports after Google crawls the site. Verification and submission must be completed in the appropriate Google account.

The sitemap URLs from other project sites are references, not proof of live deployment. Check their live status independently. Avoid submitting unverified links to search engines.

## Files

- `index.html`, `styles.css`, `script.js` — homepage and interactive filtering
- `projects.json` — project catalog and consistency inventory
- `projects/*/index.html` — search-engine-readable project detail pages
- `pages-sitemap.xml` — local page URLs
- `sitemap.xml` — aggregate sitemap index
- `robots.txt` — crawler directions
- `scripts/validate_seo.py` — standard-library SEO integrity check

