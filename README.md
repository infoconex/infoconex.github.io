# infoconex.github.io

A static, searchable index of public projects for **https://infoconex.github.io/**.

## Publish with GitHub Pages

1. Open **Settings → Pages** in this repository.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select **main** and **/(root)**, then save.
4. GitHub Pages will publish the site at **https://infoconex.github.io/** once deployment completes.

No packages, frameworks, build commands, or secrets are required.

## Add a project

Edit `projects.json` and add a new entry:

```json
{
  "name": "My Project",
  "category": "Developer Tools",
  "description": "A short description of the project.",
  "url": "https://github.com/infoconex/my-project"
}
```

Keep the array valid JSON. The homepage reads this file and renders a searchable card for each project. Only add public repositories or other URLs you intend to share.

## SEO and crawling

- `robots.txt` is served from `/robots.txt` and points to the sitemap.
- `sitemap.xml` is served from `/sitemap.xml`; it includes the site's canonical homepage.
- External GitHub repository links are **not** included in this site's sitemap because they are on a different host.
- If you add new HTML pages to this site later, add their canonical URLs to `sitemap.xml`.

## Structure

- `index.html`: homepage and metadata
- `styles.css`: responsive design
- `script.js`: search and project rendering
- `projects.json`: editable project catalog
- `robots.txt`, `sitemap.xml`: crawl discovery
- `favicon.svg`: site icon
