import simplejson as json
import os


sess = None
some_data = {}
run = 0
hsqc = None
peaks = None
resonances = None
atom = None
group = None


def kwargs(**args):
    return args


def peakToJSONObj(pk):
    return kwargs(type='peak', frequency=pk.frequency, volume=pk.volume,
                  height={'fit': pk.fit_height, 'closest': pk.data_height}, 
                  assn=pk.assignment,
                  alias=pk.alias, position=pk.position,
                  volume_method=pk.volume_method,
                  id=pk.sparky_id)


def resonanceToJSONObj(res):
    if res is None:
        return kwargs(type='resonance')
    return kwargs(type='resonance', name=res.name, 
                  #atom=res.atom,
                  #group=res.group, 
                  frequency=res.frequency, 
                  peak_ids=[p.sparky_id for p in res.peak_list()],
                  id=res.sparky_id)


def dumpJSON(my_object):
    return json.dumps(my_object, sort_keys=True, indent=2)


def some_resonances(session):
    peaks = session.project.spectrum_list()[0].peak_list()
    peaks[0].assign(0, '22', 'H')
    peaks[0].assign(1, '22', 'N')
    peaks[1].assign(0, '23', 'H')
    peaks[1].assign(1, '24', 'N')
    peaks[2].assign(0, 'SS42qrs', 'HA[2]')
    peaks[2].assign(1, 'SS42qrs', 'N')
    peaks[4].assign(0, '22', 'CA(i/1)')
    peaks[4].assign(1, '23', 'CA')
    peaks[5].assign(0, 'QQ', 'CA(i\\1)')
    peaks[5].assign(1, 'RR', 'CA')
    print peaks[0:6]


def write_json_file(my_object):
    # does this correctly clean up the resources if there's a failure?
    global run
    try:
        run += 1
        home = os.path.expanduser("~")
        dir = home + "/Sparky/JSON/"
        name = 'file' + str(run) + ".txt"
        myhandle = open(dir + name, 'w')
        myhandle.write(dumpJSON_my_object)
    except Exception, e:
        print 'oops while writing file: ', e
        raise


def write_peak_files(session):
    global run
    peaks = session.project.spectrum_list()[0].peak_list()
    try:
        run += 1
        home = os.path.expanduser("~")
        myhandle = open(home + '/Sparky/JSON/file' + str(run) + '.txt', 'w')
#        myhandle.write(str(peaks))
        myhandle.write(dumpJSON(map(peakToJSONObj, peaks)))
        resonances = []
        for p in peaks:
            for r in p.resonances():
                resonances.append(resonanceToJSONObj(r))
#            resonances.append()
#        dumpJSON([map(resonanceToJSONObj, p.resonances()) for p in peaks])
        myhandle.write(dumpJSON(resonances))
        print 'wrote file: ', os.getcwd() + "/" + myhandle.name
        myhandle.close()
    except Exception, e:
        print 'oops!', e, dir(e), e.message
        raise


def grab_some_data(session):
    global sess, some_data, hsqc, peaks, resonances, atom, group
    sess = session
    some_data['hsqc'] = hsqc = session.project.spectrum_list()[0]
    some_data['peaks'] = peaks = hsqc.peak_list()
    some_data['resonances'] = resonances = peaks[2].resonances()
    some_data['atom'] = atom = resonances[0].atom
    some_data['group'] = group = resonances[0].group
