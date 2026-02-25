(function () {
  function wire() {
    const btn = document.getElementById('hitalx-add-expense');
    const total = document.getElementById('id_hitalx_expense_inline-TOTAL_FORMS');
    const tbody = document.querySelector('#hitalx-expense-table tbody');
    const tpl = document.getElementById('hitalx-expense-row-template');
    if (!btn || !total || !tbody || !tpl) return;

    btn.addEventListener('click', function () {
      const idx = parseInt(total.value || '0', 10);
      const html = tpl.innerHTML.split('{index}').join(String(idx));
      tbody.insertAdjacentHTML('beforeend', html);
      total.value = String(idx + 1);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
