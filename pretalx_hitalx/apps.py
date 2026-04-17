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
        import importlib

        SubmissionsEditView = None
        for module_name, class_name in [
            ("pretalx.cfp.views.user", "SubmissionsEditView"),
            ("pretalx.cfp.views.user", "SubmissionEditView"),
            ("pretalx.cfp.views.submissions", "SubmissionsEditView"),
            ("pretalx.cfp.views.submissions", "SubmissionEditView"),
        ]:
            try:
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name, None)
                if cls is not None:
                    SubmissionsEditView = cls
                    logger.info("pretalx_hitalx: patching CFP view %s.%s", module_name, class_name)
                    break
            except Exception as e:
                logger.debug("pretalx_hitalx: could not import %s: %s", module_name, e)

        if SubmissionsEditView is None:
            logger.warning("pretalx_hitalx: SubmissionsEditView not found — CFP injection skipped")
            return

        if getattr(SubmissionsEditView, "_hitalx_cfp_patch", False):
            return

        OUR_TEMPLATE = "pretalx_hitalx/cfp_submission_detail.html"

        def _inject_hitalx_context(view_self):
            """Return (expenses, tours) for the current user + submission event."""
            try:
                from django_scopes import scope

                request = view_self.request
                if not hasattr(request, "user") or not request.user.is_authenticated:
                    return [], []

                # Find the submission — try self.object first, then context
                submission = getattr(view_self, "object", None)
                if submission is None:
                    return [], []

                event = getattr(submission, "event", None)
                if event is None:
                    return [], []

                with scope(event=event):
                    try:
                        profile = request.user.profiles.get(event=event)
                    except Exception:
                        return [], []

                    expenses = list(request.user.expenses.all().order_by("description"))
                    tours = list(profile.tours.all().order_by("departure_time"))
                    return expenses, tours
            except Exception:
                logger.exception("pretalx_hitalx: error building CFP context")
                return [], []

        # Patch get_context_data to inject our data into the context dict
        _orig_get_context_data = SubmissionsEditView.get_context_data

        def _patched_get_context_data(self, **kwargs):
            ctx = _orig_get_context_data(self, **kwargs)
            expenses, tours = _inject_hitalx_context(self)
            ctx["hitalx_my_expenses"] = expenses
            ctx["hitalx_my_tours"] = tours
            return ctx

        SubmissionsEditView.get_context_data = _patched_get_context_data

        # Patch get_template_names (used by TemplateResponseMixin.render_to_response)
        _orig_get_template_names = SubmissionsEditView.get_template_names

        def _patched_get_template_names(self):
            names = list(_orig_get_template_names(self))
            if OUR_TEMPLATE not in names:
                names = [OUR_TEMPLATE] + names
            return names

        SubmissionsEditView.get_template_names = _patched_get_template_names

        # Also patch render_to_response as a fallback (some views bypass get_template_names)
        _orig_render_to_response = getattr(SubmissionsEditView, "render_to_response", None)
        if _orig_render_to_response:
            def _patched_render_to_response(self, context, **response_kwargs):
                response = _orig_render_to_response(self, context, **response_kwargs)
                # TemplateResponse stores template_name and renders lazily — we can still change it
                if hasattr(response, "template_name"):
                    tnames = response.template_name
                    if isinstance(tnames, str):
                        tnames = [tnames]
                    else:
                        tnames = list(tnames)
                    if OUR_TEMPLATE not in tnames:
                        response.template_name = [OUR_TEMPLATE] + tnames
                return response

            SubmissionsEditView.render_to_response = _patched_render_to_response

        SubmissionsEditView._hitalx_cfp_patch = True
