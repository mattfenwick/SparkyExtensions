import simplejson as json
import os


sess = None
some_data = {}
run = 0


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
    peaks[2].assign(0, 'AB', 'H')
    peaks[2].assign(1, 'CB', 'N')
    peaks[4].assign(0, '22', 'CA(i/1)')
    peaks[4].assign(1, '23', 'CA')
    peaks[5].assign(0, 'QQ', 'CA(i\\1)')
    peaks[5].assign(1, 'RR', 'CA')


def write_peak_files(session):
    global run
    peaks = session.project.spectrum_list()[0].peak_list()
    try:
        run += 1
        myhandle = open('file' + str(run) + '.txt', 'w')
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
    global some_data
    print session
    print session.project
    print session.project.spectrum_list()
    some_data['hsqc'] = hsqc = session.project.spectrum_list()[0]
    some_data['peaks'] = peaks = hsqc.peak_list()
    some_data['pk3'] = pk3 = peaks[3]
    some_data['rs3'] = rs3 = pk3.resonances()
    pk3.assign(0, '22', 'CA(i-1)')
    pk3.assign(1, '22', 'CA')
    try:
        pk3.assign(2, '22', 'CB')
    except:
        print 'too many dimensions!'
    print peaks[2:6]


def doit(session):
  global sess
  sess = session
  print session
  raise ValueError(str(session))

def doittoit(session):
  print session.__dict__
