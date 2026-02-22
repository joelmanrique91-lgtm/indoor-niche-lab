console.log('Indoor Niche Lab listo');

const currentYear = document.getElementById('current-year');
if (currentYear) {
  currentYear.textContent = new Date().getFullYear();
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
    const originalDisabled = button.disabled;
    button.disabled = true;
    setActionStatus(statusNode, 'loading', 'Procesando...');

    try {
      const response = await fetch(form.action, {
        method: form.method || 'POST',
        body: new FormData(form),
      });

      if (!response.ok) {
        throw new Error('No se pudo completar la acción');
      }

      setActionStatus(statusNode, 'success', 'Acción completada');

      const destination = response.redirected && response.url ? response.url : '/admin';
      window.location.assign(destination);
    } catch (error) {
      setActionStatus(statusNode, 'error', 'Falló la acción');
      button.disabled = originalDisabled;
    }
  });
}

document.querySelectorAll('.async-action-form').forEach(handleAsyncActionForm);
