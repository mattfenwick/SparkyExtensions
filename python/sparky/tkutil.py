# ----------------------------------------------------------------------------
# Tk utility classes and routines
#
import math
import os
import pyutil
import string
import Tkinter
import tkFileDialog

# ----------------------------------------------------------------------------
#
class file_choices:

  def __init__(self, parent, title, file_type):

    self.path_list = []
    self.title = title
    self.file_type = file_type
    self.frame = Tkinter.Frame(parent)

    slist = scrolling_list(self.frame, title, 3)
    self.listbox = slist.listbox
    slist.frame.pack(side = 'top', anchor = 'w', fill = 'x', expand = 1)

    br = button_row(self.frame,
		    ('Add file', self.add_path_cb),
                    ('Remove file', self.remove_path_cb),
		    )
    br.frame.pack(side = 'top', anchor = 'w')

  # --------------------------------------------------------------------------
  #
  def add_path_cb(self):

    path = load_file(self.listbox, self.title, self.file_type)
    if path and not path in self.path_list:
      self.path_list.append(path)
      self.listbox.insert('end', path)

  # --------------------------------------------------------------------------
  #
  def remove_path_cb(self):

    indices = map(string.atoi, self.listbox.curselection())
    indices.sort()
    indices.reverse()
    for i in indices:
      del self.path_list[i]
      self.listbox.delete(i)

  # --------------------------------------------------------------------------
  #
  def set_paths(self, path_list):

    self.listbox.delete('0', 'end')
    for path in path_list:
      self.listbox.insert('end', path)
    self.path_list = path_list
    
# ----------------------------------------------------------------------------
# Make a list box with a label heading and vertical scrollbar.
# The list keeps track of data associated with each line.
#
class scrolling_list:

  def __init__(self, parent, heading, height):

    self.line_data = []

    f = Tkinter.Frame(parent)
    f.rowconfigure(1, weight = 1)
    f.columnconfigure(0, weight = 1)
    self.frame = f

    h = Tkinter.Label(f, text = heading, font = 'Courier 12',
		      anchor = 'w', justify = 'left')
    h.grid(row = 0, column = 0, sticky = 'w')
    self.heading = h

    list = Tkinter.Listbox(f, height = height, font = 'Courier 12')
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
  def set_focus_cb(self, event):
    self.listbox.focus_set()

  # --------------------------------------------------------------------------
  #
  def save_cb(self):

    path = save_file(self.listbox, 'Save List', 'save_list')
    self.write_file(path, 'w')

  # --------------------------------------------------------------------------
  #
  def append_cb(self):

    path = load_file(self.listbox, 'Append List to File', 'save_list')
    self.write_file(path, 'a+')

  # --------------------------------------------------------------------------
  #
  def write_file(self, path, mode, write_heading = 1):
    
    if path:
      file = open(path, mode)
      if write_heading and self.heading:
	file.write(self.heading['text'] + '\n')
      lines = self.listbox.get(0, 'end')
      for line in lines:
	file.write(line + '\n')
      file.close()
    
# ----------------------------------------------------------------------------
#
def listbox_select_cb(event):
  listbox = event.widget
  listbox.select_clear(0, 'end')
  line = listbox.nearest(event.y)
  if line >= 0:
    listbox.select_set(line)

# ----------------------------------------------------------------------------
#
def selected_listbox_line(listbox):
  selected_lines = listbox.curselection()  # List of string line numbers. Yuck
  if len(selected_lines) == 1:
    return string.atoi(selected_lines[0])
  return None

# ----------------------------------------------------------------------------
# Create a Tk label and entry fields in a frame
#
class entry_row:

  def __init__(self, parent, title, *entries):

    f = Tkinter.Frame(parent)
    self.frame = f
    label = Tkinter.Label(f, text = title)
    label.pack(side = 'left')
    elist = []
    vlist = []
    for name, initial, width in entries:
      e = entry_field(f, name, initial, width)
      elist.append(e)
      vlist.append(e.variable)
      e.frame.pack(side = 'left')
    self.entries = tuple(elist)
    self.variables = tuple(vlist)

# ----------------------------------------------------------------------------
# Return tuple of float values from sequence of tcl variables.
#
def float_variable_values(variables):
  values = []
  for v in variables:
    values.append(string.atof(v.get()))
  return tuple(values)

# ----------------------------------------------------------------------------
# Return tuple of integer values from sequence of tcl variables.
#
def integer_variable_values(variables):
  values = []
  for v in variables:
    values.append(string.atoi(v.get()))
  return tuple(values)

# ----------------------------------------------------------------------------
#
def variable_set_callback(widget, variable, callback):
  python_cb = pyutil.precompose(variable_set_cb, variable, callback)
  tcl_cb_name = widget._register(python_cb)
  variable._tk.call('trace', 'variable', str(variable), 'w', tcl_cb_name)

# ----------------------------------------------------------------------------
#
def variable_set_cb(variable, callback, *args):
  callback(variable.get())

# ----------------------------------------------------------------------------
#
class checkbutton:

  def __init__(self, parent, text, onoff):

    v = Tkinter.BooleanVar(parent)
    self.variable = v
    v.set(onoff)

    b = Tkinter.Checkbutton(parent, highlightthickness = 0,
#			  selectcolor = 'black',
                            text = text, variable = v)
    self.button = b

  # ---------------------------------------------------------------------------
  #
  def state(self):
    return self.variable.get()
  def set_state(self, onoff):
    self.variable.set(onoff)
    
  # ---------------------------------------------------------------------------
  #
  def add_callback(self, cb):

    variable_set_callback(self.button, self.variable, cb)

  # ---------------------------------------------------------------------------
  #
  def map_widget(self, popup):

    self.add_callback(pyutil.precompose(self.show_widget_cb, popup))
    
  # ---------------------------------------------------------------------------
  #
  def show_widget_cb(self, w, show):

    if show:
      w.pack(side = 'top', anchor = 'w', fill = 'x', after = self.button)
    else:
      w.pack_forget()

# ----------------------------------------------------------------------------
# Create a Tk label and checkbuttons in a frame
#
class checkbuttons:

  def __init__(self, parent, stackside, title, *buttons):

    f = Tkinter.Frame(parent)
    self.frame = f

    if title:
      label = Tkinter.Label(f, text = title)
      label.pack(side = stackside)

    vlist = []
    for name in buttons:
      cb = checkbutton(f, name, 1)
      cb.button.pack(side = stackside, anchor = 'nw')
      vlist.append(cb.variable)
    self.variables = vlist

# ----------------------------------------------------------------------------
#
class menu:

  def __init__(self, parent, title, *entries):

    self.button = Tkinter.Menubutton(parent, text = title)
    self.pane = Tkinter.Menu(self.button)
    self.button['menu'] = self.pane
    for name, callback in entries:
      self.pane.add_command(label = name, command = callback)

  # --------------------------------------------------------------------------
  #
  def add_button(self, name, cb):

    self.pane.add_command(label = name, command = cb)

  # --------------------------------------------------------------------------
  #
  def rename_button(self, index, name):

    self.pane.entryconfigure(index, label = name)

  # --------------------------------------------------------------------------
  #
  def add_checkbutton(self, name, color, cb):

    v = Tkinter.BooleanVar(master = self.button)
    self.pane.add('checkbutton', label = name, selectcolor = color,
                  variable = v)
    variable_set_callback(self.button, v, cb)
    return v

  # --------------------------------------------------------------------------
  #
  def add_separator(self):

    self.pane.add('separator')

  # --------------------------------------------------------------------------
  #
  def last_index(self):

    return self.pane.index('end')
  
# ----------------------------------------------------------------------------
# Create a Tk label and option menu in a frame.
#
class option_menu:

  def __init__(self, parent, title, choices, initial = None):

    self.frame = Tkinter.Frame(parent)
    label = Tkinter.Label(self.frame, text = title)
    label.pack(side = 'left')
    self.label = label

    self.variable = Tkinter.StringVar(parent)
    mb = Tkinter.Menubutton(self.frame, textvariable = self.variable,
                            indicatoron = 1, borderwidth = 2,
                            relief = 'raised',
                            highlightthickness = 2, anchor = 'c')
    mb.pack(side = 'left')
    self.menu = Tkinter.Menu(mb, tearoff = 0)
    mb['menu'] = self.menu
    for choice in choices:
      self.add_entry(choice)

    if initial == None:
      if choices:
        self.variable.set(choices[0])
    else:
      self.variable.set(initial)

  # --------------------------------------------------------------------------
  #
  def get(self): return self.variable.get()
  def set(self, value): self.variable.set(value)

  # --------------------------------------------------------------------------
  #
  def add_callback(self, cb):
    variable_set_callback(self.frame, self.variable, cb)

  # --------------------------------------------------------------------------
  #
  def add_entry(self, name):
    set_variable_cb = pyutil.precompose(self.variable.set, name)
    self.menu.add_command(label = name, command = set_variable_cb)

  # --------------------------------------------------------------------------
  #
  def remove_all_entries(self):
    self.menu.delete(0, 'end')

# ----------------------------------------------------------------------------
# Create a Tk label and entry widget in a frame.
# Return a tuple containing the frame and the text variable that
# holds the value of the entry widget.
#
class entry_field:

  def __init__(self, parent, title, initial = '', width = 10, trailer = None):

    f = Tkinter.Frame(parent)
    self.frame = f

    if title:
      label = Tkinter.Label(f, text = title)
      label.pack(side = 'left')
      self.label = label

    v = Tkinter.StringVar(parent)
    v.set(initial)
    self.variable = v
    entry = Tkinter.Entry(f, textvariable = v, width = width)
    entry.pack(side = 'left')
    self.entry = entry

    if trailer:
      t = Tkinter.Label(f, text = trailer)
      t.pack(side = 'left')
      self.trailer = t

  # ---------------------------------------------------------------------------
  #
  def show_end(self):

    end = self.entry.index('end')
    self.entry.xview(end)

# ----------------------------------------------------------------------------
# Create an entry field for a file path with a browse button to bring up
# a file dialog.
#
class file_field:

  def __init__(self, parent, title, file_type,
               browse_button = 1, save = 0, width = 20):

    self.title = title
    self.file_type = file_type
    self.frame = Tkinter.Frame(parent)
    e = entry_field(self.frame, title, '', width)
    self.entry = e
    self.variable = e.variable
    e.frame.pack(side = 'left')
    if browse_button:
      self.save = save
      b = Tkinter.Button(self.frame, text = "Browse ...",
                         command = self.file_browse_cb)
      b.pack(side = 'left')

  # --------------------------------------------------------------------------
  # Pop up a file browsing dialog and set the variable to the chosen file.
  #
  def file_browse_cb(self):

    if self.save:
      path = save_file(self.frame, self.title, self.file_type)
    else:
      path = load_file(self.frame, self.title, self.file_type)
      
    if path:
      self.variable.set(path)
      self.entry.show_end()      # Position to show file name part

  # --------------------------------------------------------------------------
  #
  def get(self):
    return self.variable.get()
  def set(self, text):
    self.variable.set(text)

# ----------------------------------------------------------------------------
#
class multiple_file_selection:

  def __init__(self, parent, directory):

    f = Tkinter.Frame(parent)
    self.frame = f

    e = entry_field(f, 'Directory ', directory, width = 30)
    e.frame.pack(side = 'top', anchor = 'nw')
    e.entry.bind('<KeyPress-Return>', self.directory_entry_cb)
    self.directory_entry = e

    sl = scrolling_list(f, '', 10)
    sl.frame.pack(side = 'top', anchor = 'nw', fill = 'both', expand = 1)
    sl.listbox.bind('<Double-ButtonRelease-1>', self.directory_click_cb)
    sl.listbox['selectmode'] = 'extended'
    self.list = sl

    self.update_files(directory)

  # ---------------------------------------------------------------------------
  #
  def directory_click_cb(self, event):

    file = self.list.event_line_data(event)
    if file == os.curdir:
      d = self.directory
    elif file == os.pardir:
      d = os.path.split(self.directory)[0]
    else:
      d = os.path.join(self.directory, file)
    self.update_files(d)

  # ---------------------------------------------------------------------------
  #
  def directory_entry_cb(self, event):

    d = self.directory_entry.variable.get()
    self.update_files(d)
    
  # ---------------------------------------------------------------------------
  #
  def update_files(self, directory):

    try:
      files = os.listdir(directory)
    except os.error:
      self.frame.bell()
      return

    self.directory = directory
    self.directory_entry.variable.set(directory)
    self.directory_entry.show_end()

    files.append(os.curdir)
    files.append(os.pardir)
    files.sort()

    self.list.clear()
    for f in files:
      self.list.append(f, f)
    
  # ---------------------------------------------------------------------------
  #
  def selected_paths(self):

    paths = []
    files = self.list.selected_line_data()
    for file in files:
      paths.append(os.path.join(self.directory, file))
    return paths
    
# ----------------------------------------------------------------------------
# Make labels in a grid.  They are specified as triples ('text', row, column).
#
def grid_labels(frame, *labels):

  for p in labels:
    label, r, c = p
    w = Tkinter.Label(frame, text = label)
    w.grid(row = r, column = c)

# ----------------------------------------------------------------------------
# Make entry fields in a grid and string variables to track their values.
# Entries are specified as tuples
#
#   (initial-value, row, column)
#
# A list of string variables is returned.
#
def grid_entries(frame, width, *entries):

  variables = []
  for p in entries:
    value, r, c = p
    v = Tkinter.StringVar(frame)
    v.set(value)
    variables.append(v)
    w = Tkinter.Entry(frame, textvariable = v, width = width)
    w.grid(row = r, column = c)
  return variables

# ----------------------------------------------------------------------------
# Make checkbuttons in a grid and boolean variables to track their values.
# Entries are specified as tuples
#
#   (label, row, column)
#
# A list of boolean variables is returned.
#
def grid_checkbuttons(frame, *entries):

  variables = []
  for text, r, c in entries:
    cb = checkbutton(frame, text, 0)
    variables.append(cb.variable)
    cb.button.grid(row = r, column = c)
  return variables

# ----------------------------------------------------------------------------
# Make a frame containing a row of buttons.
# Each button has a name and a callback.
#
class button_row:

  def __init__(self, parent, *buttons):

    self.frame = Tkinter.Frame(parent)
    self.buttons = []
    for name, cb in buttons:
      b = Tkinter.Button(self.frame, text = name, command = cb)
      b.pack(side = 'left')
      self.buttons.append(b)

# ----------------------------------------------------------------------------
#
class scrolling_text:

  def __init__(self, parent, height = 5, width = 40):

    f = Tkinter.Frame(parent)
    f.rowconfigure(0, weight = 1)
    f.columnconfigure(0, weight = 1)
    self.frame = f

    t = Tkinter.Text(f, height = height, width = width)
    t.grid(row = 0, column = 0, sticky = 'news')
    self.text = t

    yscroll = Tkinter.Scrollbar(f)
    yscroll.grid(row = 0, column = 1, sticky = 'ns')
    yscroll['command'] = t.yview
    t['yscrollcommand'] = yscroll.set

# ----------------------------------------------------------------------------
# Make a canvas in a frame with scrollbars.
#
class scrollable_canvas:
  
  def __init__(self, parent):

    f = Tkinter.Frame(parent)
    f.rowconfigure(0, weight = 1)
    f.columnconfigure(0, weight = 1)
    self.frame = f

    c = Tkinter.Canvas(f, confine = 0)
    c.grid(row = 0, column = 0, sticky = 'news')
    self.canvas = c

    xscroll = Tkinter.Scrollbar(f, orient = 'horizontal')
    xscroll.grid(row = 1, column = 0, sticky = 'ew')
    xscroll['command'] = c.xview
    c['xscrollcommand'] = xscroll.set

    yscroll = Tkinter.Scrollbar(f)
    yscroll.grid(row = 0, column = 1, sticky = 'ns')
    yscroll['command'] = c.yview
    c['yscrollcommand'] = yscroll.set

# ----------------------------------------------------------------------------
# Make a canvas in a frame with scrollbars and a zoom slider.
#
class zoomable_canvas(scrollable_canvas):

  def __init__(self, parent, zoom_cb = None):

    scrollable_canvas.__init__(self, parent)
    
    zscale = Tkinter.Scale(self.frame)
    zscale.grid(row = 0, column = 2, sticky = 'ns')
    zscale['from'] = -1
    zscale['to'] = 1
    zscale['resolution'] = .01
    zscale['showvalue'] = 0
    self.current_zoom_factor = 1
    self.zoom_cb = zoom_cb
    zscale['command'] = self.rescale_canvas_cb
    zscale.set(0)
    self.zscale = zscale

  # --------------------------------------------------------------------------
  #
  def rescale_canvas_cb(self, value):

    value = string.atof(value)
    cur_value = math.log10(self.current_zoom_factor)
    if abs(cur_value - value) > .5 * string.atof(self.zscale['resolution']):
      factor = math.pow(10.0, value) / self.current_zoom_factor
      self.zoom_by_factor(factor, 0)
   
  # ---------------------------------------------------------------------------
  #
  def zoom_by_factor(self, f, set_scale = 1):
      
    cx, cy = canvas_center(self.canvas)
    self.canvas.scale('all', 0, 0, f, f)
    r = canvas_scrollregion(self.canvas)
    if r:
      self.canvas['scrollregion'] = (f * r[0], f * r[1], f * r[2], f * r[3])
      set_canvas_center(self.canvas, f * cx, f * cy)
      self.current_zoom_factor = f * self.current_zoom_factor
      if self.zoom_cb:
        self.zoom_cb(f)
      if set_scale:
        scale_value = math.log10(self.current_zoom_factor)
        self.zscale.set(scale_value)

  # ---------------------------------------------------------------------------
  # The view will not be positioned outside the current scroll region
  #
  def zoom(self, box):

    if box[2] > box[0] and box[3] > box[1]:
      w = self.canvas.winfo_width()
      h = self.canvas.winfo_height()
      f = min(float(w) / (box[2] - box[0]), float(h) / (box[3] - box[1]))
      self.zoom_by_factor(f)
      xc = f * .5 * (box[0] + box[2])
      yc = f * .5 * (box[1] + box[3])
      set_canvas_center(self.canvas, xc, yc)

# ----------------------------------------------------------------------------
#
def canvas_center(canvas):

  w = canvas.winfo_width()
  h = canvas.winfo_height()
  cx = canvas.canvasx(w/2)
  cy = canvas.canvasy(h/2)
  return (cx, cy)

# ----------------------------------------------------------------------------
#
def set_canvas_center(canvas, cx, cy):

  w = canvas.winfo_width()
  h = canvas.winfo_height()
  set_canvas_corner(canvas, cx - w/2, cy - h/2)

# ----------------------------------------------------------------------------
#
def set_canvas_corner(canvas, cx, cy):

  box = canvas_scrollregion(canvas)
  if box:
    x0, y0, x1, y1 = box
    if x1 > x0:
      fx = (cx - x0) / (x1 - x0)
      canvas.xview('moveto', fx)
    if y1 > y0:
      fy = (cy - y0) / (y1 - y0)
      canvas.yview('moveto', fy)

# ----------------------------------------------------------------------------
# Tkinter is doesn't have scrollregion member function
#
def canvas_scrollregion(canvas):

  box_string = canvas['scrollregion']
  return canvas._getdoubles(box_string)
  
# ---------------------------------------------------------------------------
#
def fit_canvas_to_window(canvas, xy):

  box = canvas.bbox('all')

  scale = 1
  if box:
    (x0, y0, x1, y1) = box

    canvas.update_idletasks()   # Make sure geometry has been calculated
    if xy == 'x':
      new_size = x1 - x0
      old_size = canvas.winfo_width()
    else:
      new_size = y1 - y0
      old_size = canvas.winfo_height()

    if new_size > 0:
      border_frac = .1
      border = .1 * new_size
      scale = old_size / (new_size  + 2 * border)
      canvas.scale('all', 0, 0, scale, scale)
      canvas['scrollregion'] = (scale * (x0 - border), scale * (y0 - border),
                                scale * (x1 + border), scale * (y1 + border))
      canvas.xview('moveto', 0)
      canvas.yview('moveto', 0)

  return scale

# -----------------------------------------------------------------------------
#
def canvas_coordinates(canvas, event):
  return (canvas.canvasx(event.x), canvas.canvasy(event.y))

# -----------------------------------------------------------------------------
# This does not cause the scrollbar command to be invoked.
#
def set_scrollbar(sbar, v1, v2, r1, r2):

  rwidth = float(r2 - r1)
  if rwidth == 0:
    f1 = 0
    f2 = 1
  else:
    f1 = (v1 - r1) / rwidth 
    f2 = (v2 - r1) / rwidth
  sbar.set(f1, f2)

# -----------------------------------------------------------------------------
# When a scrollbar is moved by the user the command callback is invoked.
# This routine adjusts the scrollbar slider for page up/down, step up/down
# and drag.
#
def adjust_scrollbar(scrollbar, cmd, steps_per_page = 100):

  if cmd[0] == 'moveto':
    f1, f2 = scrollbar.get()
    new_f1 = string.atof(cmd[1])
    new_f2 = new_f1 + f2 - f1
    if new_f1 >= 0 and new_f2 < 1:	# Don't scroll beyond edge
      scrollbar.set(new_f1, new_f2)
  elif cmd[0] == 'scroll':
    f1, f2 = scrollbar.get()
    if cmd[2] == 'units':
      delta = (f2 - f1) * string.atof(cmd[1]) / steps_per_page
    elif cmd[2] == 'pages':
      delta = (f2 - f1) * string.atof(cmd[1])
    if f1 + delta < 0:
      delta = -f1
    elif f2 + delta > 1:
      delta = 1 - f2
    scrollbar.set(f1 + delta, f2 + delta)

# ---------------------------------------------------------------------------
# Print the part of the canvas displayed on the screen to a file.
# It looks like the Tk Canvas postscript command doesn't support multipage
# output.
#
def postscript_cb(canvas):

  path = save_file(canvas, 'Save Postscript', 'save_postscript')
  if path:
    canvas.postscript(file = path)

# ----------------------------------------------------------------------------
#
def save_file(parent, title, cache_name):

  initial_dir, initial_file = initial_file_dialog_path(cache_name)    
  path = tkFileDialog.asksaveasfilename(
    parent = parent,
#
# The -parent option causes the file dialog to crash if the previously
# used parent window has been destroyed.  This is a bug in Tk 8.0p1.
# It appears to be fixed in Tk 8.0.4.
#    
    title = title,
    initialdir = initial_dir,
    initialfile = initial_file)
  remember_file_dialog_path(path, cache_name)
  return path

# ----------------------------------------------------------------------------
#
def load_file(parent, title, cache_name):

  initial_dir, initial_file = initial_file_dialog_path(cache_name)
  path = tkFileDialog.askopenfilename(
    parent = parent,
#
# The -parent option causes the file dialog to crash if the previously
# used parent window has been destroyed.  This is a bug in Tk 8.0p1.
# It appears to be fixed in Tk 8.0.4.
#    
    title = title,
    initialdir = initial_dir,
    initialfile = initial_file)
  remember_file_dialog_path(path, cache_name)
  return path

# ----------------------------------------------------------------------------
#
file_dialog_paths = {}

def initial_file_dialog_path(cache_name):
  if file_dialog_paths.has_key(cache_name):
    path = file_dialog_paths[cache_name]
    return os.path.split(path)
  return (os.getcwd(), '')

def remember_file_dialog_path(path, cache_name):
  if path:
    file_dialog_paths[cache_name] = path

# ----------------------------------------------------------------------------
# Map or unmap a top level window.
#
def map_widget(w, show):
  if show:
    w.deiconify()
    w.tkraise()
  else:
    w.withdraw()

# ----------------------------------------------------------------------------
# Used with Tk widgets not wrapped by Tkinter (eg. View frames)
#
def raise_named_widget(tk, name):
  tk_call(tk, 'wm', 'deiconify', name)
  tk_call(tk, 'raise', name)

# ----------------------------------------------------------------------------
# Return the size of a text string in pixels.  Tkinter should provide this
# but doesn't.
#
def text_size(text, widget):
  return widget.getint(widget.tk.call('font', 'measure', widget['font'], text))

# -----------------------------------------------------------------------------
# Create the top level Tk window
#
def initialize_tk(argv):

  program_name = argv[0]
  program_class = string.capitalize(program_name)
  display = parse_display_arg(argv)
  
  tk = Tkinter.Tk(display, program_name, program_class)
  tk.withdraw()
  
  return tk

# -----------------------------------------------------------------------------
# Parse -display option from command line arguments and eliminate it from
# the argv list.
#
def parse_display_arg(argv):

  display = None
  a = 1
  while a+1 < len(argv):
    if argv[a] == '-display':
      display = argv[a+1]
      del argv[a]
      del argv[a]
    else:
      a = a + 1

  return display

# -----------------------------------------------------------------------------
# Execute a tcl command
#
def tk_call(widget, *args):

  apply(widget.tk.call, args)

# -----------------------------------------------------------------------------
# Register an idle callback.
# This routine is to allow idle callbacks to reregister themselves while
# allowing other events to be processed.  Because Tk wants to finish all
# idle tasks before going back to processing normal events, idle callbacks
# that continuously reregister themselves prevent ever returning to normal
# event processing.  The work around is to set a 0 second timer that then
# registers the idle callback.
#
def after_idle(widget, command):

  widget.after(0, lambda w = widget, cmd = command: w.after_idle(cmd))

# -----------------------------------------------------------------------------
# Set a timer callback every few seconds until a predicate returns true.
# Then call the callback function.
#
def call_me_when(widget, callback, predicate):

  ms_delay = 5000
  def check(widget, predicate, callback):
    if predicate():
      callback()
    else:
      call_me_when(widget, callback, predicate)
  cb = pyutil.precompose(check, widget, predicate, callback)
  widget.after(ms_delay, cb)
  
# -----------------------------------------------------------------------------
#
class Dialog:

  def __init__(self, tk, title):
    top = Tkinter.Toplevel(tk)
    top.withdraw()              # need to call show_window() to show it.
    top.title(title)
    top.bind('<Destroy>', self.dialog_destroyed_cb, 1)
    self.top = top
    self.dialog_destroyed = 0
    
  # ---------------------------------------------------------------------------
  #
  def show_window(self, showme):
    map_widget(self.top, showme)

  # ---------------------------------------------------------------------------
  #
  def is_window_destroyed(self):
    return self.dialog_destroyed

  # ---------------------------------------------------------------------------
  #
  def ok_cb(self):
    self.apply_cb()
    self.close_cb()

  # ---------------------------------------------------------------------------
  #
  def apply_cb(self):
    pass

  # ---------------------------------------------------------------------------
  #
  def close_cb(self):
    if hasattr(self, 'setting_dialogs'):
      for settings_dialog in self.setting_dialogs:
        settings_dialog.close_cb()
    map_widget(self.top, 0)

  # ---------------------------------------------------------------------------
  #
  def dialog_destroyed_cb(self, event):

    if str(event.widget) == str(self.top):
      self.dialog_destroyed = 1
      if hasattr(self, 'setting_dialogs'):
        for settings_dialog in self.setting_dialogs:
          settings_dialog.parent_destroyed()
      
  # ---------------------------------------------------------------------------
  # Shows the window making it application modal.
  # Returns only when dialog is closed.
  # 
  def return_when_closed(self):
    self.show_window(1)
    self.top.grab_set()
    self.top.bind('<Unmap>', self.modal_unmapped_cb)
    self.top.bind('<ButtonPress>', self.raise_modal_cb)
    self.top.mainloop()
    self.top.unbind('<ButtonPress>')
    self.top.unbind('<Unmap>')
    self.top.grab_release()
    
  # ---------------------------------------------------------------------------
  #
  def modal_unmapped_cb(self, event):
    self.top.quit()
    
  # ---------------------------------------------------------------------------
  #
  def raise_modal_cb(self, event):
    map_widget(self.top, 1)

  
# -----------------------------------------------------------------------------
# A settings dialog is used to set parameters for a parent dialog.
# For example a peak list dialog has a settings dialog to choose the
# fields to display in the list.  It is closed when the parent is closed
# or destroyed.  It is reparentable so the same settings dialog can serve
# several parent instances.
#
class Settings_Dialog(Dialog):

  def __init__(self, tk, title):

    self.parent_dialog = None
    self.new_settings_cb = None

    Dialog.__init__(self, tk, title)

  # ---------------------------------------------------------------------------
  #
  def set_parent_dialog(self, parent_dialog, settings, new_settings_cb):

    if self.parent_dialog:
      self.parent_dialog.setting_dialogs.remove(self)

    self.parent_dialog = parent_dialog

    if not hasattr(parent_dialog, 'setting_dialogs'):
      parent_dialog.setting_dialogs = []
    parent_dialog.setting_dialogs.append(self)

    self.new_settings_cb = new_settings_cb
    self.show_settings(settings)

  # ---------------------------------------------------------------------------
  #
  def parent_destroyed(self):

    self.parent_dialog = None
    self.new_settings_cb = None
    if not self.is_window_destroyed():
      self.close_cb()
    
  # ---------------------------------------------------------------------------
  #
  def apply_cb(self):

    if self.new_settings_cb:
      settings = self.get_settings()
      self.new_settings_cb(settings)

  # ---------------------------------------------------------------------------
  #
  def show_settings(self, settings):
    pass

  # ---------------------------------------------------------------------------
  #
  def get_settings(self):
    return None

# -----------------------------------------------------------------------------
#
class StopRequest(Exception):
  pass

# -----------------------------------------------------------------------------
#
class Stoppable:

  # ---------------------------------------------------------------------------
  #
  def __init__(self, progress_label, stop_button):
    self.stop_button = stop_button
    self.stoppable_progress_label = progress_label
    self.stoppable_enabled = 0
    self.stoppable_title = ''
    self.stoppable_step = 1
    self.stoppable_count = 0
    self.disallow_stop()

  # ---------------------------------------------------------------------------
  #
  def stoppable_call(self, func, *args):
    self.allow_stop()
    try:
      result = apply(func, args)
    except StopRequest:
      result = None
    self.disallow_stop()
    return result

  # ---------------------------------------------------------------------------
  #
  def stoppable_loop(self, title, step):
    self.stoppable_title = title
    self.stoppable_step = step
    self.stoppable_count = 0

  # ---------------------------------------------------------------------------
  #
  def check_for_stop(self):
    self.stoppable_count = self.stoppable_count + 1
    if self.stoppable_count % self.stoppable_step == 0:
      self.progress_report('%d %s' %
                           (self.stoppable_count, self.stoppable_title))

  # ---------------------------------------------------------------------------
  #
  def progress_report(self, message):
    self.stoppable_progress_label['text'] = message
    self.stoppable_progress_label.update()
    if self.stoppable_enabled:
      if self.stop_requested:
	raise StopRequest

  # ---------------------------------------------------------------------------
  #
  def stop_cb(self):
    self.stop_requested = 1

  # ---------------------------------------------------------------------------
  #
  def allow_stop(self):
    self.stoppable_enabled = 1
    self.stop_requested = 0
    if self.stop_button:
      self.stop_button['state'] = 'normal'

  # ---------------------------------------------------------------------------
  #
  def disallow_stop(self):
    self.stoppable_enabled = 0
    if self.stop_button:
      self.stop_button['state'] = 'disabled'
    self.stoppable_progress_label['text'] = ''

# -----------------------------------------------------------------------------
#
class Not_Stoppable:
  def stoppable_call(self, func, *args): return apply(func, args)
  def stoppable_loop(self, title, step): pass
  def check_for_stop(self): pass
  def progress_report(self, message): pass

# ----------------------------------------------------------------------------
# Sort a sequence by doing the default sort on keys.
#
def sort_by_key(seq, key_function):

  keyed_seq = map(lambda e, key = key_function: (key(e), e), seq)
  keyed_seq.sort()
  return map(lambda pair: pair[1], keyed_seq)

# ----------------------------------------------------------------------------
# Sort a sequence by doing the default sort on keys.
#
def stoppable_sort_by_key(seq, key_function, stoppable):

  def attach_key(e, key_function = key_function, stoppable = stoppable):
    stoppable.check_for_stop()
    return (key_function(e), e)

  stoppable.stoppable_loop('sort keys', 100)
  keyed_seq = map(attach_key, seq)

  def compare(e1, e2, stoppable = stoppable):
    stoppable.check_for_stop()
    return cmp(e1, e2)

  stoppable.stoppable_loop('sorting', 1000)
  keyed_seq.sort(compare)

  return map(lambda pair: pair[1], keyed_seq)
