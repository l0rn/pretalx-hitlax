from enum import Enum

from django.db import models
from django.utils.translation import ugettext as _
from pretalx.common.mixins.models import LogMixin
from pretalx.event.models import Event
from pretalx.person.models import User, SpeakerProfile


class TourType(Enum):
    BASSLINER = 'BASSLINER'
    SHUTTLE = 'SHUTTLE'


TOUR_TYPE_CHOICES = [
    (TourType.SHUTTLE.value, _('Shuttle')),
    (TourType.BASSLINER.value, _('Bassliner')),
]


class ExpenseItem(LogMixin, models.Model):
    description = models.TextField(blank=False, null=False)
    amount = models.DecimalField(
        blank=False, null=False, decimal_places=2, max_digits=60
    )
    speaker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    notes = models.TextField(blank=True, default="")
    reference = models.URLField(blank=True, null=True, verbose_name=_("Reference URL"))
    paid = models.BooleanField(default=False)


class Tour(models.Model):
    description = models.TextField(blank=False, null=False)
    departure_time = models.DateTimeField(null=False, blank=False)
    start_location = models.TextField(null=False, blank=False)
    passengers = models.ManyToManyField(SpeakerProfile, related_name='tours')
    type = models.TextField(choices=TOUR_TYPE_CHOICES)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.type} - {self.description} - {self.start_location} - {self.departure_time}'
