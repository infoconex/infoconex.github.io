/* Preview C section-aware navigation. No dependencies. */
(() => {
  const links = [...document.querySelectorAll('.toc a[href^="#"]')];
  const sections = links.map(link => document.getElementById(link.hash.slice(1)));
  if (!links.length || sections.some(section => !section)) return;

  function update() {
    // Prefer the last section that has crossed the reading line.
    const readingLine = Math.min(180, window.innerHeight * 0.27);
    let current = 0;
    sections.forEach((section, i) => {
      if (section.getBoundingClientRect().top <= readingLine) current = i;
    });
    links.forEach((link, i) => {
      const active = i === current;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }

  let scheduled = false;
  function queueUpdate() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; update(); });
  }
  window.addEventListener('scroll', queueUpdate, { passive: true });
  window.addEventListener('resize', queueUpdate);
  window.addEventListener('hashchange', queueUpdate);
  links.forEach(link => link.addEventListener('click', () => {
    links.forEach(other => {
      other.classList.toggle('active', other === link);
      if (other === link) other.setAttribute('aria-current', 'location');
      else other.removeAttribute('aria-current');
    });
  }));
  update();
})();
