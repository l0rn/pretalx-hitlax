from functools import cached_property

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import ListView, View, DeleteView
from django_context_decorator import context
from pretalx.common.views.mixins import (
    EventPermissionRequired,
    Filterable,
    PermissionRequired,
    Sortable,
)
from pretalx.common.models import ActivityLog
from pretalx.common.views.generic import CreateOrUpdateView
from pretalx.event.models import Event
from pretalx.person.forms import SpeakerFilterForm
from pretalx.person.models import SpeakerProfile
from pretalx.submission.models import Answer, SubmissionStates

from .form import SpeakerExpenseForm, SpeakerToursForm, TourForm
from .models import ExpenseItem, Tour


class SpeakerList(EventPermissionRequired, Sortable, Filterable, ListView):
    model = SpeakerProfile
    template_name = "pretalx_hitalx/speakers.html"
    context_object_name = "speakers"
    default_filters = ("user__email__icontains", "user__name__icontains")
    sortable_fields = ("user__email", "user__name")
    default_sort_field = "user__name"
    paginate_by = 25
    permission_required = "person.orga_list_speakerprofile"

    @context
    def filter_form(self):
        return SpeakerFilterForm(self.request.GET, event=self.request.event)

    def get_queryset(self):
        qs = (
            SpeakerProfile.objects.filter(
                event=self.request.event, user__in=self.request.event.submitters
            )
            .select_related("event", "user")
            .annotate(
                submission_count=Count(
                    "user__submissions",
                    filter=Q(user__submissions__event=self.request.event),
                ),
                accepted_submission_count=Count(
                    "user__submissions",
                    filter=Q(user__submissions__event=self.request.event)
                    & Q(user__submissions__state__in=[SubmissionStates.ACCEPTED, SubmissionStates.CONFIRMED]),
                ),
            )
        )

        qs = self.filter_queryset(qs)
        qs = qs.order_by("id").distinct()
        qs = self.sort_queryset(qs)
        return qs


class SpeakerExpenseList(EventPermissionRequired, ListView):
    model = ExpenseItem
    template_name = "pretalx_hitalx/speaker_expenses.html"
    context_object_name = "expenses"
    paginate_by = 25
    permission_required = "person.orga_view_speakerprofile"

    def get_queryset(self):
        return ExpenseItem.objects.filter(speaker_id=self.kwargs["speaker_id"])

    @context
    def speaker_profile(self):
        return SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()


class SpeakerExpenseDetail(PermissionRequired, CreateOrUpdateView):
    model = ExpenseItem
    form_class = SpeakerExpenseForm
    template_name = "pretalx_hitalx/speaker_expense.html"
    permission_required = "person.orga_view_speakerprofile"
    write_permission_required = "person.update_speakerprofile"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            **{
                **self.get_form_kwargs(),
                "initial": {"speaker": self.kwargs["speaker_id"]},
            }
        )

    def post(self, request, *args, **kwargs):
        created = not bool(self.object)
        response = super().post(request, *args, **kwargs)
        if self.object:
            self.object.event = request.event
            action = "pretalx_hitalx.expense_item.create" if created else "pretalx_hitalx.expense_item.edit"
            self.object.log_action(
                action,
                person=request.user,
                data={"amount": str(self.object.amount), "notes": self.object.notes},
            )
        return response

    @property
    def permission_object(self):
        return SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()

    def get_object(self):
        return ExpenseItem.objects.filter(pk=self.kwargs.get("pk")).first()

    @cached_property
    def object(self):
        return self.get_object()

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:expenses.view",
            kwargs={
                "event": self.request.event.slug,
                "speaker_id": self.kwargs["speaker_id"],
            },
        )

    @context
    def log_entries(self, **kwargs):
        if self.object:
            return ActivityLog.objects.filter(
                event=self.request.event,
                content_type=ContentType.objects.get_for_model(ExpenseItem),
                object_id=self.object.id,
            )
        return []


class MarkExpenseView(PermissionRequired, View):
    permission_required = "person.update_speakerprofile"

    @property
    def permission_object(self):
        return SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(ExpenseItem, pk=self.kwargs.get("pk"))
        paid = request.POST.get("paid", False) == "true"
        obj.paid = paid
        obj.save()
        obj.log_action(
            "pretalx_hitalx.expense_item.mark",
            person=request.user,
            data={"paid": obj.paid},
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse(
            "plugins:pretalx_hitalx:expenses.view",
            kwargs={
                "event": request.event.slug,
                "speaker_id": self.kwargs["speaker_id"],
            },
        ))


class SpeakerTourManagement(PermissionRequired, CreateOrUpdateView):
    template_name = "pretalx_hitalx/speaker_tours.html"
    form_class = SpeakerToursForm
    model = SpeakerProfile
    permission_required = "person.update_speakerprofile"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:speakers_by_expense.view",
            kwargs={"event": self.request.event.slug},
        )


class TourListView(EventPermissionRequired, Sortable, Filterable, ListView):
    template_name = "pretalx_hitalx/tours.html"
    model = Tour
    context_object_name = "tours"
    filter_fields = ["type"]
    permission_required = "person.orga_list_speakerprofile"

    def get_queryset(self):
        qs = Tour.objects.filter(event=self.request.event)
        qs = self.filter_queryset(qs).order_by("departure_time")
        return qs


class TourDetailView(EventPermissionRequired, CreateOrUpdateView):
    template_name = "pretalx_hitalx/tour.html"
    model = Tour
    form_class = TourForm
    permission_required = "person.update_speakerprofile"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            **{
                **self.get_form_kwargs(),
                "event": self.request.event,
                "initial": {"event": self.request.event.id},
            }
        )

    def get_object(self):
        return Tour.objects.filter(pk=self.kwargs.get("pk"), event=self.request.event).first()

    @cached_property
    def object(self):
        return self.get_object()

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:tours.view",
            kwargs={"event": self.request.event.slug},
        )


class TourDeleteView(EventPermissionRequired, DeleteView):
    permission_required = "person.update_speakerprofile"

    def get_object(self):
        return get_object_or_404(Tour, event=self.request.event, pk=self.kwargs.get("pk"))

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:tours.view",
            kwargs={"event": self.request.event.slug},
        )


class ShuttleView(EventPermissionRequired, View):
    permission_required = "person.orga_list_speakerprofile"

    def get(self, request, **kwargs):
        if request.user.teams.filter(name__iexact="shuttle").exists() or request.user.is_administrator:
            return render(request, "pretalx_hitalx/tours_export.html", {
                "tours": Tour.objects.filter(event=request.event).order_by("departure_time")
            })
        messages.warning(request, _("Only people in the team 'shuttle' can access this page"))
        return redirect(reverse("orga:event.dashboard", kwargs={"event": request.event.slug}))
