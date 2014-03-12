# -----------------------------------------------------------------------------
# Create peaks on a 2D C13 HSQC spectrum for all protons attached to carbons
# where proton and carbon resonances are both assigned.
#
import Tkinter

import atoms
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class hc_peak_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    tkutil.Dialog.__init__(self, session.tk, 'Place HC Peaks from Resonances')

    explain = ('Create and label peaks on a 2D C13 HSQC spectrum\n' +
               'for all protons attached to carbons, if both proton\n' +
               'and carbon resonances are assigned and labeled\n'
               'correctly.\n')
    w = Tkinter.Label(self.top, text = explain, justify = 'left')
    w.pack(side = 'top', anchor = 'w')

    m = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    m.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_menu = m

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Place peaks', self.place_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'HCPeaks')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[1])
    
  # ---------------------------------------------------------------------------
  #
  def place_cb(self):

    spectrum = self.spectrum_menu.spectrum()
    if spectrum == None:
      return

    self.stoppable_call(self.place_peaks, spectrum)
    
  # ---------------------------------------------------------------------------
  #
  def place_peaks(self, spectrum):
    
    hc_axes = pyutil.order(('1H', '13C'), spectrum.nuclei)
    if spectrum.dimension != 2 or hc_axes == None:
      self.progress_report('Spectrum must 2D with H and C axes.')
      return

    molecule = spectrum.molecule
    condition = spectrum.condition
    self.stoppable_loop('resonances', 50)
    for rH in condition.resonance_list():
      self.check_for_stop()
      if rH.atom.nucleus == '1H':
        catom = atoms.attached_heavy_atom(rH.atom, molecule)
        if catom and catom.nucleus == '13C':
          rC = condition.find_resonance(catom)
          if rC:
            assignment = pyutil.permute((rH, rC), hc_axes)
            if not spectrum.find_peak(assignment):
              freq = pyutil.permute((rH.frequency, rC.frequency), hc_axes)
              pos = sputil.alias_onto_spectrum(freq, spectrum)
              peak = spectrum.place_peak(pos)
              peak.assign(hc_axes[0], rH.group.name, rH.atom.name)
              peak.assign(hc_axes[1], rC.group.name, rC.atom.name)
              if freq != pos:
                peak.alias = pyutil.subtract_tuples(freq, pos)
              peak.show_assignment_label()
  
# -----------------------------------------------------------------------------
#
def show_dialog(session):
  sputil.the_dialog(hc_peak_dialog,session).show_window(1)
