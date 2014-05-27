# -----------------------------------------------------------------------------
# Fork a subprocess with bidirectional I/O.
# This works under Unix but not Microsoft Windows because the
# Python os.fork() call is available only for Unix.
#
import os
import sys

# -----------------------------------------------------------------------------
#
class subprocess:

  def __init__(self, *argv):

    self.argv = argv

    to_read, to_write = os.pipe()            # parent to subrocess pipe
    from_read, from_write = os.pipe()        # subprocess to parent pipe
  
    pid = os.fork()

    if pid == 0:

      # this is the subprocess

      #
      # Need to restore stderr to the original Python stderr.
      # Otherwise an error message goes to the Sparky Python shell window.
      # So both the forked child proccess and the parent are using the
      # same X display connection and this generates X protocol errors.
      #
      sys.stderr = sys.__stderr__

      os.close(to_write)
      os.close(from_read)
      os.dup2(to_read, 0)           # connect stdin
      os.dup2(from_write, 1)        # connect stdout
      try:
        os.execvp(argv[0], argv)        # doesn't return
      except os.error, e:
        arg_string = reduce(lambda args, arg: args + ' ' + arg, argv, '')
        sys.stderr.write('Error: exec %s\n' % arg_string +
                         '  errno %d: %s\n' % (e[0], e[1]))
        #
        # Call exit with no cleanup
        #
        os._exit(1)

    # this is the parent process

    os.close(to_read)
    os.close(from_write)

    self.to_process = os.fdopen(to_write, 'w')
    self.from_process = os.fdopen(from_read, 'r');
    self.process_id = pid
    self.exit_status = None

  # ---------------------------------------------------------------------------
  #
  def __del__(self):

    self.to_process.close()
    self.from_process.close()

    #
    # If the subprocess has not exitted, kill it and wait for it.
    # Even if we can rely on the process to exit itself at a later time
    # we wouldn't have a convenient way to wait for it -- creating a
    # zombie process.  Creating alot of these can reach the per user
    # process limit (typically a few 100).
    #
    self.kill()

  # ---------------------------------------------------------------------------
  # Send a kill signal and wait for the process.
  #
  def kill(self):

    if not self.exitted():
      os.kill(self.process_id, 9)
      self.wait(block = 1)
    
  # ---------------------------------------------------------------------------
  #
  def exitted(self):

    self.wait(block = 0)
    return self.exit_status != None
    
  # ---------------------------------------------------------------------------
  #
  def exit_code(self):

    self.wait(block = 1)
    return self.exit_status
    
  # ---------------------------------------------------------------------------
  #
  def wait(self, block):

    if self.exit_status == None:
      if block:
        flags = 0
      else:
        flags = os.WNOHANG
      pid, status = os.waitpid(self.process_id, flags)
      if pid == self.process_id:
        self.exit_status = os.WEXITSTATUS(status)
