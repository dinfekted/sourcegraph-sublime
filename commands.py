import sublime,sublime_plugin
import os, webbrowser

from . import utilities, urlopener

# based on Stackoverflow Search Plugin by Eric Martel (emartel@gmail.com / www.ericmartel.com)
# @author Leonid Shagabutdinov <leonid@shagabutdinov.com>

class SourcegraphSearchSelectionCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    for sel in self.view.sel():
      # TODO(sqs): get lang from current file extension
      query = {'q': utilities.textFromViewSel(self.view, sel)}
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

    documentation = [definition['Name']]
    documentation.append("=" * len(definition['Name']))

    if 'DocHTML' in definition:
      documentation.append("\n" + utilities.strip_tags(definition['DocHTML']))

    if len(definition['Data'].items()):
      documentation.append(self._format_example(definition))

    panel_name = 'describe'
    output = self.view.window().create_output_panel(panel_name)

    output.set_read_only(False)
    output.set_syntax_file('Packages/Go/Go.tmLanguage')

    output.run_command('append', {
      'characters': "\n".join(documentation)
    })

    output.set_read_only(True)
    self.view.window().run_command("show_panel", {
      "panel": "output." + panel_name
    })

    output.sel().clear()

  def _format_example(self, definition):
    max_key_length = 0
    max_value_length = 0

    for key, value in definition['Data'].items():
      key, value = str(key), str(value)

      if len(key) > max_key_length:
        max_key_length = len(key)

      if len(value) > max_value_length:
        max_value_length = len(value)

    formatter = ('| %' + str(max_key_length) + 's | %' +
      str(max_value_length) + 's |')

    first_line = formatter % ("", "")
    result = '-' * len(first_line)
    result.append(first_line)

    for key, value in definition['Data'].items():
      result.append(
        formatter % (key, str(value)) + "\n" +
        formatter % ("", "")
      )

    result.append('-' * len(first_line))
    return result

class SourcegraphUsagesCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    sublime.set_timeout_async(self.execute, 0)

  def execute(self):
    response = utilities.call_srclib(self.view, self.view.sel()[0])

    if not response['Examples']:
      utilities.StatusTimeout(self.view, 'no examples found')
      return

    panel_name = 'examples'
    output = self.view.window().create_output_panel(panel_name)

    urlopener.status_view = self.view
    urlopener.example_view = output
    urlopener.examples = response['Examples']

    output.set_read_only(False)
    output.set_syntax_file('Packages/Go/Go.tmLanguage')

    for example in response['Examples']:
      output.run_command('append', {
        'characters': self.format(example, show_src=True)
      })

    output.set_read_only(True)
    self.view.window().run_command("show_panel", {
      "panel": "output." + panel_name
    })

    output.sel().clear()

  def format(self, example, show_src):
    result = u'▶ %s/%s:%s-%s\n' % (example['Repo'], example['File'],
      example['StartLine'], example['EndLine'])

    if show_src:
      result += u"\n" + utilities.strip_tags(example['SrcHTML'])
      result += u"\n" + "_" * 110 + "\n\n"

    return result