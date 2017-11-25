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

        location = locations[0]
        on_character = view.substr(location)
        prev_char = view.substr(location - 1)

        param_auto_completion = (
            on_character in FOLLOWING_CHARS and
            prev_char == '('
        )

        if param_auto_completion:
            location -= 1

        f_name = view.substr(view.word(location))
        buffer, line, column = get_buffer_line_column(view, location)

        sense = get_elixir_sense(view)
        suggestions = sense.suggestions(buffer, line, column)

        completions = []
        for s in suggestions:
            if (s['type'] == 'hint' or
                    param_auto_completion and
                    s['name'] != f_name):
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

            if self._is_function(s):
                arity = s.get('arity')
                args = s.get('args', '').split(',')

                if not args and arity:
                    args = ['_'] * arity

                completion_args = [
                    '${%s:%s}' % (i, a) for i, a in enumerate(args, 1)
                ]

                if param_auto_completion:
                    c['show'] = ', '.join(args)
                    c['completion'] = ', '.join(completion_args)
                else:
                    c['show'] += '(' + ', '.join(args) + ')'
                    c['completion'] += '(' + ', '.join(completion_args) + ')'

            completions.append(c)

        completions.sort(key=lambda c: (
            len(c['name']) - len(c['name'].strip('_')),  # less underscores wins
            c['name'],  # alphabetically
        ))

        completions = [
            ['{show}\t{hint}'.format(**c), c['completion']]
            for c in completions
        ]
        return (
            completions,
            sublime.INHIBIT_WORD_COMPLETIONS |
            sublime.INHIBIT_EXPLICIT_COMPLETIONS
        )

    def _is_function(self, suggestion):
        return (
            suggestion['type'].endswith('function') or
            suggestion['type'] == 'macro'
        )

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

    def run(self, edit):
        self._insert_characters(edit, '(', ')')
        sublime.set_timeout(
            (lambda: self.view.run_command(
                'auto_complete',
                {
                    'next_completion_if_showing': False,
                    'auto_complete_commit_on_tab': True,
                }
            )),
            0
        )

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
