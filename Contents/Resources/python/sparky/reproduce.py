import simplejson as json
import os
from .extractor import extract, traverse
import gitdumper


sess = None
some_data = {}
run = 0
hsqc = None
peaks = None
resonances = None
atom = None
group = None


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
    peaks[3].assign(0, '22', 'CA')
    peaks[3].assign(1, '22', 'CA(i/1)')
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
        myhandle.write(dumpJSON(_my_object))
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
        myhandle.write(dumpJSON(map(extract, peaks)))
        myhandle.write('\n\n')
        resonances = []
        for p in peaks:
            for r in p.resonances():
                if r is None:
                    resonances.append(r)
                else:
                    resonances.append(extract(r))
        myhandle.write(dumpJSON(resonances))
        print 'wrote file: ', myhandle.name
        myhandle.close()
    except Exception, e:
        print 'oops!', e, dir(e), e.message
        raise


def write_dump_file(session):
    global run
    hsqc = session.project.spectrum_list()[0]
    peaks = hsqc.peak_list()
    molecs = session.project.molecule_list()
    try:
        run += 1
        home = os.path.expanduser("~")
        myhandle = open(home + "/Sparky/JSON/file" + str(run) + '.txt', 'w')
        json_peaks = map(extract, peaks)
        myhandle.write(dumpJSON(json_peaks))
#        print traverse(json_peaks, lambda c: len(c) > 0 and c[-1] == 'id', lambda x: x)
#        print extract(hsqc)
        print traverse(extract(hsqc), lambda c: len(c) > 0 and c[-1] == 'id', lambda x: x)
        myhandle.write(dumpJSON(map(extract, molecs)))
        print 'wrote file: ', myhandle.name
        myhandle.close()
    except Exception, e:
        print 'oops!', e
        raise


def grab_some_data(session):
    global sess, some_data, hsqc, peaks, resonances, atom, group
    sess = session
    some_data['hsqc'] = hsqc = session.project.spectrum_list()[0]
    some_data['peaks'] = peaks = hsqc.peak_list()
    some_data['resonances'] = resonances = peaks[2].resonances()
    some_data['atom'] = atom = resonances[0].atom
    some_data['group'] = group = resonances[0].group


def git_dump(session):
    gitdumper.dump(dumpJSON(map(extract, session.project.spectrum_list())))
