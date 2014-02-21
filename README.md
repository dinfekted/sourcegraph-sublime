# Sourcegraph for Sublime Text 3

A plugin for [Sublime Text 3](http://www.sublimetext.com/3) that integrates with
the [Sourcegraph](https://sourcegraph.com) code search engine to provide:

* Project-aware documentation and jump-to-definition for RubyGems
* Quick search interface to Sourcegraph

This plugin currently only supports Ruby, and only docs and definitions for
external RubyGems are available. (No local source analysis is performed yet;
that's a TODO.) We plan to add support for Python, Go, and JavaScript soon.

## How to use

**Install**: clone this git repository to your Packages folder.

**Requirements**: A `ruby` with the `bundler` gem must exist in your `$PATH`.

### Search current selection on Sourcegraph (context menu)

Right-click on an identifier or a selection and select _Search on Sourcegraph_
to get a list of matching modules, classes, and methods. Documentation and
method arguments are displayed (if available). Select an item from the list to
view it on Sourcegraph, with full documentation, usage examples, etc.

Sourcegraph searches for your query in all of the RubyGems that your current
project uses. The nearest ancestor Gemfile (from the current file) is used to
determine the gems that are in use.

A list of the gem names, plus your current selection, is sent to the Sourcegraph
server to deliver you the results. If Sourcegraph hasn't processed a gem, no
results will be returned from it. [Contact us](https://sourcegraph.com/contact)
to report issues.

### Search anything on Sourcegraph (palette)

Open the palette (ctrl-shift-P or cmd-shift-P) and select _Sourcegraph: Search
from input_, and then type a [Sourcegraph search
query](https://sourcegraph.com/help/users/search). The search results will open
in a new tab in your most recently browser window.

## Reporting issues

Report issues related to this plugin on the [GitHub
repository](https://github.com/sourcegraph/sourcegraph-sublime). Report issues
related to [Sourcegraph.com](https://sourcegraph.com) at the [site issue
tracker](https://github.com/sourcegraph/sourcegraph.com/issues/new) or to
[@srcgraph](https://twitter.com/srcgraph).

## Implementation details

Sourcegraph uses [RubySonar](https://github.com/yinwang0/rubysonar) and
[YARD](https://github.com/lsegal/yard) to analyze open-source RubyGems. We're
currently in the process of open-sourcing all of the analysis components as part
of the [GraphKit](http://graphkit.org/) project.


## TODOs/notes

* Currently this plugin hits the [Sourcegraph](https://sourcegraph.com) API, which is undocumented. We're working to fix that.
* We're also working on adding support for local Ruby analysis using [RubySonar](https://github.com/yinwang0/rubysonar). This means you can get docs and jump-to-definition for local files, not just external RubyGems.
* Upload to Package Control.


## Contributors

* [Quinn Slack](https://sourcegraph.com/sqs)
* [Yin Wang](https://sourcegraph.com/yinwang0) (developed [RubySonar](https://github.com/yinwang0/rubysonar), which powers the Ruby language analysis)
