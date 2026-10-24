// Project cards are static HTML for crawlers and visitors without JavaScript.
const search = document.querySelector("#project-search");
const cards = [...document.querySelectorAll(".project-card")];
const count = document.querySelector("#project-count");
const empty = document.querySelector("#no-results");
const year = document.querySelector("#year");
if (year) year.textContent = new Date().getFullYear();
function filterProjects() {
  const query = search.value.trim().toLocaleLowerCase();
  let visible = 0;
  for (const card of cards) {
    const matches = card.textContent.toLocaleLowerCase().includes(query);
    card.hidden = !matches;
    if (matches) visible++;
  }
  count.textContent = visible + (visible === 1 ? " project" : " projects");
  empty.hidden = visible !== 0;
}
if (search) { search.addEventListener("input", filterProjects); filterProjects(); }
