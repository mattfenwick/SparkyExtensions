# GSS matching
# an example GSS:
#   {'gid': ..., 'aatype': ...,
#    'resonances': {'1': {'shift': 30.38, 'atomtype': 'CB(i-1)},
#                   '2': {'shift': 36.49, 'atomtype': 'CB'}}}

# questions about GSSs:
#   multiple resonances with the same atomtype (either accidentally or on purpose)?
#     yes, I think I basically have to assume that might be the case
#   

def atomtype_warning(gss):
    """
    1. > 1 resonance for a given atomtype
    2. if there are multiple resonances for an atomtype, do they have *different* shifts?
    """
    ws = []
    ats = {}
    for (rid, res) in gss['resonances'].items():
        at_ = res['atomtype']
        if at_ not in ats:
            ats[at_] = []
        ats[at_].push(res['shift'])
    for (atomtype, shifts) in ats.items():
        if len(shifts) > 1:
            ws.push({'atomtype': atomtype, 'shifts': shifts})
    return ws


default_atomtypes = set([
    'CA', 'CB', 'CA(i-1)', 'CB(i-1)', 'CA(i/i-1)', 'CB(i/i-1)'
])

default_matches = [
    (set(['CA(i/i-1)', 'CA']), set(['CA(i-1)', 'CA(i/i-1)'])),
    (set(['CB(i/i-1)', 'CB']), set(['CB(i-1)', 'CB(i/i-1)'])),
#    (set(['?']), set(['?'])) # TODO but they have to have the same sign in the HNCACB
]


def match(rs1, rs2, stuff, matches=default_matches, tolerance=0.2):
    """
    determine how well two GSSs match
    """
    results = {'yes': [], 'no': []}
    for (rid1, r1) in rs1.iteritems():
        at1 = r1['atomtype']
        if at1 not in default_atomtypes:
            continue
        for (rid2, r2) in rs2.iteritems():
            at2 = r2['atomtype']
            if at2 not in default_atomtypes:
                continue
            for (m1, m2) in default_matches:
                if at1 not in m1 or at2 not in m2:
                    continue # not_found.append((a1, a2))
                s1, s2 = r1['shift'], r2['shift']
                diff = abs(s1 - s2)
                datum = (rid1, rid2, at1, at2, diff)
                # print stuff, datum, s1, s2, abs(s1 - s2)
                if diff <= tolerance:
                    results['yes'].append(datum)
                else:
                    results['no'].append(datum)
    return results


# is it possible to take control of the Sparky strip plot, and make strips appear?

def match_all(gs):
    """
    naive, stupid approach: match all against all
    """
    found = {}
    for (gid1, g1) in sorted(gs.iteritems(), key=lambda x: int(x[0])):
        found[gid1] = {}
        for (gid2, g2) in sorted(gs.iteritems(), key=lambda x: int(x[0])):
            if gid1 == gid2:
                continue
            result = match(g1['resonances'], g2['resonances'], [gid1, gid2])
            found[gid1][gid2] = result
    return found


def all_good(gs):
    """
    find matches in which all of the 'present' pairs are within the tolerances
    """
    matches = match_all(gs)
    unamb = []
    for (gid1, rs) in matches.items():
        for (gid2, yn) in rs.items():
            if len(yn['no']) == 0 and len(yn['yes']) > 1:
                unamb.append((gid1, gid2, yn))
    return unamb


def multiple_good(gs):
    matches = all_good(gs)
    first, second = {}, {}
    for (gid1, gid2, _) in matches:
        if gid1 not in first:
            first[gid1] = []
        if gid2 not in second:
            second[gid2] = []
        first[gid1].append(gid2)
        second[gid2].append(gid1)
    def my_filter(my_dict):
        return dict([(k,v) for (k,v) in my_dict.items() if len(v) > 1])
    return map(my_filter, (first, second))
        

def report(gs):
    matches = all_good(gs)
    for (x,y,_) in sorted(matches, key=lambda x: (int(x[0]), int(x[1]))):
        print x,y, len(_), _
