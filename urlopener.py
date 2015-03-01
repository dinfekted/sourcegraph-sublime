import sublime, sublime_plugin

from . import utilities
import webbrowser
import re

status_view = None
example_view = None
examples = None

class ExamplesUrlOpener(sublime_plugin.EventListener):
  def on_text_command(self, view, command, args):
    global example_view

    is_event_ignored = (
      command != 'drag_select' or
      'by' not in args or
      args['by'] != 'words' or
      example_view != view
    )

    if is_event_ignored:
      return

    self.view = view
    sublime.set_timeout(self._open_example, 100)
    return None

  def _open_example(self):
    global examples

    sel = self.view.sel()[0]

    line = self.view.substr(self.view.line(sel))
    if line[0] == '▶':
      url = re.sub(r':\d+\-\d+$', '', line[2:])
      webbrowser.open_new_tab(url)
      utilities.StatusTimeout(status_view, 'url has opened in browser')
      return

    example_number = self.view.substr(sublime.Region(0, sel.a)).count('_' * 110)
    example = examples[example_number]
    expression = r'<a[^>]*href="([^"]*)"[^>]*>(?:<span[^>]*>)?' + re.escape(self.view.substr(sel)) + '<'
    match = re.search(expression, example['SrcHTML'])
    if match == None:
      return

    webbrowser.open_new_tab(match.group(1))
    self.view.sel().clear()
    utilities.StatusTimeout(status_view, 'definition has opened in browser')