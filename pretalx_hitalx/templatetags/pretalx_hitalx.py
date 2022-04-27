from decimal import Decimal

from django import template
from django.db.models import Sum

register = template.Library()


@register.filter(name='total_expenses')
def total_expenses(user):
    amount = Decimal(user.expenses.all().aggregate(Sum('amount'))['amount__sum'] or 0)
    return f'{amount:.2f} €'.replace('.', ',')

