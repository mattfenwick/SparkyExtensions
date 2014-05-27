# ----------------------------------------------------------------------------
# Python utility routines and classes
#
import math
import string
import types

# ----------------------------------------------------------------------------
#
def attribute(instance, attr, default):
  if instance and hasattr(instance, attr):
    return getattr(instance, attr)
  return default

# ----------------------------------------------------------------------------
# Make a tuple of values of a specified object attribute.
#
def attribute_values(instances, attr):
  values = []
  for object in instances:
    values.append(getattr(object, attr))
  return tuple(values)

# ----------------------------------------------------------------------------
# Make a tuple of unique values of a specified object attribute.
#
def unique_attribute_values(instances, attr):
  values = {}
  for object in instances:
    values[getattr(object, attr)] = 1
  return values.keys()

# ----------------------------------------------------------------------------
# Return index positions of an element in the sequence.
#
def element_positions(element, seq):

  positions = []
  for i in range(len(seq)):
    e = seq[i]
    if e == element:
      positions.append(i)
  return positions

# ----------------------------------------------------------------------------
# Return first index position of an element in the sequence or None
#
def element_position(element, seq):

  for i in range(len(seq)):
    e = seq[i]
    if e == element:
      return i
  return None

# ----------------------------------------------------------------------------
#
def element_count(element, seq):

  count = 0
  for e in seq:
    if e == element:
      count = count + 1
  return count

# ----------------------------------------------------------------------------
#
def unique_elements(seq):
  t = {}
  for e in tuple(seq):
    t[e] = 1
  return t.keys()

# ----------------------------------------------------------------------------
#
def unused_element(seq, used_seq, default):

  used = {}
  for e in used_seq:
    used[e] = 1
  for e in seq:
    if not used.has_key(e):
      return e
  return default

# ----------------------------------------------------------------------------
#
def append_elements(list, elements):

  for e in elements:
    list.append(e)

# ----------------------------------------------------------------------------
#
def subtract_lists(list1, list2):

  remove = {}
  for e in list2:
    remove[e] = 1

  diff = []
  for e in list1:
    if not remove.has_key(e):
      diff.append(e)

  return diff

# ----------------------------------------------------------------------------
#
def intersect_lists(list1, list2):

  t2 = {}
  for e in list2:
    t2[e] = 1

  inter = []
  for e in list1:
    if t2.has_key(e):
      inter.append(e)

  return inter

# ----------------------------------------------------------------------------
# Append to a table value.
#
def table_push(table, key, value):

  if not table.has_key(key):
    table[key] = []
  table[key].append(value)

# ----------------------------------------------------------------------------
#
def table_map(f, seq):

  t = {}
  for e in seq:
    t[e] = f(e)
  return t

# ----------------------------------------------------------------------------
# Returns None for empty sequence
#
def minimum(seq):
 if seq:
   return min(seq)
 return None

# ----------------------------------------------------------------------------
# Returns None for empty sequence
#
def maximum(seq):
 if seq:
   return max(seq)
 return None

# ----------------------------------------------------------------------------
# Returns None for empty sequence
#
def average(seq):
 if seq:
   sum = reduce(lambda a,b: a+b, seq, 0)
   return float(sum) / len(seq)
 return None
   
# ----------------------------------------------------------------------------
#
def integer_sum(seq):
  sum = 0
  for s in tuple(seq):
    if type(s) == types.IntType:
      sum = sum + s
  return sum

# ----------------------------------------------------------------------------
#
def filter_out_element(seq, element):
  filtered = []
  for e in tuple(seq):
    if e != element:
      filtered.append(e)
  return filtered

# ----------------------------------------------------------------------------
#
def shift_point(p, delta):
  return (p[0] + delta[0], p[1] + delta[1])
def shift_rectangle(r, delta):
  return (r[0] + delta[0], r[1] + delta[1], r[2] + delta[0], r[3] + delta[1])
def rectangle_center(r):
  return (.5 * (r[0] + r[2]), .5 * (r[1] + r[3]))
def rectangle_width(r):
  return r[2] - r[0]
def rectangle_height(r):
  return r[3] - r[1]

# ----------------------------------------------------------------------------
#
def chain_length(chain):

  length = 0
  for k in range(1, len(chain)):
    length = length + distance(chain[k-1], chain[k])
  return length

# ----------------------------------------------------------------------------
#
def scale_tuple(p, factor):
  fp = []
  for e in p:
    fp.append(factor * e)
  return tuple(fp)

# ----------------------------------------------------------------------------
#
def add_tuples(p1, p2):
  sum = []
  for k in range(len(p1)):
    sum.append(p1[k] + p2[k])
  return tuple(sum)

# ----------------------------------------------------------------------------
#
def subtract_tuples(p1, p2):
  diff = []
  for k in range(len(p1)):
    diff.append(p1[k] - p2[k])
  return tuple(diff)

# ----------------------------------------------------------------------------
#
def add_tuple_multiple(p1, f, p2):
  sum = []
  for k in range(len(p1)):
    sum.append(p1[k] + f * p2[k])
  return tuple(sum)

# ----------------------------------------------------------------------------
#
def tuple_near_zero(p, tol):
  for c in p:
    if abs(c) > tol:
      return 0
  return 1

# ----------------------------------------------------------------------------
#
def distance(p1, p2):
  d2 = 0
  for k in range(len(p1)):
    s = p1[k] - p2[k]
    d2 = d2 + s * s
  return math.sqrt(d2)

# ----------------------------------------------------------------------------
#
def length(p):
  d2 = 0
  for k in range(len(p)):
    s = p[k]
    d2 = d2 + s * s
  return math.sqrt(d2)

# ----------------------------------------------------------------------------
#
def interpolate(p1, p2, frac):
  f1 = 1 - frac
  f2 = frac
  p = []
  for k in range(len(p1)):
    p.append(f1 * p1[k] + f2 * p2[k])
  return tuple(p)

# -----------------------------------------------------------------------------
#
def map_interval(x, from_range, to_range):

  f = float(x - from_range[0]) / (from_range[1] - from_range[0])
  return to_range[0] + f * (to_range[1] - to_range[0])

# -----------------------------------------------------------------------------
#
def bound_value(x, min, max):

  if x < min:
    return min
  elif x > max:
    return max
  return x

# ----------------------------------------------------------------------------
#
def nearest_multiple(x, step):

  return step * round(x / step)

# -----------------------------------------------------------------------------
# 
def concatenate_strings(strings, separator):

  r = ''
  for string in strings:
    r = r + string + separator
  return r[:-len(separator)]

# -----------------------------------------------------------------------------
# 
def string_contains_word(s, words):

  for word in words:
    if string.find(s, word) >= 0:
      return 1
  return 0

# -----------------------------------------------------------------------------
# Find the string in a list of strings containing the longest substring of s.
# If there is a tie, return the first in the list with longest substring.
#
def closest_string(s, strings):

  for size in range(len(s), 1, -1):
    for start in range(0, len(s)-size+1):
      for t in strings:
        if string.find(t, s[start:start+size]) >= 0:
          return t

  if strings:
    return strings[0]

  return None

# -----------------------------------------------------------------------------
# 
def sequence_string(seq, format):
  string = ''
  for e in seq:
    string = string + format % e
  return string

# -----------------------------------------------------------------------------
# 
def seq_product(seq1, seq2):
  seq = []
  for k in range(len(seq1)):
    seq.append(seq1[k] * seq2[k])
  return tuple(seq)

# -----------------------------------------------------------------------------
# 
def plural_ending(count):
  if count == 1:
    return ''
  return 's'

# -----------------------------------------------------------------------------
# 
def number_string(format, value):
  if value != None:
    return format % value
  return ''

# -----------------------------------------------------------------------------
# 
def string_to_float(s, default = None):
  try:
    value = string.atof(s)
  except ValueError:
    value = default
  return value

# -----------------------------------------------------------------------------
# 
def string_to_int(s, default = None):
  try:
    value = string.atoi(s)
  except ValueError:
    value = default
  return value

# -----------------------------------------------------------------------------
# 
def pad_field(string, size):

  format = '%%%ds' % size
  return format % string

# -----------------------------------------------------------------------------
# 
def integers_to_ranges(ints):

  sorted_ints = list(ints)
  sorted_ints.sort()
  return int_ranges(sorted_ints)

# -----------------------------------------------------------------------------
#
def int_ranges(ints):

  if ints:
    e = 0
    while e < len(ints)-1 and ints[e+1] == ints[e]+1:
      e = e + 1
    if e >= 2:
      return str(ints[0]) + '-' + str(ints[e]) + ' ' + int_ranges(ints[e+1:])
    else:
      return str(ints[0]) + ' ' + int_ranges(ints[1:])

  return ''

# -----------------------------------------------------------------------------
#
def ranges_to_integers(ranges):

  nums = []
  for r in string.split(ranges):
    ab = string.split(r, '-')
    if len(ab) == 2:
      nums = nums + range(string.atoi(ab[0]), string.atoi(ab[1])+1)
    elif len(ab) == 1:
      nums = nums + [string.atoi(ab[0])]
  return nums

# ----------------------------------------------------------------------------
#
def sort(seq):
  copy = list(seq)
  copy.sort()
  return copy

# ----------------------------------------------------------------------------
#
def sort_keys_by_value(table):
  pairs = table.items()
  pairs.sort(lambda v1, v2: cmp(v1[1], v2[1]))
  return map(lambda pair: pair[0], pairs)

# ----------------------------------------------------------------------------
#
def sort_by_function_value(seq, function):
  pairs = map(lambda e, f = function: (e, f(e)), seq)
  pairs.sort(lambda p1, p2: cmp(p1[1], p2[1]))
  return map(lambda pair: pair[0], pairs)

# ----------------------------------------------------------------------------
#
def component_comparer(index):
  return lambda v1, v2, index = index: cmp(v1[index], v2[index])

# ----------------------------------------------------------------------------
#
def permute(seq, indices):
  return tuple(map(lambda i, seq = seq: seq[i], indices))

# ----------------------------------------------------------------------------
#
def unpermute(seq, indices):
  p = len(indices) * [None]
  for i in range(len(indices)):
    p[indices[i]] = seq[i]
  return tuple(p)

# ----------------------------------------------------------------------------
# Find a permutation p such that target[k] = source[p[k]] for all k.
#
def order(target, source):

  e2i = {}
  for k in range(len(source)):
    e = source[k]
    table_push(e2i, e, k)

  order = []
  for e in target:
    if not e2i.has_key(e) or len(e2i[e]) == 0:
      return None
    indices = e2i[e]
    order.append(indices[0])
    del indices[0]

  return order

# ----------------------------------------------------------------------------
#
def subsequence(seq, indices):
  return tuple(map(lambda i, seq = seq: seq[i], indices))

# ----------------------------------------------------------------------------
#
def table_values(table, keys):
  return tuple(map(lambda k, table = table: table[k], keys))

# ----------------------------------------------------------------------------
# Take N sequences and form every N-tuple where component k comes from
# sequence k.
#
def product_tuples(component_lists):

  if not component_lists:
    return ((),)

  subtuples = product_tuples(component_lists[1:])
  tuples = []
  for c in component_lists[0]:
    for s in subtuples:
      tuples.append((c,) + s)

  return tuple(tuples)
  
# -----------------------------------------------------------------------------
# Make a new function from a given function and parameters.
# The parameters are filled in as the initial arguments of the function.
#
class precompose:
  def __init__(self, func, *params):
    self.func = func
    self.params = params
  def __call__(self, *args):
    return apply(self.func, self.params + args)

# -----------------------------------------------------------------------------
# Make a new function from a given function and parameters.
# The parameters are filled in as the last arguments of the function.
#
class postcompose:
  def __init__(self, func, *params):
    self.func = func
    self.params = params
  def __call__(self, *args):
    return apply(self.func, args + self.params)

# -----------------------------------------------------------------------------
#
class generic_class:
  pass

# -----------------------------------------------------------------------------
# Efficient clustering of objects and locating nearby objects by position
# in n dimensions.
#
class cluster:

  def __init__(self, range):

    self.bin_size = range
    self.bins = {}

  # ---------------------------------------------------------------------------
  #
  def add_point(self, p, object):

    bin = self.bin(p)
    if not self.bins.has_key(bin):
      self.bins[bin] = []
    self.bins[bin].append((p, object))

  # ---------------------------------------------------------------------------
  #
  def has_nearby_point(self, p):

    bin = self.bin(p)
    if self.bins.has_key(bin):
      return 1

    for bin in self.neighbor_bins(bin):
      if self.bins.has_key(bin):
        bin_items = self.bins[bin]
        for bp, bo in bin_items:
          if self.close(p, bp):
            return 1

    return 0

  # ---------------------------------------------------------------------------
  #
  def nearby_objects(self, p):

    nearby = []
    bin = self.bin(p)
    for bin in self.neighbor_bins(bin):
      if self.bins.has_key(bin):
        bin_items = self.bins[bin]
        for bp, bo in bin_items:
          if self.close(p, bp):
            nearby.append(bo)

    return nearby

  # ---------------------------------------------------------------------------
  #
  def clusters(self):
    
    clusters = {}
    for bin_items in self.bins.values():
      for p, object in bin_items: 
        clusters[object] = [object]

    #
    # Merge the clusters for each pair of close objects.
    # The pairs of close objects are found by scanning the bins.
    # A point in a bin is distance checked with all points in
    # forward neighbor bins.
    #
    for bin, bin_items in self.bins.items():
      nearby_items = []
      for n in self.forward_neighbor_bins(bin):
        if self.bins.has_key(n):
          nearby_items = nearby_items + self.bins[n]
      for p1, object1 in bin_items:
        for p2, object2 in nearby_items:
          if (p2 != p1 and
              clusters[object2] != clusters[object1] and
              self.close(p1, p2)):
            c = clusters[object1] + clusters[object2]
            for object in c:
              clusters[object] = c
              # Ick, n^3 in cluster size

    clist = []
    for object, cluster in clusters.items():
      if cluster[0] == object:
        clist.append(cluster)

    return clist

  # ---------------------------------------------------------------------------
  #
  def bin(self, p):

    b = []
    for k in range(len(p)):
      b.append(int(round(p[k] / self.bin_size[k])))
    return tuple(b)

  # ---------------------------------------------------------------------------
  #
  def neighbor_bins(self, bin):

    if len(bin) == 0:
      return ((),)

    b = bin[0]
    neighbors = []
    for n in self.neighbor_bins(bin[1:]):
      neighbors.append((b-1,) + n)
      neighbors.append((b,) + n)
      neighbors.append((b+1,) + n)

    return tuple(neighbors)

  # ---------------------------------------------------------------------------
  #
  def forward_neighbor_bins(self, bin):

    if len(bin) == 0:
      return ((),)

    b = bin[0]
    neighbors = []
    for n in self.neighbor_bins(bin[1:]):
      neighbors.append((b,) + n)
      neighbors.append((b+1,) + n)

    return tuple(neighbors)

  # ---------------------------------------------------------------------------
  #
  def close(self, p1, p2):

    for k in range(len(self.bin_size)):
      if abs(p1[k] - p2[k]) >= self.bin_size[k]:
        return 0
    return 1
