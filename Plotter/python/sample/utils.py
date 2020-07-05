# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import re
from TauFW.common.tools.utils import isnumber, islist, ensurelist, unwraplistargs
from TauFW.common.tools.file import ensuredir, ensureTFile
from TauFW.common.tools.log import Logger, color
from TauFW.Plotter.plot.Variable import Variable, ensurevar
import TauFW.Plotter.plot.CMSStyle as CMSStyle
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gDirectory, gROOT, TH1, THStack, TGraphErrors, TGraphAsymmErrors, Double,\
                 kSolid, kDashed, kDotted, kBlack, kWhite
gROOT.SetBatch(True)
LOG = Logger('Sample')


def unwrap_MergedSamples_args(*args,**kwargs):
  """Help function to unwrap arguments for MergedSamples."""
  from TauFW.Plotter.sample.Sample import Sample
  strings = [ ]
  name    = "noname"
  title   = "No title"
  samples = [ ]
  #args    = unwraplistargs(args)
  for arg in args:
    if isinstance(arg,str):
      strings.append(arg)
    elif isinstance(arg,Sample):
      samples.append(arg)
    elif islist(arg) and all(isinstance(s,Sample) for s in arg):
      for sample in arg:
        samples.append(sample)
  if len(strings)==1:
    name, title = strings[0], strings[0]
  elif len(strings)>1:
    name, title = strings[:2]
  elif len(samples)>1:
    name, title = '-'.join([s.name for s in samples]), ', '.join([s.title for s in samples])
  LOG.verb("unwrap_MergedSamples_args: name=%r, title=%r, samples=%s"%(name,title,samples),level=3)
  return name, title, samples
  

def unwrap_gethist_args(*args,**kwargs):
  """Help function to unwrap argument list that contain variable(s) and selection:
     - variable, cuts
     - varlist, cuts
     where variable can be
     - xvar, nxbins, xmin, xmax (str, int, float, float)
     - xvar, xbins (str, list)
     - var (Variable)
     or valist is a list of such variables.
  """
  vars   = None  # list of Variable objects
  sel    = None  # selection (string)
  single = False # only one Variable passed
  if len(args)==2:
    vars   = args[0]
    sel    = args[1]
    if isinstance(vars,Variable):
      vars   = [vars]
      single = True
    elif islist(args[0]):
      vars = [ensurevar(v) for v in args[0]]
  elif len(args) in [3,5]:
    vars   = [Variable(*args[len(args)-1])]
    sel    = args[-1]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  LOG.verb("unwrap_gethist_args: vars=%s, sel=%r, single=%r"%(vars,sel,single),level=3)
  return vars, sel, single
  

def unwrap_gethist_args_2D(*args,**kwargs):
  """Help function to unwrap argument list that contain variable(s) and selection:
     - xvar, yvar, cuts
     - xvarlist, yvarlist, cuts
     - (xvar,yvar), cuts
     - varlist, cuts
     - xvar, nxbins, xmin, xmax, yvar, nybins, ymin, ymax, cuts
     where xvar and yvar are Variable objects or arguments, and [xy]varlist is a list of such pairs.
  """
  vars   = None  # list of Variable objects
  sel    = None  # selection (string)
  single = False # only one pair of Variable objects passed
  if len(args)==2:
    vars, sel = args
    single = len(vars)==2 and islist(vars) and isinstance(vars[0],Variable) and isinstance(vars[1],Variable)
    if single:
      vars = [vars]
  elif len(args)==3:
    xvars, yvars, sel = args
    if isinstance(xvars,Variable) and isinstance(yvars,Variable):
      vars = [(xvars,yvars)]
      single = True
    elif all(isinstance(v,Variable) for v in xvars+yvars):
      vars = zip(xvars,yvars)
    elif len(xvars) in [3,5] and len(yvars) in [3,5]:
      vars = [Variable(*xvars),Variable(*yvars)]
      single = True
  elif len(args)==9:
    vars   = [Variable(*args[0:4]),Variable(*args[4:8])]
    sel    = args[-1]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args_2D: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  LOG.verb("unwrap_gethist_args_2D: vars=%s, sel=%r, single=%r"%(vars,sel,single),level=3)
  return vars, sel, single
  
