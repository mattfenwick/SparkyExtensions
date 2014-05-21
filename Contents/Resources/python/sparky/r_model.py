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

def spectra():
    return project().spectrum_list()

def molecule():
    return project().molecule_list()[0]    

def groups():
    return molecule().group_list()

def resonances():
    rs = []
    for c in project().condition_list():
        rs.extend(c.resonance_list())
    return rs


#### group and resonances names from my model

_name, _chunk = '([^\\{\\}]+)', '\\{([^\\{\\}]+)\\}'

_group_pattern = re.compile(''.join(['^', _name, _chunk, _chunk, _chunk, '$']))
_resonance_pattern = re.compile(''.join(['^', _name, _chunk, '$']))

def parse_group(name):
    match = _group_pattern.match(name)
    if match is None:
        raise ValueError('invalid group name -- ' + name)
    gid, aatype, next_, res = match.groups()
    return (gid, aatype, next_, res)

def unparse_group(gid, aatype, next_, residue):
    return '%s{%s}{%s}{%s}' % (gid, aatype, next_, residue)

def parse_resonance(name):
    match = _resonance_pattern.match(name)
    if match is None:
        raise ValueError('invalid resonance name -- ' +  name)
    rid, atom = match.groups()
    return (rid, atom)

def unparse_resonance(rid, atom):
    return '%s{%s}' % (rid, atom)


#### some more complex data structures, built from the Sparky model

def _from_peaks():
    """
    expected to match resonances ... but is it true ??
    """
    my_rs, my_gs = set([]), set([])
    for spectrum in project().spectrum_list():
        for pk in spectrum.peak_list():
            for r in pk.resonances():
                if r is not None:
                    my_rs.add(r)
                    my_gs.add(r.group)
    return (my_rs, my_gs)

def resonances_from_peaks():
    rs, _ = _from_peaks()
    return rs

def groups_from_peaks():
    _, gs = _from_peaks()
    return gs

def resonance_map():
    gs, bad, gs_info = {}, {}, {}
    for r in resonances_from_peaks():
        try:
            gid, aatype, next_, residue = parse_group(r.group.name)
            rid, atomtype = parse_resonance(r.atom.name)
        except Exception, e:
            print e
            if not bad.has_key(r.group.name):
                bad[r.group.name] = {}
            bad[r.group.name][r.atom.name] = r
            continue
        if not gs.has_key(gid):
            gs[gid] = {}
            gs_info[gid] = {'aatype': aatype, 'next': next_, 'residue': residue, 'resonances': {}}
        gs[gid][rid] = r
        if rid in gs_info[gid]['resonances']:
            old = gs_info[gid]['resonances'][rid]
            if old != atomtype:
                raise ValueError('inconsistent atomtype for resonance: (%s, %s, %s, %s)' % (gid, rid, old, atomtype))
        else:
            gs_info[gid]['resonances'][rid] = atomtype
    return gs, bad, gs_info

def group_map():
    return dict((g.name, g) for g in groups())

def spectrum_map():
    specs = {}
    for sp in spectra():
        if specs.has_key(sp.name):
            raise ValueError('unable to construct spectrum map: duplicate name %s' % sp.name)
        specs[sp.name] = sp
    return specs

#### assignment utilities

def _add_into_cluster(cls, val):
    n = 0
    for c in cls:
        v = c[0]
        diff = abs((v - val) / (1.0 * val))
        if diff < 0.002:
            return c[1]
        n = c[1]
    cls.append((val, n + 1))
    return n + 1

def _selected_peaks():
    return session().selected_peaks()

def set_group(gid, my_peaks=None):
    pks = _selected_peaks() if my_peaks is None else my_peaks
    for my_pk in pks:
        if my_pk.note in ['noise', 'artifact']:
            raise ValueError('cannot assign group of noise or artifact peak')
    groups, _, gs_info = resonance_map()
    if groups.has_key(gid):
        grp = gs_info[gid]
        aatype  = grp['aatype']
        next_   = grp['next']
        residue = grp['residue']
        r_ids = sorted([(res.frequency, int(ix)) for (ix, res) in groups[gid].items()], key=lambda x: x[1])
    else:
        r_ids = []
        aatype = next_ = residue = '?'
    n = 0
    for pk in pks:
        for i in range(len(pk.frequency)):
            # TODO should this iteration be skipped if peak dim is already assigned a resonance?
            n += 1
            int_rid = _add_into_cluster(r_ids, pk.frequency[i])
            rid, my_gr = str(int_rid), gs_info[gid]['resonances']
            if rid in my_gr:
                atomtype = my_gr[rid]
            else:
                atomtype = '?'
            pk.assign(i, 
                      unparse_group(gid, aatype, next_, residue),
                      unparse_resonance(rid, atomtype))
        pk.show_assignment_label()
    print n, 'assignments made'


def set_new_group(pks=None):
    groups, _, _ = resonance_map()
    n = len(groups) + 1
    while groups.has_key(str(n)):
        n = n + 1
    set_group(str(n), pks)


def set_aatype(gid, aatype):
    groups, _, gs_info = resonance_map()
    if not groups.has_key(gid):
        raise ValueError('invalid group name: %s' % gid)
    for res in groups[gid].values():
        for pk in res.peak_list():
            for (i, res_dim) in enumerate(pk.resonances()):
                next_, residue = gs_info[gid]['next'], gs_info[gid]['residue']
                pk.assign(i,
                          unparse_group(gid, aatype, next_, residue),
                          res_dim.atom.name)


def set_seq_ss(prev, next_):
    groups, _, _ = resonance_map()
    if not groups.has_key(prev):
        raise ValueError('invalid group name: %s' % prev)
    for res in groups[prev].values(): # we don't actually need this resonance for anything but finding the peaks it's assigned to
        for peak in res.peak_list():
            for (i, res_dim) in enumerate(peak.resonances()):
                gid, aatype, _, residue = parse_group(res_dim.group.name) # could just use the gs_info instead
                peak.assign(i,
                            unparse_group(gid, aatype, next_, residue),
                            res_dim.atom.name)


def set_residue(ssname, residue):
    groups, _, _ = resonance_map()
    if not groups.has_key(ssname):
        raise ValueError('invalid group name: %s' % ssname)
    for res in groups[ssname].values(): # we don't actually need this resonance for anything but finding the peaks it's assigned to
        for peak in res.peak_list():
            for (i, res_dim) in enumerate(peak.resonances()):
                gid, aatype, next_, _ = parse_group(res_dim.group.name)
                peak.assign(i,
                            unparse_group(gid, aatype, next_, residue),
                            res_dim.atom.name)


# TODO this seems to be wrong
def set_atomtype(gid, rid, atomtype):
    groups, _, _ = resonance_map()
    if not groups.has_key(gid):
        raise ValueError('invalid group name: %s' % gid)
    if not groups[gid].has_key(rid):
        raise ValueError('invalid resonance %s in group %s' % (rid, gid))
    res = groups[gid][rid] # we don't actually need this resonance for anything but finding the peaks it's assigned to
    for peak in res.peak_list():
        for (i, res_dim) in enumerate(peak.resonances()):
            #rid, _ = parse_resonance(res_dim.atom.name)
            #if rid != resid:
            #    continue
            if res != res_dim:
                continue
            peak.assign(i,
                        res_dim.group.name,
                        unparse_resonance(rid, atomtype))


def assign_peaktype_old(atomtypes):
    pks = _selected_peaks()
    for pk in pks:
        if len(pk.resonances()) != len(atomtypes):
            raise ValueError('peaktype does not match peak dimensionality')
        if pk.note in ['artifact', 'noise']:
            raise ValueError('cannot assign peaktype of noise or artifact')
    for pk in pks:
        for (ix, res_dim) in enumerate(pk.resonances()):
            rid, _ = parse_resonance(res_dim.atom.name)
            pk.assign(ix, 
                      res_dim.group.name,
                      unparse_resonance(rid, atomtypes[ix]))

"""
def assign_resonance_atomtypes(atomtypes):
    pks = _selected_peaks()
    if len(pks) != 1:
        raise ValueError('can only assign resonance atomtypes when a single peak is assigned')
    pk = pks[0]
    if len(pk.resonances()) != len(atomtypes):
        raise ValueError('peaktype does not match peak dimensionality')
    if pk.note in ['artifact', 'noise']:
        raise ValueError('cannot assign peaktype of noise or artifact')
    gs, _, _ = resonance_map()
    # use the peak to find the resonances that I want to deal with, then use those resonances to find the peaks that must be updated
    for (ix, res_dim) in enumerate(pk.resonances()):
        gid, aatype, next_, residue = parse_group(res_dim.group.name)
        rid, _ = parse_resonance(res_dim.atom.name)
        for my_pk in res_dim.peak_list():
            my_pk.assign(ix, 
                         res_dim.group.name,
                         unparse_resonance(rid, atomtypes[ix]))
"""


def set_noise():
    pks = _selected_peaks()
    for pk in pks:
        if set(pk.resonances()) != set([None]):
            raise ValueError("peak dimension is assigned: cannot set to noise %s" % str(pk))
        pk.color = 'red'
        pk.note = 'noise'
        # pk.show_label('noise')


def set_artifact():
    pks = _selected_peaks()
    for pk in pks:
        if set(pk.resonances()) != set([None]):
            raise ValueError("peak dimension is assigned: cannot set to artifact %s" % str(pk))
        pk.color = 'blue'
        pk.note = 'artifact'
        # pk.show_label('artifact')


def set_signal():
    pks = _selected_peaks()
    for pk in pks:
        if not pk.note in ['artifact', 'noise']:
            raise ValueError('peak is neither artifact nor noise')
        pk.note = ''
        pk.color = 'white'


def select_signal_peaks(specname):
    count = 0
    for sp in project().spectrum_list():
        if sp.name == specname:
            for pk in sp.peak_list():
                if pk.note not in ['artifact', 'noise']:
                    pk.selected = 1
            count += 1
    if count == 0:
        raise ValueError('no spectrum named %s' % specname)


def _signal_peaks(spectrum):
    return [pk for pk in spectrum.peak_list() if pk.note not in ['artifact', 'noise']]

def _close(freq1, freq2, tolerance):
    return abs(freq1 - freq2) <= tolerance

def group_peaks_into_gss(dims, spec_from, spec_to):
    specs = spectrum_map()
    fr, to = specs[spec_from], specs[spec_to]
    pks_fr, pks_to = map(_signal_peaks, (fr, to))
    matches = {}
    for pf in pks_fr:
        if not pf.selected:
            continue
        group_names = set([])
        for r in pf.resonances():
            grp, _, _, _ = parse_group(r.group.name)
            group_names.add(grp)
        if len(group_names) != 1:
            raise ValueError('unable to use peak from GSS grouping: does not have unique group name (%s)' % str(group_names))
        name = list(group_names)[0]
        for pt in pks_to:
            is_match = True
            for (df, dt, tolerance) in dims:
                if not _close(pf.frequency[df], pt.frequency[dt], tolerance):
                    is_match = False
                    break
            if is_match:
                if not matches.has_key(pt):
                    matches[pt] = []
                matches[pt].append(name)
    for (pt, names) in matches.items():
        if len(names) == 1:
            set_group(names[0], [pt])
        else:
            print 'unable to assign peak at %s to GSS: ambiguous with groups %s' % (str(pt.frequency), str(names))


def create_group_for_peak():
    for pk in _selected_peaks():
        set_new_group([pk])
    # for each selected peak, create a new group
