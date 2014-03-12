# -----------------------------------------------------------------------------
# This file defines atom name translations for translating between
# Sparky assignment, PDB, Mardigras, ... atom names, and standard names.
# The standard names are at the end of this file and should not be modified.
#
# There are 3 types of atom name translations: residue name translations,
# atom name translations for specific residues, and atom name translations
# for any residue.  In translating a residue + atom name first the residue
# name is translated, then a residue-specific translation is applied if
# one exists, otherwise residue-nonspecific translations are used.
#
# For example GLY HN -> G HN (applying a GLY->G residue name translation),
# then if there is no specific G HN atom name translation, a non-specific
# one (for instance HN -> H) is applied.
#
# To define a translation pairs of names are used where the first name is
# the non-standard name and the second name is the standard one.  For example,
# since one letter amino acid names are used as the standard, the GLY -> G
# translations is represented as ('GLY', 'G').  And a residue-nonspecific
# translation HN -> H is represented as ('HN', 'H').  A residue specific
# G HN -> G H translation is represented as a triple ('G', 'HN', 'H').
#
# A translation convention consists of three lists (possibly empty), one
# for each of the three basic translation types.  Translation conventions
# have names that are used in by the atom name translation dialog to show
# which conventions are being used.
#
# See below for examples of translations conventions.
#

translation_conventions = []

# -----------------------------------------------------------------------------
# 3 letter amino acid codes to 1 letter codes.
#
aaa_to_a = {
  'ALA':'A',
  'ARG':'R',
  'ASN':'N',
  'ASP':'D',
  'CYS':'C',
  'GLN':'Q',
  'GLU':'E',
  'GLY':'G',
  'HIS':'H',
  'ILE':'I',
  'LEU':'L',
  'LYS':'K',
  'MET':'M',
  'PHE':'F',
  'PRO':'P',
  'SER':'S',
  'THR':'T',
  'TRP':'W',
  'TYR':'Y',
  'VAL':'V',
}

# -----------------------------------------------------------------------------
# 3 letter amino acid codes to 1 letter codes.
#
translation_conventions.append(('GLY -> G, ...', aaa_to_a.items(), (), ()))

# -----------------------------------------------------------------------------
# Amide HN to H.
#
hn_h = (('HN', 'H'),)
translation_conventions.append(('HN -> H', (), (), hn_h))

# -----------------------------------------------------------------------------
# Prime / double prime -> '1 '2 rule (for H2', H2", H5', H5")
#
dp = (("H2'", "H2'1"), ('H2"', "H2'2"),
      ("H5'", "H5'1"), ('H5"', "H5'2"),)
translation_conventions.append(('''H5' -> H5'1, H5" -> H5'2, ...''',
                               (), (), dp))

# -----------------------------------------------------------------------------
# 123 prefixes to suffixes
#
pre = (("1H2'", "H2'1"), ("2H2'", "H2'2"),
       ("1H5'", "H5'1"), ("2H5'", "H5'2"),
       ('1H6', 'H61'), ('2H6', 'H62'),
       ('1H4', 'H41'), ('2H4', 'H42'),
       ('1H2', 'H21'), ('2H2', 'H22'),
       ('1H7', 'H71'), ('2H7', 'H72'), ('3H7', 'H73'),
       ('1HA', 'HA1'), ('2HA', 'HA2'), ('3HA', 'HA3'),
       ('1HB', 'HB1'), ('2HB', 'HB2'), ('3HB', 'HB3'),
       ('1HG', 'HG1'), ('2HG', 'HG2'), ('3HG', 'HG3'),
       ('1HG1', 'HG11'), ('2HG1', 'HG12'), ('3HG1', 'HG13'),
       ('1HG2', 'HG21'), ('2HG2', 'HG22'), ('3HG2', 'HG23'),
       ('1HD', 'HD1'), ('2HD', 'HD2'), ('3HD', 'HD3'),
       ('1HD1', 'HD11'), ('2HD1', 'HD12'), ('3HD1', 'HD13'),
       ('1HD2', 'HD21'), ('2HD2', 'HD22'), ('3HD2', 'HD23'),
       ('1HE', 'HE1'), ('2HE', 'HE2'), ('3HE', 'HE3'),
       ('1HE2', 'HE21'), ('2HE2', 'HE22'),
       ('1HZ', 'HZ1'), ('2HZ', 'HZ2'), ('3HZ', 'HZ3'),
       ('2HH', 'HH2'),
       ('1HH1', 'HH11'), ('2HH1', 'HH12'),
       ('1HH2', 'HH21'), ('2HH2', 'HH22'),
       )
translation_conventions.append(('1H7 -> H71, 2H7 -> H72, ...', (), (), pre))

# -----------------------------------------------------------------------------
# 12 suffixes to 23 suffixes
#
s12s23 = (
  ('G', 'HA1', 'HA2'), ('G', 'HA2', 'HA3'),
  ('C', 'HB1', 'HB2'), ('C', 'HB2', 'HB3'),
  ('D', 'HB1', 'HB2'), ('D', 'HB2', 'HB3'),
  ('E', 'HB1', 'HB2'), ('E', 'HB2', 'HB3'),
  ('E', 'HG1', 'HG2'), ('E', 'HG2', 'HG3'),
  ('F', 'HB1', 'HB2'), ('F', 'HB2', 'HB3'),
  ('H', 'HB1', 'HB2'), ('H', 'HB2', 'HB3'),
  ('I', 'HG11', 'HG12'), ('I', 'HG12', 'HG13'),
  ('K', 'HB1', 'HB2'), ('K', 'HB2', 'HB3'),
  ('K', 'HD1', 'HD2'), ('K', 'HD2', 'HD3'),
  ('K', 'HG1', 'HG2'), ('K', 'HG2', 'HG3'),
  ('K', 'HE1', 'HE2'), ('K', 'HE2', 'HE3'),
  ('L', 'HB1', 'HB2'), ('L', 'HB2', 'HB3'),
  ('M', 'HB1', 'HB2'), ('M', 'HB2', 'HB3'),
  ('M', 'HG1', 'HG2'), ('M', 'HG2', 'HG3'),
  ('N', 'HB1', 'HB2'), ('N', 'HB2', 'HB3'),
  ('P', 'HB1', 'HB2'), ('P', 'HB2', 'HB3'),
  ('P', 'HD1', 'HD2'), ('P', 'HD2', 'HD3'),
  ('P', 'HG1', 'HG2'), ('P', 'HG2', 'HG3'),
  ('Q', 'HB1', 'HB2'), ('Q', 'HB2', 'HB3'),
  ('Q', 'HG1', 'HG2'), ('Q', 'HG2', 'HG3'),
  ('R', 'HB1', 'HB2'), ('R', 'HB2', 'HB3'),
  ('R', 'HD1', 'HD2'), ('R', 'HD2', 'HD3'),
  ('R', 'HG1', 'HG2'), ('R', 'HG2', 'HG3'),
  ('S', 'HB1', 'HB2'), ('S', 'HB2', 'HB3'),
  ('W', 'HB1', 'HB2'), ('W', 'HB2', 'HB3'),
  ('Y', 'HB1', 'HB2'), ('Y', 'HB2', 'HB3'),
)

# -----------------------------------------------------------------------------
# 12 suffixes to 32 suffixes ( only Hx3 <-> Hx1 )
#
s12s32 = (
 ('G', 'HA1',  'HA3'),
 ('C', 'HB1',  'HB3'),
 ('D', 'HB1',  'HB3'),
 ('E', 'HB1',  'HB3'),
 ('E', 'HG1',  'HG3'),
 ('F', 'HB1',  'HB3'),
 ('H', 'HB1',  'HB3'),
 ('I', 'HG11', 'HG13'),
 ('K', 'HB1',  'HB3'),
 ('K', 'HD1',  'HD3'),
 ('K', 'HG1',  'HG3'),
 ('K', 'HE1',  'HE3'),
 ('L', 'HB1',  'HB3'),
 ('M', 'HB1',  'HB3'),
 ('M', 'HG1',  'HG3'),
 ('N', 'HB1',  'HB3'),
 ('P', 'HB1',  'HB3'),
 ('P', 'HD1',  'HD3'),
 ('P', 'HG1',  'HG3'),
 ('Q', 'HB1',  'HB3'),
 ('Q', 'HG1',  'HG3'),
 ('R', 'HB1',  'HB3'),
 ('R', 'HD1',  'HD3'),
 ('R', 'HG1',  'HG3'),
 ('S', 'HB1',  'HB3'),
 ('W', 'HB1',  'HB3'),
 ('Y', 'HB1',  'HB3'),
)

# -----------------------------------------------------------------------------
# Test if 1/2 or 2/3 suffixes are being used.
#
has_1_suffix = {
  ('G', 'HA1'):1, 
  ('C', 'HB1'):1, ('D', 'HB1'):1, ('E', 'HB1'):1,
  ('F', 'HB1'):1, ('H', 'HB1'):1, ('K', 'HB1'):1, ('L', 'HB1'):1,
  ('M', 'HB1'):1, ('N', 'HB1'):1, ('P', 'HB1'):1, ('Q', 'HB1'):1,
  ('R', 'HB1'):1, ('S', 'HB1'):1, ('W', 'HB1'):1, ('Y', 'HB1'):1,
  ('E', 'HG1'):1, ('K', 'HG1'):1, ('M', 'HG1'):1, ('P', 'HG1'):1,
  ('Q', 'HG1'):1, ('R', 'HG1'):1, ('I', 'HG11'):1, ('K', 'HD1'):1,
  ('P', 'HD1'):1, ('R', 'HD1'):1, 
  ('K', 'HE1'):1, 
}
has_3_suffix = {
  ('G', 'HA3'):1, 
  ('C', 'HB3'):1, ('D', 'HB3'):1, ('E', 'HB3'):1,
  ('F', 'HB3'):1, ('H', 'HB3'):1, ('K', 'HB3'):1, ('L', 'HB3'):1,
  ('M', 'HB3'):1, ('N', 'HB3'):1, ('P', 'HB3'):1, ('Q', 'HB3'):1,
  ('R', 'HB3'):1, ('S', 'HB3'):1, ('W', 'HB3'):1, ('Y', 'HB3'):1,
  ('E', 'HG3'):1, ('K', 'HG3'):1, ('M', 'HG3'):1, ('P', 'HG3'):1,
  ('Q', 'HG3'):1, ('R', 'HG3'):1, ('I', 'HG13'):1, ('K', 'HD3'):1,
  ('P', 'HD3'):1, ('R', 'HD3'):1, 
  ('K', 'HE3'):1, 
}

# -----------------------------------------------------------------------------
#
def is_using_12(group_atoms):
  for ga in group_atoms:
    if has_1_suffix.has_key(ga):        return 1
    elif has_3_suffix.has_key(ga):      return 0
  return 0

# -----------------------------------------------------------------------------
#
translation_conventions.append(('HB1 -> HB2, HB2 -> HB3, ...',
                                (), s12s32, (), is_using_12))

# -----------------------------------------------------------------------------
#
h7m7 = (('T', 'H7', 'M7'),)
translation_conventions.append(('T H7 -> T M7', (), h7m7, ()))

# -----------------------------------------------------------------------------
# The stuff below defines standard atom names.  It's not a good idea to change
# these since other code (like spin graph layout defined in spinlayout.py)
# uses these names.
#
# Protein standard atom names are taken from BioMagResBank
#

# -----------------------------------------------------------------------------
# Standard atom names for 20 standard amino acids.
# BioMagResBank names are used.
#
protein_atoms_by_group = {
  'A':('C', 'CA', 'CB', 'H', 'HA', 'HB1', 'HB2', 'HB3', 'MB', 'N'),
  'C':('C', 'CA', 'CB', 'H', 'HA', 'HB2', 'HB3', 'QB', 'HG', 'N'),
  'D':('C', 'CA', 'CB', 'CG', 'H', 'HA', 'HB2', 'HB3', 'QB', 'HD2', 'OD1', 'OD2', 'N'),
  'E':('C', 'CA', 'CB', 'CD', 'CG', 'H', 'HA', 'HB2', 'HB3', 'QB',
       'HE2', 'OE1', 'OE2', 'HG2', 'HG3', 'QG', 'N'),
  'F':('C', 'CA', 'CB', 'CD1', 'CD2', 'CQD', 'CE1', 'CE2', 'CQE', 'CG', 'CZ',
       'H', 'HA', 'HB2', 'HB3', 'QB', 'HD1', 'HD2', 'QD', 'HE1', 'HE2', 'QE',
       'HZ', 'N'),
  'G':('C', 'CA', 'H', 'HA2', 'HA3', 'QA', 'N'),
  'H':('C', 'CA', 'CB', 'CD2', 'CE1', 'CG', 'H', 'HA',
       'HB2', 'HB3', 'QB', 'HD1', 'HD2', 'HE1', 'HE2',
       'N', 'ND1', 'NE2'),
  'I':('C', 'CA', 'CB', 'CD1', 'CG1', 'CG2', 'CQG', 'H', 'HA', 'HB',
       'HD11', 'HD12', 'HD13', 'MD1', 'HG12', 'HG13', 'QG1',
       'HG21', 'HG22', 'HG23', 'MG2', 'N'),
  'K':('C', 'CA', 'CB', 'CD', 'CE', 'CG', 'H', 'HA',
       'HB2', 'HB3', 'QB', 'HD2', 'HD3', 'QD', 'HE2', 'HE3', 'QE',
       'HG2', 'HG3', 'QG', 'HZ1', 'HZ2', 'HZ3', 'MZ', 'N', 'NZ'),
  'L':('C', 'CA', 'CB', 'CD1', 'CD2', 'CQD', 'CG', 'H', 'HA',
       'HB2', 'HB3', 'QB', 'HD11', 'HD12', 'HD13', 'MD1',
       'HD21', 'HD22', 'HD23', 'MD2', 'QMD', 'HG', 'N'),
  'M':('C', 'CA', 'CB', 'CE', 'CG', 'H', 'HA', 'HB2', 'HB3', 'QB',
       'HE1', 'HE2', 'HE3', 'ME', 'HG2', 'HG3', 'QG', 'N'),
  'N':('C', 'CA', 'CB', 'CG', 'H', 'HA', 'HB2', 'HB3', 'QB',
       'HD21', 'HD22', 'QD2', 'N', 'ND2', 'OD1'),
  'P':('C', 'CA', 'CB', 'CD', 'CG', 'H2', 'H3', 'HA',
       'HB2', 'HB3', 'QB', 'HD2', 'HD3', 'QD', 'HG2', 'HG3', 'QG', 'N'),
  'Q':('C', 'CA', 'CB', 'CD', 'CG', 'H', 'HA', 'HB2', 'HB3', 'QB',
       'HE21', 'HE22', 'QE2', 'HG2', 'HG3', 'QG', 'N', 'NE2', 'OE1'),
  'R':('C', 'CA', 'CB', 'CD', 'CG', 'CZ', 'H', 'HA', 'HB2', 'HB3', 'QB',
       'HD2', 'HD3', 'QD', 'HE', 'HG2', 'HG3', 'QG', 'HH11', 'HH12', 'QH1',
       'HH21', 'HH22', 'QH2', 'QQH', 'N', 'NE', 'NH1', 'NH2', 'NQH'),
  'S':('C', 'CA', 'CB', 'H', 'HA', 'HB2', 'HB3', 'QB', 'HG', 'OG', 'N'),
  'T':('C', 'CA', 'CB', 'CG2', 'H', 'HA', 'HB', 'HG1', 'OG1',
       'HG21', 'HG22', 'HG23', 'MG2', 'N'),
  'V':('C', 'CA', 'CB', 'CG1', 'CG2', 'CQG', 'H', 'HA', 'HB',
       'HG11', 'HG12', 'HG13', 'MG1', 'HG21', 'HG22', 'HG23', 'MG2', 'QMG',
       'N'),
  'W':('C', 'CA', 'CB', 'CD1', 'CD2', 'CE2', 'CE3', 'CG', 'CH2',
       'CZ2', 'CZ3', 'H', 'HA', 'HB2', 'HB3', 'QB', 'HD1', 'HE1', 'HE3',
       'HH2', 'HZ2', 'HZ3', 'N', 'NE1'),
  'Y':('C', 'CA', 'CB', 'CD1', 'CD2', 'CQD', 'CE1', 'CE2', 'CQE', 'CG', 'CZ',
       'H', 'HA', 'HB2', 'HB3', 'QB', 'HD1', 'HD2', 'QD', 'HE1', 'HE2', 'QE',
       'HH', 'OH', 'N')
  }

# -----------------------------------------------------------------------------
#
protein_pseudo_atoms = {
  ('A', 'MB'):('HB1', 'HB2', 'HB3'),
  ('C', 'QB'):('HB2', 'HB3'),
  ('D', 'QB'):('HB2', 'HB3'),
  ('E', 'QB'):('HB2', 'HB3'),
  ('E', 'QG'):('HG2', 'HG3'),
  ('F', 'CQD'):('CD1', 'CD2'),
  ('F', 'CQE'):('CE1', 'CE2'),
  ('F', 'QB'):('HB2', 'HB3'),
  ('F', 'QD'):('HD1', 'HD2'),
  ('F', 'QE'):('HE1', 'HE2'),
  ('G', 'QA'):('HA2', 'HA3'),
  ('H', 'QB'):('HB2', 'HB3'),
  ('I', 'CQG'):('CG1', 'CG2'),
  ('I', 'MD1'):('HD11', 'HD12', 'HD13'),
  ('I', 'QG1'):('HG12', 'HG13'),
  ('I', 'MG2'):('HG21', 'HG22', 'HG23'),
  ('K', 'QB'):('HB2', 'HB3'),
  ('K', 'QG'):('HG2', 'HG3'),
  ('K', 'QD'):('HD2', 'HD3'),
  ('K', 'QE'):('HE2', 'HE3'),
  ('K', 'MZ'):('HZ1', 'HZ2', 'HZ3'),
  ('L', 'CQD'):('CD1', 'CD2'),
  ('L', 'QB'):('HB2', 'HB3'),
  ('L', 'MD1'):('HD11', 'HD12', 'HD13'),
  ('L', 'MD2'):('HD21', 'HD22', 'HD23'),
  ('L', 'QMD'):('HD11', 'HD12', 'HD13', 'HD21', 'HD22', 'HD23'),
  ('M', 'QB'):('HB2', 'HB3'),
  ('M', 'ME'):('HE1', 'HE2', 'HE3'),
  ('M', 'QG'):('HG2', 'HG3'),
  ('N', 'QB'):('HB2', 'HB3'),
  ('N', 'QD2'):('HD21', 'HD22'),
  ('P', 'QB'):('HB2', 'HB3'),
  ('P', 'QD'):('HD2', 'HD3'),
  ('P', 'QG'):('HG2', 'HG3'),
  ('Q', 'QB'):('HB2', 'HB3'),
  ('Q', 'QE2'):('HE21', 'HE22'),
  ('Q', 'QG'):('HG2', 'HG3'),
  ('R', 'NQH'):('NH1', 'NH2'),
  ('R', 'QB'):('HB2', 'HB3'),
  ('R', 'QG'):('HG2', 'HG3'),
  ('R', 'QD'):('HD2', 'HD3'),
  ('R', 'QH1'):('HH11', 'HH12'),
  ('R', 'QH2'):('HH21', 'HH22'),
  ('R', 'QQH'):('HH11', 'HH12', 'HH21', 'HH22'),
  ('S', 'QB'):('HB2', 'HB3'),
  ('T', 'MG2'):('HG21', 'HG22', 'HG23'),  
  ('V', 'CQG'):('CG1', 'CG2'),
  ('V', 'MG1'):('HG11', 'HG12', 'HG13'),
  ('V', 'MG2'):('HG21', 'HG22', 'HG23'),
  ('V', 'QMG'):('HG11', 'HG12', 'HG13', 'HG21', 'HG22', 'HG23'),
  ('W', 'QB'):('HB2', 'HB3'),
  ('Y', 'CQD'):('CD1', 'CD2'),
  ('Y', 'CQE'):('CE1', 'CE2'),
  ('Y', 'QB'):('HB2', 'HB3'),
  ('Y', 'QD'):('HD1', 'HD2'),
  ('Y', 'QE'):('HE1', 'HE2'),
}

# -----------------------------------------------------------------------------
#
protein_attached_heavy_atoms = {
  'A': {'H':'N', 'HA':'CA', 'HB1':'CB', 'HB2':'CB', 'HB3':'CB', 'MB':'CB'},
  'C': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB', 'HG':'S'},
  'D': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB', 'HD2':'OD2'},
  'E': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HE2':'OE2', 'HG2':'CG', 'HG3':'CG', 'QG':'CG'},
  'F': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD1':'CD1', 'HD2':'CD2', 'QD':'CQD',
	'HE1':'CE1', 'HE2':'CE2', 'QE':'CQE', 'HZ':'CZ'},
  'G': {'H':'N', 'HA2':'CA', 'HA3':'CA', 'QA':'CA'},
  'H': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD1':'ND1', 'HD2':'CD2', 'HE1':'CE1', 'HE2':'NE2'},
  'I': {'H':'N', 'HA':'CA', 'HB':'CB',
	'HD11':'CD1', 'HD12':'CD1', 'HD13':'CD1', 'MD1':'CD1',
	'HG12':'CG1', 'HG13':'CG1', 'QG1':'CG1',
	'HG21':'CG2', 'HG22':'CG2', 'HG23':'CG2', 'MG2':'CG2'},
  'K': {'H':'N', 'HA':'CA',
	'HB2':'CB', 'HB3':'CB', 'QB':'CB', 'HD2':'CD', 'HD3':'CD', 'QD':'CD',
	'HE2':'CE', 'HE3':'CE',	'HG2':'CG', 'HG3':'CG', 'QG':'CG',
	'HZ1':'NZ', 'HZ2':'NZ', 'HZ3':'NZ'},
  'L': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD11':'CD1', 'HD12':'CD1', 'HD13':'CD1', 'MD1':'CD1',
	'HD21':'CD2', 'HD22':'CD2', 'HD23':'CD2', 'MD2':'CD2', 'QMD':'CQD',
	'HG':'CG'},
  'M': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HE1':'CE', 'HE2':'CE', 'HE3':'CE', 'ME':'CE',
	'HG2':'CG', 'HG3':'CG', 'QG':'CG'},
  'N': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD21':'ND2', 'HD22':'ND2', 'QD2':'ND2'},
  'P': {'H2':'N', 'H3':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD2':'CD', 'HD3':'CD', 'QD':'CD', 'HG2':'CG', 'HG3':'CG', 'QG':'CG'},
  'Q': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HE21':'NE2', 'HE22':'NE2', 'QE2':'NE2',
	'HG2':'CG', 'HG3':'CG', 'QG':'CG'},
  'R': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD2':'CD', 'HD3':'CD', 'QD':'CD',
	'HE':'NE', 'HG2':'CG', 'HG3':'CG', 'QG':'CG',
	'HH11':'NH1', 'HH12':'NH1', 'QH1':'NH1',
	'HH21':'NH2', 'HH22':'NH2', 'QH2':'NH2', 'QQH':'NQH'},
  'S': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB', 'HG':'OG'},
  'T': {'H':'N', 'HA':'CA', 'HB':'CB', 'HG1':'OG1',
	'HG21':'CG2', 'HG22':'CG2', 'HG23':'CG2', 'MG2':'CG2'},
  'V': {'H':'N', 'HA':'CA', 'HB':'CB',
	'HG11':'CG1', 'HG12':'CG1', 'HG13':'CG1', 'MG1':'CG1',
	'HG21':'CG2', 'HG22':'CG2', 'HG23':'CG2', 'MG2':'CG2', 'QMG':'CQG'},
  'W': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
	'HD1':'CD1', 'HE1':'NE1', 'HE3':'CE3',
	'HH2':'CH2', 'HZ2':'CZ2', 'HZ3':'CZ3'},
  'Y': {'H':'N', 'HA':'CA', 'HB2':'CB', 'HB3':'CB', 'QB':'CB',
        'HD1':'CD1', 'HD2':'CD2', 'QD':'CQD',
        'HE1':'CE1', 'HE2':'CE2', 'QE':'CQE', 'HH':'OH'},
}

# -----------------------------------------------------------------------------
# Standard atom names for DNA and RNA
#
dna_rna_atoms_by_group = {
  'A':('P', 'O1P', 'O2P', "O2'", "O3'", "O4'", "O5'",
       "C1'", "C2'", "C3'", "C4'", "C5'",
       "H1'", "H2'1", "H2'2", "H2'", "H3'", "H4'", "H5'1", "H5'2",
       'N1', 'C2', 'N3', 'C4', 'C5', 'C6', 'N6', 'N7', 'C8', 'N9',
       'H2', 'H61', 'H62', 'H8'),
  'C':('P', 'O1P', 'O2P', "O2'", "O3'", "O4'", "O5'",
       "C1'", "C2'", "C3'", "C4'", "C5'",
       "H1'", "H2'1", "H2'2", "H2'", "H3'", "H4'", "H5'1", "H5'2",
       'N1', 'C2', 'O2', 'N3', 'C4', 'N4', 'C5', 'C6',
       'H41', 'H42', 'H5', 'H6'),
  'G':('P', 'O1P', 'O2P', "O2'", "O3'", "O4'", "O5'",
       "C1'", "C2'", "C3'", "C4'", "C5'",
       "H1'", "H2'1", "H2'2", "H2'", "H3'", "H4'", "H5'1", "H5'2",
       'N1', 'C2', 'N2', 'N3', 'C4', 'C5', 'C6', 'O6', 'N7', 'C8', 'N9',
       'H1', 'H21', 'H22', 'H8'),
  'T':('P', 'O1P', 'O2P', "O3'", "O4'", "O5'",
       "C1'", "C2'", "C3'", "C4'", "C5'",
       "H1'", "H2'1", "H2'2", "H3'", "H4'", "H5'1", "H5'2",
       'N1', 'C2', 'O2', 'N3', 'C4', 'O4', 'C5', 'C6', 'C7',
       'H3', 'H6', 'H71', 'H72', 'H73', 'M7'),
  'U':('P', 'O1P', 'O2P', "O2'", "O3'", "O4'", "O5'",
       "C1'", "C2'", "C3'", "C4'", "C5'",
       "H1'", "H2'", "H3'", "H4'", "H5'1", "H5'2",
       'N1', 'C2', 'N3', 'C4', 'C5', 'C6',
       'H3', 'H5', 'H6'),
}

# -----------------------------------------------------------------------------
# Standard atom names for DNA and RNA
#
dna_rna_pseudo_atoms = {
  ('T', 'M7'):('H71', 'H72', 'H73'),
}

# -----------------------------------------------------------------------------
#
dna_rna_attached_heavy_atoms = {
  'A': {"H1'":"C1'", "H2'1":"C2'", "H2'2":"C2'", "H2'":"C2'", "H3'":"C3'",
	"H4'":"C4'", "H5'1":"C5'", "H5'2":"C5'",
	'H2':'C2', 'H61':'N6', 'H62':'N6', 'H8':'C8'},
  'C': {"H1'":"C1'", "H2'1":"C2'", "H2'2":"C2'", "H2'":"C2'", "H3'":"C3'",
	"H4'":"C4'", "H5'1":"C5'", "H5'2":"C5'",
	'H41':'N4', 'H42':'N4', 'H5':'C5', 'H6':'C6'},
  'G': {"H1'":"C1'", "H2'1":"C2'", "H2'2":"C2'", "H2'":"C2'", "H3'":"C3'",
	"H4'":"C4'", "H5'1":"C5'", "H5'2":"C5'",
	'H1':'N1', 'H21':'N2', 'H22':'N2', 'H8':'C8'},
  'T': {"H1'":"C1'", "H2'1":"C2'", "H2'2":"C2'", "H3'":"C3'",
	"H4'":"C4'", "H5'1":"C5'", "H5'2":"C5'",
	'H3':'N3', 'H6':'C6', 'H71':'C7', 'H72':'C7', 'H73':'C7', 'M7':'C7'},
  'U': {"H1'":"C1'", "H2'":"C2'", "H3'":"C3'",
	"H4'":"C4'", "H5'1":"C5'", "H5'2":"C5'",
	'H3':'N3', 'H5':'C5', 'H6':'C6'},
}

# -----------------------------------------------------------------------------
#
def merge_table(tfrom, tto):
  for k, tv in tfrom.items():
    if not tto.has_key(k):
      tto[k] = tv
    elif type(tv) == type(()):
      tto[k] = tto[k] + tv
    elif type(tv) == type({}):
      tto[k].update(tv)

# -----------------------------------------------------------------------------
#
def group_atom_table(group_to_atom_list):

  t = {}
  for g in group_to_atom_list.keys():
    for a in group_to_atom_list[g]:
      t[(g,a)] = 1
  return t

# -----------------------------------------------------------------------------
# Setup standard tables that include proteins, dna, and rna names
#
standard_atoms_by_group = {}
merge_table(protein_atoms_by_group, standard_atoms_by_group)
merge_table(dna_rna_atoms_by_group, standard_atoms_by_group)
standard_group_atom_table = group_atom_table(standard_atoms_by_group)

standard_pseudo_atoms = {}
merge_table(protein_pseudo_atoms, standard_pseudo_atoms)
merge_table(dna_rna_pseudo_atoms, standard_pseudo_atoms)

standard_attached_heavy_atoms = {}
merge_table(protein_attached_heavy_atoms, standard_attached_heavy_atoms)
merge_table(dna_rna_attached_heavy_atoms, standard_attached_heavy_atoms)
