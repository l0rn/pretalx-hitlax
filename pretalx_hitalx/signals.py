# Register your receivers here
from django.db.models import Sum
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext as _

from pretalx.orga.signals import nav_event
from pretalx.person.models import User


@receiver(nav_event, dispatch_uid='speakers_expenses')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [{
        'label': _('Speaker expenses'),
        'icon': 'dollar',
        'url': reverse('plugins:pretalx_hitalx:speakers_by_expense.view', kwargs={
            'event': request.event.slug,
        }),
        'active': url.namespace == 'plugins:pretalx_hitalx' and url.url_name == 'speakers_by_expense.view',
    }]

