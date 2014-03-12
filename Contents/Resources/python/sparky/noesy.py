# ----------------------------------------------------------------------------
#
import Tkinter

import atoms
import axes
import pyutil
import sparky
import sputil
import tkutil

# -----------------------------------------------------------------------------
#
def extend_noesy_assignment(spectrum, hres):

  if hres and spectrum.dimension == 3:
    heavy = atoms.attached_heavy_atom(hres[0].atom, spectrum.molecule)
    if heavy == None:
      return None
    aH, aCN, aH2 = noesy_hsqc_axes(spectrum)
    if heavy.nucleus == spectrum.nuclei[aCN]:
      return noesy_hsqc_assignment(spectrum, hres[0].atom, hres[1].atom, heavy)
    else:
      return None

  return hres

# ---------------------------------------------------------------------------
# Find assignments for a given spectrum position where resonances are close.
#
def nearby_noesy_assignments(spectrum, position, ppm_range):

  if is_noesy_hsqc(spectrum):
    nearby_assignments = nearby_noesy_hsqc_assignments
  else:
    nearby_assignments = nearby_noesy_2d_assignments
  return nearby_assignments(spectrum, position, ppm_range)

# ---------------------------------------------------------------------------
# Find assignments for a given spectrum position where resonances are close.
#
def nearby_noesy_2d_assignments(spectrum, position, ppm_range):

  res_lists = nearby_resonances(spectrum, position, ppm_range)
  return pyutil.product_tuples(res_lists)

# ---------------------------------------------------------------------------
# Return resonance list for each spectrum axis of resonances near position.
# The resonances are first aliased onto the spectrum.
#
def nearby_resonances(spectrum, position, ppm_range):

  c = spectrum.condition
  rmin, rmax = spectrum.region
  sweepwidth = spectrum.sweep_width
  res_lists = []
  for a in range(spectrum.dimension):
    middle = position[a]
    r = ppm_range[a]
    ppm_max = middle + r
    ppm_min = middle - r
    nucleus = spectrum.nuclei[a]
    alias_max = rmax[a]
    alias_min = alias_max - sweepwidth[a]
    res_lists.append(c.interval_resonances(ppm_min, ppm_max, nucleus,
                                           alias_min, alias_max))
  return res_lists

# ---------------------------------------------------------------------------
# Find assignments for a given spectrum position where resonances are close
# and atoms are close.  Include assignments where the atom-atom distance
# cannot be determined because of atom name mismatches.
#
def close_noesy_assignments(spectrum, position, ppm_range,
                            models, max_distance):

  if is_noesy_hsqc(spectrum):
    close_assignments = close_noesy_hsqc_assignments
  else:
    close_assignments = close_noesy_2d_assignments
  return close_assignments(spectrum, position, ppm_range, models, max_distance)

# ---------------------------------------------------------------------------
#
def close_noesy_2d_assignments(spectrum, position, ppm_range,
                               models, max_distance):

  alist = nearby_noesy_2d_assignments(spectrum, position, ppm_range)
  clist = []
  for a in alist:
    for model in models:
      d = model.minimum_distance(a[0].atom, a[1].atom, spectrum.molecule)
      if d == None or d <= max_distance:
        clist.append(a)
        break
  return tuple(clist)

# ---------------------------------------------------------------------------
# Find assignments for a given position in a labelled noesy spectrum where
# resonances are close and the heavy atom is attached to the labelled proton.
#
def nearby_noesy_hsqc_assignments(spectrum, position, ppm_range):

  res_lists = nearby_resonances(spectrum, position, ppm_range)

  aH, aCN, aH2 = noesy_hsqc_axes(spectrum)
  rH = res_lists[aH]
  rCN = res_lists[aCN]
  rH2 = res_lists[aH2]

  rHCN = []
  m = spectrum.molecule
  c = spectrum.condition
  for r in rH:
    cnatom = atoms.attached_heavy_atom(r.atom, m)
    if cnatom != None:
      rheavy = c.find_resonance(cnatom)
      if rheavy != None and rheavy in rCN:
	rHCN.append((r, rheavy))

  alist = []
  for rh, rcn in rHCN:
    for rh2 in rH2:
      a = [None, None, None]
      a[aH] = rh
      a[aCN] = rcn
      a[aH2] = rh2
      alist.append(tuple(a))

  return tuple(alist)

# ---------------------------------------------------------------------------
# Find assignments for a given spectrum position where resonances are close
# and atoms are close.
#
def close_noesy_hsqc_assignments(spectrum, position, ppm_range,
                                 models, max_distance):

  alist = nearby_noesy_hsqc_assignments(spectrum, position, ppm_range)
  aH, aCN, aH2 = noesy_hsqc_axes(spectrum)
  clist = []
  for a in alist:
    for model in models:
      d = model.minimum_distance(a[aH].atom, a[aH2].atom, spectrum.molecule)
      if d == None or d <= max_distance:
        clist.append(a)
        break
  return tuple(clist)

# -----------------------------------------------------------------------------
#
def noesy_hsqc_axes(spectrum):
  if not hasattr(spectrum, 'labelled_proton_axis'):
    identify_hsqc_axes(spectrum)
  aH = spectrum.labelled_proton_axis
  aCN = spectrum.heavy_atom_axis
  aH2 = spectrum.unlabelled_proton_axis
  return aH, aCN, aH2

# -----------------------------------------------------------------------------
#
def is_noesy(spectrum):
  return (spectrum and
	  spectrum.dimension == 2 and
	  len(axes.proton_axes(spectrum)) == 2)

# -----------------------------------------------------------------------------
#
def is_noesy_hsqc(spectrum):
  return (spectrum and
	  spectrum.dimension == 3 and
	  len(axes.proton_axes(spectrum)) == 2)

# ----------------------------------------------------------------------------
#
def atom_pairs_to_hsqc_assignments(spectrum, atom_pairs):

  heavy_nucleus = spectrum.nuclei[spectrum.heavy_atom_axis]
  alist = []
  for h, h2 in atom_pairs:
    cn = atoms.attached_heavy_atom(h, spectrum.molecule)
    if cn and cn.nucleus == heavy_nucleus:
      assignment = noesy_hsqc_assignment(spectrum, h, h2, cn)
      if assignment:
	alist.append(assignment)

  return tuple(alist)
				 
# -----------------------------------------------------------------------------
# Return the assignment associated with atoms for a labelled noesy spectrum
#
def noesy_hsqc_assignment(spectrum, labelled_proton,
			  unlabelled_proton, heavy_atom):

  c = spectrum.condition
  aH, aCN, aH2 = noesy_hsqc_axes(spectrum)
  rH = c.find_resonance(labelled_proton)
  rH2 = c.find_resonance(unlabelled_proton)
  rCN = c.find_resonance(heavy_atom)

  if rH == None or rH2 == None or rCN == None:
    return None
  
  res = [None, None, None]
  res[aH] = rH
  res[aH2] = rH2
  res[aCN] = rCN
  
  return tuple(res)

# ---------------------------------------------------------------------------
#
def noesy_hsqc_spectrum(spectrum_list, C13orN15):
  for spectrum in spectrum_list:
    if (spectrum.nuclei == (C13orN15, '1H', '1H') or
	spectrum.nuclei == ('1H', C13orN15, '1H') or
	spectrum.nuclei == ('1H', '1H', C13orN15)):
      return spectrum
  return None

# ----------------------------------------------------------------------------
#
def atom_assignment(condition, atoms):
  res = []
  for atom in atoms:
    r = condition.find_resonance(atom)
    if r == None:
      return None
    res.append(r)
  return tuple(res)

# ----------------------------------------------------------------------------
# query user for labelled proton, or auto-determine labelled proton
#
def identify_hsqc_axes(spectrum):

  mol = spectrum.molecule
  a1, a2 = axes.proton_axes(spectrum)
  aCN = axes.heavy_atom_axes(spectrum)[0]
  for p in spectrum.peak_list():
    if p.is_assigned:
      res = p.resonances()
      h1 = atoms.attached_heavy_atom(res[a1].atom, mol)
      h2 = atoms.attached_heavy_atom(res[a2].atom, mol)
      if h1 and h2 and h1 != h2:
	if h1 == res[aCN].atom:
	  set_noesy_hsqc_axes(spectrum, a1, aCN, a2)
	  return
	elif h2 == res[aCN].atom:
	  set_noesy_hsqc_axes(spectrum, a2, aCN, a1)
	  return

  aH = axes.attached_proton_axis(spectrum, aCN)
  if aH == None:
    aH = 2
  aH2 = axes.second_nucleus_axis(spectrum, '1H', aH)
  set_noesy_hsqc_axes(spectrum, aH, aCN, aH2)

# -----------------------------------------------------------------------------
#
def set_noesy_hsqc_axes(spectrum, aH, aCN, aH2):
  spectrum.labelled_proton_axis = aH
  spectrum.unlabelled_proton_axis = aH2
  spectrum.heavy_atom_axis = aCN

# -----------------------------------------------------------------------------
#
def proton_resonances(peak):

  if peak.is_assigned:
    if is_noesy(peak.spectrum):
      return peak.resonances()
    elif is_noesy_hsqc(peak.spectrum):
      aH, aCN, aH2 = noesy_hsqc_axes(peak.spectrum)
      res = peak.resonances()
      return (res[aH], res[aH2])
  return None
