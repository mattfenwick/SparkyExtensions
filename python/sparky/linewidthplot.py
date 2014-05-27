# -----------------------------------------------------------------------------
# Display peak linewidths graphically using one row for each group/atom type
#

import math
import string
import Tkinter

import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class linewidth_plot_dialog(tkutil.Dialog, tkutil.Stoppable):

  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Peak Linewidth Plot')

    self.top.columnconfigure(0, weight = 1)
    r = 0
    
    sw = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sw.frame.grid(row = r, sticky = 'w')
    r = r + 1
    self.spectrum_widget = sw
    
    af = tkutil.entry_field(self.top, 'Spectrum axis: ', '1', 3)
    af.frame.grid(row = r, sticky = 'w')
    r = r + 1
    self.axis_variable = af.variable
    
    self.lw_ranges = [None, None]
    er = tkutil.entry_row(self.top, 'Linewidth range (hz): ',
                          ('min', '0', 3), ('max', '50', 3), ('step', '5', 3))
    (self.lw_ranges[0], self.lw_ranges[1], self.lw_step) = er.variables
    er.frame.grid(row = r, sticky = 'w')
    r = r + 1
    
    e = tkutil.entry_field(self.top, 'Atoms: ', '', 30)
    self.atoms = e.variable
    e.frame.grid(row = r, sticky = 'w')
    r = r + 1
    
    c = tkutil.scrollable_canvas(self.top)
    c.frame.grid(row = r, sticky = 'news')
    self.top.rowconfigure(r, weight = 1)
    r = r + 1
    self.canvas = c.canvas

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.grid(row = r, sticky = 'w')
    r = r + 1
    
    postscript_cb = pyutil.precompose(tkutil.postscript_cb, self.canvas)
    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Postscript', postscript_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'LinewidthPlot')),
			   )
    br.frame.grid(row = r, sticky = 'w')
    r = r + 1

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    
    if self.get_settings():
      if self.axis >= 0 and self.axis < self.spectrum.dimension:
        ap_table = atom_peaks(self.spectrum, self.axis,
                              self.min_linewidth, self.max_linewidth,
                              self.atoms_to_show)
        ap_pairs = ap_table.items()
        def ap_compare(ap1, ap2):
          a1 = ap1[0]
          a2 = ap2[0]
          return cmp((a1.group.number, a1.group.symbol, a1.name),
                     (a2.group.number, a2.group.symbol, a2.name))
        ap_pairs.sort(ap_compare)
        self.stoppable_call(self.show_linewidths, ap_pairs)

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    self.spectrum = self.spectrum_widget.spectrum()
    if self.spectrum == None:
      self.progress_report('Must select a spectrum.')
      return 0

    anum = pyutil.string_to_int(self.axis_variable.get())
    if anum == None:
      self.progress_report('Must select a spectrum axis.')
      return 0
    else:
      self.axis = anum - 1
    
    self.min_linewidth = pyutil.string_to_float(self.lw_ranges[0].get())
    self.max_linewidth = pyutil.string_to_float(self.lw_ranges[1].get())
    self.linewidth_step = pyutil.string_to_float(self.lw_step.get())
    if (self.min_linewidth == None or self.max_linewidth == None or
        self.linewidth_step == None):
      self.progress_report('Must select linewidth min, max, and step.')
      return 0

    self.atoms_per_line = 1

    atoms = tuple(map(string.strip, string.split(self.atoms.get(), ',')))
    if atoms == ('',):
      atoms = ()
    self.atoms_to_show = atoms

    return 1
  
  # ---------------------------------------------------------------------------
  #
  def show_linewidths(self, ap_pairs):

    p = pyutil.generic_class()

    p.top_yspace = 30
    p.name_xspace = 70
    p.name_yspace = 18
    p.atom_yspace = p.name_yspace / self.atoms_per_line
    p.tick_size = p.atom_yspace / 2
    p.label_gap = 15
    p.left_xspace = 20
    p.names_xspace = p.left_xspace + self.atoms_per_line * p.name_xspace
    p.plot_range = (p.names_xspace, p.names_xspace + 500)
    p.linewidth_range = (self.min_linewidth, self.max_linewidth)
    p.line = 0

    self.canvas.delete('all')

    self.plot_linewidths(ap_pairs, p)
    self.plot_grid(p)

    box = self.canvas.bbox('all')
    self.canvas['width'] = box[2]
    self.canvas['scrollregion'] = box
    tkutil.set_canvas_corner(self.canvas, 0, 0)

  # ---------------------------------------------------------------------------
  #
  def plot_linewidths(self, ap_pairs, params):

    self.stoppable_loop('atom types', 5)
    for atom, peak_list in ap_pairs:
      self.check_for_stop()
      tline = params.line / self.atoms_per_line
      ty = params.top_yspace + params.name_yspace * (tline + .2)
      tx = (params.left_xspace +
            (params.line % self.atoms_per_line) * params.name_xspace)
      name = atom.group.name + ' ' + atom.name
      self.canvas.create_text(tx, ty, anchor = 'w', text = name)
      y = (params.top_yspace + tline * params.name_yspace
	   + (params.line % self.atoms_per_line) * params.atom_yspace)
      for p in peak_list:
        lw = p.line_width[self.axis] * self.spectrum.hz_per_ppm[self.axis]
	x = map_interval(lw, params.linewidth_range, params.plot_range)
	id = self.canvas.create_line(x, y, x, y+params.tick_size)
        def show_peak(event, peak = p):
          sputil.show_peak(peak)
          sputil.select_peak(peak)
        self.canvas.tag_bind(id, '<ButtonPress>', show_peak)
      params.line = params.line + 1

  # ---------------------------------------------------------------------------
  #
  def plot_grid(self, params):

    py1 = params.top_yspace
    py2 = (params.line/self.atoms_per_line + 1.5) * params.name_yspace
    r1, r2 = params.linewidth_range
    x1 = pyutil.nearest_multiple(r1, self.linewidth_step)
    x2 = pyutil.nearest_multiple(r2, self.linewidth_step)
    precision = -int(math.floor(math.log10(self.linewidth_step)))
    linewidth_format = '%%.%df' % max(0, precision)
    self.stoppable_loop('grid line', 100)
    x = x1
    while x <= x2 + .5 * self.linewidth_step:
      self.check_for_stop()
      px = map_interval(x, params.linewidth_range, params.plot_range)
      self.canvas.create_text(px, py1 - params.label_gap,
			      text = linewidth_format % x)
      id = self.canvas.create_line(px, py1, px, py2, stipple = 'gray50')
      self.canvas.lower(id)
      x = x + self.linewidth_step

# -----------------------------------------------------------------------------
#
def map_interval(x, from_range, to_range):

  f = float(x - from_range[0]) / (from_range[1] - from_range[0])
  return to_range[0] + f * (to_range[1] - to_range[0])

# -----------------------------------------------------------------------------
# Gather peaks for each atom within linewidth bounds.
# Return a table mapping atom to list of peaks.
#
def atom_peaks(spectrum, axis, min_linewidth, max_linewidth, atoms_to_show):

  atom_linewidths = {}
  reslist = spectrum.condition.resonance_list()
  for r in reslist:
    atom = r.atom
    name = atom.group.symbol + ' ' + atom.name
    if (not atoms_to_show or
        atom.name in atoms_to_show or
        name in atoms_to_show):
      lwpeaks = []
      for p in r.peak_list():
        if p.spectrum == spectrum and p.resonances()[axis] == r:
          if p.line_width != None and p.line_width_method == 'fit':
            axis_lw = p.line_width[axis] * spectrum.hz_per_ppm[axis]
            if axis_lw >= min_linewidth and axis_lw <= max_linewidth:
              lwpeaks.append(p)
      if lwpeaks:
        if not atom_linewidths.has_key(atom):
	  atom_linewidths[atom] = []
        atom_linewidths[atom] = atom_linewidths[atom] + lwpeaks

  return atom_linewidths

# -----------------------------------------------------------------------------
#
def show_linewidth_dialog(session):
  sputil.the_dialog(linewidth_plot_dialog,session).show_window(1)
