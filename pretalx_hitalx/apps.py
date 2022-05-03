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
        version = "0.0.7"

    def ready(self):
        from . import signals  # NOQA
