# -----------------------------------------------------------------------------
# Set linewidths for each of selected peaks using other peaks in spectrum with
# same assignment along the same axis.  Also move the position of the peak to
# the average position of other peaks with the same assignment for that axis.
# If there are no other peaks with the same assigment set the linewidth along
# that axis to zero and move the peak to the resonance line frequency.  If the
# peak has no assignment along an axis set the linewidth to zero for that axis.
#
# This command is used for integrating overlapped peak.  Linewidths and
# positions are copied from already integrated peaks and then you can use
# linefitting where only the peak height is adjusted with position and
# linewidth fixed.  This should produce more sensible fits than letting
# the fit adjust all linewidths and positions.
#

import pyutil
import sputil

# -----------------------------------------------------------------------------
#
def copy_linewidths_and_positions(session):

  spectrum = session.selected_spectrum()
  if spectrum:
    peaks = spectrum.selected_peaks()
    for peak in peaks:
      f, lw = average_linewidth_and_position(spectrum, peak, peaks)
      peak.frequency = f
      peak.line_width = lw
      peak.line_width_method = 'copy'

# -----------------------------------------------------------------------------
#
def average_linewidth_and_position(spectrum, peak, not_these_peaks):

  f = []
  lw = []
  for axis in range(spectrum.dimension):
    freq, linewidth = resonance_linewidth_and_position(spectrum, peak, axis,
                                                       not_these_peaks)
    f.append(freq)
    lw.append(linewidth)
  return tuple(f), tuple(lw)

# -----------------------------------------------------------------------------
#
def resonance_linewidth_and_position(spectrum, peak, axis, not_these_peaks):

  freq = peak.frequency[axis]
  linewidth = 0
  r = peak.resonances()[axis]
  if r:
    freq = r.frequency
    opeaks = assigned_peaks(spectrum, r, axis)
    opeaks = pyutil.subtract_lists(opeaks, not_these_peaks)
    if opeaks:
      freq = average_frequency(opeaks, axis)
      linewidth = average_linewidth(opeaks, axis)
      if linewidth == 0:
        out = spectrum.session.stdout
        out.write('No w%d axis %s %s linewidth\n'
                  % (axis+1, spectrum.name, r.name))
    else:
      out = spectrum.session.stdout
      out.write('No w%d axis %s %s peaks\n'
                % (axis+1, spectrum.name, r.name))
  return freq, linewidth

# -----------------------------------------------------------------------------
#
def assigned_peaks(spectrum, resonance, axis):

  peaks = []
  for peak in resonance.peak_list():
    if peak.spectrum == spectrum and peak.resonances()[axis] == resonance:
      peaks.append(peak)
  return tuple(peaks)

# -----------------------------------------------------------------------------
#
def average_frequency(peaks, axis):

  if peaks:
    f = 0
    for peak in peaks:
      f = f + peak.frequency[axis]
    return f / len(peaks)
  return 0

# -----------------------------------------------------------------------------
#
def average_linewidth(peaks, axis):

  lw = 0
  count = 0
  for peak in peaks:
    if peak.line_width:
      lw = lw + peak.line_width[axis]
      count = count + 1
  if count > 0:
    return lw / count
  return 0
