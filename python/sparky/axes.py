# -----------------------------------------------------------------------------
# Routines that related to spectrum axes.
#
import Tkinter

import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
def unique_nucleus_axis(spectrum, nucleus):

  axis = None
  for a in range(spectrum.dimension):
    if spectrum.nuclei[a] == nucleus:
      if axis == None:
        axis = a
      else:
        return None
  return axis

# -----------------------------------------------------------------------------
#
def second_nucleus_axis(spectrum, nucleus, not_this_axis):

  for a in range(spectrum.dimension):
    if a != not_this_axis and spectrum.nuclei[a] == nucleus:
      return a
  return None

# ----------------------------------------------------------------------------
#
def proton_axes(spectrum):

  axes = []
  nuclei = spectrum.nuclei
  for a in range(spectrum.dimension):
    if nuclei[a] == '1H':
      axes.append(a)
  return axes

# ----------------------------------------------------------------------------
#
def heavy_atom_axes(spectrum):

  axes = []
  nuclei = spectrum.nuclei
  for a in range(spectrum.dimension):
    if nuclei[a] != '1H':
      axes.append(a)
  return axes

# ----------------------------------------------------------------------------
# Return axes for hnca or hnha type experiments (aH, aN, aX)
#
def amide_axes(spectrum):

  if hasattr(spectrum, 'hnx_axes'):
    return spectrum.hnx_axes
  
  if spectrum.dimension < 3:
    return None
  
  aN = unique_nucleus_axis(spectrum, '15N')
  if aN == None:
    return None
  
  aH = unique_nucleus_axis(spectrum, '1H')
  if aH == None:
    aH = attached_proton_axis(spectrum, aN)
    if aH == None:
      return None
    
  aX = 3 - aH - aN

  spectrum.hnx_axes = (aH, aN, aX)
  
  return spectrum.hnx_axes

# ----------------------------------------------------------------------------
# An option menu of spectrum axes
#
class axis_menu(tkutil.option_menu):

  def __init__(self, parent, spectrum, nucleus = None, allow_no_choice = 0):

    self.spectrum = spectrum
    axes = []
    for a in range(spectrum.dimension):
      axis_nucleus = spectrum.nuclei[a]
      if nucleus == None or axis_nucleus == nucleus: 
        axes.append(self.axis_text(a))
    if allow_no_choice:
      axes = [''] + axes

    tkutil.option_menu.__init__(self, parent, '', axes)

  # -------------------------------------------------------------------------
  #
  def axis_text(self, axis):

    return 'w%d %s' % (axis+1, self.spectrum.nuclei[axis])

  # -------------------------------------------------------------------------
  #
  def set_axis(self, axis):

    self.set(self.axis_text(axis))
    
  # -------------------------------------------------------------------------
  # Parse wN of axis label to return axis number
  #
  def chosen_axis(self):

    axis_text = self.get()
    if len(axis_text) >= 2:
      anum = pyutil.string_to_int(axis_text[1])
      if anum != None:
        axis = anum - 1
        return axis
    return None

# ----------------------------------------------------------------------------
# An option menu of all possible spectrum axis orders
#
class axis_order_menu(tkutil.option_menu):

  def __init__(self, parent, nuclei, initial_order):

    self.nuclei = nuclei

    unique_nuclei = len(pyutil.unique_elements(self.nuclei))
    self.are_nuclei_unique = (len(self.nuclei) == unique_nuclei)
    
    orders = []
    for order in self.permutations(range(len(nuclei))):
      orders.append(self.order_text(order))

    if initial_order:
      initial = self.order_text(initial_order)
    else:
      initial = None
      
    tkutil.option_menu.__init__(self, parent, '', orders, initial)

  # -------------------------------------------------------------------------
  #
  def order_text(self, order):

    ntext = ''
    atext = ''
    for axis in order:
      ntext = ntext + self.nuclei[axis][-1]
      atext = atext + '%d' % (axis + 1)

    if self.are_nuclei_unique:
      return ntext
    
    return ntext + ' ' + atext

  # -------------------------------------------------------------------------
  #
  def axis_order(self):

    order_text = self.get()
    for order in self.permutations(range(len(self.nuclei))):
      if order_text == self.order_text(order):
        return order
    return None

  # -------------------------------------------------------------------------
  #
  def set_axis_order(self, order):

    self.set(self.order_text(order))
    
  # -------------------------------------------------------------------------
  #
  def permutations(self, set):

    if len(set) <= 1:
      return (tuple(set),)

    perms = []
    plist = self.permutations(set[1:])
    e = set[0]
    for i in range(len(set)):
      for p in plist:
        perms.append(p[:i] + (e,) + p[i:])
    return tuple(perms)
    
  # -------------------------------------------------------------------------
  #
  def restrict_menu_permutations(self, nuclei):

    orig_order = self.axis_order()
    self.remove_all_entries()
    allowed_orders = []
    for order in self.permutations(range(len(nuclei))):
      if self.is_allowed_order(order, nuclei):
        allowed_orders.append(order)
        text = self.order_text(order)
        self.add_entry(text)

    if orig_order and self.is_allowed_order(orig_order, nuclei):
      self.set(self.order_text(orig_order))
    elif allowed_orders:
      self.set(self.order_text(allowed_orders[0]))
    else:
      self.set('')
    
  # -------------------------------------------------------------------------
  #
  def is_allowed_order(self, order, nuclei):

    if len(nuclei) != len(self.nuclei):
      return 0
    
    for a in range(len(order)):
      if self.nuclei[order[a]] != nuclei[a]:
        return 0
    return 1
      
# ----------------------------------------------------------------------------
#
class axis_order_column:

  def __init__(self, parent, heading, column, spectra):

    lbl = Tkinter.Label(parent, text = heading)
    lbl.grid(row = 0, column = column)

    self.spectrum_to_menu = {}
    row = 0
    for spectrum in spectra:
      row = row + 1
      aom = axis_order_menu(parent, spectrum.nuclei, initial_order = None)
      aom.frame.grid(row = row, column = column, sticky = 'w')
      self.spectrum_to_menu[spectrum] = aom
    
# -----------------------------------------------------------------------------
#
def has_attached_proton_axis(spectrum, heavy_axis):

  key = 'w%d_attached_proton_axis' % (heavy_axis + 1)
  a = spectrum.saved_value(key)
  if a:
    a = pyutil.string_to_int(a)
  return a

# -----------------------------------------------------------------------------
#
def set_attached_proton_axis(spectrum, heavy_axis, proton_axis):

  key = 'w%d_attached_proton_axis' % (heavy_axis + 1)
  spectrum.save_value(key, repr(proton_axis))

# -----------------------------------------------------------------------------
#
def attached_proton_axis(spectrum, heavy_axis):

  a = has_attached_proton_axis(spectrum, heavy_axis)
  if a == None:
    d = sputil.the_dialog(attached_proton_dialog, spectrum.session)
    d.get_attached_axis(spectrum, heavy_axis)
    
  return has_attached_proton_axis(spectrum, heavy_axis)

# -----------------------------------------------------------------------------
#
class attached_proton_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.spectrum = None
    self.heavy_axis = None
    
    tkutil.Dialog.__init__(self, session.tk, 'Attached Proton')

    am = tkutil.option_menu(self.top, 'Attached proton axis: ', ())
    am.frame.pack(side = 'top')
    self.axis_menu = am

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
                           ('Cancel', self.close_cb),
                           ('Help', sputil.help_cb(session, 'LabelledAxis')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def ok_cb(self):

    axis_name = self.axis_menu.get()
    axis_number = {'w1':0, 'w2':1, 'w3':2, 'w4':3}
    if axis_number.has_key(axis_name):
      attached_axis = axis_number[axis_name]
      if self.spectrum and self.heavy_axis != None:
        set_attached_proton_axis(self.spectrum, self.heavy_axis, attached_axis)
    self.close_cb()

  # ---------------------------------------------------------------------------
  #
  def set_spectrum_heavy_axis(self, spectrum, heavy_axis):

    self.spectrum = spectrum
    self.heavy_axis = heavy_axis
    
    request = ('Attached proton axis for w%d %s of %s: '
               % (heavy_axis+1, spectrum.nuclei[heavy_axis], spectrum.name))
    self.axis_menu.label['text'] = request

    initial = has_attached_proton_axis(spectrum, heavy_axis)
    self.axis_menu.remove_all_entries()
    for a in range(spectrum.dimension):
      if spectrum.nuclei[a] == '1H':
        axis_name = 'w%d' % (a+1)
        self.axis_menu.add_entry(axis_name)
        if a == initial or initial == None:
          self.axis_menu.set(axis_name)

  # ---------------------------------------------------------------------------
  #
  def get_attached_axis(self, spectrum, heavy_axis):

    self.set_spectrum_heavy_axis(spectrum, heavy_axis)
    self.show_window(1)
    self.return_when_closed()

# -----------------------------------------------------------------------------
#
def show_attached_axis_dialog(session):

  d = sputil.the_dialog(attached_proton_dialog, session)
  spectrum = session.selected_spectrum()
  if spectrum:
    axes = heavy_atom_axes(spectrum)
    if len(axes) == 1:
      d.set_spectrum_heavy_axis(spectrum, axes[0])
  d.show_window(1)
