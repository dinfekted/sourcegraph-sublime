# Sourcegraph for Sublime Text 2 & 3

A plugin for [Sublime Text 2 & 3](http://www.sublimetext.com/) that integrates
with [srclib](https://srclib.org) and the
[Sourcegraph](https://sourcegraph.com) code search engine to provide:

* Project-aware documentation, jump-to-definition, and find usages
* Quick search interface to [Sourcegraph](https://sourcegraph.com)


## How to use

**Install:** clone this git repository to your Packages folder.

**Requirements:** The [srclib](https://srclib.org) src tool must be installed,
as well as srclib toolchains for the languages you want to use this plugin
on.

Note: this plugin queries [Sourcegraph](https://sourcegraph.com). Your private
code is never uploaded, but information about the identifier under the cursor
is used to construct the query. This includes information such as the clone
URL of the repository you're currently in, the filename and character
position, and the name of the identifier's definition.

### Documentation & type (context menu)

Right-click on an identifier or a selection and select _Documentation & type_
to see documentation and type information about what the identifier refers to.

### Usages & examples (context menu)

Right-click on an identifier or a selection and select _Usages & examples_ to
see references to the identifier's definition in the same project (local) and
in other open-source projects (global).

### Search anything on Sourcegraph (palette)

Open the palette (ctrl-shift-P or cmd-shift-P) and select _Sourcegraph: Search
from input_, and then type a [Sourcegraph search
query](https://sourcegraph.com/help/doc#search-keywords). The search results
will open in a new tab in your most recently browser window.

Or, select some text in the editor and select _Sourcegraph: Search from
selection_ in the palette to search for your selection on Sourcegraph.

## Reporting issues

Report issues related to this plugin on the [GitHub
repository](https://github.com/sourcegraph/sourcegraph-sublime). Report issues
related to [Sourcegraph.com](https://sourcegraph.com) at the [site issue
tracker](https://github.com/sourcegraph/sourcegraph.com/issues/new) or to
[@srcgraph](https://twitter.com/srcgraph).

## TODOs/notes


* Upload to Package Control.
* There's no show_popup_menu API in ST2, so the list of matches in ST2 is not displayed next to the cursor. (In ST3, it is.)
