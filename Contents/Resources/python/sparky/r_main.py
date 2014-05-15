import sparky
from . import r_model as model
from subprocess import Popen, PIPE
import os



class GitRepo(object):

    def __init__self():
        self._path = model.project().sparky_directory
        # self._path = os.path.expanduser("~") + path
    
    def check_repo(self):
        os.chdir(self._path)
        p = Popen(["git", "status"], stdout=PIPE, stderr=PIPE)
        p.wait()
        if p.returncode != 0:
            raise ValueError("not a git repo: cannot dump & commit data (" + p.stderr.read() + ")")
    
    def dump(self, commit_message):
        check_repo()
        os.chdir(self._path)
        try:
            add = Popen(["git", "add", "."], stdout=PIPE, stderr=PIPE)
            add.wait()
            if add.returncode != 0:
                raise ValueError("git add failed (" + add.stderr.read() + ")")
            commit = Popen(["git", "commit", "-m", commit_message], 
                           stdout=PIPE, 
                           stderr=PIPE)
            commit.wait()
            if commit.returncode != 0:
                raise ValueError("git commit failed (" + commit.stderr.read() + ")")
        except Exception, e:
            print 'failure making Sparky/git repository snapshot', e
            raise

