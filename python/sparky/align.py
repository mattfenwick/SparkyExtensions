# -----------------------------------------------------------------------------
# Shift the ppm scales of a spectrum so that a selected peak in this spectrum
# aligns with a selected peak in another spectrum.
#
import Tkinter

import axes
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class align_spectrum_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Align Spectrum')
    
    m = sputil.spectrum_menu(session, self.top, 'Align spectrum ')
    m.frame.pack(side = 'top', anchor = 'w')
    m.add_callback(self.chose_spectrum_cb)
    self.align_menu = m
    
    m = sputil.spectrum_menu(session, self.top, 'using peak in ')
    m.frame.pack(side = 'top', anchor = 'w')
    m.add_callback(self.chose_spectrum_cb)
    self.ref_menu = m

    lbl = Tkinter.Label(self.top, text = 'Match axes')
    lbl.pack(side = 'top', anchor = 'w')
    
    f = Tkinter.Frame(self.top)
    f.pack(side = 'top', anchor = 'w')
    self.axis_table = f
    self.axis_menus = []

    self.setup_axis_table()

    m = Tkinter.Label(self.top)
    m.pack(side = 'top', anchor = 'w')
    self.message = m

    br = tkutil.button_row(self.top,
			   ('Align', self.align_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'AlignSpectrum')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def chose_spectrum_cb(self, name):

    self.setup_axis_table()
    
  # ---------------------------------------------------------------------------
  #
  def setup_axis_table(self):

    for w in self.axis_table.grid_slaves():
      w.destroy()

    align_spectrum = self.align_menu.spectrum()
    ref_spectrum = self.ref_menu.spectrum()
    if align_spectrum == None or ref_spectrum == None:
      return

    lbl = Tkinter.Label(self.axis_table, text = align_spectrum.name)
    lbl.grid(row = 0, column = 0, sticky = 'w')
    column = 1
    for a in range(align_spectrum.dimension):
      axis_label = 'w%d %s' % (a+1, align_spectrum.nuclei[a])
      lbl = Tkinter.Label(self.axis_table, text = axis_label)
      lbl.grid(row = 0, column = column)
      column = column + 1
    
    lbl = Tkinter.Label(self.axis_table, text = ref_spectrum.name)
    lbl.grid(row = 1, column = 0, sticky = 'w')
    column = 1
    self.axis_menus = []
    for nucleus in align_spectrum.nuclei:
      m = axes.axis_menu(self.axis_table, ref_spectrum, nucleus,
                         allow_no_choice = 1)
      m.frame.grid(row = 1, column = column, sticky = 'w')
      matches = pyutil.element_positions(nucleus, ref_spectrum.nuclei)
      if len(matches) == 1:
        m.set_axis(matches[0])
      self.axis_menus.append(m)
      column = column + 1

  # ---------------------------------------------------------------------------
  #
  def align_cb(self):

    align_sp = self.align_menu.spectrum()
    ref_sp = self.ref_menu.spectrum()
    if align_sp == ref_sp:
      msg = 'Alignment spectrum and reference spectrum must be different'
      self.message['text'] = msg
      return

    apeaks = align_sp.selected_peaks()
    rpeaks = ref_sp.selected_peaks()
    if len(apeaks) != 1 or len(rpeaks) != 1:
      self.message['text'] = 'Must select one peak from each spectrum'
      return
    align_peak = apeaks[0]
    ref_peak = rpeaks[0]

    ref_axes = []
    for m in self.axis_menus:
      ref_axes.append(m.chosen_axis())

    self.align(align_peak, ref_peak, ref_axes)

  # ---------------------------------------------------------------------------
  #
  def align(self, align_peak, ref_peak, axis_map):
    
    shift = list(align_peak.spectrum.scale_offset)
    for a in range(len(shift)):
      ra = axis_map[a]
      if ra != None:
        offset = align_peak.frequency[a] - ref_peak.frequency[ra]
        shift[a] = shift[a] - offset
    align_peak.spectrum.scale_offset = shift
    shift_string = pyutil.sequence_string(shift, ' %.3f')
    self.message['text'] = 'Set shift to' + shift_string

  # ---------------------------------------------------------------------------
  #
  def align_spectrum(self):

    align_sp = self.session.selected_spectrum()

    if align_sp:
      self.align_menu.set(align_sp.name)
    
      align_peaks = align_sp.selected_peaks()
      ref_peaks = pyutil.subtract_lists(self.session.selected_peaks(),
                                        align_peaks)
      if len(ref_peaks) == 1:
        ref_peak = ref_peaks[0]
        ref_sp = ref_peak.spectrum
        self.ref_menu.set(ref_sp.name)

    self.show_window(1)

# -----------------------------------------------------------------------------
#
def show_shift_dialog(session):

  d = sputil.the_dialog(align_spectrum_dialog, session)
  d.align_spectrum()
