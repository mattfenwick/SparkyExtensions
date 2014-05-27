# -----------------------------------------------------------------------------
# For starting Sparky within Chimera.
#
# This differs from the normal Sparky startup script in that sys.argv is
# not parsed for files to load and X windows options, sys.stdout and
# sys.stderr are not redirected to the Sparky shell, and the Tk main loop
# is not started since Chimera has already started it.
#
# This will cause a core dump if the _tkinter.so used by Chimera was compiled
# with thread support (standard on Windows).  Sparky Tk event dispatching
# is not compatible with _tkinter with threads.
#

import sys

sys.path = ['/usr/local/sparky/python'] + sys.path

import sparky

sparky.start_session(use_command_line = 0, redirect_stdio = 0,
                     start_event_loop = 0)
