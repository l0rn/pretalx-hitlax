# Register your receivers here
import json
from collections import Counter

from django.dispatch import receiver
from django.urls import resolve, reverse
from django_scopes import scope
from django.utils.translation import gettext as _
from django.utils.html import format_html
from pretalx.common.signals import activitylog_display
from pretalx.orga.signals import nav_event, nav_event_settings, speaker_form, html_below_orga_page
from pretalx.submission.models import SubmissionStates


@receiver(nav_event, dispatch_uid="hitalx_nav")
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            "label": _("Speaker expenses"),
            "icon": "dollar",
            "url": reverse(
                "plugins:pretalx_hitalx:speakers_by_expense.view",
                kwargs={
                    "event": request.event.slug,
                },
            ),
            "active": url.namespace == "plugins:pretalx_hitalx" and url.url_name == "speakers_by_expense.view",
        },
        {
            'label': _('Tours'),
            'icon': 'bus',
            'url': reverse('plugins:pretalx_hitalx:tours.view', kwargs={
                'event': request.event.slug,
            }),
            'active': url.namespace == 'plugins:pretalx_hitalx' and url.url_name == 'tours.view',
        },
        {
            'label': _('Tours export'),
            'icon': 'bus',
            'url': reverse('plugins:pretalx_hitalx:tours.export', kwargs={
                'event': request.event.slug,
            }),
            'active': url.namespace == 'plugins:pretalx_hitalx' and url.url_name == 'tours.export',
        }
    ]


PLUGIN_ACTION_TYPES = {
    "pretalx_hitalx.expense_item.edit": _("Speaker expense was edited"),
    "pretalx_hitalx.expense_item.create": _("Speaker expense was created"),
    "pretalx_hitalx.expense_item.mark": _("Expense paid status was changed"),
}


@receiver(activitylog_display)
def default_activitylog_display(sender, activitylog, **kwargs):
    if activitylog.action_type in PLUGIN_ACTION_TYPES:
        return f"{PLUGIN_ACTION_TYPES[activitylog.action_type]} ({activitylog.data})"



from .form import SpeakerExpensesInlineForm, SpeakerToursForm



@receiver(speaker_form, dispatch_uid="hitalx_speaker_inline_forms")
def speaker_inline_forms(sender, request, instance, **kwargs):
    if not instance:
        return []

    # Current pretalx speaker form passes a User instance here.
    user = getattr(instance, "user", None) and instance.user or instance
    profile = getattr(instance, "event", None) and instance or user.event_profile(sender)
    data = request.POST if request.method == "POST" else None

    with scope(event=sender):
        return [
            SpeakerExpensesInlineForm(
                data=data,
                prefix="hitalx_expense_inline",
                speaker=user,
                event=sender,
            ),
            SpeakerToursForm(
                data=data,
                instance=profile,
                prefix="hitalx_tours_inline",
            ),
        ]


@receiver(nav_event_settings, dispatch_uid="hitalx_nav_settings")
def hitalx_settings_nav(sender, request, **kwargs):
    return [{
        "label": _("Shuttle export permissions"),
        "url": reverse("plugins:pretalx_hitalx:tours.export.settings", kwargs={"event": request.event.slug}),
        "active": request.path_info.endswith('/settings/plugins/hitalx/shuttle-export/'),
    }]


@receiver(html_below_orga_page, dispatch_uid="hitalx_tag_statistics")
def tag_statistics_charts(sender, request, **kwargs):
    """Inject tag distribution pie charts on the submissions statistics page."""
    url = resolve(request.path_info)
    if url.namespace != "orga" or url.url_name != "submissions.statistics":
        return ""

    event = request.event
    tags = list(event.tags.order_by("tag"))
    if not tags:
        return ""

    # All submissions (excluding deleted/draft)
    all_subs = event.submissions.exclude(
        state__in=[SubmissionStates.DELETED, SubmissionStates.DRAFT]
    ).prefetch_related("tags")

    # Accepted + confirmed submissions
    accepted_subs = event.submissions.filter(
        state__in=SubmissionStates.accepted_states
    ).prefetch_related("tags")

    def count_by_tag(submissions, tags):
        tag_ids = {t.id: t.tag for t in tags}
        counter = Counter()
        for sub in submissions:
            for tag in sub.tags.all():
                if tag.id in tag_ids:
                    counter[tag_ids[tag.id]] += 1
        # Include tags with 0 count so all tags show up
        result = [{"label": t.tag, "value": counter.get(t.tag, 0)} for t in tags]
        return result

    all_data = json.dumps(count_by_tag(all_subs, tags))
    accepted_data = json.dumps(count_by_tag(accepted_subs, tags))

    return f"""
<div class="card mt-4">
  <div class="card-header">{_("Proposals by tag (all submissions)")}</div>
  <div id="hitalx-tag-all-data" class="d-none" data-states="{all_data.replace('"', '&quot;')}"></div>
  <div id="hitalx-tag-all" class="pie card-body" style="min-height:300px"></div>
</div>
<div class="card mt-4">
  <div class="card-header">{_("Proposals by tag (accepted &amp; confirmed)")}</div>
  <div id="hitalx-tag-accepted-data" class="d-none" data-states="{accepted_data.replace('"', '&quot;')}"></div>
  <div id="hitalx-tag-accepted" class="pie card-body" style="min-height:300px"></div>
</div>
<script>
(function() {{
  function drawHitalxTagCharts() {{
    if (typeof ApexCharts === 'undefined') {{
      setTimeout(drawHitalxTagCharts, 50);
      return;
    }}
    ['all', 'accepted'].forEach(function(scope) {{
      var dataEl = document.getElementById('hitalx-tag-' + scope + '-data');
      var chartEl = document.getElementById('hitalx-tag-' + scope);
      if (!dataEl || !chartEl) return;
      var data = JSON.parse(dataEl.dataset.states);
      var series = data.map(function(e) {{ return e.value; }});
      var labels = data.map(function(e) {{ return e.label; }});
      var options = {{
        series: series,
        labels: labels,
        chart: {{
          width: chartEl.clientWidth - 50 || 500,
          redrawOnParentResize: true,
          type: 'donut',
        }},
        dataLabels: {{ enabled: false }},
        legend: {{
          formatter: function(val, opts) {{
            if (val.length > 20) val = val.slice(0, 19) + '\u2026';
            return val + ' - ' + opts.w.globals.series[opts.seriesIndex];
          }}
        }},
        plotOptions: {{
          pie: {{
            donut: {{
              labels: {{
                show: true,
                name: {{
                  formatter: function(val) {{
                    if (val.length < 16) return val;
                    return val.slice(0, 15) + '\u2026';
                  }}
                }}
              }}
            }}
          }}
        }},
        tooltip: {{ enabled: false }},
        responsive: [{{
          breakpoint: 480,
          options: {{ chart: {{ width: 300 }}, legend: {{ position: 'bottom' }} }}
        }}]
      }};
      new ApexCharts(chartEl, options).render();
    }});
  }}
  window.addEventListener('load', drawHitalxTagCharts);
}})();
</script>
"""
