# -----------------------------------------------------------------------------
# Read Corma predicted peak intensities from a file.
#
import os
import string

import atoms
import noesy
import tkutil

# -----------------------------------------------------------------------------
#
def intensities(session, corma_path, stoppable = tkutil.Not_Stoppable()):

  if not hasattr(session, 'corma_table'):
    session.corma_table = {}
  t = session.corma_table

  if not t.has_key(corma_path):
    t[corma_path] = corma_intensities(session, corma_path, stoppable)

  return t[corma_path]

# -----------------------------------------------------------------------------
#
class corma_intensities:

  def __init__(self, session, corma_path, stoppable = tkutil.Not_Stoppable()):

    self.corma_path = corma_path
    self.intensity_table = read_intensities(corma_path, stoppable)
    self.spectrum_normalization_factors = {}

    gatable = {}
    for num_atom_1, num_atom_2 in self.intensity_table.keys():
      gatable[(None, num_atom_1[1])] = 1
      gatable[(None, num_atom_2[1])] = 1
    self.atom_translations = \
      atoms.guess_atom_name_translations(session, corma_path, gatable.keys())
    
  # ---------------------------------------------------------------------------
  #
  def normalized_intensity(self, peak):

    i = self.predicted_intensity(peak)
    if i == None:
      return None
    return self.normalization_factor(peak.spectrum) * i

  # ---------------------------------------------------------------------------
  #
  def normalization_factor(self, spectrum, stoppable = tkutil.Not_Stoppable()):

    if self.spectrum_normalization_factors.has_key(spectrum):
      return self.spectrum_normalization_factors[spectrum]

    spectrum_sum = 0
    corma_sum = 0
    progress_message = 'normalizing ' + os.path.basename(self.corma_path)
    stoppable.stoppable_loop(progress_message, 200)
    for peak in spectrum.peak_list():
      stoppable.check_for_stop()
      if peak.is_assigned and peak.volume != None:
        i = self.predicted_intensity(peak)
        if i:
          spectrum_sum = spectrum_sum + abs(peak.volume)
          corma_sum = corma_sum + i

    if corma_sum > 0 and spectrum_sum > 0:
      factor = spectrum_sum / corma_sum
    else:
      factor = 1

    self.spectrum_normalization_factors[spectrum] = factor

    return factor

  # ---------------------------------------------------------------------------
  #
  def predicted_intensity(self, peak):

    if peak.is_assigned:
      res = noesy.proton_resonances(peak)
      translate = self.atom_translations
      return self.intensity(translate.resonance_number_atom(res[0]),
                            translate.resonance_number_atom(res[1]))
    return None

  # ---------------------------------------------------------------------------
  #
  def intensity(self, num_atom_1, num_atom_2):

    try:
      return self.intensity_table[(num_atom_1, num_atom_2)]
    except KeyError:
      return None

# -----------------------------------------------------------------------------
#
def read_intensities(corma_path, stoppable):

  corma_file = open(corma_path, 'r')
  lines = corma_file.readlines()
  corma_file.close()

  intensities = {}
  stoppable.stoppable_loop('reading ' + os.path.basename(corma_path), 100)
  for line in skip_header_lines(lines):
    stoppable.check_for_stop()
    intensity_spec = parse_corma_line(line)
    if intensity_spec:
      n1, atom1, n2, atom2, intensity = intensity_spec
      na1 = (n1, atom1)
      na2 = (n2, atom2)
      intensities[(na1, na2)] = intensity
      intensities[(na2, na1)] = intensity

  return intensities

# -----------------------------------------------------------------------------
#
def skip_header_lines(lines):
  for k in range(len(lines)):
    if lines[k][:5] == 'ATOM1':
      return lines[k+1:]
  return lines

# -----------------------------------------------------------------------------
# Return n1, atom1, n2, atom2, intensity
#
def parse_corma_line(line):

  atom1 = string.strip(line[0:4])
  n1 = string.atoi(line[4:7])
  atom2 = string.strip(line[8:12])
  n2 = string.atoi(line[12:15])
  intensity = string.atof(line[35:45])

  return n1, atom1, n2, atom2, intensity
