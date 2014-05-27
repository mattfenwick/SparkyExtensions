# -----------------------------------------------------------------------------
# Choose multiple spectrum files and open them.  This is a convenience for
# opening a large set of spectra, for example, a sequence of spectra for
# determining T1 or T2 by fitting exponentially decaying peak heights.
#
import Tkinter

import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class open_spectra_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Open Multiple Spectra')

    proj = session.project
    mfs = tkutil.multiple_file_selection(self.top, proj.sparky_directory)
    mfs.frame.pack(side = 'top', anchor = 'nw', fill = 'both', expand = 1)
    self.files = mfs

    r = Tkinter.Label(self.top, justify = 'left')
    r.pack(side = 'top', anchor = 'nw')
    self.result = r
    
    br = tkutil.button_row(self.top,
                           ('Open', self.open_cb),
                           ('Cancel', self.close_cb),
                           ('Help', sputil.help_cb(session, 'OpenSpectra')),
			   )
    br.frame.pack(side = 'top', anchor = 'nw')

  # ---------------------------------------------------------------------------
  #
  def open_cb(self):

    paths = self.files.selected_paths()
    bad_paths = []
    for path in paths:
      if self.session.open_spectrum(path) == None:
        bad_paths.append(path)

    if bad_paths:
      message = 'Could not open files:'
      for path in bad_paths:
        message = message + '\n' + path
    else:
      message = 'Opened %d spectra' % len(paths)

    self.result['text'] = message

# -----------------------------------------------------------------------------
#
def show_file_dialog(session):
  d = sputil.the_dialog(open_spectra_dialog, session)
  d.show_window(1)
