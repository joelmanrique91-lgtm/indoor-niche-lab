console.log('Indoor Niche Lab listo');

const currentYear = document.getElementById('current-year');
if (currentYear) {
  currentYear.textContent = new Date().getFullYear();
}

const generatedImagePlaceholder = `data:image/svg+xml;utf8,${encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#eceae5" />
      <stop offset="100%" stop-color="#d8d6d1" />
    </linearGradient>
  </defs>
  <rect width="1200" height="800" fill="url(#bg)" />
  <rect x="120" y="140" width="960" height="520" rx="18" fill="#f8f7f4" stroke="#b8b5ad" stroke-width="2"/>
  <text x="600" y="370" text-anchor="middle" font-family="Arial, sans-serif" font-size="38" fill="#5f5b52">
    Imagen generada no disponible
  </text>
  <text x="600" y="420" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" fill="#7a756b">
    Ejecuta scripts/generate_site_images.py
  </text>
</svg>
`)}`;

function attachGeneratedFallback(img) {
  if (!img.src.includes('/static/img/generated/')) {
    return;
  }

  img.addEventListener('error', () => {
    if (img.dataset.fallbackApplied === '1') {
      return;
    }
    img.dataset.fallbackApplied = '1';
    img.src = generatedImagePlaceholder;
  });
}

document.querySelectorAll('img').forEach(attachGeneratedFallback);
