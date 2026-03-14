// SPDX-FileCopyrightText: 2026 Jonatan Zint
// SPDX-License-Identifier: Apache-2.0
//
// Renders tag distribution donut charts on the submissions statistics page.
// Injected as a deferred script (via html_head signal) only on the stats page,
// after apexcharts.min.js and stats.js — so ApexCharts is available immediately.

(function () {
  var SCOPES = ['all', 'accepted'];

  function renderTagCharts() {
    var statsDiv = document.getElementById('stats');
    var container = document.getElementById('hitalx-tag-charts');
    if (!statsDiv || !container) return;

    // Move our flex row into #stats so it shares the same layout context and styling
    statsDiv.appendChild(container);

    SCOPES.forEach(function (scope) {
      var dataEl = document.getElementById('hitalx-tag-' + scope + '-data');
      var chartEl = document.getElementById('hitalx-tag-' + scope);
      if (!dataEl || !chartEl) return;

      var raw = dataEl.dataset.states;
      if (!raw) return;
      var data = JSON.parse(raw);
      if (!data.length) return;

      var series = data.map(function (e) { return e.value; });
      var labels = data.map(function (e) { return e.label; });

      var options = {
        series: series,
        labels: labels,
        chart: {
          width: chartEl.clientWidth > 50 ? chartEl.clientWidth - 50 : 400,
          redrawOnParentResize: true,
          type: 'donut',
        },
        dataLabels: { enabled: false },
        legend: {
          formatter: function (val, opts) {
            if (val.length > 20) val = val.slice(0, 19) + '\u2026';
            return val + ' \u2013 ' + opts.w.globals.series[opts.seriesIndex];
          },
        },
        plotOptions: {
          pie: {
            donut: {
              labels: {
                show: true,
                name: {
                  formatter: function (val) {
                    if (val.length < 16) return val;
                    return val.slice(0, 15) + '\u2026';
                  },
                },
              },
            },
          },
        },
        tooltip: { enabled: false },
        responsive: [
          {
            breakpoint: 480,
            options: { chart: { width: 300 }, legend: { position: 'bottom' } },
          },
        ],
      };

      new ApexCharts(chartEl, options).render();
    });
  }

  // Deferred scripts run after DOM is parsed and after all preceding deferred scripts
  // (apexcharts.min.js, stats.js) — execute immediately, no need for event listeners.
  renderTagCharts();
})();
