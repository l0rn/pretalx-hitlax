from decimal import Decimal

from django import template
from django.db.models import Sum

register = template.Library()


@register.filter(name="total_expenses")
def total_expenses(user):
    amount = Decimal(user.expenses.all().aggregate(Sum("amount"))["amount__sum"] or 0)
    return amount


@register.filter(name="paid_expenses")
def paid_expenses(user):
    amount = Decimal(
        user.expenses.filter(paid=True).aggregate(Sum("amount"))["amount__sum"] or 0
    )
    return amount


@register.filter(name="euro_amount")
def euro_amount(amount):
    return f"{amount:.2f} €".replace(".", ",")
