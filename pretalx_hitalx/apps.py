from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PluginApp(AppConfig):
    name = "pretalx_hitalx"
    verbose_name = "Various extensions to make the Life easier for the HI Congress"

    class PretalxPluginMeta:
        name = _("Pretalx Hitalx")
        author = "Jonatan Zint"
        description = _("Various features specifically for the Hedonist International")
        visible = True
        version = "0.0.11"
        category = "CUSTOMIZATION"

    def ready(self):
        from . import signals  # noqa
