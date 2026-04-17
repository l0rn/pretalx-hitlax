from django.apps import AppConfig
from django.utils.translation import gettext_lazy
import logging

logger = logging.getLogger(__name__)


class PluginApp(AppConfig):
    name = "pretalx_hitalx"
    verbose_name = "Various extensions to make the Life easier for the HI Congress"

    class PretalxPluginMeta:
        name = gettext_lazy("Pretalx Hitalx")
        author = "Jonatan Zint"
        description = gettext_lazy(
            "Various features specifically for the Hedonist International"
        )
        visible = True
        version = "0.0.13"

    def ready(self):
        from . import signals  # NOQA

        # Work around current pretalx SpeakerDetail implementation skipping FormSignalMixin saves
        from django.contrib import messages
        from django.utils.translation import gettext as _
        from pretalx.orga.views.speaker import SpeakerDetail

        if not getattr(SpeakerDetail, "_hitalx_inline_patch", False):
            _orig_form_valid = SpeakerDetail.form_valid

            def _patched_form_valid(self, form):
                for extra_form in self.extra_forms:
                    if not extra_form.is_valid():
                        return self.get(self.request, *self.args, **self.kwargs)

                response = _orig_form_valid(self, form)

                for extra_form in self.extra_forms:
                    try:
                        extra_form.save()
                    except Exception:
                        label = getattr(extra_form, "label", "")
                        prefix = f"[{label}] " if label else ""
                        messages.error(self.request, prefix + _("Some changes could not be saved."))
                return response

            SpeakerDetail.form_valid = _patched_form_valid
            SpeakerDetail._hitalx_inline_patch = True

        # Inject expense/tour info into the speaker-facing submission edit page
        self._patch_cfp_submission_view()

    def _patch_cfp_submission_view(self):
        """
        Monkey-patch pretalx's CFP submission edit view to show the speaker's
        own expenses and tours in a read-only section at the bottom of the page.
        """
        SubmissionsEditView = None
        for module in (
            "pretalx.cfp.views.user",
            "pretalx.cfp.views.submissions",
        ):
            try:
                import importlib
                mod = importlib.import_module(module)
                cls = getattr(mod, "SubmissionsEditView", None)
                if cls is not None:
                    SubmissionsEditView = cls
                    break
            except ImportError:
                continue

        if SubmissionsEditView is None:
            logger.warning("pretalx_hitalx: could not find SubmissionsEditView — CFP injection skipped")
            return

        if getattr(SubmissionsEditView, "_hitalx_cfp_patch", False):
            return

        _orig_get_context_data = SubmissionsEditView.get_context_data
        _orig_get_template_names = SubmissionsEditView.get_template_names

        def _patched_get_template_names(self):
            original = _orig_get_template_names(self)
            return ["pretalx_hitalx/cfp_submission_detail.html"] + list(original)

        def _patched_get_context_data(self, **kwargs):
            ctx = _orig_get_context_data(self, **kwargs)
            try:
                from django_scopes import scope
                from .models import ExpenseItem, Tour

                submission = getattr(self, "object", None)
                request = self.request
                if submission is None or not hasattr(request, "user") or not request.user.is_authenticated:
                    return ctx

                event = submission.event
                with scope(event=event):
                    try:
                        profile = request.user.profiles.get(event=event)
                    except Exception:
                        return ctx

                    from django.utils.formats import date_format
                    from django.utils.timezone import localtime

                    # expenses belong to User; tours belong to SpeakerProfile via M2M
                    expenses = list(request.user.expenses.all().order_by("description"))
                    tours = list(profile.tours.all().order_by("departure_time"))

                    ctx["hitalx_my_expenses"] = expenses
                    ctx["hitalx_my_tours"] = tours
            except Exception:
                logger.exception("pretalx_hitalx: error injecting CFP context")
            return ctx

        SubmissionsEditView.get_template_names = _patched_get_template_names
        SubmissionsEditView.get_context_data = _patched_get_context_data
        SubmissionsEditView._hitalx_cfp_patch = True
