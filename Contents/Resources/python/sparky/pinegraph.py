# -----------------------------------------------------------------------------
# Graph for assignment of PINE outputs.
# -----------------------------------------------------------------------------
#
# Developed by Woonghee Lee
# e-mail: whlee@nmrfam.wisc.edu
# National Magnetic Resonance Facilities at Madison
# Department of Bichemistry, University of Wisconsin at Madison
#
# Last updated: May 10, 2010
# 
# Usage:
#
# 
# -----------------------------------------------------------------------------
import Tkinter
import types
import string
import sparky
import sputil
import pyutil
import tkutil
import pinelayout
#import pinesound
import tkMessageBox

# -----------------------------------------------------------------------------
#
class pine_graph(tkutil.Dialog, tkutil.Not_Stoppable):
  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):
    # Initialize variables
    self.session = session
    self.canvas = None
    self.selected_group = None
    self.selected_atom = None
    self.selected_groupatom = None
    self.selected_group_prev = None
    self.selected_group_next = None
    self.selected_spectrum = self.session.selected_spectrum()
    self.selected_index = -1
    self.sequences = []
    self.groups = []
    self.label_list = None

    self.selected_atom_obj = None
    
      
    tkutil.Dialog.__init__(self, session.tk, 'Pine Graph Assigner')
    
    keypress_cb = pyutil.precompose(sputil.command_keypress_cb, session)
    self.top.bind('<KeyPress>', keypress_cb)

    
    self.InitSequences()
    # set selected
    # spectrum
    self.InitSpectrum()
    # group&atom
    self.InitGroupAtom()
    
    # Setting up locations for each component
    self.canvas_frame = Tkinter.Frame(self.top, width = 600, height = 400)
    self.canvas_frame.pack(side='top', anchor='w')
    self.CreateCanvas(self.canvas_frame)            # Create Scrollable Canvas

    self.spectra_frame = Tkinter.Frame(self.top, width = 120, height = 200)
    self.spectra_frame.pack(side='left', anchor = 'nw')
    self.CreateSpectraList(self.spectra_frame)     # Create check boxes for spectra
    
    self.button_frame = Tkinter.Frame(self.top, width = 480, height = 30)
    self.button_frame.pack(side='top', anchor = 'nw')
    self.CreateButtonList(self.button_frame)     # Create buttons
    
    self.label_frame = Tkinter.Frame(self.top, width = 480, height = 170)
    self.label_frame.pack(side='top', anchor = 'nw')
    self.CreateLabelList(self.label_frame)       # Create peak lists
    # Updating components
    self.UpdateCanvas()
    self.UpdateSpectraList()
    self.UpdateLabelList()

  # ---------------------------------------------------------------------------
  # Set sequences
  #!
  def InitSequences(self):
    # set sequences
    self.sequences = []
    self.groups = []
    ga = []
    # loop labels of selected spectrum
    #tkMessageBox.showinfo('InitSequences', '1')
    for spectrum in self.session.project.spectrum_list():
        for pLabel in spectrum.label_list():                                     # M3CA-M3N-M3H[0.997]:(xx.xx,xxx.xx,x.xx)
            if pLabel.text == '?-?-?' or pLabel.text == '?-?':
                continue
            splited = pLabel.text.split('[')                        # (M3CA-M3N-M3H, [0.997]:(xx.xx,xxx.xx,x.xx))
            groupatoms = sputil.parse_assignment(splited[0])        # (('M3','CA'), ('M3','N'), ('M3','H'))
            for groupatom in groupatoms:
                if groupatom[0] == '':
                    continue

                ga = sputil.parse_group_name(groupatom[0])             # ('M', 3)
                if len(self.sequences) == 0:
                    self.sequences.append(ga)
                    self.groups.append('%s%d' % (ga[0], ga[1]) )
                    continue
                
                # check if parsed sequence is already existed or not
                if ga in self.sequences:                                 # X in XXXXXXXXXXXXX ?
                    continue                                        # if already exists, continue
                bAdded = 0
                for seq in self.sequences: 
                    if ga[1] < seq[1]:
                        idx = self.sequences.index(seq)
                        self.sequences.insert(idx, ga)
                        self.groups.insert(idx, '%s%d' % (ga[0], ga[1]) )
                        bAdded = 1
                        break
                if bAdded == 0:
                    self.sequences.append(ga)
                    self.groups.append('%s%d' % (ga[0], ga[1]) )
        
  # ---------------------------------------------------------------------------
  # Set selected spectrum
  #!
  def InitSpectrum(self):
    # Get currently selected spectrum
    self.selected_spectrum = self.session.selected_spectrum()
  # ---------------------------------------------------------------------------
  # Set selected group & atom
  #!
  def InitGroupAtom(self):
    self.selected_group = None
    self.selected_atom = None
    self.selected_groupatom = None
    self.selected_group_prev = None 
    self.selected_group_next = None
    
    # if nothing is selected, set first sequence as selected_group
    if len(self.selected_spectrum.selected_peaks()) == 0:
        if len(self.sequences) > 0:
            self.selected_group = self.sequences[0]
            self.selected_atom = 'CA'                       # Default: CA
            self.selected_groupatom = '%s%dCA' % (self.sequences[0][0], self.sequences[0][1])
            self.selected_group_prev = None
            self.selected_group_next = self.sequences[1]
            self.selected_index = 0
            return
    # if a peak is selected
    else:       
        # If the peak is assigned, get group and atom name
        selected_peak = self.selected_spectrum.selected_peaks()[0]
        bFind = 0
        # The peak should be assigned...
        if selected_peak.is_assigned == 1:
            # get index from first axis -> parse assignment
            groupatoms = sputil.parse_assignment(selected_peak.assignment)        # (('M3','CA'), ('M3','N'), ('M3','H'))
            index = groupatoms[0][1]
            # Find index
            for seq in self.sequences:
                if bFind == 1:
                    self.selected_group_next = seq
                    break
                if seq[1] == index:
                    self.selected_group = self.seq
                    self.selected_atom = 'CA'
                    self.selected_groupatom = '%s%dCA' % (seq[0], index)
                    self.selected_group_prev = seq2
                    self.selected_index = index
                    bFind = 1
                seq2 = seq
        else:
            szPos = '('
            for pos in selected_peak.position:
                szPos = szPos + ('%7.3f,' % pos).strip() 
            szPos = szPos.rstrip(',')
            szPos = szPos + ')'
            # Find nearest label & probability
            if len(self.sequences) > 0:
                for pLabel in self.selected_spectrum.label_list():
                    # Parse label_list
                    # selected_peak.position = position of pLabel
                    # Let's parse pLabel   : XXX-XXX-XXX[xxx.xxx]:(xxx.xxx,xxx.xxx,xxx.xxx)
                    splited = pLabel.text.split(':')     # (xxx.xxx,xxx.xxx,xxx.xxx)
                    if len(splited) < 2:
                        continue
                    #
                    #
                    if splited[1] == szPos:
                        # Parse index
                        splitedsplited = splited[0].split('[')
                        groupatoms = sputil.parse_assignment(splitedsplited[0])
                        index = sputil.group_number(groupatoms[0][0])
                        #index = groupatoms[0][1]
                        #tkMessageBox.showinfo('InitGroupAtom', index)
                        # Find index
                        
                        for seq in self.sequences:
                            if seq[1] == index:
                                if self.sequences.index(seq) > 0:
                                    self.selected_group_prev = self.sequences[self.sequences.index(seq)-1]
                                else:
                                    self.selected_group_prev = None
                                self.selected_group = seq    
                                self.selected_atom = 'CA'
                                self.selected_groupatom = '%s%dCA' % (seq[0], index)
                                if self.sequences.index(seq) < len(self.sequences)-1:
                                    self.selected_group_next = self.sequences[self.sequences.index(seq)+1]
                                else:
                                    self.selected_group_next = None
                                bFind = 1
                                self.selected_index = self.sequences.index(seq)
                                break
        if bFind == 0:
            if len(self.sequences) > 0:
                self.selected_group = self.sequences[0]
                self.selected_atom = 'CA'                       # Default: CA
                self.selected_groupatom = '%s%dCA' % (self.sequences[0][0], self.sequences[0][1])
                self.selected_group_prev = None
                self.selected_group_next = self.sequences[1]
                self.selected_index = 0            

  # ---------------------------------------------------------------------------
  # Create diagram canvas
  #!
  def CreateCanvas(self, parent):
    sc = Tkinter.Canvas(parent, width=600, height=400)
    self.canvas = sc
    self.canvas.bind('<ButtonRelease>', self.ButtonReleaseCB)
    sc.pack()  
    #sc = tkutil.scrollable_canvas(parent)
    #self.scanvas = sc
    #self.canvas = sc.canvas
    #self.canvas.bind('<ButtonRelease>', self.ButtonReleaseCB)
    return sc
  # ---------------------------------------------------------------------------
  #
  def ButtonReleaseCB(self, event):

    (x, y) = tkutil.canvas_coordinates(self.canvas, event)

    # outside ranges
    if x < 199 or x > 400:
        return
    if y < 21 or y > 400:
        return
    
    # Find Grid
    grid_x = int((x - 200) / 20) - 5
    grid_y = int((y - 20) / 20) - 5
    # Check group atom
    if not pinelayout.pine_layout.has_key(self.selected_group[0]):
        return
    layout = pinelayout.pine_layout[self.selected_group[0]]
    iCount = 1
    szKey = 'Atom%d' % (iCount)
    while layout.has_key(szKey):
        [szAtom, (x1, y1)] = layout[szKey]
        if x1 == grid_x and y1 == grid_y:
            self.selected_atom = szAtom
            break
        iCount = iCount+1
        szKey = 'Atom%d' % (iCount)
    # Update
    self.UpdateDialog()
    
  # ---------------------------------------------------------------------------
  #!
  # Create spectra list for showing possible peak lists
  def CreateSpectraList(self, parent):
    sl = modified_listbox(parent, 'Spectra List', 4, 10, "single")
    sl.listbox.bind('<ButtonRelease-1>', self.SelectSpectra_cb)
    self.spectra_list = sl
    sl.frame.pack(side = 'top', fill = 'both', expand = 1)
    
    return sl.frame
  # ---------------------------------------------------------------------------
  # Update peak lists when spectra selection is changed
  #!
  def SelectSpectra_cb(self, event):
    # add selected spectra to selected spectra list
    ed = self.spectra_list.event_line_data(event)
    if ed == None:
        return
    #espectra, dspectra = ed
    self.selected_spectrum = ed        # set selected spectrum
    # then update label list
    self.UpdateLabelList()
  # ---------------------------------------------------------------------------
  # Create button list
  #!
  def CreateButtonList(self, parent):    
    self.br = tkutil.button_row(parent,
                           ('<<', self.FastPrev),
                           ('<', self.Prev),
                           ('>', self.Next),
                           ('>>', self.FastNext),
                           ('Update', self.UpdateDialog),         
                           ('Assign', self.Assign),         
                           ('UnAssign', self.UnAssign), 
                           ('Close', self.close_cb),    
                          )
    self.br.frame.pack(side = 'top', anchor = 'w')
#    self.br2 = tkutil.button_row(parent,                          
#                           ('Play All', self.PlayAll),           
#                           ('Play Residue', self.PlayResidue),           
#                           ('Play Atom', self.PlayAtom),                                      
#                           ('Close', self.close_cb),           
#                          )
#    self.br2.frame.pack(side = 'top', anchor = 'w')
    
  # ---------------------------------------------------------------------------
  # Create label list
  def CreateLabelList(self, parent):
    ll = modified_listbox(parent, 'Label List', 49, 8, "multiple")
    #ll.listbox.bind('<ButtonRelease-1>', self.UpdateLabelList_cb)
    ll.listbox.bind('<Double-ButtonRelease-1>', self.MoveToSelected_cb)
    ll.listbox.bind('<ButtonRelease-3>', self.MoveToSelected_cb)
    self.label_list = ll
    ll.frame.grid(sticky='news')
    #ll.frame.pack(side = 'top', fill = 'both', expand = 1, anchor='nw')
    
    return ll.frame
  # ---------------------------------------------------------------------------
  # Update assignments when peak selection is changed
  #def UpdateLabelList_cb(self,event):
  #  update_canvas()
    
  # ---------------------------------------------------------------------------
  # Move to current selected
  #!
  def MoveToSelected_cb(self, event):
    # Get currently double clicked item
    ed = self.label_list.event_line_data(event)
    # Parsing d-clicked item
    dlabel = ed
    # Move to d-clicked item
    # parsing dlabel
    
    # if dlabel is not assigned,
    if dlabel == None:
        return

    splitedlabel = dlabel.split('(')
    if len(splitedlabel) > 1:
        splitedlabel2 = splitedlabel[1].split(')')
        pszFreq = splitedlabel2[0].split(',')
        freq = []
        ranges = []
            
        for szFreq in pszFreq:
            freq.append(eval(szFreq))
            
        # set ranges depending on atom types
        for atom_type in self.selected_spectrum.nuclei:
            if atom_type == '1H':
                ranges.append(0.03)
            elif atom_type == '13C':
                ranges.append(0.4)
            elif atom_type == '15N':
                ranges.append(0.4)
                     
        peak = sputil.closest_peak(freq, self.selected_spectrum.peak_list(), ranges)
        if peak:
            sputil.show_peak(peak)
            #sputil.show_spectrum_position(self.selected_spectrum, tuple(freq)):
 


  # ---------------------------------------------------------------------------
  # update canvas including texts
  #!  
  def UpdateCanvas(self):
    self.InitSequences()
    # Clean Canvas
    # Make grid
    self.ClearCanvas()
    # Drawing
    self.DrawCanvas()
  # ---------------------------------------------------------------------------
  # update spectra list    
  #!
  def UpdateSpectraList(self):
    # First, show up spectra list
    # Clear spectra list box
    self.spectra_list.clear()
    # Append spectra to the list box
    idx = -1
    for spectrum in self.session.project.spectrum_list():
      self.spectra_list.append(spectrum.name, spectrum)
      if spectrum == self.selected_spectrum:
          idx = self.spectra_list.listbox.size()-1
          self.selected_spectrum = spectrum
    # Select spectra
    if idx <> -1:
        self.spectra_list.listbox.selection_set(idx, )
        self.spectra_list.listbox.see(idx)

  # ---------------------------------------------------------------------------
  # update label list    
  # 1. Check selected spectra
  # 2. Check selected group atom
  # 3. Search labels from selected spectra which contains selected group atom    
  # 4. Show assignments
  #! 
  def UpdateLabelList(self):
      self.label_list.clear()
      if (self.selected_group == None) and (self.selected_atom == None):
          return

      if len(self.selected_atom) > 3:
          selected_atom = self.selected_atom[0:len(self.selected_atom)-1]
      else:
          selected_atom = self.selected_atom
      selected_group_atom = '%s%d%s' % (self.selected_group[0], self.selected_group[1], selected_atom)      # 'M13' + 'CA'
      
      spectra = self.selected_spectrum
      
      # find assigned_peaks which is related to the selected_group_atom
      assigned_peaks = []
      for peak in spectra.peak_list():
          if not peak.is_assigned:
              continue
          asns = sputil.parse_assignment(peak.assignment)
          filled_assignment = ''
          for asn in asns:
              filled_assignment = filled_assignment + asn[0] + asn[1] + '-'
          filled_assignment = filled_assignment.rstrip('-')
          #if peak.assignment.find(selected_group_atom, 0) <> -1:
          #tkMessageBox.showinfo('filled',filled_assignment)
          if filled_assignment.find(selected_group_atom, 0) <> -1:
              # distinguish C and CX
              if selected_atom != 'C' and selected_atom != 'H':
                  assigned_peaks.append(peak)
              else: # check string length of selected_atom
                  asns = sputil.parse_assignment(peak.assignment)
                  for asn in asns:
                      if asn == selected_group_atom:
                          assigned_peaks.append(peak)
                          break      
      
      self.label_list.listbox.selection_clear(0, 'end')
      
      in_file = open(self.selected_spectrum.save_path + '_pl', "r")
      try:
        for label in in_file.readlines():
          label = label.strip()
          # Check if label is related to the selected group and atom
          # Parsing text
          #tkMessageBox.showinfo('selected_group_atom',selected_atom)          
          if label.find(selected_group_atom, 0) == -1:     # check 
              continue;
          if selected_atom == 'C' or selected_atom == 'H':
              assignments = label.split('[')
              assignment = assignments[0]
              asns = sputil.parse_assignment(assignment)
              iOk = 0
              for asn in asns:
                  if asn == selected_group_atom:
                      iOk = 1
                      break
              if iOk == 0:
                  continue
          # if related..
          # add to the label list
          iAssigned = 0
          #tkMessageBox.showinfo('ga1','%d' % (len(assigned_peaks)))
          for peak in assigned_peaks:
              peak_pos = ''
              for i in range(self.selected_spectrum.dimension):
                  peak_pos = peak_pos + ('%7.3f,' % peak.position[i]).strip()
              peak_pos = peak_pos.rstrip(',')
              #tkMessageBox.showinfo('assignment',peak.assignment)
              groupatoms = sputil.parse_assignment(peak.assignment)
              assgn = ''
              ga1 = ''
              for ga in groupatoms:
                  if ga1 == '':
                      assgn = assgn + ga[0] + ga[1] + '-'
                  else:
                      if ga1 == ga[0]:
                          assgn = assgn + ga[1] + '-'
                      else:
                          assgn = assgn + ga[0] + ga[1] + '-'
                  ga1 = ga[0]  
                  
              assgn = assgn.rstrip('-') 
              #tkMessageBox.showinfo('ga1',peak_pos)
#              if label.find(peak_pos) <> -1 and label.find(assgn) <> -1:
              if label.find(peak_pos) <> -1:
                  iAssigned = 1
                  break
                  
          if iAssigned == 0:
              self.label_list.append(label, label)
          else:     # if it is already assign label,
              self.label_list.append(label + ';(*)', label + ';(*)')
              self.label_list.listbox.selection_includes(self.label_list.listbox.size()-1, )
        # Sorting probabilities.
        
      finally:
        in_file.close()  
  # ---------------------------------------------------------------------------
  #!
  def FastPrev(self):
    # Select 10 prior sequence
    if self.selected_index > 10:
        self.selected_index = self.selected_index - 10
    else:
        self.selected_index = 1
    self.selected_group = self.sequences[self.selected_index]
    if self.selected_index > 0:
        self.selected_group_prev = self.sequences[self.selected_index-1]
    else:
        self.selected_group_prev = None
    self.selected_group_next = self.sequences[self.selected_index+1]
    self.selected_atom = 'CA'
    self.selected_groupatom = '%s%dCA' % (self.selected_group[0], self.selected_group[1])
    # Update
    self.UpdateDialog()                      
  # ---------------------------------------------------------------------------
  #!
  def Prev(self):
    # Select previous sequence
    while self.selected_index > 0:
        self.selected_index = self.selected_index - 1
        self.selected_group = self.sequences[self.selected_index]
        if self.selected_index > 0:
            self.selected_group_prev = self.sequences[self.selected_index-1]
        else:
            self.selected_group_prev = None
        self.selected_group_next = self.sequences[self.selected_index+1]
        self.selected_atom = 'CA'
        self.selected_groupatom = '%s%dCA' % (self.selected_group[0], self.selected_group[1])
        if self.selected_group <> None:
            break
    # Update
    self.UpdateDialog()
  # ---------------------------------------------------------------------------
  #! 
  def Next(self):
    # Select next sequence
    while self.selected_index < len(self.sequences) - 1:
        self.selected_index = self.selected_index + 1
        self.selected_group = self.sequences[self.selected_index]
        self.selected_group_prev = self.sequences[self.selected_index-1]
        if self.selected_index < len(self.sequences) - 1:
            self.selected_group_next = self.sequences[self.selected_index+1]
        else:
            self.selected_group_next = None
        self.selected_atom = 'CA'
        self.selected_groupatom = '%s%dCA' % (self.selected_group[0], self.selected_group[1])
        if self.selected_group <> None:
            break
    # Update
    self.UpdateDialog()
  # ---------------------------------------------------------------------------
  #! 
  def FastNext(self):
    # Select next sequence
    if self.selected_index < len(self.sequences) - 11:
        self.selected_index = self.selected_index + 10
    else:
        self.selected_index = len(self.sequences) - 2
    self.selected_group = self.sequences[self.selected_index]
    self.selected_group_prev = self.sequences[self.selected_index-1]
    if self.selected_index < len(self.sequences) - 1:
        self.selected_group_next = self.sequences[self.selected_index+1]
    else:
        self.selected_group_next = None
    self.selected_atom = 'CA'
    self.selected_groupatom = '%s%dCA' % (self.selected_group[0], self.selected_group[1])
    # Update
    self.UpdateDialog()
  # ---------------------------------------------------------------------------
  # when update button is pressed,
  # 1. Draw Canvas
  # 2. Update spectra list
  # 3. Update label list
  #!
  def UpdateDialog(self):
    if self.selected_spectrum == None:
        return
      
    if self.selected_group == None:
        return
      
    # draw canvas
    self.ClearCanvas()
    self.DrawCanvas()
    # update spectra list
    self.UpdateSpectraList()
    # update label list
    self.UpdateLabelList()

  # ---------------------------------------------------------------------------
  #!
  def Assign(self):
    if self.selected_spectrum == None or self.selected_group == None or self.selected_atom == None:
        return
    if len(self.label_list.selected_line_numbers()) == 0:
        return

    for label in self.label_list.selected_line_data():
        if label.find('assigned') <> -1:
            continue
        [label_assign, label_prob, label_pos] = self.SplitPineLabel(label)
        
        # parse frequencies from label text
        splited = label.split('(')
        if splited < 2:                             #
            continue
        splitedsplited = splited[1].split(')')
        pszFreq = splitedsplited[0].split(',')
        freq = []
        for szFreq in pszFreq:
            freq.append(eval(szFreq))
        # set ranges depending on atom types
        ranges = []
        for atom_type in self.selected_spectrum.nuclei:
            if atom_type == '13C':
                ranges.append(0.4)
            elif atom_type == '1H':
                ranges.append(0.03)
            elif atom_type == '15N':
                ranges.append(0.4)
         
        peak = sputil.closest_peak(freq, self.selected_spectrum.peak_list(), ranges)
        if peak <> None:
            if peak.is_assigned:
                # unassign peak
                for i in range(self.selected_spectrum.dimension):
                    peak.assign(i, '', '')
            # Assign
            splited2 = label.split('[')
            assgn = sputil.parse_assignment(splited2[0])
            for i in range(self.selected_spectrum.dimension):
                peak.assign(i, assgn[i][0], assgn[i][1])
            # select floating labels
            # if already assigned, clear labels
            peak.selected = 0
            for pLabel in self.selected_spectrum.label_list():
                [pAssign, pProb, pPos] = self.SplitPineLabel(pLabel.text)
                if label_pos == pPos:
                    pLabel.selected = 1
                else:
                    pLabel.selected = 0
    self.UpdateDialog()

  # ---------------------------------------------------------------------------
  #
  def UnAssign(self): 
    if self.selected_spectrum == None or self.selected_group == None or self.selected_atom == None:
        return
    if len(self.label_list.selected_line_numbers()) == 0:
        return
    
    for label in self.label_list.selected_line_data():
        if label.find('(*)') == -1:
            continue
        
        # parse frequencies from label text
        splited = label.split('(')
        if splited < 2:                             #
            continue
        splitedsplited = splited[1].split(')')
        pszFreq = splitedsplited[0].split(',')
        freq = []
        for szFreq in pszFreq:
            freq.append(eval(szFreq))
        # set ranges depending on atom types
        ranges = []
        for atom_type in self.selected_spectrum.nuclei:
            if atom_type == '13C':
                ranges.append(0.4)
            elif atom_type == '1H':
                ranges.append(0.03)
            elif atom_type == '15N':
                ranges.append(0.4)
         
        peak = sputil.closest_peak(freq, self.selected_spectrum.peak_list(), ranges)
        if peak <> None:
            if peak.is_assigned:
                # unassign peak
                for i in range(self.selected_spectrum.dimension):
                    peak.assign(i, '', '')
    self.UpdateDialog()
                    
  # ---------------------------------------------------------------------------
  # Canvas Initialization
  #!
  def ClearCanvas(self):
    # 1. Clear canvas
    self.canvas.delete('all')
    # 2. Divide into grids
    self.DrawGrid()    
  # ---------------------------------------------------------------------------
  # Draw Grids on Canvas; (200+200+200)x300
  #!
  def DrawGrid(self):
    # -6 - 4: 20 pixels   10
    # -5 - 15: 20 pixels  20
    #-----------------------
    
    # Draw Grid
    for x in range(1, 600, 20):
        grid_line_x = self.canvas.create_line(x,1,x,400, fill="cyan",smooth="true")
        
    for y in range(20,400, 20):
        grid_line_y = self.canvas.create_line(1,y,600,y, fill="cyan",smooth="true")
        
    # Draw Title
    left_title_line = self.canvas.create_line(1,1,1,400)
    right_title_line = self.canvas.create_line(600,1,600,400)
    top_title_line = self.canvas.create_line(1,1,600,1)
    bottom_title_line = self.canvas.create_line(1,400,600,400)

    if self.selected_group_prev <> None:
        prev_title_text = '%s%d' % (self.selected_group_prev[0], self.selected_group_prev[1])
    else:
        prev_title_text = 'X'
    self.prev_title_text = self.canvas.create_text(90, 30, anchor="center", text = prev_title_text)
    
    if self.selected_group <> None:
        cur_title_text = '%s%d' % (self.selected_group[0], self.selected_group[1])
    else:    
        cur_title_text = 'X'
    self.cur_title_text = self.canvas.create_text(290, 30, anchor="center", text = cur_title_text)
    if self.selected_group_next <> None:
        next_title_text = '%s%d' % (self.selected_group_next[0], self.selected_group_next[1])
    else:
        next_title_text = 'X'
        
    self.next_title_text = self.canvas.create_text(490, 30, anchor="center", text = next_title_text)
        
  # ---------------------------------------------------------------------------
  # Draw Canvas
  # 1. Draw Residue
  # 2. Draw Selected Residue
  # 3. Draw Texts (average & standard deviation)
  def DrawCanvas(self):
    # 1. Draw Residue
    self.DrawResidues()
    # 2. Draw Selected Residue
    self.DrawSelectedAtom()
    # 3. Draw Texts (average & standard deviation)
    self.DrawTexts()
  
  # ---------------------------------------------------------------------------
  #
  def DrawTexts(self):
    self.DrawText(self.selected_group_prev, -1)
    self.DrawText(self.selected_group, 0)  
    self.DrawText(self.selected_group_next, 1)
  # ---------------------------------------------------------------------------
  #!
  def DrawText(self, selected_group, iLocation):
      if selected_group == None:
          return      
      if not pinelayout.pine_layout.has_key(selected_group[0]):
          return
      layout = pinelayout.pine_layout[selected_group[0]]
      
      iCount = 1
      szKey = 'Atom%d' % (iCount)
      while layout.has_key(szKey):
          [szAtom, (x, y)] = layout[szKey]
          self.DrawFreq(x, y, selected_group, szAtom, iLocation)
          iCount = iCount+1
          szKey = 'Atom%d' % (iCount)
  # ---------------------------------------------------------------------------
  #
  def DrawFreq(self, x, y, selected_group, szAtom, iLocation):
      [base_x, base_y] = self.Cell2Coord(x, y, iLocation)
      # set frequency and deviation
      [freq, devi] = self.GetFrequency(selected_group, szAtom)
      if freq == -1 and devi == -1:
          return
      szFreq = ('%7.2f' % freq).strip() 
      txt = self.canvas.create_text(base_x+18, base_y+18, text = szFreq, anchor='nw')
      szFreq = '(' + ('%7.2f' % devi).strip() + ')'
      txt2 = self.canvas.create_text(base_x+18, base_y+28, text = szFreq, anchor='nw')
  # ---------------------------------------------------------------------------
  #
  def GetFrequency(self, selected_group, szAtom):
      for condition in self.session.project.condition_list():
          group_name = '%s%d' % (selected_group[0], selected_group[1])
          resonance = condition.find_resonance(group_name, szAtom)
          if resonance <> None:
              if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                  return -1, -1
              return resonance.frequency, resonance.deviation
          else:
              # processing pseudo atoms
              if pinelayout.pseudo_layout.has_key(selected_group[0]) and szAtom[:1] == 'H':
                  layout = pinelayout.pseudo_layout[selected_group[0]];   
                  szAtom2 = ('Q%s' % szAtom[1:-1])
                  resonance = condition.find_resonance(group_name, szAtom2)
                  if resonance <> None:
                      if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                          return -1, -1                  
                      return resonance.frequency, resonance.deviation
              # processing meta atoms
              if not pinelayout.meta_layout.has_key(selected_group[0]):
                  continue
              layout = pinelayout.meta_layout[selected_group[0]];
              szAtom2 = szAtom  #HB3
              while len(szAtom2) > 2:
                  szAtom_1 = szAtom2[:-1] # HB
                  if layout.has_key(szAtom_1):
                      atom_list = layout[szAtom_1]
                      if szAtom in atom_list:
                          resonance = condition.find_resonance(group_name, szAtom_1)  
                          if resonance <> None:
                              if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                                  return -1, -1                                            
                              return resonance.frequency, resonance.deviation
                          else:
                              for szPseudoAtom in atom_list:
                                  resonance = condition.find_resonance(group_name, szPseudoAtom)
                                  if resonance <> None:
                                      if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                                          return -1, -1                                                    
                                      return resonance.frequency, resonance.deviation
                  szAtom2 = szAtom_1
                  if len(szAtom2) < 2:
                      break
      return -1, -1
    
  # ---------------------------------------------------------------------------
  #!
  def DrawSelectedAtom(self):
    if self.selected_group == None:
        return
    if self.selected_atom == None:
        return
    #tkMessageBox.showinfo('DrawSelectedAtom', self.selected_atom)
    # get layout
    layout = pinelayout.pine_layout[self.selected_group[0]]
                
    iCount = 1
    szKey = 'Atom%d' % (iCount)
    while layout.has_key(szKey):
        [szAtom, (x, y)] = layout[szKey]
        if szAtom <> self.selected_atom:
            iCount = iCount+1
            szKey = 'Atom%d' % (iCount)
            continue
        [base_x, base_y] = self.Cell2Coord(x, y, 0)
        atom_color = 'magenta'
        cl = self.canvas.create_oval(base_x, base_y, base_x + 20, base_y + 20, fill=atom_color)
        txt = self.canvas.create_text(base_x+10, base_y+10, text = szAtom)
        iCount = iCount+1
        szKey = 'Atom%d' % (iCount)
        #break        
  # ---------------------------------------------------------------------------
  #!
  def DrawResidues(self):
    # X(i-1), X(i), X(i+1)
    # prev
    if self.selected_group_prev == None:
        if self.selected_index <> 0:
            self.DrawResidue('X', -1)
    else:
        self.DrawResidue(self.selected_group_prev[0], -1)
    # cur
    if self.selected_group == None:
        self.DrawResidue('X', 0)
    else:
        self.DrawResidue(self.selected_group[0], 0)  
    # next
    if self.selected_group_next == None:
        if self.selected_index <> len(self.sequences)-1:
            self.DrawResidue('X', 1)
    else:
        self.DrawResidue(self.selected_group_next[0], 1)
  # ---------------------------------------------------------------------------    
  # draw amino acid diagram on canvas
  # iLocation: -1, 0, 1
  def DrawResidue(self, AminoAcidType, iLocation):
      if not pinelayout.pine_layout.has_key(AminoAcidType):
          return
      
      layout = pinelayout.pine_layout[AminoAcidType]
      iCount = 1
      szKey = 'Bond%d' % (iCount)
      while layout.has_key(szKey):
          [iType, (x, y)] = layout[szKey]
          self.DrawBond(x, y, iType, iLocation)
          iCount = iCount+1
          szKey = 'Bond%d' % (iCount)
          
      iCount = 1
      szKey = 'Atom%d' % (iCount)
      while layout.has_key(szKey):
          [szAtom, (x, y)] = layout[szKey]
          self.DrawAtom(x, y, szAtom, iLocation)
          iCount = iCount+1
          szKey = 'Atom%d' % (iCount)
  # ---------------------------------------------------------------------------
  #!
  def DrawBond(self, x, y, iType, iLocation):
      [base_x, base_y] = self.Cell2Coord(x, y, iLocation)
      iBondType = 1         # single bond
      if iType > 100 and iType < 200:
          iBondType = 2     # double bond
          iType = iType - 100
      elif iType > 200 and iType < 300:
          iBondType = 3     # triple bond
          iType = iType - 200
      if iType == 1:
          x1 = 10
          y1 = -5
          x2 = 10
          y2 = 25
      elif iType == 2:
          x1 = -5
          y1 = 10
          x2 = 25
          y2 = 10
      elif iType == 3:
          x1 = -5
          y1 = -5
          x2 = 25
          y2 = 25
      elif iType == 4:
          x1 = -5
          y1 = 25
          x2 = 25
          y2 = -5
      elif iType == 5:
          x1 = -5
          y1 = -2
          x2 = 25
          y2 = 12
      elif iType == 6:
          x1 = -5
          y1 = 8
          x2 = 25
          y2 = 22                          
      elif iType == 7:
          x1 = -2
          y1 = -5
          x2 = 12
          y2 = 25
      elif iType == 8:
          x1 = 8
          y1 = -5
          x2 = 22
          y2 = 25
      elif iType == 9:
          x1 = -5
          y1 = 12
          x2 = 25
          y2 = -2
      elif iType == 10:
          x1 = -5
          y1 = 22
          x2 = 25
          y2 = 8
      elif iType == 11:
          x1 = -2
          y1 = 25
          x2 = 12
          y2 = -5
      elif iType == 12:        
          x1 = 8
          y1 = 25
          x2 = 22
          y2 = -5
      # Draw Line
      ln = self.canvas.create_line(base_x+x1,base_y+y1,base_x+x2,base_y+y2)
      # Double bond or triple bond
      if iBondType > 1:
          ln2 = self.canvas.create_line(base_x+x1+2,base_y+y1+2,base_x+x2+2,base_y+y2+2)
      if iBondType > 2:
          ln3 = self.canvas.create_line(base_x+x1-2,base_y+y1-2,base_x+x2-2,base_y+y2-2)
  # ---------------------------------------------------------------------------
  def DrawAtom(self, x, y, szAtom, iLocation):
      [base_x, base_y] = self.Cell2Coord(x, y, iLocation)
      
      # check if this atom is already assigned
      if iLocation == 0:
          selected_group = self.selected_group
      elif iLocation == -1:
          selected_group = self.selected_group_prev
      elif iLocation == 1:
          selected_group = self.selected_group_next
      if selected_group == None:
          return
      
      szType = szAtom[0:1]
      if szType == 'C':
          atom_color = 'red'
      elif (szType == 'H') or (szType == 'Q'):
          atom_color = 'yellow'
      elif szType == 'N':
          atom_color = 'blue'
      else:
          atom_color = 'gray'
      
      iWidth = 1
      
      #group_name = '%s%d' % (selected_group[0], selected_group[1])
      [freq, devi] = self.GetFrequency(selected_group, szAtom)
      if not (freq == -1 and devi == -1):
          iWidth = 3
            
      #for condition in self.session.project.condition_list():
      #    group_name = '%s%d' % (selected_group[0], selected_group[1])
      #    resonance = condition.find_resonance(group_name, szAtom)
      #    if resonance <> None:
      #        iWidth = 3
      #        break
        
      # check whether the atom is available or not
      if pinelayout.pine_disabled_layout.has_key(selected_group[0]):
          disabled_layout = pinelayout.pine_disabled_layout[selected_group[0]]
          if szAtom in disabled_layout:
              atom_color = 'gray'
                
      cl = self.canvas.create_oval(base_x, base_y, base_x + 20, base_y + 20, fill=atom_color, width = iWidth)
      txt = self.canvas.create_text(base_x+10, base_y+10, text = szAtom)
  # ---------------------------------------------------------------------------
  # Convert Cell coord to screen coord
  # -6 ~ 4, -5 ~ 15
  #!    
  def Cell2Coord(self, x, y, iLocation):
      x1 = (x + 5) * 20
      y1 = (y + 6) * 20
      x1 = x1 + 201 + iLocation * 200
      newcoord = [x1, y1]
      return newcoord
  # ---------------------------------------------------------------------------
  # returns assignment, probability, position
  def SplitPineLabel(self, label_text):
      splited = label_text.split(':')
      if len(splited) < 2:
          return '','',''
      labelside = splited[0].split('[')
      probside = labelside[1].split(']')
      
      szAssignment = labelside[0]
      szProb = probside[0]
      
      posside = splited[1].split('(')
      posside2 = posside[1].split(')')
      szPosition = posside2[0]
      
      return szAssignment, szProb, szPosition
# ----------------------------------------------------------------------------
  def PlayAll(self):
    self.selected_index = 0
    self.selected_group = self.sequences[0]
    self.selected_group_prev = None
    self.selected_group_next = self.sequences[1]
    self.selected_atom = 'CA'
    self.selected_groupatom = '%s%dCA' % (self.selected_group[0], self.selected_group[1])
    self.UpdateDialog()
    self.canvas.update()
    
    iIndex = -1
    
    while (iIndex <> self.selected_index):
        self.PlayResidue()
        iIndex = self.selected_index
        self.Next()
        self.canvas.update()

      
  def PlayResidue(self):
    if self.selected_group == None:
        return
    if not pinelayout.pine_layout.has_key(self.selected_group[0]):
        return        

    layout = pinelayout.pine_layout[self.selected_group[0]]

    iCount = 1
    szKey = 'Atom%d' % (iCount)
    freq = []
   
    while layout.has_key(szKey):
        [szAtom, (x, y)] = layout[szKey]
        [dFrq, dDev] = self.GetFrequency(self.selected_group,szAtom)
        dFrq2 = pinesound.ppm2sound(dFrq, szAtom)
        if dFrq2 < 0:
            iCount = iCount+1
            szKey = 'Atom%d' % (iCount)
            continue
            
        freq.append(dFrq2);
        iCount = iCount+1
        szKey = 'Atom%d' % (iCount)

    pinesound.play_for(pinesound.waves(*freq), 1000)
    
  def PlayAtom(self):
    if (self.selected_group == None) and (self.selected_atom == None):
        return
    [dFrq, dDev] = self.GetFrequency(self.selected_group, self.selected_atom)
    if dFrq < 0:
        return
    dFrq2 = pinesound.ppm2sound(dFrq, self.selected_atom)
    pinesound.play_for(pinesound.waves(dFrq2), 1000)

# ----------------------------------------------------------------------------
# Modified scrolling_list from tkutil.py
# Make a list box with a label heading and vertical scrollbar.
# The list keeps track of data associated with each line.
#
class modified_listbox:

  def __init__(self, parent, heading, width, height, selectmode):
    self.line_data = []
    
    f = Tkinter.Frame(parent)
    f.rowconfigure(1, weight = 1)
    f.columnconfigure(0, weight = 1)
    self.frame = f

    h = Tkinter.Label(f, text = heading, font = 'Courier 12',
              anchor = 'w', justify = 'left')
    h.grid(row = 0, column = 0, sticky = 'w')
    self.heading = h

    list = Tkinter.Listbox(f, width = width, height = height, font = 'Courier 12', selectmode=selectmode, exportselection=False)
    list.grid(row = 1, column = 0, sticky = 'news')
    self.listbox = list

    yscroll = Tkinter.Scrollbar(f, command = list.yview)
    yscroll.grid(row = 1, column = 1, sticky = 'ns')
    list['yscrollcommand'] = yscroll.set
      
  # ---------------------------------------------------------------------------
  #
  def clear(self):
    self.listbox.delete('0', 'end')
    self.line_data = []

  # ---------------------------------------------------------------------------
  #
  def append(self, line, line_data = None):
    self.listbox.insert('end', line)
    self.line_data.append(line_data)
      
  # ---------------------------------------------------------------------------
  #
  def selected_line_data(self):
    data_list = []
    for line_number in self.selected_line_numbers():
      if line_number >= 0 and line_number < len(self.line_data):
        data_list.append(self.line_data[line_number])
    return data_list

  # --------------------------------------------------------------------------
  #
  def selected_line_numbers(self):
    return map(string.atoi, self.listbox.curselection())

  # --------------------------------------------------------------------------
  #
  def event_line_data(self, event):
    line_number = self.listbox.nearest(event.y)
    if line_number >= 0 and line_number < len(self.line_data):
      return self.line_data[line_number]
    return None

  # --------------------------------------------------------------------------
  #
  def delete_selected_cb(self, event):
    slines = self.selected_line_numbers()
    slines.sort()
    slines.reverse()
    for line_number in slines:
      del self.line_data[line_number]
      self.listbox.delete(line_number)
  # --------------------------------------------------------------------------
  #
  def event_line_data(self, event):
    line_number = self.listbox.nearest(event.y)
    if line_number >= 0 and line_number < len(self.line_data):
      return self.line_data[line_number]
    return None
  # --------------------------------------------------------------------------
  #
  def set_focus_cb(self, event):
    self.listbox.focus_set()
    
def show_pine_graph(session): 
  sputil.the_dialog(pine_graph, session).show_window(1)

