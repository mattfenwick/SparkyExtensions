
def error(**kwargs):
    kwargs['type'] = 'error'
    return kwargs

def change(**kwargs):
    kwargs['type'] = 'change'
    return kwargs

def new(**kwargs):
    kwargs['type'] = 'new'
    return kwargs

def lost(**kwargs):
    kwargs['type'] = 'lost'
    return kwargs


def diff_peakdim(d1, d2, specname, peakid, dimid, log):
    s1, s2 = d1['shift'], d2['shift']
    if s1 != s2: # TODO floating point equality?
        log.append(change(datum='peakdim', field='shift', specname=specname, peakid=peakid, dimid=dimid, old=s1, new=s2))
    r1, r2 = d1['resonance'], d2['resonance']
    if r1 != r2:
        log.append(change(datum='peakdim', field='assignment', specname=specname, peakid=peakid, dimid=dimid, old=r1, new=r2))

def diff_peak(p1, p2, specname, log):
    for key in ['height', 'note']:
        v1, v2 = p1[key], p2[key]
        if v1 != v2:
            log.append(change(datum='peak', field=key, specname=specname, peakid=p1['id'], old=v1, new=v2))
    for (ix,_) in enumerate(p1['alias']): # just to get the number of dimensions
        d1 = {'shift': p1['frequency'][ix], 'resonance': p1['resonances'][ix]}
        d2 = {'shift': p2['frequency'][ix], 'resonance': p2['resonances'][ix]}
        diff_peakdim(d1, d2, specname, p1['id'], ix+1, log) 

def diff_spectrum(sp1, sp2, log):
    for key in ['name', 'dims', 'data_size', 'hz_per_ppm', 'nuclei']:
        if sp1[key] != sp2[key]:
            log.append(error(datum='spectrum', field=key, specname=sp1['name'], old=sp1[key], new=sp2[key], message="can't change field"))
    ps1 = dict([(p['id'], p) for p in sp1['peaks']])
    ps2 = dict([(p['id'], p) for p in sp2['peaks']])
    # what if there's duplicates?
    if len(ps1) != len(sp1['peaks']):
        raise ValueError('duplicate peak ids in spectrum % (old)' % sp1['name'])
    if len(ps2) != len(sp2['peaks']):
        raise ValueError('duplicate peak ids in spectrum % (new)' % sp2['name'])
    # okay -- let's diff!
    ids1, ids2 = set(ps1.keys()), set(ps2.keys())
    for pkid in (ids2 - ids1):
        log.append(new(datum='spectrum', field='peak', specname=sp1['name'], peakid=pkid))
    for pkid in (ids1 - ids2):
        log.append(error(datum='spectrum', field='peak', specname=sp1['name'], peakid=pkid, message='lost peak'))
    for pkid in ids1.intersection(ids2):
        # TODO is it safe to assume they're ordered, and without gaps?
        # print 'pkid: ', pkid, map(len, (sp1['peaks'], sp2['peaks']))
        diff_peak(sp1['peaks'][pkid - 1], sp2['peaks'][pkid - 1], sp1['name'], log)

def diff_resonance(r1, r2, rid, log):
    for key in ['atomtype']: # TODO do I care about shift and deviation?
        if r1[key] != r2[key]:
            log.append(change(datum='resonance', field=key, rid=rid, old=r1[key], new=r2[key]))

def diff_group(g1, g2, gid, log):
    for key in ['aatype', 'next', 'residue']:
        if g1[key] != g2[key]:
            log.append(change(datum='group', field=key, gid=gid, old=g1[key], new=g2[key]))
    rs1, rs2 = set(g1['resonances'].keys()), set(g2['resonances'].keys())
    for rid in (rs2 - rs1): # new resonances
        log.append(new(datum='group', field='resonance', gid=gid, rid=rid))
    for rid in (rs1 - rs2): # lost resonances
        log.append(lost(datum='group', field='resonance', gid=gid, rid=rid)) # TODO how should I deal with this?
    for rid in rs1.intersection(rs2): # possibly changed resonances
        diff_resonance(g1['resonances'][rid], g2['resonances'][rid], rid, log)

def semantic_diff(m1, m2):
    # illegal:
    #   removing a peak/spectrum
    # legal
    #   removing a resonance/group
    #     by merging resonances/groups or unassigning peak dims
    #   change peak attributes
    #   peakdim-resonance
    #     if all peakdims of a resonance get re-assigned, then does the resonance go away?
    #   resonance-atomtype
    #   gss-gss, gss-aatype, gss-residue
    #   
    log = []
    # spectra
    s1, s2 = set(m1['spectra'].keys()), set(m2['spectra'].keys())
    for specname in (s1 - s2): # lost spectra
        log.append(error(datum='model', field='spectrum', specname=specname, message='lost spectrum'))
    for specname in (s2 - s1): # new spectra
        log.append(new(datum='model', field='spectrum', specname=specname))
    for specname in s1.intersection(s2): # possibly changed spectra
        diff_spectrum(m1['spectra'][specname], m2['spectra'][specname], log)
    # now continue with groups
    g1, g2 = set(m1['groups'].keys()), set(m2['groups'].keys())
    for gid in (g1 - g2): # lost groups
        pass # TODO not sure what to do
    for gid in (g2 - g1): # new groups
        pass
    for gid in g2.intersection(g1): # possibly changed groups
        diff_group(m1['groups'][gid], m2['groups'][gid], gid, log)
    # done
    return log


def eg():
    try:
        import simplejson as json
    except:
        import json
    a1 = json.loads(open('a1.txt', 'r').read())
    a2 = json.loads(open('a2.txt', 'r').read())
    return semantic_diff(a1, a2)

def eg2():
    log = eg()
    ds = {'error': [], 'change': [], 'lost': [], 'new': []}
    for l in log:
        ds[l['type']].append(l)
    return ds

def eg3():
    rs = eg2()
    for t in rs.keys():
        print '\n now for %s' % t
        for r in rs[t]:
            print r
