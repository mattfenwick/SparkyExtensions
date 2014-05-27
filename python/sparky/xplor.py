# -----------------------------------------------------------------------------
# Output XPLOR format restraint list
#
import Tkinter
import string

import noesy
import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class xplor_format_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    tkutil.Dialog.__init__(self, session.tk, 'XPLOR Restraints')

    sc = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice = sc

    pl = sputil.peak_listbox(self.top)
    pl.frame.pack(fill = 'both', expand = 1)
    pl.heading['text'] = 'XPLOR Restraint list'
    pl.listbox.bind('<ButtonRelease-1>', pl.select_peak_cb)
    pl.listbox.bind('<ButtonRelease-2>', pl.goto_peak_cb)
    pl.listbox.bind('<Double-ButtonRelease-1>', pl.goto_peak_cb)
    self.peak_list = pl

    bt = tkutil.entry_field(self.top, 'Bounds text ', width = 30)
    bt.frame.pack(side = 'top', anchor = 'w')
    self.bounds_text = bt

    nb = tkutil.checkbutton(self.top, 'Show peak notes?', 0)
    nb.button.pack(side = 'top', anchor = 'w')
    self.note = nb

    hb = tkutil.entry_row(self.top, 'Only peaks with height',
                          (' >= ', '', 8), (' and < ', '', 8))
    hb.frame.pack(side = 'top', anchor = 'w')
    self.height_min, self.height_max = hb.variables

    vb = tkutil.entry_row(self.top, 'Only peaks with volume',
                          (' >= ', '', 8), (' and < ', '', 8))
    vb.frame.pack(side = 'top', anchor = 'w')
    self.volume_min, self.volume_max = vb.variables

    eh1 = Tkinter.Label(self.top, text = 'Omit peak if note has a word from:')
    eh1.pack(side = 'top', anchor = 'w')
    ef1 = tkutil.entry_field(self.top, '  ', width = 30)
    ef1.frame.pack(side = 'top', anchor = 'w')
    self.exclude_note_words = ef1
    eh2 = Tkinter.Label(self.top, text = 'or if it has no word from:')
    eh2.pack(side = 'top', anchor = 'w')
    ef2 = tkutil.entry_field(self.top, '  ', width = 30)
    ef2.frame.pack(side = 'top', anchor = 'w')
    self.require_note_words = ef2
    et = Tkinter.Label(self.top, text = '(space separated list of words)')
    et.pack(side = 'top', anchor = 'w')
    
    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
                           ('Update', self.update_cb),
                           ('Write Restraints', self.save_peaks_cb),
                           ('Append', self.append_peaks_cb),
                           ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session,
                                                   'XplorFormat')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[3])

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    spectrum = self.spectrum_choice.spectrum()
    if spectrum == None:
      return

    show_note = self.note.state()
    bounds_text = self.bounds_text.variable.get()
    hmin = pyutil.string_to_float(self.height_min.get())
    hmax = pyutil.string_to_float(self.height_max.get())
    vmin = pyutil.string_to_float(self.volume_min.get())
    vmax = pyutil.string_to_float(self.volume_max.get())
    exclude_note_words = string.split(self.exclude_note_words.variable.get())
    exculde_note_words = filter(lambda w: len(w) > 0, exclude_note_words)
    require_note_words = string.split(self.require_note_words.variable.get())
    require_note_words = filter(lambda w: len(w) > 0, require_note_words)

    peaks = sputil.sort_peaks_by_assignment(spectrum.peak_list(), self)
    self.stoppable_call(self.show_peaks, peaks, show_note,
                        hmin, hmax, vmin, vmax,
                        exclude_note_words, require_note_words,
                        bounds_text)

  # ---------------------------------------------------------------------------
  #
  def save_peaks_cb(self):
    
    path = tkutil.save_file(self.top, 'Save XPLOR Restraint List', 'peaklist')
    if path:
      self.peak_list.write_file(path, 'w', write_heading = 0)

  # ---------------------------------------------------------------------------
  #
  def append_peaks_cb(self):
    
    path = tkutil.load_file(self.top,
                            'Append XPLOR Restraint List', 'peaklist')
    if path:
      self.peak_list.write_file(path, 'a+', write_heading = 0)

  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, peaks, show_note,
                 ht_min, ht_max, vol_min, vol_max,
                 exclude_note_words, require_note_words, bounds_text):

    self.peak_list.clear()
    
    self.stoppable_loop('peaks', 100)
    for peak in peaks:
      self.check_for_stop()
      show = (peak.is_assigned and
              (ht_min == None or sputil.peak_height(peak) >= ht_min) and
              (ht_max == None or sputil.peak_height(peak) < ht_max) and
              (vol_min == None or
               (peak.volume != None and peak.volume >= vol_min)) and
              (vol_max == None or
               (peak.volume != None and peak.volume < vol_max)) and
              (not exclude_note_words or
               not pyutil.string_contains_word(peak.note, exclude_note_words))
              and 
              (not require_note_words or
               pyutil.string_contains_word(peak.note, require_note_words))
              )
      if show:
        line = self.peak_line(peak, bounds_text)
        if line:
          self.peak_list.append(line, peak)
          if show_note and peak.note:
            note = '{%s}' % peak.note
            self.peak_list.append(note, peak)

  # ---------------------------------------------------------------------------
  #
  def peak_line(self, peak, bounds_text):

    r1, r2 = noesy.proton_resonances(peak)

    if r1 == None or r2 == None:
      return None

    if r1.group.number == None or r2.group.number == None:
      return None

    line = ('assign (residue %d and name %s) (residue %d and name %s) %s'
            % (r1.group.number, r1.atom.name,
               r2.group.number, r2.atom.name,
               bounds_text))
      
    return line

# -----------------------------------------------------------------------------
#
def show_dialog(session):
  d = sputil.the_dialog(xplor_format_dialog, session)
  d.show_window(1)
