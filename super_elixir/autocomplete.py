import re

import sublime
import sublime_plugin

from .utils import is_elixir, get_buffer_line_column
from .sense_client import get_elixir_sense


FOLLOWING_CHARS = set(["\r", "\n", "\t", " ", ")", "]", ";", "}", "\x00"])


class Autocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if not is_elixir(view):
            return

        buffer, line, column = get_buffer_line_column(view, locations[0])

        sense = get_elixir_sense(view)
        suggestions = sense.suggestions(buffer, line, column)

        completions = []
        for s in suggestions:
            if s['type'] == 'hint':
                continue

            c = {
                'name': s['name'],
                'show': s['name'],
                'hint': (
                    '%s %s' % (
                        s.get('origin', ''),
                        s['type'].replace('_', ' ')
                    )
                ).strip(),
                'completion': s['name'],
            }

            if s['type'].endswith('function') or s['type'] == 'macro':
                args = s.get('args', '')
                arity = s.get('arity')
                if args:
                    args = args.split(',')
                else:
                    args = []

                if not args and arity:
                    args = ['_'] * arity

                c['show'] += '(' + ', '.join(args) + ')'

                completion_args = [
                    '${%s:%s}' % (i, a)
                    for i, a in enumerate(args, 1)
                ]
                c['completion'] += '(' + ', '.join(completion_args) + ')'

            completions.append(c)

        completions = self._sort_by_frequency_in_view(buffer, completions)
        completions = [
            ['{show}\t{hint}'.format(**c), c['completion']]
            for c in completions
        ]
        return completions

    def _sort_by_frequency_in_view(self, buffer, completions):
        completions.sort(key=lambda c: (
            -buffer.count(c['name']),  # how many times it is in the buffer
            len(c['name']) - len(c['name'].strip('_')),  # less underscores wins
            c['name'],  # alphabetically
        ))
        return completions

    def on_hover(self, view, point, hover_zone):
        if hover_zone == sublime.HOVER_TEXT and is_elixir(view):

            buffer, line, column = get_buffer_line_column(view, point)
            sense = get_elixir_sense(view)
            docs = sense.docs(buffer, line, column)

            types = docs['docs']['types']
            types = ''.join(re.compile(r'`([^`]+)`').findall(types))

            html = (
                '<div>' +
                types.replace('\n', '</div><div>') +
                docs['docs']['docs'].replace('\n', '</div><div>') +
                '</div>'
            )

            view.show_popup(
                html,
                flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                location=point,
                max_width=1024,
            )


class SuperElixirParamsAutocomplete(sublime_plugin.TextCommand):

    def run(self, edit, characters='('):

        point = self.view.sel()[0].a
        f_name = self.view.substr(self.view.word(point))
        completions = Autocomplete().on_query_completions(
            self.view, f_name, [point])

        if completions:
            show, snippet = completions[0]
            snippet = snippet[snippet.index('('):]  # cut out the function name
            self.view.run_command('insert_snippet', {"contents": snippet})
        else:
            self._insert_characters(edit, characters, ')')

    @property
    def auto_match_enabled(self):
        """ check if sublime closes parenthesis automaticly """
        return self.view.settings().get('auto_match_enabled', True)

    def _insert_characters(self, edit, open_pair, close_pair):
        """
        Insert autocomplete character with closed pair
        and update selection regions

        If sublime option `auto_match_enabled` turned on, next behavior have to
        be:

            when none selection

            `( => (<caret>)`
            `<caret>1 => ( => (<caret>1`

            when text selected

            `text => (text<caret>)`

        In other case:

            when none selection

            `( => (<caret>`

            when text selected

            `text => (<caret>`


        :param edit: sublime.Edit
        :param characters: str
        """
        regions = [a for a in self.view.sel()]
        self.view.sel().clear()

        for region in reversed(regions):
            next_char = self.view.substr(region.begin())
            # replace null byte to prevent error
            next_char = next_char.replace('\x00', '\n')

            following_text = next_char not in FOLLOWING_CHARS

            if self.auto_match_enabled:
                self.view.insert(edit, region.begin(), open_pair)
                position = region.end() + 1

                # IF selection is non-zero
                # OR after cursor no any text and selection size is zero
                # THEN insert closing pair
                if (region.size() > 0 or
                        not following_text and region.size() == 0):
                    self.view.insert(edit, region.end() + 1, close_pair)
                    position += (len(open_pair) - 1)
            else:
                self.view.replace(edit, region, open_pair)
                position = region.begin() + len(open_pair)

            self.view.sel().add(sublime.Region(position, position))
