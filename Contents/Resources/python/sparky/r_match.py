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


def match(matches, rs1, rs2):
    """
    how do we match GSSs sequentially?
      1. Ga CA/CB match Gb CA(i-1)/CB(i-1)
      2. Ga CA matches Gb CA(i-1), CB or CB(i-1) missing
      3. same but swap CA for CB and vice versa
      4. Ga CA(i/i-1) matches Gb CA(i/i-1) or CA(i-1)
    """
    not_found, satisfied, unsatisfied = [], [], []
    for (at1, at2, tol) in matches:
        if at1 in rs1 and at2 in rs2:
            if abs(rs1[at1] - rs2[at2]) <= tol: # TODO but wait -- multiple resonances possible for each atomtype, right?
                satisfied.push((at1, at2))
            else:
                unsatisfied.push((at1, at2))
        else:
            not_found.push((at1, at2))
    return (not_found, satisfied, unsatisfied)


default_matches = [
    ('CA'           , 'CA(i-1)'     , 0.2),
    ('CA(i/i-1)'    , 'CA(i-1)'     , 0.2),
    ('CA'           , 'CA(i/i-1)'   , 0.2),
    ('CA(i/i-1)'    , 'CA(i/i-1)'   , 0.2),
    ('CB'           , 'CB(i-1)'     , 0.2),
    ('CB(i/i-1)'    , 'CB(i-1)'     , 0.2),
    ('CB'           , 'CB(i/i-1)'   , 0.2),
    ('CB(i/i-1)'    , 'CB(i/i-1)'   , 0.2),
    ('?'            , '?'           , 0.2) # TODO but they have to have the same sign
]

# is it possible to take control of the Sparky strip plot, and make strips appear?

def match_gss(g1, g2):
    not_found, sat, unsat = match(default_matches, g1, g2)
    return len(unsat) == 0

def match_all(gs):
    """
    naive, stupid approach: match all against all
    """
    found = dict([(gid, []) for (gid, g) in gs])
    for g1 in gs:
        for g2 in gs:
            if match_gss(g1, g2):
                found[g1['id']).push(g2)
                found[g2['id']).push(g1)
    return found


# BIG TODO -- have played very fast and loose with:
#   1. structure of the data
#   2. semantics of the data
# through this file -- need to figure it out and make it consistent before even trying to run the code

