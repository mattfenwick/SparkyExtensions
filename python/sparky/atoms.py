# -----------------------------------------------------------------------------
# Translate atom names.  Atom names are translated to standard names for
# matching the names you use in Sparky assignments with PDB file,
# Mardigras constraint file, and Corma intensity file atom names.  The
# standard names are also used when looking up attached heavy atoms,
# and laying out spin graphs based on standard templates.
#
# For each source of atom names, this code guesses the appropriate name
# translations to use.  The guesses can be examined and overridden and
# non-standard atom names with no translations can be inspected using the
# atom name translation dialog.
#
# Atom name translations and standard atom names are defined in
#
#	atomnames.py
#
# To add atom name translations to handle your naming conventions you copy
# atomnames.py to the Python directory in your home Sparky directory and
# edit it as described in that file.
#

import atomnames
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
def attached_heavy_atom(atom, molecule):

  heavy_atom_name = attached_heavy_atom_name(atom, molecule)
  if heavy_atom_name == None:
    return None

  return molecule.atom(atom.group.name, heavy_atom_name)

# -----------------------------------------------------------------------------
# Look up heavy atom attached to a proton of one of the 20 standard
# amino acids.  Atom names are based on BioMagResBank standard names.
#
def attached_heavy_atom_name(atom, molecule):

  name_translations = molecule_atom_name_translations(molecule)
  residue_symbol, proton_name = \
     name_translations.to_standard_name(atom.group.symbol, atom.name)

  aha = atomnames.standard_attached_heavy_atoms
  if (proton_name != None and
      aha.has_key(residue_symbol) and
      aha[residue_symbol].has_key(proton_name)):
    heavy_name = aha[residue_symbol][proton_name]
    residue_symbol, heavy_name = \
      name_translations.from_standard_name(residue_symbol, heavy_name)
    return heavy_name

  return None

# -----------------------------------------------------------------------------
#
class translations_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Atom Name Translations')

    self.trans_name = tkutil.option_menu(self.top, 'Atom set: ', ())
    self.trans_name.frame.pack(side = 'top', anchor = 'w')
    self.trans_name.add_callback(self.show_translation_cb)
      
    st = tkutil.scrolling_list(self.top, 'Select applicable translations', 5)
    st.frame.pack(side = 'top', anchor = 'w')
    st.listbox['selectmode'] = 'multiple'
    self.standard_trans = st
    
    for t in standard_translations():
      self.standard_trans.listbox.insert('end', t.name)

    self.bad_names = tkutil.scrolling_list(self.top, 'Non standard names', 5)
    self.bad_names.frame.pack(side = 'top', anchor = 'w',
                              fill = 'y', expand = 1)

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'AtomNameTrans')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  #
  def show_translation_cb(self, name):

    self.show_translations_used()
    self.show_bad_atoms()
    
  # ---------------------------------------------------------------------------
  # Select standard translations in use
  #
  def show_translations_used(self):

    t = self.translation_shown()
    listbox = self.standard_trans.listbox
    listbox.selection_clear(0, 'end')
    for std_trans in t.merged_translations:
      i = list(standard_translations()).index(std_trans)
      listbox.selection_set(i)

  # ---------------------------------------------------------------------------
  # Show atoms have non-standard names and no translation
  #
  def show_bad_atoms(self):

    t = self.translation_shown()
    self.bad_names.listbox.delete(0, 'end')
    for g, a in t.group_atoms:
      g, a = t.to_standard_name(g, a)
      if not is_standard_name(g, a):
        self.bad_names.listbox.insert('end', '%5s %5s' % (g, a))

  # ---------------------------------------------------------------------------
  #
  def translation_shown(self):

    if not hasattr(self.session, 'atom_name_translations'):
      return None
    ttable = self.session.atom_name_translations
    name = self.trans_name.get()
    for t in ttable:
      if t.name == name:
        return t
    return None
    
  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    t = self.translation_shown()
    if t:
      t.clear_translations()
      selected = self.standard_trans.selected_line_numbers()
      for i in selected:
        t.merge_translations(standard_translations()[i])
      self.show_bad_atoms()
    
  # ---------------------------------------------------------------------------
  # Translations used for Sparky atoms, PDB files, Mardigras files, ...
  # are kept in a session member list.
  #
  def add_translation(self, trans, group_atoms):

    if not hasattr(self.session, 'atom_name_translations'):
      self.session.atom_name_translations = []
    self.session.atom_name_translations.append(trans)
    self.trans_name.add_entry(trans.name)
    trans.group_atoms = group_atoms
    trans.group_atoms.sort()
    
  # ---------------------------------------------------------------------------
  #
  def get_molecule_translations(self):
  
    for m in self.session.project.molecule_list():
      molecule_atom_name_translations(m)
      
# -----------------------------------------------------------------------------
#
def is_standard_name(group_symbol, atom_name):
  return atomnames.standard_group_atom_table.has_key((group_symbol, atom_name))

# -----------------------------------------------------------------------------
#
class atom_name_translations:

  def __init__(self, name, gg_list = (), gaa_list = (), aa_list = ()):

    self.name = name
    self.clear_translations()
    self.merge_lists(gg_list, gaa_list, aa_list)

  # ---------------------------------------------------------------------------
  #
  def clear_translations(self):
    
    self.to_standard_group = {}
    self.to_standard_group_atom = {}
    self.to_standard_atom = {}

    self.from_standard_group = {}
    self.from_standard_group_atom = {}
    self.from_standard_atom = {}

    self.merged_translations = []
      
  # ---------------------------------------------------------------------------
  # Compose translations with existing ones.
  #
  def merge_lists(self, gg_list, gaa_list, aa_list):

    for g, gstd in gg_list:
      if self.from_standard_group.has_key(g):   # handle composition
        g1 = self.from_standard_group[g]
        del self.from_standard_group[g]
        g = g1
      self.to_standard_group[g] = gstd
      self.from_standard_group[gstd] = g

    for g, a, astd in gaa_list:
      if self.from_standard_group_atom.has_key((g, a)):   # handle composition
        a1 = self.from_standard_group_atom[(g, a)]
        del self.from_standard_group_atom[(g, a)]
        a = a1
      self.to_standard_group_atom[(g, a)] = astd
      self.from_standard_group_atom[(g, astd)] = a

    for a, astd in aa_list:
      if self.from_standard_atom.has_key(a):   # handle composition
        a1 = self.from_standard_atom[a]
        del self.from_standard_atom[a]
        a = a1
      self.to_standard_atom[a] = astd
      self.from_standard_atom[astd] = a
      
  # ---------------------------------------------------------------------------
  #
  def to_standard_name(self, group_symbol, atom_name):

    if self.to_standard_group.has_key(group_symbol):
      g = self.to_standard_group[group_symbol]
    else:
      g = group_symbol

    ga = (g, atom_name)
    if self.to_standard_group_atom.has_key(ga):
      a = self.to_standard_group_atom[ga]
    elif self.to_standard_atom.has_key(atom_name):
      a = self.to_standard_atom[atom_name]
    else:
      a = atom_name

    return (g, a)

  # ---------------------------------------------------------------------------
  #
  def from_standard_name(self, group_symbol, atom_name):

    ga = (group_symbol, atom_name)
    if self.from_standard_group_atom.has_key(ga):
      a = self.from_standard_group_atom[ga]
    elif self.from_standard_atom.has_key(atom_name):
      a = self.from_standard_atom[atom_name]
    else:
      a = atom_name

    g = group_symbol
    if self.from_standard_group.has_key(g):
      g = self.from_standard_group[g]

    return (g, a)

  # ---------------------------------------------------------------------------
  # Translate resonance atom name to this convention.
  #
  def resonance_number_atom(self, res):

    gsym = res.group.symbol
    aname = res.atom.name
    molecule = res.condition.molecule
    mol_names = molecule_atom_name_translations(molecule)
    gsym, aname = translate_group_atom(gsym, aname, mol_names, self)
    gnum = res.group.number
    return (gnum, aname)

  # ---------------------------------------------------------------------------
  #
  def merge_translations(self, trans):

    gaa_list = []
    for (g, a), astd in trans.to_standard_group_atom.items():
      gaa_list.append((g, a, astd))
      
    self.merge_lists(trans.to_standard_group.items(),
                     gaa_list,
                     trans.to_standard_atom.items())
    self.merged_translations.append(trans)
    
# -----------------------------------------------------------------------------
#
def translate_group_atom(group_symbol, atom_name, from_names, to_names):

  g, a = from_names.to_standard_name(group_symbol, atom_name)
  return to_names.from_standard_name(g, a)

# -----------------------------------------------------------------------------
#
def guess_atom_name_translations(session, name, group_atoms):

  t = atom_name_translations(name)

  galist = group_atoms
  for trans in standard_translations():
    if is_translation_applicable(trans, galist):
      t.merge_translations(trans)
      galist = map(lambda ga, f = trans.to_standard_name: apply(f, ga), galist)

  d = sputil.the_dialog(translations_dialog, session)
  d.add_translation(t, group_atoms)

  return t

# -----------------------------------------------------------------------------
#
def is_translation_applicable(trans, group_atoms):

  if hasattr(trans, 'is_translation_applicable'):
    return trans.is_translation_applicable(group_atoms)
  
  for g, a in group_atoms:
    if trans.to_standard_name(g, a) != (g, a):
      return 1
    elif trans.from_standard_name(g, a) != (g, a):
      return 0
  return 0

# -----------------------------------------------------------------------------
#
def molecule_atom_name_translations(molecule):

  if not hasattr(molecule, 'atom_name_translations'):
    group_atoms = {}
    for atom in molecule.atom_list():
      group_atoms[(atom.group.symbol, atom.name)] = 1
    t = guess_atom_name_translations(molecule.session,
                                     'Molecule ' + molecule.name,
                                     group_atoms.keys())
    molecule.atom_name_translations = t

  return molecule.atom_name_translations

# -----------------------------------------------------------------------------
#
standard_trans = None
def standard_translations():

  global standard_trans
  if standard_trans == None:
    standard_trans = []
    for convention in atomnames.translation_conventions:
      t = apply(atom_name_translations, convention[:4])
      if len(convention) == 5:
        t.is_translation_applicable = convention[4]
      standard_trans.append(t)
  return standard_trans
    
# -----------------------------------------------------------------------------
#
def show_translations_dialog(session):
  d = sputil.the_dialog(translations_dialog, session)
  d.get_molecule_translations()
  d.show_window(1)
  
