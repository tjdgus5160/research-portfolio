/* site.js — scroll reveal. Progressive enhancement: without JS the page is
   already readable, because .reveal only hides once this file marks the
   document as script-capable. */

document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", () => {
  const revealElements = document.querySelectorAll(".reveal");

  const showAll = () => {
    for (const el of revealElements) {
      el.classList.add("is-visible");
    }
  };

  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    showAll();
    return;
  }

  if (typeof IntersectionObserver === "undefined") {
    showAll();
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    },
    { rootMargin: "0px 0px -10% 0px", threshold: 0.1 }
  );

  for (const el of revealElements) {
    observer.observe(el);
  }
});
