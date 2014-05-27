# -----------------------------------------------------------------------------
# Display information in response to atoms picked in Midas.
#
import Tkinter

import midas
import noesy
import pdb
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class midas_pick_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Pick Atoms')

    cb = tkutil.checkbutton(self.top, 'Show atom labels?', 0)
    self.show_label = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top, 'Show distances?', 0)
    self.show_distance = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top, 'Show peaks?', 0)
    self.show_peak = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top, 'Show assigned atoms?', 0)
    self.show_assigned = cb.variable
    cb.button.pack(side = 'top', anchor = 'w')
    cb.add_callback(pyutil.precompose(color_assigned_atoms, session))

    self.status_line = Tkinter.Label(self.top, anchor = 'nw')
    self.status_line.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'MidasPick')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    self.pick_cb = self.atom_pick_cb
    midas.process(self.session).add_atom_pick_callback(self.pick_cb)

  # -------------------------------------------------------------------------
  #
  def __del__(self):

    midas.process(self.session).remove_atom_pick_callback(self.pick_cb)

  # -------------------------------------------------------------------------
  #
  def atom_pick_cb(self, midas_atom_spec):

    if hasattr(self, 'first_atom') and self.first_atom:
      atom_spec_pair = (self.first_atom, midas_atom_spec)
      self.first_atom = None
    else:
      atom_spec_pair = None
      self.first_atom = midas_atom_spec

    if self.show_label.get():
      midas.process(self.session).send_command('label %s' % midas_atom_spec)

    if self.show_distance.get() and atom_spec_pair:
      cmd = 'distance %s %s' % atom_spec_pair
      midas.process(self.session).send_command(cmd)

    if self.show_peak.get() and atom_spec_pair:
      s = self.session.selected_spectrum()
      if s and noesy.is_noesy(s):
        mp = midas.process(self.session)
	model1, a1 = mp.midas_pick_to_pdb_atom(atom_spec_pair[0])
	model2, a2 = mp.midas_pick_to_pdb_atom(atom_spec_pair[1])
	if a1 and a2:
	  c = s.condition
	  r1 = model1.find_resonance(a1, c)
	  r2 = model2.find_resonance(a2, c)
	  if r1 and r2:
	    sputil.show_assignment((r1, r2), s)
	    self.status_line['text'] = ('Showing ' + r1.name + '-' + r2.name +
					' in spectrum ' + s.name)
	  else:
	    message = 'No resonance'
	    if not r1: message = message + ' ' + a1.full_name()
	    if not r2: message = message + ' ' + a2.full_name()
	    message = message + ' in spectrum ' + s.name
	    self.status_line['text'] = message

# ---------------------------------------------------------------------------
#
def color_assigned_atoms(session, onoff):

  if onoff:
    color = 'yellow'
  else:
    color = 'white'

  condition = sputil.selected_condition(session)
  if condition:
    for pdb_path in midas.process(session).open_models:
      pdb_atoms = assigned_pdb_atoms(session, pdb_path, condition)
      midas.process(session).color_pdb_atoms(pdb_atoms, color, pdb_path)

# -----------------------------------------------------------------------------
#
def assigned_pdb_atoms(session, pdb_path, condition):

  assigned = []
  model = pdb.model(session, pdb_path)
  for a in model.pdb_atoms:
    if model.find_resonance(a, condition):
      assigned.append(a)
  return assigned
	  
# -----------------------------------------------------------------------------
#
def show_atom_pick_dialog(session):
  sputil.the_dialog(midas_pick_dialog,session).show_window(1)
