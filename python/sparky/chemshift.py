# -----------------------------------------------------------------------------
# Display resonances graphically using one line for each group/atom type
#

import math
import string
import Tkinter

import pyutil
import shiftstats
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class resonance_plot_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    tkutil.Dialog.__init__(self, session.tk, 'Chemical Shift Plot')

    self.top.columnconfigure(0, weight = 1)
    r = 0
    
    self.condition_widget = sputil.condition_menu(session, self.top, 'Condition: ')
    self.condition_widget.frame.grid(row = r, sticky = 'w')
    r = r + 1

    self.ppm_range_widget = [None, None]
    er = tkutil.entry_row(self.top, 'PPM range: ',
                          ('min', '0', 3), ('max', '12', 3), ('step', '1', 3))
    (self.ppm_range_widget[0],
     self.ppm_range_widget[1],
     self.ppm_step_widget) = er.variables
    er.frame.grid(row = r, sticky = 'w')
    r = r + 1
    
    e = tkutil.entry_field(self.top, 'Atoms: ', '', 30)
    self.atoms = e.variable
    e.frame.grid(row = r, sticky = 'w')
    r = r + 1
    
    t = tkutil.checkbutton(self.top, 'Show typical amino acid shifts?', 0)
    self.typical_range = t.variable
    t.button.grid(row = r, sticky = 'w')
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
                           ('Help', sputil.help_cb(session, 'ChemShiftPlot')),
			   )
    br.frame.grid(row = r, sticky = 'w')
    r = r + 1

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    if self.get_settings():
      reslist = self.condition.resonance_list()
      slist = shifts_by_atom(reslist, self.min_ppm, self.max_ppm,
                             self.atoms_to_show)
      slist.sort(compare_average_shift)
      self.stoppable_call(self.show_intervals, slist)

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    self.condition = self.condition_widget.condition()

    if self.condition == None:
      self.progress_report('Must select a condition.')
      return 0

    self.min_ppm = pyutil.string_to_float(self.ppm_range_widget[0].get())
    self.max_ppm = pyutil.string_to_float(self.ppm_range_widget[1].get())
    self.ppm_step = pyutil.string_to_float(self.ppm_step_widget.get())

    if self.min_ppm == None or self.max_ppm == None or self.ppm_step == None:
      self.progress_report('Must set ppm min, max, and step.')
      return 0

    self.atoms_per_line = 1

    atoms = tuple(map(string.strip, string.split(self.atoms.get(), ',')))
    if atoms == ('',):
      atoms = ()
    self.atoms_to_show = atoms

    self.show_aa_range = self.typical_range.get()

    return 1

  # ---------------------------------------------------------------------------
  #
  def show_intervals(self, slist):

    p = pyutil.generic_class()

    p.top_yspace = 30
    p.name_xspace = 70
    p.name_yspace = 18
    p.atom_yspace = p.name_yspace / self.atoms_per_line
    p.tick_size = p.atom_yspace / 2
    p.label_gap = 15
    p.left_xspace = 20
    p.names_xspace = p.left_xspace + self.atoms_per_line * p.name_xspace
    p.plot_range = (p.names_xspace + 500, p.names_xspace)
    p.ppm_range = (self.min_ppm, self.max_ppm)

    self.canvas.delete('all')

    self.plot_grid(p, len(slist))
    self.plot_shifts(slist, p)

    box = self.canvas.bbox('all')
    self.canvas['width'] = box[2]
    self.canvas['scrollregion'] = box
    tkutil.set_canvas_corner(self.canvas, 0, 0)

  # ---------------------------------------------------------------------------
  #
  def plot_shifts(self, slist, params):

    self.stoppable_loop('atom types', 5)
    atom_num = 0
    for ashifts in slist:
      self.check_for_stop()
      line = atom_num / self.atoms_per_line
      line_index = atom_num % self.atoms_per_line
      ty = params.top_yspace + params.name_yspace * (line + .2)
      tx = (params.left_xspace + line_index * params.name_xspace)
      name = ashifts.group_symbol + ' ' + ashifts.atom_name
      self.canvas.create_text(tx, ty, anchor = 'w', text = name)
      y = (params.top_yspace + line * params.name_yspace
	   + line_index * params.atom_yspace)
      for r in ashifts.resonances:
	x = pyutil.map_interval(r.frequency, params.ppm_range,
                                params.plot_range)
	id = self.canvas.create_line(x, y, x, y+params.tick_size)
        def show_resonance_peaks(event, session = self.session, resonance = r):
          session.show_resonance_peak_list(resonance)
        self.canvas.tag_bind(id, '<ButtonPress>', show_resonance_peaks)
        
      if self.show_aa_range:
        if ashifts.atom_statistics:
          ave_shift = ashifts.atom_statistics.average_shift
          dev = ashifts.atom_statistics.shift_deviation
          ave_min, ave_max = (ave_shift - dev, ave_shift + dev)
          if (ave_min >= params.ppm_range[0] and
              ave_max <= params.ppm_range[1]):
            x0 = pyutil.map_interval(ave_min, params.ppm_range, params.plot_range)
            x1 = pyutil.map_interval(ave_max, params.ppm_range, params.plot_range)
            ymid = y + params.tick_size / 2
            self.canvas.create_line(x1, ymid, x0, ymid)

      atom_num = atom_num + 1

  # ---------------------------------------------------------------------------
  #
  def plot_grid(self, params, atom_count):

    y1 = params.top_yspace
    y2 = (atom_count / self.atoms_per_line + 1.5) * params.name_yspace
    tick = self.ppm_step * round(params.ppm_range[0] / self.ppm_step)
    end_tick = self.ppm_step * (round(params.ppm_range[1] / self.ppm_step)+.5)
    precision = -int(math.floor(math.log10(self.ppm_step)))
    ppm_format = '%%.%df' % max(0, precision)
    self.stoppable_loop('grid line', 100)
    while tick <= end_tick:
      self.check_for_stop()
      x = pyutil.map_interval(tick, params.ppm_range, params.plot_range)
      self.canvas.create_text(x, y1 - params.label_gap,
			      text = ppm_format % tick)
      self.canvas.create_line(x, y1, x, y2, stipple = 'gray50')
      tick = tick + self.ppm_step

# -----------------------------------------------------------------------------
# Gather shifts for each residue/atom type.
# Return a table mapping atom names to Atom_Shift objects.
#
def shifts_by_atom(reslist, min_ppm, max_ppm, atoms_to_show):

  table = {}
  for r in reslist:
    if r.frequency >= min_ppm and r.frequency <= max_ppm:
      atom = r.atom
      name = atom.group.symbol + ' ' + atom.name
      if (not atoms_to_show or
	  atom.name in atoms_to_show or
	  name in atoms_to_show):
        if not table.has_key(name):
	  table[name] = Atom_Shifts(atom.group.symbol, atom.name)
	table[name].resonances.append(r)

  return table.values()

# -----------------------------------------------------------------------------
# List of resonances for a single residue/atom type
#
class Atom_Shifts:

  def __init__(self, group_symbol, atom_name):

    self.group_symbol = group_symbol
    self.atom_name = atom_name
    self.resonances = []
    self.average_ppm = None
    self.atom_statistics = shiftstats.atom_statistics(group_symbol, atom_name)

  def average_shift(self):

    if self.average_ppm == None:
      sum = 0
      for r in self.resonances:
	sum = sum + r.frequency
      self.average_ppm = sum / len(self.resonances)
    return self.average_ppm

# -----------------------------------------------------------------------------
#
def compare_average_shift(s1, s2):
  return cmp(s1.average_shift(), s2.average_shift())

# -----------------------------------------------------------------------------
#
def show_shifts_dialog(session):
  sputil.the_dialog(resonance_plot_dialog,session).show_window(1)
