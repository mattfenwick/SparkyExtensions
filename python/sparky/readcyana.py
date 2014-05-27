# -----------------------------------------------------------------------------
# Read a peak list from cyana and create peaks directly onto a spectrum
#
import string
import re
import Tkinter

import pyutil
import sparky
import sputil
import cyana
import tkutil

# -----------------------------------------------------------------------------
#
class read_cyana_peaks_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    self.selection_notice = None

    tkutil.Dialog.__init__(self, session.tk, 'Read Cyana peak list')

    tspectra=('2D','3D')
    initial=tspectra[0]
    self.spectratype = tkutil.option_menu(self.top, "Select spectra dimension", tspectra, initial)
    self.spectratype.frame.pack(side = 'top', anchor = 'w')

    order=('xy','yx','xyz','xzy','yxz','yzx','zxy','zyx')
    initial=order[0]

    self.order = tkutil.option_menu(self.top, "Select output order", order, initial)
    self.order.frame.pack(side = 'top', anchor = 'w')    

    self.plp = tkutil.file_field(self.top, 'Cyana output peak file: ', 'peaklist')
    self.plp.frame.pack(side = 'top', anchor = 'e')
    self.peak_list_path = self.plp
    
    self.pl = tkutil.file_field(self.top,   'Cyana output proton file:', 'protlist')
    self.pl.frame.pack(side = 'top', anchor = 'e')
    self.proton_list_path = self.pl

    self.sl = tkutil.file_field(self.top,   'Sequence file: ', 'seqlist')
    self.sl.frame.pack(side = 'top', anchor = 'e')
    self.sequence_list_path = self.sl

    sc = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice = sc

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'w')

    br = tkutil.button_row(self.top,
			   ('Create peaks', self.read_cb),
			   ('Stop', self.stop_cb),
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'ReadPeaks')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[1])

    #self.settings = self.get_settings()
  # ---------------------------------------------------------------------------
  #
  def read_cb(self):

    fin = self.peak_list_path.get()
    fprot = self.proton_list_path.get()
    fseq = self.sequence_list_path.get()
    spectrum = self.spectrum_choice.spectrum()
    if  fin and fprot and fseq and spectrum:
       self.stoppable_call(self.read_peaks, fin, fprot, fseq, spectrum)

  # ---------------------------------------------------------------------------
  #
  def read_peaks(self, fin, fprot, fseq, spectrum):
 
    #s = self.get_settings()
    #self.settings = s

    stype=self.spectratype.get()
    if stype == '2D':
	    type='2D'
    else:
        type='3D'

    order=self.order.get()
    if len(order) == 3 and stype == '2D':
    	message='You have to select 2D order'
	self.progress_report(message)
	return None
    elif len(order) == 2 and stype == '3D':
	message='You have to select 3D order'
	self.progress_report(message)
	return None

    amino={'ALA' : 'A', # alanine
       'CYS' : 'C', # cysteine
       'CYSS' : 'C', # cysteine
       'ASP' : 'D', # aspartate
       'ASP-' : 'D', # aspartate
       'GLU' : 'E', # glutamate
       'GLU-' : 'E', # glutamate
       'PHE' : 'F', # phenylalanine
       'GLY' : 'G', # glycine
       'HIS' : 'H', # histidine
       'HIS+' : 'H', # histidine
       'HEM' : 'H', # histidine
       'ILE' : 'I', # isoleucine
       'LYS' : 'K', # lysine
       'LYS+' : 'K', # lysine
       'LEU' : 'L', # leucine
       'ASN' : 'N', # asparagine
       'MET' : 'M', # methionine
       'PRO' : 'P', # proline
       'GLN' : 'Q', # glutamine
       'ARG' : 'R', # arginine
       'ARG+' : 'R', # arginine
       'SER' : 'S', # serine
       'THR' : 'T', # threonine
       'VAL' : 'V', # valine
       'TRP' : 'W', # tryptophan
       'TYR' : 'Y'} # tyrosine

    input = open(fin, 'r')
    splines = input.readlines()
    input.close()

    input = open(fprot, 'r')
    plines=input.readlines()
    input.close()

    input = open(fseq, 'r')
    slines = input.readlines()
    input.close()

    seq={}
    # List of 1 letter aa codes per residue
    aa_list = [];
    # Fill in dummy value for aa_list[0]
    aa_list.append(' ');
    for i in range(len(slines)):
      sf=string.split(string.lstrip(slines[i]))
      aa_list.append(sf[0])
      seq[sf[1]]=sf[0]
   

    at1=""
    col1=""
    col2=""
    col3=""
    icol=""
    for i in range(len(splines)):
      self.check_for_stop()
      if re.compile("^#").search(splines[i], 0):
        continue

      fields=string.split(splines[i])

      if type == '2D' and len(fields) >= 10:
        np=fields[0]
        x=float(fields[1])
        y=float(fields[2])
        integ=fields[5]

        if int(fields[9]) == 0 and int(fields[10]) == 0:
          icol='?-?'
          assignment = sputil.parse_assignment(icol)
          frequency = []
          if order == 'xy':
                frequency.append(x)
                frequency.append(y)
          elif order == 'yx':
                frequency.append(y)
                frequency.append(x)
          note = integ + ' lo NP' + np
          self.create_peak(assignment, frequency, note, spectrum)
          continue

      if type == '3D' and len(fields) >= 12:
        np=fields[0]
        x=float(fields[1])
        y=float(fields[2])
        z=float(fields[3])
        integ=fields[6]

        if int(fields[10]) == 0 and int(fields[11]) == 0 and int(fields[12]) == 0:
          icol='?-?-?'
          assignment = sputil.parse_assignment(icol)
          frequency = []
  	  if order == 'xyz':
                frequency.append(x)
                frequency.append(y)
                frequency.append(z)
          elif order == 'yxz':
                frequency.append(y)
                frequency.append(x)
                frequency.append(z)
          elif order == 'xzy':
                frequency.append(x)
                frequency.append(z)
                frequency.append(y)
          elif order == 'zyx':
                frequency.append(z)
                frequency.append(y)
                frequency.append(x)
          elif order == 'zxy':
                frequency.append(z)
                frequency.append(x)
                frequency.append(y)
          elif order == 'yzx':
                frequency.append(y)
                frequency.append(z)
                frequency.append(x)
          note = integ + ' lo NP' + np
          self.create_peak(assignment, frequency, note, spectrum)
          continue

      nar=[]
      nn=[]

      if type == '3D':
        if len(fields) >= 12:
          nn.append(fields[10])
          nn.append(fields[11])
          nn.append(fields[12])
        else:
          nn.append(fields[0])
          nn.append(fields[1])
          nn.append(fields[2])

      if type == '2D': 
        if len(fields) >= 9:
          nn.append(fields[9])
          nn.append(fields[10])
        else:
          nn.append(fields[0])
          nn.append(fields[1])

      cyana_dict = cyana.CyanaDictionary();
      
      for jj in range(len(nn)):
        for j in range(len(plines)):
          pfields=string.split(plines[j])
          if nn[jj] == pfields[0]:
             atm=pfields[3]
             if atm[0] == 'C':
               nuc='13C'
             elif atm[0] == 'N':
               nuc='15N'
             else:
               nuc='1H'
             rns = pfields[4];
             aa = aa_list[int(rns)];
             # Convert cyana nomenclature to IUPAC if necessary
             atm = cyana_dict.toIUPAC(aa,atm);
             amm=amino[seq[rns]] + rns;
             if jj == 0:
               nar.append([amm, atm, nuc, x, integ])
             elif jj == 1:
               nar.append([amm, atm, nuc, y, np])
             else:
               nar.append([amm, atm, nuc, z])
             break
      
      if len(nar) > 1:
        x=float(nar[0][3])
        y=float(nar[1][3])
        integ=nar[0][4]
        npeack=nar[1][4]
        if type == '3D':
          z=float(nar[2][3])

        if nar[0][0]==nar[1][0]:
           if type == '3D':
	     if order=='yxz':
	       col2=nar[0][1]
               if nar[2][0]==nar[0][0]:
   	         col3=nar[2][1]
               else:
	         col3=nar[2][0]+nar[2][1]
	     if order=='zxy':
               col2=nar[0][1]
               if nar[1][0]==nar[0][0]:
	         col3=nar[1][1]
	       else:
	         col3=nar[1][0]+nar[1][1]
	     if order=='yzx':
	       col2=nar[2][1]
 	       if nar[0][0]==nar[2][0]:
	         col3=nar[0][1]
	       else:
	         col3=nar[0][0]+nar[0][1]
	     if order=='xzy':
	       col2=nar[2][1]
  	       if nar[1][0]==nar[2][0]:
	         col3=nar[1][1]
	       else:
	         col3=nar[1][0]+nar[1][1] 
	     if order=='zyx':
	       col2=nar[1][1]
	       if nar[1][0]==nar[0][0]:
	         col3=nar[0][1]
 	       else:
	         col3=nar[0][0]+nar[0][1]
	     elif order=='xyz':
               col2=nar[1][1]
	       if nar[1][0]==nar[2][0]:
	         col3=nar[2][1]
	       else:
                 col3=nar[2][0]+nar[2][1]
           else:
             if order=="yx":
               col2=nar[0][1]
             else:
               col2=nar[1][1]
        else:
           if type == '3D':
	     if order=='yxz':
               col2=nar[0][0]+nar[0][1]
               if nar[0][0]==nar[2][0]:
                 col3=nar[2][1]
               else:
                 col3=nar[2][0]+nar[2][1]
	     elif order=='xzy':
	       if nar[1][0]==nar[2][0]:
                 col3=nar[1][1]
                 col2=nar[2][0]+nar[2][1]
	     elif order=='zyx':
	       if nar[1][0]==nar[2][0]:
	         col2=nar[1][1]
	       else:
	         col2=nar[1][0]+nar[1][1]
               if nar[0][0]==nar[1][0]:
                 col3=nar[0][1]
               else:
	         col3=nar[0][0]+nar[0][1]
	     elif order=="zxy":
	       if nar[0][0]==nar[2][0]:
	         col2=nar[0][1]
	       else:
	         col2=nar[0][0]+nar[0][1]
	       if nar[1][0]==nar[0][0]:
	         col3=nar[1][1]
	       else:
	         col3=nar[1][0]+nar[1][1]
	     elif order=="yzx":
	       if nar[1][0]==nar[2][0]:
	         col2=nar[2][1]
	       else:
	         col2=nar[2][0]+nar[2][1]
	       if nar[2][0]==nar[0][0]:
	         col3=nar[0][1]
	       else:
	         col3=nar[0][0]+nar[0][1]
             elif order=='xyz':
	       if nar[0][0]==nar[1][0]:
    	         col2=nar[1][1]
	       else: 
                 col2=nar[1][0]+nar[1][1]
	       if nar[1][0]==nar[2][0]:
	         col3=nar[2][1]
  	       else:
	         col3=nar[2][0]+nar[2][1]
           else:
             if order=='yx':
               col2=nar[0][0]+nar[0][1]
             else:
               col2=nar[1][0]+nar[1][1]
  
             
        if type == '3D':
          frequency = []
          if order == 'xyz':
	    col1=nar[0][0]+nar[0][1]
            icol=col1+'-'+col2+'-'+col3
	  
            frequency.append(x)
            frequency.append(y)
            frequency.append(z)
	  elif order == 'yxz':
	    col1=nar[1][0]+nar[1][1]
	    icol=col1+'-'+col2+'-'+col3    
	  
            frequency.append(y)
            frequency.append(x)
            frequency.append(z)
	  elif order == 'xzy':
	    col1=nar[0][0]+nar[0][1]
            icol=col1+'-'+col2+'-'+col3
	    
            frequency.append(x)
            frequency.append(z)
            frequency.append(y)
	  elif order == 'zyx':
	    col1=nar[2][0]+nar[2][1]
            icol=col1+'-'+col2+'-'+col3
  
            frequency.append(z)
            frequency.append(y)
            frequency.append(x)
	  elif order == 'zxy':
	    col1=nar[2][0]+nar[2][1]
            icol=col1+'-'+col2+'-'+col3
            assignment = sputil.parse_assignment(icol)
  
            frequency.append(z)
            frequency.append(x)
            frequency.append(y)
	  elif order == 'yzx':
	    col1=nar[1][0]+nar[1][1]
            icol=col1+'-'+col2+'-'+col3
  
            frequency.append(x)
            frequency.append(z)
            frequency.append(y)
        else:
          frequency = []
	  if order == 'xy':
            col1=nar[0][0]+nar[0][1]
	    icol=col1+'-'+col2
  
            frequency.append(x)
            frequency.append(y)
	  elif order == 'yx':
            col1=nar[1][0]+nar[1][1]
	    icol=col1+'-'+col2
  
            frequency.append(y)
            frequency.append(x)
  
        assignment = sputil.parse_assignment(icol)
        note = integ + ' lo NP' + npeack
        self.create_peak(assignment, frequency, note, spectrum)

    return

  # -----------------------------------------------------------------------------
  #
  def create_peak(self, assignment, frequency, note, spectrum):

    peak = spectrum.place_peak(frequency)
    self.move_peak_onto_spectrum(peak)

    assigned = 0
    for a in range(spectrum.dimension):
      group_name, atom_name = assignment[a]
      if group_name or atom_name:
        peak.assign(a, group_name, atom_name)
        assigned = 1

    if assigned:
      peak.show_assignment_label()

    if note:
      peak.note = note

    return

  # ---------------------------------------------------------------------------
  # If the peak is off the edge of the spectrum, fold it onto the spectrum
  # and set the alias to keep its frequency the same.
  #
  def move_peak_onto_spectrum(self, peak):

    freq = peak.frequency
    pos = sputil.alias_onto_spectrum(freq, peak.spectrum)
    if pos != freq:
      peak.position = pos
      peak.alias = pyutil.subtract_tuples(freq, pos)

# -----------------------------------------------------------------------------
#
def read_cyana_peak_list(session):
  sputil.the_dialog(read_cyana_peaks_dialog,session).show_window(1)
