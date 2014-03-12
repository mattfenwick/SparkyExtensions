# -----------------------------------------------------------------------------
# Dialog for assignment of PINE outputs.
# -----------------------------------------------------------------------------
#
# Developed by Woonghee Lee
# e-mail: whlee@nmrfam.wisc.edu
# National Magnetic Resonance Facilities at Madison
# Department of Bichemistry, University of Wisconsin at Madison
#
# Last updated: Apr 14, 2010
# 
# Usage:
#
# I recommend to use this dialog with peak list(lt) dialog.
# First, select spectrum to assign by clicking the spectrum window.
# Second, press "lt" to show up peak list dialog.
# Third, select wanted peak which you want to assign from the dialog.
# Fourth, press "pr" to show up this dialog.
# Fifth, select possible assignment and press "Assign" button or just click 
#     "Best Prop." button if you want to choose an assignment which is the 
#     best probability.
# Sixth, press "Floating Labels" to select floating labels, select the spectrum
#     window, and press delete key to remove them. 
# Seventh, do third step to sixth step repeatedly. Substitute fourth step with 
#     pressing "Update" button of this dialog.
# 
# -----------------------------------------------------------------------------
import math
import string
import types
import Tkinter
import atoms
import pyutil
import sparky
import sputil
import tkutil
import tkMessageBox
import pinegraph

# -----------------------------------------------------------------------------
#
class pine_dialog(tkutil.Dialog, tkutil.Stoppable):
  # ---------------------------------------------------------------------------
  #
  def __init__(self, session):
    # Initialize variables
    self.peak = None
    self.graph_dialog = None      
    self.spectrum_text = None
    self.peak_text = None
    self.label_box = None
    self.label_list = None
    self.br = None
    self.br2 = None
    self.progress_label = None
    
    tkutil.Dialog.__init__(self, session.tk, 'Pine Assigner')
    #self.top.grab_set()
    #self.top.focus_set()
    keypress_cb = pyutil.precompose(sputil.command_keypress_cb, session)
    self.top.bind('<KeyPress>', keypress_cb)    
    
    self.session = session
    self.UpdateDialog()
  # ---------------------------------------------------------------------------
  #
  def keypress_cb(self, event):
      self.session.command_characters(event.char)
  # ---------------------------------------------------------------------------
  # Generate objects inside this dialog.
  # 
  def UpdateDialog(self):
    # Clear objects
    if self.spectrum_text <> None:
        self.spectrum_text.frame.destroy()
    if self.peak_text <> None:
        self.peak_text.frame.destroy()
    if self.label_box <> None:
        self.label_box.destroy()
    if self.br <> None:
        self.br.frame.destroy()
    if self.br2 <> None:
        self.br2.frame.destroy()        
    if self.progress_label <> None:
        self.progress_label.destroy()    
    
    # Set up selected spectrum
    self.spectrum = self.session.selected_spectrum()

    # There should be selected spectrum
    if self.spectrum == None:
        self.close_cb()
        
    # There should be one selected peak    
    peaks = self.spectrum.selected_peaks()
    
    if len(peaks) > 0:
        self.peak = peaks[0]
    else:
        self.close_cb()

    # Create label object for showing spectrum name
    t = tkutil.entry_row(self.top, 'Selected Spectrum: ' + self.spectrum.name)
    t.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_text = t

    # Dunno why 'len(peaks) > 0' is not working 
    if self.peak <> None:
        if self.spectrum.dimension == 2:
            u = tkutil.entry_row(self.top, 'Selected Peak: %7.3f,%7.3f' % (self.peak.position[0],self.peak.position[1]) )
        else:
            u = tkutil.entry_row(self.top, 'Selected Peak: %7.3f,%7.3f,%7.3f' % (self.peak.position[0],self.peak.position[1],self.peak.position[2]) )
        u.frame.pack(side = 'top', anchor = 'w')
        self.peak_text = u
        
        # Create listbox object for showing labels
        lbLabel = self.label_list_box(self.top)                         # List box
        lbLabel.pack(side = 'top', fill = 'both', expand = 1)
        self.label_box = lbLabel
        self.LabelBox()                           # Set up label list box


    # Create Buttons
    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')   
    self.progress_label = progress_label
   
    self.br = tkutil.button_row(self.top,
                           ('Update', self.UpdateDialog),         # Func
                           ('Assign', self.Assign),         # Func
                           ('Best Prob.', self.AssignTheBest),
                           ('UnAssign', self.UnAssign),     # Func
                          )
    self.br2 = tkutil.button_row(self.top,
                           ('Floating Labels', self.FloatingLabel),
                           ('Graph...', self.Graph),        # Func
                           ('Stop', self.stop_cb),
                           ('Close', self.close_cb),        
                           #('Help', sputil.Help(session, 'PineAssign')),
                          )
    self.br.frame.pack(side = 'top', anchor = 'w')
    self.br2.frame.pack(side = 'top', anchor = 'w')
     
    tkutil.Stoppable.__init__(self, progress_label, self.br2.buttons[2])
    #self.top.grab_set()
    #self.top.focus_set() 
  # ---------------------------------------------------------------------------
  #
  def Close(self):        # M1N-M1CB-M1H[1.0]
      #self.close_sb
      self.close_cb()

  # ---------------------------------------------------------------------------
  #
  def label_list_box(self, parent):

    pl = tkutil.scrolling_list(parent, 'Choose possible resonance assignments by PINE', 8)
    pl.listbox.bind('<Double-ButtonRelease-1>', self.Assign_cb)          # Func
    pl.listbox.bind('<ButtonRelease-3>', self.Assign_cb)          # Func
    self.label_list = pl
    
    return pl.frame
 
  # ---------------------------------------------------------------------------
  # Fill label box
  def LabelBox(self):
    
    self.label_list.clear()

    # append labels which are located on the selected peak
    iIndex = -1
    if self.spectrum == None:                   # if there is no selected spectrum, exit this function.
        return
    if self.peak == None:
        return
    szPos = '('
    for pos in self.peak.position:
        szPos = szPos + ('%7.3f,' % pos).strip() 
    szPos = szPos.rstrip(',')
    szPos = szPos + ')'
    #----------------------------------------------------------------------------------------------
    f = open(self.spectrum.save_path + '_pl', 'r')
    try:
        for label in f.readlines():
            label = label.strip()
            if label.find(szPos) <> -1:
                #tkMessageBox.showinfo('szPos',szPos)
                # find label object
                iFound = 0
                for pLabel in self.spectrum.label_list():
                    if pLabel.text == label:
                        iFound = 1
                        break
                if iFound == 1:
                    self.label_list.append(label, pLabel)
                else:
                    self.label_list.append(label, None) 
                if self.peak.is_assigned == 1:
                    asns = sputil.parse_assignment(self.peak.assignment)
                    filled_assignment = ''
                    for asn in asns:
                        filled_assignment = filled_assignment + asn[0] + asn[1] + '-'
                    filled_assignment = filled_assignment.rstrip('-')
#                        tkMessageBox.showinfo('filled',filled_assignment)
                    if label.find(filled_assignment) <> -1:
                        iIndex = self.label_list.listbox.size()-1
#                    if self.peak.is_assigned == 1 and label.find(self.peak.assignment) <> -1: 
#                        iIndex = self.label_list.listbox.size()-1
                
    finally:
        f.close()
        
    if iIndex <> -1:
        self.label_list.listbox.selection_set(iIndex, )
        self.label_list.listbox.see(iIndex)
       
  def FloatingLabel(self):
    # if already assigned, clear labels
    self.peak.selected = 0
    
    for pLabel in self.spectrum.label_list():
        pLabel.selected = 0
        for idx in range(self.label_list.listbox.size()):
            label = self.label_list.listbox.get(idx)
            if pLabel.text == label:
                pLabel.selected = 1
                break

  # ---------------------------------------------------------------------------
  # "Best Prob."
  def AssignTheBest(self):
    if len(self.label_list.line_data) == 0:
        return
    self.spectrum = self.session.selected_spectrum()
    if self.spectrum == None: 
        return
    peaks = self.spectrum.selected_peaks()
    if len(peaks) > 0:
        if self.peak <> peaks[0]:
            self.UpdateDialog()
    else:
        return
        
    # find best line data
    dTemp = 0.0
    dMax = 0.0
    max_Label = None
    for pLabel in self.label_list.line_data:
        line_data = pLabel.text
        szSplited = line_data.split('[')
        szSplited2 = szSplited[1].split(']')
        dTemp = eval(szSplited2[0])
        if dTemp > dMax:
            dMax = dTemp
            max_Label = pLabel
    if max_Label <> None:
        if self.peak.is_assigned:
            self.UnAssign()
        pLabel2 = max_Label.text.split('[')
        pList = pLabel2[0].split('-')
        
        for i in range(len(pList)):
            tAssign = sputil.split_group_atom(pList[i])
            self.peak.assign(i, tAssign[0], tAssign[1])
    # select !!
    self.LabelBox()
    # select floating labels
    self.FloatingLabel()

  def Assign_cb(self, event):
      self.Assign()
                  
  def Assign(self):
    # First, check selected peak and label
    # Second, assign selected peak by selected label
    # Selected peak and label should be one
    if self.label_list == None:
        return
    
    if len(self.label_list.selected_line_numbers()) == 0:
        return
    
    label = self.label_list.listbox.get(self.label_list.selected_line_numbers()[0])   

    # UnAssign
    if self.peak.is_assigned:
        self.UnAssign()
    
    # Assign - # M1CA-M1N-M1H[1.0]:(xxx.xxx,x.xxx,x.xxx)
    pLabel = label.split('[')   # M1CA-M1N-M1H   
    pList = pLabel[0].split('-')   # (M1CA, M1N, M1H)
   
    for i in range(len(pList)):
        tAssign = sputil.split_group_atom(pList[i])        # (M1, CA)
        self.peak.assign(i, tAssign[0], tAssign[1])
    
    #self.peak.selected = 1
    #self.Update()
    # select floating labels
    self.FloatingLabel()
    self.LabelBox()
    
  def UnAssign(self):
    for i in range(self.spectrum.dimension):
        self.peak.assign(i, '', '')
    self.label_list.listbox.selection_clear(0, 'end')
    self.FloatingLabel()
 
  # -----------------------------------------------------------------------------
  # Shows visualized diagram of assignments
  def Graph(self): 
      self.peak.selected = 1
      sputil.the_dialog(pinegraph.pine_graph, self.session).show_window(1)
      return    
# -----------------------------------------------------------------------------
#
def show_pine_assigner(session):
  sputil.the_dialog(pine_dialog,session).show_window(1)
  
  
# -----------------------------------------------------------------------------
# Choose the best probability calculated by PINE for all peaks. 
# -----------------------------------------------------------------------------
#
# Developed by Woonghee Lee
# e-mail: whlee@nmrfam.wisc.edu
# National Magnetic Resonance Facilities at Madison
# Department of Bichemistry, University of Wisconsin at Madison
#
# Last updated: July 9, 2008
# 
#
# Usage:
# 
# First, select spectrum which you want to assign all by best probabilities.
# Second, press "ab", then it will take some time to assign all.
# Third, after processing is done, all floating labels are selected. Press delete key to remove them.
# Finally you can see all assigned peaks by the best results of PINE.
#
# -----------------------------------------------------------------------------
def best_assign(session):
    
    setup_dialog = sputil.the_dialog(base_prob, session)
    setup_dialog.show_window(1)

        
# -----------------------------------------------------------------------------
# Select spectra, expected peaks, and tolerances for assigner_dialog.
#
class base_prob(tkutil.Dialog, tkutil.Not_Stoppable):

  def __init__(self, session):

    self.session = session

    tkutil.Dialog.__init__(self, session.tk, 'Assign the best by PINE')
    
    label = Tkinter.Label(self.top, text = 'Base Probability(0.0~1.0):')
    label.pack(side = 'left')
    v = Tkinter.StringVar(self.top)
    v.set('0.9')
    self.variable = v
    entry = Tkinter.Entry(self.top, textvariable = v, width = 5)
    entry.pack(side = 'left')
        
    br = tkutil.button_row(self.top,
                           ('Assign', self.assign_cb),
                           ('Cancel', self.close_cb),
               )
    br.frame.pack(side = 'top', anchor = 'w')
        
  # ---------------------------------------------------------------------------
  #
  def assign_cb(self):
    spectrum = self.session.selected_spectrum()
    
    if spectrum == None:
        return
    
    szPrb = self.variable.get()
    dPrb = eval(szPrb)
    
    if len(spectrum.selected_peaks()) == 0:
        peaks = spectrum.peak_list()
    else:
        peaks = spectrum.selected_peaks()
    
    for pLabel in spectrum.label_list():
        pLabel.selected = 0
        
    pLabelList = []
    pSameList = []
    pFloatList = []
    pProbList = []  
     
    iTotal = len(peaks)
    iAssigned = 0
    for pPeak in peaks:
        if pPeak.is_assigned:
            continue;
        pPeak.selected = 0
        
        #pPosList = []                               # Contains position
        #pProbList = []                              # Contains probabilities
        del pLabelList[:]
        del pSameList[:]
        del pFloatList[:]
        del pProbList[:]
        for pLabel in spectrum.label_list():
            bSame = 0
            #pLabel.selected = 0
            splited = pLabel.text.split(':')        # M1CA-M1N-M1H[1.0]:(53.2120,124.321,8.23400)
            if len(splited) == 1:                   # if it doesn't have position property, then continue.
                continue
            szLabel = (splited[0].split('['))[0]
            szProb = (((splited[0].split('['))[1]).split(']'))[0]
            
            splited2 = splited[1].split('(')        # (53.2120,124.321,8.23400)
            splitedsplited = splited2[1].split(')') 
            pos = splitedsplited[0].split(',')      # 53.2120,124.321,8.23400
            
            if pos[0] == '?':
                continue
            
            bSame = 1

            for i in range(len(pos)):
                if pPeak.position[i] != eval(pos[i]):
                    bSame = 0
                                
            if bSame == 1:
                if (eval(szProb) < dPrb):
                    bSame = 0
                pFloatList.append(pLabel)
                pSameList.append(bSame)
                pLabelList.append(szLabel)
                pProbList.append(eval(szProb))
            #if bSame == 1:                          # same position...
            #    pPosList.append(pos)
            #    pProbList.append(eval(szProb))
            #    pLabelList.append(szLabel)      # M1CA-M1N-M1H[1.0]  (M1CA,M1N,M1H)
            #    break
                
        # The best is the first
        if not 1 in pSameList:
            continue
        
        # Get maximum probability
        max = 0.0
        idx = -1
        for i in range(len(pProbList)):
            if max < pProbList[i]:
                max = pProbList[i]
                idx = i
        line_data = pLabelList[idx]
        pList = line_data.split('-')   # (M1CA, M1N, M1H)
        #pList = szLabel.split('-')   # (M1CA, M1N, M1H)
        for i in range(len(pList)):
            tAssign = sputil.split_group_atom(pList[i])        # (M1, CA)
            pPeak.assign(i, tAssign[0], tAssign[1])
            
        for pLabel in pFloatList:
            pLabel.selected = 1
        iAssigned = iAssigned + 1
        
    szAssigned = '%d of %d peaks assigned.' % (iAssigned, iTotal)
    tkMessageBox.showinfo('Assign the Best by Pine', szAssigned)
    self.close_cb()  
    
# -----------------------------------------------------------------------------
# Export to PINE for better accuracy. 
# -----------------------------------------------------------------------------
#
# Developed by Woonghee Lee
# e-mail: whlee@nmrfam.wisc.edu
# National Magnetic Resonance Facility at Madison
# Department of Bichemistry, University of Wisconsin at Madison
#
# Last updated: Oct 10, 2008
# 
#
# Usage:
# 
#    1) Type "eb" and type file name to save.
#    2) Open PINE web page with your web browser and select the file by pressing "Browse" button of "Pre-assignment".
#    3) Fill other blanks.
#    4) Press "Submit" button.
# -----------------------------------------------------------------------------
def a2aaa(a):
    lAAA = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL"]
    lA = ["A", "R", "N", "D", "C", "Q", "E", "G", "H", "I", "L", "K", "M", "F", "P", "S", "T", "W", "Y", "V"]
    
    index = lA.index(a)
    return lAAA[index]

def select_all_float_labels(session):
	spectrum = session.selected_spectrum()
	if spectrum == None:
		return
	for pLabel in spectrum.label_list():
		if pLabel.peak <> None or pLabel.text == '?-?' or pLabel.text == '?-?-?':
			pLabel.selected = 0
		else:
			pLabel.selected = 1



def export_pine(session):
    path = tkutil.save_file(session.tk, "Save to PINE input file", "save to pine input")
    if path:
      f = open(path, 'w')
      # Peak list files
      f.write('number of spectra: %d\n' % (len(session.project.spectrum_list())) )
      for spectrum in session.project.spectrum_list():
          szFile = '[start of %s]\n' % spectrum.name
          f.write(szFile)
          szHead = '?'
          for i in range(spectrum.dimension-1):
              szHead = szHead + '-?'
            
          for peak in spectrum.peak_list():
              szWrite = '%10s' % szHead
              for i in range(spectrum.dimension):
                  szWrite = szWrite + '%9.3f' % (peak.frequency[i])
              szWrite = szWrite + '\n'
              f.write(szWrite)
          szFile = '[end of %s]\n' % spectrum.name    
          f.write(szFile)
      
      # Pre-assignment file
      f.write('[Pre-assignment file]\n')
      iLine = 1  
      for condition in session.project.condition_list():
          for resonance in condition.resonance_list():
              if resonance.deviation > 1:
                  continue
              aaa = a2aaa(resonance.group.symbol)
              szWrite = '%5d%5d%5s%5s%6s%9.3f%7.3f%3d\n' % (iLine, resonance.group.number, aaa, resonance.atom.name, resonance.atom.name[0:1], resonance.frequency,1.000, 0)
              iLine = iLine+1
              f.write(szWrite)
      f.write('[end of pre-assignment file]\n')
      f.close()
      
