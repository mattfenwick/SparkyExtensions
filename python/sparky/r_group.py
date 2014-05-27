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
                    ('Reset', self.reset),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')
        
        self.reset()


    def click_on_listbox(self, *args):
        ds = self.group_data.selected_line_data()
        if len(ds) != 1:
            raise ValueError('expected 1 line selected, got 0 or 2+')
        d = ds[0]
        if d['type'] == 'group':
            show_group_editor(self.session, d['gid'], d['aatype'], d['next'], d['residue'], self)
        elif d['type'] == 'resonance':
            show_resonance_editor(self.session, d['gid'], d['rid'], d['atomtype'], self)
        elif d['type'] == 'blank line':
            pass
        else:
            raise ValueError('unexpected line data type -- %s' % str(d['type']))
        print args, dir(args[0]), self.group_data.listbox.curselection(), self.group_data.selected_line_data()
    
    def reset(self):
        pos = self.group_data.listbox.yview()
        self.group_data.clear()
        gs, _, gs_info = model.resonance_map()
        for gid in sorted(gs_info.keys(), key=lambda x: int(x)):
            g = gs_info[gid]
            text = 'Group %s, residue %s, next GSS %s, GSS type %s' % (gid, g['residue'], g['next'], g['aatype'])
            self.group_data.append(text, {'type': 'group', 'gid': gid, 'residue': g['residue'], 'aatype': g['aatype'], 'next': g['next']})
            for rid in sorted(g['resonances']):
                line = 'Group %s: resonance %s:  atomtype %s, shift %s' % (gid, rid, g['resonances'][rid], gs[gid][rid].frequency)
                self.group_data.append(line, {'type': 'resonance', 'gid': gid, 'rid': rid, 'atomtype': g['resonances'][rid]})
            self.group_data.append('', {'type': 'blank line'})
        self.group_data.listbox.yview_moveto(pos[0])



class Group_editor(tkutil.Dialog):
    
    def __init__(self, session, gid=None, group_editor=None):
        self.session = session
        self.gid = gid
        self.group_editor = group_editor
        
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
                    ('Apply', self.update),
                    ('Merge resonances', self.merge_resonances),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')
    
    def setup(self, gid, aatype, next_, residue, group_editor):
        """
        work-around -- should be passed in to constructor, but the thing
        which instantiates this class doesn't pass any args
        """
        self.gid = gid
        self.top.title('Group editor -- %s' % gid)
        self.aatype.set(aatype)
        self.next_.set(next_)
        self.residue.set(residue)
        self.group_editor = group_editor

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
        self.group_editor.reset()
    
    def merge_resonances(self):
        show_merge_resonance_editor(self.session, self.gid, self.group_editor)



class Resonance_editor(tkutil.Dialog):
    
    def __init__(self, session, gid=None, rid=None, group_editor=None):
        self.gid = gid
        self.rid = rid
        self.group_editor = group_editor
        
        tkutil.Dialog.__init__(self, session.tk, 'Resonance editor --- ???')
        
        e1 = tkutil.entry_field(self.top, 'Atom type:', '', 20)
        e1.frame.pack(side='top', anchor='w')
        self.atomtype = e1.variable
    
        br = tkutil.button_row(self.top,
                    ('Apply', self.update),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')
    
    def setup(self, gid, rid, atomtype, group_editor):
        self.gid = gid
        self.top.title('group %s, resonance %s' % (gid, rid))
        self.rid = rid
        self.atomtype.set(atomtype)
        self.group_editor = group_editor
    
    def set_resonance_atomtype(self):
        model.set_atomtype(self.gid, self.rid, self.atomtype.get())
    
    def update(self):
        self.set_resonance_atomtype()
        self.group_editor.reset()


class Merge_resonance_editor(tkutil.Dialog):
    
    def __init__(self, session, gid=None, group_editor=None):
        self.session = session
        self.gid = gid
        self.group_editor = group_editor
        
        tkutil.Dialog.__init__(self, session.tk, 'merge resonances -- ???')
        
        self.rid1 = m1 = tkutil.option_menu(self.top, 'Resonance 1', [])
        m1.frame.pack(side='top', anchor='w')
        
        self.rid2 = m2 = tkutil.option_menu(self.top, 'Resonance 2', [])
        m2.frame.pack(side='top', anchor='w')
    
        br = tkutil.button_row(self.top,
                    ('Merge', self.merge_resonances),
                    ('Close', self.close_cb),
                    )
        br.frame.pack(side = 'top', anchor = 'w')
    
    def reset(self):
        _, _, gs_info = model.resonance_map()
        rids = sorted(gs_info[self.gid]['resonances'].keys())
        self.rid1.remove_all_entries()
        self.rid2.remove_all_entries()
        for rid in rids:
            self.rid1.add_entry(rid)
            self.rid2.add_entry(rid)
    
    def setup(self, gid, group_editor):
        self.top.title('merge resonances -- group %s' % gid)
        self.gid = gid
        self.group_editor = group_editor
        self.reset()
    
    def merge_resonances(self):
        rid1, rid2 = self.rid1.variable.get(), self.rid2.variable.get()
        model.merge_resonances(self.gid, rid1, [rid2])
        self.reset()
        self.group_editor.reset()
        



def show_group_editor(session, gid, aa, n, r, grp_editor):
    d = sputil.the_dialog(Group_editor, session)
    d.setup(gid, aa, n, r, grp_editor)
    d.show_window(1)

def show_resonance_editor(session, gid, rid, atomtype, grp_editor):
    d = sputil.the_dialog(Resonance_editor, session)
    d.setup(gid, rid, atomtype, grp_editor)
    d.show_window(1)

def show_merge_resonance_editor(session, gid, group_editor):
    d = sputil.the_dialog(Merge_resonance_editor, session)
    d.setup(gid, group_editor)
    d.show_window(1)

def show_group_dialog(session):
    d = sputil.the_dialog(Group_dialog, session)
    d.show_window(1)
