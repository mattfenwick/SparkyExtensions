# -----------------------------------------------------------------------------
# Produce chemical shift and peak list output from Sparky in XEASY format.
# This is the the format read by structure calculation program Dyana.
#
import string
import Tkinter

import pyutil
import sparky
import sputil
import cyana
import tkutil

# -----------------------------------------------------------------------------
#
class xeasy_format_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'DYANA / XEASY Format')

    sc = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice = sc

    sl = tkutil.scrolling_list(self.top, 'Chemical shift list', 5)
    sl.frame.pack(fill = 'both', expand = 1)
    sl.listbox.bind('<ButtonRelease-1>', self.resonance_cb)
    self.shift_list = sl

    pl = sputil.peak_listbox(self.top)
    pl.frame.pack(fill = 'both', expand = 1)
    pl.heading['text'] = 'Peak list'
    pl.listbox.bind('<ButtonRelease-1>', pl.select_peak_cb)
    pl.listbox.bind('<ButtonRelease-2>', pl.goto_peak_cb)
    pl.listbox.bind('<Double-ButtonRelease-1>', pl.goto_peak_cb)
    self.peak_list = pl

    cy = tkutil.checkbutton(self.top, 'Cyana Formatting ?', 0)
    cy.button.pack(side = 'top', anchor = 'w')
    self.cyana = cy

    hb = tkutil.checkbutton(self.top,
                            'Show peak heights instead of volumes?', 0)
    hb.button.pack(side = 'top', anchor = 'w')
    self.heights = hb

    ib = tkutil.checkbutton(self.top, 'Include unintegrated peaks?', 0)
    ib.button.pack(side = 'top', anchor = 'w')
    self.unintegrated = ib

    ab = tkutil.checkbutton(self.top, 'Include unassigned peaks?', 0)
    ab.button.pack(side = 'top', anchor = 'w')
    self.unassigned = ab

    mb = tkutil.checkbutton(self.top,
                            'Include assignments without a residue number?', 0)
    mb.button.pack(side = 'top', anchor = 'w')
    self.unnumbered = mb

    nb = tkutil.checkbutton(self.top, 'Show peak notes?', 0)
    nb.button.pack(side = 'top', anchor = 'w')
    self.note = nb

    eh = Tkinter.Label(self.top, text = 'Omit peak if note has a word from:')
    eh.pack(side = 'top', anchor = 'w')
    ef = tkutil.entry_field(self.top, '  ', width = 30)
    ef.frame.pack(side = 'top', anchor = 'w')
    self.note_words = ef
    et = Tkinter.Label(self.top, text = '(space separated list of words)')
    et.pack(side = 'top', anchor = 'w')
    
    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
                           ('Update', self.update_cb),
			   ('Write Shifts', self.save_shifts_cb),
                           ('Write Peaks', self.save_peaks_cb),
                           ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'XEASYFormat')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[3])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    spectrum = self.spectrum_choice.spectrum()
    if spectrum == None:
      return

    cyana_header = self.cyana.state()
    show_heights = self.heights.state()
    show_unintegrated = self.unintegrated.state()
    show_unassigned = self.unassigned.state()
    show_unnumbered = self.unnumbered.state()
    show_note = self.note.state()
    note_words = string.split(self.note_words.variable.get())
    note_words = filter(lambda w: len(w) > 0, note_words)
    
    self.stoppable_call(self.show_chemical_shifts, spectrum.condition,
                        show_unnumbered)
    self.stoppable_call(self.show_peaks, spectrum, cyana_header,
                        show_heights, show_unintegrated, show_unassigned,
                        show_unnumbered, show_note, note_words)

  # ---------------------------------------------------------------------------
  #
  def save_shifts_cb(self):
    
    path = tkutil.save_file(self.top, 'Save XEASY Chemical Shifts', 'peaklist')
    if path:
      self.shift_list.write_file(path, 'w', write_heading = 0)

  # ---------------------------------------------------------------------------
  #
  def save_peaks_cb(self):
    
    path = tkutil.save_file(self.top, 'Save XEASY Peak List', 'peaklist')
    if path:
      self.peak_list.write_file(path, 'w', write_heading = 0)

  # ---------------------------------------------------------------------------
  #
  def resonance_cb(self, event):
    
    r = self.shift_list.event_line_data(event)
    if r:
      self.session.show_resonance_peak_list(r)
      
  # ---------------------------------------------------------------------------
  #
  def show_chemical_shifts(self, condition, show_unnumbered):

    reslist = condition.resonance_list()
    reslist.sort(sputil.compare_resonances)
    self.assign_atom_ids(reslist)
      
    self.shift_list.clear()
    self.stoppable_loop('shifts', 100)
    cyana_dict = None;
    if self.cyana.state():
        cyana_dict = cyana.CyanaDictionary();
    for r in reslist:
      self.check_for_stop()
      if show_unnumbered or r.group.number != None:
        line = self.shift_line(r,cyana_dict);
        self.shift_list.append(line, r)

  # ---------------------------------------------------------------------------
  #
  def shift_line(self,r,cyana_dict):

    format = '%4d %8.3f %6.3f %6s %d'

    group_num = r.group.number
    if group_num == None:
      group_num = 0
      
    atom_name = r.atom.name;
    if cyana_dict:
      aa = r.group.name[0];
      atom_name = cyana_dict.toCyana(aa,atom_name);

    values = (r.atom.xeasy_id, r.frequency, r.deviation,
              atom_name, group_num)
    return format % values

  # ---------------------------------------------------------------------------
  #
  def assign_atom_ids(self, reslist):

    max_id = 0
    for r in reslist:
      if hasattr(r.atom, 'xeasy_id'):
        max_id = max(max_id, r.atom.xeasy_id)
      
    next_id = max_id + 1
    for r in reslist:
      if not hasattr(r.atom, 'xeasy_id'):
        r.atom.xeasy_id = next_id
        next_id = next_id + 1
        
  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, spectrum, cyana_header,
                 show_heights, show_unintegrated, show_unassigned,
                 show_unnumbered, show_note, note_words):

    self.peak_list.clear()
    spectrum_peak_list = spectrum.peak_list();

    heading = '# Number of dimensions %s' % spectrum.dimension
    self.peak_list.append(heading, None)
    heading = '# Number of peaks %s' % len(spectrum_peak_list) 
    self.peak_list.append(heading, None)

    if cyana_header:
      self.peak_list.append('#FORMAT cyana3D', None)
      i = 0
      heading_last = '#CYANAFORMAT '
      for nuclei in spectrum.nuclei:
        atom = nuclei[-1]
        if (i == 1 and atom == 'H'):
          atom = 'h'
        heading = '#INAME %d %s' % (i+1, atom)
        self.peak_list.append(heading, None)
        heading_last = heading_last + atom
        i = i + 1
      self.peak_list.append(heading_last, None)
    
    peak_id = 0
    self.stoppable_loop('peaks', 100)
    for peak in spectrum_peak_list:
      self.check_for_stop()
      show = ((show_unassigned or peak.is_assigned) and
              (show_unintegrated or peak.volume != None) and
              (show_unnumbered or self.assignment_numbered(peak.resonances()))
              and (not note_words or
                   not pyutil.string_contains_word(peak.note, note_words)))
      show = 1;
      if show:
        peak_id = peak_id + 1
        line = self.peak_line(peak, peak_id, show_heights)
        self.peak_list.append(line, peak)
        if show_note and peak.note:
          line = '       # ' + peak.note
          self.peak_list.append(line, peak)

  # ---------------------------------------------------------------------------
  #
  def peak_line(self, peak, peak_id, show_heights):

    color_code = 1
    spectrum_type = 'U'
    intensity_error = 0.0

    if show_heights:
      intensity_method = 'e'
      intensity = sputil.peak_height(peak)
    elif peak.volume == None:
      intensity_method = '-'
      intensity = 0.0
    else:
      intensity_method = 'e'
      intensity = peak.volume

    atom_ids = []
    for r in peak.resonances():
      if r:
        atom_ids.append(r.atom.xeasy_id)
      else:
        atom_ids.append(0)

    freq_text = pyutil.sequence_string(peak.frequency, '%8.3f')
    id_text = pyutil.sequence_string(atom_ids, '%4d ')
    
    format = '%4d%s %1d %1s %18.3g %9.2g %1s %3d %s%1d'
    values = (peak_id, freq_text, color_code, spectrum_type,
              intensity, intensity_error, intensity_method, 0, id_text, 0)
    line = format % values
    
    return line

  # ---------------------------------------------------------------------------
  #
  def assignment_numbered(self, assignment):

    for r in assignment:
      if r and r.group.number == None:
        return 0
    return 1

# -----------------------------------------------------------------------------
#
def show_dialog(session):
  d = sputil.the_dialog(xeasy_format_dialog, session)
  d.show_window(1)
