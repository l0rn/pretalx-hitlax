from functools import cached_property

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.translation import gettext
from django.views.generic import ListView, View, DeleteView, FormView
from pretalx.common.views.mixins import (
    EventPermissionRequired,
    Filterable,
    PermissionRequired,
)
from pretalx.common.models import ActivityLog
from pretalx.common.views.generic import CreateOrUpdateView
from pretalx.event.models import Event
from pretalx.person.forms import SpeakerFilterForm
from pretalx.person.models import SpeakerProfile
from pretalx.submission.models import Answer, SubmissionStates
from pretalx.submission.rules import speaker_profiles_for_user

from .form import SpeakerExpenseForm, SpeakerToursForm, TourForm, ShuttleExportPermissionForm
from .models import ExpenseItem, Tour


class SpeakerList(EventPermissionRequired, Filterable, ListView):
    model = SpeakerProfile
    template_name = "pretalx_hitalx/speakers.html"
    context_object_name = "speakers"
    default_filters = ("user__email__icontains", "user__name__icontains")
    paginate_by = 25
    permission_required = "person.orga_list_speakerprofile"

    def get_filter_form(self):
        return SpeakerFilterForm(self.request.GET, event=self.request.event)

    def get_queryset(self):
        qs = (
            speaker_profiles_for_user(self.request.event, self.request.user)
            .select_related("event", "user")
            .annotate(
                submission_count=Count(
                    "user__submissions",
                    filter=Q(user__submissions__event=self.request.event),
                ),
                accepted_submission_count=Count(
                    "user__submissions",
                    filter=Q(user__submissions__event=self.request.event)
                           & Q(user__submissions__state__in=["accepted", "confirmed"]),
                ),
            )
        )

        qs = self.filter_queryset(qs)
        if "role" in self.request.GET:
            if self.request.GET["role"] == "true":
                qs = qs.filter(
                    user__submissions__in=self.request.event.submissions.filter(
                        state__in=[
                            SubmissionStates.ACCEPTED,
                            SubmissionStates.CONFIRMED,
                        ]
                    )
                )
            elif self.request.GET["role"] == "false":
                qs = qs.exclude(
                    user__submissions__in=self.request.event.submissions.filter(
                        state__in=[
                            SubmissionStates.ACCEPTED,
                            SubmissionStates.CONFIRMED,
                        ]
                    )
                )

        question = self.request.GET.get("question")
        unanswered = self.request.GET.get("unanswered")
        answer = self.request.GET.get("answer")
        option = self.request.GET.get("answer__options")
        if question and (answer or option):
            if option:
                answers = Answer.objects.filter(
                    person_id=OuterRef("user_id"),
                    question_id=question,
                    options__pk=option,
                )
            else:
                answers = Answer.objects.filter(
                    person_id=OuterRef("user_id"),
                    question_id=question,
                    answer__exact=answer,
                )
            qs = qs.annotate(has_answer=Exists(answers)).filter(has_answer=True)
        elif question and unanswered:
            answers = Answer.objects.filter(
                question_id=question, person_id=OuterRef("user_id")
            )
            qs = qs.annotate(has_answer=Exists(answers)).filter(has_answer=False)
        qs = qs.order_by("id").distinct()
        return qs


class SpeakerExpenseList(EventPermissionRequired, ListView):
    model = ExpenseItem
    template_name = "pretalx_hitalx/speaker_expenses.html"
    context_object_name = "speakers"
    paginate_by = 25
    permission_required = "person.orga_list_speakerprofile"

    def get_queryset(self):
        return super().get_queryset().filter(speaker_id=self.kwargs["speaker_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["speaker_profile"] = SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()
        return context


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
        created = False if self.object else True
        response = super(SpeakerExpenseDetail, self).post(request, *args, **kwargs)
        self.object.event = request.event
        if created:
            self.object.log_action(
                "pretalx_hitalx.expense_item.create",
                person=request.user,
                data={"amount": str(self.object.amount), "notes": self.object.notes},
            )
        else:
            self.object.log_action(
                "pretalx_hitalx.expense_item.edit",
                person=request.user,
                data={"amount": str(self.object.amount), "notes": self.object.notes},
            )
        return response

    @property
    def permission_object(self):
        return SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()

    def get_permission_object(self):
        return self.permission_object

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context["log_entries"] = ActivityLog.objects.filter(
                event=self.request.event,
                content_type=ContentType.objects.get_for_model(ExpenseItem),
                object_id=self.object.id,
            )
        else:
            context["log_entries"] = []
        return context


class MarkExpenseView(PermissionRequired, View):
    model = ExpenseItem
    context_object_name = "expense_item"
    permission_required = "person.orga_view_speakerprofile"
    write_permission_required = "person.update_speakerprofile"

    def get_object(self):
        return self.object

    @cached_property
    def object(self):
        return ExpenseItem.objects.filter(pk=self.kwargs.get("pk")).first()

    @property
    def permission_object(self):
        return SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()

    def get_permission_object(self):
        return self.permission_object

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        paid = request.POST.get("paid", False) == "true"
        obj.paid = paid
        obj.save()
        self.object.event = request.event
        obj.log_action(
            "pretalx_hitalx.expense_item.mark",
            person=request.user,
            data={"paid": self.object.paid},
        )
        referer = request.META.get("HTTP_REFERER", None)
        if referer:
            return HttpResponseRedirect(referer)
        else:
            return HttpResponseRedirect(
                reverse(
                    "plugins:pretalx_hitalx:expenses.view",
                    kwargs={
                        "event": self.request.event.slug,
                        "speaker_id": self.kwargs["speaker_id"],
                    },
                )
            )


class SpeakerTourManagement(PermissionRequired, CreateOrUpdateView):
    template_name = "pretalx_hitalx/speaker_tours.html"
    form_class = SpeakerToursForm
    model = SpeakerProfile
    permission_required = "person.orga_view_speakerprofile"
    write_permission_required = "person.update_speakerprofile"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:speakers_by_expense.view",
            kwargs={
                "event": self.request.event.slug
            },
        )


class TourListView(EventPermissionRequired, Filterable, ListView):
    template_name = "pretalx_hitalx/tours.html"
    model = Tour
    context_object_name = "tours"
    filter_fields = ['type']
    permission_required = "person.orga_view_speakerprofile"

    def get_queryset(self):
        qs = Tour.objects.filter(event__slug=self.request.event.slug)
        qs = self.filter_queryset(qs).order_by('departure_time')
        return qs


class TourDetailView(EventPermissionRequired, CreateOrUpdateView):
    template_name = "pretalx_hitalx/tour.html"
    model = Tour
    form_class = TourForm
    permission_required = "person.orga_view_speakerprofile"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            **{
                **self.get_form_kwargs(),
                "initial": {"event": Event.objects.filter(slug=self.kwargs["event"]).first().id},
            }
        )

    def get_object(self):
        return Tour.objects.filter(pk=self.kwargs.get("pk")).first()

    @cached_property
    def object(self):
        return self.get_object()

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:tours.view",
            kwargs={
                "event": self.request.event.slug
            },
        )


class TourDeleteView(EventPermissionRequired, DeleteView):
    permission_required = "person.orga_view_speakerprofile"

    def get_object(self):
        return get_object_or_404(
            Tour.objects.all(), event=self.request.event, pk=self.kwargs.get("pk")
        )

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:tours.view",
            kwargs={
                "event": self.request.event.slug
            },
        )


class ShuttleExportSettingsView(EventPermissionRequired, FormView):
    template_name = "pretalx_hitalx/shuttle_export_settings.html"
    form_class = ShuttleExportPermissionForm
    permission_required = "event.update_event"

    def get_initial(self):
        value = self.request.event.settings.get("hitalx_shuttle_export_teams", "shuttle")
        return {"team_names": value}

    def form_valid(self, form):
        raw = form.cleaned_data.get("team_names", "")
        teams = [t.strip() for t in raw.split(",") if t.strip()]
        value = ", ".join(teams)
        self.request.event.settings.set("hitalx_shuttle_export_teams", value)
        messages.success(self.request, gettext("Shuttle export permissions updated."))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("plugins:pretalx_hitalx:tours.export.settings", kwargs={"event": self.request.event.slug})


class ShuttleView(View):
    def get(self, request, **kwargs):
        if request.user.teams.filter(name='shuttle').exists():
            return render(request, 'pretalx_hitalx/tours_export.html', {
                'tours': Tour.objects.filter(event=request.event).order_by('departure_time')
            })
        else:
            messages.warning(request, gettext('Only people in the team \'shuttle\' can access this page'))
            return redirect(reverse('orga:event.login', kwargs={'event': request.event.slug}))
