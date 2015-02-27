import sublime
import sublime_plugin

import os
from . import utilities

import webbrowser

# based on Stackoverflow Search Plugin by Eric Martel (emartel@gmail.com / www.ericmartel.com)
# @author Leonid Shagabutdinov <leonid@shagabutdinov.com>

class SourcegraphSearchSelectionCommand(sublime_plugin.TextCommand):

  def run(self, edit):

    for sel in self.view.sel():
      # TODO(sqs): get lang from current file extension
      query = {
        'q': utilities.textFromViewSel(self.view, sel)
      }
      utilities.gotoSourcegraph('/search', query)


class SourcegraphSearchFromInputCommand(sublime_plugin.WindowCommand):

  def run(self):
    # Get the search item
    self.window.show_input_panel('Search Sourcegraph for', '',
      self.on_done, self.on_change, self.on_cancel)

  def on_done(self, input):
    utilities.gotoSourcegraph('/search', {'q': input})

  def on_change(self, input):
    pass

  def on_cancel(self):
    pass


class SourcegraphJumpToDefinition(sublime_plugin.TextCommand):

  def run(self, edit):
    sublime.set_timeout_async(self.execute, 0)

  def execute(self):
    response = utilities.call_srclib(self.view, self.view.sel()[0],
      ['--no-examples'])

    if 'Def' not in response:
      utilities.StatusTimeout(self.view, 'definition not found')
      return

    definition = response['Def']

    if 'Repo' in definition:
      # TODO: Resolve to local file - waiting for Src API to expose method for this
      url = utilities.BASE_URL + "/%s/.%s/%s/.def/%s" % (definition['Repo'],
          definition['UnitType'], definition['Unit'], definition['Path'])
      webbrowser.open_new_tab(url)
      utilities.StatusTimeout(self.view, 'definition is opened in browser')
      return

    file_path = definition['File']
    if not os.path.isfile(file_path):
      utilities.StatusTimeout(self.view, 'definition found but file %s does ' +
        'not exist.' % file_path)
      return

    view = self.view.window().open_file(file_path)
    sublime.set_timeout(lambda: utilities.show_location(view,
      definition['DefStart'], definition['DefEnd']), 10)

    utilities.StatusTimeout(self.view, 'definition found')

class SourcegraphDescribeCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    sublime.set_timeout_async(self.execute, 0)

  def execute(self):
    response = utilities.call_srclib(self.view, self.view.sel()[0],
      ['--no-examples'])

    if 'Def' not in response:
      utilities.StatusTimeout(self.view, 'definition not found')
      return

    definition = response['Def']

    choices = [definition['Name']]

    if 'DocHTML' in definition:
      choices.append(utilities.strip_tags(definition['DocHTML']))

    for k, v in definition['Data'].items():
      choices.append('%s: %s' % (k, str(v)))

    # ST2 lacks view.show_popup_menu
    if hasattr(self.view, "show_popup_menu"):
      self.view.show_popup_menu(choices, self.goto_describe_link,
            sublime.MONOSPACE_FONT)
    else:
      # TODO(sqs): multi-line rows don't work in show_quick_panel
      self.view.window().show_quick_panel(choices, self.goto_describe_link,
        sublime.MONOSPACE_FONT)

  def goto_describe_link(self, picked):
    if picked == -1 or len(self.results) == 0:
      return

    sym = self.results[picked]
    url = utilities.BASE_URL + ('/%s/symbols/%s/%s' % (quote(sym['repo']),
      quote(sym['lang']), quote(sym['path'])))

    webbrowser.open_new_tab(url)


class SourcegraphUsagesCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    sublime.set_timeout_async(self.execute, 0)

  def execute(self):
    response = utilities.call_srclib(self.view, self.view.sel()[0])

    #### show examples in output panel
    # get_output_panel doesn't "get" the panel, it *creates* it,
    # so we should only call get_output_panel once
    panel_name = 'examples'
    output = self.view.window().create_output_panel(panel_name)
    output.set_read_only(False)
    output.set_syntax_file('Packages/Go/Go.tmLanguage')

    if response['Examples']:
      for example in response['Examples']:
        output.run_command('append', {
          'characters': self.format(example, show_src=True)
        })
    else:
      ex_str = "No examples"
      if response['Def'] and response['Def']['Path']:
          ex_str += " for " + response['Def']['Path']
      output.run_command('append', {'characters': ex_str})

    output.set_read_only(True)
    self.view.window().run_command("show_panel", {
      "panel": "output." + panel_name
    })

  def format(self, example, show_src):
    result = u'▶ %s/%s:%s-%s\n' % (example['Repo'], example['File'],
      example['StartLine'], example['EndLine'])

    if show_src:
        result += u"\n" + utilities.strip_tags(example['SrcHTML'])
        result += u"\n▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁\n\n"

    return result