import tkutil
import sputil
import r_peaktypes as peaktypes
import r_model as model
import r_dump as dump
from r_git import GitRepo



class Peak_grouper_dialog(tkutil.Dialog):

    def __init__(self, session):
        self.session = session
        self.title = 'Assign peaks into GSSs'
        
        tkutil.Dialog.__init__(self, session.tk, self.title)

        _spectrum_names = [sp.name for sp in model.spectra()]
        self.spec_from = m1 = tkutil.option_menu(self.top, 'Using selected peaks in spectrum:', _spectrum_names)
        m1.frame.pack(side='top', anchor='w')
        
        self.spec_to = m2 = tkutil.option_menu(self.top, 'Assign peaks to GSSs in spectrum:', _spectrum_names)
        m2.frame.pack(side='top', anchor='w')
        
        _d3 = [1, 2, 3] # TODO do those values need to be strings?
        
        # matching dimension 1
        self.match1_from = m3 = tkutil.option_menu(self.top, 'Matching dimension 1: from:', _d3)
        m3.frame.pack(side='top', anchor='w')
        
        self.match1_to = m4 = tkutil.option_menu(self.top, 'Matching dimension 1: to:', _d3)
        m4.frame.pack(side='top', anchor='w')
        
        self.tol1 = tkutil.entry_field(self.top, 'Matching dimension 1: tolerance (PPM):', '0.2', 20)
        self.tol1.frame.pack(side = 'top', anchor = 'w')

        # matching dimension 2
        self.match2_from = tkutil.option_menu(self.top, 'Matching dimension 2: from:', _d3)
        self.match2_from.frame.pack(side='top', anchor='w')
        
        self.match2_to = tkutil.option_menu(self.top, 'Matching dimension 2: to:', _d3)
        self.match2_to.frame.pack(side='top', anchor='w')
        
        self.tol2 = tkutil.entry_field(self.top, 'Matching dimension 2: tolerance (PPM):', '0.2', 20)
        self.tol2.frame.pack(side = 'top', anchor = 'w')

        # TODO check that the nuclei match
        # TODO are 2 matching dimensions enough?
    
        br = tkutil.button_row(self.top,
                    ('Assign peaks', self.execute),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')
    
    
    def execute(self):
        def extract_int(widget):
            return int(widget.variable.get()) - 1
        d1 = [extract_int(self.match1_from), 
              extract_int(self.match1_to),
              float(self.tol1.variable.get())]
        d2 = [extract_int(self.match2_from),
              extract_int(self.match2_to),
              float(self.tol2.variable.get())]
        model.group_peaks_into_gss([d1, d2], 
                                   self.spec_from.variable.get(),
                                   self.spec_to.variable.get())
    


class Snapshot_dialog(tkutil.Dialog):

    def __init__(self, session):
        self.g = GitRepo(model.project().sparky_directory)
        
        self.session = session
        self.title = 'Reproducibility'
        
        tkutil.Dialog.__init__(self, session.tk, self.title)
        
        br = tkutil.button_row(self.top, ('Make snapshot', self.make_snapshot))
        br.frame.pack(side='top', anchor='w')
        # TODO would like to get an enumerated list of these from somewhere
        e = tkutil.entry_field(self.top, 'Deductive reason used:', '<enter reason>', 50)
        e.frame.pack(side='top', anchor='w')
        self.message = e.variable

        br2 = tkutil.button_row(self.top, ('Set groups of selected peaks', self.set_group))
        br2.frame.pack(side = 'top', anchor = 'w')
        e2 = tkutil.entry_field(self.top, 'Group name:', '', 20, '(leave blank for name to be autogenerated)')
        e2.frame.pack(side = 'top', anchor = 'w')
        self.group = e2.variable

        br4 = tkutil.button_row(self.top, ('Create new group for peak', self.create_new_group))
        br4.frame.pack(side = 'top', anchor = 'w')

        br5 = tkutil.button_row(self.top, ('Set selected peaks to noise', self.set_noise))
        br5.frame.pack(side = 'top', anchor = 'w')

        br6 = tkutil.button_row(self.top, ('Set selected peaks to artifact', self.set_artifact))
        br6.frame.pack(side = 'top', anchor = 'w')
        
        self.peaktype_spectrum = m1 = tkutil.option_menu(self.top, 'Select peaktype spectrum', peaktypes.spectra.keys())
        m1.frame.pack(side='top', anchor='w')
        m1.add_callback(self.set_peaktype_spectrum)
        
        self.peaktype_dim_order = m3 = tkutil.option_menu(self.top, 'Peaktype dimension order', [])
        self.dim_order = ','.join(map(str, peaktypes.orders[1][0]))
        m3.frame.pack(side='top', anchor='w')
        m3.add_callback(self.set_peaktype_dim_order)
        
        self.peaktype = m2 = tkutil.option_menu(self.top, 'Assign peaktype', [])
        m2.frame.pack(side='top', anchor='w')
        m2.add_callback(self.assign_peaktype)

        _spectrum_names = [sp.name for sp in model.spectra()]
        self.select_signal_peaks_menu = m4 = tkutil.option_menu(self.top, 'Select signal peaks', _spectrum_names)
        m4.frame.pack(side='top', anchor='w')
        m4.add_callback(self.select_signal_peaks)

        self.changed_callback = model.session().notify_me('selection changed', self.selection_changed)
    
        br = tkutil.button_row(self.top,
                    ('Open peak-GSS dialog', self.peaks_to_gss),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')



    def selection_changed(self):
        pass
    
    def make_snapshot(self):
        # TODO could track whether the files have been saved or not since the last time a snapshot was taken ... maybe?
        try:
            self.g.dump(self.message.get())
            print 'successfully captured git snapshot'
        except Exception, e:
            print 'exception!', e
        
    def create_new_group(self):
        model.create_group_for_peak()
    
    def set_group(self):
        name = self.group.get()
        if name == '':
            model.set_new_group()
        else:
            model.set_group(name)
    
    def set_noise(self):
        model.set_noise()
    
    def set_artifact(self):
        model.set_artifact()
    
    def set_peaktype_spectrum(self, spectrum):
        self.peaktype.remove_all_entries()
        for pt in peaktypes.spectra[spectrum]:
            self.peaktype.add_entry(','.join(pt))
        self.peaktype_dim_order.remove_all_entries()
        for o in peaktypes.orders[len(pt) - 1]:
            self.peaktype_dim_order.add_entry(','.join(map(str, o)))
    
    def set_peaktype_dim_order(self, order):
        self.dim_order = order.split(',')
    
    def assign_peaktype(self, peaktype):
        pt = peaktype.split(',')
        my_pt = [y for (_, y) in sorted(zip(self.dim_order, pt), key=lambda x: x[0])]
        model.assign_peaktype(my_pt)

    def select_signal_peaks(self, name):
        model.select_signal_peaks(name)
    
    def peaks_to_gss(self):
        show_peak_grouper_dialog(self.session)



def show_snapshot_dialog(session):
    d = sputil.the_dialog(Snapshot_dialog, session)
    d.show_window(1)

def show_peak_grouper_dialog(session):
    d = sputil.the_dialog(Peak_grouper_dialog, session)
    d.show_window(1)
