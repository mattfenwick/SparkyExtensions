# -----------------------------------------------------------------------------
# Pick peaks of a spectrum in regions near peaks of a reference spectrum.
#
import string
import Tkinter

import axes
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class restricted_pick_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Restricted Peak Pick')
    
    m = sputil.view_menu(session, self.top, 'Find peaks in ')
    m.frame.pack(side = 'top', anchor = 'w')
    m.add_callback(self.chose_spectrum_cb)
    self.pick_menu = m

    m = sputil.spectrum_menu(session, self.top, 'Using peaks in ')
    m.frame.pack(side = 'top', anchor = 'w')
    m.add_callback(self.chose_spectrum_cb)
    self.ref_menu = m

    b = tkutil.checkbutton(self.top, 'Use selected peaks only?', 0)
    b.button.pack(side = 'top', anchor = 'w')
    self.selected_only = b

    lbl= Tkinter.Label(self.top, text = 'Axis match tolerances (ppm)')
    lbl.pack(side = 'top', anchor = 'w')
    self.axis_table_heading = lbl
    
    f = Tkinter.Frame(self.top)
    f.pack(side = 'top', anchor = 'w')
    self.axis_table = f
    self.range_entries = []
    
    self.setup_axis_table()

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Pick peaks', self.pick_cb),
                           ('Select peaks', self.select_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'RestrictedPick')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

  # ---------------------------------------------------------------------------
  #
  def chose_spectrum_cb(self, name):

    self.setup_axis_table()
    
  # ---------------------------------------------------------------------------
  #
  def setup_axis_table(self):

    for w in self.axis_table.grid_slaves():
      w.destroy()

    ref_spectrum = self.ref_menu.spectrum()
    pick_view = self.pick_menu.view()
    if ref_spectrum == None or pick_view == None:
      return

    heading = ('\nAxis match tolerances (ppm)\n%s \ %s' % (ref_spectrum.name,
                                                           pick_view.name))
    self.axis_table_heading['text'] = heading

    column = 1
    pick_nuclei = pick_view.spectrum.nuclei
    for nucleus in pick_nuclei:
      lbl= Tkinter.Label(self.axis_table, text = nucleus)
      lbl.grid(row = 1, column = column)
      column = column + 1
    
    row = 2
    ref_nuclei = ref_spectrum.nuclei
    for nucleus in ref_nuclei:
      lbl= Tkinter.Label(self.axis_table, text = nucleus)
      lbl.grid(row = row, column = 0, sticky = 'w')
      row = row + 1

    self.range_entries = []
    for r in range(len(ref_nuclei)):
      for p in range(len(pick_nuclei)):
        if ref_nuclei[r] == pick_nuclei[p]:
          if ref_nuclei[r] == '1H':
            rtext = '.02'
          else:
            rtext = '.2'
          e = tkutil.entry_field(self.axis_table, '', rtext, 4)
          e.frame.grid(row = r + 2, column = p + 1, sticky = 'w')
          self.range_entries.append((r,p,e))
  
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    settings = pyutil.generic_class()

    settings.ref_spectrum = self.ref_menu.spectrum()
    if settings.ref_spectrum == None:
      self.progress_report('Spectrum %s not found' % self.ref_menu.get())
      return None

    settings.pick_view = self.pick_menu.view()
    if settings.pick_view == None:
      self.progress_report('View %s not found' % self.pick_menu.get())
      return None

    settings.selected_only = self.selected_only.state()

    settings.ranges = []
    for ref_axis, pick_axis, ef in self.range_entries:
      rtext = ef.variable.get()
      r = pyutil.string_to_float(rtext)
      if r != None:
        settings.ranges.append((ref_axis, pick_axis, r))

    return settings
    
  # ---------------------------------------------------------------------------
  #
  def pick_cb(self):

    settings = self.get_settings()
    if settings:
      if settings.selected_only:
        ref_peaks = settings.ref_spectrum.selected_peaks()
      else:
        ref_peaks = settings.ref_spectrum.peak_list()
      self.stoppable_call(self.pick_peaks, settings.pick_view,
                          ref_peaks, settings.ranges)
      message = 'Picked %d peaks in %d regions' % (self.picked,
                                                   self.region_count)
      self.progress_report(message)

  # ---------------------------------------------------------------------------
  #
  def pick_peaks(self, pick_view, ref_peaks, ranges):

    pick_spectrum = pick_view.spectrum

    height_thresholds = self.picking_thresholds(pick_view)
    min_linewidth = pick_spectrum.pick_minimum_linewidth
    min_dropoff = pick_spectrum.pick_minimum_drop_factor
    
    self.region_count = 0
    self.picked = 0
    picked_peaks = []
    for peak in ref_peaks:

      self.region_count = self.region_count + 1
      region = self.pick_region(peak, pick_spectrum, ranges)
      region_peaks = pick_spectrum.pick_peaks(region, height_thresholds,
                                              min_linewidth, min_dropoff)

      alias = self.pick_alias(peak, pick_spectrum, ranges)
      for p in region_peaks:
        p.alias = alias
        
      for p in region_peaks:
        p.selected = 1
      picked_peaks = picked_peaks + region_peaks
      self.picked = len(picked_peaks)
      
      message = ('%d peaks in %d of %d regions' %
                 (self.picked, self.region_count, len(ref_peaks)))
      self.progress_report(message)

  # ---------------------------------------------------------------------------
  # Take the higher of the spectrum peak picking threshold and the lowest
  # displayed contour level.
  #
  def picking_thresholds(self, pick_view):

    return (pick_view.negative_levels.lowest, pick_view.positive_levels.lowest)

  # ---------------------------------------------------------------------------
  #
  def pick_alias(self, ref_peak, pick_spectrum, ranges):

    alias = pick_spectrum.dimension * [0]
    for ref_axis, pick_axis, range in ranges:
      freq = ref_peak.frequency[ref_axis]
      pos = sputil.alias_axis_onto_spectrum(freq, pick_axis, pick_spectrum)
      if pos != freq:
        alias[pick_axis] = freq - pos
    return alias

  # ---------------------------------------------------------------------------
  #
  def pick_region(self, ref_peak, pick_spectrum, ranges):

    rmin = list(pick_spectrum.region[0])
    rmax = list(pick_spectrum.region[1])
    for ref_axis, pick_axis, range in ranges:
      freq = ref_peak.frequency[ref_axis]
      pos = sputil.alias_axis_onto_spectrum(freq, pick_axis, pick_spectrum)
      rmin[pick_axis] = max(rmin[pick_axis], pos - range)
      rmax[pick_axis] = min(rmax[pick_axis], pos + range)
    return (tuple(rmin), tuple(rmax))
  
  # ---------------------------------------------------------------------------
  #
  def select_cb(self):

    settings = self.get_settings()
    if settings:
      if settings.selected_only:
        ref_peaks = settings.ref_spectrum.selected_peaks()
      else:
        ref_peaks = settings.ref_spectrum.peak_list()
      self.stoppable_call(self.select_peaks, settings.pick_view.spectrum,
                          ref_peaks, settings.ranges)

      message = 'Selected %d peaks in %d regions' % (self.selected,
                                                     self.region_count)
      self.progress_report(message)

  # ---------------------------------------------------------------------------
  #
  def select_peaks(self, pick_spectrum, ref_peaks, ranges):

    target_peaks = pick_spectrum.peak_list()

    selected_peaks = {}
    self.region_count = 0
    for rp in ref_peaks:
      self.region_count = self.region_count + 1
      for tp in target_peaks:
        if self.close_peaks(rp, tp, ranges):
          selected_peaks[tp] = 1
      self.selected = len(selected_peaks)
      message = ('%d peaks selected in %d of %d regions' %
                 (self.selected, self.region_count, len(ref_peaks)))
      self.progress_report(message)
    selected_peaks = selected_peaks.keys()

    #
    # Select the peaks
    #
    if selected_peaks:
      self.session.unselect_all_ornaments()
    for p in selected_peaks:
      p.selected = 1

  # ---------------------------------------------------------------------------
  #
  def close_peaks(self, ref_peak, target_peak, ranges):

    for ref_axis, pick_axis, range in ranges:
      dist = abs(ref_peak.frequency[ref_axis]-target_peak.frequency[pick_axis])
      if dist > range:
        return 0
    return 1

# -----------------------------------------------------------------------------
#
def show_dialog(session):
  sputil.the_dialog(restricted_pick_dialog,session).show_window(1)
