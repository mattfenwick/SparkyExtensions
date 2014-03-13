import sparky


def kwargs(**args):
    return args


def peak(pk):
    # samity check
    if pk.assignment != '?-?':
        a, b = pk.assignment, '-'.join([r.name for r in pk.resonances()])
        if a != b:
            print "oops -- assignment doesn't match resonances -- (%s, %s)" % (a, b)
    # here's the real deal
    return kwargs(type='peak', 
                  frequency=pk.frequency, 
                  volume=pk.volume,
                  height={'fit': pk.fit_height, 'closest': pk.data_height}, 
                  assn=pk.assignment,
                  alias=pk.alias, 
                  position=pk.position,
                  volume_method=pk.volume_method,
                  id=pk.sparky_id)


def resonance(res):
    return kwargs(type='resonance', name=res.name, 
                  atom=extract(res.atom),
                  group=extract(res.group), 
                  frequency=res.frequency, 
                  peak_ids=[p.sparky_id for p in res.peak_list()],
                  id=res.sparky_id)


def atom(at):
    return kwargs(type='atom',
                  name=at.name,
                  nucleus=at.nucleus,
                  group=group(at.group),
                  id=at.sparky_id)


def group(grp):
    return kwargs(type='group',
                  name=grp.name,
                  symbol=grp.symbol,
                  number=grp.number,
                  suffix=grp.suffix,
                  id=grp.sparky_id)


def molecule(mol):
    return kwargs(type='molecule',
                  name=mol.name,
                  atoms=map(atom, mol.atom_list()),
                  groups=map(group, mol.group_list()),
                  id=mol.sparky_id)


def spectrum(spc):
    return kwargs(type='spectrum',
                  name=spc.name,
                  dims=spc.dimension,
                  sw=spc.sweep_width,
                  peaks=map(extract, spc.peak_list()),
                  id=spc.sparky_id)


dispatch = {
        sparky.Atom      : atom      ,
        sparky.Peak      : peak      ,
        sparky.Resonance : resonance ,
        sparky.Group     : group     ,
        sparky.Molecule  : molecule  ,
        sparky.Spectrum  : spectrum
    }


def extract(my_object):
    """
    extract the data from a Sparky object model into dictionaries, arrays, and scalars
    
    purposes:
     1. serialization
     2. not all properties show up in reflection (perhaps b/c there's a wrapper over C++ code)
     3. some objects (atoms, groups) can't be printed
     4. get rid of redundancy
    """
    for (my_type, f) in dispatch.items():
        if isinstance(my_object, my_type):
            return f(my_object)
    raise TypeError('unable to extract Sparky value with keys ' + str(dir(my_object)))


def traverse(my_object, pred, f):
    def traverse_help(obj, context, result):
        if pred(context):
            result.append((context, f(obj)))
        if isinstance(obj, dict):
            for (key, val) in obj.iteritems():
                traverse_help(val, context + (key,), result)
        elif isinstance(obj, list):
            for (ix, val) in enumerate(obj): # in python2.5, can't use `start` keyword argument
                traverse_help(val, context + (str(ix),), result)
    out = []
    traverse_help(my_object, (), out)
    return out
