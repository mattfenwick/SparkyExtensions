# -----------------------------------------------------------------------------
# Read PDB file atom coordinates
#
import os
import string

import atomnames
import atoms
import noesy
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
# Cache PDB Model objects
#
def model(session, pdb_path, stoppable = tkutil.Not_Stoppable()):

  if not hasattr(session, 'model_table'):
    session.model_table = {}
  t = session.model_table

  if not t.has_key(pdb_path):
    try:
      t[pdb_path] = pdb_model(session, pdb_path, stoppable)
    except IOError:
      return None

  return t[pdb_path]

# -----------------------------------------------------------------------------
#
class pdb_model:

  def __init__(self, session, pdb_path, stoppable = tkutil.Not_Stoppable()):

    self.pdb_path = pdb_path
    self.pdb_atoms = self.read_pdb_atoms(pdb_path, stoppable)

    t = {}
    for a in self.pdb_atoms:
      t[(a.residue_number, a.atom_name)] = a
    self.atom_table = t

    gatable = {}
    for a in self.pdb_atoms:
      gatable[(a.residue_symbol, a.atom_name)] = 1
    self.atom_translations = \
      atoms.guess_atom_name_translations(session, pdb_path, gatable.keys())
    
  # ---------------------------------------------------------------------------
  #
  def read_pdb_atoms(self, pdb_path, stoppable):

    pdb_file = open(pdb_path, 'r')
    lines = pdb_file.readlines()
    pdb_file.close()

    atoms = []
    stoppable.stoppable_loop('reading ' + os.path.basename(pdb_path), 200)
    for line in lines:
      stoppable.check_for_stop()
      if line[:4] == 'ATOM':
	atoms.append(pdb_atom(line))

    return atoms

  # ---------------------------------------------------------------------------
  # Calculate distance between atoms.
  #
  def noesy_distance(self, peak):

    if peak.is_assigned:
      res = noesy.proton_resonances(peak)
      if res != None and len(res) == 2:
        mol = peak.spectrum.molecule
	return self.minimum_distance(res[0].atom, res[1].atom, mol)
    return None

  # ---------------------------------------------------------------------------
  # Calculate distance between atoms or pseudo atoms.  For pseudo atoms the
  # minimum distance is returned.
  #
  def minimum_distance(self, atom_1, atom_2, molecule):

    pdb_atoms_1 = self.atom_to_pdb_atoms(atom_1, molecule)
    pdb_atoms_2 = self.atom_to_pdb_atoms(atom_2, molecule)

    min_dist = None
    for pdb_atom_1 in pdb_atoms_1:
      for pdb_atom_2 in pdb_atoms_2:
        d = pyutil.distance(pdb_atom_1.xyz, pdb_atom_2.xyz)
        if min_dist == None or d < min_dist:
          min_dist = d

    return min_dist

  # ---------------------------------------------------------------------------
  # Convert a Sparky atom to one or more PDB atoms.  Pseudo atoms produce a
  # list of more than one pdb atom.
  #
  def atom_to_pdb_atoms(self, atom, molecule):

    num = atom.group.number
    translate = atoms.molecule_atom_name_translations(molecule)
    residue_symbol, atom_name = \
                    translate.to_standard_name(atom.group.symbol, atom.name)

    atype = (residue_symbol, atom_name)
    pseudo = atomnames.standard_pseudo_atoms
    if pseudo.has_key(atype):
      atom_names = pseudo[atype]
    else:
      atom_names = (atom_name,)

    atable = self.atom_table
    pdb_atom_list = []
    for aname in atom_names:
      pdb_sym, pdb_aname = \
               self.atom_translations.from_standard_name(residue_symbol, aname)
      num_atom = (num, pdb_aname)
      if atable.has_key(num_atom):
        pdb_atom_list.append(atable[num_atom])

    return pdb_atom_list

  # ---------------------------------------------------------------------------
  # This doesn't do any atom name translation.
  #
  def num_atom_to_pdb_atom(self, num_atom):

    if self.atom_table.has_key(num_atom):
      return self.atom_table[num_atom]
    return None

  # ---------------------------------------------------------------------------
  #
  def find_resonance(self, pdb_atom, condition):

    mol_names = atoms.molecule_atom_name_translations(condition.molecule)
    gsym, aname = atoms.translate_group_atom(pdb_atom.residue_symbol,
                                             pdb_atom.atom_name,
                                             self.atom_translations, mol_names)
    gnum = pdb_atom.residue_number
    gname = gsym + str(gnum)
    return condition.find_resonance(gname, aname)

# -----------------------------------------------------------------------------
#
class pdb_atom:

  def __init__(self, line):

    self.atom_name = string.strip(line[12:16])
    self.residue_symbol = string.strip(line[17:20])
    self.residue_number = string.atoi(line[22:26])

    self.chain_id = line[21:22]
    self.xyz = (string.atof(line[30:38]),
		string.atof(line[38:46]),
		string.atof(line[46:54]))

  # ---------------------------------------------------------------------------
  #
  def full_name(self):
    return self.residue_symbol + str(self.residue_number) + self.atom_name

# -----------------------------------------------------------------------------
# Show Sparky resonances without corresponding pdb atoms
#
class pdb_atom_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    tkutil.Dialog.__init__(self, session.tk, 'PDB Atom Name Check')

    cm = sputil.condition_menu(session, self.top, 'Condition: ')
    cm.frame.pack(side = 'top', anchor = 'w')
    self.condition_menu = cm

    pf = tkutil.file_field(self.top, 'PDB File: ', 'pdb')
    pf.frame.pack(side = 'top', anchor = 'w')
    self.pdb_path = pf

    al = tkutil.scrolling_list(self.top, 'Resonances w/o PDB atoms', 5)
    al.frame.pack(fill = 'both', expand = 1)
    self.atom_list = al

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'PDBNames')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    pdb_path = self.pdb_path.get()
    cond = self.condition_menu.condition()
    mod = model(self.session, pdb_path)
    if mod and cond:
      mol = cond.molecule
      self.atom_list.clear()
      alist = []
      for r in cond.resonance_list():
        a = r.atom
        if not mod.atom_to_pdb_atoms(a, mol):
          alist.append(a)
      alist.sort(sputil.compare_atoms)
      for a in alist:
        line = '%5s %5s' % (a.group.name, a.name)
        self.atom_list.append(line)
      heading = '%d resonances w/o PDB atoms' % len(alist)
      self.atom_list.heading['text'] = heading

    
# -----------------------------------------------------------------------------
#
def show_pdb_atom_dialog(session):
  d = sputil.the_dialog(pdb_atom_dialog, session)
  d.show_window(1)
