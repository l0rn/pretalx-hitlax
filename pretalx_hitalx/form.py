from django.forms import ModelForm, CharField

from pretalx.common.mixins.forms import ReadOnlyFlag
from .models import ExpenseItem


class SpeakerExpenseForm(ReadOnlyFlag, ModelForm):
    description = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker'].disabled = True
        self.fields['paid'].disabled = True

    class Meta:
        model = ExpenseItem
        fields = ['speaker', 'description', 'amount', 'paid', 'reference', 'notes']
        readonly_fields = ['speaker', 'paid']

