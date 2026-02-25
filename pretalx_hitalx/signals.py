# Register your receivers here
from django.dispatch import receiver
from django.urls import resolve, reverse
from django_scopes import scope
from django.utils.translation import gettext as _
from pretalx.common.signals import activitylog_display
from pretalx.orga.signals import nav_event, nav_event_settings, speaker_form


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
