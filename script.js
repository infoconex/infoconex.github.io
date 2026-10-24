// Edit projects.json to add, remove, or reorder projects.
// Only include repositories you intend to publish.
const grid = document.querySelector("#project-grid");
const search = document.querySelector("#project-search");
const count = document.querySelector("#project-count");
document.querySelector("#year").textContent = new Date().getFullYear();

function render(projects, query = "") {
  const q = query.trim().toLowerCase();
  const visible = projects.filter(p => [p.name, p.description, p.category].join(" ").toLowerCase().includes(q));
  count.textContent = visible.length + (visible.length === 1 ? " project" : " projects");
  grid.replaceChildren();
  if (!visible.length) {
    const p = document.createElement("p");
    p.className = "empty-state";
    p.textContent = "No projects match your search.";
    grid.append(p);
    return;
  }
  for (const project of visible) {
    const card = document.createElement("a");
    card.className = "project-card";
    card.href = project.url;
    card.target = "_blank";
    card.rel = "noopener noreferrer";
    const top = document.createElement("div");
    top.className = "card-top";
    const tag = document.createElement("span");
    tag.className = "card-tag";
    tag.textContent = project.category || "Project";
    const arrow = document.createElement("span");
    arrow.className = "card-arrow";
    arrow.textContent = "↗";
    arrow.setAttribute("aria-hidden", "true");
    top.append(tag, arrow);
    const h3 = document.createElement("h3");
    h3.textContent = project.name;
    const detail = document.createElement("p");
    detail.textContent = project.description || "View repository on GitHub.";
    card.append(top, h3, detail);
    grid.append(card);
  }
}

fetch("projects.json")
  .then(response => { if (!response.ok) throw new Error("Failed to load project catalog"); return response.json(); })
  .then(projects => {
    render(projects);
    search.addEventListener("input", () => render(projects, search.value));
  })
  .catch(() => {
    count.textContent = "";
    grid.textContent = "The project list could not be loaded. Browse repositories at github.com/infoconex.";
  });
