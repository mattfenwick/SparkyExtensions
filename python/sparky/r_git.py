import r_model as model
import os
 
 
def import_non_local(name):
    """
    goal: import a shadowed built-in module in python2.4 and python2.5
    cribbed from: http://stackoverflow.com/questions/6031584/python-importing-from-builtin-library-when-module-with-same-name-exists
    """
    import imp, sys
 
    f, pathname, desc = imp.find_module(name, sys.path[1:])
    module = imp.load_module(name, f, pathname, desc)
    f.close()
 
    return module
 
 
#try:
    # for python2.5
#    from __future__ import absolute_import # TODO -- does this affect importing for *every other module in python/sparky/ ?
#    import subprocess
#except SyntaxError: # ??? why doesn't this throw an ImportError ???
#    # for python2.4
#    subprocess = import_non_local('subprocess')
subprocess = import_non_local('subprocess')
Popen = subprocess.Popen
PIPE = subprocess.PIPE



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
