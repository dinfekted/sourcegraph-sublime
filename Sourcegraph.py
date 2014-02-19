# based on Stackoverflow Search Plugin by Eric Martel (emartel@gmail.com / www.ericmartel.com)

import logging
import sublime
import sublime_plugin
import sys

import webbrowser

log = logging.getLogger("sourcegraph")
stderr_hdlr = logging.StreamHandler(sys.stderr)
stderr_hdlr.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
log.handlers = [stderr_hdlr]
log.setLevel(logging.INFO)

def gotoSourcegraph(lib, lang, name):
    log.info("sourcegraph: lib=%s lang=%s name=%s" % (lib, lang, name))
    url = 'http://localhost:3000/api/assist/info?lib=%s&lang=%s&name=%s' % (lib, lang, name)
    webbrowser.open_new_tab(url)

class SourcegraphSearchSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for selection in self.view.sel():
            # if the user didn't select anything, search the currently highlighted word
            if selection.empty():
                selection = self.view.word(selection)
            text = self.view.substr(selection)
            gotoSourcegraph("rails", "ruby", text)


class SourcegraphSearchFromInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Get the search item
        self.window.show_input_panel('Search Sourcegraph for', '',
            self.on_done, self.on_change, self.on_cancel)

    def on_done(self, input):
        SearchFor(input)

    def on_change(self, input):
        pass

    def on_cancel(self):
        pass
