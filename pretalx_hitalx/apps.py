from django.apps import AppConfig
from django.utils.translation import gettext_lazy


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
        version = "0.0.12"

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
