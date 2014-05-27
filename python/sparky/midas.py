# -----------------------------------------------------------------------------
# Start Midas with this code acting as a delegate.
# Dispatch atom picking commands from Midas.
#
import os
import re
import string
import tempfile
import traceback

import pdb
import sparky
import sputil
import subprocess

midas_path = '/usr/local/midas/bin/midas'
echo_commands = 0

class BrokenPipe(Exception): pass

# -----------------------------------------------------------------------------
#
the_midas_proc = None
def the_midas_process(session):

  global the_midas_proc
  if not the_midas_proc:
    the_midas_proc = midas_process(session)
  return the_midas_proc

# -----------------------------------------------------------------------------
# Shorthand name
#
process = the_midas_process

# -----------------------------------------------------------------------------
#
def new_midas_process(session):

  global the_midas_proc
  the_midas_proc = None

# -----------------------------------------------------------------------------
#
class midas_process:

  def __init__(self, session):

    self.session = session
    self.open_models = []               # file paths
    self.model_numbers = {}             # pdb path -> model number
    self.next_model_num = 100

    self.midas = subprocess.subprocess(midas_path, '-d', 'sparky')
    self.from_midas = self.midas.from_process
    self.to_midas = self.midas.to_process
    self.send_sync()

    self.atom_pick_callbacks = []
    self.request_cb = session.add_input_callback(self.from_midas,
                                                 self.midas_request_cb)

  # -------------------------------------------------------------------------
  #
  def send_command(self, midas_command):

    self.send_line(midas_command)
    return self.read_midas_reply()

  # -------------------------------------------------------------------------
  #
  def send_sync(self):

    self.send_line('SYNC')

  # -------------------------------------------------------------------------
  #
  def send_line(self, line):

    if echo_commands:
      self.session.stdout.write('Line to midas: ' + line + '\n')
      
    try:
      self.to_midas.write(line + '\n')
      self.to_midas.flush()
    except IOError:
      raise BrokenPipe

  # -------------------------------------------------------------------------
  #
  def read_midas_reply(self):

    if echo_commands:
      self.session.stdout.write('Midas reply: ')
    line = self.from_midas.readline()
    if echo_commands:
      self.session.stdout.write(line)
    if line == 'SYNC\n' or line == '':
      return ''
    return line + self.read_midas_reply()

  # -------------------------------------------------------------------------
  #
  def show_pdb_models(self, pdb_paths):

    for path in self.open_models:
      if not path in pdb_paths:
	self.send_command('~open %d' % self.model_numbers[path])

    for path in pdb_paths:
      if not path in self.open_models:
	self.model_numbers[path] = self.next_model_number()
	self.send_command('open %d %s' % (self.model_numbers[path], path))

    self.open_models = pdb_paths

  # ---------------------------------------------------------------------------
  #
  def show_objects(self, name, path):

    if not self.model_numbers.has_key(name):
      self.model_numbers[name] = self.next_model_number()
    else:
      self.send_command('~open %d' % self.model_numbers[name])

    model_number = self.model_numbers[name]
    self.send_command('open object %d %s' % (model_number, path))

  # ---------------------------------------------------------------------------
  #
  def unshow_objects(self, name):

    if self.model_numbers.has_key(name):
      self.send_command('~open %d' % self.model_numbers[name])

  # -------------------------------------------------------------------------
  #
  def next_model_number(self):

    n = self.next_model_num
    self.next_model_num = n + 1
    return n

  # ---------------------------------------------------------------------------
  #
  def add_atom_pick_callback(self, callback):

    if not callback in self.atom_pick_callbacks:
      self.atom_pick_callbacks.append(callback)
      if len(self.atom_pick_callbacks) == 1:
	self.send_command('pickatom')

  # ---------------------------------------------------------------------------
  #
  def remove_atom_pick_callback(self, callback):

    if callback in self.atom_pick_callbacks:
      self.atom_pick_callbacks.remove(callback)
      if len(self.atom_pick_callbacks) == 0:
	self.send_command('pickabort')

  # ---------------------------------------------------------------------------
  # Process a user command entered through midas.
  #
  def midas_request_cb(self):

    if echo_commands:
      self.session.stdout.write('Midas request: ')
    line = self.from_midas.readline()
    if echo_commands:
      self.session.stdout.write(line)
    if line == '':                                      # Midas sent EOF
      self.session.remove_input_callback(self.request_cb)
    else:
      if line[:8] == 'pickatom':
	atom_spec = line[9:-1]
	if atom_spec == '': return		# handle a Midas bug
	for cb in self.atom_pick_callbacks:
	  try:
	    cb(atom_spec)
	  except:
	    traceback.print_exc()
	self.send_command('pickatom')
      elif line[:9] == 'pickabort':
	self.atom_pick_callbacks = []
      self.send_sync()

  # -------------------------------------------------------------------------
  # Parse #0:48@2H5' to get model 0, residue 48, atom 2H5'
  # and return a pdb model and pdb atom.
  #
  def midas_pick_to_pdb_atom(self, midas_atom_spec):

    match = re.match('(#)(\d+)(:)(\d+)(@)(.+)', midas_atom_spec)
    if match:
      g = match.groups()
      model_number = string.atoi(g[1])
      path = self.model_path(model_number)
      if path:
        residue_number = string.atoi(g[3])
        atom_name = g[5]
        model = pdb.model(self.session, path)
        num_atom = (residue_number, atom_name)
        pdb_atom = model.num_atom_to_pdb_atom(num_atom)
	return model, pdb_atom

    return None, None

  # -------------------------------------------------------------------------
  #
  def model_path(self, model_number):

    for path, num in self.model_numbers.items():
      if num == model_number:
	return path

    return None

  # ---------------------------------------------------------------------------
  #
  def color_pdb_atoms(self, pdb_atoms, color, pdb_path):

    if not pdb_path in self.open_models:
      return
    
    s = ''
    for a in pdb_atoms:
      s = s + ':%d@%s' % (a.residue_number, a.atom_name)

    if s:
      model_number = self.model_numbers[pdb_path]
      command = 'color %s #%d' % (color, model_number) + s
      self.send_command(command)

# -----------------------------------------------------------------------------
#
class midas_object_file:

  def __init__(self, name):

    self.name = name
    self.lines = []

  # -------------------------------------------------------------------------
  #
  def add_line(self, point1, point2, color):

    self.lines.append('.color %s\n' % color)
    self.lines.append('.m %.3f %.3f %.3f\n' % point1)
    self.lines.append('.d %.3f %.3f %.3f\n' % point2)

  # -------------------------------------------------------------------------
  #
  def add_text(self, text, point, color):

    self.lines.append('.color %s\n' % color)
    self.lines.append('.cmov %.3f %.3f %.3f\n' % point)
    self.lines.append(text + '\n')

  # -------------------------------------------------------------------------
  #
  def show_objects(self, session):

    path = self.temporary_file(self.name)
    file = open(path, 'w')
    file.writelines(self.lines);
    file.close()
    the_midas_process(session).show_objects(self.name, path)

    #
    # I assume Midas reads the objects before replying to command so
    # it is safe to delete the file now.
    #
    os.remove(path)

  # -------------------------------------------------------------------------
  #
  def temporary_file(self, prefix):

    old_template = tempfile.template
    tempfile.template = prefix
    path = tempfile.mktemp()
    tempfile.template = old_template
    return path
