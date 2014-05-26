import sparky
import r_model as model
import tkutil
import sputil
import r_peaktypes as peaktypes
import simplejson as json


aatypes = [
    '?',
    'b', # ambiguous backbone
    'R', 'H', 'K', 'D', 'E', 'S', 'T', 'N', 'Q', 'W', 
    'C', 'G', 'P', 'A', 'V', 'I', 'L', 'M', 'F', 'Y', 
    'S/T', 'sN', 'sQ', 'sN/Q', 'sR', 'sW', 'sK'
]


class Group_dialog(tkutil.Dialog, tkutil.Stoppable):

    def __init__(self, session):
        self.session = session
        self.title = 'Group dialog'
        
        tkutil.Dialog.__init__(self, session.tk, self.title)

        br1 = tkutil.button_row(self.top, ('Select group', self.select_group))
        br1.frame.pack(side='top', anchor='w')
        e1 = tkutil.entry_field(self.top, 'Group name:', '', 20)
        e1.frame.pack(side='top', anchor='w')
        self.group_name = e1.variable
        
        # modify things
        #   gid
        #     aatype, next, residue
        #   resonance
        #     merge
        #     atomtype
        
        # use group_data.listbox.bind to add my own callbacks (see peaklist for an example)
        self.group_data = tkutil.scrolling_list(self.top, 'Group data', 5)
        self.group_data.frame.pack(side = 'top', fill = 'both', expand = 1)
        self.group_data.listbox.bind('<ButtonRelease-1>', self.click_on_listbox)

        # display things
        #   aatype, next, residue
        #   resonances in group
        #     aatype
        #     shift
        #     low, high shifts of peak dimensions
        
        # when peak selection is changed, if the peak's resonances are all
        #   only assigned to a single group, make that the active group

        br = tkutil.button_row(self.top,
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')




    def click_on_listbox(self, *args):
        ds = self.group_data.selected_line_data()
        if len(ds) != 1:
            raise ValueError('expected 1 line selected, got 0 or 2+')
        d = ds[0]
        if d['type'] == 'group':
            show_group_editor(self.session, d['gid'], d['aatype'], d['next'], d['residue'])
        elif d['type'] == 'resonance':
            show_resonance_editor(self.session, **d['args'])
        print args, dir(args[0]), self.group_data.listbox.curselection(), self.group_data.selected_line_data()
    
    def reset(self):
        self.group_data.clear()
        gs, _, gs_info = model.resonance_map()
        for gid in sorted(gs_info.keys()):
            g = gs_info[gid]
            text = 'Group %s, residue %s, next GSS %s, aatype %s' % (gid, g['residue'], g['next'], g['aatype'])
            self.group_data.append(text, {'type': 'group', 'gid': gid, 'residue': g['residue'], 'aatype': g['aatype'], 'next': g['next']})
            for rid in sorted(g['resonances']):
                line = 'Group %s: resonance %s:  atomtype %s, shift %s' % (gid, rid, g['resonances'][rid], gs[gid][rid].frequency)
                self.group_data.append(line, {'type': 'resonance', 'rid': rid, 'atomtype': g['resonances'][rid]})

    def selection_changed(self):
        rs = []
        for pk in model._selected_peaks():
            rs.extend(pk.resonances())
        gs, _, gs_info = model.resonance_map(set(rs))
        if len(gs_info) == 1:
            k = gs_info.keys()[0]
            # do some stuff ... populate widgets


class Group_editor(tkutil.Dialog):
    
    def __init__(self, session, gid=None):
        self.gid = gid
        tkutil.Dialog.__init__(self, session.tk, 'Group editor -- ???')
        
        e1 = tkutil.entry_field(self.top, 'GSS type:', '', 20)
        e1.frame.pack(side='top', anchor='w')
        self.aatype = e1.variable
    
        e2 = tkutil.entry_field(self.top, 'Next GSS:', '', 20)
        e2.frame.pack(side='top', anchor='w')
        self.next_ = e2.variable
    
        e3 = tkutil.entry_field(self.top, 'Residue:', '', 20)
        e3.frame.pack(side='top', anchor='w')
        self.residue = e3.variable
    
        br = tkutil.button_row(self.top,
                    ('Update', self.update),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')
    
    def setup(self, gid, aatype, next_, residue):
        """
        work-around -- should be passed in to constructor, but the thing
        which instantiates this class doesn't pass any args
        """
        self.gid = gid
        self.top.title('Group editor -- %s' % gid)
        self.aatype.set(aatype)
        self.next_.set(next_)
        self.residue.set(residue)

    def set_group_aatype(self):
        model.set_aatype(self.gid, self.aatype.get())
    
    def set_group_residue(self):
        model.set_residue(self.gid, self.residue.get())
    
    def set_seq_ss(self):
        model.set_seq_ss(self.gid, 
                         self.next_.get())
    
    def update(self):
        self.set_group_aatype()
        self.set_group_residue()
        self.set_seq_ss()



class Resonance_editor(tkutil.Dialog):
    
    def __init__(self, session, rid):
        tkutil.Dialog.__init__(self, session.tk, 'Resonance editor --- ???')
        
        e1 = tkutil.entry_field(self.top, 'Atom type:', '', 20)
        e1.frame.pack(side='top', anchor='w')
        self.aatype = e1.variable
    
        e2 = tkutil.entry_field(self.top, 'next GSS:', '', 20)
        e2.frame.pack(side='top', anchor='w')
        self.next_ = e2.variable
            
    def set_resonance_atomtype(self):
        model.set_atomtype(self.res_group_name.get(), 
                           self.set_resonance.variable.get(), 
                           self.res_atom.get())
    
    def merge_resonances(self):
        # what a hack
        params = self.merge_resonances_var.get().split(',')
        gid, rid1, rids = params[0], params[1], params[2:]
        model.merge_resonances(gid, rid1, rids)



def show_group_editor(session, gid, aa, n, r):
    d = sputil.the_dialog(Group_editor, session)
    d.setup(gid, aa, n, r)
    d.show_window(1)

def show_group_dialog(session):
    d = sputil.the_dialog(Group_dialog, session)
    d.show_window(1)
