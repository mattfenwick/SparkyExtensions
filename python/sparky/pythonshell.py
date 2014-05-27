# ----------------------------------------------------------------------------
# Python shell dialog.  Displays output from python interpretter and accepts
# user typed commands.
#
import string
import sys
import traceback

import pyutil
import sparky
import sputil
import spy
import tkutil

# ----------------------------------------------------------------------------
# Define system prompts.  These are only defined by Python if it is run in
# interactive mode.
#
sys.ps1 = '>>> '
sys.ps2 = '... '

# ----------------------------------------------------------------------------
#
class python_shell_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    self.raise_on_error = 1
    
    tkutil.Dialog.__init__(self, session.tk, 'Python Shell')
    self.top.bind('<Destroy>', self.window_destroyed_cb, 1)

    w = tkutil.scrolling_text(self.top, 10, 80)
    w.frame.pack(side = 'top', fill = 'both', expand = 1)
    w.text.bind('<KeyRelease-Return>', self.enter_cb)
    w.text.focus_set()  # Initial focus child is text window
    self.text = w.text
    br = tkutil.button_row(self.top,
                           ('Preferences...', self.preferences_cb),
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'PythonShell')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    #
    # Python output goes to this dialog
    #
    class output_object:
      def __init__(self, write_cb):
        self.write = write_cb

    #
    # Make stdout and stderr output go to this shell window
    #
    self.stdout = output_object(self.output_text)
    self.stderr = output_object(self.output_error)

    session.stdout = self.stdout
    session.stderr = self.stderr
    
    if hasattr(session, 'redirect_stdio') and session.redirect_stdio:
      sys.stdout = self.stdout
      sys.stderr = self.stderr

    self.stdout.write(sys.ps1)

  # ---------------------------------------------------------------------------
  # Note that last text character is always a new line, and 'end' refers
  # to start of next line.
  #
  def output_text(self, text):

    self.text.insert('end', text)
    self.text.mark_set('start_command', 'end - 1 chars')
    self.text.mark_gravity('start_command', 'left')
    self.text.see('end')

  # ---------------------------------------------------------------------------
  #
  def output_error(self, text):
      
    if self.raise_on_error:
      self.show_window(1)
    self.output_text(text)

  # ---------------------------------------------------------------------------
  #
  def window_destroyed_cb(self, event):

    if sys.stderr == self.stderr:
      sys.stderr = sys.__stderr__
    if sys.stdout == self.stdout:
      sys.stdout = sys.__stdout__

  # ---------------------------------------------------------------------------
  #
  def preferences_cb(self):

    pd = sputil.the_dialog(shell_preferences_dialog, self.session)
    settings = {'raise-on-error': self.raise_on_error}
    pd.set_parent_dialog(self, settings, self.set_preferences)
    pd.show_window(1)

  # ---------------------------------------------------------------------------
  #
  def set_preferences(self, settings):

    self.raise_on_error = settings['raise-on-error']
    
  # ---------------------------------------------------------------------------
  #
  def enter_cb(self, event):

    if self.text.index('insert') == self.text.index('end - 1 chars'):
      cmd = self.text.get('start_command', 'end - 1 chars')
      command = remove_prompts(cmd)
      if is_complete_command(command):
        self.execute_command(command);
      else:
        self.text.insert('end', sys.ps2)

  # ---------------------------------------------------------------------------
  #
  def send_command(self, command):

    cmd = command + '\n'
    self.stdout.write(cmd)
    self.execute_command(cmd)
    self.top.update()
  
  # ---------------------------------------------------------------------------
  # Output from the command goes to sys.stdout instead of self.stdout.
  # Consequently the result is not printed to this shell unless sys.stdout
  # is redirected to this shell.
  # The problem is that the compiled code object of type 'single' prints
  # the result to sys.stdout when evaluated.  The eval() returns None.
  # The other compile types 'eval' and 'exec' do no better.  With 'eval'
  # only expressions are allowed -- a statement like 'import sys' generates
  # an error.  With 'exec', the result is neither printed nor returned
  # when evaluating the code object, so the result is lost.
  #
  def execute_command(self, command):

    cmd = string.lstrip(command)
    if cmd:
      dict = sys.modules['__main__'].__dict__
      try:
        c = compile(cmd, '<stdin>', 'single')
        result = eval(c, dict, dict)
      except:
        traceback.print_exc(file = self.stderr)
      else:
        if result != None:
          self.stdout.write(str(result) + '\n')

    self.stdout.write(sys.ps1)

# ----------------------------------------------------------------------------
#
class shell_preferences_dialog(tkutil.Settings_Dialog):

  def __init__(self, session):

    tkutil.Settings_Dialog.__init__(self, session.tk,
                                    'Python Shell Preferences')

    cb = tkutil.checkbutton(self.top, 'Show Python shell if error occurs?', 1)
    cb.button.pack(side = 'top', anchor = 'nw')
    self.raise_variable = cb.variable

    br = tkutil.button_row(self.top,
                           ('Ok', self.ok_cb),
                           ('Apply', self.apply_cb),
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'PythonShell')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):

    self.raise_variable.set(settings['raise-on-error'])
    
  # ---------------------------------------------------------------------------
  #
  def get_settings(self):

    settings = {'raise-on-error': self.raise_variable.get()}
    return settings

# -----------------------------------------------------------------------------
#
def is_complete_command(command):

  return not is_compound_statement(command) or command[-2:] == '\n\n'

# -----------------------------------------------------------------------------
#
def is_compound_statement(command):

  return (initial_match("if ", command) or
          initial_match("while ", command) or
          initial_match("for ", command) or
          initial_match("try ", command) or
          initial_match("def ", command) or
          initial_match("class ", command))

# ---------------------------------------------------------------------------
#
def remove_prompts(command):

  lines = string.split(command, '\n')
  cmd = remove_initial_match(lines[0], sys.ps1)
  for line in lines[1:]:
    cmd = cmd + '\n' + remove_initial_match(line, sys.ps2)
  return cmd

# ----------------------------------------------------------------------------
#
def remove_initial_match(string, prefix):

  if initial_match(prefix, string):
    length = len(prefix)
    return string[length:]
  return string

# ----------------------------------------------------------------------------
#
def initial_match(prefix, string):

  length = len(prefix)
  return string[:length] == prefix
  
# -----------------------------------------------------------------------------
# Sparky sends all output to session.stdout and session.stderr which are
# initialized in this routine to go to the Python shell window.  Some
# Python commands (eg. print and reload) send output to sys.stdout and
# sys.stderr.  Also if a Tk callback raises an exception it is printed
# to sys.stderr.  If redirect_stdio is true then sys.stdout and sys.stderr
# are set to session.stdout and session.stderr.  If other modules, such
# as the molecular visualization package Chimera are running under the
# same Python interpretter it may be desirable not to redirect the sys
# module streams since the other module may redirect them to its Python
# shell window.
#
# This routine also imports sparky_site and sparky_init and calls the
# initialize_session routine with session as an argument provide the
# routine exists.
#
def initialize_shell(session, redirect_stdio = 0):

  session.redirect_stdio = redirect_stdio
  sputil.the_dialog(python_shell_dialog, session)         # setup Sparky stdio

  args = (session,)
  invoke_module_function(session, 'sparky_site', 'initialize_session', args)
  invoke_module_function(session, 'sparky_init', 'initialize_session', args)
  
# -----------------------------------------------------------------------------
#
def invoke_module_function(session, module_name, function_name, args):

  try:
    module_path = 'sparky.' + module_name
    code = compile('import %s' % module_path, '<string>', 'single')
    eval(code)
    module = sys.modules[module_path]
    if hasattr(module, function_name):
      func = getattr(module, function_name)
      apply(func, args)
  except:
    traceback.print_exc(file = session.stderr)

# -----------------------------------------------------------------------------
#
def add_command(accel, menu_text, module_name, func_name, session):

  cb = pyutil.precompose(invoke_module_function, session,
                         module_name, func_name, (session,))
  session.add_command(accel, menu_text, cb)

# -----------------------------------------------------------------------------
#
def send_command(session, command):
  sputil.the_dialog(python_shell_dialog,session).send_command(command)
def show_python_shell(session):
  sputil.the_dialog(python_shell_dialog,session).show_window(1)
