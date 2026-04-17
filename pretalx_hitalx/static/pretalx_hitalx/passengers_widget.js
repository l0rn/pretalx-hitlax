/**
 * Pill / autocomplete widget for the tour passengers field.
 * Wraps the hidden <select multiple class="hitalx-passenger-select"> with a
 * tag-input UI: text field that filters a dropdown, selected items shown as
 * removable pills.
 */
(function () {
  function init() {
    var hiddenSelect = document.querySelector('.hitalx-passenger-select');
    if (!hiddenSelect) return;

    // Snapshot all options before hiding the original select
    var allOptions = Array.from(hiddenSelect.options).map(function (o) {
      return { value: o.value, label: o.text };
    });

    hiddenSelect.style.display = 'none';

    /* ── DOM structure ──────────────────────────────────────────────────────
       .hitalx-pw-wrapper
         .hitalx-pw-pillbox          ← looks like the input border
           .hitalx-pw-pill × N       ← one per selected speaker
           input.hitalx-pw-input     ← search text
         .hitalx-pw-dropdown         ← floating option list
    ───────────────────────────────────────────────────────────────────── */
    var wrapper = document.createElement('div');
    wrapper.className = 'hitalx-pw-wrapper';
    hiddenSelect.parentNode.insertBefore(wrapper, hiddenSelect);

    var pillBox = document.createElement('div');
    pillBox.className = 'hitalx-pw-pillbox';
    wrapper.appendChild(pillBox);

    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'hitalx-pw-input';
    searchInput.placeholder = 'Add speaker\u2026';
    searchInput.autocomplete = 'off';
    searchInput.spellcheck = false;
    pillBox.appendChild(searchInput);

    var dropdown = document.createElement('div');
    dropdown.className = 'hitalx-pw-dropdown';
    dropdown.style.display = 'none';
    wrapper.appendChild(dropdown);

    // ── helpers ────────────────────────────────────────────────────────────

    function selectedValues() {
      return Array.from(hiddenSelect.options)
        .filter(function (o) { return o.selected; })
        .map(function (o) { return o.value; });
    }

    function setSelected(value, selected) {
      var opt = hiddenSelect.querySelector('option[value="' + CSS.escape(value) + '"]');
      if (opt) opt.selected = selected;
    }

    function removePills() {
      Array.from(pillBox.querySelectorAll('.hitalx-pw-pill')).forEach(function (p) {
        p.remove();
      });
    }

    function renderPills() {
      removePills();
      selectedValues().forEach(function (value) {
        var opt = allOptions.find(function (o) { return o.value === value; });
        if (!opt) return;

        var pill = document.createElement('span');
        pill.className = 'hitalx-pw-pill badge bg-primary';
        pill.dataset.value = value;

        var label = document.createTextNode(opt.label + '\u00a0');
        pill.appendChild(label);

        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'hitalx-pw-pill-remove';
        x.setAttribute('aria-label', 'Remove ' + opt.label);
        x.textContent = '\u00d7';
        x.addEventListener('click', function (e) {
          e.stopPropagation();
          setSelected(value, false);
          renderPills();
          renderDropdown(searchInput.value);
        });
        pill.appendChild(x);
        pillBox.insertBefore(pill, searchInput);
      });
    }

    function renderDropdown(query) {
      var q = (query || '').toLowerCase().trim();
      var selected = selectedValues();

      var matches = allOptions.filter(function (o) {
        if (selected.indexOf(o.value) !== -1) return false; // already a pill
        if (!q) return true;
        return o.label.toLowerCase().indexOf(q) !== -1;
      });

      dropdown.innerHTML = '';

      if (matches.length === 0) {
        dropdown.style.display = 'none';
        return;
      }

      matches.slice(0, 30).forEach(function (o) {
        var item = document.createElement('div');
        item.className = 'hitalx-pw-item';
        // Highlight matching portion
        if (q) {
          var idx = o.label.toLowerCase().indexOf(q);
          item.appendChild(document.createTextNode(o.label.slice(0, idx)));
          var mark = document.createElement('mark');
          mark.textContent = o.label.slice(idx, idx + q.length);
          item.appendChild(mark);
          item.appendChild(document.createTextNode(o.label.slice(idx + q.length)));
        } else {
          item.textContent = o.label;
        }
        item.addEventListener('mousedown', function (e) {
          e.preventDefault(); // keep focus on input
          setSelected(o.value, true);
          searchInput.value = '';
          renderPills();
          renderDropdown('');
          searchInput.focus();
        });
        dropdown.appendChild(item);
      });

      dropdown.style.display = 'block';
    }

    // ── events ─────────────────────────────────────────────────────────────

    searchInput.addEventListener('input', function () {
      renderDropdown(this.value);
    });

    searchInput.addEventListener('focus', function () {
      renderDropdown(this.value);
    });

    searchInput.addEventListener('blur', function () {
      // Short delay so mousedown on a dropdown item fires first
      setTimeout(function () { dropdown.style.display = 'none'; }, 200);
    });

    searchInput.addEventListener('keydown', function (e) {
      // Remove last pill on Backspace when input is empty
      if (e.key === 'Backspace' && this.value === '') {
        var pills = pillBox.querySelectorAll('.hitalx-pw-pill');
        if (pills.length > 0) {
          var last = pills[pills.length - 1];
          setSelected(last.dataset.value, false);
          renderPills();
          renderDropdown('');
        }
      }
      // Close on Escape
      if (e.key === 'Escape') {
        dropdown.style.display = 'none';
      }
    });

    pillBox.addEventListener('click', function (e) {
      if (e.target === pillBox || e.target === searchInput) {
        searchInput.focus();
      }
    });

    // ── initial render ─────────────────────────────────────────────────────
    renderPills();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
