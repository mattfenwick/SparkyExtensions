# -----------------------------------------------------------------------------
# Read a peak list and create peaks in a spectrum.
#
import string
import Tkinter

import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class volume_error_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    tkutil.Dialog.__init__(self, session.tk, 'Set Volume Errors')

    self.spectrum_choice = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    self.spectrum_choice.frame.pack(side = 'top', anchor = 'w')

    f = Tkinter.Frame(self.top)
    f.pack(side = 'top', anchor = 'w')

    r = 0

    w = Tkinter.Label(f, text = 'Error (%)')
    w.grid(row = r, column = 1)
    r = r + 1

    cb = tkutil.checkbutton(f, 'Default fit', 1)
    self.fit_default = cb.variable
    cb.button.grid(row = r, column = 0, sticky = 'w')
    e = tkutil.entry_field(f, '', '10', 4)
    self.fit_default_error = e.variable
    e.frame.grid(row = r, column = 1)
    r = r + 1

    cb = tkutil.checkbutton(f, 'Default box / ellipse', 1)
    self.box_default = cb.variable
    cb.button.grid(row = r, column = 0, sticky = 'w')
    e = tkutil.entry_field(f, '', '20', 4)
    self.box_default_error = e.variable
    e.frame.grid(row = r, column = 1)
    r = r + 1

    cb = tkutil.checkbutton(f, 'Near diagonal', 0)
    self.near_diagonal = cb.variable
    cb.button.grid(row = r, column = 0, sticky = 'w')
    e = tkutil.entry_field(f, '', '20', 4)
    self.near_diagonal_error = e.variable
    e.frame.grid(row = r, column = 1)
    tkutil.grid_labels(f, ('Range (ppm)', r, 2))
    e = tkutil.entry_field(f, '|w1-w2| ', '.1', 4)
    self.near_diagonal_range = e.variable
    e.frame.grid(row = r+1, column = 2)
    r = r + 2

    cb = tkutil.checkbutton(f, 'Near other peaks', 0)
    self.nearby_peaks = cb.variable
    cb.button.grid(row = r, column = 0, sticky = 'w')
    tkutil.grid_labels(f,
                       ('Relative volume', r+1, 0),
                       ('< .5', r+2, 0),
                       ('.5 - 2', r+3, 0),
                       ('> 2', r+4, 0),
                       ('unintegrated', r+5, 0))
    self.nearby_error = {}
    (self.nearby_error['< .5'],
     self.nearby_error['.5 - 2'],
     self.nearby_error['> 2'],
     self.nearby_error['unintegrated']
     ) = tkutil.grid_entries(f, 4,
                             ('5', r+2, 1),
                             ('10', r+3, 1),
                             ('20', r+4, 1),
                             ('20', r+5, 1))
    self.nearby_range = {}
    tkutil.grid_labels(f, ('Range (ppm)', r+1, 2))
    e = tkutil.entry_field(f, 'w1 ', '.05', 4)
    self.nearby_range['w1 range'] = e.variable
    e.frame.grid(row = r+2, column = 2)
    e = tkutil.entry_field(f, 'w2 ', '.05', 4)
    self.nearby_range['w2 range'] = e.variable
    e.frame.grid(row = r+3, column = 2)
    r = r + 6

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Set Volume Errors', self.update_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'VolumeErrors')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[1])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    self.stoppable_call(self.set_volume_errors)

  # ---------------------------------------------------------------------------
  #
  def set_volume_errors(self):

    self.settings = self.read_settings()
    peaks = self.settings.spectrum.peak_list()
    self.stoppable_loop('peaks', 100)
    for peak in peaks:
      self.check_for_stop()
      self.set_volume_error(peak)

  # ---------------------------------------------------------------------------
  #
  def read_settings(self):

    atof = pyutil.string_to_float
    settings = pyutil.generic_class()

    settings.spectrum = self.spectrum_choice.spectrum()

    settings.fit_default_error = None
    if self.fit_default.get():
      settings.fit_default_error = atof(self.fit_default_error.get())

    settings.box_default_error = None
    if self.box_default.get():
      settings.box_default_error = atof(self.box_default_error.get())

    settings.near_diagonal_range = None
    settings.near_diagonal_error = None
    if self.near_diagonal.get():
      settings.near_diagonal_range = atof(self.near_diagonal_range.get())
      settings.near_diagonal_error = atof(self.near_diagonal_error.get())
      
    settings.nearby_peaks = {}
    settings.nearby_error = {}
    if self.nearby_peaks.get():
      range = (atof(self.nearby_range['w1 range'].get()),
	       atof(self.nearby_range['w2 range'].get()))
      if range[0] != None and range[1] != None:
        plist = settings.spectrum.peak_list()
        settings.nearby_peaks = nearby_peak_table(plist, range, self)
        for range in ('< .5', '.5 - 2', '> 2', 'unintegrated'):
          e = atof(self.nearby_error[range].get(), 0)
          settings.nearby_error[range] = e

    return settings

  # ---------------------------------------------------------------------------
  #
  def set_volume_error(self, peak):

    if peak.volume == None or peak.volume_error_method == 'manual':
      return

    method = peak.volume_method
    settings = self.settings
    e = 0

    if settings.fit_default_error:
      if method == 'gaussian' or method == 'lorentzian':
	e = e + settings.fit_default_error
      elif method == 'peak-group':
	methods = pyutil.attribute_values(peak.peaklets(), 'volume_method')
	if 'gaussian' in methods or 'lorentzian' in methods:
	  e = e + settings.fit_default_error

    if settings.box_default_error:
      if method == 'box' or method == 'ellipse':
	e = e + settings.box_default_error
      elif method == 'peak-group':
	methods = pyutil.attribute_values(peak.peaklets(), 'volume_method')
	if 'box' in methods or 'ellipse' in methods:
	  e = e + settings.box_default_error

    if settings.near_diagonal_error and settings.near_diagonal_range:
      f = peak.frequency
      if abs(f[0] - f[1]) <= settings.near_diagonal_range:
	e = e + settings.near_diagonal_error

    if settings.nearby_peaks:
      vol = peak.volume
      for p in settings.nearby_peaks[peak]:
	pvol = p.volume
	if pvol == None:
	  e = e + settings.nearby_error['unintegrated']
	elif pvol < .5 * vol:
	  e = e + settings.nearby_error['< .5']
	elif pvol < 2 * vol:
	  e = e + settings.nearby_error['.5 - 2']
	else:
	  e = e + settings.nearby_error['> 2']

    if e > 0:
      peak.volume_error = e / 100.0
      peak.volume_error_method = 'auto'

# -----------------------------------------------------------------------------
# Return a table mapping each peak to a list of other peaks that are nearby.
#
def nearby_peak_table(peaks, range, stoppable = tkutil.Not_Stoppable):

  cell_size = []
  for r in range:
    cell_size.append(2 * r)

  cells = {}
  stoppable.stoppable_loop('nearby peaks', 100)
  for peak in peaks:
    stoppable.check_for_stop()
    i = cell_index(peak.frequency, cell_size)
    if not cells.has_key(i):
      cells[i] = []
    cells[i].append(peak)

  neighbors = {}
  stoppable.stoppable_loop('nearby peaks', 100)
  for peak in peaks:
    stoppable.check_for_stop()
    nearby = []
    freq = peak.frequency
    for near in neighbor_cell_contents(freq, cell_size, cells):
      if near != peak and points_are_close(freq, near.frequency, range):
	nearby.append(near)
    neighbors[peak] = nearby

  return neighbors

# -----------------------------------------------------------------------------
#
def cell_index(point, cell_size):

  i = []
  for k in range(len(point)):
    i.append(int(divmod(point[k], cell_size[k])[0]))
  return tuple(i)

# -----------------------------------------------------------------------------
#
def neighbor_cell_contents(point, cell_size, cells):

  neighbors = []
  for i in neighbor_cell_indexes(point, cell_size):
    if cells.has_key(i):
      neighbors = neighbors + cells[i]
  return neighbors

# -----------------------------------------------------------------------------
# Return indices for the 2 by 2 by 2 by ... block with center closest to the
# specified point.
#
def neighbor_cell_indexes(point, cell_size):

  if len(point) == 0:
    return ()

  i, frac = divmod(point[0], cell_size[0])
  i = int(i)
  if frac >= .5:	j = i + 1
  else:			j = i - 1

  indices = []
  if len(point) == 1:
    indices.append((i,))
    indices.append((j,))
  else:
    for index in neighbor_cell_indexes(point[1:], cell_size[1:]):
      indices.append((i,) + index)
      indices.append((j,) + index)
  return indices

# -----------------------------------------------------------------------------
#
def points_are_close(p1, p2, max_range):

  for k in range(len(p1)):
    if abs(p1[k] - p2[k]) > max_range[k]:
      return 0
  return 1

# -----------------------------------------------------------------------------
#
def show_volume_error_dialog(session):
  sputil.the_dialog(volume_error_dialog,session).show_window(1)
