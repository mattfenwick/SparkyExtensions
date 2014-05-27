# -----------------------------------------------------------------------------
# Use structure atom distances to help fixup assignments.  For example,
# find possible assignments for NOE peaks where atoms are within 5 angstroms
# and resonances are within .03 ppm.  Or find all proton pairs within 5
# angstroms for which there is no assigned peak.
#
import Tkinter
import types

import atoms
import noesy
import pdb
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
class assignment_distance_dialog(tkutil.Dialog, tkutil.Stoppable):

  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):

    self.session = session
    self.selection_notice = None

    tkutil.Dialog.__init__(self, session.tk, 'Assignment Distances')

    self.top.bind('<Destroy>', self.window_destroyed_cb, 1)

    self.pdb_paths = tkutil.file_choices(self.top, 'PDB files: ', 'pdb')
    self.pdb_paths.frame.pack(side = 'top', anchor = 'w', fill = 'x')

    self.spectrum_choice = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    self.spectrum_choice.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice.add_callback(self.spectrum_cb)

    er = tkutil.entry_row(self.top, 'PPM tolerance: ',
		       ('w1', '.01', 4), ('w2', '.01', 4), ('w3', '.01', 4))
    self.ppm_range = er.variables
    self.w3_range_widget = er.entries[2].frame
    er.frame.pack(side = 'top', anchor = 'w')

    self.line_format = '%15s %s %7s %s'

    self.spectrum_cb(self.spectrum_choice.get())

    e = tkutil.entry_field(self.top, 'Max atom distance: ', '', 5)
    self.max_dist = e.variable
    e.frame.pack(side = 'top', anchor = 'w')

    tchoices = ('Assignments with far atoms',
	       'Peaks with multiple assignments',
	       'Close atoms with no peak',
	       'Assignments for unassigned peaks',
	       'Unassignable peaks',
	       'Assignments for selected peaks')
    initial = tchoices[5]
    self.show_type = tkutil.option_menu(self.top, 'Show: ', tchoices, initial)
    self.show_type.frame.pack(side = 'top', anchor = 'w')

    dchoices = ('shortest', 'all', 'min, ave, max')
    self.show_dist = tkutil.option_menu(self.top, 'Show model distances: ', dchoices)
    self.show_dist.frame.pack(side = 'top', anchor = 'w')

    pl = tkutil.scrolling_list(self.top, '', 5)
    pl.frame.pack(side = 'top', fill = 'both', expand = 1)
    pl.listbox.bind('<ButtonRelease-1>', self.select_peak_or_assignment_cb)
    pl.listbox.bind('<ButtonRelease-2>', self.goto_peak_or_assignment_cb)
    pl.listbox.bind('<Double-ButtonRelease-1>',
                    self.goto_peak_or_assignment_cb)
    self.peak_list = pl

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'nw')

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Save', self.peak_list.save_cb),
			   ('Stop', self.stop_cb),
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session,
                                                   'AssignmentDistance')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

    self.settings = self.get_settings()

  # ---------------------------------------------------------------------------
  #
  def window_destroyed_cb(self, event):

    self.remove_selection_callback()

  # ---------------------------------------------------------------------------
  #
  def close_cb(self):

    self.remove_selection_callback()
    tkutil.Dialog.close_cb(self)

  # ---------------------------------------------------------------------------
  #
  def remove_selection_callback(self):
    
    if self.selection_notice != None:
      if sparky.object_exists(self.session):
        self.session.dont_notify_me(self.selection_notice)
      self.selection_notice = None

  # ---------------------------------------------------------------------------
  #
  def spectrum_cb(self, name):

    spectrum = sputil.name_to_spectrum(name, self.session)
    if spectrum == None:
      return

    if spectrum.dimension == 3:
      self.w3_range_widget.pack(side = 'left', anchor = 'w')
      self.line_format = '%20s %s %7s %s'
    else:
      self.w3_range_widget.pack_forget()
      self.line_format = '%15s %s %7s %s'

    default_ppm_range = {'1H':.02, '13C':.2, '15N':.2}
    for a in range(spectrum.dimension):
      nucleus = spectrum.nuclei[a]
      if default_ppm_range.has_key(nucleus):
        ppm_range = default_ppm_range[nucleus]
      else:
        ppm_range = .02
      self.ppm_range[a].set('%.2f' % ppm_range)

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    s = self.get_settings()
    self.settings = s
    
    self.models = self.get_models(s.pdb_paths)

    self.peak_list.spectrum = s.spectrum

    if s.show_type == 'Assignments with far atoms':
      if s.max_distance != None:
        self.stoppable_call(self.show_peaks,
                            self.show_far_atom_peak,
                            'excessive distance peaks')
    elif s.show_type == 'Peaks with multiple assignments':
      self.stoppable_call(self.show_peaks,
			  self.show_multiple_assignments,
			  'multiply assignable peaks')
    elif s.show_type == 'Close atoms with no peak':
      self.stoppable_call(self.show_missing_assignments)
    elif s.show_type == 'Assignments for unassigned peaks':
      self.stoppable_call(self.show_peaks,
			  self.show_assignable_unassigned_peak,
			  'assignable unassigned peaks')
    elif s.show_type == 'Unassignable peaks':
      self.stoppable_call(self.show_peaks,
			  self.show_unassignable_unassigned_peak,
			  'unassignable unassigned peaks')
    elif s.show_type == 'Assignments for selected peaks':
      if self.selection_notice == None:
	self.selection_notice = self.session.notify_me('selection changed',
                                        self.show_selected_peak_assignments)
      self.show_selected_peak_assignments()
    if (self.selection_notice and
	s.show_type != 'Assignments for selected peaks'):
      self.remove_selection_callback()

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    settings = pyutil.generic_class()
    settings.spectrum = self.spectrum_choice.spectrum()
    settings.noesy_hsqc = noesy.is_noesy_hsqc(settings.spectrum)
    settings.pdb_paths = list(self.pdb_paths.path_list)
    settings.max_distance = pyutil.string_to_float(self.max_dist.get())
    if settings.spectrum:
      dim = settings.spectrum.dimension
      settings.ppm_range = tkutil.float_variable_values(self.ppm_range)[:dim]
    else:
      settings.ppm_range = None
    settings.show_type = self.show_type.get()
    settings.show_dist = self.show_dist.get()
    
    return settings

  # ---------------------------------------------------------------------------
  #
  def get_models(self, pdb_paths):

    models = []
    bad_paths = ''
    for pdb_path in pdb_paths:
      model = pdb.model(self.session, pdb_path)
      if model == None:
        bad_paths = bad_paths + pdb_path + '\n'
      else:
        models.append(model)
    if bad_paths:
      self.progress_report("Couldn't open\n" + bad_paths)
    return models

  # ---------------------------------------------------------------------------
  #
  def select_peak_or_assignment_cb(self, event):

    pora = self.peak_list.event_line_data(event)
    if type(pora) == types.InstanceType:
      sputil.select_peak(pora)
    elif type(pora) == types.TupleType or type(pora) == types.ListType:
      sputil.select_peak(self.settings.spectrum.find_peak(pora))
      
  # ---------------------------------------------------------------------------
  #
  def goto_peak_or_assignment_cb(self, event):

    pora = self.peak_list.event_line_data(event)
    if type(pora) == types.InstanceType:
      sputil.show_peak(pora)
    elif type(pora) == types.TupleType or type(pora) == types.ListType:
      sputil.show_assignment(pora, self.settings.spectrum)

  # ---------------------------------------------------------------------------
  #
  def show_peaks(self, show_peak, heading, peaks = None):

    self.peak_list.clear()

    if peaks == None:
      if self.settings.spectrum:
        peaks = self.settings.spectrum.peak_list()
      else:
        peaks = []

    shown = 0
    self.stoppable_loop('peaks', 50)
    for peak in peaks:
      self.check_for_stop()
      if show_peak(peak):
        shown = shown + 1

    self.peak_list.heading['text'] = ('%d %s\n' % (shown, heading)
				      + '  ' + self.line_format %
				      ('assignment', self.distance_heading(),
                                       'S/N', '      offset        '))

  # ---------------------------------------------------------------------------
  #
  def show_far_atom_peak(self, peak):

    dist = self.shortest_distance(peak.resonances())
    return (dist != None and
	    dist > self.settings.max_distance and
	    self.show_alternative_assignments(peak))

  # ---------------------------------------------------------------------------
  #
  def show_multiple_assignments(self, peak):

    return self.show_alternative_assignments(peak, 2)

  # ---------------------------------------------------------------------------
  #
  def show_assignable_unassigned_peak(self, peak):

    return not peak.is_assigned and self.show_alternative_assignments(peak, 1)

  # ---------------------------------------------------------------------------
  #
  def show_unassignable_unassigned_peak(self, peak):

    if peak.is_assigned:
      return 0
    alist = self.possible_assignments(peak)
    if len(alist) > 0:
      return 0
    self.peak_list.append(self.peak_format(peak), peak)
    return 1

  # ---------------------------------------------------------------------------
  #
  def show_missing_assignments(self):

    self.peak_list.clear()

    spectrum = self.settings.spectrum
    if spectrum == None:
      return

    if self.settings.max_distance == None or len(self.models) == 0:
      return
    
    mol = spectrum.molecule
    atoms = sputil.hydrogen_atoms(mol)

    missing = 0
    self.stoppable_loop('atoms', 1)
    for atom in atoms:
      self.check_for_stop()
      missing = missing + self.show_missing_atom_assignments(atom, atoms, mol)

    self.peak_list.heading['text'] = ('%d missing peaks\n' % missing
				      + '  ' + self.line_format %
				      ('assignment', self.distance_heading(),
                                       'S/N', '   frequency       '))

  # ---------------------------------------------------------------------------
  #
  def show_missing_atom_assignments(self, atom, atoms, molecule):

    spectrum = self.settings.spectrum
    if spectrum == None:
      return
    
    max_distance = self.settings.max_distance
    missing = 0
    close_list = close_atoms(atom, atoms, molecule, self.models, max_distance)
    for close_atom in close_list:
	if close_atom != atom:
	  assignment = self.missing_assignment(atom, close_atom, spectrum)
	  if assignment and not spectrum.find_peak(assignment):
	    line = self.missing_peak_format(assignment)
	    self.peak_list.append(line, assignment)
	    missing = missing + 1
    return missing

  # ---------------------------------------------------------------------------
  #
  def missing_assignment(self, atom1, atom2, spectrum):

    hres = noesy.atom_assignment(spectrum.condition, (atom1, atom2))
    if self.settings.noesy_hsqc:
      return noesy.extend_noesy_assignment(spectrum, hres)
    return hres
      
  # ---------------------------------------------------------------------------
  #
  def show_selected_peak_assignments(self):

    spectrum = self.settings.spectrum
    if spectrum == None:
      return

    #
    # If the spectrum is deleted this will remove the peak selection
    # callback.  This suppresses errors that would be displayed on every
    # peak selection.  Should be notified about spectrum delete and
    # update appropriately instead.
    #
    if not sparky.object_exists(spectrum):
      self.remove_selection_callback()
      
    self.stoppable_call(self.show_peaks,
			self.show_alternative_assignments, 'selected peaks',
			spectrum.selected_peaks())

  # ---------------------------------------------------------------------------
  #
  def show_alternative_assignments(self, peak, min_assignments = 0):

    alist = self.possible_assignments(peak)
    if len(alist) < min_assignments:
      return

    alist = filter(lambda a, pa = peak.resonances(): a != pa, alist)

    if len(alist) + 1 < min_assignments:
      return 0

    self.peak_list.append(self.peak_format(peak), peak)
    alist = self.sort_alternative_assignments(peak, alist)
    for a in alist:
      line = self.alternate_assignment_format(a, peak)
      self.peak_list.append(line, a)

    return 1

  # ---------------------------------------------------------------------------
  #
  def possible_assignments(self, peak):

    max_dist = self.settings.max_distance
    if max_dist == None or len(self.models) == 0:
      alist = noesy.nearby_noesy_assignments(peak.spectrum, peak.position,
                                             self.settings.ppm_range)
    else:
      alist = noesy.close_noesy_assignments(peak.spectrum, peak.position,
                                            self.settings.ppm_range,
                                            self.models, max_dist)
    return alist

  # ---------------------------------------------------------------------------
  # Sort assigment lists by frequency offset from peak position.
  # The sum of squares of frequency offsets along each axis normalized
  # by the ppm range used along that axis gives the offset.
  #
  def sort_alternative_assignments(self, peak, alist):

    dim = peak.spectrum.dimension
    pfreq = peak.frequency
    scale = self.settings.ppm_range

    offsets = {}
    for assignment in alist:
      afreq = pyutil.attribute_values(assignment, 'frequency')
      offset2 = 0
      for k in range(dim):
        diff = afreq[k] - pfreq[k]
        if scale[k] != 0:
          w = diff / scale[k]
          offset2 = offset2 + w*w
      offsets[assignment] = offset2
      
    return pyutil.sort_keys_by_value(offsets)

  # ---------------------------------------------------------------------------
  #
  def peak_format(self, peak):

    name = peak.assignment
    resonances  = peak.resonances()
    distance = self.distance_format(resonances)
    strength = '%7.1f' % (sputil.peak_height(peak) / peak.spectrum.noise)
    offset = sputil.resonance_offset_string(peak.frequency, resonances)

    return '  ' + self.line_format % (name, distance, strength, offset)

  # ---------------------------------------------------------------------------
  #
  def alternate_assignment_format(self, assignment, peak):

    name = sputil.assignment_name(assignment)
    distance = self.distance_format(assignment)
    strength = ''
    offset = sputil.resonance_offset_string(peak.frequency, assignment)

    return 'a ' + self.line_format % (name, distance, strength, offset)

  # ---------------------------------------------------------------------------
  #
  def missing_peak_format(self, assignment):

    if self.settings.spectrum == None:
      return ''

    name = sputil.assignment_name(assignment)
    distance = self.distance_format(assignment)
    spectrum = self.settings.spectrum
    freq = sputil.assignment_position(assignment, spectrum)
    strength = '%7.1f' % (spectrum.data_height(freq) / spectrum.noise)
    frequency = pyutil.sequence_string(freq, ' %7.3f')

    return 'm ' + self.line_format % (name, distance, strength, frequency)

  # ---------------------------------------------------------------------------
  #
  def shortest_distance(self, assignment):

    distances = self.assignment_distances(assignment)
    distances = filter(lambda d: d != None, distances)
    if len(distances) == 0:
      return None
    return min(distances)
  
  # ---------------------------------------------------------------------------
  #
  def distance_format(self, assignment):

    if self.settings.show_dist == 'shortest':
      d = self.shortest_distance(assignment)
      dstring = self.distance_string(d)
    elif self.settings.show_dist == 'all':
      distances = self.assignment_distances(assignment)
      dstring = ''
      for d in distances:
        dstring = dstring + self.distance_string(d)
    elif self.settings.show_dist == 'min, ave, max':
      distances = self.assignment_distances(assignment)
      distances = filter(lambda d: d != None, distances)
      min_d = pyutil.minimum(distances)
      ave_d = pyutil.average(distances)
      max_d = pyutil.maximum(distances)
      dstring = (self.distance_string(min_d) +
                 self.distance_string(ave_d) +
                 self.distance_string(max_d))

    return dstring

  # ---------------------------------------------------------------------------
  #
  def distance_string(self, dist):

    if dist == None:
      return ' %5s' % ''

    return ' %5.2f' % dist

  # ---------------------------------------------------------------------------
  #
  def distance_heading(self):
    
    if self.settings.show_dist == 'shortest':
      dheading = ' %5s' % 'dist'
    elif self.settings.show_dist == 'all':
      dformat = '%' + ('%d' % (6 * len(self.models))) + 's'
      dheading = dformat % 'dist'
    elif self.settings.show_dist == 'min, ave, max':
      dheading = '%18s' % self.settings.show_dist
    return dheading
  
  # ---------------------------------------------------------------------------
  #
  def assignment_distances(self, assignment):

    spectrum = self.settings.spectrum
    if spectrum == None:
      return []
    
    if self.settings.noesy_hsqc:
      a1, aCN, a2 = noesy.noesy_hsqc_axes(spectrum)
    else:
      a1 = 0
      a2 = 1

    r1 = assignment[a1]
    r2 = assignment[a2]
    distances = []
    if r1 and r2:
      for model in self.models:
        dist = model.minimum_distance(r1.atom, r2.atom, spectrum.molecule)
        distances.append(dist)

    return distances

# -----------------------------------------------------------------------------
#
def close_atoms(atom, atoms, molecule, pdb_models, max_distance):

  atom_list = []
  for a in atoms:
    for model in pdb_models:
      d = model.minimum_distance(atom, a, molecule)
      if d != None and d <= max_distance:
        atom_list.append(a)
        break

  return atom_list

# -----------------------------------------------------------------------------
#
def show_dialog(session):
  sputil.the_dialog(assignment_distance_dialog,session).show_window(1)
