"""This module exports the elixirc plugin class."""

import re

import sublime

from SublimeLinter.lint import Linter, persist

from .utils import find_mix_project


class Elixirc(Linter):
    """
    Provides an interface to elixirc.

    Error formats:

    1) Error type 1:
    |== Compilation error on file {filename} ==
    |** ({error_name}) {filename}:{line}: {message}
    |    ...

    2.1) Error type 2 -- source file first in trace:
    |== Compilation error on file {filename} ==
    |** ({error_name}) {message}
    |    {filename}:{line}
    |    ...

    2.2) Error type 2.2 -- lib files first in trace:
    |== Compilation error on file {filename} ==
    |** ({error_name}) {message}
    |    (libname) {other_filename}:{line}
    |    ...
    |    {filename}:{line}
    |    ...

    2.3) Error type 2.3 -- function names first in trace:
    |== Compilation error on file {filename} ==
    |** ({error_name}) {message}
    |    {function_name}()
    |    ...
    |    {filename}:{line}
    |    ...

    2.4) Error type 2.4 -- irrelevant files first in trace:
    |== Compilation error on file {filename} ==
    |** ({error_name}) {message}
    |    {filename_2}:{line_2}
    |    {filename_3}:{line_3}
    |    ...
    |    {filename}:{line}
    |    ...

    3) Error type 3:
    |** ({error_name}) {filename}:{line}: {message}
    |...<trace lines>...

    Warning formats:

    1) Warning type 1:
    |{filename}:{line}: warning: {message}

    2) Warning type 2:
    |warning: {message}
    |  {filename}:{line}

    In order to cover all cases we need a complex regex.
    Since a single regex does *not* allow to have several
    groups with the same name, we introduce custom group
    names.
    The group names are then transformed back to the ones
    expected by the Linter. This is done by overriding
    the split_match method.


    Examples (mix project of a Phoenix app):
    1)
    |== Compilation error on file web/router.ex ==
    |** (CompileError) web/router.ex:19: undefined function get/2
    |    ...

    2.1) #todo

    2.2) Insert a "resources :users, UserController" line in router.ex
    |== Compilation error on file web/router.ex ==
    |** (FunctionClauseError) no function clause matching in Phoenix.Router.Resource.build/3
    |    (phoenix) lib/phoenix/router/resource.ex:30: Phoenix.Router.Resource.build(:users, UserController, [])
    |    web/router.ex:20: (module)
    |    ...

    2.3) Modify line 2 to "use MyApp.Web, :dasdsadasda" in router.ex
    |== Compilation error on file web/controllers/page_controller.ex ==
    |** (UndefinedFunctionError) undefined function: MyApp.Web.controllers/0
    |    MyApp.Web.controllers()
    |    expanding macro: MyApp.Web.__using__/1
    |    web/controllers/page_controller.ex:2: MyApp.PageController (module)
    |    ...

    2.4) Define an virtual attribute with the same name as an existing association
    |== Compilation error on file web/models/user.ex ==
    |** (ArgumentError) field/association :roles is already set on schema
    |    lib/ecto/schema.ex:1196: Ecto.Schema.put_struct_field/3
    |    lib/ecto/schema.ex:1176: Ecto.Schema.association/5
    |    web/models/user.ex:20: (module)
    |    (stdlib) erl_eval.erl:669: :erl_eval.do_apply/6
    |    (elixir) lib/kernel/parallel_compiler.ex:97: anonymous fn/4 in Kernel.ParallelCompiler.spawn_compilers/8

    3) #todo

    """

    syntax = "elixir"
    tempfile_suffix = "ex"

    regex_parts = (
        # Error type 1
        r"== Compilation error on file (?P<e_file1>.+) ==\n"
        r"\*\* \(.+?\) (?P=e_file1):(?P<e_line1>\d+): (?P<e_msg1>.+)",

        # Error type 2
        r"== Compilation error on file (?P<e_file2>.+) ==\n"
        r"\*\* \(.+?\) (?P<e_msg2>.+)\n"
        r"(.+\n)*?"
        r"    (?P=e_file2):(?P<e_line2>\d+)",

        # Error type 3
        r"\*\* \(.+?\) (?P<e_file3>.+):(?P<e_line3>\d+): (?P<e_msg3>.+)",

        # Warning type 1
        r"(?P<w_file1>.+):(?P<w_line1>\d+): warning: (?P<w_msg1>.+)",

        # Warning type 2
        r"warning: (?P<w_msg2>.+)\n"
        r"  (?P<w_file2>.+):(?P<w_line2>\d+)"
    )

    regex = "|".join([r"^(?:%s)" % x for x in regex_parts])

    dummy_regex = re.compile(
        r"(?P<filename>.+):"
        r"(?P<line>\d+):"
        r"(?:(?P<error>error)|(?P<warning>warning)):"
        r"(?P<message>.+)",
        re.UNICODE
    )


    #
    # Make elixir 'lint' itself by at least checking the syntax
    # (see https://groups.google.com/forum/#!msg/elixir-lang-talk/B29noPHvQ-8/9JvSGPop7n0J)
    #
    exs_script = '''
case Code.string_to_quoted(System.argv |> Enum.fetch!(0) |> File.read!) do
  {:ok, _} -> :ok
  {:error, {l, msg1, msg2}} -> IO.puts("** (...) %s:#{l}: #{msg1}#{msg2}")
end
'''

    multiline = True
    executable = "elixir"

    def get_chdir(self, settings):
        if self.filename:
            return find_mix_project(self.filename)
        else:
            return super()().get_chdir(settings)

    def cmd(self):
        """Convert the linter options to command arguments."""
        if self.filename.endswith('.exs'):
            return [
                self.executable,
                '-e',
                self.exs_script % (self.filename),
                self.filename
            ]
        else:
            return [
                self.executable_path,
                '-S', 'mix', 'compile',
                '--warnings-as-errors',
                '--ignore-module-conflict',
            ]

    def find_errors(self, output):
        print(output)
        return super().find_errors(output)

    def split_match(self, match):
        """
        Pre-process the matchObject before passing it upstream.

        Several reasons for this:
          * unrelated library files can throw errors, and
            we only want errors from the linted file.
          * our regex contains more than just the basic
            capture groups (filename, line, message, etc.)
            but we still need to pass a match object that
            contains the above groups upstream.
          * Line is not reported for some macro errors
          * etc..

        """
        dummy_match = None

        if match:
            captures = match.groupdict()
            dummy_string = self.build_dummy_string(captures)
            dummy_match = re.match(self.dummy_regex, dummy_string)

        m = dummy_match.groupdict() if dummy_match else {}

        if m and self.filename.endswith(m['filename']):
            line = m['line']
            near = None
            if line:
                line = int(line) - 1
                near = self.find_near_what(m['message'], line)
            print(
                dummy_match,
                line,
                None,
                m['error'],
                m['warning'],
                m['message'],
                near
            )
            return (
                dummy_match,
                line,
                None,
                m['error'],
                m['warning'],
                m['message'],
                near
            )
        return (None,) * 7

    def find_near_what(self, message, err_line):
        words = re.compile('([\w\.]+)').findall(message)
        words.sort(key=lambda w: -len(w))
        for word in words:
            for region in self.view.find_all(word, sublime.LITERAL):
                line, _ = self.view.rowcol(region.a)
                if line == err_line:
                    return word

    def build_dummy_string(self, captures):
        """
        Build a string to be matched against self.dummy_regex.

        It is used to ensure that a matchObject with the
        appropriate group names is passed upstream.

        Returns a string with the following format:
        {filename}:{line}:{error_type}:{message}

        """
        if captures['e_file1'] is not None:
            persist.debug('Error type 1')
            dummy_str = '%s:%s:%s:%s' % (
                captures['e_file1'],
                captures['e_line1'],
                'error',
                captures['e_msg1']
            )
        elif captures['e_file2'] is not None:
            persist.debug('Error type 2')
            dummy_str = "%s:%s:%s:%s" % (
                captures['e_file2'],
                captures['e_line2'],
                'error',
                captures['e_msg2']
            )
        elif captures['e_file3'] is not None:
            persist.debug('Error type 3')
            dummy_str = "%s:%s:%s:%s" % (
                captures['e_file3'],
                captures['e_line3'],
                'error',
                captures['e_msg3']
            )
        elif captures['w_file1'] is not None:
            persist.debug('Warning type 1')
            dummy_str = "%s:%s:%s:%s" % (
                captures['w_file1'],
                captures['w_line1'],
                'warning',
                captures['w_msg1']
            )
        elif captures['w_file2'] is not None:
            persist.debug('Warning type 2')
            dummy_str = "%s:%s:%s:%s" % (
                captures['w_file2'],
                captures['w_line2'],
                'warning',
                captures['w_msg2']
            )
        else:
            persist.debug('No match')
            dummy_str = ""

        persist.debug("Dummy string: %s" % dummy_str)
        return dummy_str
