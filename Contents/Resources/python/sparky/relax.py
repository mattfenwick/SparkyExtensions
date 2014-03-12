# -----------------------------------------------------------------------------
# Fit peak heights or volumes in a series of spectra to a decaying exponential.
#
import math
import re
import string
import Tkinter

import curvefit
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class relaxation_dialog(tkutil.Dialog, tkutil.Stoppable):

  HEIGHTS_MODE = 'heights at same position in each spectrum'
  ASSIGNED_HEIGHTS_MODE = 'heights at assigned peak positions if available'
  ASSIGNED_HEIGHTS_ONLY_MODE = 'heights at assigned peak positions only'
  VOLUMES_MODE = 'volumes of assigned peaks only'

  def __init__(self, session):

    self.session = session
    self.spectrum_times = []
    self.last_spectrum_times = []
    self.error_estimate_trials = 5
    
    tkutil.Dialog.__init__(self, session.tk, 'Relaxation Peak Heights')

    pl = tkutil.scrolling_list(self.top, heading = '', height = 5)
    pl.frame.pack(side = 'top', fill = 'both', expand = 1)
    pl.listbox.bind('<ButtonRelease-1>', self.show_fit_cb)
    pl.listbox.bind('<KeyPress-Delete>', pl.delete_selected_cb)
    # The following is needed so key press is received by list box.
    pl.listbox.bind('<ButtonPress-1>', pl.set_focus_cb)
    self.peak_list = pl

    md = tkutil.option_menu(self.top, 'Use ',
                            (self.HEIGHTS_MODE,
                             self.ASSIGNED_HEIGHTS_MODE,
                             self.ASSIGNED_HEIGHTS_ONLY_MODE,
                             self.VOLUMES_MODE))
    md.frame.pack(side = 'top', anchor = 'w')
    self.mode = md.variable

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
                           ('Setup...', self.setup_cb),
                           ('Save', self.peak_list.save_cb),
                           ('Append', self.peak_list.append_cb),
                           ('Clear', self.clear_cb),
                           ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'RelaxFit')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[4])

  # ---------------------------------------------------------------------------
  #
  def setup_cb(self):

    setup_dialog = sputil.the_dialog(relax_setup_dialog, self.session)
    settings = {'spectrum-times': self.spectrum_times,
                'error-estimate-trials': self.error_estimate_trials}
    setup_dialog.set_parent_dialog(self, settings, self.set_params)
    setup_dialog.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def set_params(self, settings):

    self.spectrum_times = settings['spectrum-times']
    self.error_estimate_trials = settings['error-estimate-trials']

  # ---------------------------------------------------------------------------
  #
  def clear_cb(self):

    self.peak_list.clear()

  # ---------------------------------------------------------------------------
  #
  def show_fit_cb(self, event):

    fit = self.peak_list.event_line_data(event)
    if fit:
      curvefit.show_fit(self.session, fit.name, fit, self.show_peak_cb)

  # ---------------------------------------------------------------------------
  #
  def show_peak_cb(self, fit, n):

    # Need to skip spectra where no fit height was available.
    sh_pairs = map(lambda th, st: (st[0], th[1]),
                   fit.th_pairs, fit.spectrum_times)
    fit_sh = filter(lambda sh: sh[1] != None, sh_pairs)
    fit_spectra = map(lambda sh: sh[0], fit_sh)
    
    sputil.show_spectrum_position(fit_spectra[n], fit.peak_position)
    
  # ---------------------------------------------------------------------------
  #
  def show_peak_heights(self):

    if not self.top.winfo_ismapped():
      self.show_window(1)

    if self.spectrum_times:
      if self.spectrum_times != self.last_spectrum_times:
        self.last_spectrum_times = self.spectrum_times
        self.show_heading(self.spectrum_times)
      peaks = self.session.selected_peaks()
      count = self.stoppable_call(self.show_peaks, peaks, self.spectrum_times)
      not_fit = len(peaks) - count
      if not_fit:
        self.peaks_not_fit_warning(not_fit)
    
  # ---------------------------------------------------------------------------
  #
  def peaks_not_fit_warning(self, not_fit):

    if not_fit > 0:
      if not_fit > 1:  plural = 's'
      else:            plural = ''
      if self.mode.get() == self.VOLUMES_MODE:   h_or_v = 'volumes'
      else:                                      h_or_v = 'heights'
      msg = ('%d peak%s with less than 2 %s not fit.'
             % (not_fit, plural, h_or_v))
      self.progress_report(msg)
    
  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, peaks, spectrum_times):

    value_mode = self.mode.get()
    self.stoppable_loop(' peaks', 1)
    count = 0
    for p in self.session.selected_peaks():
      self.check_for_stop()
      th_pairs = self.time_height_pairs(p, value_mode, spectrum_times)
      
      fit = self.fit_exponential(th_pairs)
      if fit == None:
        continue
      fit.name = p.assignment
      fit.peak_position = p.position
      fit.spectrum_times = spectrum_times
      fit.th_pairs = th_pairs
      line = self.peak_line(p, fit)
      self.peak_list.append(line, fit)
      self.peak_list.listbox.see('end')
      count = count + 1

    return count
      
  # ---------------------------------------------------------------------------
  #
  def show_heading(self, spectrum_times):

    self.peak_list.clear()
    heading = '%15s %9s %-8s ' % ('Assignment', 'T-decay', 'SD')
    for s, t in spectrum_times:
      st = '%s/%.3g' % (s.name, t)
      heading = heading + '%10s ' % st
    self.peak_list.heading['text'] = heading

  # ---------------------------------------------------------------------------
  #
  def time_height_pairs(self, peak, value_mode, spectrum_times):

    pos = peak.position

    if peak.is_assigned and value_mode != self.HEIGHTS_MODE:
      assignment = peak.assignment
    else:
      assignment = None

    th_pairs = []
    for s, t in spectrum_times:
      h = None
      if assignment:
        p = s.find_peak(assignment)
      else:
        p = None
      if value_mode == self.HEIGHTS_MODE:
        h = s.data_height(pos)
      elif value_mode == self.ASSIGNED_HEIGHTS_MODE:
        if p:
          h = s.data_height(p.position)
        else:
          h = s.data_height(pos)
      elif value_mode == self.ASSIGNED_HEIGHTS_ONLY_MODE:
        if p:
          h = s.data_height(p.position)
      elif value_mode == self.VOLUMES_MODE:
        if p and p.volume != None:
          h = p.volume
      th_pairs.append((t, h))

    return th_pairs

  # ---------------------------------------------------------------------------
  #
  def fit_exponential(self, th_pairs):

    fit_th_pairs = filter(lambda th: th[1] != None, th_pairs)
    if len(fit_th_pairs) < 2:
      return None
    
    exp_func = a_exp_bx_function()
    
    h_values = map(lambda th: th[1], fit_th_pairs)
    h_middle = .5 * (max(h_values) + min(h_values))
    params = (h_middle, 0)
    trials = self.error_estimate_trials

    fit = curvefit.least_squares_fit(fit_th_pairs, exp_func, params, 1e-6)
    fit.estimate_parameter_error(fit.point_sd, trials)

    self.calculate_decay_time(fit)

    return fit

  # ---------------------------------------------------------------------------
  # The error estimate for T is not the standard deviation over fits with
  # gaussian random y errors added.  I believe such a standard deviation is
  # divergent because the flat fit (T = infinity) case has codimension 1.
  # So instead I take the SD of the rate constant (1/T) and convert this
  # to an equivalent T error.
  #
  def calculate_decay_time(self, fit):

    if fit.converged and fit.params[1] != 0:
      t_decay = -1 / fit.params[1]
      t_sd = abs(t_decay * fit.param_sd[1] /  fit.params[1])
    else:
      t_decay = 0
      t_sd = 0
    
    fit.t_decay = t_decay
    fit.t_sd = t_sd

  # ---------------------------------------------------------------------------
  #
  def peak_line(self, peak, fit):

    htext = ''
    for t, h in fit.th_pairs:
      if h == None:
        htext = htext + '%10s ' % 'N/A'
      else:
        htext = htext + '%10.4g ' % h

    ftext = '%15s %9.4g %-8.3g ' % (peak.assignment, fit.t_decay, fit.t_sd)
    line = ftext + htext
    
    return line
  
# -----------------------------------------------------------------------------
#
class a_exp_bx_function:

  def parameter_count(self):
    return 2
  def value(self, params, x):
    a, b = params
    # Multiply overflows in fit error calculation cause core dump on DEC Alpha
    bx = pyutil.bound_value(b*x, -50, 50)
    e = math.exp(bx)
    return a * e
  def parameter_derivatives(self, params, x):
    a, b = params
    e = math.exp(b*x)
    return (e, x*a*e)

# -----------------------------------------------------------------------------
# Select spectra and time constants for fitting.
#
class relax_setup_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk, 'Relaxation Spectra')

    headings = ('Spectrum  ', 'Time parameter')
    st = sputil.spectrum_table(session, self.top, headings,
                               self.add_spectrum, self.remove_spectrum)
    st.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_widgets = {}

    spectra = session.project.spectrum_list()
    def time_param(s, self=self):
      return pyutil.string_to_float(self.default_time_parameter(s), 0)
    spectra = pyutil.sort_by_function_value(spectra, time_param)
    for spectrum in spectra:
      st.add_spectrum(spectrum)

    e = tkutil.entry_field(self.top, 'Use ', '5', 3,
                           ' random trials for error estimates.')
    e.frame.pack(side = 'top', anchor = 'w')
    self.trials = e
    
    br = tkutil.button_row(self.top,
                           ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),                           
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'RelaxFit')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def add_spectrum(self, spectrum, table, row):

    onoff = self.default_onoff(spectrum)
    b = tkutil.checkbutton(table.frame, spectrum.name, onoff)
    b.button.grid(row = row, column = 0, sticky = 'nw')

    ttext = self.default_time_parameter(spectrum)
    e = tkutil.entry_field(table.frame, '', ttext)
    e.frame.grid(row = row, column = 1, sticky = 'nw')

    self.spectrum_widgets[spectrum] = (b, e)

  # ---------------------------------------------------------------------------
  #
  def remove_spectrum(self, spectrum, table):

    b, e = self.spectrum_widgets[spectrum]
    del self.spectrum_widgets[spectrum]
    b.button.destroy()
    e.frame.destroy()
    
  # ---------------------------------------------------------------------------
  #
  def default_onoff(self, spectrum):

    return spectrum.saved_value('relaxation_time_parameter') != None
  
  # ---------------------------------------------------------------------------
  #
  def default_time_parameter(self, spectrum):

    ttext = spectrum.saved_value('relaxation_time_parameter')
    if ttext:
      return ttext
    
    match = re.search('[0-9]+', spectrum.name)
    if match:
      return match.group(0)
    
    return '0'

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    stimes = {}
    for s, t in settings['spectrum-times']:
      stimes[s] = t
      
    for s, (b, e) in self.spectrum_widgets.items():
      b.variable.set(stimes.has_key(s))
      if (stimes.has_key(s) and
          pyutil.string_to_float(e.variable.get()) != stimes[s]):
        e.variable.set('%.5g' % stimes[s])
      
    self.trials.variable.set('%d' % settings['error-estimate-trials'])

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    trials = pyutil.string_to_int(self.trials.variable.get(), 0)
    settings = {'spectrum-times': self.spectrum_times(),
                'error-estimate-trials': trials}
    return settings
    
  # ---------------------------------------------------------------------------
  #
  def spectrum_times(self):

    st = []
    for s, (b, e) in self.spectrum_widgets.items():
      if b.variable.get():
        ttext = e.variable.get()
        t = pyutil.string_to_float(ttext)
        st.append((s, t))
        s.save_value('relaxation_time_parameter', ttext)
    st.sort(self.spectrum_time_order)
    return tuple(st)

  # ---------------------------------------------------------------------------
  #
  def spectrum_time_order(self, st1, st2):

    return cmp(st1[1], st2[1]) or cmp(st1[0].name, st2[0].name)

# -----------------------------------------------------------------------------
#
def show_peak_heights(session):
  sputil.the_dialog(relaxation_dialog,session).show_peak_heights()
