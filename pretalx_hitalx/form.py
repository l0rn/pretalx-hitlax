from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.formats import date_format
from django.utils.timezone import localtime
from django.utils.safestring import mark_safe
from django.forms import CharField, ModelForm, modelformset_factory
from django.db.models import Sum
from django_scopes.forms import SafeModelMultipleChoiceField
from django_scopes import scope
from pretalx.common.forms.mixins import ReadOnlyFlag
from pretalx.event.models import Event
from pretalx.person.models import SpeakerProfile

from .models import ExpenseItem
from .models import Tour


class SpeakerExpenseForm(ReadOnlyFlag, ModelForm):
    description = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["speaker"].disabled = True
        self.fields["reference"].label = _("Reference (URL)")

    class Meta:
        model = ExpenseItem
        fields = ["speaker", "description", "amount", "paid", "reference", "notes"]
        readonly_fields = ["speaker"]


class TourChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        when = date_format(localtime(obj.departure_time), format="SHORT_DATETIME_FORMAT")
        return f"{obj.description} — {when}"


class SpeakerToursForm(ModelForm):
    label = _("Tours")
    tours = TourChoiceField(
        queryset=Tour.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    def save(self, *args, **kwargs):
        instance = self.instance
        if "tours" in self.changed_data:
            instance.tours.set(self.cleaned_data["tours"])
        return instance

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        if instance:
            with scope(event=instance.event):
                self.fields["tours"].queryset = Tour.objects.filter(event=instance.event).order_by("departure_time")
                self.initial["tours"] = instance.tours.all()

    class Meta:
        model = SpeakerProfile
        fields = ["tours"]
        field_classes = {
            "tours": SafeModelMultipleChoiceField,
        }


class PassengerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.user.get_display_name()


class TourForm(ModelForm):
    description = CharField()
    start_location = CharField()
    departure_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}, format="%Y-%m-%dT%H:%M"))
    passengers = PassengerChoiceField(
        queryset=SpeakerProfile.objects.none(),
        widget=forms.SelectMultiple(attrs={
            "class": "hitalx-pw-select",
        }),
        blank=True,
        required=False,
    )

    def __init__(self, *args, user=None, locales=None, organiser=None, **kwargs):
        initial = kwargs.get("initial", {}) or {}
        super().__init__(*args, **kwargs)
        event_id = initial.get("event") or getattr(self.instance, "event_id", None)
        if event_id:
            with scope(event=Event.objects.get(id=event_id)):
                self.fields["passengers"].queryset = SpeakerProfile.objects.all().order_by("user__name")

    class Meta:
        model = Tour
        fields = ["description", "departure_time", "start_location", "notes", "type", "event", "passengers"]
        labels = {
            "start_location": _("Start location"),
            "notes": _("Notes"),
        }
        widgets = {
            'event': forms.HiddenInput(),
            'notes': forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        field_classes = {
            "passengers": SafeModelMultipleChoiceField,
        }


class SpeakerToursInlineForm:
    """Editable pill-widget for assigning tours to a speaker on the admin speaker detail page."""
    label = _("Tours")

    def __init__(self, *args, speaker=None, instance=None, data=None, prefix="hitalx_tours", **kwargs):
        self.profile = instance  # SpeakerProfile
        self.prefix = prefix
        self.data = data
        self._errors = {}
        self._is_valid = None
        self._selected_ids = None  # None means "not yet parsed from POST"

        self._all_tours = []
        self._current_ids = set()
        if self.profile:
            with scope(event=self.profile.event):
                self._all_tours = list(
                    Tour.objects.filter(event=self.profile.event).order_by("departure_time")
                )
                self._current_ids = set(self.profile.tours.values_list("id", flat=True))

    def is_valid(self):
        if self._is_valid is not None:
            return self._is_valid
        if self.data is None:
            self._is_valid = True
            return True
        field_name = f"{self.prefix}-selected"
        raw = self.data.getlist(field_name)
        try:
            self._selected_ids = [int(x) for x in raw if x]
        except (ValueError, TypeError):
            self._errors = {"tours": [str(_("Invalid selection"))]}
            self._is_valid = False
            return False
        self._is_valid = True
        return True

    @property
    def errors(self):
        return self._errors

    def save(self):
        if not self.profile or self._selected_ids is None:
            return None
        self.profile.tours.set(self._selected_ids)
        return self.profile

    def _render(self):
        if not self.profile:
            return mark_safe('<p class="text-muted"><em>' + str(_("No tours assigned.")) + '</em></p>')

        field_name = f"{self.prefix}-selected"
        options = ""
        for tour in self._all_tours:
            when = date_format(localtime(tour.departure_time), format="SHORT_DATETIME_FORMAT")
            loc = str(_("Start location")) + ": " + tour.start_location
            label = f"{tour.description} — {when} — {loc}"
            sel = ' selected' if tour.id in self._current_ids else ''
            options += f'<option value="{tour.id}"{sel}>{label}</option>'

        html = f'<select multiple name="{field_name}" class="hitalx-pw-select">{options}</select>'
        return mark_safe(html)

    def __html__(self):
        return self._render()

    def __str__(self):
        return str(self._render())




class ExpenseItemInlineForm(ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ["description", "amount", "reference", "notes", "paid"]
        labels = {"reference": _("Reference (URL)")}
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "reference": forms.URLInput(attrs={"class": "form-control"}),
            "notes": forms.TextInput(attrs={"class": "form-control"}),
        }


class SpeakerExpensesInlineForm:
    label = _("Expenses")

    def __init__(self, *args, speaker=None, event=None, prefix="hitalx_expense_inline", data=None, **kwargs):
        self.speaker = speaker
        self.event = event
        self.prefix = prefix
        queryset = speaker.expenses.all().order_by("-id") if speaker else ExpenseItem.objects.none()
        FormSet = modelformset_factory(ExpenseItem, form=ExpenseItemInlineForm, extra=1, can_delete=True)
        self.formset = FormSet(data=data, queryset=queryset, prefix=prefix)

    def is_valid(self):
        return self.formset.is_valid()

    @property
    def errors(self):
        return self.formset.errors

    def save(self):
        # Delete marked forms first
        for form in self.formset.deleted_forms:
            if form.instance.pk:
                form.instance.delete()
        saved = []
        for form in self.formset.forms:
            if form in self.formset.deleted_forms:
                continue
            if not hasattr(form, "cleaned_data"):
                continue
            if not form.cleaned_data:
                continue
            if not form.has_changed():
                continue
            obj = form.save(commit=False)
            if not obj.speaker_id and self.speaker:
                obj.speaker = self.speaker
                obj.paid = bool(form.cleaned_data.get("paid", False))
            obj.save()
            saved.append(obj)
        return saved

    def _row_html(self, form):
        return (
            "<tr>"
            f"<td>{form['description']}{form['id']}</td>"
            f"<td><div class='input-group'><span class='input-group-text'>€</span>{form['amount']}</div></td>"
            f"<td>{form['reference']}</td>"
            f"<td>{form['notes']}</td>"
            f"<td>{form['paid']}</td>"
            f"<td class='text-center'>{form['DELETE']}</td>"
            "</tr>"
        )

    def _render_table(self):
        rows = ''.join(self._row_html(form) for form in self.formset.forms)
        empty_row = self._row_html(self.formset.empty_form).replace('__prefix__', '{index}')
        html = (
            str(self.formset.management_form)
            + '<table class="table table-sm table-hover" id="hitalx-expense-table">'
            + f'<thead><tr><th>{_("Description")}</th><th>{_("Amount")}</th><th>{_("Reference (URL)")}</th><th>{_("Notes")}</th><th>{_("Paid")}</th><th>{_("Delete")}</th></tr></thead>'
            + f'<tbody>{rows}</tbody></table>'
            + f'<button type="button" class="btn btn-sm btn-outline-primary" id="hitalx-add-expense">+ {_("Add expense")}</button>'
            + f'<template id="hitalx-expense-row-template">{empty_row}</template>'
            + '<script defer src="/static/pretalx_hitalx/expenses_inline.js"></script>'
        )
        return mark_safe(html)

    def __html__(self):
        return self._render_table()

    def __str__(self):
        return str(self._render_table())



class ShuttleExportPermissionForm(forms.Form):
    team_names = forms.CharField(
        label=_("Allowed teams"),
        help_text=_("Comma-separated team names that may access the tours export (e.g. shuttle, crew)."),
        required=False,
    )
