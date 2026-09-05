'use strict';
const field = document.querySelector('.line-field');
for (let i = 0; i < 14; i++) {
  const line = document.createElement('div');
  line.className = 'scanline';
  line.style.setProperty('--i', i);
  line.style.setProperty('--wave-start', `${100 - i * 7}%`);
  line.style.setProperty('--wave-end', `${107 - i * 7}%`);
  field.append(line);
}
const identity = document.querySelector('.identity'),
  toggle = document.querySelector('.menu-toggle'),
  menu = document.querySelector('.site-menu'),
  shade = document.querySelector('.menu-shade');
function setMenu(open) {
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  menu.hidden = !open;
  shade.hidden = !open;
  identity.classList.toggle('is-open', open);
  document.body.classList.toggle('menu-open', open);
}
toggle.addEventListener('click', () =>
  setMenu(toggle.getAttribute('aria-expanded') !== 'true'),
);
shade.addEventListener('click', () => setMenu(false));
menu
  .querySelectorAll('a')
  .forEach((a) => a.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    setMenu(false);
    toggle.focus();
  }
});
// Collapsing identity card: visible while scrolling up, tucked away on the way down.
let lastY = window.scrollY,
  scrollQueued = false;
window.addEventListener(
  'scroll',
  () => {
    if (scrollQueued) return;
    scrollQueued = true;
    requestAnimationFrame(() => {
      const y = window.scrollY;
      if (Math.abs(y - lastY) > 5) {
        identity.classList.toggle('is-hidden', y > lastY && y > 180);
        lastY = y;
      }
      scrollQueued = false;
    });
  },
  { passive: true },
);
// Accessible tab groups, including arrow, Home and End keyboard navigation.
document.querySelectorAll('[role="tablist"]').forEach((list) => {
  const tabs = [...list.querySelectorAll('[role="tab"]')];
  function select(tab, focus = false) {
    tabs.forEach((item) => {
      const chosen = item === tab;
      item.setAttribute('aria-selected', String(chosen));
      item.tabIndex = chosen ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden =
        !chosen;
    });
    if (focus) tab.focus();
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', (event) => {
      let next = i;
      if (event.key === 'ArrowRight') next = (i + 1) % tabs.length;
      else if (event.key === 'ArrowLeft')
        next = (i - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      select(tabs[next], true);
    });
  });
});
// Client carousel supports buttons, trackpad/touch, mouse dragging and the keyboard.
const track = document.querySelector('.client-track'),
  cards = [...document.querySelectorAll('.client-card')],
  counter = document.querySelector('#client-counter');
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
function currentCard() {
  return Math.round(track.scrollLeft / (cards[0].offsetWidth + 16));
}
function moveCard(delta) {
  const next = (currentCard() + delta + cards.length) % cards.length;
  track.scrollTo({
    left: next * (cards[0].offsetWidth + 16),
    behavior: reduced.matches ? 'instant' : 'smooth',
  });
}
document
  .querySelector('#client-prev')
  .addEventListener('click', () => moveCard(-1));
document
  .querySelector('#client-next')
  .addEventListener('click', () => moveCard(1));
track.addEventListener('keydown', (e) => {
  if (e.target !== track) return;
  if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
    e.preventDefault();
    moveCard(e.key === 'ArrowRight' ? 1 : -1);
  }
});
track.addEventListener(
  'scroll',
  () => {
    counter.textContent = `${String(Math.min(cards.length, currentCard() + 1)).padStart(2, '0')} / 03`;
  },
  { passive: true },
);
let drag = null,
  didDrag = false;
track.addEventListener('pointerdown', (e) => {
  if (
    e.pointerType !== 'mouse' ||
    e.button !== 0 ||
    e.target.closest('a,button')
  )
    return;
  drag = { x: e.clientX, left: track.scrollLeft, id: e.pointerId };
  didDrag = false;
});
track.addEventListener('pointermove', (e) => {
  if (!drag) return;
  const distance = e.clientX - drag.x;
  if (Math.abs(distance) > 5) {
    if (!didDrag) track.setPointerCapture(drag.id);
    didDrag = true;
    track.classList.add('dragging');
    track.scrollLeft = drag.left - distance;
  }
});
function stopDrag() {
  if (!drag) return;
  const target = Math.round(track.scrollLeft / (cards[0].offsetWidth + 16));
  drag = null;
  track.classList.remove('dragging');
  track.scrollTo({
    left: target * (cards[0].offsetWidth + 16),
    behavior: reduced.matches ? 'instant' : 'smooth',
  });
}
track.addEventListener('pointerup', stopDrag);
track.addEventListener('pointercancel', stopDrag);
track.addEventListener('lostpointercapture', stopDrag);
track.addEventListener(
  'click',
  (e) => {
    if (didDrag) {
      e.preventDefault();
      didDrag = false;
    }
  },
  true,
);
// Native modal preserves keyboard focus and keeps all project details on the device.
const dialog = document.querySelector('#inquiry'),
  form = document.querySelector('#inquiry-form'),
  result = document.querySelector('.form-result');
let inquiryTrigger = null;
document.querySelectorAll('[data-contact]').forEach((link) =>
  link.addEventListener('click', (e) => {
    e.preventDefault();
    setMenu(false);
    inquiryTrigger = link;
    result.textContent = '';
    dialog.showModal();
  }),
);
document
  .querySelector('.dialog-close')
  .addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (e) => {
  if (e.target === dialog) {
    const rect = dialog.getBoundingClientRect();
    if (
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom
    )
      dialog.close();
  }
});
dialog.addEventListener('close', () => inquiryTrigger?.focus());
form.addEventListener('submit', (e) => {
  e.preventDefault();
  if (!form.reportValidity()) return;
  const data = new FormData(form);
  const brief = `PROJECT BRIEF\n=============\n\nName: ${data.get('name')}\nEmail: ${data.get('email')}\n\nProject\n-------\n${data.get('project')}\n\nCreated locally in an independent Webisoft design study. This brief has not been sent.\n`;
  const url = URL.createObjectURL(
    new Blob([brief], { type: 'text/plain;charset=utf-8' }),
  );
  const download = document.createElement('a');
  download.href = url;
  download.download = 'project-brief.txt';
  document.body.append(download);
  download.click();
  download.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  result.textContent =
    'Your project brief is ready. No information has been sent.';
});
function updateClocks() {
  document.querySelectorAll('.office-clock').forEach((el) => {
    try {
      el.textContent =
        new Intl.DateTimeFormat('en-GB', {
          hour: '2-digit',
          minute: '2-digit',
          timeZone: el.dataset.zone,
          hour12: false,
        }).format(new Date()) + ' LOCAL TIME';
    } catch {
      el.textContent = 'EASTERN TIME';
    }
  });
}
updateClocks();
setInterval(updateClocks, 60000);
if ('IntersectionObserver' in window && !reduced.matches) {
  document.documentElement.classList.add('motion-ready');
  const observer = new IntersectionObserver(
    (entries) =>
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      }),
    { threshold: 0.15 },
  );
  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
}
// Pause decorative motion while the tab is not being viewed.
document.addEventListener('visibilitychange', () => {
  document.querySelectorAll('.scanline,.contact-marquee').forEach((el) => {
    el.style.animationPlayState = document.hidden ? 'paused' : 'running';
  });
});
