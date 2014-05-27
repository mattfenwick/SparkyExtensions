# -----------------------------------------------------------------------------
# Get amino acid or nucleic acid sequence for molecules
#
import string
import Tkinter

import atomnames
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
# Query user for sequence.
#
class sequence_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.molecule = None
    
    tkutil.Dialog.__init__(self, session.tk, 'Sequence Entry')

    se = self.sequence_entry(self.top)
    se.pack(side = 'top', anchor = 'w', fill = 'x', expand = 1)

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
                           ('Cancel', self.close_cb),
                           ('Help', sputil.help_cb(session, 'Sequence')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
      
  # ---------------------------------------------------------------------------
  #
  def sequence_entry(self, parent):

    f = Tkinter.Frame(parent)

    h = Tkinter.Label(f, text = 'Sequence')
    h.pack(side = 'top', anchor = 'w')
    self.header = h
    
    t = tkutil.scrolling_text(f)
    t.text['wrap'] = 'char'
    t.frame.pack(side = 'top', fill = 'x', expand = 1)
    self.sequence_text = t

    ff = tkutil.file_field(f, 'Sequence File', 'sequence')
    ff.frame.pack(side = 'top', anchor = 'w')
    self.file_field = ff

    fr = tkutil.entry_field(f, 'First residue number', '1')
    fr.frame.pack(side = 'top', anchor = 'w')
    self.first_residue = fr

    return f

  # ---------------------------------------------------------------------------
  #
  def read_sequence(self):

    path = self.file_field.get()
    if path:
      seqfile = open(path, 'r')
      seq = seqfile.read()
      seqfile.close()
      self.sequence_text.text.delete('0.0', 'end')
      self.sequence_text.text.insert('0.0', seq)
    aa_sequence = self.sequence_text.text.get('0.0', 'end')
    first_residue_number = pyutil.string_to_int(self.first_residue.variable.get(), 1)
    s = sequence(aa_sequence, first_residue_number)
    return s

  # ---------------------------------------------------------------------------
  #
  def ok_cb(self):

    seq = self.read_sequence()
    if self.molecule:
      set_molecule_sequence(self.molecule, seq)
    self.close_cb()

  # ---------------------------------------------------------------------------
  #
  def set_molecule(self, molecule):

    self.molecule = molecule
    
    if molecule and molecule.name:
      self.header['text'] = 'Sequence for %s molecule' % molecule.name
    else:
      self.header['text'] = 'Sequence'

    self.sequence_text.text.delete('0.0', 'end')

    if molecule:
      seq = has_molecule_sequence(molecule)
      if seq:
        self.sequence_text.text.insert('0.0', seq.one_letter_codes)

  # ---------------------------------------------------------------------------
  #
  def get_sequence(self, molecule):

    self.set_molecule(molecule)
    self.return_when_closed()

# -----------------------------------------------------------------------------
#
def has_molecule_sequence(molecule):

  if not hasattr(molecule, 'sequence'):
    s = molecule.saved_value('sequence')
    f = molecule.saved_value('first_residue_number')
    if s == None or f == None:
      molecule.sequence = None
    else:
      f = pyutil.string_to_int(f)
      molecule.sequence = sequence(s, f)
  return molecule.sequence

# -----------------------------------------------------------------------------
#
def set_molecule_sequence(molecule, seq):

  if seq:
    s = seq.one_letter_codes
    f = seq.first_residue_number
    molecule.save_value('sequence', s)
    molecule.save_value('first_residue_number', repr(f))
  molecule.sequence = seq

# -----------------------------------------------------------------------------
# Return the molecule sequence.  Query user if it is not known.
#
def molecule_sequence(molecule):

  seq = has_molecule_sequence(molecule)
  if seq == None:
    d = sputil.the_dialog(sequence_dialog, molecule.session)
    d.get_sequence(molecule)

  return has_molecule_sequence(molecule)
      
# -----------------------------------------------------------------------------
#
class sequence:

  def __init__(self, one_letter_codes, first_residue_number):

    olc = ''
    for symbol in one_letter_codes:
      if not symbol in string.whitespace:
        olc = olc + string.capitalize(symbol)
    self.one_letter_codes = olc
    
    n2s = self.number_to_symbol_table(olc, first_residue_number)
    self.number_to_symbol = n2s
                                                        
    self.first_residue_number = first_residue_number
    self.last_residue_number = first_residue_number + len(n2s) - 1

    self.resonances = self.create_resonances()

    nsa_to_res = {}
    for r in self.resonances:
      nsa_to_res[(r.number, r.symbol, r.atom_name)] = r
    self.nsa_to_resonance = nsa_to_res

    ga_to_res = {}
    for r in self.resonances:
      ga_to_res[r.group_atom] = r
    self.group_atom_to_resonance = ga_to_res
    
  # ---------------------------------------------------------------------------
  #
  def number_to_symbol_table(self, one_letter_codes, first_residue_number):

    ns_table = {}
    number = first_residue_number
    for symbol in one_letter_codes:
      ns_table[number] = symbol
      number = number + 1
    return ns_table

  # ---------------------------------------------------------------------------
  #
  def create_resonances(self):

    rlist = []
    for number, symbol in self.number_to_symbol.items():
      for atom_name in atomnames.protein_atoms_by_group[symbol]:
        r = resonance(number, symbol, atom_name)
        rlist.append(r)
    return rlist
    
  # ---------------------------------------------------------------------------
  #
  def resonance(self, number, symbol, atom_name):

    nsa = (number, symbol, atom_name)
    if self.nsa_to_resonance.has_key(nsa):
      return self.nsa_to_resonance[nsa]
    return None
    
  # ---------------------------------------------------------------------------
  #
  def peak_resonances(self, peak):

    res = []
    for r in peak.resonances():
      seq_r = self.resonance(r.group.number, r.group.symbol, r.atom.name)
      res.append(seq_r)
    return tuple(res)
  
# -----------------------------------------------------------------------------
#
class resonance:

  def __init__(self, number, symbol, atom_name):
    
    self.number = number
    self.symbol = symbol
    self.atom_name = atom_name
    self.group_name = symbol + repr(number)
    self.group_atom = (self.group_name, atom_name)

# -----------------------------------------------------------------------------
# Show molecule sequence dialog
#
def show_sequence_dialog(session):

  d = sputil.the_dialog(sequence_dialog, session)
  s = session.selected_spectrum()
  if s:
    d.set_molecule(s.molecule)
  d.show_window(1)
