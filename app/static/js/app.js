console.log('Indoor Niche Lab listo');

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const topbar = document.querySelector('.topbar');
const topbarHeight = topbar ? topbar.offsetHeight : 0;

const currentYear = document.getElementById('current-year');
if (currentYear) {
  currentYear.textContent = new Date().getFullYear();
}

function setNavActiveByPath() {
  const path = document.body.dataset.path || window.location.pathname;
  const navLinks = document.querySelectorAll('[data-nav-root]');
  navLinks.forEach((link) => {
    const root = link.dataset.navRoot;
    const isHome = root === '/';
    const isActive = isHome ? path === '/' : path === root || path.startsWith(`${root}/`);
    link.classList.toggle('active', isActive);
    if (isActive) {
      link.setAttribute('aria-current', 'page');
    } else {
      link.removeAttribute('aria-current');
    }
  });
}

function setHomeSectionObserver() {
  if (window.location.pathname !== '/') return;
  const homeNav = document.querySelector('[data-home-nav]');
  if (!homeNav) return;

  const sections = document.querySelectorAll('[data-home-section]');
  if (!sections.length || !('IntersectionObserver' in window)) return;

  const sectionTone = {
    beneficios: 'section-beneficios',
    'como-funciona': 'section-como-funciona',
    testimonios: 'section-testimonios',
    faq: 'section-faq',
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      homeNav.classList.remove('section-beneficios', 'section-como-funciona', 'section-testimonios', 'section-faq');
      const sectionName = entry.target.getAttribute('data-home-section');
      if (sectionName && sectionTone[sectionName]) {
        homeNav.classList.add(sectionTone[sectionName]);
      }
    });
  }, { threshold: 0.45, rootMargin: `-${topbarHeight}px 0px -45% 0px` });

  sections.forEach((section) => observer.observe(section));
}

function smoothScrollToHash(hash) {
  const target = document.querySelector(hash);
  if (!target) return;
  const offset = topbarHeight + 12;
  const targetTop = target.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top: targetTop, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
}

function setupSmoothAnchors() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (event) => {
      const hash = anchor.getAttribute('href');
      if (!hash || hash === '#') return;
      const target = document.querySelector(hash);
      if (!target) return;
      event.preventDefault();
      smoothScrollToHash(hash);
      history.replaceState(null, '', hash);
    });
  });

  if (window.location.hash && document.querySelector(window.location.hash)) {
    requestAnimationFrame(() => smoothScrollToHash(window.location.hash));
  }
}

function setActionStatus(statusNode, type, text) {
  if (!statusNode) return;

  const iconByType = {
    loading: '/static/assets/icons/loading_spinner.svg',
    success: '/static/assets/icons/success_check.svg',
    error: '/static/assets/icons/error_alert.svg',
  };

  statusNode.innerHTML = '';
  const icon = document.createElement('img');
  icon.src = iconByType[type];
  icon.alt = '';
  if (type === 'loading') {
    icon.classList.add('spin');
  }
  const label = document.createElement('span');
  label.textContent = text;
  statusNode.append(icon, label);
}

async function handleAsyncActionForm(form) {
  const button = form.querySelector('button[type="submit"]');
  const statusNode = form.querySelector('.action-status');
  if (!button || !statusNode) {
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    button.disabled = true;
    setActionStatus(statusNode, 'loading', 'Ejecutando...');

    try {
      const response = await fetch(form.action, {
        method: form.method || 'POST',
        body: new FormData(form),
      });

      if (!response.ok) {
        throw new Error('No se pudo completar la acción');
      }

      setActionStatus(statusNode, 'success', 'Acción completada');
      if (!form.dataset.noRedirect && response.redirected && response.url) {
        window.location.assign(response.url);
      }
    } catch (error) {
      setActionStatus(statusNode, 'error', 'Falló la acción');
      button.disabled = false;
    }
  });
}

function setupFaqAccordion() {
  const faqRoot = document.querySelector('[data-faq-accordion]');
  if (!faqRoot) return;

  faqRoot.querySelectorAll('.faq-trigger').forEach((button) => {
    button.addEventListener('click', () => {
      const panelId = button.getAttribute('aria-controls');
      const panel = panelId ? document.getElementById(panelId) : null;
      if (!panel) return;

      const isExpanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!isExpanded));
      panel.hidden = isExpanded;
      panel.classList.toggle('is-open', !isExpanded);
    });
  });
}

function setupFormValidation() {
  document.querySelectorAll('[data-validate-form]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const errorNode = form.querySelector('[data-form-error]');
      if (!errorNode) return;
      errorNode.textContent = '';

      const requiredFields = Array.from(form.querySelectorAll('[required]'));
      const hasEmpty = requiredFields.some((field) => !field.value.trim());
      if (hasEmpty) {
        event.preventDefault();
        errorNode.textContent = 'Faltan campos obligatorios.';
        return;
      }

      const estimatedCost = form.querySelector('input[name="estimated_cost_usd"]');
      if (estimatedCost && estimatedCost.value && Number(estimatedCost.value) < 0) {
        event.preventDefault();
        errorNode.textContent = 'El costo no puede ser negativo.';
      }
    });
  });
}

setNavActiveByPath();
setHomeSectionObserver();
setupSmoothAnchors();
setupFaqAccordion();
setupFormValidation();
document.querySelectorAll('.async-action-form').forEach(handleAsyncActionForm);
