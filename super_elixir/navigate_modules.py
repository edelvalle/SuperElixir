from functools import partial

import sublime_plugin
from .utils import BaseLookUpJediCommand
from .sense_client import get_elixir_sense


class SuperElixirNavigateModules(
        BaseLookUpJediCommand, sublime_plugin.TextCommand):

    def run(self, edit):
        sense = get_elixir_sense(self.view)
        all_modules = sense.all_modules
        self.view.window().show_quick_panel(
            all_modules,
            partial(self._select_module, modules=all_modules),
        )

    def _select_module(self, i, modules=None):
        if i < 0:
            return

        module = modules[i]
        sense = get_elixir_sense(self.view)
        definition = sense.definition(module, 0, len(module))
        self.go_to_definition(definition)
