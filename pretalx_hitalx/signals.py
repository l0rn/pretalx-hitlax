# Register your receivers here
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext as _
from pretalx.common.signals import activitylog_display
from pretalx.orga.signals import nav_event


@receiver(nav_event, dispatch_uid="speakers_expenses")
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
            "active": url.namespace == "plugins:pretalx_hitalx"
            and url.url_name == "speakers_by_expense.view",
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

@receiver(nav_event, dispatch_uid='tours')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [{
        'label': _('Tours'),
        'icon': 'bus',
        'url': reverse('plugins:pretalx_hitalx:tours.view', kwargs={
            'event': request.event.slug,
        }),
        'active': url.namespace == 'plugins:pretalx_hitalx' and url.url_name == 'tours.view',
    }]

