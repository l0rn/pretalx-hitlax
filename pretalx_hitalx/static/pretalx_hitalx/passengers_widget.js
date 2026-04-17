/**
 * Pill / autocomplete widget for any <select multiple class="hitalx-pw-select">.
 *
 * Structure built on top of the hidden <select multiple>:
 *
 *   .hitalx-pw-wrapper
 *     .hitalx-pw-input-row          ← position:relative anchor for dropdown
 *       input.form-control           ← search / filter (never moves)
 *       .hitalx-pw-dropdown          ← floating option list
 *     .hitalx-pw-pills               ← selected speakers as removable pills
 */
(function () {
  function initOne(hiddenSelect) {
    // Guard against double-init
    if (hiddenSelect.dataset.pwInit) return;
    hiddenSelect.dataset.pwInit = '1';

    var allOptions = Array.from(hiddenSelect.options).map(function (o) {
      return { value: o.value, label: o.text };
    });

    hiddenSelect.style.display = 'none';

    /* ── build DOM ── */
    var wrapper = document.createElement('div');
    wrapper.className = 'hitalx-pw-wrapper';
    hiddenSelect.parentNode.insertBefore(wrapper, hiddenSelect);

    // Input row (position:relative so dropdown is positioned against it)
    var inputRow = document.createElement('div');
    inputRow.className = 'hitalx-pw-input-row';
    wrapper.appendChild(inputRow);

    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control';
    searchInput.placeholder = 'Add\u2026';
    searchInput.autocomplete = 'off';
    searchInput.spellcheck = false;
    inputRow.appendChild(searchInput);

    var dropdown = document.createElement('div');
    dropdown.className = 'hitalx-pw-dropdown';
    dropdown.style.display = 'none';
    inputRow.appendChild(dropdown);

    // Pills row (below the input, never causes the input to shift)
    var pillRow = document.createElement('div');
    pillRow.className = 'hitalx-pw-pills';
    wrapper.appendChild(pillRow);

    /* ── helpers ── */
    function selectedValues() {
      return Array.from(hiddenSelect.options)
        .filter(function (o) { return o.selected; })
        .map(function (o) { return o.value; });
    }

    function setSelected(value, selected) {
      var opt = hiddenSelect.querySelector('option[value="' + CSS.escape(value) + '"]');
      if (opt) opt.selected = selected;
    }

    function renderPills() {
      pillRow.innerHTML = '';
      selectedValues().forEach(function (value) {
        var opt = allOptions.find(function (o) { return o.value === value; });
        if (!opt) return;

        var pill = document.createElement('span');
        pill.className = 'hitalx-pw-pill';
        pill.dataset.value = value;

        pill.appendChild(document.createTextNode(opt.label));

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'hitalx-pw-pill-remove';
        btn.setAttribute('aria-label', 'Remove ' + opt.label);
        btn.textContent = '\u00d7';
        btn.addEventListener('click', function () {
          setSelected(value, false);
          renderPills();
          renderDropdown(searchInput.value);
        });
        pill.appendChild(btn);
        pillRow.appendChild(pill);
      });
    }

    function renderDropdown(query) {
      var q = (query || '').toLowerCase().trim();
      var selected = selectedValues();

      var matches = allOptions.filter(function (o) {
        if (selected.indexOf(o.value) !== -1) return false;
        return !q || o.label.toLowerCase().indexOf(q) !== -1;
      });

      dropdown.innerHTML = '';

      if (matches.length === 0) {
        dropdown.style.display = 'none';
        return;
      }

      matches.slice(0, 30).forEach(function (o) {
        var item = document.createElement('div');
        item.className = 'hitalx-pw-item';

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
          e.preventDefault();
          setSelected(o.value, true);
          searchInput.value = '';
          renderPills();
          dropdown.style.display = 'none';
          searchInput.focus();
        });
        dropdown.appendChild(item);
      });

      dropdown.style.display = 'block';
    }

    /* ── events ── */
    searchInput.addEventListener('input', function () {
      renderDropdown(this.value);
    });

    searchInput.addEventListener('focus', function () {
      renderDropdown(this.value);
    });

    searchInput.addEventListener('blur', function () {
      setTimeout(function () { dropdown.style.display = 'none'; }, 200);
    });

    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && this.value === '') {
        var pills = pillRow.querySelectorAll('.hitalx-pw-pill');
        if (pills.length > 0) {
          var last = pills[pills.length - 1];
          setSelected(last.dataset.value, false);
          renderPills();
          renderDropdown('');
        }
      }
      if (e.key === 'Escape') {
        dropdown.style.display = 'none';
      }
    });

    /* ── initial render ── */
    renderPills();
  }

  function initAll() {
    document.querySelectorAll('.hitalx-pw-select').forEach(initOne);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
