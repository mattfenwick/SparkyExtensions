# -----------------------------------------------------------------------------
# Move one assigned peak and have all other peaks in the same spectrum
# move by the same amount if they have the same assignment along an axis.
# One use of this is to assign a spectrum taken under new experimental
# conditions when a previous spectrum has already been assigned.
# You can select all peaks from the old spectrum (pa) and copy and
# paste) them to the new spectrum (accelerators oc and op).  Then start this
# tool and move a peak for each resonance line to its shifted location.
#

import Tkinter

import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
def move_peaks(peak, from_freq):

  count = 0
  res = peak.resonances()
  for a in range(len(res)):
    resonance = res[a]
    if resonance:
      shift = peak.frequency[a] - from_freq[a]
      for p in resonance.peak_list():
        if (p.spectrum == peak.spectrum and
            p.resonances()[a] == resonance and
            p != peak):
          peaklets = p.peaklets()
          if peaklets:
            for peaklet in peaklets:
              if peaklet != peak:
                shift_peak_frequency(peaklet, a, shift)
          else:
            shift_peak_frequency(p, a, shift)
          count = count + 1

  return count

# -----------------------------------------------------------------------------
#
def shift_peak_frequency(peak, axis, shift):

  freq = list(peak.frequency)
  freq[axis] = freq[axis] + shift
  peak.frequency = freq

# -----------------------------------------------------------------------------
#
class peak_mover(tkutil.Dialog):

  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):

    self.session = session
    self.peak = None
    
    tkutil.Dialog.__init__(self, session.tk, 'Peak Resonance Mover')

    self.spectrum_menu = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    self.spectrum_menu.frame.pack(side = 'top', anchor = 'w')

    cb = tkutil.checkbutton(self.top, 'On / Off', 0)
    cb.button.pack(side = 'top', anchor = 'w')
    cb.add_callback(self.onoff_cb)
    self.onoff = cb
    self.will_drag_notice = None
    self.dragged_notice = None

    self.message = Tkinter.Label(self.top)
    self.message.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'ShiftRes')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def onoff_cb(self, state):

    if state:
      self.will_drag_notice = self.session.notify_me('will drag peak',
                                                     self.will_drag_cb)
      self.dragged_notice = self.session.notify_me('dragged peak',
                                                   self.dragged_cb)
    else:
      self.remove_drag_callbacks()

  # ---------------------------------------------------------------------------
  #
  def remove_drag_callbacks(self):

    if self.will_drag_notice:
      self.session.dont_notify_me(self.will_drag_notice)
      self.will_drag_notice = None
    if self.dragged_notice:
      self.session.dont_notify_me(self.dragged_notice)
      self.dragged_notice = None

  # ---------------------------------------------------------------------------
  #
  def will_drag_cb(self, peak):

    self.peak = peak
    self.from_frequency = peak.frequency

  # ---------------------------------------------------------------------------
  #
  def dragged_cb(self, peak):

    if self.is_window_destroyed():
      self.remove_drag_callbacks()
      return

    spectrum = self.spectrum_menu.spectrum()
    if peak != self.peak or peak.spectrum != spectrum:
      self.peak = None
      return

    count = move_peaks(peak, self.from_frequency)
    self.message['text'] = 'Moved %d additional peaks' % count

  # ---------------------------------------------------------------------------
  #
  def close_cb(self):

    self.onoff.set_state(0)
    tkutil.Dialog.close_cb(self)

# -----------------------------------------------------------------------------
#
def show_move_peak_dialog(session):
  sputil.the_dialog(peak_mover,session).show_window(1)
