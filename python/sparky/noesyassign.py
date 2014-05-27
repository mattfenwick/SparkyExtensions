# -----------------------------------------------------------------------------
# Present possible noesy assignments in tables and diagrams.
#
import math
import Tkinter
import types

import noesy
import pyutil
import sparky
import sputil
import tkutil

ranges = (('intra',0,0), ('seq',1,1), ('med',2,4), ('long',5,1000000))
range_names = map(lambda r: r[0], ranges)

# -----------------------------------------------------------------------------
#
class noesy_assign_dialog(tkutil.Dialog, tkutil.Stoppable):

  def __init__(self, session):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Possible Noesy Assignments')

    sc = sputil.spectrum_menu(session, self.top, 'Spectrum: ')
    sc.frame.pack(side = 'top', anchor = 'w')
    self.spectrum_choice = sc
    sc.add_callback(self.spectrum_cb)

    er = tkutil.entry_row(self.top, 'PPM tolerance: ',
		       ('w1', '.01', 4), ('w2', '.01', 4), ('w3', '.01', 4))
    self.ppm_range = er.variables
    self.w3_range_widget = er.entries[2].frame
    er.frame.pack(side = 'top', anchor = 'w')

    self.spectrum_cb(self.spectrum_choice.get())

    t = tkutil.scrolling_text(self.top, height = 32, width = 60)
    t.frame.pack(side = 'top', anchor = 'nw', fill = 'both', expand = 1)
    t.text['wrap'] = 'none'
    self.text = t.text

    progress_label = Tkinter.Label(self.top, anchor = 'nw')
    progress_label.pack(side = 'top', anchor = 'nw')

    br = tkutil.button_row(self.top,
			   ('Update', self.update_cb),
                           ('Diagram', self.diagram_cb),
			   ('Stop', self.stop_cb),
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'NoesyAssign')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    tkutil.Stoppable.__init__(self, progress_label, br.buttons[2])

  # ---------------------------------------------------------------------------
  #
  def spectrum_cb(self, name):

    spectrum = sputil.name_to_spectrum(name, self.session)
    if spectrum == None:
      return

    if spectrum.dimension == 3:
      self.w3_range_widget.pack(side = 'left', anchor = 'w')
      self.line_format = '%20s %5s %7s %s'
    else:
      self.w3_range_widget.pack_forget()
      self.line_format = '%15s %5s %7s %s'

    default_ppm_range = {'1H':.02, '13C':.2, '15N':.2}
    for a in range(spectrum.dimension):
      nucleus = spectrum.nuclei[a]
      if default_ppm_range.has_key(nucleus):
        ppm_range = default_ppm_range[nucleus]
      else:
        ppm_range = .02
      self.ppm_range[a].set('%.2f' % ppm_range)

  # ---------------------------------------------------------------------------
  #
  def update_cb(self):

    spectrum = self.spectrum_choice.spectrum()
    if spectrum == None:
      return
    self.resonances = spectrum.condition.resonance_list()
    
    dim = spectrum.dimension
    ppm_range = tkutil.float_variable_values(self.ppm_range)[:dim]

    self.stoppable_call(self.tabulate_assignments, spectrum, ppm_range)
    self.show_report(spectrum, self.assignments_by_range, self.peaks_by_range,
                     self.categorized_peaks)

  # ---------------------------------------------------------------------------
  #
  def diagram_cb(self):

    num_range = sequence_range(self.resonances)
    d = assignment_circle_dialog(self.session, num_range)
    d.show_window(1)

    palist4 = self.peak_assignments(('4+-shortest', 'long'))
    palist3 = self.peak_assignments(('3-shortest', 'long'))
    palist2 = self.peak_assignments(('2-shortest', 'long'))
    palist1 = self.peak_assignments(('unique', 'long'))

    #
    # Add some code to eliminate isolated assignments
    #

    d.draw_assignments(palist4, 'blue')
    d.draw_assignments(palist3, 'green')
    d.draw_assignments(palist2, 'yellow')
    d.draw_assignments(palist1, 'red')

  # ---------------------------------------------------------------------------
  #
  def peak_assignments(self, category):

    if self.categorized_peaks.has_key(category):
      plist = self.categorized_peaks[category]
    else:
      plist = []

    palist = []
    for peak in plist:
      alist = self.possible_assignments[peak]
      for a in alist:
        palist.append((peak, a))

    return palist

  # ---------------------------------------------------------------------------
  #
  def show_report(self, spectrum, assignments_by_range, peaks_by_range,
                  categorized_peaks):

    self.text.delete('0.0', 'end')
    heading = ('Possible %s assignments.\n' % spectrum.name +
               'Click on any peak count to see a list of peaks.\n\n')
    self.text.insert('end', heading)

    self.show_assignment_count_table(categorized_peaks)
    self.show_assignment_range_table(assignments_by_range)
    self.show_shortest_range_table(peaks_by_range)
    self.show_unique_assignment_table(categorized_peaks)
    self.show_multiple_assignment_table(categorized_peaks)

  # ---------------------------------------------------------------------------
  #
  def show_assignment_count_table(self, categorized_peaks):

    ptext = 'Peak counts with 0, 1, 2, ... possible assignments.\n\n'
    self.text.insert('end', ptext)

    ctable = {}
    for category, plist in categorized_peaks.items():
      if type(category) == types.IntType:
        ctable[category] = 1
    counts = ctable.keys()
    counts.sort()

    cline = ''
    for c in counts:
      cline = cline + ('%4d' % c)
    self.text.insert('end', cline + '\n')

    for c in counts:
      field = ('%4d' % len(categorized_peaks[c]))
      tag = 'count%d' % c
      self.text.insert('end', field, tag)
      cb = pyutil.postcompose(self.show_category_cb, c)
      self.text.tag_bind(tag, '<ButtonPress-1>', cb)
    self.text.insert('end', '\n\n')

  # ---------------------------------------------------------------------------
  #
  def show_assignment_range_table(self, assignments_by_range):

    rtext = ('Counts of possible assignments by range.\n\n')
    rline = ''
    cline = ''
    for r in range_names:
      rline = rline + ('%6s' % r)
      cline = cline + ('%6d' % assignments_by_range[r])
    self.text.insert('end', rtext + rline + '\n' + cline + '\n\n')

  # ---------------------------------------------------------------------------
  #
  def show_shortest_range_table(self, peaks_by_range):

    ctext = 'Counts of peaks by shortest range assignment.\n\n'
    self.text.insert('end', ctext)
    
    rline = ''
    for r in range_names:
      rline = rline + ('%6s' % r)
    self.text.insert('end', rline + '\n')
      
    cline = ''
    for range_name in range_names:
      if peaks_by_range.has_key(range_name):
        count = len(peaks_by_range[range_name])
        tag = range_name + '-peaks'
        self.text.insert('end', '%6d' % count, tag)
        cb = pyutil.postcompose(self.show_range_cb, range_name)
        self.text.tag_bind(tag, '<ButtonPress-1>', cb)
      else:
        self.text.insert('end', '%6s' % '')
    self.text.insert('end', '\n\n')

  # ---------------------------------------------------------------------------
  #
  def show_unique_assignment_table(self, categorized_peaks):

    ctext = 'Peaks with one possible assignment.\n\n'
    self.text.insert('end', ctext)
    
    rline = ''
    for r in range_names:
      rline = rline + ('%6s' % r)
    self.text.insert('end', rline + '\n')
      
    cline = ''
    for range_name in range_names:
      category = ('unique', range_name)
      if categorized_peaks.has_key(category):
        count = len(categorized_peaks[category])
        tag = 'unique-' + range_name
        self.text.insert('end', '%6d' % count, tag)
        cb = pyutil.postcompose(self.show_category_cb, category)
        self.text.tag_bind(tag, '<ButtonPress-1>', cb)
      else:
        self.text.insert('end', '%6s' % '')
    self.text.insert('end', '\n\n')

  # ---------------------------------------------------------------------------
  #
  def show_multiple_assignment_table(self, categorized_peaks):

    ctext = ('The table below shows peak counts for peaks with more\n' +
             'than one possible assignment.  These are categorized\n' +
             'according to the shortest range assignment possible,\n' +
             'intra residue, sequential, medium (2-4 residues), or\n' +
             'long (5 or more residues apart).  The first line shows\n' +
             'peaks having exactly one possible assignment of shortest\n' +
             'range with additional longer range possiblities.  The next\n' +
             'line shows peak counts with 2 possible assignments of\n' +
             'shortest range, ...\n\n')
    self.text.insert('end', ctext)
    
    rline = '%10s' % ''
    for r in range_names:
      rline = rline + ('%6s' % r)
    self.text.insert('end', rline + '\n')
      
    for range in ('1', '2', '3', '4+'):
      self.text.insert('end', '%-10s' % range)
      pline = ''
      uniqueness = range + '-shortest'
      for shortest_range in range_names:
        category = (uniqueness, shortest_range)
        if categorized_peaks.has_key(category):
          count = len(categorized_peaks[category])
          tag = uniqueness + '-' + shortest_range
          self.text.insert('end', '%6d' % count, tag)
          cb = pyutil.postcompose(self.show_category_cb, category)
          self.text.tag_bind(tag, '<ButtonPress-1>', cb)
        else:
          self.text.insert('end', '%6s' % '')
      self.text.insert('end', '\n')
    
  # ---------------------------------------------------------------------------
  #
  def show_category_cb(self, event, category):

    self.session.show_peak_list(self.categorized_peaks[category])
    
  # ---------------------------------------------------------------------------
  #
  def show_range_cb(self, event, range):

    self.session.show_peak_list(self.peaks_by_range[range])
    
  # ---------------------------------------------------------------------------
  #
  def tabulate_assignments(self, spectrum, ppm_range):

    self.assignments_by_range = {}              # assignment counts
    for r in range_names:
      self.assignments_by_range[r] = 0

    self.possible_assignments = {}
    self.categorized_peaks = {}
    self.peaks_by_range = {}
    self.stoppable_loop('peaks', 10)
    for peak in spectrum.peak_list():
      self.check_for_stop()
      alist = noesy.nearby_noesy_assignments(spectrum, peak.position,
                                             ppm_range)
      self.possible_assignments[peak] = alist
      pyutil.table_push(self.categorized_peaks, len(alist), peak)
      range_counts, total = self.assignment_range_counts(alist)
      for r, count in range_counts.items():
        self.assignments_by_range[r] = self.assignments_by_range[r] + count
      if total > 0:
        category = self.peak_category(range_counts, total)
        pyutil.table_push(self.categorized_peaks, category, peak)
        pyutil.table_push(self.peaks_by_range, category[1], peak)
          
  # ---------------------------------------------------------------------------
  #
  def peak_category(self, range_counts, total):

    for shortest_range in range_names:
      if range_counts[shortest_range] > 0:
        break
    if total == 1:
      uniqueness = 'unique'
    else:
      shortest_count = range_counts[shortest_range]
      if shortest_count <= 3:
        uniqueness = '%d-shortest' % shortest_count
      else:
        uniqueness = '4+-shortest'
    category = (uniqueness, shortest_range)
    return category
  
  # ---------------------------------------------------------------------------
  #
  def assignment_range_counts(self, assignment_list):

    range_counts = {}
    for r in range_names:
      range_counts[r] = 0
      
    total = 0
    for assignment in assignment_list:
      range = sputil.assignment_range(assignment)
      if range != None:
        for r, low, high in ranges:
          if range >= low and range <= high:
            range_counts[r] = range_counts[r] + 1
        total = total + 1
    return range_counts, total
  
# -----------------------------------------------------------------------------
#
class assignment_circle_dialog(tkutil.Dialog):

  def __init__(self, session, num_range):

    self.session = session
    
    tkutil.Dialog.__init__(self, session.tk, 'Noesy Assignment Diagram')

    c = Tkinter.Canvas(self.top, width = 700, height = 700)
    c.pack(fill = 'both', expand = 1)
    self.canvas = c

    br = tkutil.button_row(self.top,
                           ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'NoesyAssign')),
			   )
    br.frame.pack(side = 'top', anchor = 'w')

    self.draw_circle(num_range)
    
  # ---------------------------------------------------------------------------
  #
  def draw_circle(self, num_range):

    pad = 50
    radius = 300
    dot_radius = 2
    label_step = 10
    tick_length = 10
    tick_gap = 3
    
    min_n, max_n = num_range
    max_angle = (2 - .1) * math.pi                    # Don't close circle
    angle_step = max_angle / (max_n - min_n + 1)

    self.position = {}
    center = (radius + pad, radius + pad)
    for n in range(min_n, max_n + 1):
      angle = (n - min_n) * angle_step
      dir = (math.sin(angle), -math.cos(angle))
      offset = pyutil.scale_tuple(dir, radius)
      c = pyutil.add_tuples(center, offset)
      self.position[n] = c
      self.canvas.create_oval(c[0] - dot_radius, c[1] - dot_radius,
                              c[0] + dot_radius, c[1] + dot_radius,
                              fill = 'black')
      if n % label_step == 0:
        offset1 = pyutil.scale_tuple(dir, dot_radius + tick_gap)
        offset2 = pyutil.scale_tuple(dir, dot_radius + tick_gap + tick_length)
        offset3 = pyutil.scale_tuple(dir, dot_radius + 2*tick_gap +tick_length)
        b = pyutil.add_tuples(c, offset1)
        e = pyutil.add_tuples(c, offset2)
        self.canvas.create_line(b[0], b[1], e[0], e[1])
        lbl = pyutil.add_tuples(c, offset3)
        anchor = direction_anchor(-dir[0], dir[1])
        self.canvas.create_text(lbl[0], lbl[1], text = '%d' %n,
                                anchor = anchor)
    
  # ---------------------------------------------------------------------------
  #
  def draw_assignments(self, peak_assignments, color):

    lines = {}
    for peak, assignment in peak_assignments:
      nums = []
      for r in assignment:
        if r.atom.nucleus == '1H':
          nums.append(r.group.number)
      if len(nums) == 2:
        pyutil.table_push(lines, tuple(nums), peak)

    for (num1, num2), peaks in lines.items():
      b = self.position[num1]
      e = self.position[num2]
      id = self.canvas.create_line(b[0], b[1], e[0], e[1],
                                   width = len(peaks), fill = color)
      cb = pyutil.postcompose(self.show_peaks_cb, peaks)
      self.canvas.tag_bind(id, '<ButtonPress-1>', cb)
    
  # ---------------------------------------------------------------------------
  #
  def show_peaks_cb(self, event, peaks):

    self.session.show_peak_list(peaks)

# -----------------------------------------------------------------------------
#
def sequence_range(resonances):

  rtable = {}
  for r in resonances:
    rtable[r] = 1
  rlist = rtable.keys()

  ntable = {}
  for r in rlist:
    num = r.group.number
    if num != None and num > 0:
      ntable[num] = 1
  numlist = ntable.keys()
  numlist.sort()

  if numlist:
    return numlist[0], numlist[-1]

  return None

# -----------------------------------------------------------------------------
#
def direction_anchor(x, y):

  angle = 180 * math.atan2(x, y) / math.pi
  
  a = angle + 22.5
  if a < 0:
    a = a + 360
  i = int(a / 45.0)
  
  dnames = ('n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw')
  
  return dnames[i]
  
# -----------------------------------------------------------------------------
#
def show_dialog(session):
  sputil.the_dialog(noesy_assign_dialog,session).show_window(1)
