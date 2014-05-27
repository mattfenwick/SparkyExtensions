# -----------------------------------------------------------------------------
# Show Mardigras constraint violations using Midas
#

import atoms
import mardigras
import midas
import pdb
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class midas_constraint_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'View Constraints')

    self.pdb_file = tkutil.file_field(self.top, 'PDB File: ', 'pdb')
    self.pdb_file.frame.pack(side = 'top', anchor = 'w')

    self.mardi_file = tkutil.file_field(self.top,
					'Mardigras Constraint File: ',
					'mardigras')
    self.mardi_file.frame.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top, 'Show satisfied constraints?', 0)
    self.satisfied = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top, 'Show violated constraints?', 1)
    self.violated = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Show', self.show_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session,
                                                   'MidasConstraints')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # -------------------------------------------------------------------------
  #
  def show_cb(self):

    try:
      self.show()
    except midas.BrokenPipe:
      midas.new_midas_process(self.session)
      self.show()

  # -------------------------------------------------------------------------
  #
  def show(self):
      
    pdb_path = self.pdb_file.get()
    midas.process(self.session).show_pdb_models([pdb_path])
    mardi_path = self.mardi_file.get()
    self.show_constraints(mardi_path, pdb_path)

  # -------------------------------------------------------------------------
  # Show constraints colored by violation
  #
  def show_constraints(self, mardi_path, pdb_path):

    midas.process(self.session).unshow_objects('constraints')

    if not mardi_path or not pdb_path:
      return

    show_satisfied = self.satisfied.get()
    show_violated = self.violated.get()
    if not (show_satisfied or show_violated):
      return
    
    lines = midas.midas_object_file('constraints')
    model = pdb.model(self.session, pdb_path)
    mardi = mardigras.bounds(self.session, mardi_path)
    for (num_atom_1, num_atom_2), (rmin, rmax) in mardi.bounds_table.items():
      num_atom_1 = translate_atom_name(num_atom_1, mardi, model)
      num_atom_2 = translate_atom_name(num_atom_2, mardi, model)
      pdb_atom_1 = model.num_atom_to_pdb_atom(num_atom_1)
      pdb_atom_2 = model.num_atom_to_pdb_atom(num_atom_2)
      if pdb_atom_1 and pdb_atom_2:
        d = pyutil.distance(pdb_atom_1.xyz, pdb_atom_2.xyz)
        if ((show_satisfied and d >= rmin and d <= rmax) or
            (show_violated and (d < rmin or d > rmax))):
          if d < .8 * rmin:	color = 'blue'
          elif d < rmin:	color = 'cyan'
          elif d <= rmax:	color = 'green'
          elif d < 1.2 * rmax:	color = 'magenta'
          else:			color = 'red'
          pdb_atom_1 = model.num_atom_to_pdb_atom(num_atom_1)
          pdb_atom_2 = model.num_atom_to_pdb_atom(num_atom_2)
	  lines.add_line(pdb_atom_1.xyz, pdb_atom_2.xyz, color)

    lines.show_objects(self.session)

# -----------------------------------------------------------------------------
# Translate a mardigras (residue #, atom name) to pdb file format
#
def translate_atom_name(num_atom, mardi, model):

  g, a = atoms.translate_group_atom(None, num_atom[1],
                                    mardi.atom_translations,
                                    model.atom_translations)
  return (num_atom[0], a)
  
# -----------------------------------------------------------------------------
#
def show_constraint_dialog(session):
  sputil.the_dialog(midas_constraint_dialog,session).show_window(1)
