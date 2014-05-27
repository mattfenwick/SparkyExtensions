# -----------------------------------------------------------------------------
# Strip plot display for 3D spectra
#

import Tkinter

import axes
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class strip_plot(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    tkutil.Dialog.__init__(self, session.tk, 'Strip Plot')

    self.strip_width = 52       # width in screen pixels
    self.strip_gap = 8
    self.y_center = {'13C':None, '1H':None, '15N':None}
    self.y_pixel_size = {'13C':None, '1H':None, '15N':None}
    self.y_limits = {'13C':None, '1H':None, '15N':None}
    self.strips = []
    self.strips_to_reposition = {}
    self.first_strip_index = 0
    self.spectrum_label = 0

    self.chosen_spectra = []
    self.spectrum_axis_orders = self.default_axis_orders()
    
    self.match_tolerances = {'1H': .02, '13C': .2, '15N': .2}
    self.max_unmatched = 0

    mbar = self.create_menus(self.top, session)
    mbar.pack(side = 'top', anchor = 'nw', fill = 'x')

    sf = self.create_strip_frame(self.top)
    sf.pack(side = 'top', anchor = 'nw', fill = 'both', expand = 1)
    
    self.strips_frame.bind('<Configure>', self.resize_cb, 1)

    self.msg = Tkinter.Label(self.top)
    self.msg.pack(side = 'top', anchor = 'w')
      
  # ---------------------------------------------------------------------------
  #
  def default_axis_orders(self):

    axis_orders = {}
    spectra = self.session.project.spectrum_list()
    for spectrum in spectra:
      if spectrum.dimension == 3:
        order = pyutil.order(('1H', '13C', '15N'), spectrum.nuclei)
        if order == None:
          order = (0, 1, 2)
        axis_orders[spectrum] = order
    return axis_orders
      
  # ---------------------------------------------------------------------------
  #
  def create_menus(self, parent, session):

    mbar = Tkinter.Frame(parent)

    m = tkutil.menu(mbar, 'Show')
    m.button.pack(side = 'left')
    add_button = pyutil.precompose(self.add_menu_button, m)
    
    add_button('Select strip spectra...', 'ss', select_strip_spectra)
    add_button('Set strip width...', 'sw', choose_strip_width)
    m.add_separator()
    add_button('Add selected peak strips', 'sk', add_peak_strips)
    add_button('All assigned strips', 'sn', add_assigned_strips)
    m.add_separator()
    add_button('Zoom strips in', 'si', zoom_in_strips)
    add_button('Zoom strips out', 'so', zoom_out_strips)
    add_button('Copy view strip options', 'sv', copy_view_options)
    m.add_separator()
    add_button('Delete selected strip', 'sd', delete_view_strip)
    add_button('Delete all strips', 'sD', delete_all_strips)
    m.add_separator()
    m.add_button('Help', sputil.help_cb(self.session, 'StripPlot'))
    m.add_button('Close', self.close_cb)
      
    m = tkutil.menu(mbar, 'Find')
    m.button.pack(side = 'left')
    add_button = pyutil.precompose(self.add_menu_button, m)
    
    add_button('Go to assigned peak strip', 'sj', goto_assigned_strip)
    m.add_separator()
    add_button('Strip matching tolerances...', 'sT', matching_strips_setup)
    add_button('Add strips matching peaks', 'sm', add_matching_strips)
    add_button('Delete matched strips', 'sM', delete_matched_strips)

    return mbar
  
  # ---------------------------------------------------------------------------
  #
  def add_menu_button(self, menu, menu_text, accel, func):

    cb = pyutil.precompose(func, self.session)
    menu.add_button(menu_text + (' (%s)' % accel), cb)
    self.session.add_command(accel, '', cb)
  
  # ---------------------------------------------------------------------------
  #
  def create_strip_frame(self, parent):

    sf = Tkinter.Frame(parent)
    
    sf.rowconfigure(0, weight = 1)
    sf.columnconfigure(0, weight = 1)

    strips = Tkinter.Frame(sf, width = 200, height = 800)
    strips.grid(row = 0, column = 0, sticky = 'news')
    strips.rowconfigure(0, weight = 1)
    self.strips_frame = strips
    
    vbar = Tkinter.Scrollbar(sf, command = self.scroll_strips)
    vbar.grid(row = 0, column = 1, sticky = 'ns')
    vbar.set(0, 1)
    self.vbar = vbar
    
    hbar = Tkinter.Scrollbar(sf, orient = 'horizontal',
                             command = self.shift_strips)
    hbar.grid(row = 1, column = 0, sticky = 'ew')
    hbar.set(0, 1)
    self.hbar = hbar

    return sf

  # ---------------------------------------------------------------------------
  #
  def resize_cb(self, event):
    
    self.change_visible_strips()
    self.update_vertical_scrollbar()
    
  # ---------------------------------------------------------------------------
  #
  def select_strip_spectra(self):

    sd = sputil.the_dialog(choose_strips_dialog, self.session)
    settings = (self.chosen_spectra, self.spectrum_axis_orders, self.spectrum_label)
    sd.set_parent_dialog(self, settings, self.set_spectra)
    sd.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def set_spectra(self, settings):

    self.chosen_spectra, self.spectrum_axis_orders, self.spectrum_label = settings
    
  # ---------------------------------------------------------------------------
  #
  def choose_strip_width(self):

    sd = sputil.the_dialog(strip_plot_settings, self.session)
    settings = (self.strip_width, self.strip_gap)
    sd.set_parent_dialog(self, settings, self.set_strip_width)
    sd.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def set_strip_width(self, settings):

    self.strip_width, self.strip_gap = settings
    self.change_visible_strips()
    
  # ---------------------------------------------------------------------------
  #
  def add_strips(self, strips):

    for strip in strips:
      self.set_y_scale(strip)
      self.strips.append(strip)

    if strips:
      self.change_visible_strips()
  
  # ---------------------------------------------------------------------------
  #
  def sort_strips(self, compare):

    if self.strips:

      first = self.strips[self.first_strip_index]
      self.strips.sort(compare)
      self.first_strip_index = self.strips.index(first)
      self.change_visible_strips()
  
  # ---------------------------------------------------------------------------
  #
  def goto_strip(self, strip):

    s = self.strip_position(strip)
    if s == None:
      return

    self.first_strip_index = s
    self.change_visible_strips()
  
  # ---------------------------------------------------------------------------
  #
  def strip_position(self, strip):

    for s in range(len(self.strips)):
      if self.strips[s] == strip:
        return s
    return None
      
  # ---------------------------------------------------------------------------
  # Set the y pixel size and center y position for the strip
  #
  def set_y_scale(self, strip):

    self.expand_y_scale(strip)

    y_nucleus = strip.y_nucleus
    strip.set_y_center(self.y_center[y_nucleus])
    strip.set_y_pixel_size(self.y_pixel_size[y_nucleus])
      
  # ---------------------------------------------------------------------------
  # Expand or initialize the strip plot y limits for this nucleus.
  #
  def expand_y_scale(self, strip):

    y_axis = strip.xyz_axes[1]
    r = strip.spectrum.region
    y_min = r[0][y_axis]
    y_max = r[1][y_axis]

    y_nucleus = strip.y_nucleus
    y_limits = self.y_limits[y_nucleus]
    if y_limits == None:
      self.y_limits[y_nucleus] = (y_min, y_max)
      y_middle = .5 * (y_min + y_max)
      self.y_center[y_nucleus] = y_middle
      y_range = y_max - y_min
      self.strips_frame.update_idletasks()        # determine window geometry
      window_height = self.strips_frame.winfo_height()
      self.y_pixel_size[y_nucleus] = y_range / window_height
    elif y_min < y_limits[0] or y_max > y_limits[1]:
      self.y_limits[y_nucleus] = (min(y_min, y_limits[0]),
                                  max(y_max, y_limits[1]))
      self.update_vertical_scrollbar()
    
  # ---------------------------------------------------------------------------
  #
  def adjust_y_scale(self, y_nucleus, y_center, y_pixel_size):

    y_limits = self.y_limits[y_nucleus]
    if y_limits:
      middle_f = (y_center - y_limits[0]) / (y_limits[1] - y_limits[0])
      self.adjust_y_center(middle_f)
      scale_f = y_pixel_size / self.y_pixel_size[y_nucleus]
      self.zoom_strips(scale_f)

  # ---------------------------------------------------------------------------
  #
  def adjust_y_center(self, y_center_fraction):

    f = y_center_fraction
    for y_nucleus, y_limits in self.y_limits.items():
      if y_limits:
        self.y_center[y_nucleus] = f * y_limits[1] + (1-f) * y_limits[0]

    for strip in self.strips:
      strip.set_y_center(self.y_center[strip.y_nucleus])

  # ---------------------------------------------------------------------------
  #
  def delete_strips(self, strips):

    deleted_strips = {}
    for strip in strips:
      deleted_strips[strip] = 1

    keepers = []
    for s in range(len(self.strips)):
      strip = self.strips[s]
      if self.strips_to_reposition.has_key(strip):
        del self.strips_to_reposition[strip]
      if deleted_strips.has_key(strip):
        self.set_column(strip, self.strips_frame, None)
        if s < self.first_strip_index:
          self.first_strip_index = self.first_strip_index - 1
      else:
        keepers.append(strip)
    self.strips = keepers
    self.change_visible_strips()
    
  # ---------------------------------------------------------------------------
  #
  def delete_view_strip(self, view):

    for strip in self.strips:
      if strip.view == view:
        self.delete_strips([strip])
        return
    
  # ---------------------------------------------------------------------------
  #
  def delete_spectrum_strips(self, spectrum):

    strips = []
    for strip in self.strips:
      if strip.spectrum == spectrum:
        strips.append(strip)
    self.delete_strips(strips)
    
  # ---------------------------------------------------------------------------
  #
  def delete_all_strips(self):

    for i in range(len(self.strips)):
      self.set_column(self.strips[i], self.strips_frame, None)
    self.strips = []
    self.first_strip_index = 0
    self.change_visible_strips()

  # ---------------------------------------------------------------------------
  #
  def scroll_strips(self, *args):

    tkutil.adjust_scrollbar(self.vbar, args)
    (f1, f2) = self.vbar.get()
    f = .5 * (f1 + f2)
    self.adjust_y_center(f)

  # ---------------------------------------------------------------------------
  #
  def shift_strips(self, *args):

    steps_per_page = self.visible_strip_count()
    tkutil.adjust_scrollbar(self.hbar, args, steps_per_page)
    (f1, f2) = self.hbar.get()
    self.first_strip_index = int(round(f1 * len(self.strips)))
    self.change_visible_strips()
    
  # ---------------------------------------------------------------------------
  #
  def change_visible_strips(self):

    if len(self.strips) == 0:
      for nucleus in self.y_limits.keys():
        self.y_limits[nucleus] = None

    first_index = self.first_strip_index
    for strip in self.strips[:first_index]:
      self.set_column(strip, self.strips_frame, None)
    count = self.visible_strip_count()
    for strip in self.strips[first_index+count:]:
      self.set_column(strip, self.strips_frame, None)
    for i in range(count):
      self.set_column(self.strips[first_index + i], self.strips_frame, i)
    self.update_horizontal_scrollbar()
    
  # ---------------------------------------------------------------------------
  #
  def set_column(self, strip, parent, column):

    strip.position_label(parent, column, self.strip_width, self.strip_gap)
    self.request_strip_position(strip, parent, column)

  # ---------------------------------------------------------------------------
  # Defer view creation and deletion so scrolling through many strips
  # remains responsive.
  #
  def request_strip_position(self, strip, parent, column):

    self.strips_to_reposition[strip] = (parent, column)
    if len(self.strips_to_reposition) == 1:
      parent.after_idle(self.reposition_views)

  # ---------------------------------------------------------------------------
  #
  def reposition_views(self):

    if self.strips_to_reposition:
      strip, (parent, column) = self.strips_to_reposition.items()[0]
      del self.strips_to_reposition[strip]
      strip.position_view(parent, column, self.strip_width, self.strip_gap)
      if self.strips_to_reposition:
        parent.after_idle(self.reposition_views)

  # ---------------------------------------------------------------------------
  # Adjust the scrollbar well size to reflect the fraction of the spectrum
  # region shown.  If there are different nuclei on the vertical axis
  # make the well size represent the one with the smallest fraction.
  # This assures that the scrollbar can reach the edge of the spectrum for
  # every strip.
  #
  def update_vertical_scrollbar(self):

    #
    # Use the height of the strips frame to determine the fraction of spectrum
    # that can be seen by multiplying by the y_pixel_size.  This overestimates
    # the viewable region if there is any border around the spectrum.  The
    # result is that the scrollbar can't quite reach the edge of the spectrum.
    # Correct for the 2 pixel highlight thickness of strips.
    #
    self.strips_frame.update_idletasks()        # determine window geometry
    strip_height = self.strips_frame.grid_bbox(row = 0, column = 0)[3]
    strip_height = max(1, strip_height - 4)

    min_bar_size = None
    params = None
    for y_nucleus in self.y_limits.keys():
      y_limits = self.y_limits[y_nucleus]
      if y_limits:
        r_low, r_high = y_limits
        y_range = r_high - r_low
        y_height = strip_height * self.y_pixel_size[y_nucleus]
        bfrac = y_height / y_range
        if min_bar_size == None or bfrac < min_bar_size:
          y_center = self.y_center[y_nucleus]
          y_low = y_center - .5 * y_height
          y_high = y_center + .5 * y_height
          min_bar_size = bfrac
          params = (y_low, y_high, r_low, r_high)

    if params:
      (y_low, y_high, r_low, r_high) = params
      tkutil.set_scrollbar(self.vbar, y_low, y_high, r_low, r_high)

  # ---------------------------------------------------------------------------
  #
  def update_horizontal_scrollbar(self):

    self.top.update_idletasks()      # Make sure view geometry is correct

    first = self.first_strip_index
    count = self.visible_strip_count()
    tkutil.set_scrollbar(self.hbar, first, first + count, 0, len(self.strips))

  # ---------------------------------------------------------------------------
  #
  def visible_strip_count(self):

    frame_width = self.strips_frame.winfo_width()
    max_strips = len(self.strips) - self.first_strip_index
    count = max(1, frame_width / (self.strip_width + self.strip_gap))
    return min(max_strips, count)
  
  # ---------------------------------------------------------------------------
  #
  def spectrum_strip(self, spectrum, xyz_axes, center, label_text):

    settings = self.default_view_options()
    mimic_view = self.view_to_mimic(spectrum)
    if mimic_view:
      for attr in settings.keys():
        settings[attr] = getattr(mimic_view, attr)

    s = strip(spectrum, xyz_axes, center, settings, label_text)

    return s
  
  # ---------------------------------------------------------------------------
  #
  def default_view_options(self):

    return {
      'pixel_size':None,
      'visible_depth':None,
      'positive_levels':None,
      'negative_levels':None,
      'show_ornaments':1,
      'show_peaks':1,
      'show_peakgroups':1,
      'show_labels':1,
      'show_lines':1,
      'show_grids':1,
      'show_crosshair':1,
      'show_crosshair_from_other_views':1,
      }

  # ---------------------------------------------------------------------------
  #
  def view_to_mimic(self, spectrum):

    for strip in self.strips:
      if strip.view_exists() and strip.spectrum == spectrum:
        return strip.view
    return sputil.preferred_view(spectrum)
    
  # ---------------------------------------------------------------------------
  #
  def zoom_in_strips(self):

    self.zoom_strips(.5)
    
  # ---------------------------------------------------------------------------
  #
  def zoom_out_strips(self):

    self.zoom_strips(2)
    
  # ---------------------------------------------------------------------------
  #
  def zoom_strips(self, factor):

    for y_nucleus, y_pixel_size in self.y_pixel_size.items():
      if y_pixel_size:
        self.y_pixel_size[y_nucleus] = factor * y_pixel_size
      
    for strip in self.strips:
      strip.set_y_pixel_size(self.y_pixel_size[strip.y_nucleus])

    self.update_vertical_scrollbar()
    
  # ---------------------------------------------------------------------------
  #
  def copy_view_options(self, view):

    if view:

      settings = self.default_view_options()
      for attr in settings.keys():
        settings[attr] = getattr(view, attr)

      for strip in self.strips:
        if strip.spectrum == view.spectrum:
          strip.change_view_options(settings)
    
  # ---------------------------------------------------------------------------
  #
  def matching_strips_setup(self):

    msd = sputil.the_dialog(match_settings_dialog, self.session)
    settings = (self.match_tolerances, self.max_unmatched)
    msd.set_parent_dialog(self, settings, self.set_match_tolerances)
    msd.show_window(1)
    
  # ---------------------------------------------------------------------------
  #
  def set_match_tolerances(self, settings):

    self.match_tolerances, self.max_unmatched = settings
    
  # ---------------------------------------------------------------------------
  #
  def add_matching_strips(self, spectrum, target_peaks):

    if spectrum == None:
      return

    tolerances = []
    for nucleus in spectrum.nuclei:
      tolerances.append(self.match_tolerances[nucleus])
    
    target_shifts = []
    for peak in target_peaks:
      xyz_axes = self.xyz_axes(peak.spectrum)
      if xyz_axes:
        aX, aY, aZ = xyz_axes
        target_shifts.append(peak.frequency[aY])

    strips = self.matching_strips(spectrum, tolerances,
                                  target_shifts, self.max_unmatched)
    self.add_strips(strips)

    plural = pyutil.plural_ending(len(strips))
    self.message('Added %d matching strip%s' % (len(strips), plural))
    
  # ---------------------------------------------------------------------------
  #
  def matching_strips(self, spectrum, tolerances,
                      target_shifts, max_unmatched):

    xyz_axes = self.xyz_axes(spectrum)
    if xyz_axes == None:
      return []
    aX, aY, aZ = xyz_axes

    matches = {}
    clusters = sputil.cluster_peaks(spectrum.peak_list(),
                                    aX, tolerances[aX], aZ, tolerances[aZ])
    for cluster in clusters:
      score = self.match_score(cluster, aY, tolerances[aY],
                               target_shifts, max_unmatched)
      if score > 0:
        matches[cluster[0]] = score
    peaks = pyutil.sort_keys_by_value(matches)
    peaks.reverse()                     # put in descending order

    strips = []
    for peak in peaks:
      strip = self.peak_strips(peak, [spectrum])[0]
      strips.append(strip)

    self.last_match_strips = strips     # for deleting
    
    return strips
    
  # ---------------------------------------------------------------------------
  #
  def match_score(self, cluster, axis, tolerance,
                  target_shifts, max_unmatched):

    no_match = 0
    score = 0
    for target in target_shifts:
      range = tolerance
      for peak in cluster:
        freq = peak.frequency[axis]
        delta = abs(freq - target)
        range = min(delta, range)
      if range == tolerance:
        no_match = no_match + 1
        if no_match > max_unmatched:
          return 0
      else:
        score = score + (tolerance - range)
    return score
    
  # ---------------------------------------------------------------------------
  #
  def delete_matched_strips(self):

    if hasattr(self, 'last_match_strips'):
      self.delete_strips(self.last_match_strips)
      self.last_match_strips = []
  
  # ---------------------------------------------------------------------------
  #
  def xyz_axes(self, spectrum):

    ao = self.spectrum_axis_orders
    if not ao.has_key(spectrum):
      return None
    return ao[spectrum]
    
  # ---------------------------------------------------------------------------
  #
  def message(self, text):

    self.msg['text'] = text
    
  # ---------------------------------------------------------------------------
  #
  def show_peak_strips(self, peaks):

    strips = self.strips_for_peaks(peaks)
    self.show_window(1)
    self.add_strips(strips)

    plural1 = pyutil.plural_ending(len(strips))
    plural2 = pyutil.plural_ending(len(peaks))
    self.message('Added %d strip%s for %d peak%s' %
                 (len(strips), plural1, len(peaks), plural2))
    
  # ---------------------------------------------------------------------------
  #
  def strips_for_peaks(self, peaks):

    spectra_3d = self.chosen_spectra

    spectra = spectra_3d
    strips = []
    for peak in peaks:
      if not spectra_3d:
        if peak.spectrum.dimension == 3:
          spectra = [peak.spectrum]
        else:
          spectra = []
      strips = strips + self.peak_strips(peak, spectra)

    return strips
    
  # ---------------------------------------------------------------------------
  #
  def peak_strips(self, peak, spectra_3d):

    peak_xyz_axes = self.peak_strip_axes(peak, spectra_3d)
    if peak_xyz_axes == None:
      return []

    paX, paY, paZ = peak_xyz_axes
    if paY == None:
      xyz_freq = (peak.frequency[paX], 0, peak.frequency[paZ])
    else:
      xyz_freq = pyutil.permute(peak.frequency, peak_xyz_axes)

    nuclei = peak.spectrum.nuclei
    xz_nuclei = (nuclei[paX], nuclei[paZ])

    label = self.peak_strip_label(peak, paX, paZ)
    
    strips = []
    for spectrum in spectra_3d:
      xyz_axes = self.xyz_axes(spectrum)
      if xyz_axes:
        aX, aY, aZ = xyz_axes
        if (spectrum.nuclei[aX], spectrum.nuclei[aZ]) == xz_nuclei:
          if self.spectrum_label:
            label = spectrum.name + '\n' + label
          center = pyutil.unpermute(xyz_freq, xyz_axes)
          center = sputil.alias_onto_spectrum(center, spectrum)
          strip = self.spectrum_strip(spectrum, xyz_axes, center, label)
          strips.append(strip)
          label = '\n\n'

    return strips
    
  # ---------------------------------------------------------------------------
  # Peak can be from 3D or 2D spectrum.
  #
  def peak_strip_axes(self, peak, spectra_3d):

    xyz_axes = self.xyz_axes(peak.spectrum)
    if xyz_axes:
      return xyz_axes

    #
    # Peak is not from 3D spectrum, probably from 2D spectrum
    # try to figure out which axes to use for X and Z by matching nuclei.
    #
    xz_axes = self.matching_xz_axes(peak.spectrum.nuclei, spectra_3d)
    if xz_axes:
      aX, aZ = xz_axes
      return aX, None, aZ

    return None
    
  # ---------------------------------------------------------------------------
  #
  def peak_strip_label(self, peak, aX, aZ):

    label = '%.4g\n%.4g\n' % (peak.frequency[aX], peak.frequency[aZ])
    x_res = peak.resonances()[aX]
    if x_res:
      label = label + x_res.group.name + ' ' + x_res.atom.name 

    return label

  # ---------------------------------------------------------------------------
  #
  def matching_xz_axes(self, nuclei, spectra_3d):

    for spectrum in spectra_3d:
      xyz_axes = self.xyz_axes(spectrum)
      if xyz_axes:
        aX, aY, aZ = xyz_axes
        x_axis = pyutil.element_position(spectrum.nuclei[aX], nuclei)
        z_axis = pyutil.element_position(spectrum.nuclei[aZ], nuclei)
        if x_axis != None and z_axis != None:
          return (x_axis, z_axis)
    return None
    
  # ---------------------------------------------------------------------------
  #
  def add_assigned_strips(self):

    spectra_3d = self.chosen_spectra

    xz_assignments = {}
    for spectrum in spectra_3d:
      aX, aY, aZ = self.xyz_axes(spectrum)
      for peak in spectrum.peak_list():
        res = peak.resonances()
        rX = res[aX]
        rZ = res[aZ]
        if rX and rZ:
          xz_assignments[((rX.group.number, rX.group.name, rX.atom.name),
                          (rZ.group.number, rZ.group.name, rZ.atom.name))] = 1
    xz_assignments = xz_assignments.keys()
    xz_assignments.sort()
    xz_assignments = map(lambda xz: (xz[0][1:], xz[1][1:]), xz_assignments)
    
    strips = []
    for xz_assignment in xz_assignments:
      for spectrum in spectra_3d:
        strip = self.assigned_strip(spectrum, xz_assignment)
        if strip:
          strips.append(strip)

    self.add_strips(strips)

    plural1 = pyutil.plural_ending(len(strips))
    plural2 = pyutil.plural_ending(len(xz_assignments))
    self.message('Added %d strip%s for %d assignment%s' %
                 (len(strips), plural1, len(xz_assignments), plural2))
    
  # ---------------------------------------------------------------------------
  #
  def assigned_strip(self, spectrum, xz_assignment):

    c = spectrum.condition
    x_assignment, z_assignment = xz_assignment
    rX = apply(c.find_resonance, x_assignment)
    rZ = apply(c.find_resonance, z_assignment)
    if rX and rZ:
      freq = [0,0,0]
      xyz_axes = self.xyz_axes(spectrum)
      aX, aY, aZ = xyz_axes
      freq[aX] = rX.frequency
      freq[aZ] = rZ.frequency
      center = sputil.alias_onto_spectrum(freq, spectrum)
      group_name = x_assignment[0]
      atom_name = x_assignment[1]
      label = '%.4g\n%.4g\n%s %s' % (center[aX], center[aZ], group_name, atom_name)
      if self.spectrum_label:
        spectrum_name = spectrum.name
        label = spectrum_name + '\n' + label 
      strip = self.spectrum_strip(spectrum, xyz_axes, center, label)
      strip.xz_assignment = xz_assignment
      return strip
    return None
    
  # ---------------------------------------------------------------------------
  #
  def goto_assigned_strip(self, peak):

    if peak == None:
      return
    
    assignments = []
    for r in peak.resonances():
      if r:
        assignments.append((r.group.name, r.atom.name))

    if len(assignments) < 2:
      return
    
    for strip in self.strips:
      if hasattr(strip, 'xz_assignment'):
        x_assignment, z_assignment = strip.xz_assignment
        if x_assignment in assignments and z_assignment in assignments:
          self.goto_strip(strip)
          return
    
# -----------------------------------------------------------------------------
#
class strip:

  def __init__(self, spectrum, xyz_axes, center, settings, label_text):

    self.spectrum = spectrum
    self.xyz_axes = xyz_axes
    self.y_nucleus = spectrum.nuclei[xyz_axes[1]]
    self.center = center
    self.settings = settings.copy()
    self.label_text = label_text

    self.view = None
    self.label = None
    
  # ---------------------------------------------------------------------------
  #
  def __del__(self):

    self.delete_label()
    self.delete_view()
        
  # ---------------------------------------------------------------------------
  #
  def position_label(self, parent, column, strip_width, strip_gap):

    if column == None:
      self.delete_label()
    else:
      parent.columnconfigure(column, minsize = strip_width + strip_gap)
      self.create_label(parent, column)
      self.label.grid(row = 4, column = column, sticky = 'news')
        
  # ---------------------------------------------------------------------------
  #
  def create_label(self, parent, column):

    if self.label == None:
      color = sputil.spectrum_color(self.spectrum)
      self.label = Tkinter.Label(parent, text = self.label_text,
                                 highlightthickness = 1,
                                 highlightbackground = color)

  # ---------------------------------------------------------------------------
  #
  def delete_label(self):

    if self.label:
      self.label.destroy()
      self.label = None

  # ---------------------------------------------------------------------------
  #
  def position_view(self, parent, column, strip_width, strip_gap):

    if column == None:
      self.delete_view()
    else:
      if not self.view_exists():
        if sparky.object_exists(self.spectrum):
          self.view = self.create_view(parent, column, strip_width)
        else:
          self.view = None
          return
      tkutil.tk_call(parent, self.view.frame, 'configure',
                     '-width', strip_width)
      tkutil.tk_call(parent, 'grid', 'configure', self.view.frame,
                     '-row', 0, '-column', column,
                     '-sticky', 'news', '-padx', strip_gap/2)

  # ---------------------------------------------------------------------------
  #
  def view_exists(self):

    v = self.view
    if v == None:
      return 0

    if not sparky.object_exists(v):
      self.view = None      # view object no longer exists
      return 0

    return 1

  # ---------------------------------------------------------------------------
  #
  def create_view(self, parent, column, strip_width):
    
    session = self.spectrum.session
    v = session.create_view(parent, self.spectrum)
    v.show_scales = 0
    v.show_scrollbars = 0
    v.axis_order = self.xyz_axes
    v.center = self.center

    self.set_view_options(v, self.settings)

    #
    # Set the view frame width and don't listen to resize requests from view
    #
    width = strip_width
    height = 800
    color = sputil.spectrum_color(self.spectrum)
    tkutil.tk_call(parent, v.frame, 'configure',
                   '-width', width, '-height', height,
                   '-highlightthickness', 2, '-highlightcolor', color)
    tkutil.tk_call(parent, 'grid', 'propagate', v.frame, 0)

    return v
  
  # ---------------------------------------------------------------------------
  #
  def change_view_options(self, settings):

    self.settings = settings.copy()
    if self.view_exists():
      self.set_view_options(self.view, settings)
      
  # ---------------------------------------------------------------------------
  #
  def set_view_options(self, view, settings):
    
    for attr, value in settings.items():
      if value == None:
        settings[attr] = getattr(view, attr)
      else:
        setattr(view, attr, value)
  
  # ---------------------------------------------------------------------------
  #
  def delete_view(self):

    if self.view_exists():
      for attr in self.settings.keys():
        self.settings[attr] = getattr(self.view, attr)
      self.view.destroy()
      self.view = None
    
  # ---------------------------------------------------------------------------
  #
  def set_y_center(self, y_center):
    
    center = list(self.center)
    y_axis = self.xyz_axes[1]
    center[y_axis] = y_center
    self.center = tuple(center)
    if self.view_exists():
      self.view.center = self.center

  # ---------------------------------------------------------------------------
  #
  def set_y_pixel_size(self, y_pixel_size):

    y_axis = self.xyz_axes[1]
    pixel_size = self.settings['pixel_size']
    factor = y_pixel_size / pixel_size[y_axis]
    pixel_size = pyutil.scale_tuple(pixel_size, factor)
    self.settings['pixel_size'] = pixel_size
    if self.view_exists():
      self.view.pixel_size = pixel_size
    
# -----------------------------------------------------------------------------
#
class match_settings_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):
    
    tkutil.Settings_Dialog.__init__(self, session.tk,
                                    'Strip Matching Parameters')

    t = tkutil.entry_row(self.top, 'Tolerances ',
                         (' 1H', '.02', 5),
                         (' 13C', '.2', 5),
                         (' 15N', '.2', 5))
    t.frame.pack(side = 'top', anchor = 'w')
    self.tolerances = {'1H': t.variables[0],
                       '13C': t.variables[1],
                       '15N': t.variables[2]}

    e = tkutil.entry_field(self.top, 'Allow ', '0', 3, ' unmatched peaks')
    e.frame.pack(side = 'top', anchor = 'w')
    self.max_unmatched = e.variable
    
    br = tkutil.button_row(self.top,
                           ('Ok', self.ok_cb),
			   ('Apply', self.apply_cb),                           
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'StripPlot')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    match_tolerances, max_unmatched = settings

    for nucleus, tol in match_tolerances.items():
      var = self.tolerances[nucleus]
      cur_tol = pyutil.string_to_float(var.get(), 0)
      new_tol = match_tolerances[nucleus]
      if new_tol != cur_tol:
        var.set('%.3g' % new_tol)

    self.max_unmatched.set('%d' % max_unmatched)
    
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    match_tolerances = {}
    for nucleus in ('1H', '13C', '15N'):
      tol = pyutil.string_to_float(self.tolerances[nucleus].get(), 0)
      match_tolerances[nucleus] = tol

    max_unmatched = pyutil.string_to_int(self.max_unmatched.get(), 0)
    
    return (match_tolerances, max_unmatched)
  
# -----------------------------------------------------------------------------
# Select spectra for which strips will be displayed.
#
class choose_strips_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    self.session = session
    
    tkutil.Settings_Dialog.__init__(self, session.tk, 'Show Peak Strips')

    f = self.spectrum_choice_table(self.top)
    f.pack(side = 'top', anchor = 'w')
    
    sx = tkutil.checkbutton(self.top, 'Show spectrum name under each strip', 0)
    sx.button.pack(side = 'top', anchor = 'w', padx = 10, pady = 10)
    self.label_spectrum = sx

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
			   ('Apply', self.apply_cb),
			   ('Close', self.close_cb),                           
                           ('Help', sputil.help_cb(session, 'StripPlot')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def spectrum_choice_table(self, parent):

    headings = ('Show strips   ', 'XYZ axes')
    st = sputil.spectrum_table(self.session, parent, headings,
                               self.add_spectrum, self.remove_spectrum)
    st.spectrum_to_checkbutton = {}
    st.chosen_spectra = []
    st.axis_order_menu = {}
    self.spectrum_table = st
    
    spectra = self.session.project.spectrum_list()
    for spectrum in spectra:
      st.add_spectrum(spectrum)

    return st.frame

  # ---------------------------------------------------------------------------
  #
  def add_spectrum(self, spectrum, table, row):

    if spectrum.dimension != 3:
      return
    
    #
    # Make spectrum checkbutton
    #
    cb = tkutil.checkbutton(table.frame, spectrum.name, 0)
    cb.button['selectcolor'] = sputil.spectrum_color(spectrum)
    choose_cb = pyutil.precompose(sputil.choose_spectrum_cb, spectrum,
                                  table.chosen_spectra)
    cb.add_callback(choose_cb)
    cb.button.grid(row = row, column = 0, sticky = 'w')
    table.spectrum_to_checkbutton[spectrum] = cb

    #
    # Make axis order menu.  Set default xyz axis order for triple
    # resonance spectra to HCN.
    #
    hcn_order = pyutil.order(('1H', '13C', '15N'), spectrum.nuclei)
    aom = axes.axis_order_menu(table.frame, spectrum.nuclei,
                               initial_order = hcn_order)
    aom.frame.grid(row = row, column = 1, sticky = 'w')
    table.axis_order_menu[spectrum] = aom

  # ---------------------------------------------------------------------------
  #
  def remove_spectrum(self, spectrum, table):

    if not table.spectrum_to_checkbutton.has_key(spectrum):
      return
    
    cb = table.spectrum_to_checkbutton[spectrum]
    cb.set_state(0)
    cb.button.destroy()
    del table.spectrum_to_checkbutton[spectrum]

    table.axis_order_menu[spectrum].frame.destroy()
    del table.axis_order_menu[spectrum]

    self.parent_dialog.delete_spectrum_strips(spectrum)

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    chosen_spectra, spectrum_axis_orders, spectrum_label = settings

    chosen = {}
    for s in chosen_spectra:
      chosen[s] = 1
      
    st = self.spectrum_table
    for s, cb in st.spectrum_to_checkbutton.items():
      cb.set_state(chosen.has_key(s))

    for s, aom in st.axis_order_menu.items():      
      if spectrum_axis_orders.has_key(s):
        aom.set_axis_order(spectrum_axis_orders[s])
        
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    st = self.spectrum_table
    chosen_spectra = st.chosen_spectra[:]

    spectrum_axis_orders = {}
    for spectrum, aom in st.axis_order_menu.items():
      spectrum_axis_orders[spectrum] = aom.axis_order()

    spectrum_label = self.label_spectrum.state()
      
    return (chosen_spectra, spectrum_axis_orders, spectrum_label)
  
# -----------------------------------------------------------------------------
#
class strip_plot_settings(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk, 'Show Peak Strips')

    sw = tkutil.entry_field(self.top, 'Strip width (screen pixels): ', '', 4)
    sw.frame.pack(side = 'top', anchor = 'w')
    self.strip_width = sw.variable

    gp = tkutil.entry_field(self.top, 'Gap between strips (screen pixels): ',
                            '', 4)
    gp.frame.pack(side = 'top', anchor = 'w')
    self.strip_gap = gp.variable

    br = tkutil.button_row(self.top,
			   ('Ok', self.ok_cb),
			   ('Apply', self.apply_cb),
			   ('Close', self.close_cb),                           
                           ('Help', sputil.help_cb(session, 'StripPlot')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    swidth, sgap = settings
    self.strip_width.set('%d' % swidth)
    self.strip_gap.set('%d' % sgap)
    
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    swidth = pyutil.string_to_int(self.strip_width.get(), 52)
    sgap = pyutil.string_to_int(self.strip_gap.get(), 8)
    return (swidth, sgap)
  
# -----------------------------------------------------------------------------
#
def strip_dialog(session):
  return sputil.the_dialog(strip_plot, session)
  
# -----------------------------------------------------------------------------
# Strip plot commands
#
def show_strip_plot(session):
  strip_dialog(session).show_window(1)

def delete_view_strip(session):
  strip_dialog(session).delete_view_strip(session.selected_view())
def delete_all_strips(session):
  strip_dialog(session).delete_all_strips()
def zoom_in_strips(session):
  strip_dialog(session).zoom_in_strips()
def zoom_out_strips(session):
  strip_dialog(session).zoom_out_strips()
def copy_view_options(session):
  strip_dialog(session).copy_view_options(session.selected_view())

def select_strip_spectra(session):
  strip_dialog(session).select_strip_spectra()
def choose_strip_width(session):
  strip_dialog(session).choose_strip_width()
def add_peak_strips(session):
  strip_dialog(session).show_peak_strips(session.selected_peaks())
def matching_strips_setup(session):
  strip_dialog(session).matching_strips_setup()
def add_matching_strips(session):
  strip_dialog(session).add_matching_strips(session.selected_spectrum(),
                                            session.selected_peaks())
def delete_matched_strips(session):
  strip_dialog(session).delete_matched_strips()

def add_assigned_strips(session):
  strip_dialog(session).add_assigned_strips()
def goto_assigned_strip(session):
  strip_dialog(session).goto_assigned_strip(sputil.selected_peak(session))
