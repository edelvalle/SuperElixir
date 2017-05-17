
# SuperElixir

This is a sublime plug-in that provide IDE like capabilities to sublime when working with the Elixir language. It does not include the syntax highlighting, please install ()[]


## Features

- Autocompletion
- Go to definition
- In-place documentation
- Navigation through modules
- Linting (Install SublimeLinter to use)

## Installation

### with Git

    cd ~/.config/sublime-text-3/Packages/
    git clone https://github.com/edelvalle/SuperElixir

### with [Sublime Package Control](http://wbond.net/sublime_packages/package_control)

 1. Open command pallet (default: `ctrl+shift+p`)
 2. Type `package control install` and select command `Package Control: Install Package`
 3. Type `SuperElixir` and select "SuperElixir"

Additional info installations you can find here [http://wbond.net/sublime_packages/package_control/usage](http://wbond.net/sublime_packages/package_control/usage).

## Configuration

Make sure you have at least Elixir 2.4.4 installed.

## Special thanks

- Elixir Sense: provides the Elixir introspection capabilities.
- PyErlang: allows the plug-in to talk to Elixir Sense.
- Sublime Jedi: provides the Python to do the go to definition in Sublime.
- Elixir Linting: provides most of the code for linting.
- Sublime Elixir: provides some helper functions to put all together.

## Room for improvement

- How documentation is shown. Right now is just shown in plain text and is kind of ugly, I think we should  use a markdown renderer for Sublime like [Sublime Markdown Popups](https://github.com/facelessuser/sublime-markdown-popups/).
- Improve the linting, so it just does not work on safe but in real-time typing.
- When sublime includes scopes in mouse map maybe we can have Ctrl-Click to go to definitions.
- Support Windows. Right now the communication with Elixir Sense is over Unix sockets; and Windows can't do that. But.. who writes Elixir in Windows any way? :trollface:
