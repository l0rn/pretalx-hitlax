from django import forms
from django.forms import CharField, ModelForm
from django.utils.translation import gettext_lazy as _
from django_scopes.forms import SafeModelMultipleChoiceField
from django_scopes import scope
from pretalx.common.forms.mixins import ReadOnlyFlag
from pretalx.event.models import Event
from pretalx.person.models import SpeakerProfile

from .models import ExpenseItem, Tour


class SpeakerExpenseForm(ReadOnlyFlag, ModelForm):
    description = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["speaker"].disabled = True
        if "paid" in self.fields:
            self.fields["paid"].disabled = True

    class Meta:
        model = ExpenseItem
        fields = ["speaker", "description", "amount", "paid", "reference", "notes"]
        readonly_fields = ["speaker", "paid"]


class SpeakerToursForm(ReadOnlyFlag, ModelForm):
    label = _("Tours")
    tours = SafeModelMultipleChoiceField(
        queryset=Tour.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        required=False,
    )

    def save(self, *args, **kwargs):
        instance = self.instance
        if "tours" in self.changed_data:
            instance.tours.set(self.cleaned_data["tours"])

    def __init__(self, *args, **kwargs):
        event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)
        if not event and self.instance.pk:
            event = self.instance.event

        if event:
            self.fields["tours"].queryset = Tour.objects.filter(event=event).order_by("departure_time")

        if self.instance.pk:
            self.initial["tours"] = self.instance.tours.all()

    class Meta:
        model = SpeakerProfile
        fields = ["tours"]


class PassengerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.user.get_display_name()


class TourForm(ReadOnlyFlag, ModelForm):
    description = CharField()
    start_location = CharField()
    departure_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"class": "datetimepickerfield"})
    )
    passengers = PassengerChoiceField(
        queryset=SpeakerProfile.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        blank=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)
        if not event and "initial" in kwargs and "event" in kwargs["initial"]:
            event = Event.objects.filter(id=kwargs["initial"]["event"]).first()

        if event:
            with scope(event=event):
                self.fields["passengers"].queryset = SpeakerProfile.objects.all()

        if "event" in self.fields:
            self.fields["event"].widget = forms.HiddenInput()

    class Meta:
        model = Tour
        fields = [
            "description",
            "departure_time",
            "start_location",
            "type",
            "event",
            "passengers",
        ]
        field_classes = {
            "passengers": SafeModelMultipleChoiceField,
        }
