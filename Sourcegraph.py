# based on Stackoverflow Search Plugin by Eric Martel (emartel@gmail.com / www.ericmartel.com)
# coding=utf-8

import logging
import sublime
import sublime_plugin
import sys
import threading

import webbrowser
try:
    from urllib.request import urlopen
    from urllib.parse import urlencode, quote
except ImportError:
    from urllib import urlopen, urlencode, quote
import json
import os.path
import subprocess

BASE_URL = "https://sourcegraph.com"
VIA = "sourcegraph-sublime-1"

log = logging.getLogger("sourcegraph")
stderr_hdlr = logging.StreamHandler(sys.stderr)
stderr_hdlr.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
log.handlers = [stderr_hdlr]
log.setLevel(logging.INFO)
settings = {}

def plugin_loaded ():
    global settings
    settings = sublime.load_settings('Sourcegraph.sublime-settings')

def gotoSourcegraph(path, params):
    params['_via'] = VIA
    webbrowser.open_new_tab(BASE_URL + path + '?' + urlencode(params))

def textFromViewSel(view, sel):
    # if the user didn't select anything, search the currently highlighted word
    if sel.empty():
        sel = view.word(sel)
    return view.substr(sel)

def show_location(view, start, end, retries=0):
  if not view.is_loading():
    def_region = sublime.Region(start, end)

    view.sel().clear()
    view.sel().add(def_region)
    view.show_at_center(start)
  else:
    if retries < 10:
      sublime.set_timeout(lambda: show_location(view, start, end, retries+1), 10)
      log.info('waiting for file to load...')
    else:
      log.error('timed out waiting for file load')

class SourcegraphJumpToDefinition(sublime_plugin.TextCommand):
  def run(self, edit):
    for sel in self.view.sel():
      InfoThread(self.view, sel, 'jump').start()

class SourcegraphSearchSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            # TODO(sqs): get lang from current file extension
            gotoSourcegraph('/search', {'q': textFromViewSel(self.view, sel)})

class SourcegraphDescribeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            InfoThread(self.view, sel, 'describe').start()

class SourcegraphUsagesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            InfoThread(self.view, sel, 'usages').start()

class InfoThread(threading.Thread):
    def __init__(self, view, sel, what):
        self.view = view
        self.sel = sel
        self.what = what
        threading.Thread.__init__(self)

    def run(self):
        def show_popup_menu():
            try:
                file_name = self.view.file_name()
                cmd = [settings.get('which_src'), "api", "describe", "--file", file_name, "--start-byte", str(self.sel.begin())]
                if self.what != 'usages':
                    cmd.append("--no-examples")
                data = check_output(cmd)
                self.resp = json.loads(data.decode("utf8"))

                if self.what == 'describe':
                    defn = self.resp['Def']
                    choices = [defn['Name']]
                    if 'DocHTML' in defn:
                        choices.append(strip_tags(defn['DocHTML']))
                    for k, v in defn['Data'].items():
                        choices.append('%s: %s' % (k, str(v)))
                    log.error(defn)
                    # ST2 lacks view.show_popup_menu
                    if hasattr(self.view, "show_popup_menu"):
                        self.view.show_popup_menu(choices, self.on_done, sublime.MONOSPACE_FONT)
                    else:
                        # TODO(sqs): multi-line rows don't work in show_quick_panel
                        self.view.window().show_quick_panel(choices, self.on_done, sublime.MONOSPACE_FONT)
                elif self.what == 'usages':
                    #### show examples in output panel
                    # get_output_panel doesn't "get" the panel, it *creates* it,
                    # so we should only call get_output_panel once
                    panel_name = 'examples'
                    v = self.view.window().create_output_panel(panel_name)
                    v.set_read_only(False)
                    v.set_syntax_file('Packages/Go/Go.tmLanguage')
                    #region = sublime.Region(0, v.size())
                    #v.erase(None, region)
                    #v.insert(None, 0, "foo")
                    #v.show(0)
                    #v.run_command('panel_output', {'text': "foo\n"})
                    if self.resp['Examples']:
                        for x in self.resp['Examples']:
                            v.run_command('append', {'characters': format_example(x, show_src=True)})
                    v.set_read_only(True)
                    self.view.window().run_command("show_panel", {"panel": "output." + panel_name})
                elif self.what == 'jump':
                    Def = self.resp['Def']
                    if 'Repo' in Def:
                        # TODO: Resolve to local file - waiting for Src API to expose method for this
                        url = BASE_URL + "/%s/.%s/%s/.def/%s" % (Def['Repo'], Def['UnitType'], Def['Unit'], Def['Path'])
                        webbrowser.open_new_tab(url)
                    else:
                        file_path = Def['File']
                        if os.path.isfile(file_path): # Ensure that file exists before trying to open
                          view = self.view.window().open_file(file_path)
                          sublime.set_timeout(lambda: show_location(view, Def['DefStart'], Def['DefEnd']), 10)
                        else:
                          log.error('File %s does not exist.' % file_path)

            except Exception as e:
                log.error('src api describe failed: %s' % e)

        sublime.set_timeout(show_popup_menu, 10)

    def on_done(self, picked):
        if picked == -1 or len(self.results) == 0:
            return
        sym = self.results[picked]
        webbrowser.open_new_tab(BASE_URL + ('/%s/symbols/%s/%s' % (quote(sym['repo']), quote(sym['lang']), quote(sym['path']))))

def format_example(x, show_src):
    xstr = u'▶ %s/%s:%s-%s\n' % (x['Repo'], x['File'], x['StartLine'], x['EndLine'])
    if show_src:
        xstr += u"\n" + strip_tags(x['SrcHTML'])
        xstr += u"\n▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁\n\n"
    return xstr

class SourcegraphSearchFromInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Get the search item
        self.window.show_input_panel('Search Sourcegraph for', '',
            self.on_done, self.on_change, self.on_cancel)

    def on_done(self, input):
        gotoSourcegraph('/search', {'q': input})

    def on_change(self, input):
        pass

    def on_cancel(self):
        pass

# Python 2.6 doesn't have subprocess.check_output, so backport it. (From
# https://gist.github.com/edufelipe/1027906.)
def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    Backported from Python 2.7 as it's implemented as pure python on stdlib.

    >>> check_output(['/usr/bin/python', '--version'])
    Python 2.6.2
    """
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output

# from http://stackoverflow.com/a/925630
try:
    # python 3
    from html.parser import HTMLParser
except:
    # python 2
    from HTMLParser import HTMLParser
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
