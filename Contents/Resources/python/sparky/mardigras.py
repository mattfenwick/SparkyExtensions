# -----------------------------------------------------------------------------
# Read Mardigras constraint file lower and upper distance bounds.
#
import os
import string
import Tkinter

import atoms
import noesy
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
def bounds(session, mardi_path, stoppable = tkutil.Not_Stoppable()):

  if not hasattr(session, 'mardi_table'):
    session.mardi_table = {}
  t = session.mardi_table
  
  if not t.has_key(mardi_path):
    t[mardi_path] = mardigras_bounds(session, mardi_path, stoppable)

  return t[mardi_path]

# -----------------------------------------------------------------------------
#
class mardigras_bounds:

  def __init__(self, session, mardi_path, stoppable = tkutil.Not_Stoppable()):

    self.mardi_path = mardi_path
    self.bounds_table = read_bounds(session, mardi_path, stoppable)

    gatable = {}
    for num_atom_1, num_atom_2 in self.bounds_table.keys():
      gatable[(None, num_atom_1[1])] = 1
      gatable[(None, num_atom_2[1])] = 1
    self.atom_translations = \
      atoms.guess_atom_name_translations(session, mardi_path, gatable.keys())

  # ---------------------------------------------------------------------------
  #
  def distance_bounds(self, peak):

    if peak.is_assigned:
      res = noesy.proton_resonances(peak)
      translate = self.atom_translations
      return self.bounds(translate.resonance_number_atom(res[0]),
                         translate.resonance_number_atom(res[1]))
    return None

  # ---------------------------------------------------------------------------
  #
  def bounds(self, num_atom_1, num_atom_2):

    try:
      return self.bounds_table[(num_atom_1, num_atom_2)]
    except KeyError:
      return None

# -----------------------------------------------------------------------------
#
def read_bounds(session, mardi_path, stoppable):

  mardi_file = open(mardi_path, 'r')
  lines = mardi_file.readlines()
  mardi_file.close()

  bounds = {}
  bad_lines = 0
  stoppable.stoppable_loop('reading ' + os.path.basename(mardi_path), 100)
  for line in lines:
    stoppable.check_for_stop()
    line_fields = parse_mardi_line(line)
    if line_fields:
      n1, atom1, n2, atom2, lower, upper = line_fields
      na1 = (n1, atom1)
      na2 = (n2, atom2)
      b = (lower, upper)
      bounds[(na1, na2)] = b
      bounds[(na2, na1)] = b
    else:
      bad_lines = bad_lines + 1

  if bad_lines > 0:
    session.stdout.write('Warning: %d unreadable lines in %s\n' %
                         (bad_lines, mardi_path))
    
  return bounds

# -----------------------------------------------------------------------------
# Return n1, atom1, n2, atom2, lower, upper
#
def parse_mardi_line(line):

  atom1 = string.strip(line[0:4])
  n1 = pyutil.string_to_int(line[4:7])
  atom2 = string.strip(line[8:12])
  n2 = pyutil.string_to_int(line[12:15])

  if n1 == None or n2 == None:
    return None
  
  bounds = string.split(line[15:])
  if len(bounds) < 2:
    return None

  lower = pyutil.string_to_float(bounds[0])
  upper = pyutil.string_to_float(bounds[1])

  if lower == None or upper == None:
    return None

  return n1, atom1, n2, atom2, lower, upper

# -----------------------------------------------------------------------------
# Output Mardigras format peak lists
#
class mardigras_format_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    tkutil.Dialog.__init__(self, session.tk, 'MARDIGRAS Format')

    sc = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice = sc

    pl = sputil.peak_listbox(self.top)
    pl.frame.pack(fill = 'both', expand = 1)
    pl.heading['text'] = 'Peak list'
    pl.listbox.bind('<ButtonRelease-1>', pl.select_peak_cb)
    pl.listbox.bind('<ButtonRelease-2>', pl.goto_peak_cb)
    pl.listbox.bind('<Double-ButtonRelease-1>', pl.goto_peak_cb)
    self.peak_list = pl

    ib = tkutil.checkbutton(self.top, 'Include unintegrated peaks?', 0)
    ib.button.pack(side = 'top', anchor = 'w')
    self.unintegrated = ib

    nb = tkutil.checkbutton(self.top, 'Show peak notes?', 0)
    nb.button.pack(side = 'top', anchor = 'w')
    self.note = nb

    eh = Tkinter.Label(self.top, text = 'Omit peak if note has a word from:')
    eh.pack(side = 'top', anchor = 'w')
    ef = tkutil.entry_field(self.top, '  ', width = 30)
    ef.frame.pack(side = 'top', anchor = 'w')
    self.note_words = ef
    et = Tkinter.Label(self.top, text = '(space separated list of words)')
    et.pack(side = 'top', anchor = 'w')
    
    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
                           ('Update', self.update_cb),
                           ('Write Peaks', self.save_peaks_cb),
                           ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session,
                                                   'MardigrasFormat')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    spectrum = self.spectrum_choice.spectrum()
    if spectrum == None:
      return

    show_unintegrated = self.unintegrated.state()
    show_note = self.note.state()
    note_words = string.split(self.note_words.variable.get())
    note_words = filter(lambda w: len(w) > 0, note_words)

    peaks = sputil.sort_peaks_by_assignment(spectrum.peak_list(), self)
    self.stoppable_call(self.show_peaks, peaks,
                        show_unintegrated, show_note, note_words)

  # ---------------------------------------------------------------------------
  #
  def save_peaks_cb(self):
    
    path = tkutil.save_file(self.top, 'Save MARDIGRAS Peak List', 'peaklist')
    if path:
      self.peak_list.write_file(path, 'w', write_heading = 0)

  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, peaks, show_unintegrated, show_note, note_words):

    self.peak_list.clear()

    heading = 'ATOM1   ATOM2   INTENSITY       '
    self.peak_list.append(heading, None)
    
    self.stoppable_loop('peaks', 100)
    for peak in peaks:
      self.check_for_stop()
      show = (peak.is_assigned and
              (show_unintegrated or peak.volume != None) and
              (not note_words or
               not pyutil.string_contains_word(peak.note, note_words)))
      if show:
        line = self.peak_line(peak, show_note)
        if line:
          self.peak_list.append(line, peak)

  # ---------------------------------------------------------------------------
  #
  def peak_line(self, peak, show_note):

    r1, r2 = noesy.proton_resonances(peak)

    if r1 == None or r2 == None:
      return ''

    if r1.group.number == None or r2.group.number == None:
      return ''

    volume = peak.volume
    if volume == None:
      volume = 0
    
    line = "%-4.4s%3d %-4.4s%3d %11.4e" % (r1.atom.name, r1.group.number,
                                           r2.atom.name, r2.group.number,
                                           volume)

    if show_note and peak.note:
      line = line + '   # ' + peak.note
      
    return line

# -----------------------------------------------------------------------------
#
def show_dialog(session):
  d = sputil.the_dialog(mardigras_format_dialog,session)
  d.show_window(1)
