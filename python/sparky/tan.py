# -----------------------------------------------------------------------------
# Transferation of Assignments to Noesy
# -----------------------------------------------------------------------------
#
# Developed by Woonghee Lee
# e-mail: whlee@nmrfam.wisc.edu
# National Magnetic Resonance Facilities at Madison
# Department of Bichemistry, University of Wisconsin at Madison
#
# Last updated: Apr 27, 2010
# 
# Install:
#   Add the following line in the assignment_menu part of sparky_site.py
#       ('ta', 'Transfer assignment to NOESY', ('tan','TAN')),
#
# Usage:
#   Select target NOESY spectra to make it assigned using backbone and side chain assignments
#   type "ta" command or select from extension menu
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
import pinelayout


#
def GetFreq(session, group, szAtom):
    selected_group = []
    selected_group.append(group.symbol)
    selected_group.append(group.number)
    for condition in session.project.condition_list():
        group_name = '%s%d' % (selected_group[0], selected_group[1])
        #group_name = '%s%d' % (selected_group[0], selected_group[1])
        resonance = condition.find_resonance(group_name, szAtom)
        if resonance <> None:
            if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                return 9999, 9999
            return resonance.frequency, resonance.deviation
        else:
            # HN
            if szAtom == 'H':
                resonance = condition.find_resonance(group_name, 'HN')
                if resonance <> None:
                    if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                        return 9999, 9999
                    return resonance.frequency, resonance.deviation
            # processing pseudo atoms
            if pinelayout.pseudo_layout.has_key(selected_group[0]) and szAtom[:1] == 'H':
                layout = pinelayout.pseudo_layout[selected_group[0]]
                szAtom2 = ('Q%s' % szAtom[1:len(szAtom)])
                resonance = condition.find_resonance(group_name, szAtom2)
                if resonance <> None:
                    if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                        return 9999, 9999  
                    return resonance.frequency, resonance.deviation
            # processing meta atoms
            if szAtom == 'H':
                szAtom2 = ('M%s' % szAtom[1:len(szAtom)])
                resonance = condition.find_resonance(group_name, szAtom2)
                if resonance <> None:
                    if (resonance.frequency == 0.0) and (resonance.deviation == 0.0):
                        return 9999, 9999
                    return resonance.frequency, resonance.deviation
    return 9999, 9999

# transferation of assignments
def TAN(session):
    spectrum = session.selected_spectrum()
    if (spectrum == None) or (spectrum.dimension <> 3):
        tkMessageBox.showinfo('Error', 'Select NOESY spectrum to be assigned.')
        return

    #szPrint = '%lf' % (spectrum.region[0][0])
    #tkMessageBox.showinfo('0,0', szPrint)
    #return

    Carbons = 'CA CB CD CD1 CD2 CE CE1 CE2 CE3 CG CG1 CG2 CH2 CZ CZ2 CZ3'
    Protons = 'HA HA2 HA3 HB HB2 HB3 HD1 HD2 HD21 HD22 HD3 HE HE1 HE2 HE21 HE22 HE3 HG HG1 HG12 HG13 HG2 HG3 HH11 HH12 HH2 HH21 HH22 HZ HZ2 HZ3 QA QB QG QG1 QG2 QD QD1 QD2 QE QE2 QH1 QH2 QZ'
    Nitrogen = 'N'
 
    # Check NOESY TYPE
    # NNOESY: N 100-150, H < 15, H < 15
    # CNOESY: C 20 - 80, H < 15, H < 15
    [[min1, min2, min3], [max1, max2, max3]] = spectrum.region

    # DIM 1
    if (max1 > 100) and (max1 < 150):
        ntype = 'N'
    elif (max1 > 20) and (max1 < 80):
        ntype = 'C'
    elif (max1 < 15):
        ntype = 'H'
    else:
        tkMessageBox.showinfo('Error', 'Select NOESY spectrum to be assigned.')
        return

    # DIM 2
    if (max2 > 100) and (max2 < 150):
        ntype = ntype + 'N'
    elif (max2 > 20) and (max2 < 80):
        ntype = ntype + 'C'
    elif (max2 < 15):
        ntype = ntype + 'H'
    else:
        tkMessageBox.showinfo('Error', 'Select NOESY spectrum to be assigned.')
        return
    # DIM 3
    if (max3 > 100) and (max3 < 150):
        ntype = ntype + 'N'
    elif (max3 > 20) and (max3 < 80):
        ntype = ntype + 'C'
    elif (max3 < 15):
        ntype = ntype + 'H'
    else:
        tkMessageBox.showinfo('Error', 'Select NOESY spectrum to be assigned.')
        return
        
    if (ntype <> 'NHH') and (ntype <> 'HNH') and (ntype <> 'HHN') and (ntype <> 'CHH') and (ntype <> 'HCH') and (ntype <> 'HHC'):
        tkMessageBox.showinfo('Error', 'Select NOESY spectrum to be assigned.')
        return    

    if (ntype == 'NHH') or (ntype == 'HNH') or (ntype == 'HHN'):
        ntype1 = 1  # N-NOESY
    else:
        ntype1 = 2  # C-NOESY

    pnames = Protons.split()
    cnames = Carbons.split()
    hnames = pnames
    hnames.insert(0, 'H')

    iCNidx = ntype.find('N')
    heavyatoms = Nitrogen.split()
    if iCNidx == -1:
        iCNidx = ntype.find('C')
        heavyatoms = cnames

    #N, C:1
    if (spectrum.spectrum_width[0] > spectrum.spectrum_width[1]) and (spectrum.spectrum_width[0] > spectrum.spectrum_width[2]):
        if (spectrum.spectrum_width[1] > spectrum.spectrum_width[2]):
            szHH = 'NhH'
        else:
            szHH = 'NHh'
    #N, C:2
    elif (spectrum.spectrum_width[1] > spectrum.spectrum_width[0]) and (spectrum.spectrum_width[1] > spectrum.spectrum_width[2]):
        if (spectrum.spectrum_width[0] > spectrum.spectrum_width[2]):
            szHH = 'hNH'
        else:
            szHH = 'HNh'
    #N, C:3
    elif (spectrum.spectrum_width[2] > spectrum.spectrum_width[0]) and (spectrum.spectrum_width[2] > spectrum.spectrum_width[1]):
        if (spectrum.spectrum_width[0] > spectrum.spectrum_width[1]):
            szHH = 'hHN'
        else:
            szHH = 'HhN'
    # change N to C-NOESY
    if ntype1 == 2:
        szHH.replace('N','C')

    # Get sequence index
    # Sorting is included
    group_list = []
    for molecule in session.project.molecule_list():
        for group in molecule.group_list():
            bAdded = False
            for group2 in group_list:
                if group == group2:
                    bAdded = True
                    break
            if bAdded == False:
                group_list.append(group)            
    # Sorting
    for i in range(len(group_list)):
        group = group_list[i]
        for j in range(len(group_list)):
            if i >= j:
                continue
            group2 = group_list[j]
            if group.number > group2.number:
                group_list[i] = group2
                group_list[j] = group
                group = group2
                continue

      
    # Loop sequence
    # GROUP: M1     #ATOMNAME:CA #RESONANCE.name : M1CA
    iAddedCount = 0
    for i in range(len(group_list)):
        if i == 0:
            group = None
        else:
            group = group_list[i-1]
        group2 = group_list[i]
        if i == len(group_list)-1:
            group3 = None
        else:
            group3 = group_list[i+1]
        # see prior and next group sequence index	
        if (group <> None) and (group.number <> group2.number-1):
            group = None
        if (group3 <> None) and (group3.number <> group2.number+1):
            group3 = None

        # set list for group, group2, group3
        grouplt = []
        if group <> None:
            grouplt.append(group)
        if group2 <> None:
            grouplt.append(group2)
        if group3 <> None:	
            grouplt.append(group3)

        # N, CX loop
        for szHeavyAtom in heavyatoms:
            # N, CX frequency
            [fHeavyFreq, fHeavyDevi] = GetFreq(session, group2, szHeavyAtom)
            if (fHeavyFreq > 1000) and (fHeavyDevi > 1000):
                continue
            # H, HX frequency
            H_atom_list = []
            szTempH = 'H' + szHeavyAtom[1:]
            szTempQ = 'Q' + szHeavyAtom[1:]
            #tkMessageBox.showinfo('szTempH', szTempH)
            #tkMessageBox.showinfo('szTempQ', szTempQ)
            for szHAtom in hnames: 
                #tkMessageBox.showinfo('szHAtom', szHAtom)
                if (szHAtom == szTempH) or ( (szHAtom[:-1] == szTempH) and (szHAtom[:-1] <> 'H') ) or (szHAtom == szTempQ) or ( (szHAtom[:-1] == szTempQ) and (szHAtom[:-1] <>'Q')):
                    #szStr = '%s, %s, %s' % (szHAtom, szTempH, szTempQ)
                    #tkMessageBox.showinfo('szHAtom', szStr)
                    H_atom_list.append(szHAtom)
            for szHAtom in H_atom_list:
                [fHFreq, fHDevi] = GetFreq(session, group2, szHAtom)
                if (fHFreq > 1000) and (fHDevi > 1000):
                    continue

                # loop for group, group2, group3
                for grp in grouplt:
                    for szhAtom in hnames:
                        if grp.number <> group2.number:
                            if grp.number+1 == group2.number:   # i-1
                                #if ntype1 == 1: # N-NOESY
                                #    if szhAtom == 'H':
                                #        continue
                                #elif ntype1 == 2: # C-NOESY
                                if ntype1 == 2: # C-NOESY
                                    #if szhAtom <> 'H':
                                        # if ((szHAtom <> 'HA') and (szHAtom <> 'HA2')) or ((szhAtom <> 'HA') and (szhAtom <> 'HA2')):
                                        continue
                            elif grp.number-1 == group2.number:  # i+1
                                if ntype1 == 1: # N-NOESY
                                    if szhAtom <> 'H':
                                        continue
                                elif ntype1 == 2: # C-NOESY
                                    if szhAtom <> 'H':
                                        #if ((szHAtom <> 'HA') and (szHAtom <> 'HA2')) or ((szhAtom <> 'HA') and (szhAtom <> 'HA2')):
                                        continue
                        [fhFreq, fhDevi] = GetFreq(session, grp, szhAtom)
                        if (fhFreq > 1000) and (fhDevi > 1000):
                            continue
                        # Assign!
                        pFreqList = []
                        pAtomList = []
                        pSymbolList = [] # M1, D2......
                        # axis order
                        for j in range(3):
                            if (szHH[j] == 'N') or (szHH[j] == 'C'):
                                pFreqList.append(fHeavyFreq)
                                pAtomList.append(szHeavyAtom)
                                pSymbolList.append(group2.symbol+str(group2.number))
                            elif (szHH[j] == 'H'):
                                pFreqList.append(fHFreq)
                                pAtomList.append(szHAtom)
                                pSymbolList.append(group2.symbol+str(group2.number))
                            elif (szHH[j] == 'h'):
                                pFreqList.append(fhFreq)
                                pAtomList.append(szhAtom)
                                pSymbolList.append(grp.symbol+str(grp.number))

                        pPeak = spectrum.place_peak(pFreqList)
                        pPeak.assign(0, pSymbolList[0], pAtomList[0])
                        pPeak.assign(1, pSymbolList[1], pAtomList[1])
                        pPeak.assign(2, pSymbolList[2], pAtomList[2])
                        pPeak.show_assignment_label() 
                        iAddedCount = iAddedCount+1
    ########################################################

    szPrint = '%d peaks were transfered.' % (iAddedCount)
    tkMessageBox.showinfo('Transfer Assignment to NOESY', szPrint)
