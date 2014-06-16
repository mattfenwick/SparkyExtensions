import r_model as model
# module purpose:
#   convert Sparky data model to JSON-compatible objects
#   for serializing as text in a file



def groups():
    """
    convert resonance_map output into pure JSON-compatible data structure (i.e. no Sparky objects)
    """
    gs_info, _, gs = model.resonance_map()
    my_groups = {}
    for (gid, g) in gs_info.items():
        my_g = gs[gid]
        my_groups[gid] = {
            'residue': my_g['residue'],
            'aatype': my_g['aatype'],
            'next': my_g['next'],
            'resonances': dict([(rid, {'atomtype': atomtype, 'shift': g[rid].frequency, 'deviation': g[rid].deviation}) 
                                for (rid, atomtype) in my_g['resonances'].items()])
        }
    return my_groups
    

def _parse_assignment(res):
    """
    extract gid, rid for a Sparky resonance
    """
    if res is None:
        return None
    gid, _, _, _ = model.parse_group(res.group.name) # other 3 fields are accessed through group
    rid, _       = model.parse_resonance(res.atom.name) # other 1 field accessed through resonance
    return (gid, rid)


def peak(pk, my_id):
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
        'region'    : spc.region,
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
        'spectra'   : dict([(sp.name, spectrum(sp)) for sp in proj.spectrum_list()])
    }


def full_dump():
    return project(model.project())
