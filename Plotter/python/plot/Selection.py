# -*- coding: utf-8 -*-
import re
from copy import copy, deepcopy
from ROOT import TH1D, TH2D
from TauFW.Plotter.plot.Context import getcontext
from TauFW.Plotter.plot.utils import LOG, isnumber, islist, ensurelist, unwraplistargs


class Selection(object):
  """
  Selection class to:
    - hold all relevant information of a selection that will be used to make plots:
        selection pattern, filename friendly name, LaTeX friendly title, ...
    - easy string conversions: filename, LaTeX, ...
    - analysis-specific operations: relaxing cuts, inverting cuts, applying variations, ...
  Initialize as
    Selection()
    Selection(str selection)
    Selection(str name, str selection)
    Selection(str name, str title, str selection)
  """
  
  def __init__(self, *args, **kwargs):
    self.name          = ""
    self.title         = ""
    self.selection     = ""
    self.weight        = ""
    if len(args)==1:
      if isinstance(args[0],Selection):
        self.name      = args[0].name
        self.title     = args[0].title
        self.selection = args[0].selection
      else:
        self.name      = args[0]
        self.title     = args[0]
        self.selection = args[0]
    elif len(args)==2:
      self.name        = args[0]
      self.title       = args[0]
      self.selection   = getselstr(args[1])
    elif len(args)==3:
      self.name        = args[0]
      self.title       = args[1]
      self.selection   = getselstr(args[2])
    elif len(args)>=4:
      self.name        = args[0]
      self.title       = args[1]
      self.selection   = getselstr(args[2])
      self.weight      = args[3]
    self.title         = kwargs.get('title',    maketitle(self.title) )
    self.filename      = makefilename(self.name)
    self.filename      = kwargs.get('fname',    self.filename )
    self.filename      = kwargs.get('filename', self.filename ) # name for files, histograms
    self.weight        = kwargs.get('weight',   self.weight   )
    #if self.selection=="":
    #   LOG.warning('Selection::Selection - No selection string given for %r!'%(self.name))
    self.context       = getcontext(kwargs,self.selection) # context-dependent channel selections
    self.only          = kwargs.get('only',       [ ]     )
    self.veto          = kwargs.get('veto',       [ ]     )
    self.only          = ensurelist(self.only)
    self.veto          = ensurelist(self.veto)
  
  @property
  def cut(self): return self.selection
  @cut.setter
  def cut(self,val): self.selection = val
  
  def __str__(self):
    """Returns string representation of Selection object."""
    return self.name
  
  def __repr__(self):
    """Returns string representation of Selection object."""
    return "<%s(%r,%r) at %s>"%(self.__class__.__name__,self.name,self.selection,hex(id(self)))
  
  def __iter__(self):
    """Start iteration over selection information."""
    for i in [self.name,self.selection]:
      yield i
  
  def __add__(self, selection2):
    """Add selections by combining their selection string (can be string or Selection object)."""
    if isinstance(selection2,str):
      selection2 = Selection(selection2,selection2) # make selection object
    return self.combine(selection2)
  
  def __mul__(self, weight):
    """Multiply selection with some weight (that can be string or Selection object)."""
    result = None
    weight = joinweights(self.weight,weight)
    if isinstance(weight,str):
      result = Selection("%s (%s)"(self.name,weight),joincuts(self.selection,weight=weight))
    else:
      result = Selection("%s (%s)"(self.name,weight.title),joincuts(self.selection,weight=weight))
    return result
  
  def contains(self, string, **kwargs):
    """Return if selection string contains given substring."""
    return string in self.selections
  
  def replace(self, old, new, **kwargs):
    """Replace given substring in selection string."""
    if kwargs.get('regex',False):
      self.selection = self.selection.replace(old,new)
    else:
      self.selection = re.sub(old,new,self.selection)
    return self.selection
  
  def changecontext(self,*args):
    """Change the contextual selections for a set of arguments, if it is available"""
    if self.context:
      self.selections = self.context.getContext(*args)
  
  def drawcmd(self,*args,**kwargs):
    """Construct string for TTree::Draw method."""
    if self.weight:
      if self.selection:
        return "(%s)*%s"%(self.selection,self.weight)
      else:
        return self.weight
    return self.selection
  
  def plotfor(self,variable,**kwargs):
    """Check is variable is vetoed for this variable."""
    verbosity = LOG.getverbosity(kwargs)
    if not isinstance(variable,str):
      variable = variable.name
    for searchterm in self.veto:
      if re.search(searchterm,variable):
        LOG.verb("Variable.plotFor: Regex match of variable %r to %r"%(variable,searchterm),verbosity,level=2)
        return False
    for searchterm in self.only:
      if re.search(searchterm,variable):
        LOG.verb("Variable.plotFor: Regex match of variable %r to %r"%(variable,searchterm),verbosity,level=2)
        return True
    return len(self.only)==0
  
  def combine(self, *selections):
    # TODO: check if selection2 is a string, if possible
    selections = [self]+list(selections)
    name       = ", ".join([s.name     for s in selections if s.name    ])
    title      = ", ".join([s.title    for s in selections if s.title   ])
    filename   = "_".join( [s.filename for s in selections if s.filename])
    cuts       = joincuts(*[s.cut for s in selections])
    sum        = Selection(name,cuts,title=title,filename=filename)
    return sum
  
  ###def invertIsolation(self,**kwargs):
  ###  """Find, invert and replace isolation selections."""
  ###  name      = "%s_relaxed_iso"%(self.name)
  ###  title     = "%s (relaxed iso)"%(self.title)
  ###  filename  = "%s_relaxed_iso"%(self.filename)
  ###  selection = invertIsolation(self.selection,**kwargs)
  ###  return Selection(name,selection,title=title,filename=self.filename)
  
  ###def relaxJetSelections(self,**kwargs):
  ###  """Find, relax and replace jet selections."""
  ###  name      = "%s_relaxed_jets"%(self.name)
  ###  title     = "%s (relaxed jet selections)"%(self.title)
  ###  filename  = "%s_relaxed_jets"%(self.filename)
  ###  selection = relaxJetSelection(self.selection,**kwargs)
  ###  return Selection(name,selection,title=title,filename=self.filename)
  
  def latex(self):
    return makelatex(self.name)
  
  def shift(self,vshift,vars,**kwargs):
    """Shift all given variable in selections string,
    and create new Selection object, e.g.
      sel = Selection('ptcut','jpt_1_jecUp>50 && met_jecUp<50')
      sel.shift('jecUp',['jpt_[12]','met']) -> 'jpt_1_jecUp>50 && met_jecUp<50'
    """
    if kwargs.get('us',True) and len(vshift)>0 and vshift[0]!='_':
      vshift = '_'+vshift
    oldstr = self.selection # old selection string
    newstr = shift(oldstr,vshift,vars,**kwargs) # shift variables in string
    newsel = deepcopy(self) # create new object
    newsel.selection = newstr # overwrite selection string
    if kwargs.get('keepfile',False) and self.selection!=newstr:
      newsel.filename += vshift # overwrite filename
    return newsel
  
  def shiftjme(self,jshift,jmevars=None,**kwargs):
    """Shift all jet variable in selection string (e.g. to propagate JEC/JER),
    and create new Selection object, e.g.
      sel = Selection('ptcut','jpt_1_jecUp>50 && met_jecUp<50')
      sel.shiftjme('jecUp') -> 'jpt_1_jecUp>50 && met_jecUp<50'
    """
    if kwargs.get('us',True) and len(jshift)>0 and jshift[0]!='_':
      jshift = '_'+jshift
    oldstr = self.selection # old selection string
    newstr = shiftjme(oldstr,jshift,jmevars,**kwargs) # shift variables in string
    newsel = deepcopy(self) # create new object
    newsel.selection = newstr # overwrite selection string
    if kwargs.get('keepfile',False) and self.selection!=newstr:
      newsel.filename += jshift # overwrite filename
    return newsel
  
  def match(self, *terms, **kwargs):
    """Match search terms to the selection's name, title and selection strings."""
    return match(terms,[self.name,self.title,self.selection])
  
Sel = Selection # short alias
from TauFW.Plotter.plot.string import *