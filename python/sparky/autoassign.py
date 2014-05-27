# -----------------------------------------------------------------------------
# Setup input, run, and read output for AutoAssign, an automatic assignment
# program.  This is done by writing peak lists and spectrum list files needed,
# starting an AutoAssign subprocess, reading AutoAssign peak assignments,
# and applying assignments to peaks.
#

import os
import socket
import string
import time
import Tkinter
import types

import assigngraph
import atomnames
import axes
import expectedpeaks
import pyutil
import sequence
import sparky
import sputil
import subprocess
import tkutil

# -----------------------------------------------------------------------------
#
default_client_executable = 'AsciiClient'
default_server_executable = 'AutoServer'
default_server_port = '8050'

# -----------------------------------------------------------------------------
#

# default_assignment_script = 'Execute (Submit Batch)\n'

default_assignment_script = (
  'Execute (Submit Batch)\n' +
  'Execute (Incremental Match, CA,  0.99,   10,   0.005)\n' +
  'Execute (Submit Batch)\n' +
  'Execute (Incremental Match, CB,  0.99,   10,   0.005)\n' +
  'Execute (Submit Batch)\n' +
  'Execute (Incremental Match, HA,  0.99,   10,   0.005)\n' +
  'Execute (Submit Batch)\n' +
  'Execute (Incremental Match, CO,  0.99,   10,   0.005)\n' +
  'Execute (Submit Batch)\n'
  )

# -----------------------------------------------------------------------------
# AutoAssign spectrum types
#
spectrum_types = (
      'HSQC',
      'HNCO',
      'HNcaCO',
      'HNCA',
      'HNcoCA',
      'HNCACB',
      'HNcoCACB',
      'HNHA',
      'HNcoHA',
      )
optional_types = ('HNCO', 'HNcaCO', 'HNHA', 'HNcoHA')

# -----------------------------------------------------------------------------
# Spectrum name strings used to choose default spectra for each AutoAssign
# spectrum type.
#
type_aliases = {
      'HSQC':    ('n15hsqc', 'hsqc'),
      'HNCO':    ('hnco',),
      'HNcaCO':  ('hncaco', 'cocanh'),
      'HNCA':    ('hnca',),
      'HNcoCA':  ('hncoca', 'caconh'),
      'HNCACB':  ('hncacb',),
      'HNcoCACB':('cbcaconh', 'hncocacb', 'cbca'),
      'HNHA':    ('hnha',),
      'HNcoHA':  ('haconh', 'hncoha')
      }

# -----------------------------------------------------------------------------
#
class autoassign_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.sparky_session = session
    self.autoassign_session = None

    self.server_exists = 0
    self.server_host = socket.gethostname()
    self.server_port = default_server_port
    self.server_lag = '1'
    self.server_executable = default_server_executable
    self.client_executable = default_client_executable

    self.tsp_list = self.default_spectra()
    self.tolerances = {'HN': .02, 'N15': .3, 'CA': .5, 'CB': .5,
                       '{CA CB }': .5, 'HA': .1, 'CO': .5}
    self.temp_directory = os.path.join(session.project.sparky_directory,
                                       'autoassign')
    
    tkutil.Dialog.__init__(self, session.tk, 'Run AutoAssign')

    sh = Tkinter.Label(self.top, text = 'AutoAssign script:')
    sh.pack(side = 'top', anchor = 'w')
    
    sc = tkutil.scrolling_text(self.top, height = 5)
    sc.frame.pack(side = 'top', anchor = 'w', fill = 'both', expand = 1)
    self.assignment_script = sc.text
    self.assignment_script.insert('end', default_assignment_script)

    ssm = Tkinter.Label(self.top, text = 'Single step mode:')
    ssm.pack(side = 'top', anchor = 'w')

    sb = tkutil.button_row(self.top,
			   ('Start', self.start_autoassign_cb),
                           ('Run line', self.run_line_cb),
                           ('Run selected lines', self.run_selected_cb),
                           ('Show assignments', self.show_assignments_cb),
			   ('Quit', self.quit_autoassign_cb),
			   )
    sb.frame.pack(side = 'top', anchor = 'w')

    oh = Tkinter.Label(self.top, text = 'AutoAssign output:')
    oh.pack(side = 'top', anchor = 'w')
    
    op = tkutil.scrolling_text(self.top, height = 5)
    op.frame.pack(side = 'top', anchor = 'w', fill = 'both', expand = 1)
    self.output_text = op.text
    
    progress_label = Tkinter.Label(self.top, anchor = 'nw', justify = 'left')
    progress_label.pack(side = 'top', anchor = 'w')

    br1 = tkutil.button_row(self.top,
                            ('Spectrum Setup...', self.show_setup_cb),
                            ('Server Setup...', self.show_details_cb),
                            ('Run AutoAssign', self.run_cb),
                            ('Stop', self.stop_cb),
                            )
    br1.frame.pack(side = 'top', anchor = 'w')

    br2 = tkutil.button_row(self.top,
                            ('Write Peak Lists...', self.write_peak_lists_cb),
                            ('Read Shifts...', self.read_shifts_cb),
                            ('Close', self.close_cb),
                            ('Help', sputil.help_cb(session, 'AutoAssign')),
                            )
    br2.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br1.buttons[3])

  # ---------------------------------------------------------------------------
  #
  def default_spectra(self):

    default_phase = ''
    tsp_list = []
    for type in spectrum_types:
      spectrum = self.default_spectrum(type)
      if spectrum:
        tsp_list.append((type, spectrum, default_phase))
    return tsp_list

  # ---------------------------------------------------------------------------
  #
  def default_spectrum(self, type):

    for alias in type_aliases[type]:
      for spectrum in self.sparky_session.project.spectrum_list():
        sname = string.lower(spectrum.name)
        if string.find(sname, alias) >= 0:
          return spectrum
    return None

  # ---------------------------------------------------------------------------
  #
  def show_setup_cb(self):

    setup = sputil.the_dialog(autoassign_setup_dialog, self.sparky_session)
    settings = {'type-spectrum-phase-list': self.tsp_list,
                'tolerance-table': self.tolerances,
                'temp-directory': self.temp_directory}
    setup.set_parent_dialog(self, settings, self.set_spectra)
    setup.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def set_spectra(self, settings):

    self.tsp_list = settings['type-spectrum-phase-list']
    self.tolerances = settings['tolerance-table']
    self.temp_directory = settings['temp-directory']

  # ---------------------------------------------------------------------------
  #
  def show_details_cb(self):

    details = sputil.the_dialog(autoassign_details_dialog, self.sparky_session)
    settings = (self.server_exists, self.server_host,
                self.server_port, self.server_lag,
                self.server_executable, self.client_executable)
    details.set_parent_dialog(self, settings, self.set_details)
    details.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def set_details(self, settings):

    (self.server_exists, self.server_host,
     self.server_port, self.server_lag,
     self.server_executable, self.client_executable) = settings

  # ---------------------------------------------------------------------------
  #
  def write_peak_lists_cb(self):

    self.start_session(write_peak_lists = 1,
                       start_server = 0, start_client = 0)

  # ---------------------------------------------------------------------------
  #
  def read_shifts_cb(self):

    path = tkutil.load_file(self.top,
                            'Open AutoAssign Publication Shifts Table',
                            'autoassign')
    if path:
      f = open(path, 'r')
      lines = f.readlines()
      f.close()
      session = self.start_session(write_peak_lists = 0,
                                   start_server = 0, start_client = 0)
      self.show_assignments(session, lines)
    
  # ---------------------------------------------------------------------------
  #
  def clear_output(self):

    self.output_text.delete('0.0', 'end')
    
  # ---------------------------------------------------------------------------
  #
  def show_output(self, lines):

    for line in lines:
      self.output_text.insert('end', line)
    self.output_text.see('insert')

  # ---------------------------------------------------------------------------
  #
  def run_cb(self):

    if self.autoassign_session:
      self.autoassign_session.end_run()

    start_server = not self.server_exists
    self.autoassign_session = self.start_session(start_server = start_server)
    if self.autoassign_session == None:
      return
    
    assignment_script = self.assignment_script.get('0.0', 'end')
    output = self.autoassign_session.run_script(assignment_script)
    self.show_output(output)

    self.show_assignments(self.autoassign_session)

    self.autoassign_session.end_run()
    self.autoassign_session = None
  
  # ---------------------------------------------------------------------------
  #
  def start_autoassign_cb(self):

    if self.autoassign_session == None:
      start_server = not self.server_exists
      self.autoassign_session = self.start_session(start_server = start_server)
      self.assignment_script.mark_set('insert', '0.0')
      self.assignment_script.focus_set()
      
  # ---------------------------------------------------------------------------
  #
  def run_line_cb(self):

    if self.autoassign_session:
      script = self.assignment_script.get('insert linestart', 'insert lineend')
      output = self.autoassign_session.run_script(script)
      self.show_output(output)
      self.assignment_script.mark_set('insert', 'insert + 1 lines')

  # ---------------------------------------------------------------------------
  #
  def run_selected_cb(self):

    if self.autoassign_session:
      script = ''
      ranges = self.assignment_script.tag_ranges('sel')
      for k in range(0, len(ranges), 2):
        section = self.assignment_script.get(ranges[k], ranges[k+1])
        script = script + section
      output = self.autoassign_session.run_script(script)
      self.show_output(output)
  
  # ---------------------------------------------------------------------------
  #
  def show_assignments_cb(self):

    if self.autoassign_session:
      self.show_assignments(self.autoassign_session)
      
  # ---------------------------------------------------------------------------
  #
  def quit_autoassign_cb(self):

    if self.autoassign_session:
      self.autoassign_session.end_run()
      self.autoassign_session = None
      
  # ---------------------------------------------------------------------------
  #
  def start_session(self, write_peak_lists = 1,
                    start_server = 1, start_client = 1):
    
    if self.tsp_list == None:
      return None

    session = autoassign_session(self.tsp_list, self.tolerances,
                                 self.progress_report, self.sparky_session)

    if write_peak_lists:
      self.progress_report('Writing peak lists')
      session.write_autoassign_input_files(self.tolerances,
                                           self.temp_directory)

    server_port = pyutil.string_to_int(self.server_port, default_server_port)
    if start_server:
      self.progress_report('Running AutoAssign server')
      server_lag = pyutil.string_to_int(self.server_lag, 0)
      session.start_server(self.server_host, server_port,
                           self.server_executable, server_lag)

    if start_client:
      self.progress_report('Running AutoAssign client')
      session.start_client(self.client_executable, self.server_host,
                           server_port)
    
      table_path = os.path.join(self.temp_directory, 'table.aat')
      init_script = 'Execute (Initialize, %s)\n' % table_path

      output = session.run_script(init_script)
      self.show_output(output)

    self.progress_report('')
        
    return session

  # ---------------------------------------------------------------------------
  #
  def show_assignments(self, session, output = None):

    if output == None:
      res_script = 'Examine (List, Chemical Shifts Publish Format)\n'
      output = session.run_script(res_script)
      self.show_output(output)
    
    peak_assignments = session.parse_assignments(output)

    count = 0
    for alist in peak_assignments.values():
      count = count + len(alist)

    if count == 0:
      self.progress_report('No peak assignments made')
    else:
      session.show_peak_assignments(peak_assignments)

# -----------------------------------------------------------------------------
#
class autoassign_setup_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    self.sparky_session = session
    
    tkutil.Settings_Dialog.__init__(self, session.tk, 'AutoAssign Setup')

    sc = self.spectrum_choice_table(self.top)
    sc.pack(side = 'top', anchor = 'w')

    t = tkutil.entry_row(self.top, 'Tolerances (ppm)',
                         ('HN', '', 4),
                         ('N15', '', 4),
                         ('CA', '', 4),
                         ('CB', '', 4),
                         ('HA', '', 4),
                         ('CO', '', 4),
                         )
    t.frame.pack(side = 'top', anchor = 'w')
    self.tolerances = t.entries
 
    td = tkutil.file_field(self.top, 'Temp directory for peak lists: ',
                           'autoassign', browse_button = 0, width = 30)
    td.frame.pack(side = 'top', anchor = 'w')
    self.temp_directory = td
    
    m = Tkinter.Label(self.top, anchor = 'nw', justify = 'left')
    m.pack(side = 'top', anchor = 'w')
    self.message = m

    br = tkutil.button_row(self.top,
                           ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'AutoAssign')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def spectrum_choice_table(self, parent):

    f = Tkinter.Frame(parent, borderwidth = 5)

    self.type_to_spectrum_menu = {}
    self.type_to_phase = {}

    count = 0
    entries_per_column = 5
    row = 1
    column = 0
    for type in spectrum_types:

      column = 4 * (count / entries_per_column)
      row = 1 + (count % entries_per_column)
      
      if row == 1:
        lbl = Tkinter.Label(f, text = '  ')
        lbl.grid(row = 0, column = column)
        lbl = Tkinter.Label(f, text = 'Spectrum')
        lbl.grid(row = 0, column = column + 2)
        lbl = Tkinter.Label(f, text = 'Phase')
        lbl.grid(row = 0, column = column + 3)

      lbl = Tkinter.Label(f, text = type)
      lbl.grid(row = row, column = column + 1, sticky = 'w')

      m = sputil.spectrum_menu(self.sparky_session, f, '', allow_no_choice = 1)
      m.frame.grid(row = row, column = column + 2, sticky = 'w')
      self.type_to_spectrum_menu[type] = m

      p = tkutil.entry_field(f, '', width = 6)
      p.frame.grid(row = row, column = column + 3, sticky = 'w')
      self.type_to_phase[type] = p.variable
      
      count = count + 1

    return f

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    tsp_list = settings['type-spectrum-phase-list']
    if tsp_list:
      types = {}
      for type, spectrum, phase in tsp_list:
        if sparky.object_exists(spectrum):
          self.type_to_spectrum_menu[type].set(spectrum.name)
        self.type_to_phase[type].set(phase)
        types[type] = 1
      for type in self.type_to_spectrum_menu.keys():
        if not types.has_key(type):
          self.type_to_spectrum_menu[type].set('')
      
    ttable = settings['tolerance-table']
    for e in self.tolerances:
      atom_name = e.label['text']
      if ttable.has_key(atom_name):
        new_tol = ttable[atom_name]
        current_tol = pyutil.string_to_float(e.variable.get(), 0)
        if new_tol != current_tol:
          e.variable.set('%.3g' % new_tol)

    self.temp_directory.set(settings['temp-directory'])
    
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):
    
    settings = {'type-spectrum-phase-list': self.type_spectrum_phase_list(),
                'tolerance-table': self.read_tolerances(),
                'temp-directory': self.temp_directory.get()
                }
    return settings
    
  # ---------------------------------------------------------------------------
  #
  def type_spectrum_phase_list(self):

    missing_types = []
    tsp_list = []
    for type in spectrum_types:
      menu = self.type_to_spectrum_menu[type]
      spectrum = menu.spectrum()
      if spectrum:
        phase = self.type_to_phase[type].get()
        tsp_list.append((type, spectrum, phase))
      elif not type in optional_types:
        missing_types.append(type)

    if missing_types:
      types = reduce(lambda n, t: n + t + ' ', missing_types, '')
      self.message['text'] = ('Require spectra ' + types)
      return None

    return tsp_list
      
  # ---------------------------------------------------------------------------
  #
  def read_tolerances(self):

    tolerances = {}
    for e in self.tolerances:
      atom_name = e.label['text']
      tolerance = pyutil.string_to_float(e.variable.get(), 0)
      tolerances[atom_name] = tolerance
    tolerances['{CA CB }'] = min(tolerances['CA'], tolerances['CB'])
    return tolerances

# -----------------------------------------------------------------------------
#
class autoassign_details_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):
  
    tkutil.Settings_Dialog.__init__(self, session.tk, 'AutoAssign Details')

    se = tkutil.checkbutton(self.top,
                            'Use an already running AutoAssign server?', 0)
    se.button.pack(side = 'top', anchor = 'w')
    self.server_exists = se.variable

    hp = tkutil.entry_row(self.top, 'Server on',
                          ('host ', '', 25),
                          (' port ', '', 5),
                          )
    hp.frame.pack(side = 'top', anchor = 'w')
    self.server_host, self.server_port = hp.variables

    sl = tkutil.entry_field(self.top,
			    'Sleep time after server startup (seconds): ',
                            initial = 1, width = 3)
    sl.frame.pack(side = 'top', anchor = 'w')
    self.server_lag = sl.variable

    sp = tkutil.entry_field(self.top, 'Server program ', '', width = 25)
    sp.frame.pack(side = 'top', anchor = 'w')
    self.server_executable = sp.variable

    cp = tkutil.entry_field(self.top, 'Client program ', '', width = 25)
    cp.frame.pack(side = 'top', anchor = 'w')
    self.client_executable = cp.variable

    br = tkutil.button_row(self.top,
                           ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'AutoAssign')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    (server_exists, server_host, server_port,
     server_lag, server_executable, client_executable) = settings
    self.server_exists.set(server_exists)
    self.server_host.set(server_host)
    self.server_port.set(server_port)
    self.server_lag.set(server_lag)
    self.server_executable.set(server_executable)
    self.client_executable.set(client_executable)

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    settings = (self.server_exists.get(), self.server_host.get(),
                self.server_port.get(), self.server_lag.get(),
                self.server_executable.get(), self.client_executable.get())
    return settings

# -----------------------------------------------------------------------------
# Run AutoAssign server and client process, create peak list and spectrum
# table input files, run AutoAssign scripts, parse resonance assignments,
# and guess peak assignments.
#
class autoassign_session:
  
  def __init__(self, tsp_list, tolerances, progress_report, sparky_session):

    self.sparky_session = sparky_session
    self.progress_report = progress_report
    self.initialize_name_tables()
    
    asys = self.autoassign_assignment_system(tsp_list, tolerances)
    self.assignment_system = asys

    self.server_process = None
    self.client_process = None
    
  # ---------------------------------------------------------------------------
  # This blocks and hangs Sparky if client does not send END_TASK.
  # Also if a script line generates more than one END_TASK then
  # output from this script will be given erroneously as output
  # for the next run_script().
  #
  # I could use an self.sparky_session.add_input_callback() and non-blocking
  # i/o set with fcntl to avoid hanging if the END_TASK line doesn't
  # come but it doesn't seem worth the complexity.
  #
  def run_script(self, script):

    if script and script[-1] != '\n':
      script = script + '\n'

    aa_proc = self.client_process

    if aa_proc == None:
      out = self.sparky_session.stderr
      out.write('autoassign.py: AutoAssign client not started.\n')
      return []
    
    if aa_proc.exitted():
      if self.server_process and self.server_process.exitted():
        out = self.sparky_session.stderr
        out.write('autoassign.py: AutoAssign server exitted.\n')
      else:
        out = self.sparky_session.stderr
        out.write('autoassign.py: AutoAssign client exitted.\n')
      return []
      
    aa_proc.to_process.write(script)
    aa_proc.to_process.flush()

    commands = string.split(script, '\n')
    commands = filter(lambda line: line, commands)
    task_count = len(commands)

    return self.read_autoassign_output(task_count)

  # ---------------------------------------------------------------------------
  #
  def read_autoassign_output(self, task_count):
  
    end_task = 'END_TASK\n'
    lines = []
    while task_count > 0:
      line = self.client_process.from_process.readline()
      if line == '':
        break                                      # end of file reached
      lines.append(line)
      if line == end_task:
        task_count = task_count - 1
    return lines

  # ---------------------------------------------------------------------------
  #
  def parse_assignments(self, lines):

    cs_lines = self.chemical_shift_lines(lines)
    asys = self.assignment_system
    rshifts = self.resonance_assignments(asys.sequence, cs_lines)

    peak_assignments = {}
    for asp in asys.assignable_spectra:
      self.progress_report('Inferring peak assignments for ' +
                           asp.spectrum.name)
      peak_assignments[asp] = self.guess_peak_assignments(asp, rshifts)

    return peak_assignments

  # ---------------------------------------------------------------------------
  # Closes pipe to client, waits for client to exit, then kills server.
  #
  def end_run(self):

    aa_proc = self.client_process
    if aa_proc:
      aa_proc.to_process.close()
      code = aa_proc.exit_code()
      if code:
        out = self.sparky_session.stderr
        out.write('%s process %d exit code = %d\n'
                  % (aa_proc.argv[0], aa_proc.process_id, code))

    if self.server_process:
      self.kill_server(self.server_process)
    
  # ---------------------------------------------------------------------------
  #
  def initialize_name_tables(self):
    
    self.type_to_axis_name_table = {
      'HSQC':     {'1H':'HN', '15N':'N15'},
      'HNCO':     {'1H':'HN', '15N':'N15', '13C':'CO'},
      'HNcaCO':   {'1H':'HN', '15N':'N15', '13C':'CO'},
      'HNcoCA':   {'1H':'HN', '15N':'N15', '13C':'CA'},
      'HNCA':     {'1H':'HN', '15N':'N15', '13C':'CA'},
      'HNcoCACB': {'1H':'HN', '15N':'N15', '13C':'{CA CB }'},
      'HNCACB':   {'1H':'HN', '15N':'N15', '13C':'{CA CB }'},
      'HNcoHA':   {'1H':('HN','HA'), '15N':'N15'},
      'HNHA':     {'1H':('HN','HA'), '15N':'N15'},
    }

    self.type_to_pattern_name = {
      'HSQC':    'n15hsqc',
      'HNCO':    'hnco',
      'HNcaCO':  'hncaco',
      'HNCA':    'hnca',
      'HNcoCA':  'hncoca',
      'HNCACB':  'hncacb',
      'HNcoCACB':'cbcaconh',
      'HNHA':    'hnha',
      'HNcoHA':  'haconh',
      }

    self.root_spectrum = 'HSQC'
    self.intra_peak_spectra = ('HSQC', 'HNcaCO', 'HNCA', 'HNCACB', 'HNHA',)
    self.inter_peak_spectra = ('HNCO', 'HNcoCA', 'HNCA', 'HNcoCACB',
                               'HNCACB', 'HNcoHA', 'HNHA',)
    
  # ---------------------------------------------------------------------------
  #
  def autoassign_assignment_system(self, tsp_list, tolerances):

    asp_list = []
    for type, spectrum, phase in tsp_list:
      axis_names = self.autoassign_axis_names(spectrum, type)
      tol = pyutil.table_values(tolerances, axis_names)
      self.progress_report('Calculating expected peaks for ' + spectrum.name)
      pat_name = self.type_to_pattern_name[type]
      if spectrum.dimension == 3:
        pat_axes = axes.amide_axes(spectrum)
      else:
        pat_axes = pyutil.order(('1H', '15N'), spectrum.nuclei)
      asp = expectedpeaks.assignable_spectrum_from_pattern(spectrum, tol,
                                                           pat_name, pat_axes,
                                                           self)
      asp.autoassign_type = type
      asp.autoassign_phase = phase
      asp_list.append(asp)

    return expectedpeaks.assignment_system(asp_list)
    
  # ---------------------------------------------------------------------------
  #
  def autoassign_axis_names(self, spectrum, stype):

    axis_names = []
    n2n = self.type_to_axis_name_table[stype]
    for axis in range(spectrum.dimension):
      nucleus = spectrum.nuclei[axis]
      axis_name = n2n[nucleus]
      if type(axis_name) == types.TupleType:
        heavy_axis = axes.heavy_atom_axes(spectrum)[0]
        attached_axis = axes.attached_proton_axis(spectrum, heavy_axis)
        if axis == attached_axis:
          axis_name = axis_name[0]
        else:
          axis_name = axis_name[1]
      axis_names.append(axis_name)
    return axis_names

  # ---------------------------------------------------------------------------
  # Start AutoAssign server
  #
  def start_server(self, server_host, server_port, server_executable,
		   server_lag):

    local_host = socket.gethostname()
    if server_host != local_host:
      out = self.sparky_session.stderr
      out.write('Can only start AutoAssign server on '
                'local machine %s\n' % local_host)

    s_proc = subprocess.subprocess(server_executable, '%d' % server_port)
    s_proc.from_process.close()
    s_proc.to_process.close()
                        
    #
    # Sleep and pray that the server comes up before the client queries it
    #
    time.sleep(server_lag)

    self.server_process = s_proc

  # ---------------------------------------------------------------------------
  # Kill AutoAssign server
  #
  def kill_server(self, server_proc):
    
    server_proc.kill()
    code = server_proc.exit_code()
    if code:
      out = self.sparky_session.stderr
      out.write('AutoServer process %d exit code = %d\n'
                % (server_proc.process_id, code))

  # ---------------------------------------------------------------------------
  # Start AutoAssign client
  #
  def start_client(self, client_executable, server_host, server_port):

    aa_proc = subprocess.subprocess(client_executable, server_host,
                                    '%d' % server_port, '-')
    self.client_process = aa_proc

  # ---------------------------------------------------------------------------
  #
  def write_autoassign_input_files(self, tolerances, temp_directory):

    asys = self.assignment_system
    assignable_spectra = asys.assignable_spectra
    if len(assignable_spectra) == 0:
      return

    self.write_peak_lists(asys, temp_directory)

    molecule = assignable_spectra[0].spectrum.molecule
    self.write_spectrum_table(asys, molecule, tolerances, temp_directory)
    
    return 1
    
  # ---------------------------------------------------------------------------
  #
  def write_spectrum_table(self, asys, molecule, tolerances, temp_directory):

    table_path = os.path.join(temp_directory, 'table.aat')
    f = open(table_path, 'w')

    f.write('#\n' +
            '# %s table file for AutoAssign\n' % molecule.name +
            '#\n')
    f.write('Protein: %s\n' % molecule.name)
    f.write('\n')

    seq = sequence.molecule_sequence(molecule)
    f.write('Sequence: %d %s*\n' % (seq.first_residue_number,
                                    seq.one_letter_codes))
    f.write('\n')

    toltext = ''
    for atom_name in ('HN', 'N15', 'CA', 'CB', 'HA', 'CO'):
      toltext = toltext + ' %s %.3f' % (atom_name, tolerances[atom_name])
    f.write('Tolerances: %s\n' % toltext)
    f.write('\n')

    f.write('Spectra:\n')
    for asp in asys.assignable_spectra:
      self.write_spectrum_table_entry(asp, f)
    f.write('$\n')
    
    f.close()
    
  # ---------------------------------------------------------------------------
  #
  def write_spectrum_table_entry(self, assignable_spectrum, file):

    type = assignable_spectrum.autoassign_type
    ref_type = self.root_spectrum
    if type == ref_type:
      ref_type = 'ROOT'

    file_name = type + '.pks'

    intra = type in self.intra_peak_spectra
    inter = type in self.inter_peak_spectra
    phase = assignable_spectrum.autoassign_phase
    
    file.write('%s %s %s %d %d 0 phase: {%s} {\n' %
               (type, ref_type, file_name, intra, inter, phase))

    tolerances = assignable_spectrum.tolerances
    spectrum = assignable_spectrum.spectrum
    min_ppm, max_ppm = spectrum.region
    min_ppm = pyutil.subtract_tuples(max_ppm, spectrum.sweep_width)
    axis_names = self.autoassign_axis_names(spectrum, type)
    for a in range(spectrum.dimension):
      file.write('{%10s %8.3f %8.3f   0 %8.3f unfolded }\n' %
                 (axis_names[a], min_ppm[a], max_ppm[a], tolerances[a]))
    file.write('}\n')
    
  # ---------------------------------------------------------------------------
  #
  def write_peak_lists(self, asys, directory):

    for asp in asys.assignable_spectra:
      file_name = asp.autoassign_type + '.pks'
      path = os.path.join(directory, file_name)
      self.write_peak_list(asp, path)

  # ---------------------------------------------------------------------------
  #
  def write_peak_list(self, assignable_spectrum, path):

    f = open(path, 'w')

    spectrum = assignable_spectrum.spectrum
    axes = pyutil.sequence_string(spectrum.nuclei, '%3s ppm  ')
    heading = '# index  %s     intensity  spectrum\n' % axes
    f.write(heading)

    id = 0
    type = assignable_spectrum.autoassign_type
    for peak in spectrum.peak_list():
      id = id + 1
      ppm = pyutil.sequence_string(peak.frequency, '%8.3f ')
      height = sputil.peak_height(peak)
      line = '%5d %s %12.5g %10s\n' % (id, ppm, height, type)
      f.write(line)
      
    f.write('*\n')
    f.close()

  # ---------------------------------------------------------------------------
  # Extract chemical shift lines from output of AutoAssign ascii client.
  #
  def chemical_shift_lines(self, lines):

    start_line = 'AA         HN    N15     CO     CA     CB     HA\n'
    start_line115 = 'AA         HN    N15     CO     CA     CB     HA           \n'
    start_lines = [start_line, start_line115]
    end_line = 'END_MSG\n'

    s = 0
    while s < len(lines) and lines[s] not in start_lines:
      s = s + 1
    s = s + 2           # skip to first chemical shift line

    e = s
    while e < len(lines) and lines[e] != end_line:
      e = e + 1

    return lines[s:e]
        
  # ---------------------------------------------------------------------------
  # Lines are in AutoAssign publication format.
  #
  def resonance_assignments(self, seq, lines):

    rtable = {}
    for line in lines:
      symbol3 = string.upper(line[0:3])
      symbol = atomnames.aaa_to_a[symbol3]
      number = string.atoi(line[3:7])
      self.set_resonance_shift(symbol, number, 'H', seq, line[7:14], rtable)
      self.set_resonance_shift(symbol, number, 'N', seq, line[14:21], rtable)
      self.set_resonance_shift(symbol, number, 'C', seq, line[21:28], rtable)
      self.set_resonance_shift(symbol, number, 'CA', seq, line[28:35], rtable)
      self.set_resonance_shift(symbol, number, 'CB', seq, line[35:42], rtable)
      self.set_resonance_shift(symbol, number, 'HA', seq, line[42:49], rtable)
      self.set_resonance_shift(symbol, number, 'HA2', seq, line[49:56], rtable)
    return rtable
        
  # ---------------------------------------------------------------------------
  # Add and entry to a resonance shift table is shift_text is non empty
  #
  def set_resonance_shift(self, symbol, number, atom_name, sequence,
                          shift_text, rtable):

    shift = pyutil.string_to_float(shift_text)
    if shift == None:
      return

    r = sequence.resonance(number, symbol, atom_name)
    if r == None:
      return

    rtable[r] = shift
        
  # ---------------------------------------------------------------------------
  # Guess peak assignments from resonance assignments.  AutoAssign can't
  # output peak assignments.  This should be fixed since these guessed peak
  # assignments are not always what AutoAssign actually used.
  #
  def guess_peak_assignments(self, assignable_spectrum, rshifts):

    alist = []
    for epeak in assignable_spectrum.expected_peaks:
      if epeak.are_resonances_assigned(rshifts):
        freq = pyutil.table_values(rshifts, epeak.resonances)
        dpeaks = epeak.matching_data_peaks(freq, self)
        dpeak = sputil.closest_peak(freq, dpeaks,
                                    assignable_spectrum.tolerances)
        if dpeak:
          alist.append((epeak, dpeak))
    return alist
        
  # ---------------------------------------------------------------------------
  #
  def show_peak_assignments(self, peak_assignments):

    self.assign_peaks(peak_assignments)
    self.show_assignments(self.assignment_system)
        
  # ---------------------------------------------------------------------------
  #
  def assign_peaks(self, peak_assignments):

    for asp, alist in peak_assignments.items():
      self.progress_report('Assigning peaks for ' + asp.spectrum.name)
      sputil.unassign_spectrum(asp.spectrum)
      for epeak, dpeak in alist:
        epeak.assign(dpeak)
        
  # ---------------------------------------------------------------------------
  #
  def show_assignments(self, asys):

    self.progress_report('Showing peak assignments')
    assigngraph.show_assignment_system(self.sparky_session, asys)
    self.progress_report('')

# -----------------------------------------------------------------------------
#
def show_dialog(session):
  sputil.the_dialog(autoassign_dialog,session).show_window(1)
