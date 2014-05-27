# -----------------------------------------------------------------------------
# Center a specified view using the current mouse position.
# Center a specified view on a selected peak.
#
import Tkinter

import pythonshell
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class view_center_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    self.view_to_center = None
    self.selection_notice = None
    
    tkutil.Dialog.__init__(self, session.tk, 'View Center')

    explain = ('Specify a view window to be centered\n' +
               'by the cm or cp commands.  The cm command\n' +
               'centers the view at the point under the mouse\n'
               'when the command is invoked in any window.\n' +
               'The cp command centers the view on the selected\n' +
               'peak.')
    w = Tkinter.Label(self.top, text = explain, justify = 'left')
    w.pack(side = 'top', anchor = 'w')

    add_command = pythonshell.add_command
    add_command('cm', '', 'centerview', 'center_view_on_mouse', session)
    add_command('cp', '', 'centerview', 'center_view_on_peak', session)

    self.center_view = sputil.view_menu(session, self.top, 'View to center: ')
    self.center_view.frame.pack(side = 'top', anchor = 'w')

    ps = tkutil.checkbutton(self.top, 'Center when peak selected?', 0)
    ps.button.pack(side = 'top', anchor = 'w')
    self.peak_select = ps

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'CenterViews')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  #
  def apply_cb(self):

    self.view_to_center = self.center_view.view()

    if self.peak_select.state():
      if self.selection_notice == None:
        self.selection_notice = self.session.notify_me('selection changed',
                                                       self.peak_selected_cb)
    elif self.selection_notice:
      self.session.dont_notify_me(self.selection_notice)
      self.selection_notice = None
    
  # ---------------------------------------------------------------------------
  #
  def peak_selected_cb(self):

    if self.is_window_destroyed():
      if self.selection_notice:
        self.session.dont_notify_me(self.selection_notice)
        self.selection_notice = None
      return
    self.center_on_peak()
      
  # ---------------------------------------------------------------------------
  #
  def center_on_mouse(self):

    pointer_view = self.session.selected_view()
    if pointer_view:
      p = pointer_view.pointer_position
      if p:
        self.center_on_point(pointer_view.spectrum, p)
    
  # ---------------------------------------------------------------------------
  # Center the view specified by the option menu on the selected peak.
  #
  def center_on_peak(self):

    peak = sputil.selected_peak(self.session)
    if peak:
      self.center_on_point(peak.spectrum, peak.frequency)
    
  # ---------------------------------------------------------------------------
  #
  def center_on_point(self, spectrum, point):

    view_to_center = self.view_to_center
    if view_to_center:
      center = self.map_point(spectrum, point,
                              view_to_center.spectrum, view_to_center.center)
      center = sputil.alias_onto_spectrum(center, view_to_center.spectrum)
      view_to_center.center = center
    
  # ---------------------------------------------------------------------------
  # Map a point from one spectrum to another matching nucleus types.
  # A default destination point is specified and components are only
  # changed if the nucleus type is unique in the source spectrum or
  # the same axis number of the source spectrum has the correct nucleus.
  #
  def map_point(self, from_spectrum, from_p, to_spectrum, to_p_default):

    from_nuclei = from_spectrum.nuclei
    to_nuclei = to_spectrum.nuclei
    to_p = list(to_p_default)
    for to_a in range(to_spectrum.dimension):
      matching_axes = pyutil.element_positions(to_nuclei[to_a], from_nuclei)
      if matching_axes:
        if len(matching_axes) == 1:
          from_a = matching_axes[0]
          to_p[to_a] = from_p[from_a]
        elif (to_a < from_spectrum.dimension and
              from_nuclei[to_a] == to_nuclei[to_a]):
          from_a = to_a
          to_p[to_a] = from_p[from_a]
    return to_p
    
# -----------------------------------------------------------------------------
#
def center_view_on_mouse(session):
  sputil.the_dialog(view_center_dialog,session).center_on_mouse()
def center_view_on_peak(session):
  sputil.the_dialog(view_center_dialog,session).center_on_peak()
def center_view_setup(session):
  sputil.the_dialog(view_center_dialog,session).show_window(1)

