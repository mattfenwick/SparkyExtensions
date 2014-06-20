# this works with data in the format of the r_dump module
# it allows multiple resonances with the same atomptype assignment

def atomtype_warning(gid, gss):
    """
    checks if > 1 resonance for a given atomtype
    """
    ats = {'gid': gid}
    for (_, res) in gss['resonances'].items():
        at_ = res['atomtype']
        if at_ == '?':
            continue
        if at_ not in ats:
            ats[at_] = []
        ats[at_].append(res['shift'])
    multiple = dict([(a,s) for (a,s) in ats.items() if len(s) > 1])
    # TODO hope this isn't whacking an atomtype named 'gid' !!
    multiple['gid'] = gid
    return multiple


def atomtype_report(gs):
    """
    just a little printed report of GSSs with multiple resonances assigned to the same atomtype
    """
    reports = map(lambda x: atomtype_warning(*x), gs.items())
    print 'atomtype reports'
    for r in sorted(reports, key=lambda x: int(x['gid'])):
        if len(r) > 1:
            print r


def shift_warning(gid, gss):
    """
    returns the gid if there's two resonances with very close chemical shifts; None otherwise
    """
    shifts = sorted([r['shift'] for r in gss['resonances'].values()])
    for (ix, sh) in enumerate(shifts[:-1]): # leave off the last b/c there's nothing following it
        sh1 = shifts[ix + 1]
        if sh < 12:
            allowed = 0.02
        else:
            allowed = 0.2
        if abs(sh1 - sh) < allowed:
            return gid
    return None


def shift_report(gs):
    """
    just a little printed report of shift warnings
    """
    reports = map(lambda x: shift_warning(*x), gs.items())
    print 'shift report'
    for r in sorted(reports):
        if r is not None:
            print r


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
    """
    matches where there's more than 1 pair of resonances within tolerances
    """
    matches = all_good(gs)
    first, second = {}, {}
    for (gid1, gid2, _) in matches:
        if gid1 not in first:
            first[gid1] = []
        if gid2 not in second:
            second[gid2] = []
        first[gid1].append(gid2)
        second[gid2].append(gid1)
    def split(my_dict):
        unamb, amb = {}, {}
        for (k,v) in my_dict.items():
            if len(v) > 1:
                amb[k] = v
            else:
                unamb[k] = v
        return {'unamb': unamb, 'amb': amb}
    return {'next': split(first), 'prev': split(second)}
        

def matching_report(gs):
    """
    just a little sorted print-out of the all-good matches
    """
    matches = all_good(gs)
    for (x,y,_) in sorted(matches, key=lambda x: (int(x[0]), int(x[1]))):
        print x,y, len(_), _


def build_chains(gs):
    matches = all_good(gs)
    seq = {}
    for (gid1, gid2, _) in matches:
        pass # TODO finish!
