document.addEventListener('DOMContentLoaded', function () {

  /*CLIENT-SIDE FILTER
     Filters cards by study type and date
     without a full page reload (S1 requirement) */
  const filterType = document.getElementById('filter-type');
  const filterDate = document.getElementById('filter-date');
  const filterClear = document.getElementById('filter-clear');
  const recordCards = document.querySelectorAll('.record-card-wrapper');
  const emptyMessage = document.getElementById('empty-filter-msg');

  function applyFilters() {
  if (!filterType) return;

  const selectedType = filterType.value;
  const selectedDate = filterDate ? filterDate.value : '';
  let visibleCount = 0;
  
  document.querySelectorAll('.record-item').forEach(function (card) {
    const cardType = card.dataset.type || '';
    const cardDate = card.dataset.date || '';

    const typeMatch = !selectedType || cardType === selectedType;
    const dateMatch = !selectedDate || cardDate === selectedDate;

    if (typeMatch && dateMatch) {
      card.style.display = '';
      visibleCount++;
    } else {
      card.style.display = 'none';
    }
  });

  if (emptyMessage) {
    emptyMessage.style.display = visibleCount === 0 ? 'block' : 'none';
  }

  announceToScreenReader(
    visibleCount === 0
      ? 'No records match the current filter.'
      : visibleCount + ' record' + (visibleCount > 1 ? 's' : '') + ' shown.'
  );
}

  if (filterType) filterType.addEventListener('change', applyFilters);
  if (filterDate) filterDate.addEventListener('change', applyFilters);
  if (filterClear) {
    filterClear.addEventListener('click', function () {
      if (filterType) filterType.value = '';
      if (filterDate) filterDate.value = '';
      applyFilters();
    });
  }


  /*AJAX DELETE
     Deletes a record without page reload */
  document.querySelectorAll('.btn-ajax-delete').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const url = btn.dataset.url;
      const cardWrapper = btn.closest('.record-card-wrapper') || btn.closest('.card');
      const csrfToken = getCookie('csrftoken');

      if (!confirm('Delete this record? This cannot be undone.')) return;

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
        .then(function (res) {
          if (res.ok) {
            cardWrapper.style.transition = 'opacity 0.3s, transform 0.3s';
            cardWrapper.style.opacity = '0';
            cardWrapper.style.transform = 'scale(0.95)';
            setTimeout(function () {
              cardWrapper.remove();
              announceToScreenReader('Record deleted.');
              showToast('Record deleted successfully.', 'success');
            }, 320);
          } else {
            showToast('Could not delete record. Please try again.', 'danger');
          }
        })
        .catch(function () {
          showToast('Network error. Please check your connection.', 'danger');
        });
    });
  });


  /*FORM ENHANCEMENTS
     Character counter for reflection note */
  const reflectionField = document.getElementById('id_reflection_note');
  const charCounter = document.getElementById('reflection-counter');
  if (reflectionField && charCounter) {
    function updateCounter() {
      charCounter.textContent = reflectionField.value.length + ' characters';
    }
    reflectionField.addEventListener('input', updateCounter);
    updateCounter();
  }

  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('[type=submit]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Saving...';
      }
    });
  });


  /*ACCESSIBILITY HELPERS*/

  const liveRegion = document.getElementById('sr-live-region');
  function announceToScreenReader(msg) {
    if (!liveRegion) return;
    liveRegion.textContent = '';
    setTimeout(function () { liveRegion.textContent = msg; }, 50);
  }

  function showToast(message, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const id = 'toast-' + Date.now();
    const html =
      '<div id="' + id + '" class="toast align-items-center text-bg-' + type + ' border-0" role="alert" aria-live="assertive" aria-atomic="true">' +
      '  <div class="d-flex">' +
      '    <div class="toast-body">' + message + '</div>' +
      '    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
      '  </div>' +
      '</div>';
    container.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', function () { toastEl.remove(); });
  }

  function getCookie(name) {
    let value = null;
    document.cookie.split(';').forEach(function (c) {
      const [k, v] = c.trim().split('=');
      if (k === name) value = decodeURIComponent(v);
    });
    return value;
  }

});