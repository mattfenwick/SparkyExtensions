'''
@author: mattf
'''
import sparky
import re


def session():
    return sparky.session_list[0]

def project():
    return session().project

def molecule():
    return project().molecule_list()[0]

class GSS(object):
    
    def __init__(self, name):
        self._name = name
        self.next = None
        self.residue = None
    
    def name(self):
        nxt = '[' + ('?' if self.next is None else self.next) + ']'
        res = '{' + ('?' if self.residue is None else self.residue) + '}'
        return self._name + nxt + res
    
    

def groups():
    return molecule().group_list()

def resonances():
    return project().condition_list()[0].resonance_list()

def rs():
    """
    expected to match resonances ... not sure !!
    """
    my_rs = set([])
    for spectrum in project().spectrum_list():
        for pk in spectrum.peak_list():
            for r in pk.resonances():
                if r is not None:
                    my_rs.add(r)
    return my_rs
            

grp = re.compile('^([^\\[]+)\\[([^\\]]+)\\]\\{([^\\}]+)\\}$')
res = re.compile('^([^\\[]+)\\[([^\\]]+)\\]$')

def parse_group(name):
    match = grp.match(name)
    if match is None:
        raise ValueError('invalid group name -- ' + name)
    gid, next, res = match.groups()
    return (gid, next, res)

def parse_resonance(name):
    match = res.match(name)
    if match is None:
        raise ValueError('invalid resonance name -- ' +  name)
    rid, atom = match.groups()
    return (rid, atom)

def resonance_map():
    gs = {}
    for r in resonances():
        gid, _, _ = parse_group(r.group.name)
        if not gs.has_key(gid):
            gs[gid] = {}
        rid, _ = parse_resonance(r.atom.name)
        gs[gid][rid] = r
    return gs

def group_map():
    return dict((g.name, g) for g in groups())

def add_into_cluster(cls, val):
    n = 0
    for c in cls:
        v = c[0]
        if abs((v - val) / (1.0 * val)) < 0.01:
            return c[1]
        n = c[1]
    cls.append((val, n + 1))
    return n + 1

def set_groups(name):
    pks = session().selected_peaks()
    r_ids = []
    n = 0
    for pk in pks:
        for i in range(len(pk.frequency)):
            n += 1
            my_id = add_into_cluster(r_ids, pk.frequency[i])
            pk.assign(i, name + '[?]{?}', str(my_id) + '[?]')
        pk.show_assignment_label()
    print n, 'assignments made'
