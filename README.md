
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

### Elixir interpreter settings

By default this package will use default Elixir interpreter from the `PATH`.
Also you can set different interpreter for each Sublime Project.

To set project related Elixir interpreter you have to edit yours project config file.
By default project config name is `<project name>.sublime-project`

You can set Elixir interpreter, using for example the following:

    # <project name>.sublime-project
    {
        // ...

        "settings": {
            // ...
            "elixir_interpreter": "~/elixir-2.4.4/bin/elixir",
        }
    }

### Autocomplete on DOT

If you want auto-completion on dot, you can define a trigger in the
Sublime User or Python preferences:

    # User/Preferences.sublime-settings or User/Elixir.sublime-settings
    {
        // ...
        "auto_complete_triggers": [{"selector": "source.elixir", "characters": "."}],
    }

If you want auto-completion **ONLY** on dot and not while typing, you can
set (additionally to the trigger above):


    # User/Preferences.sublime-settings or User/Elixir.sublime-settings
    {
        // ...
        "auto_complete_selector": "-",
    }

### Go to definition

Find function / variable / module definition / anything else.

Shortcuts: `CTRL+SHIFT+G`

Mouse binding, was disabled, because sublime does not allows to set a scope so is active just in Elixir source files, and this can interfere with the global SublimeText configuration. But, if you want to use your mouse you can bind `CTRL + LeftMouseButton`:

    # User/Default.sublime-mousemap
    [
        {
            "modifiers": ["ctrl"], "button": "button1",
            "command": "super_elixir_goto",
            "press_command": "drag_select",
        }
    ]


### Code navigation

As Elixir code is structured as a set of hierarchical modules this feature lists all loaded modules and allows you to select one of them an go to it.

Shortcuts: `CTRL+ALT+M`

#### Show types and documentation

Just put your mouse on top of the term and you want documentation about. If it is a function it will list types first and then the documentation. It is not very pretty, we are working on it.


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
