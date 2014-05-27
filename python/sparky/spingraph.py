# -----------------------------------------------------------------------------
# Draw a diagram of atoms connected by lines where the lines represent peaks.
#

import math
import string
import types
import Tkinter

import atoms
import pyutil
import sparky
import spinlayout
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class spin_graph_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    self.graph = None
    self.shown_spectra = []
    self.updating = 0
    self.chosen_group_atoms = []

    tkutil.Dialog.__init__(self, session.tk, 'Spin Graph')

    self.top.rowconfigure(1, weight = 1)
    self.top.columnconfigure(0, weight = 1)
    self.top.bind('<Destroy>', self.window_destroyed_cb, 1)
    keypress_cb = pyutil.precompose(sputil.command_keypress_cb, session)
    self.top.bind('<KeyPress>', keypress_cb)

    mbar = self.create_menus(self.top)
    mbar.grid(row = 0, column = 0, sticky = 'ew')

    zc = self.create_canvas(self.top)
    zc.frame.grid(row = 1, column = 0, sticky = 'news')

    stop_button = Tkinter.Button(self.menubar, text = 'Stop',
                                 command = self.stop_cb)
    stop_button.pack(side = 'right')

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.grid(row = 2, column = 0, sticky = 'ew')

    tkutil.Stoppable.__init__(self, progress_label, stop_button)
    
  # ---------------------------------------------------------------------------
  #
  def create_canvas(self, parent):

    zc = tkutil.zoomable_canvas(parent, self.zoom_cb)
    self.zcanvas = zc
    self.canvas = zc.canvas
    self.pointer_action = pointer_action(self)
    return zc
  
  # ---------------------------------------------------------------------------
  #
  def zoom_cb(self, factor):

    if self.graph:
      self.graph.canvas_scaled(factor)
      
  # ---------------------------------------------------------------------------
  #
  def create_menus(self, parent):

    mbar = Tkinter.Frame(parent)
    self.menubar = mbar

    m = tkutil.menu(mbar, 'Show')
    m.button.pack(side = 'left')

    m.add_button('Choose spectra...', self.show_spectrum_dialog)

    m.add_separator()
    m.add_button('What to show...', self.show_what_dialog)
    m.add_button('Feature sizes...', self.show_sizes_dialog)
    
    m.add_separator()
    m.add_button('Row Layout', self.row_layout_cb)
    m.add_button('Load Layout', self.load_layout_cb)
    m.add_button('Save Layout', self.save_layout_cb)
    m.add_button('Templates...', self.templates_cb)

    m.add_separator()
    m.add_button('Center spectrum', self.center_spectrum_cb)
    self.recenter_menu = m
    self.recenter_menu_index = m.last_index()
    
    m.add_separator()
    m.add_button('Save Postscript', self.postscript_cb)

    m.add_separator()
    m.add_button('Help', sputil.help_cb(self.session, 'SpinGraph'))
    m.add_button('Close', self.close_cb)

    return mbar
  
  # ---------------------------------------------------------------------------
  #
  def update_chosen_atoms(self, group_atoms):

    self.chosen_group_atoms = group_atoms
    assignment = sputil.group_atom_assignment_name(group_atoms)
    self.recenter_menu.rename_button(self.recenter_menu_index,
                                     'Center spectrum at ' + assignment)

  # ---------------------------------------------------------------------------
  #
  def center_spectrum_cb(self):

    galist = self.chosen_group_atoms
    
    spectrum = self.session.selected_spectrum()
    if spectrum == None or len(galist) < spectrum.dimension:
      return

    assignment = sputil.group_atom_assignment_name(galist)
    reslist = sputil.group_atom_resonances(spectrum.condition, galist)
    if reslist == None:
      self.progress_report('Unknown resonances %s' % assignment)
      return
    
    sputil.show_assignment(reslist, spectrum)
    self.progress_report('Centered %s at %s' % (spectrum.name, assignment))
    
  # ---------------------------------------------------------------------------
  #
  def show_spectrum_dialog(self):

    d = sputil.the_dialog(spectrum_choice_dialog, self.session)
    d.set_parent_dialog(self, self.shown_spectra, self.show_spectra)
    d.show_window(1)
    
  # ---------------------------------------------------------------------------
  #
  def show_sizes_dialog(self):

    d = sputil.the_dialog(sizes_dialog, self.session)
    d.set_parent_dialog(self, self.size_options(), self.set_sizes)
    d.show_window(1)
    
  # ---------------------------------------------------------------------------
  #
  def size_options(self):

    if self.graph:
      return self.graph.sizes
    return graph_sizes()
    
  # ---------------------------------------------------------------------------
  #
  def set_sizes(self, size_options):

    if self.graph:
      self.graph.update_sizes(size_options)
    
  # ---------------------------------------------------------------------------
  #
  def show_what_dialog(self):

    d = sputil.the_dialog(what_to_show_dialog, self.session)
    d.set_parent_dialog(self, self.what_options(), self.set_what_to_show)
    d.show_window(1)
    
  # ---------------------------------------------------------------------------
  #
  def what_options(self):

    if self.graph:
      return self.graph.what_to_show
    return what_to_show()
    
  # ---------------------------------------------------------------------------
  #
  def set_what_to_show(self, what):

    if self.graph:
      apply(self.graph.update_what_to_show, (), vars(what))

  # ---------------------------------------------------------------------------
  #
  def window_destroyed_cb(self, event):

    if str(event.widget) == str(self.top):
      if self.graph:
        self.graph.break_cycles()
      
  # ---------------------------------------------------------------------------
  #
  def show_spectra(self, spectra):

    if self.updating:
      return

    self.updating = 1

    unshow = pyutil.subtract_lists(self.shown_spectra, spectra)
    for spectrum in unshow:
      self.unplot_spectrum(spectrum)

    show = pyutil.subtract_lists(spectra, self.shown_spectra)
    for spectrum in show:
      self.plot_spectrum(spectrum)

    self.updating = 0

  # ---------------------------------------------------------------------------
  #
  def plot_spectrum(self, spectrum):

    if spectrum in self.shown_spectra:
      return

    if self.graph == None:
      self.layout_molecule(spectrum.molecule)

    peaks = spectrum.peak_list()
    color = sputil.spectrum_color(spectrum)
    elist = self.stoppable_call(self.graph.add_edges, peaks, color, self)

    self.shown_spectra.append(spectrum)

#    out = self.session.stdout
#    out.write('Created %d edges for %d peaks of spectrum %s\n'
#                   % (len(elist), len(peaks), spectrum.name))

  # ---------------------------------------------------------------------------
  #
  def unplot_spectrum(self, spectrum):

    if sparky.object_exists(spectrum):
      self.progress_report('Erasing ' + spectrum.name)
      self.graph.remove_deleted_peaks()
      for peak in spectrum.peak_list():
        self.graph.remove_peak_edges(peak)
      self.progress_report('')
    self.shown_spectra.remove(spectrum)

  # ---------------------------------------------------------------------------
  #
  def unplot_all_spectra(self):

    spectra = tuple(self.shown_spectra)
    for spectrum in spectra:
      self.unplot_spectrum(spectrum)

  # ---------------------------------------------------------------------------
  #
  def layout_molecule(self, molecule):

    groups_per_row = self.zigzag_groups_per_row(len(molecule.group_list()))
    group_atom_list = sputil.molecule_group_atom_list(molecule)
    name_translations = atoms.molecule_atom_name_translations(molecule)

    self.set_graph(group_atom_list, groups_per_row, 0, name_translations)

  # ---------------------------------------------------------------------------
  #
  def set_graph(self, group_atom_list, groups_per_row, pad_factor,
                name_translations):

    self.unplot_all_spectra()
    self.canvas.delete('all')
    self.graph = group_atom_graph(self.session, self.canvas, groups_per_row,
                                  pad_factor, group_atom_list,
                                  name_translations, self)

  # ---------------------------------------------------------------------------
  #
  def zigzag_groups_per_row(self, group_count):

    s = int(math.sqrt(group_count))
    return max(5, s)

  # ---------------------------------------------------------------------------
  #
  def color_group_atom(self, group_atom, color):

    v = self.graph.group_atom_to_vertex[group_atom]
    v.set_color(color)

  # ---------------------------------------------------------------------------
  #
  def shade_group_atom(self, group_atom, shade):

    v = self.graph.group_atom_to_vertex[group_atom]
    v.set_shading(shade)

  # ---------------------------------------------------------------------------
  #
  def add_peak(self, peak):

    color = sputil.spectrum_color(peak.spectrum)
    self.graph.add_peak_edges(peak, color)

  # ---------------------------------------------------------------------------
  #
  def remove_peak(self, peak):

    self.graph.remove_peak_edges(peak)

  # ---------------------------------------------------------------------------
  #
  def row_layout_cb(self):

    if self.graph == None:
      return
    self.graph.single_row_layout()
    
  # ---------------------------------------------------------------------------
  #
  def load_layout_cb(self):

    if self.graph == None:
      self.progress_report('Display a graph before loading a layout')
      return

    path = tkutil.load_file(self.top, 'Load Layout', 'spin_graph')
    if path:
      file = open(path, 'r')
      layout = {}
      for line in file.readlines():
	fields = string.split(line)
	if len(fields) == 6:
	  fields.append('black')
	  fields.append('4')		# dot size
	group_name, atom_name, x, y, label_x, label_y, color = fields
	xy = (string.atof(x), string.atof(y))
	label_xy = (string.atof(label_x), string.atof(label_y))
	layout[(group_name, atom_name)] = (xy, color, label_xy)
      file.close()
      self.graph.set_layout(layout)

  # ---------------------------------------------------------------------------
  #
  def save_layout_cb(self):

    path = tkutil.save_file(self.top, 'Save Layout', 'spin_graph')
    if path:
      file = open(path, 'w')
      for v in self.graph.vertices:
	group_name, atom_name = v.group_atom
	xy = v.position()
	label_xy = v.label_position()
	line = ('%6s %6s %8.2f %8.2f %8.2f %8.2f %s\n'
		% (group_name, atom_name,
		   xy[0], xy[1], label_xy[0], label_xy[1],
		   v.color()))
	file.write(line)
      file.close()

  # ---------------------------------------------------------------------------
  #
  def postscript_cb(self):

    tkutil.postscript_cb(self.canvas)
	      
  # ---------------------------------------------------------------------------
  #
  def templates_cb(self):

    d = sputil.the_dialog(template_dialog, self.session)
    d.set_parent_dialog(self, None, None)
    d.show_window(1)
	      
  # ---------------------------------------------------------------------------
  #
  def show_residue_templates(self, molecule_type):

    if molecule_type == 'Protein':
      layout = spinlayout.protein_layout
    else:
      layout = spinlayout.dna_rna_layout
    pad_factor = .5
    template = spin_graph_template(layout, spinlayout.cell_size, pad_factor,
                                   spinlayout.sizes)

    group_atom_list = template.group_atom_list()
    group_count = len(template.atom_layouts)
    groups_per_row = self.zigzag_groups_per_row(group_count)
    self.set_graph(group_atom_list, groups_per_row, pad_factor, None)

    self.graph.show_atoms(1)
  
  # ---------------------------------------------------------------------------
  #
  def save_residue_templates(self):

    path = tkutil.save_file(self.top, 'Save Templates', 'spin_graph')
    if path:
      template = template_from_graph(self.graph)
      write_template(template, path)

# -----------------------------------------------------------------------------
#
class pointer_action:

  def __init__(self, sg_dialog):

    self.sg_dialog = sg_dialog
    c = sg_dialog.canvas
    c.bind('<ButtonPress>', self.button_press_cb)
    c.bind('<Button1-Motion>', self.pointer_drag_cb)
    c.bind('<Button2-Motion>', self.pointer_drag_cb)
    c.bind('<Button3-Motion>', self.pointer_drag_cb)
    c.bind('<ButtonRelease>', self.button_release_cb)

    self.canvas = c
    self.last_xy = None
    self.chain = vertex_group_chain()

    self.selected_group_atoms = []
    self.atom_selection_callbacks = []
    
  # ---------------------------------------------------------------------------
  #
  def button_press_cb(self, event):

    (x, y) = tkutil.canvas_coordinates(self.canvas, event)
    button_number = event.num
    shift_pressed = event.state & 1
    
    self.start_xy = (x, y)
    self.last_xy = (x, y)

    id = self.clicked_item(self.canvas, x, y)
    self.start_zoom(id)
    self.grab_vertex(id)
    self.grab_label(id)
    self.grab_line(id, button_number)
    self.grab_group(id, button_number)

  # ---------------------------------------------------------------------------
  #
  def pointer_drag_cb(self, event):

    if self.last_xy == None:
      return

    (x, y) = tkutil.canvas_coordinates(self.canvas, event)
    delta = (x - self.last_xy[0], y - self.last_xy[1])

    (self.drag_vertex(delta) or
     self.drag_label(delta) or
     self.drag_group(delta) or
     self.drag_zoom(x, y)
     )

    self.last_xy = (x, y)

  # ---------------------------------------------------------------------------
  #
  def button_release_cb(self, event):

    (x, y) = tkutil.canvas_coordinates(self.canvas, event)

    (self.drop_vertex() or
     self.drop_group(x, y) or
     self.finish_zoom()
     )

    self.last_xy = None

  # ---------------------------------------------------------------------------
  #
  def clicked_item(self, canvas, x, y):

    id_list = canvas.find('closest', x, y)
    if id_list:
      id = id_list[0]
      if id in self.close_items(canvas, x, y):
        return id
    return None

  # ---------------------------------------------------------------------------
  #
  def close_items(self, canvas, x, y):

    r = 5
    return canvas.find('overlapping', x-r, y-r, x+r, y+r)

  # ---------------------------------------------------------------------------
  #
  def start_zoom(self, id):

    self.zooming = (id == None)
    self.drag_box = None
    
  # ---------------------------------------------------------------------------
  #
  def drag_zoom(self, x, y):
    
    if self.zooming:
      if self.drag_box == None:
        self.drag_box = self.canvas.create_rectangle(self.start_xy, (x, y))
      else:
        self.canvas.coords(self.drag_box,
                           self.start_xy[0], self.start_xy[1], x, y)
      return 1

  # ---------------------------------------------------------------------------
  #
  def finish_zoom(self):

    if self.zooming:
      if self.drag_box:
        box = self.canvas.bbox(self.drag_box)
        self.canvas.delete(self.drag_box)
        self.sg_dialog.zcanvas.zoom(box)
      return 1
      
  # ---------------------------------------------------------------------------
  #
  def grab_vertex(self, id):

    self.vertex = None
    g = self.sg_dialog.graph
    if g and g.plot_id_to_vertex.has_key(id):
      v = g.plot_id_to_vertex[id]
      if v.dot_id == id:
        self.vertex = v
        self.moved_vertex = 0
      
  # ---------------------------------------------------------------------------
  #
  def drag_vertex(self, delta):
    
    if self.vertex:
      self.vertex.move(delta)
      self.moved_vertex = 1
      return 1

  # ---------------------------------------------------------------------------
  #
  def drop_vertex(self):

    if self.vertex:
      if not self.moved_vertex:
        self.select_vertex(self.vertex)
      return 1

  # ---------------------------------------------------------------------------
  #
  def select_vertex(self, v):

    self.sg_dialog.progress_report('Chose %s %s' % v.group_atom)
    
    self.remember_resonance(v.group_atom)

    for cb in self.atom_selection_callbacks:
      cb(v.group_atom)

  # ---------------------------------------------------------------------------
  # Record atoms for future recenter spectrum request.
  #
  def remember_resonance(self, group_atom):

    self.selected_group_atoms.append(group_atom)
    
    spectrum = self.sg_dialog.session.selected_spectrum()
    if spectrum == None:
      return

    dim = spectrum.dimension
    if len(self.selected_group_atoms) > dim:
      self.selected_group_atoms = self.selected_group_atoms[-dim:]

    self.sg_dialog.update_chosen_atoms(self.selected_group_atoms)
  
  # ---------------------------------------------------------------------------
  #
  def add_atom_select_callback(self, atom_select_cb):

    self.atom_selection_callbacks.append(atom_select_cb)
      
  # ---------------------------------------------------------------------------
  #
  def grab_label(self, id):

    self.label = None
    g = self.sg_dialog.graph
    if g and g.plot_id_to_vertex.has_key(id):
      v = g.plot_id_to_vertex[id]
      if v.label_id == id:
        self.label = v

  # ---------------------------------------------------------------------------
  #
  def drag_label(self, delta):
  
    if self.label:
      self.label.move_label(delta)
      return 1

  # ---------------------------------------------------------------------------
  #
  def grab_line(self, id, button_number):

    g = self.sg_dialog.graph
    if g and g.plot_id_to_linelet.has_key(id):
      linelet = g.plot_id_to_linelet[id]
      peak = linelet.edges[0].peak
      if button_number == 1:
        sputil.select_peak(peak)
        self.sg_dialog.progress_report('Selected %s of %s' %
                                       (peak.assignment, peak.spectrum.name))
      elif button_number == 2:
        sputil.select_peak(peak)
        sputil.show_peak(peak)
        self.sg_dialog.progress_report('Centered %s at %s' %
                                       (peak.spectrum.name, peak.assignment))

  # ---------------------------------------------------------------------------
  #
  def grab_group(self, id, button_number):

    self.group = None
    g = self.sg_dialog.graph
    if g and g.plot_id_to_group.has_key(id):
      self.group = g.plot_id_to_group[id]
      self.moved_group = 0
      if button_number == 1:
        self.move_type = 'atoms'
        self.drag_box = None
      elif button_number == 2:
        self.move_type = 'label'
      elif button_number == 3:
        self.move_type = 'chain'
        self.chain.grab(self.group)

  # ---------------------------------------------------------------------------
  #
  def drag_group(self, delta):
  
    if self.group:
      if self.move_type == 'label':
        self.group.move_label(delta)
      elif self.move_type == 'atoms':
        if self.drag_box == None:
          box = self.canvas.bbox(self.group.name)
          self.drag_box = self.canvas.create_rectangle(box)
        self.canvas.move(self.drag_box, delta[0], delta[1])
      elif self.move_type == 'chain':
        self.chain.move_chain(delta)
      self.moved_group = 1
      return 1

  # ---------------------------------------------------------------------------
  #
  def drop_group(self, x, y):

    if self.group:
      if self.drag_box:
        self.canvas.delete(self.drag_box)
      if self.move_type == 'atoms':
        vg = self.group
        if self.moved_group:
          vg.move((x - self.start_xy[0], y - self.start_xy[1]))
        else:
          vg.show_atoms(not vg.atoms_displayed())
      elif self.move_type == 'chain':
        self.chain.end_chain_drag()
      return 1

# -----------------------------------------------------------------------------
# Used for interactively dragging a sequence of vertex groups
#
class vertex_group_chain:
  
  # ---------------------------------------------------------------------------
  #
  def __init__(self):

    self.end_groups = {}
  
  # ---------------------------------------------------------------------------
  #
  def grab(self, vertex_group):

    self.chain_groups = self.group_list(vertex_group)
    self.n_grab = self.chain_groups.index(vertex_group)
    self.chain_xy = self.chain_points(self.chain_groups)
    self.chain_minimum_segment_length = (pyutil.chain_length(self.chain_xy)
                                         / len(self.chain_xy))
    self.canvas = vertex_group.graph.canvas
    self.line_id = self.create_line(self.canvas, self.chain_xy)
    self.moved = 0

  # ---------------------------------------------------------------------------
  #
  def group_list(self, vertex_group):

    if not vertex_group.group_number:
      return [vertex_group]

    vg_list = []
    for vg in vertex_group.graph.vertex_groups:
      if vg.is_displayed() and vg.group_number:
        vg_list.append(vg)
    vg_list.sort(compare_group_numbers)

    n = vg_list.index(vertex_group)

    last = n
    for last in range(n+1, len(vg_list)):
      if self.end_groups.has_key(vg_list[last]):
        last = last - 1
        break

    for first in range(n, -1, -1):
      if self.end_groups.has_key(vg_list[first]):
        break

    return vg_list[first:last+1]

  # ---------------------------------------------------------------------------
  #
  def chain_points(self, chain_groups):

    chain_xy = []
    for vg in chain_groups:
      chain_xy.append(vg.position())
    return chain_xy

  # ---------------------------------------------------------------------------
  #
  def create_line(self, canvas, chain_xy):

    if len(chain_xy) >= 2:
      line_id = apply(canvas.create_line, tuple(chain_xy))
      canvas.itemconfigure(line_id, width = 3, fill = 'yellow')
      canvas.lower(line_id)
      return line_id

  # ---------------------------------------------------------------------------
  #
  def move_chain(self, delta):

    self.move_half_chain(delta, self.n_grab, len(self.chain_xy)-1, 1)
    self.move_half_chain(delta, self.n_grab, 0, -1)

    new_p = pyutil.shift_point(self.chain_xy[self.n_grab], delta)
    self.chain_xy[self.n_grab] = new_p
    
    xy_list = []
    for x, y in self.chain_xy:
      xy_list.append(x)
      xy_list.append(y)
      
    apply(self.canvas.coords, (self.line_id,) + tuple(xy_list))

    self.moved = 1
    
  # ---------------------------------------------------------------------------
  #
  def move_half_chain(self, delta, first, last, step):

    chain = self.chain_xy
    p1 = chain[first]
    new_p1 = (p1[0] + delta[0], p1[1] + delta[1])
    for k in range(first + step, last + step, step):
      p0 = p1
      new_p0 = new_p1
      p1 = chain[k]
      new_p1 = self.pull_point(p0, new_p0, p1)
      if new_p1 == p1:
        break
      chain[k] = new_p1
    
  # ---------------------------------------------------------------------------
  #
  def pull_point(self, p0, new_p0, p1):

    d = pyutil.distance(p0, p1)
    new_d = pyutil.distance(new_p0, p1)
    if new_d <= d or new_d <= self.chain_minimum_segment_length:
      return p1
    f1 = d / new_d
    f0 = 1 - f1
    return (f0 * new_p0[0] + f1 * p1[0], f0 * new_p0[1] + f1 * p1[1])
    
  # ---------------------------------------------------------------------------
  #
  def end_chain_drag(self):

    self.canvas.delete(self.line_id)

    if self.moved:
      for k in range(len(self.chain_groups)):
        vg = self.chain_groups[k]
        xy = vg.position()
        new_xy = self.chain_xy[k]
        if new_xy != xy:
          delta = (new_xy[0] - xy[0], new_xy[1] - xy[1])
          vg.move(delta)
    else:
      vg = self.chain_groups[self.n_grab]
      if self.end_groups.has_key(vg):
        del self.end_groups[vg]
        vg.set_color('black')
      else:
        self.end_groups[vg] = 1
        vg.set_color('yellow')
    
# -----------------------------------------------------------------------------
#
def compare_group_numbers(vg1, vg2):

  return cmp(vg1.group_number, vg2.group_number)

# -----------------------------------------------------------------------------
#
class template_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk,
                                    'Spin Graph Residue Templates')

    f = Tkinter.Frame(self.top)
    f.pack(side = 'top')

    message = ('You can adjust the default residue atom layout\n' +
               'by creating a file specifying atom positions, colors,\n' +
               'sizes, and text label positions.  Sparky provides a\n' +
               'default layout file\n' +
               '\n\t/usr/local/sparky/python/spinlayout.py\n\n' +
               'You override this file by making your own copy\n' +
               '\n\t~/Sparky/Python/spinlayout.py\n\n' +
               'You can create the desired template on the screen\n'
               'and save the result in the format expected in spinlayout.py\n'
               'using the edit and save buttons below.')
    
    msg = Tkinter.Label(self.top, justify = 'left', text = message)
    msg.pack(side = 'top', anchor = 'w')
    
    t = tkutil.option_menu(self.top, 'Molecule type: ',
                           ('Protein', 'DNA/RNA'), 'Protein')
    t.frame.pack(side = 'top', anchor = 'w')
    self.molecule_type = t
    
    br = tkutil.button_row(self.top,
			   ('Edit', self.edit_cb),
                           ('Save', self.save_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'SpinGraph')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def edit_cb(self):

    if self.parent_dialog:
      mtype = self.molecule_type.get()
      self.parent_dialog.show_residue_templates(mtype)

  # ---------------------------------------------------------------------------
  #
  def save_cb(self):

    if self.parent_dialog:
      self.parent_dialog.save_residue_templates()

# -----------------------------------------------------------------------------
#
class spectrum_choice_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk, 'Spin Graph Spectra')

    st = sputil.spectrum_checkbuttons(session, self.top, 'Show spectra')
    st.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_table = st
    
    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'SpinGraph')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, spectra):

    s2cb = self.spectrum_table.spectrum_to_checkbutton
    for cb in s2cb.values():
      cb.set_state(0)

    for spectrum in spectra:
      if sparky.object_exists(spectrum):
        s2cb[spectrum].set_state(1)

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    spectra = self.spectrum_table.chosen_spectra
    return spectra
      
# -----------------------------------------------------------------------------
#
class sizes_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk, 'Spin Graph Sizes')

    f = Tkinter.Frame(self.top)
    f.pack(side = 'top')

    tkutil.grid_labels(f,
                       ('Atom label', 1, 0),
                       ('Residue label', 2, 0),
                       ('Peak count', 3, 0),
                       ('Dot radius', 4, 0),
                       ('Line thickness', 5, 0),
                       ('Line spacing', 6, 0),
                       ('Size', 0, 1),
                       ('Scale', 0, 2))

    (self.vertex_font_height,
     self.group_font_height,
     self.line_font_height,
     self.dot_radius,
     self.line_thickness,
     self.line_spacing,
     ) = tkutil.grid_entries(f, 4, ('', 1, 1), ('', 2, 1), ('', 3, 1),
                             ('', 4, 1), ('', 5, 1), ('', 6, 1))

    (self.scale_vertex_label,
     self.scale_group_label,
     self.scale_line_label
     ) = tkutil.grid_checkbuttons(f,
                                  ('', 1, 2),
                                  ('', 2, 2),
                                  ('', 3, 2))

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'SpinGraph')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  #
  def show_settings(self, size_options):

    so = size_options
    self.vertex_font_height.set('%.1f' % so.vertex_font_height)
    self.group_font_height.set('%.1f' % so.group_font_height)
    self.line_font_height.set('%.1f' % so.line_font_height)
    self.dot_radius.set('%.1f' % so.dot_radius)
    self.line_thickness.set('%.1f' % so.line_thickness)
    self.line_spacing.set('%.1f' % so.line_spacing)
    self.scale_vertex_label.set(so.scale_vertex_label)
    self.scale_group_label.set(so.scale_group_label)
    self.scale_line_label.set(so.scale_line_label)
  
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    so = graph_sizes()
    s2f = pyutil.string_to_float
    so.vertex_font_height = s2f(self.vertex_font_height.get(), 10)
    so.group_font_height = s2f(self.group_font_height.get(), 10)
    so.line_font_height = s2f(self.line_font_height.get(), 10)
    so.dot_radius = s2f(self.dot_radius.get(), 1)
    so.line_thickness = s2f(self.line_thickness.get(), 1)
    so.line_spacing = s2f(self.line_spacing.get(), 1)
    so.scale_vertex_label = self.scale_vertex_label.get()
    so.scale_group_label = self.scale_group_label.get()
    so.scale_line_label = self.scale_line_label.get()

    return so
  
# -----------------------------------------------------------------------------
#
class what_to_show_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk, 'Spin Graph Display')

    cb = tkutil.checkbutton(self.top, 'Show atoms?', 0)
    cb.button.pack(side = 'top', anchor = 'w')
    self.show_atoms = cb.variable

    ef = tkutil.entry_field(self.top, 'Only atoms')
    ef.frame.pack(side = 'top', anchor = 'w')
    self.only_these_atoms = ef.variable

    ef = tkutil.entry_field(self.top, 'Only residues')
    ef.frame.pack(side = 'top', anchor = 'w')
    self.only_these_residues = ef.variable

    cb = tkutil.checkbuttons(self.top, 'top', '',
                             'Atom labels',
                             'Residue labels',
                             'Peak counts',
                             'Lines to residue labels')
    cb.frame.pack(side = 'top', anchor = 'w')
    (self.show_vertex_label,
     self.show_group_label,
     self.show_line_label,
     self.lines_to_groups,
     ) = cb.variables
    
    cb = tkutil.checkbuttons(self.top, 'top', '',
                             'Intra-residue peaks',
                             'Peaks i to i+1',
                             'Peaks i to i+2, i+3, ...',
                             'Shade by peak range')
    cb.frame.pack(side = 'top', anchor = 'w')
    self.show_range = {}
    (self.show_range['intra-residue'],
     self.show_range['sequential'],
     self.show_range['long-range'],
     self.shade_by_range,
     ) = cb.variables

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'SpinGraph')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  #
  def show_settings(self, what_to_show):
    
    what = what_to_show

    self.show_atoms.set(what.show_atoms)
    astring = pyutil.concatenate_strings(what.only_these_atoms, ' ')
    self.only_these_atoms.set(astring)
    rranges = pyutil.integers_to_ranges(what.only_these_residues)
    self.only_these_residues.set(rranges)
      
    self.show_vertex_label.set(what.show_vertex_label)
    self.show_group_label.set(what.show_group_label)
    self.show_line_label.set(what.show_line_label)
    self.lines_to_groups.set(what.lines_to_groups)

    for range in ('intra-residue', 'sequential', 'long-range'):
      self.show_range[range].set(what.show_range[range])
    self.shade_by_range.set(what.shade_by_range)

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    what = what_to_show()

    what.show_atoms = self.show_atoms.get()
    what.only_these_atoms = string.split(self.only_these_atoms.get())
    what.only_these_residues = pyutil.ranges_to_integers(self.only_these_residues.get())
    what.show_vertex_label = self.show_vertex_label.get()
    what.show_group_label = self.show_group_label.get()
    what.show_line_label = self.show_line_label.get()
    what.lines_to_groups = self.lines_to_groups.get()
    for range in ('intra-residue', 'sequential', 'long-range'):
      what.show_range[range] = self.show_range[range].get()
    what.shade_by_range = self.shade_by_range.get()

    return what
  
# -----------------------------------------------------------------------------
#
class graph:

  def __init__(self, vertices, vertex_groups, sizes, canvas, stoppable):

    self.what_to_show = what_to_show()
    self.sizes = sizes
    self.stoppable = stoppable
    
    t = {}
    for v in vertices:
      v.graph = self
      t[v.group_atom] = v
    self.group_atom_to_vertex = t

    for vg in vertex_groups:
      vg.graph = self
      vg.xy = vg.bottom_position()

    self.vertices = vertices
    self.vertex_groups = vertex_groups
    self.edges = []
    self.lines = {}             # table for deletion speed, line -> 1
    self.canvas = canvas

    self.plot_id_to_vertex = {}
    self.plot_id_to_linelet = {}
    self.plot_id_to_group = {}
    self.pair_to_line = {}
    self.peak_to_edges = {}

    for vg in vertex_groups:
      vg.display()

    self.full_view('x')

  # ---------------------------------------------------------------------------
  #
  def show_atoms(self, show):

    self.stoppable.stoppable_loop('atoms', 50)
    check_for_stop = self.stoppable.check_for_stop
    
    if show:
      for v in self.vertices:
        check_for_stop()
        v.display()
    else:
      for v in self.vertices:
        check_for_stop()
        v.undisplay()

  # ---------------------------------------------------------------------------
  #
  def reposition_group_labels(self):

    for vg in self.vertex_groups:
      vg.move_label_to_bottom()

  # ---------------------------------------------------------------------------
  #
  def set_layout(self, layout):

    c = self.canvas
    for v in self.vertices:
      if layout.has_key(v.group_atom):
	xy, color, label_xy = layout[v.group_atom]
        v.set_geometry(xy, label_xy)
        v.set_color(color)
    
    self.move_edges(self.edges)
    self.reposition_group_labels()
    self.full_view('x')

  # ---------------------------------------------------------------------------
  #
  def single_row_layout(self):

    vgroups = list(self.vertex_groups)
    vgroups.sort(self.group_order)

    x = 0
    y = 0
    pad_factor = 1
    max_height = 0
    for vg in vgroups:
      x1, y1, x2, y2 = vg.vertex_bounding_box()
      width = x2 - x1
      height = y2 - y1
      vg.move((x - x1, y - y2))
      x = x + width * (1 + pad_factor)
      max_height = max(max_height, height)

    for vg in vgroups:
      vg.move((0, max_height))

    self.full_view('y')
    
  # ---------------------------------------------------------------------------
  #
  def group_order(self, vg1, vg2):

    return cmp(vg1.group_number, vg2.group_number) or cmp(vg1.name, vg2.name)
  
  # ---------------------------------------------------------------------------
  #
  def full_view(self, xy):

    factor = tkutil.fit_canvas_to_window(self.canvas, xy)
    self.canvas_scaled(factor)

  # ---------------------------------------------------------------------------
  #
  def canvas_scaled(self, factor):

    # Resize fonts

    so = self.sizes
    if so.scale_vertex_label:
      so.vertex_font_height = factor * so.vertex_font_height
    if so.scale_group_label:
      so.group_font_height = factor * so.group_font_height
    if so.scale_line_label:
      so.line_font_height = factor * so.line_font_height
    self.set_font_sizes()

    so.dot_radius = factor * so.dot_radius
    
    # Reposition undisplayed vertices and groups
    
    for v in self.vertices:
      v.scale(factor)
    for vg in self.vertex_groups:
      vg.scale(factor)
    for line in self.lines.keys():
      line.scale(factor)

  # ---------------------------------------------------------------------------
  #
  def vertex_font(self):
    return 'Courier %d' % max(2, self.sizes.vertex_font_height)
  def group_font(self):
    return 'Courier %d bold' % max(2, self.sizes.group_font_height)
  def line_font(self):
    return 'Courier %d' % max(2, self.sizes.line_font_height)
  def set_font_sizes(self):
    c = self.canvas
    c.itemconfigure('vertex-label', font = self.vertex_font())
    c.itemconfigure('group-label', font = self.group_font())
    c.itemconfigure('line-label', font = self.line_font())

  # ---------------------------------------------------------------------------
  #
  def update_sizes(self, sizes):

    self.sizes = sizes
    self.set_font_sizes()
    
    for v in self.vertices:
      v.dot_resized()
    
    for vg in self.vertex_groups:
      vg.label_resized()

    self.canvas.itemconfigure('line', width = sizes.line_thickness)
    for line in self.lines.keys():
      line.move()

  # ---------------------------------------------------------------------------
  #
  def update_what_to_show(self, **kw):

    what = self.what_to_show

    #
    # Need to call what_changed() for all fields to update what dictionary.
    #
    change = self.what_changed('show_atoms', kw, what)
    change = self.what_changed('only_these_atoms', kw, what) or change
    change = self.what_changed('only_these_residues', kw, what) or change
    if change:
      self.show_only_these(what.show_atoms, what.only_these_atoms,
                           what.only_these_residues)

    if self.what_changed('show_vertex_label', kw, what):
      for v in self.vertices:
        v.show_label(what.show_vertex_label)

    if self.what_changed('what.show_group_label', kw, what):
      for vg in self.vertex_groups:
        vg.show_label(what.show_group_label)

    if self.what_changed('show_line_label', kw, what):
      for line in self.lines.keys():
        line.show_count(what.show_line_label)

    # update for lines to groups switch
    if self.what_changed('lines_to_groups', kw, what):
      for vg in self.vertex_groups:
        vg.redisplay_lines()

    if self.what_changed('show_range', kw, what):
      for e in self.edges:
        if what.show_range[e.range]:
          e.display()
        else:
          e.undisplay()

    if self.what_changed('shade_by_range', kw, what):
      for e in self.edges:
        e.update_shading()

  # ---------------------------------------------------------------------------
  #
  def what_changed(self, attribute, kw, what_to_show):

    changed = (kw.has_key(attribute) and
               kw[attribute] != getattr(what_to_show, attribute))
    if changed:
      setattr(what_to_show, attribute, kw[attribute])
    return changed
      
  # ---------------------------------------------------------------------------
  # If residue number list is empty this means accept any residue number.
  # If atom name list is empty accept any atom name.
  #
  def show_only_these(self, show_atoms, atom_names, residue_numbers):

    rtable = {}
    for r in residue_numbers:
      rtable[r] = 1

    shown_groups = {}
    for vg in self.vertex_groups:
      if len(rtable) == 0 or rtable.has_key(vg.group_number):
        shown_groups[vg] = 1
        vg.display()
      else:
        vg.undisplay()

    atable = {}
    for a in atom_names:
      atable[a] = 1

    for v in self.vertices:
      if (show_atoms and shown_groups.has_key(v.vertex_group) and
          (len(atable) == 0 or atable.has_key(v.group_atom[1]))):
        v.display()
      else:
        v.undisplay()
        
  # ---------------------------------------------------------------------------
  #
  def move_edges(self, edges):

    for e in edges:
      e.move()

  # ---------------------------------------------------------------------------
  #
  def add_edges(self, peaks, color, stoppable = tkutil.Not_Stoppable()):

    description = 'peaks'
    if peaks:
      description = peaks[0].spectrum.name + ' peaks'
    stoppable.stoppable_loop(description, 50)

    edges = []
    for peak in peaks:
      stoppable.check_for_stop()
      elist = self.add_peak_edges(peak, color)
      for e in elist:
        edges.append(e)
    return edges

  # ---------------------------------------------------------------------------
  #
  def add_peak_edges(self, peak, color):

    elist = []
    if peak.is_assigned:
      vtable = self.group_atom_to_vertex
      ga = sputil.group_atom_assignment(peak.resonances())
      for a in range(len(ga)-1):
	ga0 = ga[a]
	ga1 = ga[a+1]
	if (vtable.has_key(ga0) and vtable.has_key(ga1)):
          v0 = vtable[ga0]
          v1 = vtable[ga1]
          rtype = assignment_range(sputil.group_number(v0.group_atom[0]),
                                   sputil.group_number(v1.group_atom[0]))
	  e = edge(self, peak, v0, v1, color, rtype)
	  self.edges.append(e)
          e.display()
          elist.append(e)
      self.peak_to_edges[peak] = elist
    return elist

  # ---------------------------------------------------------------------------
  #
  def remove_peak_edges(self, peak):

    if self.peak_to_edges.has_key(peak):
      self.remove_edges(self.peak_to_edges[peak])
      del self.peak_to_edges[peak]

  # ---------------------------------------------------------------------------
  #
  def remove_deleted_peaks(self):

    for peak in self.peak_to_edges.keys():
      if not sparky.object_exists(peak):
        self.remove_peak_edges(peak)
        
  # ---------------------------------------------------------------------------
  #
  def remove_edges(self, edges):

    self.edges = pyutil.subtract_lists(self.edges, edges)

    for e in edges:
      e.undisplay()
      e.v0.edges.remove(e)
      e.v1.edges.remove(e)
  
  # ---------------------------------------------------------------------------
  #
  def break_cycles(self):

    for v in self.vertices:
      v.edges = None
      v.graph = None
      v.vertex_group = None
    for e in self.edges:
      e.graph = None
    for vg in self.vertex_groups:
      vg.graph = None

# -----------------------------------------------------------------------------
#
class what_to_show:

  def __init__(self):

    self.show_atoms = 0
    self.only_these_atoms = ()
    self.only_these_residues = ()
    
    self.show_vertex_label = 1
    self.show_group_label = 1
    self.show_line_label = 1
    self.lines_to_groups = 1

    self.show_range = {'intra-residue':1, 'sequential':1, 'long-range':1}
    self.shade_by_range = 1

  # ---------------------------------------------------------------------------
  #
  shades = {'intra-residue':'',
            'sequential':'gray25',
            'long-range':'gray50',
            None:''}
  def range_shading(self, range):

    if self.shade_by_range and self.shades.has_key(range):
      return self.shades[range]
    return ''

# -----------------------------------------------------------------------------
#
class graph_sizes:

  def __init__(self):

    self.vertex_font_height = 0
    self.group_font_height = 0
    self.line_font_height = 0
    self.dot_radius = 0
    self.line_thickness = 0
    self.line_spacing = 0

    self.scale_vertex_label = 1
    self.scale_group_label = 1
    self.scale_line_label = 1

# -----------------------------------------------------------------------------
#
class vertex:

  def __init__(self, group_name, atom_name, xy, color, label_xy):

    self.group_atom = (group_name, atom_name)
    self.edges = []
    self.graph = None
    self.vertex_group = None
    self.dot_id = None
    self.label_id = None
    self.xy = xy
    self.label_xy = label_xy
    self.clr = color
    self.shade = ''
    
  # ---------------------------------------------------------------------------
  #
  def position(self):

    if self.dot_id == None:
      return self.xy
    else:
      return pyutil.rectangle_center(self.graph.canvas.coords(self.dot_id))

  # ---------------------------------------------------------------------------
  #
  def move(self, delta):

    if self.is_displayed():
      c = self.graph.canvas
      c.move(self.dot_id, delta[0], delta[1])
    else:
      self.xy = (self.xy[0] + delta[0], self.xy[1] + delta[1])
    self.move_label(delta)
    for e in self.edges:
      e.move()

  # ---------------------------------------------------------------------------
  #
  def scale(self, scale):

    self.xy = (scale * self.xy[0], scale * self.xy[1])
    self.label_xy = (scale * self.label_xy[0], scale * self.label_xy[1])
    
  # ---------------------------------------------------------------------------
  #
  def label_position(self):

    if self.label_id == None:
      return self.label_xy
    else:
      return tuple(self.graph.canvas.coords(self.label_id))

  # ---------------------------------------------------------------------------
  #
  def move_label(self, delta):

    if self.label_id == None:
      self.label_xy = (self.label_xy[0] + delta[0],
                       self.label_xy[1] + delta[1])
    else:
      c = self.graph.canvas
      c.move(self.label_id, delta[0], delta[1])
      
  # ---------------------------------------------------------------------------
  #
  def label_text(self):

    return self.group_atom[1]
    
  # ---------------------------------------------------------------------------
  #
  def color(self):

    if self.dot_id == None:
      return self.clr
    else:
      c = self.graph.canvas
      return c.itemcget(self.dot_id, 'fill')
    
  # ---------------------------------------------------------------------------
  #
  def set_color(self, color):

    self.clr = color
    if self.dot_id != None:
      c = self.graph.canvas
      c.itemconfigure(self.dot_id, fill = color)
    
  # ---------------------------------------------------------------------------
  #
  def shading(self):

    if self.dot_id == None:
      return self.shade
    else:
      c = self.graph.canvas
      return c.itemcget(self.dot_id, 'stipple')
    
  # ---------------------------------------------------------------------------
  #
  def set_shading(self, shading):

    self.shade = shading
    if self.dot_id != None:
      c = self.graph.canvas
      c.itemconfigure(self.dot_id, stipple = shading)

  # ---------------------------------------------------------------------------
  #
  def dot_resized(self):

    self.set_geometry(self.position(), self.label_position())

  # ---------------------------------------------------------------------------
  #
  def set_geometry(self, xy, label_xy):

    self.xy = xy
    self.label_xy = label_xy
    if self.dot_id != None:
      x, y = self.xy
      r = self.graph.sizes.dot_radius
      self.graph.canvas.coords(self.dot_id, x - r, y - r, x + r, y + r)
    if self.label_id != None:
      x, y = self.label_xy
      self.graph.canvas.coords(self.label_id, x, y)

  # ---------------------------------------------------------------------------
  #
  def is_displayed(self):

    return self.dot_id != None

  # ---------------------------------------------------------------------------
  #
  def display(self):

    self.show_dot(1)
    self.show_label(self.graph.what_to_show.show_vertex_label)
      
  # ---------------------------------------------------------------------------
  #
  def undisplay(self):

    self.show_dot(0)
    self.show_label(0)

  # ---------------------------------------------------------------------------
  #
  def show_dot(self, show):
    if show:
      if self.dot_id == None:

        x, y = self.xy
        r = self.graph.sizes.dot_radius
        dot_coords = (x - r, y - r, x + r, y + r)

        g = self.graph
        c = g.canvas
        self.dot_id = c.create_oval(dot_coords, fill = self.clr,
                                    stipple = self.shade,
                                    tags = ('vertex', self.group_atom[0]))
        self.graph.plot_id_to_vertex[self.dot_id] = self
        self.redisplay_lines()

    else:
      if self.dot_id != None:

        self.xy = self.position()
        self.clr = self.color()
        self.shade = self.shading()

        g = self.graph
        c = g.canvas
        c.delete(self.dot_id)
        del g.plot_id_to_vertex[self.dot_id]
        self.dot_id = None
        self.redisplay_lines()

  # ---------------------------------------------------------------------------
  #
  def redisplay_lines(self):

    for e in self.edges:
      e.redisplay_line()

  # ---------------------------------------------------------------------------
  #
  def show_label(self, show):

    if show:
      if self.is_displayed() and self.label_id == None:
        g = self.graph
        c = g.canvas
        self.label_id = c.create_text(self.label_xy, text = self.label_text(),
                                      font = g.vertex_font(),
                                      tags = 'vertex-label')
        g.plot_id_to_vertex[self.label_id] = self
    else:
      if self.label_id != None:
        self.label_xy = self.label_position()
        g = self.graph
        c = g.canvas
        c.delete(self.label_id)
        del g.plot_id_to_vertex[self.label_id]
        self.label_id = None

# -----------------------------------------------------------------------------
#
class edge:

  def __init__(self, graph, peak, v0, v1, color, range):

    self.graph = graph
    self.peak = peak
    self.v0 = v0
    self.v1 = v1
    v0.edges.append(self)
    v1.edges.append(self)
    self.color = color
    self.range = range
    self.shading = graph.what_to_show.range_shading(range)
    self.line = None
    
  # ---------------------------------------------------------------------------
  #
  def is_displayed(self):

    return self.line != None

  # ---------------------------------------------------------------------------
  #
  def display(self):

    g = self.graph
    if self.is_displayed() or not g.what_to_show.show_range[self.range]:
      return
    
    v_or_vg_0 = self.end_vertex(self.v0)
    v_or_vg_1 = self.end_vertex(self.v1)
    if v_or_vg_0 and v_or_vg_1 and v_or_vg_0 != v_or_vg_1:
      p = (v_or_vg_0, v_or_vg_1)
      if not g.pair_to_line.has_key(p):
        el = line(v_or_vg_0, v_or_vg_1)
        g.pair_to_line[p] = el
        g.pair_to_line[(v_or_vg_1, v_or_vg_0)] = el
      self.line = g.pair_to_line[p]
      self.line.add_edge(self)

  # ---------------------------------------------------------------------------
  #
  def end_vertex(self, vertex):

    if vertex.is_displayed():
      return vertex
    elif (self.graph.what_to_show.lines_to_groups and
          vertex.vertex_group and
          vertex.vertex_group.is_displayed()):
      return vertex.vertex_group

  # ---------------------------------------------------------------------------
  #
  def undisplay(self):

    if self.line:
      self.line.remove_edge(self)
      self.line = None

  # ---------------------------------------------------------------------------
  #
  def move(self):

    if self.line:
      self.line.move()

  # ---------------------------------------------------------------------------
  #
  def redisplay_line(self):

    self.undisplay()
    self.display()

  # ---------------------------------------------------------------------------
  #
  def update_shading(self):
    
    shading = self.graph.what_to_show.range_shading(self.range)
    if shading != self.shading:
      self.shading = shading
      if self.line:
        self.line.change_shading(self.color, shading)

# -----------------------------------------------------------------------------
# A line manages one or more parallel colored segments between vertices
# and an optionally displayed count.  Each segment is a linelet object.
#
class line:

  def __init__(self, v_or_vg_0, v_or_vg_1):

    self.graph = v_or_vg_0.graph
    self.v_or_vg_0 = v_or_vg_0
    self.v_or_vg_1 = v_or_vg_1
    self.linelets = {}                  # color -> linelet
    self.edge_count = 0

    g = self.graph
    g.lines[self] = 1

    self.label_id = None
    self.show_count(g.what_to_show.show_line_label)

  # ---------------------------------------------------------------------------
  #
  def show_count(self, show):

    if show:
      if self.label_id == None:
        g = self.graph
        c = g.canvas
        p0, p1 = self.end_points()
        lp = self.label_position(p0, p1)
        self.label_id = c.create_text(lp, font = g.line_font(),
                                      tags = 'line-label')
        self.update_count()
    else:
      if self.label_id != None:
        self.graph.canvas.delete(self.label_id)
        self.label_id = None

  # ---------------------------------------------------------------------------
  #
  def update_count(self):

    if self.label_id != None:
      c = self.graph.canvas
      c.itemconfigure(self.label_id, text = str(self.edge_count))

  # ---------------------------------------------------------------------------
  # Change shading for linelet of specified color.
  #
  def change_shading(self, color, shading):

    if self.linelets.has_key(color):
      self.linelets[color].change_shading(shading)

  # ---------------------------------------------------------------------------
  #
  def add_edge(self, edge):

    color = edge.color
    if not self.linelets.has_key(color):
      g = self.graph
      offset = len(self.linelets)
      p0, p1 = self.end_points()
      normal = self.line_normal(p0, p1)
      shading = edge.shading
      self.linelets[color] = linelet(g, p0, p1, normal, offset, color, shading)
    self.linelets[color].add_edge(edge)
    self.edge_count = self.edge_count + 1
    self.update_count()
    
  # ---------------------------------------------------------------------------
  #
  def remove_edge(self, edge):

    self.remove_edge_2(edge)
    self.update_count()
    if self.edge_count == 0:
      self.undisplay()
    
  # ---------------------------------------------------------------------------
  #
  def remove_edge_2(self, edge):

    linelet = self.linelets[edge.color]
    linelet.remove_edge(edge)
    self.edge_count = self.edge_count - 1
    if len(linelet.edges) == 0:
      offset_deleted = linelet.offset
      del self.linelets[edge.color]
      for ll in self.linelets.values():
        if ll.offset > offset_deleted:
          ll.offset = ll.offset - 1
      self.move()
    
  # ---------------------------------------------------------------------------
  #
  def undisplay(self):

    g = self.graph
    c = g.canvas
    if self.label_id != None:
      c.delete(self.label_id)
    del g.pair_to_line[(self.v_or_vg_0, self.v_or_vg_1)]
    del g.pair_to_line[(self.v_or_vg_1, self.v_or_vg_0)]
    del g.lines[self]

  # ---------------------------------------------------------------------------
  #
  def move(self):

    p0, p1 = self.end_points()
    normal = self.line_normal(p0, p1)
    for linelet in self.linelets.values():
      linelet.move(p0, p1, normal)
    self.move_label()
    
  # ---------------------------------------------------------------------------
  #
  def move_label(self):

    if self.label_id != None:
      p0, p1 = self.end_points()
      c = self.graph.canvas
      lp = self.label_position(p0, p1)
      apply(c.coords, (self.label_id,) + lp)

  # ---------------------------------------------------------------------------
  #
  def scale(self, factor):

    # Count offset distance and linelet separation don't scale
    self.move()
    
  # ---------------------------------------------------------------------------
  #
  def end_points(self):

    p0 = self.v_or_vg_0.position()
    p1 = self.v_or_vg_1.position()
    return p0, p1

  # ---------------------------------------------------------------------------
  #
  def label_position(self, p0, p1):

    mx, my = (.5 * (p0[0] + p1[0]), .5 * (p0[1] + p1[1]))
    nx, ny = self.line_normal(p0, p1)
    sizes = self.graph.sizes
    label_offset = sizes.line_font_height + .5 * sizes.line_thickness
    lp = (mx + nx * label_offset, my + ny * label_offset)
    return lp

  # ---------------------------------------------------------------------------
  #
  def line_normal(self, p0, p1):

    nx, ny = (p0[1] - p1[1], p1[0] - p0[0])
    norm = math.sqrt(nx * nx + ny * ny)
    if norm > 0:
      nx = nx / norm
      ny = ny / norm
    else:
      nx = 0
      ny = 1
    return (nx, ny)
    
# -----------------------------------------------------------------------------
# A linelet is one of the parallel colored segments that comprise a line.
#
class linelet:

  def __init__(self, graph, p0, p1, normal, offset, color, shading):

    self.graph = graph
    self.offset = offset
    self.edges = []
    self.shading = shading

    g = self.graph
    c = g.canvas
    op0, op1 = self.offset_points(p0, p1, normal)
    self.line_id = c.create_line(op0[0], op0[1], op1[0], op1[1],
                                 width = g.sizes.line_thickness,
                                 fill = color, stipple = shading,
                                 tags = 'line')
    c.lower(self.line_id)
    g.plot_id_to_linelet[self.line_id] = self

  # ---------------------------------------------------------------------------
  #
  def add_edge(self, edge):

    self.edges.append(edge)
    
  # ---------------------------------------------------------------------------
  #
  def remove_edge(self, edge):

    self.edges.remove(edge)
    if len(self.edges) == 0:
      g = self.graph
      c = g.canvas
      c.delete(self.line_id)
      del g.plot_id_to_linelet[self.line_id]
      self.line_id = None

  # ---------------------------------------------------------------------------
  #
  def move(self, p0, p1, normal):

    op0, op1 = self.offset_points(p0, p1, normal)
    c = self.graph.canvas
    c.coords(self.line_id, op0[0], op0[1], op1[0], op1[1])

  # ---------------------------------------------------------------------------
  #
  def offset_points(self, p0, p1, normal):

    offset = -self.offset * self.graph.sizes.line_spacing
    dx, dy =  offset * normal[0], offset * normal[1]
    return (p0[0] + dx, p0[1] + dy), (p1[0] + dx, p1[1] + dy)

  # ---------------------------------------------------------------------------
  #
  def change_shading(self, shading):

    if shading != self.shading:
      self.shading = shading
      c = self.graph.canvas
      c.itemconfigure(self.line_id, stipple = shading)
      
# -----------------------------------------------------------------------------
#
class vertex_group:

  def __init__(self, name, vertices):

    self.name = name
    self.group_number = sputil.group_number(name)
    self.vertices = vertices
    self.graph = None
    self.label_id = None
    self.xy = (0, 0)

  # ---------------------------------------------------------------------------
  #
  def add_vertex(self, v):

    self.vertices.append(v)
    v.vertex_group = self

  # ---------------------------------------------------------------------------
  #
  def is_displayed(self):

    return self.label_id != None
  
  # ---------------------------------------------------------------------------
  #
  def display(self):

    self.show_label(self.graph.what_to_show.show_group_label)

  # ---------------------------------------------------------------------------
  #
  def undisplay(self):

    self.show_label(0)
    self.show_atoms(0)

  # ---------------------------------------------------------------------------
  #
  def show_label(self, show):

    if show:
      if self.label_id == None:
        g = self.graph
        c = g.canvas
        self.bg_id = c.create_rectangle(self.xy, self.xy,
                                        fill = c['background'],
                                        outline = '')
        self.label_id = c.create_text(self.xy, text = self.name,
                                      font = g.group_font(),
                                      tag = ('group-label', self.name))
        apply(c.coords, (self.bg_id,) + c.bbox(self.label_id))
        g.plot_id_to_group[self.label_id] = self
        self.redisplay_lines()
    else:
      if self.label_id != None:
        self.xy = self.position()
        g = self.graph
        c = g.canvas
        c.delete(self.bg_id)
        c.delete(self.label_id)
        del g.plot_id_to_group[self.label_id]
        self.label_id = None
        self.redisplay_lines()

  # ---------------------------------------------------------------------------
  #
  def position(self):

    if self.label_id == None:
      return self.xy
    return tuple(self.graph.canvas.coords(self.label_id))

  # ---------------------------------------------------------------------------
  #
  def move(self, delta):

    self.move_label(delta)
    for v in self.vertices:
      v.move(delta)

  # ---------------------------------------------------------------------------
  #
  def move_label(self, delta):

    if self.is_displayed():
      c = self.graph.canvas
      c.move(self.label_id, delta[0], delta[1])
      c.move(self.bg_id, delta[0], delta[1])
    else:
      self.xy = (self.xy[0] + delta[0], self.xy[1] + delta[1])

  # ---------------------------------------------------------------------------
  #
  def redisplay_lines(self):

    for v in self.vertices:
      v.redisplay_lines()

  # ---------------------------------------------------------------------------
  #
  def scale(self, scale):

    self.xy = (scale * self.xy[0], scale * self.xy[1])
    self.label_resized()

  # ---------------------------------------------------------------------------
  # Resize backing rectangle
  #
  def label_resized(self):
    
    if self.is_displayed():
      c = self.graph.canvas
      apply(c.coords, (self.bg_id,) + c.bbox(self.label_id))

  # ---------------------------------------------------------------------------
  #
  def move_label_to_bottom(self):

    self.xy = self.bottom_position()
    if self.label_id != None:
      apply(self.graph.canvas.coords, (self.label_id,) + self.xy)

  # ---------------------------------------------------------------------------
  #
  def bottom_position(self):

    x1, y1, x2, y2 = self.vertex_bounding_box()
    label_offset = 2 * self.graph.sizes.group_font_height
    x = .5 * (x1 + x2)
    y = y2 + label_offset
    return (x, y)

  # ---------------------------------------------------------------------------
  #
  def vertex_bounding_box(self):

    xlist = []
    ylist = []
    for v in self.vertices:
      x, y = v.position()
      xlist.append(x)
      ylist.append(y)
    return (min(xlist), min(ylist), max(xlist), max(ylist))

  # ---------------------------------------------------------------------------
  #
  def set_color(self, color):

    c = self.graph.canvas
    c.itemconfigure(self.label_id, fill = color)

  # ---------------------------------------------------------------------------
  #
  def show_atoms(self, show):

    if show:
      for v in self.vertices:
        v.display()
      if self.label_id != None:
        c = self.graph.canvas
        c.tkraise(self.bg_id)
        c.tkraise(self.label_id)
    else:
      for v in self.vertices:
        v.undisplay()

  # ---------------------------------------------------------------------------
  #
  def atoms_displayed(self):

    for v in self.vertices:
      if v.is_displayed():
        return 1
    return 0
  
# ---------------------------------------------------------------------------
#
def unit_normal(x0, y0, x1, y1):

  dx = x1 - x0
  dy = y1 - y0
  d = math.sqrt(dx * dx + dy * dy)
  if d > 0:
    dx = dx / d
    dy = dy / d
  return (-dy, dx)

# -----------------------------------------------------------------------------
#
def assignment_range(g0, g1):
  if g0 != None and g1 != None:
    d = abs(g1 - g0)
    if d == 0:
      return 'intra-residue'
    elif d == 1:
      return 'sequential'
    else:
      return 'long-range'
  return None
  
# -----------------------------------------------------------------------------
#
def group_atom_graph(session, canvas, groups_per_row, pad_factor,
                     group_atom_list, atom_name_translations, stoppable):

  template = spin_graph_template(spinlayout.layout,
                                 spinlayout.cell_size,
                                 pad_factor,
                                 spinlayout.sizes)
  vlist = []
  nolayout = []
  stoppable.stoppable_loop('Spin graph atoms', 50) 
  for ga in group_atom_list:
    stoppable.check_for_stop()
    place = template.vertex_placement(groups_per_row,
                                      ga[0], ga[1], atom_name_translations)
    if place:
      xy, color, label_xy = place
      v = vertex(ga[0], ga[1], xy, color, label_xy)
      vlist.append(v)
    else:
      nolayout.append(ga)

  if nolayout:
    names = ''
    for ga in nolayout:
      names = names + '%s%s, ' % ga
    names = names[:-2]
    session.stdout.write('No template layout for atoms %s\n' % names)

  vgroups = atom_groups(vlist)

  sizes = graph_sizes()
  for attr, value in spinlayout.sizes.items():
    setattr(sizes, attr, value)

  g = graph(vlist, vgroups, sizes, canvas, stoppable)
  
  return g

# ---------------------------------------------------------------------------
#
def atom_groups(vertices):

  gtable = {}
  for v in vertices:
    group_name = v.group_atom[0]
    if not gtable.has_key(group_name):
      gtable[group_name] = vertex_group(group_name, [])
    gtable[group_name].add_vertex(v)
  return gtable.values()

# -----------------------------------------------------------------------------
#
#	atom_layouts[group_symbol][standard_atom_name]
#
#         = ((x, y), color, (label_x, label_y))
#
#	cell_size = (width, height) of cell containing a group
#
class spin_graph_template:

  def __init__(self, layout, cell_size, pad_factor, sizes):

    self.atom_layouts = layout
    self.cell_size = cell_size
    self.pad_factor = pad_factor
    self.sizes = sizes

  # ---------------------------------------------------------------------------
  # Return (position, color, label_position)
  #
  def vertex_placement(self, groups_per_row,
                       group_name, atom_name, name_translations):

    group_symbol, seqnum = sputil.parse_group_name(group_name)
    if name_translations:
      group_symbol, atom_name = \
        name_translations.to_standard_name(group_symbol, atom_name)
    if (atom_name == None or seqnum == None or
	not self.atom_layouts.has_key(group_symbol)):
      return None
    atom_layouts = self.atom_layouts[group_symbol]
    if not atom_layouts.has_key(atom_name):
      return None

    ((x,y), color, (lx, ly)) = atom_layouts[atom_name]

    row = (seqnum - 1) / groups_per_row
    column = (seqnum - 1) % groups_per_row
    if row % 2 == 1:
      column = groups_per_row - 1 - column

    f = 1 + self.pad_factor
    xshift = column * self.cell_size[0] * f
    yshift = row * self.cell_size[1] * f
    x = x + xshift
    y = y + yshift
    lx = lx + xshift
    ly = ly + yshift

    return ((x,y), color, (lx, ly))

  # ---------------------------------------------------------------------------
  # Return (position, color, label_position)
  #
  def group_atom_list(self):

    group_atom_list = []
    seqnum = 0
    for g in pyutil.sort(self.atom_layouts.keys()):
      seqnum = seqnum + 1
      group_name = g + repr(seqnum)
      for atom_name in self.atom_layouts[g].keys():
        group_atom_list.append((group_name, atom_name))

    return group_atom_list

# -----------------------------------------------------------------------------
#
def template_from_graph(graph):

  layout = {}
  for v in graph.vertices:
    group_name, atom_name = v.group_atom
    group_symbol = group_name[0]
    if not layout.has_key(group_symbol):
      layout[group_symbol] = {}
    layout[group_symbol][atom_name] = v

  xsize = ysize = 0
  for g in layout.keys():
    (x1,y1,x2,y2) = vertex_region(layout[g].values())
    if x2 - x1 > xsize: xsize = x2 - x1
    if y2 - y1 > ysize: ysize = y2 - y1
  xsize = xsize
  ysize = ysize
  cell_size = (xsize, ysize)

  for g in layout.keys():
    (x1,y1,x2,y2) = vertex_region(layout[g].values())
    xoffset = .5 * (x1 + x2) - .5 * xsize
    yoffset = y2 - ysize
    for a in layout[g].keys():
      v = layout[g][a]
      (x,y) = v.position()
      x = x - xoffset
      y = y - yoffset
      (lx,ly) = v.label_position()
      lx = lx - xoffset
      ly = ly - yoffset
      layout[g][a] = ((x,y), v.color(), (lx,ly))

  sizes = {}
  for attr in ('vertex_font_height', 'group_font_height', 'line_font_height',
               'dot_radius', 'line_thickness', 'line_spacing'):
    sizes[attr] = getattr(graph.sizes, attr)

  pad_factor = 0
  
  return spin_graph_template(layout, cell_size, pad_factor, sizes)

# -----------------------------------------------------------------------------
#
def write_template(template, path):

  file = open(path, 'w')
  normalize_template(template)

  file.write('cell_size = (%d, %d)\n' % (int(template.cell_size[0]),
                                         int(template.cell_size[1])))

  file.write('sizes = {\n')
  for key, value in template.sizes.items():
    file.write('  \'%s\':%d,\n' % (key, int(value)))
  file.write('  }\n')

  file.write('layout = {\n')
  for g in pyutil.sort(template.atom_layouts.keys()):
    file.write('  %s: {\n' % repr(g))
    for a in pyutil.sort(template.atom_layouts[g].keys()):
      ((x,y), color, (lx,ly)) = template.atom_layouts[g][a]
      value = ((int(x),int(y)), color, (int(lx),int(ly)))
      file.write('\t%s:%s,\n' % (repr(a), repr(value)))
    file.write('\t},\n')
  file.write('  }\n')
  file.close()

# -----------------------------------------------------------------------------
# Scale template so cell size width = 300 pixels
#
def normalize_template(template):

  cx, cy = template.cell_size
  f = 300.0 / cx
  template.cell_size = (f*cx, f*cy)
  for g, alayouts in template.atom_layouts.items():
    for a, layout in alayouts.items():
      ((x,y), color, (lx,ly)) = layout
      template.atom_layouts[g][a] = ((f*x,f*y), color, (f*lx,f*ly))

  #
  # line thickness and line spacing don't get scaled
  #
  for key in ('vertex_font_height', 'group_font_height', 'line_font_height',
              'dot_radius'):
    template.sizes[key] = f * template.sizes[key]

# -----------------------------------------------------------------------------
#
def vertex_region(vlist):

  if vlist:
    (x,y) = vlist[0].position()
    (xmin, ymin, xmax, ymax) = (x, y, x, y)
    for v in vlist:
      (x,y) = v.position()
      if x < xmin: xmin = x
      elif x > xmax: xmax = x
      if y < ymin: ymin = y
      elif y > ymax: ymax = y
    return (xmin, ymin, xmax, ymax)
  return None

# -----------------------------------------------------------------------------
#
def show_spin_graph(session):
  sputil.the_dialog(spin_graph_dialog,session).show_window(1)
