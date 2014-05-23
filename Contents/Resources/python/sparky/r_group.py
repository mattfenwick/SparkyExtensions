import sparky
from . import r_model as model
import tkutil
import sputil
import r_peaktypes as peaktypes
import simplejson as json



class Group_dialog(tkutil.Dialog):

    def __init__(self, session):
        self.session = session
        self.title = 'Group editor'
        
        tkutil.Dialog.__init__(self, session.tk, self.title)
        
        # modify things
        #   gid
        #     aatype, next, residue
        #   resonance
        #     merge
        #     aatype

        # display things
        #   aatype, next, residue
        #   resonances in group
        #     aatype
        #     shift
        #     low, high shifts of peak dimensions
        
        # when peak selection is changed, if the peak's resonances are all
        #   only assigned to a single group, make that the active group


    def selection_changed(self):
        rs = []
        for pk in model._selected_peaks():
            rs.extend(pk.resonances())
        gs, _, gs_info = model.resonance_map(set(rs))
        if len(gs_info) == 1:
            k = gs_info.keys()[0]
            self.group_name.set(k)
            self.group_name_aatype.set(k)
            self.res_group_name.set(k)
            self.set_resonance.remove_all_entries()
            for x in gs_info[k]['resonances'].keys():
                self.set_resonance.add_entry(x)

    def make_snapshot(self):
        self.g.dump(self.message.get())
    
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
    
    def set_group_aatype(self, aatype):
        gid = self.group_name_aatype.get()
        model.set_aatype(gid, aatype)
    
    def set_group_residue(self):
        model.set_residue(self.group_name.get(), self.residue_name.get())
    
    def set_resonance_atomtype(self):
        model.set_atomtype(self.res_group_name.get(), 
                           self.set_resonance.variable.get(), 
                           self.res_atom.get())
    
    def set_seq_ss(self):
        model.set_seq_ss(self.seq_ss_prev.get(), 
                         self.seq_ss_next.get())

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

    def select_signal_peaks(self):
        name = self.select_signal_peaks_name.get()
        model.select_signal_peaks(name)

    def group_peaks_into_gss(self):
        # what a hack with JSON here
        params = json.loads(self.group_peaks_parameters.get())
        model.group_peaks_into_gss(*params)
    
    def merge_resonances(self):
        # what a hack
        params = self.merge_resonances_var.get().split(',')
        gid, rid1, rids = params[0], params[1], params[2:]
        model.merge_resonances(gid, rid1, rids)



def show_group_dialog(session):
    d = sputil.the_dialog(Group_dialog, session)
    d.show_window(1)
