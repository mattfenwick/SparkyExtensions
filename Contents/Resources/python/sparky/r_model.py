'''
@author: mattf
'''
import sparky
import re


########## access objects from Sparky model

def session():
    return sparky.session_list[0]

def project():
    return session().project

def molecule():
    return project().molecule_list()[0]    

def groups():
    return molecule().group_list()

def resonances():
    rs = []
    for c in project().condition_list():
        rs.extend(c.resonance_list())
    return rs

def resonances_from_peaks():
    """
    expected to match resonances ... but is it true ??
    """
    my_rs = set([])
    for spectrum in project().spectrum_list():
        for pk in spectrum.peak_list():
            for r in pk.resonances():
                if r is not None:
                    my_rs.add(r)
    return my_rs

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


#### group and resonances names from my model

_group_pattern = re.compile('^([^\\[]+)\\[([^\\]]+)\\]\\{([^\\}]+)\\}$')
_resonance_pattern = re.compile('^([^\\[]+)\\[([^\\]]+)\\]$')

def parse_group(name):
    match = _group_pattern.match(name)
    if match is None:
        raise ValueError('invalid group name -- ' + name)
    gid, next_, res = match.groups()
    return (gid, next_, res)

def unparse_group(gid, next_, residue):
    return '%s[%s]{%s}' % (gid, next_, residue)

def parse_resonance(name):
    match = _resonance_pattern.match(name)
    if match is None:
        raise ValueError('invalid resonance name -- ' +  name)
    rid, atom = match.groups()
    return (rid, atom)

def unparse_resonance(rid, atom):
    return '%s[%s]' % (rid, atom)


#### assignment utilities

def _add_into_cluster(cls, val):
    n = 0
    for c in cls:
        v = c[0]
        if abs((v - val) / (1.0 * val)) < 0.01:
            return c[1]
        n = c[1]
    cls.append((val, n + 1))
    return n + 1

def _selected_peaks():
    return session().selected_peaks()

def set_group(name):
    pks = _selected_peaks()
    r_ids = []
    n = 0
    for pk in pks:
        for i in range(len(pk.frequency)):
            n += 1
            my_id = _add_into_cluster(r_ids, pk.frequency[i])
            pk.assign(i, 
                      unparse_group(name, '?', '?'), 
                      unparse_resonance(str(my_id), '?'))
        pk.show_assignment_label()
    print n, 'assignments made'


def set_next_ss(prev, next_):
    raise ValueError('unimplemented')


def set_residue(ss, residue):
    raise ValueError('unimplemented')


def set_atomtype(group, resid, atomtype):
    # do I have to reset, for each peak dimension assigned to this resonance, the name?
    raise ValueError('unimplemented')


def set_noise():
    pks = _selected_peaks()
    for pk in pks:
        if set(pk.resonances()) != set([None]):
            raise ValueError("peak dimension is assigned: cannot set to noise %s" % str(pk))
        pk.color = 'red'
        # pk.show_label('noise')


def set_artifact():
    pks = _selected_peaks()
    for pk in pks:
        if set(pk.resonances()) != set([None]):
            raise ValueError("peak dimension is assigned: cannot set to artifact %s" % str(pk))
        pk.color = 'blue'
        # pk.show_label('artifact')


def set_signal():
    raise ValueError('unimplemented')
