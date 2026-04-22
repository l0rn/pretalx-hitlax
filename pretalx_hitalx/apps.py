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

        # Inject expense/tour info into the speaker-facing submission edit page
        self._patch_cfp_submission_view()

    def _patch_cfp_submission_view(self):
        """
        Monkey-patch pretalx's CFP SubmissionsEditView.dispatch() to inject
        a read-only expense/tour section into the rendered response HTML.
        This approach works regardless of how the view renders its template.
        """
        import importlib

        SubmissionsEditView = None
        for module_name, class_name in [
            ("pretalx.cfp.views.user", "SubmissionsEditView"),
            ("pretalx.cfp.views.user", "SubmissionEditView"),
            ("pretalx.cfp.views.submissions", "SubmissionsEditView"),
        ]:
            try:
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name, None)
                if cls is not None:
                    SubmissionsEditView = cls
                    logger.info(
                        "pretalx_hitalx: found CFP view at %s.%s — patching dispatch()",
                        module_name, class_name,
                    )
                    break
            except Exception as e:
                logger.warning("pretalx_hitalx: could not import %s: %s", module_name, e)

        if SubmissionsEditView is None:
            logger.warning("pretalx_hitalx: SubmissionsEditView not found — CFP injection skipped")
            return

        if getattr(SubmissionsEditView, "_hitalx_cfp_patch", False):
            return

        _orig_dispatch = SubmissionsEditView.dispatch

        def _patched_dispatch(self, request, *args, **kwargs):
            response = _orig_dispatch(self, request, *args, **kwargs)

            # Only inject on GET responses that render HTML
            if request.method != "GET":
                return response

            try:
                from django.template.loader import render_to_string
                from django_scopes import scope

                submission = getattr(self, "object", None)
                if submission is None or not getattr(request, "user", None) or not request.user.is_authenticated:
                    return response

                event = getattr(submission, "event", None)
                if event is None:
                    return response

                with scope(event=event):
                    try:
                        profile = request.user.profiles.get(event=event)
                    except Exception:
                        return response

                    from .models import AccommodationBooking
                    expenses = list(request.user.expenses.all().order_by("description"))
                    tours = list(profile.tours.all().order_by("departure_time"))
                    accom_bookings = list(
                        AccommodationBooking.objects.filter(
                            speaker=request.user,
                            accommodation__event=event,
                        ).select_related("accommodation").order_by("from_date")
                    )

                if not expenses and not tours and not accom_bookings:
                    return response

                extra_html = render_to_string(
                    "pretalx_hitalx/cfp_expense_tour_section.html",
                    {
                        "hitalx_my_expenses": expenses,
                        "hitalx_my_tours": tours,
                        "hitalx_my_accommodation_bookings": accom_bookings,
                    },
                    request=request,
                )

                # Force TemplateResponse to render if it hasn't yet
                if hasattr(response, "render") and not getattr(response, "is_rendered", True):
                    response.render()

                if hasattr(response, "content"):
                    content = response.content
                    # Try to inject inside the main container; fall back to </body>
                    wrapped = '<div class="container">' + extra_html + '</div>'
                    for marker in (b"</main>", b"</body>"):
                        if marker in content:
                            response.content = content.replace(
                                marker, wrapped.encode("utf-8") + marker, 1
                            )
                            break
            except Exception:
                logger.exception("pretalx_hitalx: CFP dispatch injection failed")

            return response

        SubmissionsEditView.dispatch = _patched_dispatch
        SubmissionsEditView._hitalx_cfp_patch = True
