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
        self.fields["paid"].disabled = True
        self.fields["reference"].label = _("Reference (URL)")

    class Meta:
        model = ExpenseItem
        fields = ["speaker", "description", "amount", "paid", "reference", "notes"]
        readonly_fields = ["speaker", "paid"]


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
    departure_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}))
    passengers = PassengerChoiceField(
        queryset=SpeakerProfile.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        blank=True,
        required=False
    )

    def __init__(self, *args, user=None, locales=None, organiser=None, **kwargs):
        initial = kwargs.get("initial", {}) or {}
        super().__init__(*args, **kwargs)
        event_id = initial.get("event") or getattr(self.instance, "event_id", None)
        if event_id:
            with scope(event=Event.objects.get(id=event_id)):
                self.fields["passengers"].queryset = SpeakerProfile.objects.all()

    class Meta:
        model = Tour
        fields = ["description", "departure_time", "start_location", "type", "event", "passengers"]
        labels = {"reference": _("Reference (URL)")}
        widgets = {'event': forms.HiddenInput(), 'passengers': forms.CheckboxSelectMultiple()}
        field_classes = {
            "passengers": SafeModelMultipleChoiceField,
        }




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
        FormSet = modelformset_factory(ExpenseItem, form=ExpenseItemInlineForm, extra=1, can_delete=False)
        self.formset = FormSet(data=data, queryset=queryset, prefix=prefix)

    def is_valid(self):
        return self.formset.is_valid()

    @property
    def errors(self):
        return self.formset.errors

    def save(self):
        saved = []
        for form in self.formset.forms:
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
            "</tr>"
        )

    def _render_table(self):
        rows = ''.join(self._row_html(form) for form in self.formset.forms)
        empty_row = self._row_html(self.formset.empty_form).replace('__prefix__', '{index}')
        html = (
            str(self.formset.management_form)
            + '<table class="table table-sm table-hover" id="hitalx-expense-table">'
            + f'<thead><tr><th>{_("Description")}</th><th>{_("Amount")}</th><th>{_("Reference (URL)")}</th><th>{_("Notes")}</th><th>{_("Paid")}</th></tr></thead>'
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
