# -----------------------------------------------------------------------------
# Show a list of assignments with columns for one or more spectra and
# check marks for spectra which have a peak with that assignment.
# For noesy spectra list proton pairs with columns for one or more 2-D or
# 3-D noesy spectra and check marks for spectra which have an assigned peak
# for that proton pair.  Show above/below diagonal peaks on the same line.
#
import Tkinter

import noesy
import sparky
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class peak_table_dialog(tkutil.Dialog, tkutil.Stoppable):

  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Peak Table')

    setup = Tkinter.Frame(self.top)
    setup.pack(side = 'top', anchor = 'w')

    # Choose Spectra

    sbutton = tkutil.checkbutton(self.top, 'Choose Spectra', 1)
    sbutton.button.pack(side = 'top', anchor = 'w')

    schoice = Tkinter.Frame(self.top)
    schoice.pack(side = 'top', anchor = 'w')

    sc = sputil.spectrum_checkbuttons(session, schoice, '')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_list = sc.chosen_spectra

    cb = tkutil.checkbutton(schoice, 'Noesy format?', 0)
    self.noesy_format = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    sbutton.map_widget(schoice)

    # Peak list

    pl = sputil.assignment_listbox(session, self.top)
    pl.frame.pack(side = 'top', fill = 'both', expand = 1)
    pl.listbox.bind('<ButtonRelease-1>', self.select_assignment_cb)
    pl.listbox.bind('<ButtonRelease-2>', self.goto_assignment_cb)
    pl.listbox.bind('<Double-ButtonRelease-1>', self.goto_assignment_cb)
    self.peak_list = pl

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Save', self.peak_list.save_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'PeakTable')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    self.stoppable_call(self.show_peaks)

  # ---------------------------------------------------------------------------
  #
  def show_peaks(self):

    self.noesy = self.noesy_format.get()
    name_to_spect = pyutil.precompose(sputil.name_to_spectrum, self.session)
    peaks = self.assigned_peaks(self.spectrum_list)
    self.show_assignments(peaks)

  # ---------------------------------------------------------------------------
  # Return table [spectrum][assignment] -> peak
  #
  def assigned_peaks(self, spectra):

    s2a = {}
    for spectrum in spectra:
      s2a[spectrum] = {}
      self.stoppable_loop(spectrum.name + ' peaks', 100)
      for peak in spectrum.peak_list():
	self.check_for_stop()
        a = self.assignment(peak)
	if a:
	  s2a[spectrum][a] = peak

    peaks = map(lambda s: (s,s2a[s]), spectra)
    return peaks

  # ---------------------------------------------------------------------------
  #
  def assignment(self, peak):

    if peak.is_assigned:
      if self.noesy:
	res = noesy.proton_resonances(peak)
      else:
	res = peak.resonances()
      return sputil.group_atom_assignment(res)
    return None

  # ---------------------------------------------------------------------------
  #
  def show_assignments(self, peaks):

    assignments = {}
    for spectrum, assigned_peaks in peaks:
      for a in assigned_peaks.keys():
	assignments[a] = 1

    if self.noesy:
      # Above and below diagonal peaks combined on same line
      for a in assignments.keys():
	if sputil.number_group_atom(a[0]) > sputil.number_group_atom(a[1]):
	  del assignments[a]
	  assignments[(a[1], a[0])] = 1

    def nga(a): return tuple(map(sputil.number_group_atom, a))
    assignment_list = tkutil.stoppable_sort_by_key(assignments.keys(),
                                                   nga, self)
    
    self.peak_list.clear()
    self.stoppable_loop('assignments', 50)
    for assignment in assignment_list:
      self.check_for_stop()
      self.show_assignment(assignment, peaks)

    spectra = map(lambda s_ap: s_ap[0], peaks)
    self.set_column_ranges(spectra)
    count = self.peak_list.listbox.index('end')
    self.peak_list.heading['text'] = '%d assignments\n' % count + self.heading

  # ---------------------------------------------------------------------------
  #
  def show_assignment(self, assignment, peaks):

    line = self.assignment_line(assignment, peaks)
    self.peak_list.append(line, assignment)

  # ---------------------------------------------------------------------------
  #
  def assignment_line(self, assignment, peaks):

    line = '%-20s' % self.assignment_name(assignment)
    for spectrum, assigned_peaks in peaks:
      line = line + self.peak_field(assignment, spectrum, assigned_peaks)
      if self.noesy:
	crossdiag = (assignment[1], assignment[0])
	line = line + self.peak_field(crossdiag, spectrum, assigned_peaks)

    return line

  # ---------------------------------------------------------------------------
  #
  def assignment_name(self, assignment):

    if self.noesy:
      return mardigras_name(assignment)
    return sputil.group_atom_assignment_name(assignment)

  # ---------------------------------------------------------------------------
  #
  def peak_field(self, assignment, spectrum, assigned_peaks):

    if assigned_peaks.has_key(assignment):
      peak = assigned_peaks[assignment]
      if peak.volume:
	return '%10.2e' % peak.volume
      else:
	return '%10s' % 'yes'
    else:
      res = sputil.group_atom_resonances(spectrum.condition, assignment)
      if self.noesy:
	res = noesy.extend_noesy_assignment(spectrum, res)
      if res:
	return '%10s' % 'no'
      return '%10s' % '.'

  # ---------------------------------------------------------------------------
  #
  def set_column_ranges(self, spectra):

    h = heading = '%-20s' % 'Assignment'
    field_width = tkutil.text_size(' %9s' % '', self.peak_list.listbox)
    column_ranges = []
    for s in spectra:
      x = tkutil.text_size(heading, self.peak_list.listbox)
      column_ranges.append((s, 0, x, x + field_width))
      if self.noesy:
	column_ranges.append((s, 1, x + field_width, x + 2*field_width))
	heading = heading + ' %19s' % s.name
      else:
	heading = heading + ' %9s' % s.name
    self.column_ranges = column_ranges
    self.heading = heading

  # ---------------------------------------------------------------------------
  #
  def select_assignment_cb(self, event):

    res, spectrum = self.clicked_assignment(event)
    sputil.select_assignment(res, spectrum)

  # ---------------------------------------------------------------------------
  #
  def goto_assignment_cb(self, event):

    res, spectrum = self.clicked_assignment(event)
    sputil.show_assignment(res, spectrum)

  # ---------------------------------------------------------------------------
  #
  def clicked_assignment(self, event):

    spectrum = None
    for s, t, x1, x2 in self.column_ranges:
      if event.x >= x1 and event.x <= x2:
	spectrum = s
	transpose = t
	break

    res = None
    if spectrum:
      assignment = self.peak_list.event_line_data(event)
      if assignment:
        if transpose:
          assignment = (assignment[1], assignment[0])
        res = sputil.group_atom_resonances(spectrum.condition, assignment)
        if self.noesy:
          res = noesy.extend_noesy_assignment(spectrum, res)
        if res == None:
          aname = self.assignment_name(assignment)
          self.progress_report("Can't determine %s location in %s" %
                               (aname, spectrum.name))

    return res, spectrum

# ----------------------------------------------------------------------------
#
def mardigras_name(assignment):
  (g1, a1), (g2, a2) = assignment
  return mardigras_atom_format(g1, a1) + ' ' + mardigras_atom_format(g2, a2)

# ----------------------------------------------------------------------------
#
def mardigras_atom_format(group, atom):
  n = sputil.group_number(group)
  if n == None:
    n = 0
  return "%-4.4s%3d" % (atom, n)

# -----------------------------------------------------------------------------
#
def show_peak_table(session):
  sputil.the_dialog(peak_table_dialog,session).show_window(1)
