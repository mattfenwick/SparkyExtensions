# -----------------------------------------------------------------------------
# Show a list of peaks with columns for chemical shifts, volumes, linewidths,
# height, distance bounds, model distances, predicted intensities, ...
#
import os
import Tkinter

import atoms
import corma
import mardigras
import noesy
import pdb
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class peak_list_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    self.title = 'Peak List'
    self.spectrum = None
    self.peaks = ()
    self.settings = peak_list_settings()

    tkutil.Dialog.__init__(self, session.tk, self.title)

    pl = sputil.peak_listbox(self.top)
    pl.frame.pack(side = 'top', fill = 'both', expand = 1)
    pl.listbox.bind('<ButtonRelease-1>', pl.select_peak_cb)
    pl.listbox.bind('<ButtonRelease-2>', pl.goto_peak_cb)
    pl.listbox.bind('<Double-ButtonRelease-1>', pl.goto_peak_cb)
    self.peak_list = pl

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Setup...', self.setup_cb),
			   ('Save...', self.peak_list.save_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'PeakListPython')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[3])
  
  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, peaks, title):

    self.title = title
    self.top.title(self.title)
    self.spectrum = None
    self.peaks = peaks
    self.stoppable_call(self.update_peaks)
  
  # ---------------------------------------------------------------------------
  #
  def show_spectrum_peaks(self, spectrum):

    self.title = spectrum.name + ' peak list'
    self.top.title(self.title)
    self.spectrum = spectrum
    self.peaks = None
    self.stoppable_call(self.update_peaks)

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    self.stoppable_call(self.update_peaks)
  
  # ---------------------------------------------------------------------------
  #
  def setup_cb(self):

    psd = sputil.the_dialog(peak_list_settings_dialog, self.session)
    psd.set_parent_dialog(self, self.settings, self.new_settings)
    psd.top.title(self.title + ' settings')
    psd.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def new_settings(self, settings):

    self.settings = settings
    self.stoppable_call(self.update_peaks)

  # ---------------------------------------------------------------------------
  #
  def update_peaks(self):
    
    self.progress_report('Getting peaks')
    if self.spectrum:
      peaks = self.spectrum.peak_list()
    else:
      peaks = self.peaks

    if self.settings.sort_by_assignment:
      peaks = sputil.sort_peaks_by_assignment(peaks, self)
    if self.settings.pair_crossdiagonal_peaks:
      peaks = pair_crossdiagonal_peaks(peaks, self)

    self.field_initializations(peaks)

    if peaks:
      dimension = peaks[0].spectrum.dimension
    else:
      dimension = 0
    self.peak_list.heading['text'] = ('%d peaks\n' % len(peaks) +
				      self.heading(dimension))

    self.peak_list.clear()
    self.stoppable_loop('peaks', 50)
    for peak in peaks:
      self.check_for_stop()
      self.peak_list.append(self.peak_line(peak), peak)

  # ---------------------------------------------------------------------------
  #
  def field_initializations(self, peaks):

    for field in self.settings.fields:
      if field.onoff:
	field.initialize(self.session, peaks, self)

  # ---------------------------------------------------------------------------
  #
  def peak_line(self, peak):

    line = ''
    for field in self.settings.fields:
      if field.onoff:
	line = line + field.string(peak)
    return line

  # ---------------------------------------------------------------------------
  #
  def heading(self, dim):

    heading = ''
    for field in self.settings.fields:
      if field.onoff:
	heading = heading + field.heading(dim)
    return heading

# -----------------------------------------------------------------------------
#
class peak_list_field:
  def __init__(self):
    self.onoff = 0
  def heading(self, dim):
    if hasattr(self, 'title'):
      return self.pad(self.title(dim), dim)
    return self.pad(self.name, dim)
  def initialize(self, session, peaks, stoppable):
    pass
  def string(self, peak):
    return self.pad(self.text(peak), peak.spectrum.dimension)
  def pad(self, string, dim):
    size = self.size(dim)
    if size == None:
      return string
    return pyutil.pad_field(string, size)

  # ---------------------------------------------------------------------------
  # Make check button for peak list settings dialog
  #
  class field_widgets:
    def __init__(self, parent, name):
      cb = tkutil.checkbutton(parent, name, 0)
      cb.button.pack(side = 'top', anchor = 'w')
      self.checkbutton = cb
    def get_widget_state(self, field):
      field.onoff = self.checkbutton.state()
    def set_widget_state(self, field):
      self.checkbutton.set_state(field.onoff)
    
# ---------------------------------------------------------------------------
#
field_classes = []

# ---------------------------------------------------------------------------
#
class assignment_field(peak_list_field):
  name = 'Assignment'
  def size(self, dim): return 8 * dim
  def text(self, peak): return sputil.assignment_name(peak.resonances())
field_classes.append(assignment_field)

# -------------------------------------------------------------------------
#
class chemical_shift_field(peak_list_field):
  name = 'Chemical Shift'
  def title(self, dim): return 'Shift (ppm)'
  def size(self, dim): return 8 * dim
  def text(self, peak):
    return pyutil.sequence_string(peak.frequency, ' %7.3f')
field_classes.append(chemical_shift_field)

# -------------------------------------------------------------------------
#
class volume_field(peak_list_field):
  name = 'Volume'
  def size(self, dim): return 10
  def text(self, peak):
    if peak.volume: return '%.3g' % peak.volume
    return ''
field_classes.append(volume_field)

# -------------------------------------------------------------------------
#
class data_height_field(peak_list_field):
  name = 'Data Height'
  def title(self, dim): return 'Height'
  def size(self, dim): return 10
  def text(self, peak):
    return '%.3g' % sputil.peak_height(peak)
field_classes.append(data_height_field)

# -------------------------------------------------------------------------
#
class signal_to_noise_field(peak_list_field):
  name = 'Signal / Noise'
  def title(self, dim): return 'S/N'
  def size(self, dim): return 6
  def text(self, peak):
    return '%.1f' % (sputil.peak_height(peak) / peak.spectrum.noise)
field_classes.append(signal_to_noise_field)

# -------------------------------------------------------------------------
#
class fit_height_field(peak_list_field):
  name = 'Fit Height'
  def size(self, dim): return 11
  def text(self, peak):
    if peak.fit_height == None: return ''
    return '%.3g' % peak.fit_height
field_classes.append(fit_height_field)

# -------------------------------------------------------------------------
#
class linewidth_field(peak_list_field):
  name = 'Linewidth'
  def title(self, dim): return 'Linewidth (Hz)'
  def size(self, dim): return 8 * dim
  def text(self, peak):
    if peak.line_width == None: return ''
    linewidth = pyutil.seq_product(peak.line_width,
                                   peak.spectrum.hz_per_ppm)
    return pyutil.sequence_string(linewidth, ' %7.2f')
field_classes.append(linewidth_field)

# -------------------------------------------------------------------------
#
class mardigras_bounds_field(peak_list_field):
  name = 'Mardigras Bounds'
  def __init__(self):
    self.path = ''
    peak_list_field.__init__(self)
  def title(self, dim): return '%6s %6s' % ('R-min', 'R-max')
  def size(self, dim): return 14
  def text(self, peak):
    bounds = self.bounds.distance_bounds(peak)
    if bounds == None: return ''
    return ' %6.2f %6.2f' % bounds
  def initialize(self, session, peaks, stoppable):
    self.bounds = mardigras.bounds(session, self.path, stoppable)
  class field_widgets(peak_list_field.field_widgets):
    def __init__(self, parent, name):
      peak_list_field.field_widgets.__init__(self, parent, name)
      self.path_widget = tkutil.file_field(parent, 'File: ', 'mardigras')
      self.checkbutton.map_widget(self.path_widget.frame)
    def get_widget_state(self, field):
      peak_list_field.field_widgets.get_widget_state(self, field)
      field.path = self.path_widget.get()
    def set_widget_state(self, field):
      peak_list_field.field_widgets.set_widget_state(self, field)
      self.path_widget.set(field.path)
field_classes.append(mardigras_bounds_field)

# -------------------------------------------------------------------------
#
class corma_intensity_field(peak_list_field):
  name = 'Corma Intensities'
  def __init__(self):
    self.path = ''
    peak_list_field.__init__(self)
  def title(self, dim): return 'Corma     '
  def size(self, dim): return 14
  def text(self, peak):
    intensity = self.intensities.normalized_intensity(peak)
    if intensity == None: return ''
    if peak.volume:
      return '%8.3g %4.1f' % (intensity, intensity / peak.volume)
    else:
      return '%8.3g %4s' % (intensity, '')
  def initialize(self, session, peaks, stoppable):
    i = corma.intensities(session, self.path, stoppable)
    for spectrum in sputil.spectra_for_peaks(peaks):
      i.normalization_factor(spectrum, stoppable)
    self.intensities = i
  class field_widgets(peak_list_field.field_widgets):
    def __init__(self, parent, name):
      peak_list_field.field_widgets.__init__(self, parent, name)
      self.path_widget = tkutil.file_field(parent, 'File: ', 'corma')
      self.checkbutton.map_widget(self.path_widget.frame)
    def get_widget_state(self, field):
      peak_list_field.field_widgets.get_widget_state(self, field)
      field.path = self.path_widget.get()
    def set_widget_state(self, field):
      peak_list_field.field_widgets.set_widget_state(self, field)
      self.path_widget.set(field.path)
field_classes.append(corma_intensity_field)

# -------------------------------------------------------------------------
#
class pdb_distance_field(peak_list_field):
  name = 'PDB Distance'
  def __init__(self):
    self.pdb_path_list = []
    peak_list_field.__init__(self)
  def title(self, dim):
    h = ''
    for pdb_path in self.pdb_path_list:
      h = h + ' %6s' % os.path.basename(pdb_path)
    return h
  def size(self, dim): return 7 * len(self.pdb_path_list)
  def text(self, peak):
    f = ''
    if peak.is_assigned:
      for model in self.models:
        d = model.noesy_distance(peak)
        if d == None:
          f = f + ' %6s' % ''
        else:
          f = f + ' %6.2f' % d
    return f
  def initialize(self, session, peaks, stoppable):
    self.models = []
    for pdb_path in self.pdb_path_list:
      m = pdb.model(session, pdb_path, stoppable)	# read pdb files
      self.models.append(m)
  class field_widgets(peak_list_field.field_widgets):
    def __init__(self, parent, name):
      peak_list_field.field_widgets.__init__(self, parent, name)
      self.pdb_files = tkutil.file_choices(parent, 'PDB Files', 'pdb')
      self.checkbutton.map_widget(self.pdb_files.frame)
    def get_widget_state(self, field):
      peak_list_field.field_widgets.get_widget_state(self, field)
      field.pdb_path_list = list(self.pdb_files.path_list)
    def set_widget_state(self, field):
      peak_list_field.field_widgets.set_widget_state(self, field)
      self.pdb_files.set_paths(field.pdb_path_list)
field_classes.append(pdb_distance_field)

# -------------------------------------------------------------------------
#
class color_field(peak_list_field):
  name = 'Color'
  def size(self, dim): return 8
  def text(self, peak): return '%8s' % peak.color
field_classes.append(color_field)

# -------------------------------------------------------------------------
#
class note_field(peak_list_field):
  name = 'Note'
  def size(self, dim): return 21
  def text(self, peak): return ' %-20s' % peak.note
field_classes.append(note_field)

# -----------------------------------------------------------------------------
# Dialog of possible peak list fields.
#
class peak_list_settings_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk, 'Peak List Settings')

    fb = Tkinter.Frame(self.top, borderwidth = 3, relief = 'groove')
    fb.pack(side = 'top', fill = 'x')

    #
    # Create the checkbutton and extra widgets for each possible field
    #
    self.field_widgets = {}
    for fc in field_classes:
      self.field_widgets[fc] = fc.field_widgets(self.top, fc.name)

    opt = Tkinter.Frame(self.top, borderwidth = 3, relief = 'groove')
    opt.pack(side = 'top', fill = 'x')

    cb = tkutil.checkbutton(opt, 'Sort by assignment?', 1)
    self.assignmentsort = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(opt, 'Pair crossdiagonal peaks?', 0)
    self.crosspair = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
                           ('Ok', self.ok_cb),
			   ('Apply', self.apply_cb),
			   ('Close', self.close_cb),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    for f in settings.fields:
      self.field_widgets[f.__class__].set_widget_state(f)
    self.assignmentsort.set(settings.sort_by_assignment)
    self.crosspair.set(settings.pair_crossdiagonal_peaks)

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    settings = peak_list_settings()
    for f in settings.fields:
      self.field_widgets[f.__class__].get_widget_state(f)
    settings.sort_by_assignment = self.assignmentsort.get()
    settings.pair_crossdiagonal_peaks = self.crosspair.get()
    return settings

# -----------------------------------------------------------------------------
#
class peak_list_settings:

  def __init__(self):

    fields = []
    for fc in field_classes:
      fields.append(fc())
      
    self.fields = fields
    self.sort_by_assignment = 1
    self.pair_crossdiagonal_peaks = 0

  # ---------------------------------------------------------------------------
  #
  def show_fields(self, *field_names):

    ftable = {}
    for f in self.fields:
      ftable[f.name] = f

    for name in field_names:
      if ftable.has_key(name):
        ftable[name].onoff = 1
        
# -----------------------------------------------------------------------------
# Return a new list of peaks where peaks and crossdiagonal peaks
# are placed consecutively in list.
#
def pair_crossdiagonal_peaks(peaks, stoppable):

  assignment_to_peak = {}
  stoppable.stoppable_loop('finding crossdiagonal peaks', 200)
  for peak in peaks:
    stoppable.check_for_stop()
    r = noesy.proton_resonances(peak)
    assignment_to_peak[(r, peak.spectrum)] = peak

  plist = []
  peak_used = {}
  stoppable.stoppable_loop('sorting crossdiagonal peaks', 200)
  for peak in peaks:
    stoppable.check_for_stop()
    if not peak_used.has_key(peak):
      plist.append(peak)
      peak_used[peak] = 1
      r = noesy.proton_resonances(peak)
      if r:
	tr = (r[1], r[0])
	if assignment_to_peak.has_key((tr, peak.spectrum)):
	  tpeak = assignment_to_peak[(tr, peak.spectrum)]
	  if not peak_used.has_key(tpeak):
	    plist.append(tpeak)
	    peak_used[tpeak] = 1

  return plist

# -----------------------------------------------------------------------------
# Show a peak list for the selected spectrum.  If a peak list has already
# been created for the spectrum just make that dialog visible.  Otherwise
# create a new dialog.
#
def show_spectrum_peaks(session):

  spectrum = session.selected_spectrum()
  if spectrum == None:
    return

  if not hasattr(session, 'spectrum_dialogs'):
    session.spectrum_dialogs = {}
  dialogs = session.spectrum_dialogs
  if (dialogs.has_key(spectrum) and
      not dialogs[spectrum].is_window_destroyed()):
    dialogs[spectrum].show_window(1)
  else:
    d = peak_list_dialog(session)
    d.show_window(1)
    d.settings.show_fields('Assignment', 'Chemical Shift')
    d.show_spectrum_peaks(spectrum)
    dialogs[spectrum] = d

# -----------------------------------------------------------------------------
# Show a list of selected peaks.
#
def show_selected_peaks(session):

  peaks = session.selected_peaks()
  title = '%d selected peaks' % len(peaks)
  d = peak_list_dialog(session)
  d.show_window(1)
  d.settings.show_fields('Assignment', 'Chemical Shift')
  d.show_peaks(peaks, title)
