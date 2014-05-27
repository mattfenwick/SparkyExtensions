# -----------------------------------------------------------------------------
# Use mirror peaks to help make assignments of 3-D labelled noesy spectra.
# For a pair of close protons H1, H2 you expect two hsqc-noesy peaks.  One
# corresponds to the two protons and the C13 or N15 attached to the first
# proton, and the other is for the two protons and the C13/N15 attached to
# the second proton.  To check a proposed assignment for a peak you can
# look to see if the "mirror peak" (the other peak associated with the pair
# of protons) exists.  This code helps you look for mirror peaks.
# For each possible assignment it lists the signal/noise at the mirror peak
# location and allows you to jump to that place in the spectrum.
#
import string
import Tkinter
import types

import atoms
import axes
import noesy
import pyutil
import sparky
import sputil
import strips
import tkutil

class AttachedAtomUnknown(Exception): pass
class AtomUnknown(Exception): pass
class AtomUnassigned(Exception): pass
class NoHeavyAtomSpectrum(Exception): pass

# -----------------------------------------------------------------------------
#
class mirror_assignment_dialog(tkutil.Dialog, tkutil.Stoppable):

  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):

    self.session = session
    self.last_peak = None
    self.selection_notice = None
    self.make_dialog()

  # ---------------------------------------------------------------------------
  #
  def make_dialog(self):

    tkutil.Dialog.__init__(self, self.session.tk, 'Mirror Assignment Checker')

    self.top.bind('<Destroy>', self.window_destroyed_cb, 1)

    w = self.make_noesy_table(self.top)
    w.pack(side = 'top', anchor = 'w')

    choices = ('Selected peaks',
	       'Peaks with assigned mirror peak',
	       'Peaks without assigned mirror peak',
	       'Unassigned with assigned mirror',
	       )
    self.show_type = tkutil.option_menu(self.top, 'Show ',
                                        choices, choices[0])
    self.show_type.frame.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top,
                            'Exclude mirrors with low signal/noise?', 0)
    cb.button.pack(side = 'top', anchor = 'w')
    self.exclude_mirrors = cb

    f = Tkinter.Frame(self.top)
    cb.map_widget(f)
    
    e = tkutil.entry_field(f, 'C13 / N15 intensity ratio: ', '1', 3)
    self.c13_n15_factor = e.variable
    e.frame.pack(side = 'top', anchor = 'w')

    e = tkutil.entry_field(f, 'Minimum mirror intensity factor: ', '.5', 3)
    self.min_mirror_factor = e.variable
    e.frame.pack(side = 'top', anchor = 'w')

    pl = tkutil.scrolling_list(self.top, '', 5)
    pl.frame.pack(side = 'top', fill = 'both', expand = 1)
    pl.listbox.bind('<ButtonRelease-2>', self.select_peak_or_assignment_cb)
    pl.listbox.bind('<ButtonRelease-1>', self.goto_peak_or_assignment_cb)
    self.peak_list = pl

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Strips', self.strips_cb),
			   ('Save', self.peak_list.save_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(self.session,
                                                   'MirrorPeak')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[3])

    self.settings = self.get_settings()

  # ---------------------------------------------------------------------------
  #
  def make_noesy_table(self, parent):

    f = Tkinter.Frame(parent)

    t = Tkinter.Label(f, text = 'noesy spectrum')
    t.grid(row = 1, column = 1)

    t = Tkinter.Label(f, text = 'PPM Tolerance')
    t.grid(row = 0, column = 2, columnspan = 3)
    for a in range(3):
      name = 'w%d' % (a+1)
      h = Tkinter.Label(f, text = name)
      h.grid(row = 1, column = 2 + a)

    self.c13_spect, self.c13_ppm_range = self.noesy_table_row(f, 2, '13C')
    self.n15_spect, self.n15_ppm_range = self.noesy_table_row(f, 3, '15N')

    return f

  # ---------------------------------------------------------------------------
  #
  def noesy_table_row(self, table, row, atom_name):

    t = Tkinter.Label(table, text = atom_name + ' ')
    t.grid(row = row, column = 0)

    spectrum = sputil.spectrum_menu(self.session, table,
                                    '', allow_no_choice = 1)
    spectrum.frame.grid(row = row, column = 1)

    ppm_range = []
    for a in range(3):
      v = Tkinter.StringVar(table)
      v.set('.02')
      e = Tkinter.Entry(table, textvariable = v, width = 5)
      e.grid(row = row, column = 2 + a)
      ppm_range.append(v)

    spectra = self.session.project.spectrum_list()
    s = noesy.noesy_hsqc_spectrum(spectra, atom_name)
    if s:
      spectrum.set(s.name)
      heavy_axis = axes.unique_nucleus_axis(s, atom_name)
      ppm_range[heavy_axis].set('.2')

    return spectrum, ppm_range

  # ---------------------------------------------------------------------------
  #
  def window_destroyed_cb(self, event):

    self.remove_selection_callback()

  # ---------------------------------------------------------------------------
  #
  def close_cb(self):

    self.remove_selection_callback()
    tkutil.Dialog.close_cb(self)
    
  # ---------------------------------------------------------------------------
  #
  def remove_selection_callback(self):

    if self.selection_notice:
      if sparky.object_exists(self.session):
        self.session.dont_notify_me(self.selection_notice)
      self.selection_notice = None

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    self.settings = self.get_settings()

    show_type = self.settings.show_type
    if show_type == 'Peaks with assigned mirror peak':
      self.stoppable_call(self.show_peaks,
			  self.show_peak_with_mirror,
			  'peaks with mirror peak')
    elif show_type == 'Peaks without assigned mirror peak':
      self.stoppable_call(self.show_peaks,
			  self.show_peak_without_mirror,
			  'peaks without mirror peak')
    elif show_type == 'Unassigned with assigned mirror':
      self.stoppable_call(self.show_peaks,
			  self.show_unassigned_with_mirror,
			  'unassigned peaks with assigned mirror peak')
    elif show_type == 'Selected peaks':
      if self.selection_notice == None:
	self.selection_notice = self.session.notify_me('selection changed',
                                         self.show_selected_peak_assignments)
      self.show_selected_peak_assignments()
    if self.selection_notice and show_type != 'Selected peaks':
      self.remove_selection_callback()

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):
    settings = pyutil.generic_class()

    settings.c13_spectrum = self.c13_spect.spectrum()
    settings.n15_spectrum = self.n15_spect.spectrum()
    settings.c13_ppm_range = tkutil.float_variable_values(self.c13_ppm_range)
    settings.n15_ppm_range = tkutil.float_variable_values(self.n15_ppm_range)
    settings.show_type = self.show_type.get()
    settings.exclude_mirrors = self.exclude_mirrors.state()
    if settings.exclude_mirrors:
      ftext = self.c13_n15_factor.get()
      settings.c13_n15_factor = pyutil.string_to_float(ftext, 1)
      ftext = self.min_mirror_factor.get()
      settings.min_mirror_factor = pyutil.string_to_float(ftext, 0)
    return settings

  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, show_peak, description, peaks = None):

    self.peak_list.clear()
    heading = '%20s   %s' % ('Assignment', 'Signal/Noise')
    self.peak_list.heading['text'] = description + '\n' + heading

    if peaks == None:
      peaks = (self.spectrum_peaks(self.settings.c13_spectrum) +
	       self.spectrum_peaks(self.settings.n15_spectrum))

    count = 0
    self.stoppable_loop('peaks', 1)
    for peak in peaks:
      self.check_for_stop()
      show_peak(peak)
      count = count + 1 

    self.peak_list.heading['text'] = ('%d %s\n%s' %
                                      (count, description, heading))

  # ---------------------------------------------------------------------------
  #
  def spectrum_peaks(self, spectrum):

    peaks = []
    if spectrum:
      peaks = spectrum.peak_list()
    return peaks

  # ---------------------------------------------------------------------------
  #
  def show_peak_with_mirror(self, peak):

    if not peak.is_assigned:
      return 0

    mirror_assignment, mirror_spectrum, error_message = \
      self.mirror_assignment(peak.resonances(), peak.spectrum)
    if (mirror_assignment == None or
	mirror_spectrum.find_peak(mirror_assignment) == None):
      return 0

    self.show_peak(peak)
    return 1

  # ---------------------------------------------------------------------------
  #
  def show_peak_without_mirror(self, peak):

    if not peak.is_assigned:
      return 0

    mirror_assignment, mirror_spectrum, error_message = \
      self.mirror_assignment(peak.resonances(), peak.spectrum)
    if (mirror_assignment != None and
	mirror_spectrum.find_peak(mirror_assignment) != None):
      return 0

    self.show_peak(peak)
    return 1

  # ---------------------------------------------------------------------------
  #
  def show_unassigned_with_mirror(self, peak):

    if peak.is_assigned:
      return 0

    if not self.is_assignable_with_mirror(peak):
      return 0

    self.show_peak(peak)
    return 1

  # ---------------------------------------------------------------------------
  #
  def is_assignable_with_mirror(self, peak):

    alist = self.possible_assignments(peak)
    for a in alist:
      mirror_assignment, mirror_spectrum, error_message = \
        self.mirror_assignment(a, peak.spectrum)
      if (mirror_assignment != None and
	  mirror_spectrum.find_peak(mirror_assignment) != None):
        return 1
    return 0

  # ---------------------------------------------------------------------------
  #
  def mirror_assignment(self, assignment, spectrum = None):

    if not sputil.is_complete_assignment(assignment):
      return None, None, 'partial assignment'

    if spectrum == None:
      spectrum = self.assignment_spectrum(assignment)

    try:
      mirror_assign, mirror_spectrum = \
	mirror_assignment(assignment, spectrum,
			  self.settings.c13_spectrum,
			  self.settings.n15_spectrum)
    except AtomUnknown, e:
      error_message = 'no Sparky atom %s' % (e.args[0] + e.args[1])
    except AtomUnassigned, e:
      atom = e.args[0]
      atom_name = atom.group.name + atom.name
      error_message = 'atom %s unassigned' % atom_name
    except AttachedAtomUnknown, e:
      atom = e.args[0]
      atom_name = atom.group.name + atom.name
      error_message = 'atom attached to %s unknown' % atom_name
    except NoHeavyAtomSpectrum, e:
      atom = e.args[0]
      error_message = 'no spectrum for %s' % atom.name
    else:
      return mirror_assign, mirror_spectrum, None

    return None, None, error_message

  # ---------------------------------------------------------------------------
  #
  def assignment_spectrum(self, assignment):

    c13_spectrum = self.settings.c13_spectrum
    n15_spectrum = self.settings.n15_spectrum
    if c13_spectrum:
      aH, aCN, aH2 = noesy.noesy_hsqc_axes(c13_spectrum)
      r = assignment[aCN]
      if r and r.atom.nucleus == '13C':
	return c13_spectrum
    if n15_spectrum:
      aH, aCN, aH2 = noesy.noesy_hsqc_axes(n15_spectrum)
      r = assignment[aCN]
      if r and r.atom.nucleus == '15N':
	return n15_spectrum
    return None

  # ---------------------------------------------------------------------------
  #
  def show_selected_peak_assignments(self):

    self.stoppable_call(self.show_peaks, self.show_peak, 'selected peaks',
                        self.selected_peaks())

  # ---------------------------------------------------------------------------
  #
  def selected_peaks(self):

    peaks = []
    if self.settings.c13_spectrum:
      peaks = peaks + self.settings.c13_spectrum.selected_peaks()
    if self.settings.n15_spectrum:
      peaks = peaks + self.settings.n15_spectrum.selected_peaks()
    return peaks

  # ---------------------------------------------------------------------------
  #
  def show_peak(self, peak):

    self.peak_list.append(self.peak_format(peak), peak)
    self.show_mirror_assignments(peak)

  # ---------------------------------------------------------------------------
  #
  def show_mirror_assignments(self, peak):

    alist = self.possible_assignments(peak)

    for a in alist:
      mirror_assignment, mirror_spectrum, error_message = \
        self.mirror_assignment(a, peak.spectrum)
      if mirror_assignment:
        line = self.mirror_format(a, mirror_assignment, mirror_spectrum)
      else:
        line = self.no_mirror_format(a, error_message)
      self.peak_list.append(line, mirror_assignment)

  # ---------------------------------------------------------------------------
  #
  def possible_assignments(self, peak):

    if peak.spectrum == self.settings.c13_spectrum:
      ppm_range = self.settings.c13_ppm_range
    elif peak.spectrum == self.settings.n15_spectrum:
      ppm_range = self.settings.n15_ppm_range
    else:
      return None
    alist = noesy.nearby_noesy_hsqc_assignments(peak.spectrum,
						peak.position,
						ppm_range)

    if self.min_mirror_factor:
      alist = self.minimum_mirror_intensity_filter(alist, peak)

    #
    # If peak is assigned always consider that assignment first even
    # if it is not within ppm tolerances.
    #
    if peak.is_assigned:
      pa = peak.resonances()
      if pa in alist:
        alist.remove(pa)
      alist.insert(0, pa)
      
    return alist

  # ---------------------------------------------------------------------------
  #
  def minimum_mirror_intensity_filter(self, assignments, peak):

    minimum_intensity = self.minimum_mirror_intensity_table(peak)
    alist = []
    for assignment in assignments:
      mirror_assignment, mirror_spectrum, error_message = \
	self.mirror_assignment(assignment, peak.spectrum)
      if mirror_assignment == None:
	alist.append(assignment)
      else:
	intensity = self.signal_to_noise(mirror_assignment, mirror_spectrum)
	if abs(intensity) >= minimum_intensity[mirror_spectrum]:
	  alist.append(assignment)
    return alist

  # ---------------------------------------------------------------------------
  #
  def minimum_mirror_intensity_table(self, peak):

    s = self.settings
    c13_spectrum = s.c13_spectrum
    n15_spectrum = s.n15_spectrum
    minimum_intensity = {}
    minimum_intensity[c13_spectrum] = 0
    minimum_intensity[n15_spectrum] = 0
    if s.exclude_mirrors:
      min_factor = s.min_mirror_factor
      c13_n15_factor = s.c13_n15_factor
      peak_min = min_factor * abs(sputil.peak_height(peak)) / peak.spectrum.noise
      if peak.spectrum == c13_spectrum:
        minimum_intensity[c13_spectrum] = peak_min
        minimum_intensity[n15_spectrum] = peak_min / c13_n15_factor
      elif peak.spectrum == n15_spectrum:
        minimum_intensity[c13_spectrum] = peak_min * c13_n15_factor
        minimum_intensity[n15_spectrum] = peak_min
    return minimum_intensity

  # ---------------------------------------------------------------------------
  #
  def signal_to_noise(self, assignment, spectrum):

    peak = spectrum.find_peak(assignment)
    if peak:
      height = sputil.peak_height(peak)
    else:
      pos = sputil.assignment_position(assignment, spectrum)
      height = spectrum.data_height(pos)
    return height / spectrum.noise

  # ---------------------------------------------------------------------------
  #
  def peak_format(self, peak):

    signal_to_noise = sputil.peak_height(peak) / peak.spectrum.noise
    line = '  %20s %7.1f' % (peak.assignment, signal_to_noise)
    return line

  # ---------------------------------------------------------------------------
  #
  def mirror_format(self, assignment, mirror_assignment, mirror_spectrum):

    atext = sputil.assignment_name(assignment)
    signal_to_noise = self.signal_to_noise(mirror_assignment, mirror_spectrum)
    line = 'a %20s        %7.1f' % (atext, signal_to_noise)
    if mirror_spectrum.find_peak(mirror_assignment):
      line = line + ' assigned mirror'
    return line

  # ---------------------------------------------------------------------------
  #
  def no_mirror_format(self, assignment, error_message):

    line = 'for ' + sputil.assignment_name(assignment) + ' ' + error_message
    return line

  # ---------------------------------------------------------------------------
  #
  def select_peak_or_assignment_cb(self, event):

    pora = self.peak_list.event_line_data(event)
    if type(pora) == types.InstanceType:
      sputil.select_peak(pora)
    elif type(pora) == types.TupleType or type(pora) == types.ListType:
      s = self.assignment_spectrum(pora)
      if s:
        sputil.select_peak(s.find_peak(pora))
      
  # ---------------------------------------------------------------------------
  #
  def goto_peak_or_assignment_cb(self, event):

    pora = self.peak_list.event_line_data(event)
    if type(pora) == types.InstanceType:
      sputil.show_peak(pora)
    elif type(pora) == types.TupleType or type(pora) == types.ListType:
      s = self.assignment_spectrum(pora)
      sputil.show_assignment(pora, s)

  # ---------------------------------------------------------------------------
  #
  def strips_cb(self):

    peaks = self.selected_peaks()
    for peak in peaks:
      self.show_peak_strips(peak)

  # ---------------------------------------------------------------------------
  #
  def show_peak_strips(self, peak):
      
    strip_plot = strips.strip_dialog(self.session)

    strip = self.assignment_strip(peak.resonances(), peak.spectrum,
                                  peak.position, strip_plot)
    strip_list = [strip]

    alist = self.possible_assignments(peak)
    for a in alist:
      strip = self.mirror_strip(a, peak.spectrum, strip_plot)
      if strip:
        strip_list.append(strip)

    aH, aCN, aH2 = noesy.noesy_hsqc_axes(peak.spectrum)
    y_center = peak.position[aH]
    y_pixel_size = .002

    strip_plot.show_window(1)
    strip_plot.delete_all_strips()
    strip_plot.add_strips(strip_list)
    strip_plot.adjust_y_scale('1H', y_center, y_pixel_size)

  # ---------------------------------------------------------------------------
  #
  def mirror_strip(self, assignment, spectrum, strip_plot):

    mirror_assignment, mirror_spectrum, error_message = \
      self.mirror_assignment(assignment, spectrum)
    if mirror_assignment:
      center = sputil.assignment_position(mirror_assignment, mirror_spectrum)
      return self.assignment_strip(mirror_assignment, mirror_spectrum,
                                   center, strip_plot)
    return None

  # ---------------------------------------------------------------------------
  #
  def assignment_strip(self, assignment, spectrum, center, strip_plot):

    aH, aCN, aH2 = noesy.noesy_hsqc_axes(spectrum)
    xyz_axes = (aH, aH2, aCN)
    label = self.strip_label(assignment, xyz_axes, center)
    strip = strip_plot.spectrum_strip(spectrum, xyz_axes, center, label)
    return strip

  # ---------------------------------------------------------------------------
  #
  def strip_label(self, assignment, xyz_axes, center):

    aX, aY, aZ = xyz_axes
    rX_name = self.resonance_name(assignment[aX])
    rY_name = self.resonance_name(assignment[aY])
    label = '%s\n%s\n%.4g\n%.4g' % (rX_name, rY_name, center[aX], center[aZ])
    return label

  # ---------------------------------------------------------------------------
  #
  def resonance_name(self, resonance):

    if resonance:
      return resonance.name
    return ''
    
  # ---------------------------------------------------------------------------
  # Zoom a view to position where mirror peak of selected peak should be found
  #
  def show_mirror_peak(self):

    peak = sputil.selected_peak(self.session)
    if peak == None:
      return

    if not peak.is_assigned:
      out = self.session.stdout
      out.write('show_mirror_peak(): selected peak is unassigned\n')
      return

    if (self.settings.c13_spectrum == None and
	self.settings.n15_spectrum == None):
      self.show_window(1)	# query for C13 and N15 noesy spectra
      return

    if (peak.spectrum != self.settings.c13_spectrum and
	peak.spectrum != self.settings.n15_spectrum):
      out = self.session.stdout
      out.write('show_mirror_peak(): selected peak is not in spectrum ' +
                self.spectrum_names() + '\n')
      return

    if peak == self.last_peak:	# repeating command reshows selected peak
      sputil.show_peak(peak)
      self.last_peak = None
      return

    assignment, mirror_spectrum, error_message = \
      self.mirror_assignment(peak.resonances(), peak.spectrum)

    if assignment:
      sputil.show_assignment(assignment, mirror_spectrum)
    else:
      out = self.session.stdout
      out.write('show_mirror_peak(): ' + error_message + '\n')

    self.last_peak = peak

  # ---------------------------------------------------------------------------
  #
  def spectrum_names(self):

    names = ''
    if self.settings.c13_spectrum:
      names = names + ' ' + self.settings.c13_spectrum.name
    if self.settings.n15_spectrum:
      names = names + ' ' + self.settings.n15_spectrum.name
    return names

# ---------------------------------------------------------------------------
#
def resonance_name(resonance, omit_group = None):

  if resonance == None:
    return '?'
  g = resonance.group
  if g == omit_group:
    return resonance.atom.name
  return '%s %s' % (g.name, resonance.atom.name)

# -----------------------------------------------------------------------------
# Return assignment and spectrum for mirror peak.
# Throws AtomUnknown, AtomUnassigned, AttachedAtomUnknown, NoHeavyAtomSpectrum
#
def mirror_assignment(assignment, spectrum, c13_spectrum, n15_spectrum):

  aH, aCN, aH2 = noesy.noesy_hsqc_axes(spectrum)
  labelled_proton = assignment[aH].atom
  unlabelled_proton = assignment[aH2].atom
  mol = spectrum.molecule
  other_heavy_atom = atoms.attached_heavy_atom(unlabelled_proton, mol)

  if other_heavy_atom == None:
    hname = atoms.attached_heavy_atom_name(unlabelled_proton, mol)
    if hname == None:
      raise AttachedAtomUnknown, unlabelled_proton
    else:
      raise AtomUnknown, (unlabelled_proton.group.name, hname)

  nucleus = other_heavy_atom.nucleus
  if nucleus == '13C':
    mirror_spectrum = c13_spectrum
  elif nucleus == '15N':
    mirror_spectrum = n15_spectrum
  else:
    raise NoHeavyAtomSpectrum, other_heavy_atom

  a = noesy.noesy_hsqc_assignment(mirror_spectrum, unlabelled_proton,
				  labelled_proton, other_heavy_atom)
  if a == None:
    raise AtomUnassigned, other_heavy_atom

  return (a, mirror_spectrum)

# -----------------------------------------------------------------------------
#
def show_mirror_dialog(session):
  sputil.the_dialog(mirror_assignment_dialog,session).show_window(1)

# -----------------------------------------------------------------------------
#
def select_noesy_spectra(session):
  sputil.the_dialog(mirror_assignment_dialog,session).show_window(1)

# -----------------------------------------------------------------------------
#
def show_mirror_peak(session):
  sputil.the_dialog(mirror_assignment_dialog,session).show_mirror_peak()
