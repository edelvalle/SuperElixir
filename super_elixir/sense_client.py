import re
import socket
import struct
import subprocess
import os

from . import erlang
from .utils import find_mix_project
from . import settings


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ELIXIR_SENSE_EXEC = os.path.join(CURRENT_DIR, '../elixir_sense/run.exs')
SOCKET_RE = re.compile(rb'ok:localhost:(?P<socket>.+)\n')


ERLANG_ATOMS = {
    'nil': None,
    'true': True,
    'false': False,
}


def decode_term(term):
    if isinstance(term, dict):
        term = {
            decode_term(k): decode_term(v)
            for k, v in term.items()
        }
    elif isinstance(term, list):
        term = [decode_term(i) for i in term]
    elif isinstance(term, erlang.OtpErlangAtom):
        if isinstance(term.value, bytes):
            term = term.value.decode()
        else:
            term = term.value
        term = ERLANG_ATOMS.get(term, term)
    elif isinstance(term, erlang.OtpErlangBinary):
        term = term.value.decode()
    return term


SERVERS = {}


def get_elixir_sense(view):
    if view.file_name() is not None:
        project_path = find_mix_project(view.file_name())
        sense = SERVERS.get(project_path)
        if not sense:
            elixir_exec = settings.get_settings_param(
                view,
                'elixir_interpreter',
                'elixir'
            )
            sense = SERVERS[project_path] = ElixirSense(
                project_path,
                elixir_exec=elixir_exec,
            )
        return sense


class ElixirSense:
    def __init__(self, project_path, elixir_exec='elixir'):
        self.project_path = project_path
        self.elixir_exec = elixir_exec
        self._start_process()

    def _start_process(self):
        # start sub process
        self._proc = subprocess.Popen(
            [self.elixir_exec, ELIXIR_SENSE_EXEC, 'unix', '0', 'dev'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.project_path,
        )

        # connect socket
        first_line = self._proc.stdout.readline()
        match = SOCKET_RE.match(first_line)
        if not match:
            raise RuntimeError("Can't find the socket to talk to elixir_sense")

        socket_path = match.groupdict()['socket']
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(socket_path)
        print(socket_path)
        self._request_n = 0

    def _send_request(self, request, **kwargs):
        self._request_n += 1
        request = {
            'request_id': self._request_n,
            'auth_token': None,
            'request': request,
            'payload': kwargs
        }

        payload = erlang.term_to_binary(request)
        header = struct.pack('!I', len(payload))
        self._socket.send(header + payload)

        header = self._socket.recv(4)
        if header:
            (length,) = struct.unpack('!I', header)
            response = self._socket.recv(length)
            data = decode_term(erlang.binary_to_term(response))
            if data.get('error'):
                raise IOError(data)
            else:
                return data.get('payload')

    def __del__(self):
        print('Cleaning up Elixir')
        if hasattr(self, '_socket'):
            self._socket.close()
        self._proc.terminate()

    @property
    def all_modules(self):
        return self._send_request('all_modules')

    def signature(self, buffer, line, column):
        return self._send_request(
            'signature',
            buffer=buffer,
            line=line,
            column=column,
        )

    def docs(self, buffer, line, column):
        return self._send_request(
            'docs',
            buffer=buffer,
            line=line,
            column=column,
        )

    def definition(self, buffer, line, column):
        return self._send_request(
            'definition',
            buffer=buffer,
            line=line,
            column=column,
        )

    def suggestions(self, buffer, line, column):
        return self._send_request(
            'suggestions',
            buffer=buffer,
            line=line,
            column=column,
        )

    def expand_full(self, buffer, selected_code, line):
        return self._send_request(
            'expand_full',
            buffer=buffer,
            selected_code=selected_code,
            line=line,
        )

    def quote(self, code):
        return self._send_request('quote', code=code)

    def match(self, code):
        return self._send_request('match', code=code)

    def set_context(self, env, cwd):
        return self._send_request('set_context', env=env, cwd=cwd)


# code = """
# defmodule MyModule do
#   alias List, as: MyList
#   MyList.flatten(par0,
# end
# """

# e = ElixirSense('elixir_sense')
# from p`print` import pprint
# pprint(e.suggestions(code, 4, 13))
