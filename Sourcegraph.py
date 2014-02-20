# based on Stackoverflow Search Plugin by Eric Martel (emartel@gmail.com / www.ericmartel.com)

import logging
import sublime
import sublime_plugin
import sys
import threading

import webbrowser
import urllib.request
import json
import os.path
import subprocess
from urllib.parse import quote, urlencode

BASE_URL = "http://localhost:3000"
VIA = "sourcegraph-sublime-1"
DEFAULT_LIBS = "rails,ruby"

log = logging.getLogger("sourcegraph")
stderr_hdlr = logging.StreamHandler(sys.stderr)
stderr_hdlr.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
log.handlers = [stderr_hdlr]
log.setLevel(logging.INFO)

def symbolURL(endpoint, params):
    url = BASE_URL + '/api/assist/%s?_via=%s&%s' % (endpoint, VIA, urlencode(params))
    return url

def gotoSourcegraph(params):
    webbrowser.open_new_tab(symbolURL("goto", params))

def libsForFile(filename):
    dir = filename
    while True:
        parentDir = os.path.dirname(dir)
        if dir == parentDir:
            # we're at the root dir
            break
        dir = parentDir
        gemfilePath = os.path.join(dir, 'Gemfile')
        if os.path.exists(gemfilePath):
            log.info('Gemfile at %s' % gemfilePath)
            try:
                out = subprocess.check_output(['ruby', '-rbundler', '-e', 'Bundler.load.dependencies_for.each{|d|puts d.name}'], cwd=dir)
                libs = out.decode("utf-8").strip().split("\n")
                return ','.join(libs)
            except Exception as e:
                log.warn('Warning: failed to list gems in %s: %s (using default libs %s)' % (gemfilePath, e, DEFAULT_LIBS))
        
    log.info('No Gemfile found in any ancestor directory of %s (using default libs %s)' % (filename, DEFAULT_LIBS))
    return DEFAULT_LIBS
        

def paramsFromViewSel(view, sel):
    # if the user didn't select anything, search the currently highlighted word
    if sel.empty():
        sel = view.word(sel)
    text = view.substr(sel)
    return {"libs": libsForFile(view.file_name()), "lang": "ruby", "name": text}

class SourcegraphSearchSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            gotoSourcegraph(paramsFromViewSel(self.view, sel))

class SourcegraphShowInfoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            InfoThread(self.view, paramsFromViewSel(self.view, sel)).start()

class InfoThread(threading.Thread):
    def __init__(self, view, params):
        self.view = view
        self.params = params
        threading.Thread.__init__(self)

    def run(self):
        def show_popup_menu():
            try:
                resp = urllib.request.urlopen(symbolURL("info", self.params))
                data = resp.read().decode("utf-8")
                log.info('DATA: %s' % data)
                self.results = json.loads(data)
                if len(self.results) > 0:
                    choices = ['%s   —   %s' % (r["specificPath"], r["repo"]) for r in self.results]
                else:
                    choices = ['(no results found)']
                self.view.show_popup_menu(choices, self.on_done)
            except Exception as e:
                log.error('failed to get symbols: %s' % e)
        sublime.set_timeout(show_popup_menu, 10)

    def on_done(self, picked):
        if picked == -1 or len(self.results) == 0:
            return
        sym = self.results[picked]
        webbrowser.open_new_tab(BASE_URL + ('/%s/symbols/%s/%s' % (quote(sym['repo']), quote(sym['lang']), quote(sym['path']))))

class SourcegraphSearchFromInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Get the search item
        self.window.show_input_panel('Search Sourcegraph for', '',
            self.on_done, self.on_change, self.on_cancel)

    def on_done(self, input):
        webbrowser.open_new_tab(BASE_URL + '/search?q=%s&_via=%s' % (quote(input), VIA))

    def on_change(self, input):
        pass

    def on_cancel(self):
        pass
