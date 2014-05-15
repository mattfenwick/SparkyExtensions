import sparky
from . import r_model as model
from subprocess import Popen, PIPE
import os



class GitRepo(object):

    def __init__(self):
        self._path = model.project().sparky_directory
        # self._path = os.path.expanduser("~") + path
    
    def check_repo(self):
        os.chdir(self._path)
        p = Popen(["git", "status"], stdout=PIPE, stderr=PIPE)
        p.wait()
        return p
    
    def dump(self, commit_message):
        p = self.check_repo()
        if p.returncode != 0:
            raise ValueError("not a git repo: " + p.stderr.read())
        os.chdir(self._path)
        try:
            add = Popen(["git", "add", "Projects/", "Save/"], stdout=PIPE, stderr=PIPE)
            add.wait()
            if add.returncode != 0:
                raise ValueError("git add failed (" + add.stderr.read() + ")")
            commit = Popen(["git", "commit", "-m", commit_message], 
                           stdout=PIPE, 
                           stderr=PIPE)
            commit.wait()
            if commit.returncode != 0:
                raise ValueError("git commit failed (" + commit.stderr.read() + ", " + commit.stdout.read() + ")")
        except Exception, e:
            print 'failure making Sparky/git repository snapshot', e
            raise

g = GitRepo()



import tkutil
import sputil


class Snapshot_dialog(tkutil.Dialog):

  def __init__(self, session):

    self.session = session
    self.title = 'Snapshot'

    tkutil.Dialog.__init__(self, session.tk, self.title)

    br = tkutil.button_row(self.top,
                           ('Make snapshot', self.make_snapshot))
    br.frame.pack(side = 'top', anchor = 'w')
    
    # TODO would like to get an enumerated list of these from somewhere
    e = tkutil.entry_field(self.top, 'Deductive reason used:', '<enter reason>', 50)
    e.frame.pack(side = 'top', anchor = 'w')
    self.message = e.variable


  def make_snapshot(self):
      g.dump(self.message.get())


def show_snapshot_dialog(session):
    d = sputil.the_dialog(Snapshot_dialog, session)
    d.show_window(1)



##### API

def set_group(name):
    pass

def set_next_ss(prev, next_):
    pass

def set_residue(ss, residue):
    pass

def set_atomtype(group, resid, atomtype):
    # do I have to reset, for each peak dimension assigned to this resonance, the name?
    pass

def set_noise():
    # all peak dimensions must be unassigned
    # change peak color
    # change label
    pass

def set_artifact():
    # see `set_noise`
    pass

def set_signal():
    pass
