from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext as _
from pretalx.common.signals import activitylog_display
from pretalx.orga.signals import nav_event, speaker_form


@receiver(nav_event, dispatch_uid="hitalx_nav")
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_perm("person.orga_list_speakerprofile", request.event):
        return []
    return [
        {
            "label": _("Speaker expenses"),
            "icon": "money-bill-wave",
            "url": reverse(
                "plugins:pretalx_hitalx:speakers_by_expense.view",
                kwargs={
                    "event": request.event.slug,
                },
            ),
            "active": url.namespace == "plugins:pretalx_hitalx"
            and url.url_name == "speakers_by_expense.view",
        },
        {
            "label": _("Tours"),
            "icon": "bus",
            "url": reverse(
                "plugins:pretalx_hitalx:tours.view",
                kwargs={
                    "event": request.event.slug,
                },
            ),
            "active": url.namespace == "plugins:pretalx_hitalx"
            and url.url_name == "tours.view",
        },
        {
            "label": _("Tours export"),
            "icon": "bus",
            "url": reverse(
                "plugins:pretalx_hitalx:tours.export",
                kwargs={
                    "event": request.event.slug,
                },
            ),
            "active": url.namespace == "plugins:pretalx_hitalx"
            and url.url_name == "tours.export",
        },
    ]


@receiver(speaker_form, dispatch_uid="hitalx_speaker_form")
def hitalx_speaker_form(sender, request, instance, **kwargs):
    from .form import SpeakerToursForm

    return SpeakerToursForm(
        instance=instance,
        event=request.event,
        data=request.POST if request.method == "POST" and "hitalx_tours-tours" in request.POST else None,
        prefix="hitalx_tours",
    )


PLUGIN_ACTION_TYPES = {
    "pretalx_hitalx.expense_item.edit": _("Speaker expense was edited"),
    "pretalx_hitalx.expense_item.create": _("Speaker expense was created"),
    "pretalx_hitalx.expense_item.mark": _("Expense paid status was changed"),
}


@receiver(activitylog_display)
def default_activitylog_display(sender, activitylog, **kwargs):
    if activitylog.action_type in PLUGIN_ACTION_TYPES:
        return f"{PLUGIN_ACTION_TYPES[activitylog.action_type]} ({activitylog.data})"
