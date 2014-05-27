# -----------------------------------------------------------------------------
# Show the mean and root mean square deviation of spectrum data values for
# a region dragged out with the mouse.
#

import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class region_rmsd_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    self.drag_notice = None
    
    tkutil.Dialog.__init__(self, session.tk, 'Region RMSD')

    self.top.columnconfigure(0, weight = 1)

    import Tkinter
    explain = ('Dragging a box calculates the mean and RMSD\n'
               'of data values for that spectrum region.')
    w = Tkinter.Label(self.top, text = explain, justify = 'left')
    w.grid(row = 0, column = 0, sticky = 'nw')

    r = Tkinter.Label(self.top, justify = 'left')
    r.grid(row = 1, column = 0, sticky = 'nw')
    self.result_label = r

    br = tkutil.button_row(self.top,
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'RegionRMSD')),
			   )
    br.frame.grid(row = 2, column = 0, sticky = 'nw')

    self.register_callback(1)
    self.top.bind('<Map>', lambda e, s=self: s.register_callback(1))
    self.top.bind('<Unmap>', lambda e, s=self: s.register_callback(0))

  # ---------------------------------------------------------------------------
  #
  def register_callback(self, register):

    if register:
      if self.drag_notice == None:
        self.drag_notice = self.session.notify_me('drag region',
                                                  self.region_selected_cb)
    else:
      if self.drag_notice:
        self.session.dont_notify_me(self.drag_notice)
        self.drag_notice = None

  # ---------------------------------------------------------------------------
  #
  def region_selected_cb(self, region):

    if self.is_window_destroyed():
      self.register_callback(0)
      return

    s = self.session.selected_spectrum()
    if s == None:
      self.result_label['text'] = 'No spectrum selected'
      return
    
    rmin, rmax = region
    ranges = map(lambda vmin, vmax: '%.4g-%.4g' % (vmin, vmax), rmin, rmax)
    import string
    rtext = '[ ' + string.join(ranges, ', ') + ' ]'

    mean, rmsd, samples = spectrum_region_statistics(s, region)
    
    msg = ('  Spectrum    %s\n' % s.name +
           '  Region      %s\n\n' % rtext +
           '  Mean  %12.5g\n' % mean +
           '  RMSD  %12.5g\n' % rmsd +
           '  Samples %10d\n' % samples)
    self.result_label['text'] = msg

# -----------------------------------------------------------------------------
#
def spectrum_region_statistics(spectrum, region):

  ppm_per_index = map(lambda w,s: float(w)/s,
                      spectrum.spectrum_width, spectrum.data_size)
  sum = 0
  sum2 = 0
  n = 0
  p = region[0]
  
  while p:
    h = spectrum.data_height(p)
    sum = sum + h
    sum2 = sum2 + h*h
    n = n + 1
    p = next_point(p, region, ppm_per_index)
  
  mean = sum / n
  import math
  rmsd = math.sqrt(sum2/n - mean * mean)
  
  return mean, rmsd, n
  
# -----------------------------------------------------------------------------
#
def next_point(p, region, step):

  dim = len(p)
  rmin, rmax = region
  next_p = list(p)
  for a in range(dim):
    next_p[a] = next_p[a] + step[a]
    if next_p[a] <= rmax[a]:
      return next_p
    else:
      next_p[a] = rmin[a]

  return None
  
# -----------------------------------------------------------------------------
#
def show_region_rmsd_dialog(session):

  sputil.the_dialog(region_rmsd_dialog,session).show_window(1)
