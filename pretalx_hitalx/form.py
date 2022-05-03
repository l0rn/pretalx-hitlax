from django import forms
from django.forms import CharField, ModelForm
from pretalx.common.mixins.forms import ReadOnlyFlag
from pretalx.person.models import SpeakerProfile

from .models import ExpenseItem
from .models import Tour

class SpeakerExpenseForm(ReadOnlyFlag, ModelForm):
    description = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["speaker"].disabled = True
        self.fields["paid"].disabled = True

    class Meta:
        model = ExpenseItem
        fields = ["speaker", "description", "amount", "paid", "reference", "notes"]
        readonly_fields = ["speaker", "paid"]


class SpeakerToursForm(ReadOnlyFlag, ModelForm):
    tours = forms.ModelMultipleChoiceField(
         queryset=Tour.objects.all(),
         widget=forms.SelectMultiple(attrs={"class": "select2"}),
    )

    class Meta:
        model = SpeakerProfile
        fields = ["tours"]

