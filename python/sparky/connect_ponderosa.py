
# -----------------------------------------------------------------------------
# Dialog for Ponderosa Analyzer connect.
# -----------------------------------------------------------------------------
#
# Developed by Woonghee Lee
# e-mail: whlee@nmrfam.wisc.edu
# National Magnetic Resonance Facilities at Madison
# Department of Bichemistry, University of Wisconsin at Madison
#
# Last updated: Mar 15, 2014
# 
# Usage:
#
# 
# -----------------------------------------------------------------------------
#
import string
import re
import Tkinter

import pyutil
import sparky
import sputil
import tkutil
import tkMessageBox
import os
import os.path


# -----------------------------------------------------------------------------
#
class connect_ponderosa_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):
    tkutil.Dialog.__init__(self, session.tk, 'Connect Ponderosa Analyzer')

    cnt = tkutil.file_field(self.top, 'Connect file (sparky.cnt): ', 'Connect file')
    cnt.frame.pack(side = 'top', anchor = 'w')
    self.cnt_path = cnt
    szCnt = os.getcwd() +  os.sep + "sparky.cnt"
    if os.path.isfile(szCnt):
      self.cnt_path.set(szCnt)

    spec1 = sputil.spectrum_menu(session, self.top, '15N-NOESY: ')
    spec1.frame.pack(side = 'top', anchor = 'w')
    self.nnoe = spec1

    spec2 = sputil.spectrum_menu(session, self.top, '13C-NOESY(ali-): ')
    spec2.frame.pack(side = 'top', anchor = 'w')
    self.cnoe = spec2

    spec3 = sputil.spectrum_menu(session, self.top, '13C-NOESY(aro-): ')
    spec3.frame.pack(side = 'top', anchor = 'w')
    self.aronoe = spec3

    self.n15_ppms = []        # w1, w2, w3 chemical shifts
    self.c15_ppms = []        # w1, w2, w3 chemical shifts

    self.br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
			   ('Move(15N-)', self.move_n_cb),
			   ('Move(13C-)', self.move_c_cb),
			   ('Close', self.close_cb),
			   )
    self.br.frame.pack(side = 'top', anchor = 'w')

    self.label_frame = Tkinter.Frame(self.top, width = 500, height = 100)
    self.label_frame.pack(side='top', anchor = 'nw')

    ll = modified_listbox(self.label_frame, 'Label List', 49, 8, "single")
    ll.listbox.bind('<Double-ButtonRelease-1>', self.move_to_selected_cb)
    ll.listbox.bind('<ButtonRelease-3>', self.move_to_selected_cb)
    self.label_list = ll
    self.label_list.frame.grid(sticky='news')
 

# ----------------------------------------------------------------------------
  def update_cb(self):
    # check if user set sparky.cnt file
    # if not, show message
    if self.cnt_path.get() == '' or os.path.isfile(self.cnt_path.get()) == False:
      tkMessageBox.showerror("Connection Error", "Please set valid sparky.cnt.")
      return

    # read sparky.cnt and validate the format
    self.label_list.clear()
    f = open(self.cnt_path.get(), 'r')

    self.n15_ppms = []        # w1, w2, w3 chemical shifts
    self.c13_ppms = []        # w1, w2, w3 chemical shifts    

    cnt_read = f.readlines()
    f.close()
    # if not, show message
    if len(cnt_read) <> 12:
      tkMessageBox.showerror("Connection Error", "Please set valid sparky.cnt.")
      return

    for i in range(len(cnt_read)):
      if cnt_read[i] == '\n':
        cnt_read[i] = 'None'

    w1 = []
    w1.append(cnt_read[0].rstrip())
    w1.append(cnt_read[3].rstrip())
    w2 = []
    w2.append(cnt_read[1].rstrip())    
    w2.append(cnt_read[4].rstrip())
    w3 = []
    w3.append(cnt_read[2].rstrip())    
    w3.append(cnt_read[5].rstrip())

    self.n15_ppms.append(w1)
    self.n15_ppms.append(w2)
    self.n15_ppms.append(w3)

    w4 = []
    w4.append(cnt_read[6].rstrip())    
    w4.append(cnt_read[9].rstrip())
    w5 = []
    w5.append(cnt_read[7].rstrip())    
    w5.append(cnt_read[10].rstrip())
    w6 = []
    w6.append(cnt_read[8].rstrip())    
    w6.append(cnt_read[11].rstrip())

    self.c13_ppms.append(w4)
    self.c13_ppms.append(w5)
    self.c13_ppms.append(w6)

    # update labels in the box
    # 15N
    szLabel = '15N: %s[%s]-%s[%s]-%s[%s]' % (w1[1], w1[0], w2[1], w2[0], w3[1], w3[0])
    self.label_list.append(szLabel, self.n15_ppms)

    # 13C
    szLabel = '13C: %s[%s]-%s[%s]-%s[%s]' % (w4[1], w4[0], w5[1], w5[0], w6[1], w6[0])
    self.label_list.append(szLabel, self.c13_ppms)

# ----------------------------------------------------------------------------
  def move_n_cb(self):
    # validate 15N label
    if len(self.n15_ppms) <> 3:
      tkMessageBox.showerror("Connection Error", "No valid 15N position set.")
      return      
    s1 = self.n15_ppms[0][0]
    s2 = self.n15_ppms[1][0]
    s3 = self.n15_ppms[2][0]
    w1 = self.n15_ppms[0][1]
    w2 = self.n15_ppms[1][1]
    w3 = self.n15_ppms[2][1]
    if s1 == 'None' or s2 == 'None' or s3 == 'None' or w1 == 'None' or w2 == 'None' or w3 == 'None':
      tkMessageBox.showerror("Connection Error", "No valid 15N position set.")
      return      
    v1 = eval(w1)
    v2 = eval(w2)
    v3 = eval(w3)

    # check if user set spectrum
    if self.nnoe.spectrum() == None: 
      tkMessageBox.showerror("Connection Error", "Please set 15N NOESY.")
      return
      
    # move to the 15N, place a peak
    peak = self.nnoe.spectrum().place_peak((v1, v2, v3))
    peak.selected = 1
    for i in range(len(self.n15_ppms)):
      assgn = sputil.split_group_atom(self.n15_ppms[i][0])
      peak.assign(i, assgn[0], assgn[1]) 
    if peak:
      sputil.show_peak(peak)

# ----------------------------------------------------------------------------
  def move_c_cb(self):
    # validate 13C label
    if len(self.c13_ppms) <> 3:
      tkMessageBox.showerror("Connection Error", "No valid 13C position set.")
      return      
    s1 = self.c13_ppms[0][0]
    s2 = self.c13_ppms[1][0]
    s3 = self.c13_ppms[2][0]
    w1 = self.c13_ppms[0][1]
    w2 = self.c13_ppms[1][1]
    w3 = self.c13_ppms[2][1]
    if s1 == 'None' or s2 == 'None' or s3 == 'None' or w1 == 'None' or w2 == 'None' or w3 == 'None':
      tkMessageBox.showerror("Connection Error", "No valid 13C position set.")
      return      
    v1 = eval(w1)
    v2 = eval(w2)
    v3 = eval(w3)

    # check if user set spectrum
    if v1 > 100 or v2 > 100 or v3 > 100:
      spec = self.aronoe.spectrum()
    else:
      spec = self.cnoe.spectrum()
    if spec == None: 
      tkMessageBox.showerror("Connection Error", "Please set 13C NOESY.")
      return
      
    # move to the 13C, place a peak
    frequency = []
    frequency.append(v1)
    frequency.append(v2)
    frequency.append(v3)
    peak = spec.place_peak((v1, v2, v3))
    peak.selected = 1
    for i in range(len(self.c13_ppms)):
      assgn = sputil.split_group_atom(self.c13_ppms[i][0])
      peak.assign(i, assgn[0], assgn[1]) 
    if peak:
      sputil.show_peak(peak)
# ----------------------------------------------------------------------------
  def move_to_selected_cb(self, event):
    # Get currently double clicked item
    ilines = self.label_list.selected_line_numbers()
    if len(ilines) == 0: 
      tkMessageBox.showerror("Connection Error", "Please select a label.")
      return    

    # Parsing d-clicked item
    if ilines[0] == 0:
      self.move_n_cb()
    else:
      self.move_c_cb()
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
# -----------------------------------------------------------------------------
#
def connect_ponderosa_analyzer(session):
  sputil.the_dialog(connect_ponderosa_dialog,session).show_window(1)
