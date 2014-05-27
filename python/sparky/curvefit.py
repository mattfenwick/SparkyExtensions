# -----------------------------------------------------------------------------
# Fit data set of xy pairs to a specified parameterized function,
# for example,
#
#       y = A exp(-Bx)
#
# and display graph of fit.
#
import math
import random
import Tkinter

import pyutil
import sputil
import tkutil

# -----------------------------------------------------------------------------
# Method uses a local linear approximation for fit function to do a least
# squares fit to take one step, the iterates until converged.
#
# Convergence means the fit error (sum of squares of residuals) change
# during a step is less than a certain fraction of the total fit error.
#
class least_squares_fit:

  def __init__(self, xy_pairs, fit_function, params, tolerance):

    self.max_steps = 100
    self.max_cuts = 20
    self.min_fit_error = 1e-6
    
    self.xy_pairs = xy_pairs
    self.fit_function = fit_function
    self.params = params
    self.tolerance = tolerance

    self.fit_error = self.calculate_error(self.params)
    self.error_step = -self.fit_error
    self.step_count = 0
    self.converged = self.find_fit()
    self.point_sd = math.sqrt(self.fit_error / len(xy_pairs))
    
  # ---------------------------------------------------------------------------
  #
  def find_fit(self):

    while (self.fit_error > self.min_fit_error and
           -self.error_step > self.tolerance * self.fit_error and
           self.step_count < self.max_steps and
           self.take_step()):
      self.step_count = self.step_count + 1

    converged = (self.fit_error <= self.min_fit_error or
                 -self.error_step <= self.tolerance * self.fit_error)
    return converged
    
  # ---------------------------------------------------------------------------
  #
  def take_step(self):

    step = self.linear_step()
    if step == None:
      return 0

    cut_count = 0
    while cut_count < self.max_cuts and not self.try_step(step):
      step = pyutil.scale_tuple(step, .5)
      cut_count = cut_count + 1
    if cut_count == self.max_cuts:
      return 0

    return 1

  # ---------------------------------------------------------------------------
  #
  def try_step(self, step):

    new_params = pyutil.add_tuples(self.params, step)
    new_error = self.calculate_error(new_params)
    
    good_step = (new_error < self.fit_error)
    if good_step:
      self.params = new_params
      self.error_step = new_error - self.fit_error
      self.fit_error = new_error

    return good_step

  # ---------------------------------------------------------------------------
  # Find step solving least squares problem with linearized fit function.
  #
  def linear_step(self):

    n = self.fit_function.parameter_count()
    A = zero_matrix(n)
    b = n * [0]
    
    for x, y in self.xy_pairs:
      y_fit = self.fit_function.value(self.params, x)
      g = self.fit_function.parameter_derivatives(self.params, x)
      e = y_fit - y
      for j in range(n):
        Aj = A[j]
        gj = g[j]
        for k in range(n):
          Aj[k] = Aj[k] + gj * g[k]
        b[j] = b[j] - e * gj

    step = solve_positive_system(A, b)

    return step

  # ---------------------------------------------------------------------------
  #
  def calculate_error(self, params):

    esum = 0
    for x, y in self.xy_pairs:
      y_fit = self.fit_function.value(params, x)
      e = y_fit - y
      esum = esum + e * e
    return esum
    
  # ---------------------------------------------------------------------------
  # Add Gaussian distributed errors to y values of xy pairs and fit.
  # Do this multiple times and compute standard deviations for the resulting
  # fit parameters.
  #
  def estimate_parameter_error(self, y_sd, trials):

    trial_params = []
    n = self.fit_function.parameter_count()
    param_sd = n * [0]

    if self.converged:

      while len(trial_params) < trials:
        new_xy_pairs = []
        for x, y in self.xy_pairs:
          new_y = y + random.gauss(0, y_sd)
          new_xy_pairs.append((x, new_y))
        fit = least_squares_fit(new_xy_pairs, self.fit_function,
                                self.params, self.tolerance)
        if fit.converged:
          trial_params.append(fit.params)

      sum_d2 = n * [0]
      for params in trial_params:
        diff = pyutil.subtract_tuples(params, self.params)
        diff2 = map(lambda d: d*d, diff)
        sum_d2 = pyutil.add_tuples(sum_d2, diff2)
      param_sd = map(lambda d, m=trials: math.sqrt(d/m), sum_d2)

    self.trial_params = trial_params
    self.param_sd = param_sd
  
# -----------------------------------------------------------------------------
# Solve positive definite system of linear equations Ax = b.
# The matrix A is modified.
#
def solve_positive_system(A, b):

  if not LLt_decompose(A):
    return None
  return back_solve(A, b)

# -----------------------------------------------------------------------------
# Decompose positive definite matrix A as L * L-transpose where L is lower
# triangular.  The lower triangular part of A contains the result.
#
def LLt_decompose(A):

  n = len(A)
  for k in range(n):
    Ak = A[k]
    Akk = Ak[k]
    if Akk <= 0:
      return 0                  # matrix A is not positive definite
    sqrt_Akk = math.sqrt(Akk)
    for j in range(k, n):
      Ak[j] = Ak[j] / sqrt_Akk
    for i in range(k+1, n):
      Ai = A[i]
      Aki = Ak[i]
      for j in range(i, n):
        Ai[j] = Ai[j] - Aki * Ak[j]
  return 1
  
# -----------------------------------------------------------------------------
# Back solve the system L * L-transpose * x = b where L is lower triangular.
# Only the lower triangular part of the passed in matrix L is used.
#
def back_solve(L, b):

  n = len(b)

  # First solve Lc = b
  c = n * [0]
  for k in range(0, n):
    t = b[k]
    for j in range(0, k):
      t = t - L[j][k] * c[j]
    c[k] = t / L[k][k]

  # Now solve L-transpose * x = c
  x = n * [0]
  for k in range(n-1, -1, -1):
    t = c[k]
    for j in range(k+1, n):
      t = t - L[k][j] * x[j]
    x[k] = t / L[k][k]

  return x

# -----------------------------------------------------------------------------
#
def zero_matrix(n):

  A = []
  for k in range(n):
    A.append(n * [0])
  return A

# -----------------------------------------------------------------------------
#
class fit_display(tkutil.Dialog):

  def __init__(self, session):
    
    tkutil.Dialog.__init__(self, session.tk, 'Fit Plot')

    self.top.rowconfigure(1, weight = 1)
    self.top.columnconfigure(0, weight = 1)

    h = Tkinter.Label(self.top)
    h.grid(row = 0, column = 0, sticky = 'w')
    self.heading = h

    c = Tkinter.Canvas(self.top)
    c.grid(row = 1, column = 0, sticky = 'news')
    self.canvas = c
    
    br = tkutil.button_row(self.top,
			   ('Close', self.close_cb),
                           ('Help', sputil.help_cb(session, 'RelaxFit')),
			   )
    br.frame.grid(row = 2, sticky = 'w')

    self.show_window(1)
    
  # ---------------------------------------------------------------------------
  #
  def plot_fit(self, heading, fit, callback = None):

    self.heading['text'] = heading

    x_range, y_range = self.xy_ranges(fit.xy_pairs)

    c = self.canvas
    c.delete('all')
    c.update_idletasks()   # Make sure geometry has been calculated
    w = c.winfo_width()
    h = c.winfo_height()
    r = 5

    if w > 1:
      points = []
      f = fit.fit_function
      for px in range(w):
        x = pyutil.map_interval(px, (0,w), x_range)
        y = f.value(fit.params, x)
        py = pyutil.map_interval(y, y_range, (h,0))
        points.append((px,py))
      points = tuple(points)
      apply(c.create_line, points)

    for k in range(len(fit.xy_pairs)):
      x, y = fit.xy_pairs[k]
      px = pyutil.map_interval(x, x_range, (0,w))
      py = pyutil.map_interval(y, y_range, (h,0))
      id = c.create_oval(px-r, py-r, px+r, py+r, fill = 'black')
      if callback:
        cb = lambda event, fit=fit, k=k, callback=callback: callback(fit, k)
        c.tag_bind(id, '<ButtonPress>', cb)

    c.update_idletasks()
    
  # ---------------------------------------------------------------------------
  #
  def xy_ranges(self, xy_pairs):

    border_padding = .1
    xvalues = tuple(map(lambda xy: xy[0], xy_pairs))
    xrange = self.interval(xvalues, border_padding)
    yvalues = tuple(map(lambda xy: xy[1], xy_pairs))
    yrange = self.interval(yvalues, border_padding)

    return (xrange, yrange)
    
  # ---------------------------------------------------------------------------
  #
  def interval(self, values, padding):
  
    xmin = apply(min, values)
    xmax = apply(max, values)
    if xmax > xmin:
      border = padding * (xmax - xmin)
    elif xmin != 0:
      border = abs(xmin)
    else:
      border = 1

    return (xmin - border, xmax + border)
  
# -----------------------------------------------------------------------------
#
class A_plus_Bx_function:

  def parameter_count(self):
    return 2
  def value(self, params, x):
    a, b = params
    return a + b * x
  def parameter_derivatives(self, params, x):
    a, b = params
    return (1, x)
  
# -----------------------------------------------------------------------------
#
def xy_test_data(f, params, xvalues, sd):

  xy_pairs = []
  for x in xvalues:
    y = f.value(params, x)
    y = y + random.gauss(0, sd)
    xy_pairs.append((x, y))
  return xy_pairs
  
# -----------------------------------------------------------------------------
#
def test_fit():

  d = fit_display()

  trials = 10
  error_trials = 10
  f = A_plus_Bx_function()
  params = (100, -50)
  xvalues = range(1, 10)
  sd = 5
  tolerance = 1e-6
  start_params = (1, 0)

  print 'Steps    SD       Fit parameters (value, sd)'
  for k in range(trials):
    xy_pairs = xy_test_data(f, params, xvalues, sd)
    fit = least_squares_fit(xy_pairs, f, start_params, tolerance)
    d.plot_fit('Test fit %d' % k, fit)

    fit.estimate_parameter_error(sd, error_trials)

    line = ''
    if not fit.converged:
      line = line + '*'
    line = line + ('%4d %7.3g ' % (fit.step_count, fit.point_sd))
    for k in range(len(params)):
      line = line + '%7.3g %-7.3g ' % (fit.params[k], fit.param_sd[k])
    print line
  
# -----------------------------------------------------------------------------
#
#test_fit()
  
# -----------------------------------------------------------------------------
#
def show_fit(session, heading, fit, callback = None):
  d = sputil.the_dialog(fit_display, session)
  d.show_window(1)
  d.plot_fit(heading, fit, callback)
