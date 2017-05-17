
import sublime_plugin
from .utils import BaseLookUpJediCommand, get_buffer_line_column
from .sense_client import get_elixir_sense


class SuperElixirGoto(BaseLookUpJediCommand, sublime_plugin.TextCommand):

    def run(self, edit):
        sense = get_elixir_sense(self.view)
        buffer, line, column = get_buffer_line_column(self.view)
        definition = sense.definition(buffer, line, column)
        self.go_to_definition(definition)
