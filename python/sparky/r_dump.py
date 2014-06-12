import sparky
import r_model as model


def groups():
    gs_info, _, _ = model.resonance_map()
    return gs_info
    

def _parse_assignment(res):
    """
    extract gid, rid for a Sparky resonance
    """
    if res is None:
        return None
    gid, _, _, _ = model.parse_group(res.group.name)
    rid, _       = model.parse_resonance(res.atom.name)
    return (gid, rid)


def peak(pk, my_id):
    # sanity check
    if pk.assignment != '?-?':
        a, b = pk.assignment, '-'.join([r.name for r in pk.resonances()])
        if a != b:
            print "oops -- assignment doesn't match resonances -- (%s, %s)" % (a, b)
    # here's the real deal
    return {
        'type'          : 'peak',
        'note'          : pk.note,
        'frequency'     : pk.frequency,
        'volume'        : pk.volume,
        'height'        : {'fit': pk.fit_height, 'closest': pk.data_height}, 
        'resonances'    : map(_parse_assignment, pk.resonances()),
        'alias'         : pk.alias,
        'position'      : pk.position,
        'volume_method' : pk.volume_method,
        'id'            : my_id
    }


def spectrum(spc):
    return {
        'type'      : 'spectrum',
        'name'      : spc.name,
        'noise'     : spc.noise,
        'keyvals'   : {}, # TODO
        'dims'      : spc.dimension,
        'sw'        : spc.sweep_width,
        'region'    : spc.regiono,
        'hz_per_ppm': spc.hz_per_ppm,
        'data_size' : spc.data_size,
        'nuclei'    : spc.nuclei,
        'peaks'     : map(lambda (ix, pk): peak(pk, ix + 1),
                          enumerate(spc.peak_list()))
    }


def project(proj):
    return {
        'type'      : 'project',
        'path'      : proj.save_path,
        'dir'       : proj.sparky_directory,
        'groups'    : groups(),
        'keyvals'   : {}, # TODO
        'spectra'   : dict([(sp.name, spectrum(sp) for sp in proj.spectrum_list()]))
    }

