# -*- coding: utf-8 -*-
import re
from copy import copy, deepcopy
from ROOT import TH1D, TH2D
from TauFW.Plotter.plot.string import joinweights, invertcharge
from TauFW.Plotter.plot.Context import getcontext
from TauFW.Plotter.plot.utils import LOG, isnumber, islist, ensurelist


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
    Selection(str name, str title, str selection, str weight)
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
      else: # str selection
        self.name      = args[0]
        self.title     = args[0]
        self.selection = args[0]
    elif len(args)==2: # str name, str selection
      self.name        = args[0]
      self.title       = args[0]
      self.selection   = getselstr(args[1])
    elif len(args)==3: # str name, str title, str selection
      self.name        = args[0]
      self.title       = args[1]
      self.selection   = getselstr(args[2])
    elif len(args)>=4: # str name, str title, str selection, str weight
      self.name        = args[0]
      self.title       = args[1]
      self.selection   = getselstr(args[2])
      self.weight      = args[3]
    self.title         = kwargs.get('title', maketitle(self.title) )
    self.filename      = makefilename(self.name) # ensure filename-safe name
    self.selection     = kwargs.get('selection',self.selection ) # selection string, e.g. "q_1*q_2<0 && pt_1>20 && pt_2>20"
    self.contextstr    = kwargs.get('context',  self.selection ) # context string for Variable.context
    self.filename      = kwargs.get('fname',    self.filename  ) # alias
    self.filename      = kwargs.get('filename', self.filename  ) # name for files, histograms
    self.weight        = kwargs.get('weight',   self.weight    )
    #if self.selection=="":
    #   LOG.warn('Selection::Selection - No selection string given for %r!'%(self.name))
    self.context       = getcontext(kwargs,self.selection) # context-dependent channel selections
    self.only          = kwargs.get('only',     [ ]            ) # only plot variables that match these search/filter words
    self.veto          = kwargs.get('veto',     [ ]            ) # do not plot variables that match these search/filter words
    self.flag          = kwargs.get('flag',     ""             ) # flag, e.g. 'up', 'down', ...
    self.only          = ensurelist(self.only)
    self.veto          = ensurelist(self.veto)
  
  def __str__(self):
    """Returns string representation of Selection object."""
    return self.name
  
  def __repr__(self):
    """Returns string representation of Selection object."""
    return "<%s(%r,%r) at %s>"%(self.__class__.__name__,self.name,self.selection,hex(id(self)))
  
  def __iter__(self):
    """Start iteration over selection information."""
    yield self.name
    yield self.selection
  
  def __add__(self, selection2):
    """Add selections by combining their selection string (can be string or Selection object)."""
    if isinstance(selection2,str):
      selection2 = Selection(selection2,selection2) # make selection object
    return self.join(selection2)
  
  def __mul__(self, weight):
    """Multiply selection with some weight (that can be string or Selection object)."""
    result = None
    weight = joinweights(self.weight,weight)
    if isinstance(weight,str):
      result = Selection("%s (%s)"%(self.name,weight),joincuts(self.selection,weight=weight))
    else:
      result = Selection("%s (%s)"%(self.name,weight.title),joincuts(self.selection,weight=weight))
    return result
  
  def clone(self,*args,**kwargs):
    """Shallow copy."""
    verbosity = LOG.getverbosity(self,kwargs)
    strargs = tuple([a for a in args if isinstance(a,str)]) # string arguments: name, title, selection
    if verbosity>=2:
      print(">>> Selection.clone: Old strargs=%r, kwargs=%r"%(strargs,kwargs))
    if not strargs:
      strargs = (kwargs.pop('name',self.name),) # default name
    if len(strargs)==1:
      strargs = (strargs[0],kwargs.pop('title',self.title),)+strargs[1:] # insert default title
    newdict = self.__dict__.copy()
    if 'fname' in kwargs:
      kwargs['filename'] = kwargs['fname']
    if 'filename' in kwargs:
      kwargs['filename'] = kwargs['filename'].replace('$FILE',self.filename)
    if 'tag' in kwargs:
      kwargs['filename'] = kwargs.get('filename',self.filename)+kwargs['tag']
    if kwargs.get('combine',True) and 'weight' in kwargs and self.weight:
      kwargs['weight'] = joinweights(kwargs['weight'],self.weight)
    if 'replace' in kwargs: # replace part of selection
      rargs = kwargs['replace']
      if len(rargs)==2 and isinstance(rargs[0],str) and isinstance(rargs[1],str):
        rargs = [rargs] # ensure list of tuples with two strings
      for rarg in rargs: # loop over tuples of two strings: (oldpattern,newpattern)
        assert len(rarg)==2, "Replace argument must be tuple of length 2! Got: %r"%(rarg,)
        kwargs.setdefault('update',False) # do not overwrite attribute of current object
        newsel = self.replace(*rarg,**kwargs) # use substitution with regular expressions
      LOG.verb("Selection.clone: Replaced %r -> %r"%(self.selection,newsel),verbosity,level=2)
      strargs = strargs[:2]+(newsel,)+strargs[2:] # insert default title
    for key in list(kwargs.keys())+['name','title','selection','replace']: # prevent overwrite: set via newargs
      newdict.pop(key,None)
    newargs = strargs
    if verbosity>=2:
      print(">>> Selection.clone: New args=%r, kwargs=%r"%(newargs,kwargs))
    newsel = Selection(*newargs,**kwargs)
    newsel.__dict__.update(newdict)
    if verbosity>=2:
      print(">>> Selection.clone: Cloned %r -> %r"%(self,newsel))
    return newsel
  
  def contains(self, string, **kwargs):
    """Return if selection string contains given substring."""
    return string in self.selections
  
  def replace(self, old, new, **kwargs):
    """Replace given substring in selection string."""
    verbosity = LOG.getverbosity(self,kwargs)
    if kwargs.get('regex',False): # use substitution with regular expressions
      newsel = re.sub(old,new,self.selection)
    else:
      newsel = self.selection.replace(old,new)
    if kwargs.get('update',True):
      LOG.verb("Selection.replace: Update selection string %r -> %r"%(self.selection,newsel),verbosity,level=2)
      self.selection = newsel
    else:
      LOG.verb("Selection.replace: Created selection string %r -> %r"%(self.selection,newsel),verbosity,level=2)
    return newsel
  
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
    """Check is variable is filtered or vetoed for this variable."""
    verbosity = LOG.getverbosity(kwargs)
    if not isinstance(variable,str):
      variable = variable.name
    for searchterm in self.veto: # veto variable if matches search term
      if re.search(searchterm,variable):
        LOG.verb("Selection.plotFor: Regex match of variable %r to %r"%(variable,searchterm),verbosity,level=2)
        return False # do not plot
    for searchterm in self.only: # filter variable if matches search term
      if re.search(searchterm,variable):
        LOG.verb("Selection.plotFor: Regex match of variable %r to %r"%(variable,searchterm),verbosity,level=2)
        return True # plot
    return len(self.only)==0 # plot, unless filters are defined
  
  def join(self, *selections):
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
  
  def invertcharge(self,**kwargs):
    """Invert charge requirement:
      q_1*q_2<0 (OS) -> q_1*q_2>0 (SS)
    """
    oldstr = self.selection # old selection string
    newsel = deepcopy(self) # create new object
    newsel.selection = invertcharge(oldstr,**kwargs) # overwrite selection string
    return newsel
    
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
