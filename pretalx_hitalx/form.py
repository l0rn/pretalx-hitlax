from django import forms
from django.forms import CharField, ModelForm
from django_scopes.forms import SafeModelMultipleChoiceField
from django_scopes import scope
from pretalx.common.mixins.forms import ReadOnlyFlag
from pretalx.event.models import Event
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
        queryset=Tour.objects.all().order_by('departure_time'),
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
    )

    def save(self, *args, **kwargs):
        instance = self.instance
        if "tours" in self.changed_data:
            instance.tours.set(self.cleaned_data["tours"])

    def __init__(self, *args, **kwargs):
        super(SpeakerToursForm, self).__init__(*args, **kwargs)
        self.initial['tours'] = kwargs['instance'].tours.all()

    class Meta:
        model = SpeakerProfile
        fields = ["tours"]
        field_classes = {
            "tours": SafeModelMultipleChoiceField,
        }


class PassengerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.user.get_display_name()


class TourForm(ReadOnlyFlag, ModelForm):
    description = CharField()
    start_location = CharField()
    departure_time = forms.DateTimeField()
    passengers = PassengerChoiceField(
        queryset=SpeakerProfile.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        blank=True,
        required=False
    )

    def __init__(self, *args, user=None, locales=None, organiser=None, **kwargs):
        super().__init__(*args, **kwargs)
        with scope(event=Event.objects.get(id=kwargs['initial'].get('event', None))):
            self.fields["passengers"].queryset = SpeakerProfile.objects.all()
        self.fields["departure_time"].widget.attrs["class"] = "datetimepickerfield"

    class Meta:
        model = Tour
        fields = ["description", "departure_time", "start_location", "type", "event", "passengers"]
        widgets = {'event': forms.HiddenInput(), 'passengers': forms.SelectMultiple()}
        field_classes = {
            "passengers": SafeModelMultipleChoiceField,
        }
