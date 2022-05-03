from functools import cached_property

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.views.generic import ListView, View
from django_context_decorator import context
from pretalx.common.mixins.views import (
    ActionFromUrl,
    EventPermissionRequired,
    Filterable,
    PermissionRequired,
    Sortable,
)
from pretalx.common.models import ActivityLog
from pretalx.common.views import CreateOrUpdateView
from pretalx.person.forms import SpeakerFilterForm
from pretalx.person.models import SpeakerProfile
from pretalx.submission.models import Answer, SubmissionStates

from .form import SpeakerExpenseForm, SpeakerToursForm
from .models import ExpenseItem, Tour


class SpeakerList(EventPermissionRequired, Sortable, Filterable, ListView):
    model = SpeakerProfile
    template_name = "pretalx_hitalx/speakers.html"
    context_object_name = "speakers"
    default_filters = ("user__email__icontains", "user__name__icontains")
    sortable_fields = ("user__email", "user__name")
    default_sort_field = "user__name"
    paginate_by = 25
    permission_required = "orga.view_speakers"

    @context
    def filter_form(self):
        return SpeakerFilterForm(self.request.event, self.request.GET)

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
        qs = self.sort_queryset(qs)
        return qs


class SpeakerExpenseList(EventPermissionRequired, ListView):
    model = ExpenseItem
    template_name = "pretalx_hitalx/speaker_expenses.html"
    context_object_name = "speakers"
    default_sort_field = "user__name"
    paginate_by = 25
    permission_required = "orga.view_speakers"

    def get_queryset(self):
        return super().get_queryset().filter(speaker_id=self.kwargs["speaker_id"])

    @context
    def speaker_profile(self):
        return SpeakerProfile.objects.filter(
            user=self.kwargs["speaker_id"], event=self.request.event
        ).first()


class SpeakerExpenseDetail(PermissionRequired, ActionFromUrl, CreateOrUpdateView):
    model = ExpenseItem
    form_class = SpeakerExpenseForm
    template_name = "pretalx_hitalx/speaker_expense.html"
    permission_required = "orga.view_speaker"
    write_permission_required = "orga.change_speaker"

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
                data={"amount": self.object.amount, "notes": self.object.notes},
            )
        else:
            self.object.log_action(
                "pretalx_hitalx.expense_item.edit",
                person=request.user,
                data={"amount": self.object.amount, "notes": self.object.notes},
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

    @context
    def log_entries(self, **kwargs):
        if self.object:
            return ActivityLog.objects.filter(
                event=self.request.event,
                content_type=ContentType.objects.get_for_model(ExpenseItem),
                object_id=self.object.id,
            )
        else:
            return []


class MarkExpenseView(PermissionRequired, View):
    model = ExpenseItem
    context_object_name = "expense_item"
    permission_required = "orga.view_speaker"
    write_permission_required = "orga.change_speaker"

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


class SpeakerTourManagement(PermissionRequired, ActionFromUrl, CreateOrUpdateView):
    template_name = "pretalx_hitalx/speaker_tours.html"
    form_class = SpeakerToursForm
    model = SpeakerProfile
    permission_required = "orga.view_speaker"
    write_permission_required = "orga.change_speaker"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_hitalx:speakers_by_expense.view",
            kwargs={
                "event": self.request.event.slug
            },
        )


class TourListView(EventPermissionRequired, Sortable, ListView):
    template_name = "pretalx_hitalx/tours.html"
    model = Tour
    context_object_name = "tours"
    permission_required = "orga.view_speaker"
