import r_model as model
import simplejson as json
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
    extra = spc.saved_value('extra')
    extra = json.loads(extra) if extra is not None else {}
    return {
        'type'      : 'spectrum',
        'name'      : spc.name,
        'noise'     : spc.noise,
        'keyvals'   : extra,
        'dims'      : spc.dimension,
        'sw'        : spc.sweep_width,
        'region'    : spc.region,
        'hz_per_ppm': spc.hz_per_ppm,
        'data_size' : spc.data_size,
        'nuclei'    : spc.nuclei,
        'peaks'     : map(lambda (ix, pk): peak(pk, ix + 1),
                          enumerate(spc.peak_list())) # this is intended to match the Sparky numbering
    }


def project(proj):
    # ugh ... so ugly to have to use JSON here, but the saved_value has to be a string
    extra = proj.saved_value('extra')
    extra = json.loads(extra) if extra is not None else {}
    notes = proj.saved_value('notes')
    notes = json.loads(notes) if notes is not None else []
    return {
        'type'      : 'project',
        'path'      : proj.save_path,
        'dir'       : proj.sparky_directory,
        'groups'    : groups(),
        'keyvals'   : extra,
        'notes'     : notes,
        'spectra'   : dict([(sp.name, spectrum(sp)) for sp in proj.spectrum_list()])
    }


def full_dump():
    return project(model.project())
