# -----------------------------------------------------------------------------
# Define expected peak sets used for guessing assignments.
#
import string

import atomnames
import axes
import pyutil
import sequence
import sputil

# -----------------------------------------------------------------------------
# Manage sets of expected peaks for multiple spectra.
#
class assignment_system:

  def __init__(self, assignable_spectra):

    self.assignable_spectra = assignable_spectra

    if assignable_spectra:
      self.sequence = assignable_spectra[0].sequence
    else:
      self.sequence = None
      
    self.resonance_to_expected_peaks = \
      self.resonance_to_expected_peaks_table(assignable_spectra)

    self.assignable_resonances = self.assignable_resonance_list()
  
  # ---------------------------------------------------------------------------
  #
  def resonance_to_expected_peaks_table(self, asp_list):

    r2ep = {}

    if self.sequence:
      for r in self.sequence.resonances:
        r2ep[r] = {}
        
    for asp in asp_list:
      for p in asp.expected_peaks:
        for r in p.resonances:
          r2ep[r][p] = 1

    eptable = {}
    for r in r2ep.keys():
      eptable[r] = r2ep[r].keys()

    return eptable
  
  # ---------------------------------------------------------------------------
  #
  def assignable_resonance_list(self):

    res = []
    if self.sequence:
      for r in self.sequence.resonances:
        if self.resonance_to_expected_peaks[r]:
          res.append(r)

    return res
    
  # ---------------------------------------------------------------------------
  #
  def reread_data_peaks(self):

    for asp in self.assignable_spectra:
      asp.reread_data_peaks()
      
# -----------------------------------------------------------------------------
# Manage expected peaks and real peaks for spectrum.
# Subclasses for each type of spectrum know how
# to create a list of all expected peaks.
#
class assignable_spectrum:

  def __init__(self, spectrum, sequence, expected_peaks, tolerances):

    self.sequence = sequence
    self.spectrum = spectrum
    self.tolerances = tolerances
    self.data_peaks = spectrum.peak_list()
    self.expected_peaks = expected_peaks
    
    for p in expected_peaks:
      p.peak_set = self

    a2ep = {}
    for p in expected_peaks:
      a2ep[p.resonances] = p
    self.assignment_to_expected_peak = a2ep

    #
    # Binned real peaks for fast search for nearby peaks
    #
    self.peak_tables = {}
    
  # ---------------------------------------------------------------------------
  # Return peaks matching non-None components of frequency to within tolerances
  #
  def nearby_peaks(self, frequency, stoppable):

    axes = self.search_axes(frequency)
    if not axes:
      return []
    
    f = pyutil.subsequence(frequency, axes)
    if not self.peak_tables.has_key(axes):
      stoppable.progress_report('Clustering %s peaks' % self.spectrum.name)
      self.peak_tables[axes] = self.peak_table(axes)
      stoppable.progress_report('')

    return self.peak_tables[axes].nearby_objects(f)
    
  # ---------------------------------------------------------------------------
  #
  def peak_table(self, axes):

    range = pyutil.subsequence(self.tolerances, axes)
    c = pyutil.cluster(range)
    for p in self.data_peaks:
      f = pyutil.subsequence(p.frequency, axes)
      c.add_point(f, p)
    return c
    
  # ---------------------------------------------------------------------------
  #
  def search_axes(self, frequency):

    axes = []
    for a in range(len(frequency)):
      if frequency[a] != None:
        axes.append(a)
    return tuple(axes)
    
  # ---------------------------------------------------------------------------
  #
  def expected_peak_for_assigned_data_peak(self, data_peak):

    if not data_peak.is_assigned:
      return None

    a = self.sequence.peak_resonances(data_peak)
    if self.assignment_to_expected_peak.has_key(a):
      return self.assignment_to_expected_peak[a]

    return None
    
  # ---------------------------------------------------------------------------
  #
  def reread_data_peaks(self):

    self.data_peaks = self.spectrum.peak_list()
    self.peak_tables = {}
    
# -----------------------------------------------------------------------------
#
class expected_peak:

  def __init__(self, resonances, sign):

    self.peak_set = None
    self.sign = sign
    self.resonances = resonances

  # ---------------------------------------------------------------------------
  #
  def assignment_text(self):

    assignment = ''
    last_group = None
    for r in self.resonances:
      group = r.symbol + repr(r.number)
      atom = r.atom_name
      if assignment:
        assignment = assignment + '-'
      if group == last_group:
        assignment = assignment + atom
      else:
        assignment = assignment + group + atom
      last_group = group
    return assignment

  # ---------------------------------------------------------------------------
  #
  def matching_data_peaks(self, freq, stoppable):
                                            
    dpeaks = self.peak_set.nearby_peaks(freq, stoppable)
    dpeaks = filter(self.is_sign_correct, dpeaks)
    return dpeaks

  # ---------------------------------------------------------------------------
  #
  def is_sign_correct(self, dpeak):
    
    if self.sign > 0:
      return sputil.peak_height(dpeak) > 0
    elif self.sign < 0:
      return sputil.peak_height(dpeak) < 0
    return 1
    
  # ---------------------------------------------------------------------------
  #
  def are_resonances_assigned(self, rshifts):

    for r in self.resonances:
      if not rshifts.has_key(r):
        return 0
    return 1

  # ---------------------------------------------------------------------------
  #
  def resonance_axes(self, resonance):

    axes = []
    for axis in range(len(self.resonances)):
      if self.resonances[axis] == resonance:
        axes.append(axis)
    return tuple(axes)

  # ---------------------------------------------------------------------------
  #
  def assign(self, data_peak):

    # Make peak assignment
    rlist = self.resonances
    for axis in range(len(rlist)):
      r = rlist[axis]
      group_name = r.symbol + repr(r.number)
      data_peak.assign(axis, group_name, r.atom_name)

# -----------------------------------------------------------------------------
#
def atom_table(*salist):

  t = {}
  for symbols, atom_name in salist:
    for sym in symbols:
      pyutil.table_push(t, sym, atom_name)
  return t

# -----------------------------------------------------------------------------
#
def combine_atom_tables(*atables):

  at = {}
  for atable in atables:
    for sym, alist in atable.items():
      if at.has_key(sym):
        at[sym] = at[sym] + alist
      else:
        at[sym] = alist
  return at

# -----------------------------------------------------------------------------
#
atom_tables = {
  'H': atom_table(('ACDEFGHIKLMNQRSTVWY', 'H')),
  'N': atom_table(('ACDEFGHIKLMNPQRSTVWY', 'N')),
  'C': atom_table(('ACDEFGHIKLMNPQRSTVWY', 'C')),
  'CA': atom_table(('ACDEFGHIKLMNPQRSTVWY', 'CA')),
  'CB': atom_table(('ACDEFHIKLMNPQRSTVWY', 'CB')),
  'CG': atom_table(('DEFHKLMNPQRWY', 'CG')),
  'CG1': atom_table(('VI', 'CG1')),
  'CG2': atom_table(('VIT', 'CG2')),
  'CD': atom_table(('KPQR', 'CD')),
  'CD1': atom_table(('LI', 'CD1')),
  'CD2': atom_table(('L', 'CD2')),
  'CD-ring': atom_table(('FHWY', 'CD1'), ('FHWY', 'CD2')),
  'CEtocsy': atom_table(('K', 'CE')),
  'HA': atom_table(('ACDEFHIKLMNPQRSTVWY', 'HA'),
                   ('G', 'HA2'), ('G', 'HA3')),
  'HB': atom_table(('CDEFHKLMNPQRSWY', 'HB2'),
                   ('CDEFHKLMNPQRSWY', 'HB3'),
                   ('A', 'MB'), ('ITV', 'HB')),
  'HGtocsy': atom_table(('EKMPQR', 'HG2'), ('EKMPQR', 'HG3'), ('L', 'HG')),
  'HG1': atom_table(('I' ,'HG12'), ('I' ,'HG13'), ('V', 'MG1')),
  'HG2': atom_table(('VIT', 'MG2')),
  'HD': atom_table(('KPR', 'HD2'), ('KPR', 'HD3')),
  'HD1tocsy': atom_table(('LI', 'MD1')),
  'HD2tocsy': atom_table(('L', 'MD2'), ('N', 'HD21'), ('N', 'HD22')),
  'HD-ring': atom_table(('FHWY', 'HD1'), ('FHY', 'HD2')),
  'HEtocsy': atom_table(('K', 'HE2'), ('K', 'HE3')),
  'HE-ring': atom_table(('FHWY', 'HE1'), ('FY', 'HE2')),
  'HZ': atom_table(('K', 'MZ')),
  'HZ-ring': atom_table(('F', 'HZ'), ('W', 'HZ2'), ('W', 'HZ3')),
  'HH': atom_table(('R', 'HH11'), ('R', 'HH12'), ('R', 'HH21'), ('R', 'HH22'),
                   ('Y', 'HH')),
  'HH-ring': atom_table(('W', 'HH2')),
  }
atom_tables['CACB'] = combine_atom_tables(atom_tables['CA'], atom_tables['CB'])
atom_tables['HAHB'] = combine_atom_tables(atom_tables['HA'], atom_tables['HB'])
atom_tables['Cspinsys'] = combine_atom_tables(atom_tables['CA'],
                                              atom_tables['CB'],
                                              atom_tables['CG'],
                                              atom_tables['CG1'],
                                              atom_tables['CG2'],
                                              atom_tables['CD'],
                                              atom_tables['CD1'],
                                              atom_tables['CD2'],
                                              atom_table(('K', 'CE')),
                                              atom_table(('W', 'CD2')))
atom_tables['Htocsy'] = combine_atom_tables(atom_tables['HA'],
                                            atom_tables['HB'],
                                            atom_tables['HGtocsy'],
                                            atom_tables['HG1'],
                                            atom_tables['HG2'],
                                            atom_tables['HD'],
                                            atom_tables['HD1tocsy'],
                                            atom_tables['HD2tocsy'],
                                            atom_tables['HEtocsy'])

# -----------------------------------------------------------------------------
#
expected_peak_descriptions = {
  'n15hsqc':            ['H N'],
  'hnco':               ['H N C-1'],
  'hncaco':             ['H N C', 'H N C-1'],
  'hnca':               ['H N CA', 'H N CA-1'],
  'hncoca':             ['H N CA-1'],
  'hncacb':             ['H N CACB', 'H N CACB-1'],
  'cbcaconh':           ['H N CACB-1'],
  'cconh':              ['H N Cspinsys-1'],
  'hnha':               ['H N HA', 'H N HA-1'],
  'haconh':             ['H N HA-1'],
  'hbhaconh':           ['H N HA-1', 'H N HB-1'],
  'c13hsqc-hahb':       ['CA HA', 'CB HB'],
  'hcchtocsy-hahb':     ['HA CA HAHB', 'HB CB HAHB'],
  'hcchtocsy':          ['HA CA Htocsy',
                         'HB CB Htocsy',
                         'HGtocsy CG Htocsy',
                         'HG1 CG1 Htocsy',
                         'HG2 CG2 Htocsy',
                         'HD CD Htocsy',
                         'HD1tocsy CD1 Htocsy',
                         'HD2tocsy CD2 Htocsy',
                         'HEtocsy CEtocsy Htocsy'],

  'n15noesy-hanh':      ['H N H', 'HA N H', 'HA-1 N H'],
  'c13noesy-hacah':     ['HA CA HA', 'HA CA H', 'HA-1 CA-1 H',],
  }

# -----------------------------------------------------------------------------
# Parse expected peak patterns producing a list of expected peaks for a
# given residue sequence.
#
def expected_peaks_from_pattern(pat, pat_axes, seq):

  atomspecs = expected_peaks_specifier(pat)
  atomspecs = pyutil.unpermute(atomspecs, pat_axes)
  epeaks = specified_expected_peaks(atomspecs, seq)
  return epeaks

# -----------------------------------------------------------------------------
# Parse expected peak patterns such as 'H N HA-1' producing a list
# of expected peaks for a given residue sequence.
#
def expected_peaks_specifier(pattern):

  atoms = string.split(pattern)

  #
  # Remove offset suffix.
  #
  atomnames = []
  offsets = []
  for atom in atoms:
    if atom[-2:] == '-1':
      offsets.append(-1)
      atomnames.append(atom[:-2])
    else:
      offsets.append(0)
      atomnames.append(atom)

  #
  # Lookup atom tables by name (eg HAHB) mapping residue symbol to atom names
  #
  atomtables = []
  for aname in atomnames:
    atable = atom_tables[aname]
    atomtables.append(atable)

  atomspecs = map(lambda atable, offset: (atable, offset), atomtables, offsets)

  return atomspecs

# -----------------------------------------------------------------------------
#
def specified_expected_peaks(atomspecs, sequence):

  epeaks = []
  n2s = sequence.number_to_symbol
  for number, symbol in n2s.items():
    repeaks = residue_expected_peaks(atomspecs, sequence, number, symbol)
    epeaks = epeaks + repeaks
  return epeaks

# -----------------------------------------------------------------------------
#
def residue_expected_peaks(atomspecs, sequence, number, symbol):

  reslists = []
  n2s = sequence.number_to_symbol
  for atomtable, offset in atomspecs:
    n = number + offset
    if n2s.has_key(n):
      s = n2s[n]
      resonances = expected_resonances(n, s, atomtable, sequence)
      reslists.append(resonances)
    else:
      reslists.append([])
  assignments = pyutil.product_tuples(reslists)
  epeaks = map(lambda a: expected_peak(a, sign = 0), assignments)
  return epeaks
  
# -----------------------------------------------------------------------------
#
def expected_resonances(num, group_symbol, atom_table, seq):

  if not atom_table.has_key(group_symbol):
    return []
  atom_names = atom_table[group_symbol]
  atom_res = lambda a, n=num, s=group_symbol, seq=seq: seq.resonance(n,s,a)
  resonances = map(atom_res, atom_names)
  return resonances

# -----------------------------------------------------------------------------
# Return an ordered list of nucleus types for an expected peak pattern.
#
def pattern_nuclei(pattern):

  nuclei = []
  atomspecs = expected_peaks_specifier(pattern)
  for atable, offset in atomspecs:
    aname = atable.values()[0][0]
    if aname[0] == 'C':         nuclei.append('13C')
    elif aname[0] == 'N':       nuclei.append('15N')
    else:                       nuclei.append('1H')
  return tuple(nuclei)

# -----------------------------------------------------------------------------
#
def default_spectrum_pattern_name(spectrum):

  spectrum_name = string.lower(spectrum.name)
  pattern_names = map(string.lower, expected_peak_descriptions.keys())
  pat_name = pyutil.closest_string(spectrum_name, pattern_names)
  return pat_name
  
# -----------------------------------------------------------------------------
#
def remember_pattern(spectrum, pattern_name, pattern_axes):
  
  axes = ''
  for a in pattern_axes:
    axes = axes + '%d ' % a
  axes = axes[:-1]
  spectrum.save_value('peak_pattern_name', pattern_name)
  spectrum.save_value('peak_pattern_axes', axes)
  
# -----------------------------------------------------------------------------
#
def recall_pattern(spectrum):

  pat_name = spectrum.saved_value('peak_pattern_name')
  axes_text = spectrum.saved_value('peak_pattern_axes')
  if pat_name and expected_peak_descriptions.has_key(pat_name) and axes_text:
    axes = map(string.atoi, string.split(axes_text))
    return pat_name, axes
  return None, None
  
# -----------------------------------------------------------------------------
#
def assignable_spectrum_from_pattern(spectrum, tolerances,
                                     pattern_name, pattern_axes, stoppable):

  remember_pattern(spectrum, pattern_name, pattern_axes)
  seq = sequence.molecule_sequence(spectrum.molecule)
  pattern_list = expected_peak_descriptions[pattern_name]

  epeaks = []
  for pat in pattern_list:
    stoppable.progress_report(pattern_name + ' pattern ' + pat)
    patpeaks = expected_peaks_from_pattern(pat, pattern_axes, seq)
    epeaks = epeaks + patpeaks

  asp = assignable_spectrum(spectrum, seq, epeaks, tolerances)

  asp.expected_peak_pattern_name = pattern_name
  asp.pattern_axis_order = pattern_axes

  return asp

