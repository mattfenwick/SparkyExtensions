# -----------------------------------------------------------------------------
# Read a peak list and create peaks in a spectrum.
#
import string
import Tkinter

import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class read_peaks_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    tkutil.Dialog.__init__(self, session.tk, 'Read Peak List')

    plp = tkutil.file_field(self.top, 'Peak file: ', 'peaklist')
    plp.frame.pack(side = 'top', anchor = 'w')
    self.peak_list_path = plp
    
    sc = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice = sc

    sl = tkutil.scrolling_list(self.top, 'Unreadable lines', 5)
    sl.frame.pack(side = 'top', anchor = 'w', fill = 'both', expand = 1)
    self.unreadable = sl
    
    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Create peaks', self.read_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'ReadPeaks')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[1])

  # ---------------------------------------------------------------------------
  #
  def read_cb(self):

    self.unreadable.listbox.delete('0' ,'end')
    spectrum = self.spectrum_choice.spectrum()
    path = self.peak_list_path.get()
    if spectrum and path:
      self.stoppable_call(self.read_peaks, path, spectrum)

  # ---------------------------------------------------------------------------
  #
  def read_peaks(self, path, spectrum):

    input = open(path, 'r')
    lines = input.readlines()
    input.close()

    count = 0
    self.stoppable_loop('peaks', 100)
    for line in lines:
      self.check_for_stop()
      count = count + self.create_peak(line, spectrum)

    msg = ('%d peaks created\n' % count +
	   '%d unreadable lines shown below' % (len(lines) - count))
    self.unreadable.heading['text'] = msg

  # ---------------------------------------------------------------------------
  #
  def create_peak(self, line, spectrum):

    pinfo = self.parse_peak_line(line, spectrum.dimension)
    if pinfo:
      assignment, frequency, note = pinfo
      peak = spectrum.place_peak(frequency)
      self.move_peak_onto_spectrum(peak)

      assigned = 0
      for a in range(spectrum.dimension):
	group_name, atom_name = assignment[a]
        if group_name or atom_name:
          peak.assign(a, group_name, atom_name)
          assigned = 1

      if assigned:
        peak.show_assignment_label()
        
      if note:
	peak.note = note
      peak.selected = 1
      return 1
    
    return 0

  # ---------------------------------------------------------------------------
  # If the peak is off the edge of the spectrum, fold it onto the spectrum
  # and set the alias to keep its frequency the same.
  #
  def move_peak_onto_spectrum(self, peak):

    freq = peak.frequency
    pos = sputil.alias_onto_spectrum(freq, peak.spectrum)
    if pos != freq:
      peak.position = pos
      peak.alias = pyutil.subtract_tuples(freq, pos)

  # ---------------------------------------------------------------------------
  #
  def parse_peak_line(self, line, dim):

    fields = string.split(line, None, dim + 1)
    if len(fields) < dim + 1:
      return None

    assignment = sputil.parse_assignment(fields[0])
    if assignment == None or len(assignment) != dim:
      self.unreadable.listbox.insert('end', line)
      return None

    frequency = []
    for a in range(dim):
      f = pyutil.string_to_float(fields[a+1])
      if f == None:
        self.unreadable.listbox.insert('end', line)
        return None
      frequency.append(f)

    if len(fields) > dim + 1:
      note = fields[dim + 1]
    else:
      note = ''

    return (assignment, frequency, note)

# -----------------------------------------------------------------------------
#
def read_peak_list(session):
  sputil.the_dialog(read_peaks_dialog,session).show_window(1)
