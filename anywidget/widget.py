import sys
from functools import lru_cache

import traitlets.traitlets as t

from ._descriptor import MimeBundleDescriptor, DEFAULT_ESM


@lru_cache(maxsize=None)
def _enable_custom_widget_manager():
    # Enable custom widgets manager so that our widgets display in Colab
    # https://github.com/googlecolab/colabtools/issues/498#issuecomment-998308485
    sys.modules["google.colab.output"].enable_custom_widget_manager()  # type: ignore


class AnyWidget(t.HasTraits):
    _repr_mimebundle_ = MimeBundleDescriptor()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Add anywidget JS/CSS source as traits if not registered
        anywidget_traits = {
            k: t.Unicode(getattr(self, k)).tag(sync=True)
            for k in ("_esm", "_module", "_css")
            if hasattr(self, k) and not self.has_trait(k)
        }

        # show default _esm if not defined
        if all(not hasattr(self, i) for i in ("_esm", "_module")):
            anywidget_traits["_esm"] = t.Unicode(DEFAULT_ESM).tag(sync=True)

        self.add_traits(**anywidget_traits)

        # Check if we are in Colab
        if "google.colab.output" in sys.modules:
            _enable_custom_widget_manager()

            # Monkey-patch _ipython_display_ for each instance if missing.
            # Necessary for Colab to display third-party widget
            # see https://github.com/manzt/anywidget/issues/48
            if not hasattr(self, "_ipython_display_"):

                def _ipython_display_(**kwargs):
                    from IPython.display import display

                    data = self._repr_mimebundle_(**kwargs)
                    display(data, raw=True)

                self._ipython_display_ = _ipython_display_
