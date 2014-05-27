#
# Roger Chylla
# National Magnetic Resonance Facility at Madison (www.nmrfam.wisc.edu)

# This data structure represents a list of iupac/cyana non-conformances
# Atom_names stored within SPARKY ideally have IUPAC nomenclatures only and 
# CYANA uses some non IUPAC conventions. The data structure below is a list 
# of tuples where each tuple entry is
# the amino acid name (1 letter code), amino_acid (3 letter code),
# iupac nomenclature, and cyana_nomenclature 
# for each instance in which the cyana pseudoatom nomenclature differs from 
# iupac
cyana_iupac_diff = [
    ('A','ALA','MB','QB'),
    ('I','ILE','QG','QG1'),
    ('V','VAL','QG','QQG'),
    ('I','ILE','MG','QG2'),
    ('T','THR','MG','QG2'),
    ('V','VAL','MG1','QG1'),
    ('V','VAL','MG2','QG2'),
    ('N','ASN','QD','QD2'),
    ('N','ASN','QD','QD2'),
    ('I','ILE','MD','QD1'),
    ('L','LEU','MD1','QD1'),
    ('L','LEU','MD2','QD2'),
    ('L','LEU','QD','QQD'),
    ('Q','GLN','QE','QE2'),
    ('M','MET','ME','QE'),
    ('R','ARG','QH','QQH'),
]

#Gets conversion table from Cyana -> IUPAC nomenclature for those pseudoatom
#nomenclatures that are different between the two
def getCyanaToIUPACConversionTable():
  cyanaToIUPAC = {};
  for entry in cyana_iupac_diff:
    aa1,aa3,iupac_atom,cyana_atom = entry;
    key = aa1 + cyana_atom;
    cyanaToIUPAC[key] = iupac_atom;
    key = aa3 + cyana_atom;
    cyanaToIUPAC[key] = iupac_atom;
  return cyanaToIUPAC; 

#Gets conversion table from IUPAC -> Cyana nomenclature for those pseudoatom
#nomenclatures that are different between the two
def getIUPACToCyanaConversionTable():
  iupacToCyana = {};
  for entry in cyana_iupac_diff:
    aa1,aa3,iupac_atom,cyana_atom = entry;
    key = aa1 + iupac_atom;
    iupacToCyana[key] = cyana_atom;
    key = aa3 + iupac_atom;
    iupacToCyana[key] = cyana_atom;
  return iupacToCyana; 

#Applies a conversion table to perform an atom name replacement if necessary
def applyConversion(aa,atom_name,table):
    key = aa.upper() + atom_name;
    has_key = table.has_key(key);
    if has_key:
        atom_name = table[key];
    return atom_name;

# Class for performing conversions. This is the public class that can be instantiated
# and used by external modules
class CyanaDictionary:
  def __init__(self):
      self.cyanaToIUPAC = getCyanaToIUPACConversionTable();
      self.iupacToCyana = getIUPACToCyanaConversionTable();
      
  # Convert from IUPAC to CYANA nomenclature
  # aa = Amino acid 1 letter code
  # atom_name = Atom name (e.g. HA, HB2, HB3, QB, etc.)
  # return Replacement (if necessary) of atom name with cyana compatible atom name
  def toCyana(self,aa,atom_name):
      return applyConversion(aa,atom_name,self.iupacToCyana);
  
  # Convert from CYANA to IUPAC nomenclature
  # aa = Amino acid 1 letter code
  # atom_name = Atom name (e.g. HA, HB2, HB3, QB, etc.)
  # return Replacement (if necessary) of atom name with IUPAC compatible atom name
  def toIUPAC(self,aa,atom_name):
      return applyConversion(aa,atom_name,self.cyanaToIUPAC);
      
