from django.db import models
from django.utils.translation import ugettext as _
from pretalx.common.mixins.models import LogMixin
from pretalx.person.models import User


class ExpenseItem(LogMixin, models.Model):
    description = models.TextField(blank=False, null=False)
    amount = models.DecimalField(
        blank=False, null=False, decimal_places=2, max_digits=60
    )
    speaker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    notes = models.TextField(blank=True, default="")
    reference = models.URLField(blank=True, null=True, verbose_name=_("Reference URL"))
    paid = models.BooleanField(default=False)
