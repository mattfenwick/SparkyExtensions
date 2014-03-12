# -----------------------------------------------------------------------------
# Shift spectrum axis scale by one sweepwidth and
# alias all peaks back to original positions.
#

import pyutil
import sputil

# -----------------------------------------------------------------------------
#
def fold_spectrum(spectrum, axis, multiples):

  if axis >= spectrum.dimension:
    return

  sweepwidth = spectrum.sweep_width[axis]
  delta = spectrum.dimension * [0]
  delta[axis] = multiples * sweepwidth
  spectrum.scale_offset = pyutil.add_tuples(spectrum.scale_offset, delta)

  #
  # Add alias to every peak
  #
  for peak in spectrum.peak_list():

    peak.alias = pyutil.subtract_tuples(peak.alias, delta)
    peaklets = peak.peaklets()
    if peaklets:
      for p in peaklets:
        p.alias = pyutil.subtract_tuples(p.alias, delta)

# -----------------------------------------------------------------------------
#
def fold_selected_spectrum(session, axis, multiples):

  s = session.selected_spectrum()
  if s:
    fold_spectrum(s, axis, multiples)
