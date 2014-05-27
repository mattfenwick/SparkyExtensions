# -----------------------------------------------------------------------------
# Show assignments as lines between atoms using Chimera.
# Assignments for selected peaks can be shown.
# Mardigras constraint violations can be shown.
#
import string
import Tkinter

import atoms
import mardigras
import noesy
import pdb
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class noeshow_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    self.pdb_path = None
    self.model = None
    self.pseudobond_group = None
    self.recenter_on_peak = 1
    self.chimera_atom_to_num_atom = {}
    self.num_atom_to_chimera_atom = {}
    self.chimera_atom_to_resonance = {}
    self.num_atom_pair_to_pseudobond = {}
    self.selected_atoms = []
    self.peak_selected_notice = None
    self.bond_selection_trigger = None
    self.chimera_quit_trigger = None
    self.chimera_running = 0

    tkutil.Dialog.__init__(self, session.tk, 'Chimera Model')

    self.pdb_file = tkutil.file_field(self.top, 'PDB File: ', 'pdb')
    self.pdb_file.frame.pack(side = 'top', anchor = 'w')

    colors = ('white', 'black', 'red', 'yellow',
              'green', 'cyan', 'blue', 'magenta')
    c = tkutil.option_menu(self.top, 'Color assigned atoms ',
                           colors, 'yellow')
    c.frame.pack(side = 'top', anchor = 'w')
    self.assigned_atom_color = c

    cb = tkutil.checkbutton(self.top,
                            'Selecting peak highlights assignment line?', 1)
    cb.button.pack(side = 'top', anchor = 'w')
    self.show_selected_peaks = cb

    cb = tkutil.checkbutton(self.top,
                            'Selecting assignment line recenters spectrum?', 1)
    cb.button.pack(side = 'top', anchor = 'w')
    self.show_selected_lines = cb

    cb = tkutil.checkbutton(self.top, 'Selecting atoms recenters spectrum?', 1)
    cb.button.pack(side = 'top', anchor = 'w')
    self.show_selected_atoms = cb

    c = tkutil.option_menu(self.top, 'Color lines for assignments ',
                           colors, 'blue')
    c.frame.pack(side = 'top', anchor = 'w')
    self.peak_line_color = c

    cb = tkutil.checkbutton(self.top, 'Show contraint violations?', 0)
    cb.button.pack(side = 'top', anchor = 'w')
    self.show_constraints = cb
    constraint_frame = Tkinter.Frame(self.top, borderwidth = 2,
                                     relief = 'sunken')
    cb.map_widget(constraint_frame)

    self.mardi_file = tkutil.file_field(constraint_frame,
					'Mardigras Constraint File: ',
					'mardigras')
    self.mardi_file.frame.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbuttons(constraint_frame, 'top', '',
                             'Show satisfied constraints?',
                             'Show violated constraints?')
    cb.frame.pack(side = 'top', anchor = 'w')
    self.show_satisfied, self.show_violated = cb.variables
    self.show_satisfied.set(0)

    color_frame = Tkinter.Frame(constraint_frame)
    color_frame.pack(side = 'top', anchor = 'w')
    h = Tkinter.Label(color_frame, text = 'Constraint line colors:')
    h.grid(row = 0, column = 0, columnspan = 2, sticky = 'w')

    self.constraint_colors = []
    row = 1
    for text, color in (('< 0.8 times lower bound', 'blue'),
                        ('0.8-1.0 times lower bound', 'cyan'),
                        ('satisfied constraint', 'green'),
                        ('1.0-1.2 times upper bound', 'magenta'),
                        ('> 1.2 times upper bound', 'red')):
      c = tkutil.option_menu(color_frame, '', colors, color)
      c.frame.grid(row = row, column = 0, sticky = 'e', padx = 10)
      label = Tkinter.Label(color_frame, text = text)
      label.grid(row = row, column = 1, sticky = 'w')
      row = row + 1
      self.constraint_colors.append(c)
    
    self.status_line = Tkinter.Label(self.top, anchor = 'nw',
                                     wraplength = '15c', justify = 'left')
    self.status_line.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Show', self.show_cb),
                           ('Erase', self.erase_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'Chimera')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # -------------------------------------------------------------------------
  #
  def show_cb(self):

    self.show()

  # -------------------------------------------------------------------------
  #
  def erase_cb(self):

    for line in self.num_atom_pair_to_pseudobond.values():
      self.pseudobond_group.deletePseudoBond(line)
    self.num_atom_pair_to_pseudobond = {}
    
  # -------------------------------------------------------------------------
  #
  def show(self):

    pdb_path = self.pdb_file.get()
    assigned_color = self.assigned_atom_color.get()
    
    self.chimera_open_model(pdb_path)
    self.color_assigned_atoms(assigned_color)

    if self.show_constraints.state():
      mardi_path = self.mardi_file.get()
      range_colors = map(lambda m: m.get(), self.constraint_colors)
      self.show_constraint_lines(mardi_path, pdb_path, range_colors)

  # -------------------------------------------------------------------------
  # Start chimera if not already started,
  # register peak and bond selection callbacks,
  # and return the chimera module
  #
  def chimera(self):

    if not self.chimera_running:
      start_chimera()
      import chimera
      ct = chimera.triggers
      self.bond_selection_trigger = \
        ct.addHandler('selection changed', self.chimera_selection_cb, None)
      self.chimera_quit_trigger = \
        ct.addHandler(chimera.APPQUIT, self.chimera_quit_cb, None)
      self.peak_selected_notice = \
        self.session.notify_me('selection changed', self.peak_selected_cb)
      self.chimera_running = 1

    import chimera
    return chimera

  # -------------------------------------------------------------------------
  #
  def chimera_quit_cb(self, trigger, user_data, trigger_data):

    if self.peak_selected_notice:
      self.session.dont_notify_me(self.peak_selected_notice)
    self.chimera_running = 0
    self.model_closed()

  # -------------------------------------------------------------------------
  #
  def model_closed(self):
    
    self.pdb_path = None
    self.model = None
    self.num_atom_pair_to_pseudobond = {}
    
  # -------------------------------------------------------------------------
  #
  def chimera_open_model(self, pdb_path):
      
    if pdb_path == self.pdb_path:
      return

    if self.model:
      chimera = self.chimera()
      chimera.openModels.close([self.model])
      self.model = None
      # I suspect closing the model also eliminates all constraint pseudobonds
      self.num_atom_pair_to_pseudobond = {}

    self.pdb_path = pdb_path
    chimera = self.chimera()
    models = chimera.openModels.open(pdb_path, type='PDB')
    self.model = models[0]    # assume just one molecule in the PDB file
    self.model.color = chimera.Color_lookup('gray')

    trans = pdb.model(self.session, pdb_path).atom_translations
    self.make_atom_tables(self.model.atoms, trans)

    if self.pseudobond_group == None:
      m = chimera.PseudoBondMgr_mgr()
      self.pseudobond_group = m.newPseudoBondGroup('NOESY constraints')
      del m

    chimera.openModels.add([self.pseudobond_group], sameAs = self.model)

  # -------------------------------------------------------------------------
  #
  def make_atom_tables(self, chimera_atoms, translations):

    ca2na = {}
    na2ca = {}
    for ca in chimera_atoms:
      na = self.chimera_num_atom(ca, translations)
      ca2na[ca] = na
      na2ca[na] = ca
    self.chimera_atom_to_num_atom = ca2na
    self.num_atom_to_chimera_atom = na2ca

    ca2r = {}
    condition = sputil.selected_condition(self.session)
    if condition:
      for r in condition.resonance_list():
	num_atom = self.resonance_num_atom(r)
	if na2ca.has_key(num_atom):
	  ca = na2ca[num_atom]
	  ca2r[ca] = r
    self.chimera_atom_to_resonance = ca2r
  
  # -------------------------------------------------------------------------
  #
  def color_assigned_atoms(self, colorname):

    chimera = self.chimera()
    color = chimera.Color_lookup(colorname)
    if color == None:
      return
    
    for ca, r in self.chimera_atom_to_resonance.items():
      if r.peak_count > 0:
	ca.color = color

  # -------------------------------------------------------------------------
  # Example :23@CA
  #
  def chimera_atom_name(self, chimera_atom):

    chimera = self.chimera()
    return chimera_atom.oslIdent(start=chimera.SelResidue)

  # -------------------------------------------------------------------------
  #
  def chimera_num_atom(self, chimera_atom, translations):
    
    cname = self.chimera_atom_name(chimera_atom)
    num_string, atom = string.split(cname[1:], '@')
    num = string.atoi(num_string)
    return standard_num_atom(num, atom, translations)

  # -------------------------------------------------------------------------
  #
  def resonance_num_atom(self, r):

    trans = atoms.molecule_atom_name_translations(r.condition.molecule)
    return standard_num_atom(r.group.number, r.atom.name, trans)
  
  # -------------------------------------------------------------------------
  # Show constraints colored by violation
  #
  def show_constraint_lines(self, mardi_path, pdb_path, range_colors):

    # unshow previous constraints

    if not mardi_path or not pdb_path:
      return

    show_satisfied = self.show_satisfied.get()
    show_violated = self.show_violated.get()
    if not (show_satisfied or show_violated):
      return
    
    pdb_model = pdb.model(self.session, pdb_path)
    mardi = mardigras.bounds(self.session, mardi_path)
    for (num_atom_1, num_atom_2), (rmin, rmax) in mardi.bounds_table.items():
      num_atom_1 = translate_atom_name(num_atom_1, mardi, pdb_model)
      num_atom_2 = translate_atom_name(num_atom_2, mardi, pdb_model)
      pdb_atom_1 = pdb_model.num_atom_to_pdb_atom(num_atom_1)
      pdb_atom_2 = pdb_model.num_atom_to_pdb_atom(num_atom_2)
      if pdb_atom_1 and pdb_atom_2:
        d = pyutil.distance(pdb_atom_1.xyz, pdb_atom_2.xyz)
        if ((show_satisfied and d >= rmin and d <= rmax) or
            (show_violated and (d < rmin or d > rmax))):
          if d < .8 * rmin:	color = range_colors[0]
          elif d < rmin:	color = range_colors[1]
          elif d <= rmax:	color = range_colors[2]
          elif d < 1.2 * rmax:	color = range_colors[3]
          else:			color = range_colors[4]
	  self.show_constraint(num_atom_1, num_atom_2, color)

  # -------------------------------------------------------------------------
  #
  def show_constraint(self, num_atom_1, num_atom_2, color):

    chimera = self.chimera()
    
    b = self.find_constraint(num_atom_1, num_atom_2)
    if b:
      b.color = chimera.Color_lookup(color)
      return b

    if (self.num_atom_to_chimera_atom.has_key(num_atom_1) and
	self.num_atom_to_chimera_atom.has_key(num_atom_2)):
      a1 = self.num_atom_to_chimera_atom[num_atom_1]
      a2 = self.num_atom_to_chimera_atom[num_atom_2]
      if a1 != a2:
        b = self.pseudobond_group.newPseudoBond(a1, a2)
        b.color = chimera.Color_lookup(color)
        b.display = 1
        b.halfbond = 0
        atom_pair = self.num_atom_pair(num_atom_1, num_atom_2)
        self.num_atom_pair_to_pseudobond[atom_pair] = b
        return b
    return None

  # -------------------------------------------------------------------------
  #
  def find_constraint(self, num_atom_1, num_atom_2):
    
    atom_pair = self.num_atom_pair(num_atom_1, num_atom_2)
    if self.num_atom_pair_to_pseudobond.has_key(atom_pair):
      return self.num_atom_pair_to_pseudobond[atom_pair]
    return None
    
  # ---------------------------------------------------------------------------
  #
  def num_atom_pair(self, num_atom_1, num_atom_2):

    pair = [num_atom_1, num_atom_2]
    pair.sort()
    return tuple(pair)
    
  # ---------------------------------------------------------------------------
  #
  def peak_selected_cb(self):

    if self.is_dialog_destroyed():
      return

    if self.show_selected_peaks.state():
      line_color = self.peak_line_color.get()
      peaks = self.session.selected_peaks()
      self.show_peak_lines(peaks, line_color)

  # -------------------------------------------------------------------------
  #
  def is_dialog_destroyed(self):

    if self.is_window_destroyed():
      if self.bond_selection_trigger != None:
        chimera = self.chimera()
        chimera.triggers.deleteHandler('selection changed',
                                       self.bond_selection_trigger)
        self.bond_selection_trigger = None
      if self.peak_selected_notice != None:
        self.session.dont_notify_me(self.peak_selected_notice)
        self.peak_selected_notice = None
      return 1
    return 0

  # -------------------------------------------------------------------------
  #
  def show_peak_lines(self, peaks, line_color):

    bonds = []
    missing = {}
    found = []
    for peak in peaks:
      rlist = peak.resonances()
      if len(rlist) > 2:
        rlist = filter(lambda r: r and r.atom.nucleus == '1H', rlist)
      if len(rlist) == 2:
        r1, r2 = rlist
        if r1 and r2:
          num_atom_1 = self.resonance_num_atom(r1)
          num_atom_2 = self.resonance_num_atom(r2)
          b = self.find_constraint(num_atom_1, num_atom_2)
          if b == None:
            b = self.show_constraint(num_atom_1, num_atom_2, line_color)
          if b == None:
            if not self.num_atom_to_chimera_atom.has_key(num_atom_1):
              missing[r1] = 1
            if not self.num_atom_to_chimera_atom.has_key(num_atom_2):
              missing[r2] = 1
          else:
            found.append(peak)
            bonds.append(b)

    message = ''
    if found:
      message = message + 'Highlighted '
      for peak in found:
        message = message + ' ' + peak.assignment
      message = message + '\n'
    if missing:
      message = message + 'No PDB atom for'
      for r in missing.keys():
        message = message + ' ' + r.name
      message = message + '\n'
    if message:
      self.status_line['text'] = message

    self.recenter_on_peak = 0
    chimera = self.chimera()
    chimera.selection.setCurrent(bonds)     # Set Chimera selection
    self.recenter_on_peak = 1
          
  # -------------------------------------------------------------------------
  #
  def chimera_selection_cb(self, trigger, user_data, selection):

    if self.is_dialog_destroyed():
      return

    if not self.chimera_running:
      return    # Sometimes get a callback after Chimera APPQUIT trigger

    if not self.recenter_on_peak:
      return

    if self.show_selected_lines.state():
      edge = self.selected_edge(selection)
      if edge:
        self.show_atom_pair_assignment(edge.atoms)

    if self.show_selected_atoms.state():
      atom = self.selected_atom(selection)
      if atom:
        self.atom_selected(atom)
        
  # -------------------------------------------------------------------------
  #
  def selected_edge(self, selection):

    chimera = self.chimera()
    edges = selection.edges()
    edges = filter(lambda e, c=chimera: isinstance(e, c.PseudoBond), edges)
    edges = filter(lambda e, c=self.pseudobond_group: e.pseudoBondGroup == c,
                   edges)
    if len(edges) == 1:
      return edges[0]
    return None
          
  # -------------------------------------------------------------------------
  #
  def show_atom_pair_assignment(self, atoms):

    s = self.session.selected_spectrum()
    if s == None or not noesy.is_noesy(s):
      self.status_line['text'] = ('Trying to recenter spectrum\n'
                                  'but NOESY spectrum not selected')
      return

    atom1, atom2 = atoms
    r1 = self.chimera_atom_resonance(atom1)
    r2 = self.chimera_atom_resonance(atom2)
    if r1 and r2:
      sputil.show_assignment((r1, r2), s)
      sputil.select_assignment((r1, r2), s)
      message = 'Showing %s-%s in spectrum %s' % (r1.name, r2.name, s.name)
      self.status_line['text'] = message
    else:
      message = 'No resonance'
      if not r1: message = message + ' ' + self.chimera_atom_name(atom1)
      if not r2: message = message + ' ' + self.chimera_atom_name(atom2)
      message = message + ' in spectrum ' + s.name
      self.status_line['text'] = message
        
  # -------------------------------------------------------------------------
  #
  def selected_atom(self, selection):

    chimera = self.chimera()
    atoms = selection.vertices()
    atoms = filter(lambda a, c=chimera: isinstance(a, c.Atom), atoms)
    if len(atoms) == 1:
      return atoms[0]
    return None
          
  # -------------------------------------------------------------------------
  #
  def atom_selected(self, atom):

    r = self.chimera_atom_resonance(atom)
    if r == None:
      self.status_line['text'] = 'No resonance ' + self.chimera_atom_name(atom)
      return

    self.selected_atoms.append(atom)
    if len(self.selected_atoms) == 1:
      self.status_line['text'] = 'Selected ' + self.chimera_atom_name(atom)
    else:
      self.show_atom_pair_assignment(self.selected_atoms)
      self.selected_atoms = []

  # -------------------------------------------------------------------------
  #
  def chimera_atom_resonance(self, chimera_atom):

    if self.chimera_atom_to_resonance.has_key(chimera_atom):
      return self.chimera_atom_to_resonance[chimera_atom]
    return None

# -----------------------------------------------------------------------------
# Translate a mardigras (residue #, atom name) to pdb file format
#
def translate_atom_name(num_atom, mardi, model):

  g, a = atoms.translate_group_atom(None, num_atom[1],
                                    mardi.atom_translations,
                                    model.atom_translations)
  return (num_atom[0], a)

# -----------------------------------------------------------------------------
# Apply atom name translations.
#
def standard_num_atom(num, atom, translations):

  g, a = translations.to_standard_name(None, atom)
  return (num, a)

# -----------------------------------------------------------------------------
#
start_count = 0
def start_chimera():

  setup_chimera()

  import chimeraInit
  try:
    chimeraInit.init(argv = [], eventloop = 0, exitonquit = 0)
  except SystemExit, value:
    # Chimera raises SystemExit sometimes when it can't start.
    # Have to catch it here or Sparky will exit.
    import traceback
    traceback.print_exc()
    raise EnvironmentError, 'Chimera failed to start'
  except:
    global start_count
    if start_count == 1:
      warning = '''
Chimera can only be started once per Sparky session.
This is a limitation in all versions of Chimera released so far
(through March 2004).

'''
      import sys
      sys.stdout.write(warning)
    raise

  start_count += 1

# -----------------------------------------------------------------------------
# Do initial Chimera setup that only needs to be done once even if Chimera
# is started and quit several times.
#
chimera_setup = 0
def setup_chimera():

  global chimera_setup
  if chimera_setup:
    return
  
  import os
  if not os.environ.has_key('CHIMERA'):
    raise EnvironmentError, 'CHIMERA environment variable not set.'
  
  chimera_path = os.environ['CHIMERA']
  import os.path
  if not os.path.exists(chimera_path):
    raise EnvironmentError, 'CHIMERA environment variable gives non-existent directory ' + chimera_path

  chimera_python = os.path.join(chimera_path, 'share')
  chimera_lib = os.path.join(chimera_path, 'lib')
  import sys
  if sys.platform == 'win32':
    chimera_site_packages = os.path.join(chimera_path, 'bin', 'Lib',
                                         'site-packages')
  else:
    chimera_site_packages = os.path.join(chimera_path, 'lib', 'python2.4',
                                         'site-packages')
  
  sys.path.insert(0, chimera_site_packages)
  sys.path.insert(0, chimera_python)
  sys.path.insert(0, chimera_lib)

# -----------------------------------------------------------------------------
#
def show_chimera_dialog(session):
  sputil.the_dialog(noeshow_dialog,session).show_window(1)
