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
  if sel.empty():
    sel = view.word(sel)

  return view.substr(sel)

def show_location(view, start, end, retries=0):
  if not view.is_loading():
    view.sel().clear()
    view.sel().add(sublime.Region(start, end))
    view.show_at_center(start)

    view.run_command('move', {
      'by': 'characters',
      'forward': False,
      'extend': True
    })

    view.run_command('move', {
      'by': 'characters',
      'forward': True,
      'extend': True
    })
  else:
    if retries < 10:
      sublime.set_timeout(lambda: show_location(view, start, end, retries+1), 10)
      print('waiting for file to load...')
    else:
      print('timed out waiting for file load')

def call_srclib(view, sel, tail = []):
  view.set_status('sourcegraph_command', 'sourcegraph: executing src command...')
  StatusAnimation(view).animate()

  # import time
  # time.sleep(5) # for developing
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

  try:
    data = check_output(command, env=getenv())
    return json.loads(data.decode("utf8"))
  except subprocess.CalledProcessError as error:
    report_error(str(error) + "\n" + str(error.output))
    raise error
  except ValueError as error:
    report_error("failed to parse json (" + str(error) + "), response: " +
      str(data))
    raise error
  except Exception as error:
    report_error(str(error))
    raise error
  finally:
    view.erase_status('sourcegraph_command')

def report_error(message):
  output = sublime.active_window().new_file()
  output.set_scratch(True)
  text = (sublime.load_resource('Packages/Sourcegraph/error.txt') +
    ' ' + str(message))
  output.run_command('insert', {'characters': text})
  StatusTimeout(sublime.active_window().active_view(), 'error has occured')

class StatusTimeout():

  def __init__(self, view, status, timeout = 5000):
    self.view = view
    self.view.set_status('sourcegraph_status', 'sourcegraph: ' + status)
    sublime.set_timeout(self._hide, timeout)

  def _hide(self):
    self.view.erase_status('sourcegraph_status')

class StatusAnimation():

  def __init__(self, view):
    self.view = view

  def animate(self):
    sublime.set_timeout(self._animate, 250)

  def _animate(self):
    status = self.view.get_status('sourcegraph_command')
    if status != None and status.endswith('...'):
      if status.endswith('.' *  10):
        status = status[:-7]

      self.view.set_status('sourcegraph_command', status + '.')
      sublime.set_timeout(self._animate, 250)

# Python 2.6 doesn't have subprocess.check_output, so backport it. (From
# https://gist.github.com/edufelipe/1027906.)
def check_output(*popenargs, **kwargs):
  r"""Run command with arguments and return its output as a byte string.

  Backported from Python 2.7 as it's implemented as pure python on stdlib.

  >>> check_output(['/usr/bin/python', '--version'])
  Python 2.6.2
  """
  process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    *popenargs, **kwargs)

  output, err = process.communicate()
  retcode = process.poll()
  if retcode:
    cmd = kwargs.get("args")
    if cmd is None:
      cmd = popenargs[0]

    error = subprocess.CalledProcessError(retcode, cmd)
    error.output = str(output) + "\n" + str(err)
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