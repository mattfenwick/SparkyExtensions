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


import tkutil
import sputil


class Snapshot_dialog(tkutil.Dialog):

    def __init__(self, session):
        self.g = GitRepo()
        
        self.session = session
        self.title = 'Snapshot'
        
        tkutil.Dialog.__init__(self, session.tk, self.title)
        
        br = tkutil.button_row(self.top, ('Make snapshot', self.make_snapshot))
        br.frame.pack(side = 'top', anchor = 'w')
        # TODO would like to get an enumerated list of these from somewhere
        e = tkutil.entry_field(self.top, 'Deductive reason used:', '<enter reason>', 50)
        e.frame.pack(side = 'top', anchor = 'w')
        self.message = e.variable

        br = tkutil.button_row(self.top, ('Set group', self.set_group))
        br.frame.pack(side = 'top', anchor = 'w')
        # TODO would like to get an enumerated list of these from somewhere
        e = tkutil.entry_field(self.top, 'Group name:', '', 20)
        e.frame.pack(side = 'top', anchor = 'w')
        self.group = e.variable

#        br = tkutil.button_row(self.top, ('Make snapshot', self.make_snapshot))
#        br.frame.pack(side = 'top', anchor = 'w')
#        # TODO would like to get an enumerated list of these from somewhere
#        e = tkutil.entry_field(self.top, 'Deductive reason used:', '<enter reason>', 50)
#        e.frame.pack(side = 'top', anchor = 'w')
#        self.message = e.variable


    def make_snapshot(self):
        self.g.dump(self.message.get())
    
    def set_group(self):
        model.set_group(self.group.get())


def show_snapshot_dialog(session):
    d = sputil.the_dialog(Snapshot_dialog, session)
    d.show_window(1)
