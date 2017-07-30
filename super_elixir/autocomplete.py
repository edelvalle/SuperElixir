import re

import sublime
import sublime_plugin

from .utils import is_elixir, get_buffer_line_column
from .sense_client import get_elixir_sense


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
            -buffer.count(c['name']),
            len(c['name']) - len(c['name'].strip('_')),
            c['name'],
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
