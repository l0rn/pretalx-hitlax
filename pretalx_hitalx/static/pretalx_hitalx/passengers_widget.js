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
        btn.addEventListener('mousedown', function (e) {
          // Prevent the button from stealing focus from searchInput,
          // which would trigger a spurious focus→renderDropdown cycle.
          e.preventDefault();
        });
        btn.addEventListener('click', function () {
          setSelected(value, false);
          renderPills();
          closeDropdown();
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

    /* ── helpers ── */
    function closeDropdown() {
      dropdown.style.display = 'none';
    }

    /* ── events ── */
    searchInput.addEventListener('input', function () {
      renderDropdown(this.value);
    });

    searchInput.addEventListener('focus', function () {
      renderDropdown(this.value);
    });

    searchInput.addEventListener('blur', function () {
      // Delay so mousedown on a dropdown item fires first (item selection via mousedown)
      setTimeout(closeDropdown, 200);
    });

    // Close when clicking anything outside the widget (capture phase fires before
    // any inner handlers, ensuring the dropdown is already hidden by the time
    // inner click handlers run if the click was outside)
    document.addEventListener('mousedown', function (e) {
      if (!wrapper.contains(e.target)) {
        closeDropdown();
      }
    }, true);

    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && this.value === '') {
        var pills = pillRow.querySelectorAll('.hitalx-pw-pill');
        if (pills.length > 0) {
          var last = pills[pills.length - 1];
          setSelected(last.dataset.value, false);
          renderPills();
          closeDropdown();
        }
      }
      if (e.key === 'Escape') {
        closeDropdown();
      }
    });

    /* ── initial render ── */
    renderPills();
  }

  function initAll() {
    document.querySelectorAll('.hitalx-pw-select').forEach(initOne);
  }

  /* ── Single-select autocomplete for <select class="hitalx-ss-select"> ── */
  function initSingleSelect(sel) {
    if (sel.dataset.ssInit) return;
    sel.dataset.ssInit = '1';

    var allOptions = Array.from(sel.options)
      .filter(function (o) { return o.value !== ''; })
      .map(function (o) { return { value: o.value, label: o.text.trim() }; });

    sel.style.display = 'none';

    var wrapper = document.createElement('div');
    wrapper.className = 'hitalx-pw-wrapper';
    sel.parentNode.insertBefore(wrapper, sel);

    var inputRow = document.createElement('div');
    inputRow.className = 'hitalx-pw-input-row';
    wrapper.appendChild(inputRow);

    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control';
    searchInput.placeholder = 'Search\u2026';
    searchInput.autocomplete = 'off';
    searchInput.spellcheck = false;
    inputRow.appendChild(searchInput);

    var dropdown = document.createElement('div');
    dropdown.className = 'hitalx-pw-dropdown';
    dropdown.style.display = 'none';
    inputRow.appendChild(dropdown);

    var pillRow = document.createElement('div');
    pillRow.className = 'hitalx-pw-pills';
    wrapper.appendChild(pillRow);

    function getSelected() {
      return sel.value ? allOptions.find(function (o) { return o.value === sel.value; }) : null;
    }

    function clearSelection() {
      sel.value = '';
      searchInput.value = '';
      searchInput.style.display = '';
      renderPill();
    }

    function renderPill() {
      pillRow.innerHTML = '';
      var chosen = getSelected();
      if (!chosen) return;

      searchInput.style.display = 'none';

      var pill = document.createElement('span');
      pill.className = 'hitalx-pw-pill';

      pill.appendChild(document.createTextNode(chosen.label));

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'hitalx-pw-pill-remove';
      btn.textContent = '\u00d7';
      btn.addEventListener('mousedown', function (e) { e.preventDefault(); });
      btn.addEventListener('click', clearSelection);
      pill.appendChild(btn);
      pillRow.appendChild(pill);
    }

    function renderDropdown(query) {
      var q = (query || '').toLowerCase().trim();
      var matches = allOptions.filter(function (o) {
        return !q || o.label.toLowerCase().indexOf(q) !== -1;
      });

      dropdown.innerHTML = '';
      if (matches.length === 0) { dropdown.style.display = 'none'; return; }

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
          sel.value = o.value;
          searchInput.value = '';
          dropdown.style.display = 'none';
          renderPill();
        });
        dropdown.appendChild(item);
      });
      dropdown.style.display = 'block';
    }

    searchInput.addEventListener('input', function () { renderDropdown(this.value); });
    searchInput.addEventListener('focus', function () { renderDropdown(this.value); });
    searchInput.addEventListener('blur', function () { setTimeout(function () { dropdown.style.display = 'none'; }, 200); });
    searchInput.addEventListener('keydown', function (e) { if (e.key === 'Escape') dropdown.style.display = 'none'; });

    document.addEventListener('mousedown', function (e) {
      if (!wrapper.contains(e.target)) dropdown.style.display = 'none';
    }, true);

    renderPill();
  }

  function initAllSingleSelects() {
    document.querySelectorAll('.hitalx-ss-select').forEach(initSingleSelect);
  }

  /* ── POST-button handler (avoids nested <form> elements) ──
   * Buttons with data-post-url submit a dynamically created form
   * appended to <body>, safely outside any existing form.
   */
  function initPostButtons() {
    document.querySelectorAll('[data-post-url]').forEach(function (btn) {
      if (btn.dataset.postInit) return;
      btn.dataset.postInit = '1';
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var url = btn.dataset.postUrl;
        var csrf = btn.dataset.csrf;
        var form = document.createElement('form');
        form.method = 'post';
        form.action = url;
        var inp = document.createElement('input');
        inp.type = 'hidden';
        inp.name = 'csrfmiddlewaretoken';
        inp.value = csrf;
        form.appendChild(inp);
        document.body.appendChild(form);
        form.submit();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initAll();
      initAllSingleSelects();
      initPostButtons();
    });
  } else {
    initAll();
    initAllSingleSelects();
    initPostButtons();
  }
})();
