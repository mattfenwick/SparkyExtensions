# -----------------------------------------------------------------------------
# Create a fake spectrum using peak intensities predicted by corma.
#
import os
import Tkinter

import corma
import pyutil
import sparky
import sputil
import mysubprocess as subprocess
import tkutil

# -----------------------------------------------------------------------------
#
class corma_spectrum_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Create Corma Spectrum')

    sm = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sm.frame.pack(side = 'top', anchor = 'w')
    sm.add_callback(self.spectrum_cb)
    self.spectrum_menu = sm

    ms = tkutil.entry_row(self.top, 'Matrix size: ',
                          ('w1', '0', 5), ('w2', '0', 5))
    ms.frame.pack(side = 'top', anchor = 'w')
    self.matrix_size = ms

    lw = tkutil.entry_row(self.top, 'Default linewidth (hz): ',
                          ('w1', '0', 5), ('w2', '0', 5))
    lw.frame.pack(side = 'top', anchor = 'w')
    self.default_linewidth = lw

    cp = tkutil.file_field(self.top, 'Corma file: ', 'corma')
    cp.frame.pack(side = 'top', anchor = 'w')
    self.corma_path = cp

    sp = tkutil.file_field(self.top, 'Save in file: ', 'spectrum', save = 1)
    sp.frame.pack(side = 'top', anchor = 'w')
    self.save_path = sp
    
    progress_label = Tkinter.Label(self.top, anchor = 'nw', justify = 'left')
    progress_label.pack(side = 'top', anchor = 'w')
    
    self.spectrum_cb(self.spectrum_menu.get())

    br = tkutil.button_row(self.top,
			   ('Create Spectrum', self.create_spectrum_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'CormaSpectrum')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[1])

  # ---------------------------------------------------------------------------
  # Initialize matrix size and save path entries
  #
  def spectrum_cb(self, name):

    spectrum = sputil.name_to_spectrum(name, self.session)
    if spectrum and spectrum.dimension == 2:
      for a in range(2):
        self.matrix_size.variables[a].set(spectrum.data_size[a])
      self.save_path.set(spectrum.data_path + '.corma')

  # ---------------------------------------------------------------------------
  #
  def create_spectrum_cb(self):

    spectrum = self.spectrum_menu.spectrum()
    size = tkutil.integer_variable_values(self.matrix_size.variables)

    default_lw = tkutil.float_variable_values(self.default_linewidth.variables)

    corma_path = self.corma_path.get()
    corma_data = self.stoppable_call(corma.intensities,
                                     self.session, corma_path, self)
    if corma_data == None:
      return

    save_path = self.save_path.get()

    origin = spectrum.region[1]
    nuclei = spectrum.nuclei
    sfreq = spectrum.hz_per_ppm
    swidth = pyutil.seq_product(spectrum.spectrum_width, spectrum.hz_per_ppm)

    gaussians = self.stoppable_call(self.gaussian_list,
                                    spectrum, corma_data, default_lw)
    if gaussians == None:
      return
    
    self.progress_report('%d unassigned resonances\n' % self.unassigned +
                         '%d unknown linewidths\n' % self.nolinewidth +
                         'Writing %s' % os.path.basename(save_path))

    self.run_peaks2ucsf(save_path, size, origin, nuclei,
                        sfreq, swidth, gaussians)
                        
  # ---------------------------------------------------------------------------
  #
  def gaussian_list(self, spectrum, corma_data, default_linewidth):

    reslist = spectrum.condition.resonance_list()
    na2r = self.number_atom_to_resonance_table(reslist)
    res_linewidths_1 = self.resonance_to_linewidth_hz_table(spectrum, 0)
    res_linewidths_2 = self.resonance_to_linewidth_hz_table(spectrum, 1)

    no_linewidth_1 = len(reslist) - len(res_linewidths_1)
    no_linewidth_2 = len(reslist) - len(res_linewidths_2)
    self.nolinewidth = no_linewidth_1 + no_linewidth_2

    unassigned = {}
    scale_factor = 1e6
    gaussians = []
    for (num_atom_1, num_atom_2), volume in corma_data.intensity_table.items():
      if not na2r.has_key(num_atom_1):
        unassigned[num_atom_1] = 1
      elif not na2r.has_key(num_atom_2):
        unassigned[num_atom_2] = 1
      else:
        r1 = na2r[num_atom_1]
        r2 = na2r[num_atom_2]
        lw1 = self.linewidth(r1, res_linewidths_1, default_linewidth[0])
        lw2 = self.linewidth(r2, res_linewidths_2, default_linewidth[1])
        if lw1 and lw2:
          freq = (r1.frequency, r2.frequency)
          h = scale_factor * volume / (lw1 * lw2)
          lw = (lw1, lw2)
          gaussians.append((freq, h, lw))

    self.unassigned = len(unassigned)

    return gaussians
    
  # ---------------------------------------------------------------------------
  #
  def linewidth(self, r, r2lw, default_lw):

    if r2lw.has_key(r):
      lw = r2lw[r]
    else:
      lw = default_lw
    return lw

  # ---------------------------------------------------------------------------
  #
  def number_atom_to_resonance_table(self, reslist):
      
    na2r = {}
    for r in reslist:
      na = (r.group.number, r.atom.name)
      na2r[na] = r
    return na2r
    
  # ---------------------------------------------------------------------------
  #
  def resonance_to_linewidth_hz_table(self, spectrum, axis):

    res_linewidths = {}
    self.stoppable_loop('axis w%d resonance linewidths' % (axis+1), 10)
    for r in spectrum.condition.resonance_list():
      self.check_for_stop()
      lw = self.resonance_linewidth_hz(r, spectrum, axis)
      if lw:
        res_linewidths[r] = lw
    return res_linewidths
    
  # ---------------------------------------------------------------------------
  #
  def resonance_linewidth_hz(self, resonance, spectrum, axis):

    lw_total = 0
    lw_count = 0
    hz_per_ppm = spectrum.hz_per_ppm
    for p in resonance.peak_list():
      if p.spectrum == spectrum:
        peak_linewidth = p.line_width
        if peak_linewidth:
          peak_resonances = p.resonances()
          if peak_resonances[axis] == resonance:
            lw_total = lw_total + peak_linewidth[axis] * hz_per_ppm[axis]
            lw_count = lw_count + 1

    if lw_count == 0:
      return None

    return lw_total / lw_count
  
  # ---------------------------------------------------------------------------
  #
  def run_peaks2ucsf(self, save_path, msize, origin, nuclei, sfreq, swidth,
                     gaussians):


    #
    # Use my subprocess code instead of popen because I want to not block
    # waiting for subprocess to finish and I want to be notified when it
    # has finished
    #
    p2u_path = os.path.join(sparky.installation_path(), 'bin', 'peaks2ucsf')
    proc = subprocess.subprocess(p2u_path, save_path)
    p2u = proc.to_process

    p2u.write('%d' % len(msize) + ' # dimension\n')
    p2u.write(pyutil.sequence_string(msize, '%d ') + '# matrix size\n')
    p2u.write(pyutil.sequence_string(origin, '%.6f ') + '# ppm origin\n')
    p2u.write(pyutil.sequence_string(nuclei, '%s ') + '# nuclei\n')
    p2u.write(pyutil.sequence_string(sfreq, '%.9f ') + '# spectometer freq\n')
    p2u.write(pyutil.sequence_string(swidth, '%.3f ') + '# spectrum width\n')

    for ppm_center, height, linewidth in gaussians:
      p2u.write(pyutil.sequence_string(ppm_center, '%8.5f ') +
                '%10.4g' % height +
                pyutil.sequence_string(linewidth, '%8.2f ') +
                '\n')

    p2u.close()

    message = ('%d unassigned resonances\n' % self.unassigned +
               '%d unknown linewidths\n' % self.nolinewidth +
               'Writing ' + os.path.basename(save_path))
    report_finished = pyutil.precompose(self.report_finished, proc, message)
    tkutil.call_me_when(self.top, report_finished, proc.exitted)

  # ---------------------------------------------------------------------------
  #
  def report_finished(self, peaks2ucsf_process, message):
  
    if peaks2ucsf_process.exit_status == 0:
      message = message + ' finished'
    else:
      message = (message + ' FAILED' +
                 '(exit code %d)' % peaks2ucsf_process.exit_status)
    self.progress_report(message)

    self.show_window(1)

# -----------------------------------------------------------------------------
#
def show_corma_spectrum(session):
  sputil.the_dialog(corma_spectrum_dialog,session).show_window(1)
