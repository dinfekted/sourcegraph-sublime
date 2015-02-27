import sublime
import sublime_plugin

import sys
import threading
import webbrowser

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import json
import subprocess
import os

BASE_URL = "https://sourcegraph.com"
VIA = "sourcegraph-sublime-1"

# log = logging.getLogger("sourcegraph")
# stderr_hdlr = logging.StreamHandler(sys.stderr)
# stderr_hdlr.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
# log.handlers = [stderr_hdlr]
# log.setLevel(logging.INFO)

settings = {}

def getenv():
    env = os.environ
    gopath = settings.get('gopath')
    if gopath:
        env['GOPATH'] = gopath
    goroot = settings.get('goroot')
    if goroot:
        env['GOROOT'] = goroot
    return env

def plugin_loaded():
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
      print('waiting for file to load...')
    else:
      print('timed out waiting for file load')

def call_srclib(view, sel, tail = []):
  # import time
  # time.sleep(2) # for developing
  command = [
    settings.get('which_src'),
    "api",
    "describe",
    "--file",
    view.file_name(),
    "--start-byte",
    str(sel.begin())
  ]

  command += tail

  data = check_output(command, env=getenv())
  return json.loads(data.decode("utf8"))

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
