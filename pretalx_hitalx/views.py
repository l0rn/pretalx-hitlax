from functools import cached_property

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, View
from django_context_decorator import context
from pretalx.common.mixins.views import EventPermissionRequired, ActionFromUrl, PermissionRequired
from pretalx.common.models import ActivityLog
from pretalx.common.views import CreateOrUpdateView
from pretalx.person.models import SpeakerProfile
from .models import ExpenseItem
from .form import SpeakerExpenseForm


class SpeakerExpenseList(EventPermissionRequired, ListView):
    model = ExpenseItem
    template_name = "pretalx_hitalx/speaker_expenses.html"
    context_object_name = "speakers"
    default_sort_field = "user__name"
    paginate_by = 25
    permission_required = "orga.view_speakers"

    def get_queryset(self):
        return super().get_queryset().filter(speaker_id=self.kwargs['speaker_id'])

    @context
    def speaker_profile(self):
        return SpeakerProfile.objects.filter(user=self.kwargs['speaker_id'], event=self.request.event).first()


class SpeakerExpenseDetail(PermissionRequired, ActionFromUrl, CreateOrUpdateView):
    model = ExpenseItem
    form_class = SpeakerExpenseForm
    template_name = "pretalx_hitalx/speaker_expense.html"
    permission_required = "orga.view_speaker"
    write_permission_required = "orga.change_speaker"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**{
            **self.get_form_kwargs(),
            'initial': {'speaker': self.kwargs['speaker_id']}
        })

    def post(self, request, *args, **kwargs):
        created = False if self.object else True
        response = super(SpeakerExpenseDetail, self).post(request, *args, **kwargs)
        setattr(self.object, "event", request.event)
        if created:
            self.object.log_action(
                'pretalx_hitalx.expense_item.create',
                person=request.user,
                data={'amount': self.object.amount, 'notes': self.object.notes}
            )
        else:
            self.object.log_action(
                'pretalx_hitalx.expense_item.edit',
                person=request.user,
                data={'amount': self.object.amount, 'notes': self.object.notes}
            )
        return response

    @property
    def permission_object(self):
        return SpeakerProfile.objects.filter(user=self.kwargs['speaker_id'], event=self.request.event).first()

    def get_permission_object(self):
        return self.permission_object

    def get_object(self):
        return ExpenseItem.objects.filter(
            pk=self.kwargs.get("pk")
        ).first()

    @cached_property
    def object(self):
        return self.get_object()

    def get_success_url(self) -> str:
        return reverse(
            'plugins:pretalx_hitalx:expenses.view',
            kwargs={"event": self.request.event.slug, "speaker_id": self.kwargs["speaker_id"]},
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
        return ExpenseItem.objects.filter(
            pk=self.kwargs.get("pk")
        ).first()

    @property
    def permission_object(self):
        return SpeakerProfile.objects.filter(user=self.kwargs['speaker_id'], event=self.request.event).first()

    def get_permission_object(self):
        return self.permission_object

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        paid = request.POST.get('paid', False) == 'true'
        obj.paid = paid
        obj.save()
        setattr(obj, "event", request.event)
        obj.log_action(
            'pretalx_hitalx.expense_item.mark',
            person=request.user,
            data={'paid': self.object.paid}
        )
        referer = request.META.get('HTTP_REFERER', None)
        if referer:
            return HttpResponseRedirect(referer)
        else:
            return HttpResponseRedirect(reverse(
                'plugins:pretalx_hitalx:expenses.view',
                kwargs={"event": self.request.event.slug, "speaker_id": self.kwargs["speaker_id"]},
            ))
