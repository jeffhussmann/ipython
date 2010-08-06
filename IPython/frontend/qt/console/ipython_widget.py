# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.core.usage import default_banner
from frontend_widget import FrontendWidget


class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    # The default stylesheet for prompts, colors, etc.
    default_stylesheet = """
        .error { color: red; }
        .in-prompt { color: navy; }
        .in-prompt-number { font-weight: bold; }
        .out-prompt { color: darkred; }
        .out-prompt-number { font-weight: bold; }
    """

    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, parent=None):
        super(IPythonWidget, self).__init__(parent)

        # Initialize protected variables.
        self._magic_overrides = {}
        self._prompt_count = 0

        # Set a default stylesheet.
        self.set_style_sheet(self.default_stylesheet)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _execute(self, source, hidden):
        """ Reimplemented to override magic commands.
        """
        magic_source = source.strip()
        if magic_source.startswith('%'):
            magic_source = magic_source[1:]
        magic, sep, arguments = magic_source.partition(' ')
        if not magic:
            magic = magic_source

        callback = self._magic_overrides.get(magic)
        if callback:
            output = callback(arguments)
            if output:
                self.appendPlainText(output)
            self._show_interpreter_prompt()
        else:
            super(IPythonWidget, self)._execute(source, hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Reimplemented to use the 'run' magic.
        """
        self.execute('run %s' % path, hidden=hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _get_banner(self):
        """ Reimplemented to return IPython's default banner.
        """
        return default_banner

    def _show_interpreter_prompt(self):
        """ Reimplemented for IPython-style prompts.
        """
        self._prompt_count += 1
        prompt_template = '<span class="in-prompt">%s</span>'
        prompt_body = '<br/>In [<span class="in-prompt-number">%i</span>]: '
        prompt = (prompt_template % prompt_body) % self._prompt_count
        self._show_prompt(prompt, html=True)

        # Update continuation prompt to reflect (possibly) new prompt length.
        cont_prompt_chars = '...: '
        space_count = len(self._prompt.lstrip()) - len(cont_prompt_chars)
        cont_prompt_body = '&nbsp;' * space_count + cont_prompt_chars
        self._continuation_prompt_html = prompt_template % cont_prompt_body

    #------ Signal handlers ----------------------------------------------------

    def _handle_execute_error(self, reply):
        """ Reimplemented for IPython-style traceback formatting.
        """
        content = reply['content']
        traceback_lines = content['traceback'][:]
        traceback = ''.join(traceback_lines)
        traceback = traceback.replace(' ', '&nbsp;')
        traceback = traceback.replace('\n', '<br/>')

        ename = content['ename']
        ename_styled = '<span class="error">%s</span>' % ename
        traceback = traceback.replace(ename, ename_styled)

        self.appendHtml(traceback)

    def _handle_pyout(self, omsg):
        """ Reimplemented for IPython-style "display hook".
        """
        prompt_template = '<span class="out-prompt">%s</span>'
        prompt_body = 'Out[<span class="out-prompt-number">%i</span>]: '
        prompt = (prompt_template % prompt_body) % self._prompt_count
        self.appendHtml(prompt)
        self.appendPlainText(omsg['content']['data'] + '\n')

    #---------------------------------------------------------------------------
    # 'IPythonWidget' interface
    #---------------------------------------------------------------------------

    def set_magic_override(self, magic, callback):
        """ Overrides an IPython magic command. This magic will be intercepted
            by the frontend rather than passed on to the kernel and 'callback'
            will be called with a single argument: a string of argument(s) for
            the magic. The callback can (optionally) return text to print to the
            console.
        """
        self._magic_overrides[magic] = callback

    def remove_magic_override(self, magic):
        """ Removes the override for the specified magic, if there is one.
        """
        try:
            del self._magic_overrides[magic]
        except KeyError:
            pass

    def set_style_sheet(self, stylesheet):
        """ Sets the style sheet.
        """
        self.document().setDefaultStyleSheet(stylesheet)


if __name__ == '__main__':
    from IPython.frontend.qt.kernelmanager import QtKernelManager

    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager.
    kernel_manager = QtKernelManager()
    kernel_manager.start_kernel()
    kernel_manager.start_channels()

    # Launch the application.
    app = QtGui.QApplication([])
    widget = IPythonWidget()
    widget.kernel_manager = kernel_manager
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    app.exec_()
