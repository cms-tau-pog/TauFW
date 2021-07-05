# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
import re
from array import array
from copy import copy, deepcopy
from ROOT import TH1D, TH2D
from TauFW.Plotter.plot.string import *
from TauFW.Plotter.plot.Context import getcontext
from TauFW.Plotter.plot.utils import LOG, isnumber, islist, ensurelist, unwraplistargs


class Variable(object):
  """
  Variable class to:
   - hold all relevant information of a variable that will be plotted;
       var name, filename friendly name, LaTeX friendly title, binning, ...
   - allow for variable binning into TH1
   - allow for contextual binning, i.e. depending on channel/selection/...
   - easy string conversions: filename, LaTeX, ...
   - analysis-specific operations: applying variations, ...
  """
  
  def __init__(self, name, *args, **kwargs):
    strings           = [a for a in args if isinstance(a,str) ]
    self.name         = name # variable name in tree, to be used in draw command
    self._name        = name # backup for addoverflow
    self.title        = strings[0] if strings else self.name
    filename          = makefilename(self.name.replace('/','_'))  # file-safe name
    self.title        = kwargs.get('title',       self.title    ) # for plot axes
    self.filename     = kwargs.get('fname',       filename      ) # file-friendly name for files & histograms
    self.filename     = kwargs.get('filename',    self.filename ) # alias
    self.filename     = self.filename.replace('$NAME',self.name).replace('$VAR',filename) #.replace('$FILE',self.filename)
    self.tag          = kwargs.get('tag',         ""            )
    self.units        = kwargs.get('units',       True          ) # for plot axes
    self.latex        = kwargs.get('latex',       True          ) # for plot axes
    self.nbins        = None
    self.min          = None
    self.max          = None
    self.bins         = None # bin edges
    self.cut          = kwargs.get('cut',         ""            ) # extra cut when filling histograms
    self.weight       = kwargs.get('weight',      ""            ) # extra weight when filling histograms (MC only)
    self.dataweight   = kwargs.get('dataweight',  ""            ) # extra weight when filling histograms for data
    self.setbins(*args)
    self.dividebins   = kwargs.get('dividebins', self.hasvariablebins() ) # divide each histogram bins by it bin size (done in Plot.draw)
    self.data         = kwargs.get('data',        True          ) # also draw data
    self.flag         = kwargs.get('flag',        ""            ) # flag, e.g. 'up', 'down', ...
    self.binlabels    = kwargs.get('labels',      [ ]           ) # bin labels for x axis
    self.ymin         = kwargs.get('ymin',        None          )
    self.ymax         = kwargs.get('ymax',        None          )
    self.rmin         = kwargs.get('rmin',        None          )
    self.rmax         = kwargs.get('rmax',        None          )
    self.ratiorange   = kwargs.get('rrange',      None          )
    self.logx         = kwargs.get('logx',        False         )
    self.logy         = kwargs.get('logy',        False         )
    self.ymargin      = kwargs.get('ymargin',     None          ) # margin between hist maximum and plot's top
    self.logyrange    = kwargs.get('logyrange',   None          ) # log(y) range from hist maximum to ymin
    self.position     = kwargs.get('pos',         ""            ) # legend position
    self.position     = kwargs.get('position',    self.position ) # legend position
    self.ncols        = kwargs.get('ncol',        None          ) # number of legend columns
    self.ncols        = kwargs.get('ncols',       self.ncols    ) # number of legend columns
    #self.plot         = kwargs.get('plots',       True          )
    self.only         = kwargs.get('only',        [ ]           ) # only plot for these patterns
    self.veto         = kwargs.get('veto',        [ ]           ) # do not plot for these patterns
    self.blindcuts    = kwargs.get('blind',       ""            ) # string for blind cuts to blind data
    self._addoverflow = kwargs.get('addof',       False         ) # add overflow to last bin
    self._addoverflow = kwargs.get('addoverflow', self._addoverflow ) # add overflow to last bin
    if self.latex:
      self.title = makelatex(self.title,units=self.units)
      if 'ctitle' in kwargs:
        for ckey, title in kwargs['ctitle'].iteritems():
          kwargs['ctitle'][ckey] = makelatex(title)
    if self.only:
      self.only = ensurelist(self.only)
    if self.veto:
      self.veto = ensurelist(self.veto)
    if self.binlabels and len(self.binlabels)<self.nbins:
      LOG.warning("Variable.init: len(binlabels)=%d < %d=nbins"%(len(self.binlabels),self.nbins))
    if self._addoverflow:
      self.addoverflow()
    if islist(self.blindcuts):
      LOG.insist(len(self.blindcuts)==2,"Variable.init: blind cuts must be a string, or a pair of floats! Got: %s"%(self.blindcuts,))
      self.blindcuts = self.blind(*self.blindcuts)
    self.ctxtitle    = getcontext(kwargs, self.title,     key='ctitle',    regex=True ) # context-dependent title
    self.ctxbins     = getcontext(kwargs, args,           key='cbins',     regex=True ) # context-dependent binning
    self.ctxposition = getcontext(kwargs, self.position,  key='cposition', regex=True ) # context-dependent position
    self.ctxblind    = getcontext(kwargs, self.blindcuts, key='cblind',    regex=True ) # context-dependent blind limits
    self.ctxymargin  = getcontext(kwargs, self.ymargin,   key='cymargin',  regex=True ) # context-dependent ymargin
    self.ctxcut      = getcontext(kwargs, self.cut,       key='ccut',      regex=True ) # context-dependent cuts
    self.ctxweight   = getcontext(kwargs, self.weight,    key='cweight',   regex=True ) # context-dependent cuts
      
  
  @property
  def xmin(self): return self.min
  @xmin.setter
  def xmin(self,value): self.xmin = value
  
  @property
  def xmax(self): return self.max
  @xmax.setter
  def xmax(self,value): self.xmax = value
  
  def __str__(self):
    """Returns string representation of Variable object."""
    return self.name
  
  def __repr__(self):
    """Returns string representation of Variable object."""
    #return '<%s.%s("%s","%s",%s,%s,%s)>'%(self.__class__.__module__,self.__class__.__name__,self.name,self.title,self.nbins,self.xmin,self.xmax)
    return '<%s(%r,%r,%s,%s,%s) at %s>'%(self.__class__.__name__,self.name,self.title,self.nbins,self.xmin,self.xmax,hex(id(self)))
  
  def __iter__(self):
    """Start iteration over variable information."""
    for i in [self.name,self.nbins,self.min,self.max]:
      yield i
  
  def __gt__(self,ovar):
    """Order alphabetically."""
    return self.filename > ovar.filename
  
  def clone(self,*args,**kwargs):
    """Shallow copy."""
    verbosity = LOG.getverbosity(self,kwargs)
    if not args:
      args = self.getbins()
      cut  = kwargs.get('cut',None)
      if cut and self.ctxbins: # change context based on extra cut
        bins = self.ctxbins.getcontext(cut) # get bins in this context
        if args!=bins and verbosity>=2:
          print ">>> Variable.clone: Changing binning %r -> %r because of context %r"%(args,bins,cut)
        args = bins
      if isinstance(args,list): # assume list is bin edges
        args = (args,)
    newdict = self.__dict__.copy()
    if 'fname' in kwargs:
      kwargs['filename'] = kwargs['fname']
    if 'filename' in kwargs:
      kwargs['filename'] = kwargs['filename'].replace('$FILE',self.filename)
    if kwargs.get('combine',True) and 'weight' in kwargs and self.weight:
      kwargs['weight'] = combineWeights(kwargs['weight'],self.weight)
    for key in kwargs.keys()+['nbins','min','max','bins']: # to be reset with args
      if key in newdict:
        newdict.pop(key)
    if 'cbins' in kwargs:
      newdict.pop('ctxbins')
    elif self.ctxbins:
      newdict['ctxbins'] = self.ctxbins.clone() # create new dictionary
      newdict['ctxbins'].default = args # change default context
    newvar = Variable(self.name,*args,**kwargs)
    newvar.__dict__.update(newdict)
    if verbosity>=2:
      print ">>> Variable.clone: Cloned %r -> %r"%(self,newvar)
    return newvar
  
  def issame(self,ovar,**kwargs):
    """Compare Variable objects."""
    return self.name==ovar.name and self.getbins()==ovar.getbins()
  
  def printbins(self,filename=False):
    """Print the variable name with the binning."""
    if filename:
      return '%s(%s,%s,%s)'%(self.filename,self.nbins,self.xmin,self.xmax)
    else:
      return '%s(%s,%s,%s)'%(self.name,self.nbins,self.xmin,self.xmax)
  
  def setbins(self,*args):
    """Set binning: (N,min,max), or bins if it is set"""
    LOG.verb('Variable.setbins: setting binning to %s'%(args,),level=2)
    numbers         = [a for a in args if isnumber(a)]
    bins            = [a for a in args if islist(a)  ]
    if len(numbers)==3:
      self.nbins    = numbers[0]
      self.min      = numbers[1]
      self.max      = numbers[2]
      self.bins     = None
    elif len(bins)>0:
      edges         = list(bins[0])
      self.nbins    = len(edges)-1
      self.min      = edges[0]
      self.max      = edges[-1]
      self.bins     = edges
    else:
      LOG.throw(IOError,'Variable: bad arguments "%s" for binning!'%(args,))
  
  def getbins(self,full=False):
    """Get binning: (N,xmin,xmax), or bins if it is set"""
    if self.hasvariablebins():
      return self.bins
    elif full: # get binedges
      return [self.min+i*(self.max-self.min)/self.nbins for i in xrange(self.nbins+1)]
    else:
      return (self.nbins,self.min,self.max)
  
  def getedge(self,i):
    """Get edge. 0=first edge, nbins+1=last edge"""
    LOG.insist(i>=0,"getedge: Number of bin edge has to be >= 0! Got: %s"%(i))
    LOG.insist(i<=self.nbins+1,"getedge: Number of bin edge has to be <= %d! Got: %s"%(self.nbins+1,i))
    if self.hasvariablebins():
      return self.bins[i]
    return self.min+i*(self.max-self.min)/self.nbins
  
  def hasvariablebins(self):
    """True if bins is set."""
    return self.bins!=None
  
  def hasintbins(self):
    """True if binning is integer."""
    width = (self.max-self.min)/self.nbins
    return self.bins==None and int(self.min)==self.min and int(self.max)==self.max and width==1
  
  def match(self, *terms, **kwargs):
    """Match search terms to the variable's name and title."""
    return match(terms,[self.name,self.title])
  
  def changecontext(self,*args,**kwargs):
    """Change the contextual title, binning or position for a set of arguments, if it is available"""
    if self.ctxtitle:
      title = self.ctxtitle.getcontext(*args)
      if title!=None:
        self.title = title
    if self.ctxbins:
      bins = self.ctxbins.getcontext(*args)
      if isinstance(bins,list):
        bins = (bins,)
      if bins!=None:
        self.setbins(*bins)
      if self._addoverflow:
        self.addoverflow() # in case the last bin changed
      self.dividebybinsize = kwargs.get('dividebybinsize',self.hasvariablebins())
    if self.ctxposition:
      position = self.ctxposition.getcontext(*args)
      if position!=None:
        self.position = position
    if self.ctxymargin:
      ymargin = self.ctxymargin.getcontext(*args)
      if ymargin!=None:
        self.ymargin = ymargin
    if self.ctxcut:
      cut = self.ctxcut.getcontext(*args)
      if cut!=None:
        self.cut = cut
    if self.ctxweight:
      weight = self.ctxweight.getcontext(*args)
      if weight!=None:
        self.weight = weight
  
  def plotfor(self,*strings,**kwargs):
    """Check if given string is filtered (with 'only') or vetoed (with 'veto') for this variable."""
    verbosity = LOG.getverbosity(self,kwargs)
    strings   = list(strings)
    LOG.verbose('Variable.plotfor: strings=%s, veto=%s, only=%s'%(strings,self.veto,self.only),verbosity,level=2)
    for i, string in enumerate(strings):
      if string.__class__.__name__=='Selection':
        string     = string.selection
        strings[i] = string
      for searchterm in self.veto:
        if re.search(searchterm,string):
          LOG.verbose('Variable.plotfor: Regex match of string "%s" to "%s"'%(string,searchterm),verbosity,level=2)
          return False
    if len(self.only)==0:
      return True
    for i, string in enumerate(strings):
      for searchterm in self.only:
        if re.search(searchterm,string):
          LOG.verbose('Variable.plotfor: Regex match of string "%s" to "%s"'%(string,searchterm),verbosity,level=2)
          return True
    return False
  
  def unwrap(self):
    return (self.name,self.nbins,self.min,self.max)
  
  def getnametitle(self,name=None,title=None,tag=None):
    """Help function to create name and title."""
    if tag and tag[0]!='_':
      tag   = '_'+tag
    if name==None:
      name  = self.filename+tag
    if title==None:
      title = self.title
    name = name.replace('(','').replace(')','').replace('[','').replace(']','').replace(',','-').replace('.','p')
    return name, title
  
  def gethist(self,name=None,title=None,**kwargs):
    """Create a 1D histogram."""
    tag     = kwargs.get('tag',     ""          )
    poisson = kwargs.get('poisson', False       )
    sumw2   = kwargs.get('sumw2',   not poisson )
    xtitle  = kwargs.get('xtitle',  self.title  )
    #TH1Class = TH1D # TH1I if self.hasintbins() else TH1D
    name, title = self.getnametitle(name,title,tag)
    if self.hasvariablebins():
      hist = TH1D(name,title,self.nbins,array('d',list(self.bins)))
    else:
      hist = TH1D(name,title,self.nbins,self.min,self.max)
    if poisson:
      hist.SetBinErrorOption(TH1D.kPoisson)
    elif sumw2:
      hist.Sumw2()
    hist.GetXaxis().SetTitle(xtitle)
    #hist.SetDirectory(0)
    return hist
  
  def gethist2D(self,yvariable,name=None,title=None,**kwargs):
    """Create a 2D histogram."""
    tag     = kwargs.get('tag',     ""          )
    poisson = kwargs.get('poisson', False       )
    sumw2   = kwargs.get('sumw2',   not poisson )
    xtitle  = kwargs.get('xtitle',  self.title  )
    name, title = self.getnametitle(name,title,tag)
    if self.hasvariablebins() and yvariable.hasvariablebins():
      hist = TH2D(name,title,self.nbins,array('d',list(self.bins)),yvariable.nbins,array('d',list(yvariable.bins)))
    elif self.hasvariablebins():
      hist = TH2D(name,title,self.nbins,array('d',list(self.bins)),yvariable.nbins,yvariable.min,yvariable.max)
    else:
      hist = TH2D(name,title,self.nbins,self.min,self.max,yvariable.nbins,yvariable.min,yvariable.max)
    if poisson:
      hist.SetBinErrorOption(TH2D.kPoisson)
    elif sumw2:
      hist.Sumw2()
    hist.GetXaxis().SetTitle(xtitle)
    return hist
  
  def drawcmd(self,name=None,tag="",bins=False,**kwargs):
    """Create variable expression for the Tree.Draw method."""
    histname, title = self.getnametitle(name,None,tag)
    varname = self.name
    if kwargs.get('undoshift',False): # remove up/down tags from varname
      varname = undoshift(varname)
    if bins:
      dcmd = "%s >> %s(%d,%s,%s)"%(varname,histname,self.nbins,self.min,self.max)
    else:
      dcmd = "%s >> %s"%(varname,histname)
    return dcmd
  
  def drawcmd2D(self,yvar,name=None,tag="",bins=False):
    """Create variable expression for the Tree.Draw method."""
    histname, title = self.getnametitle(name,None,tag)
    if bins:
      dcmd = "%s:%s >> %s(%d,%s,%s,%d,%s,%s)"%(yvar.name,self.name,histname,self.nbins,self.min,self.max,yvar.nbins,yvar.min,yvar.max)
    else:
      dcmd = "%s:%s >> %s"%(yvar.name,self.name,histname)
    return dcmd
  
  def draw(self,tree,cut,name=None,title=None,**kwargs):
    """Create and fill histogram from tree."""
    hist   = self.gethist(name,title,**kwargs)
    option = kwargs.get('option','gOff')
    dcmd   = self.drawcmd(name,**kwargs)
    tree.Draw(dcmd,cut,option)
    return hist
  
  def shift(self,vshift,vars=None,**kwargs):
    """Create new variable with a shift tag added to its name."""
    if len(vshift)>0 and vshift[0]!='_':
      vshift = '_'+vshift
    if vars: # shift only the variables in this list
      newname = shift(self.name,vshift,vars,**kwargs)
    else: # simply add shift at the end
      newname = self.name+vshift
    newvar = deepcopy(self)
    newvar.name = newname # overwrite name
    if not kwargs.get('keepfile',False) and self.name!=newname:
      newvar.filename += vshift # overwrite file name
    return newvar
  
  def shiftjme(self,jshift,**kwargs):
    """Create new variable with a shift tag added to its name."""
    if len(jshift)>0 and jshift[0]!='_':
      jshift = '_'+jshift
    newname  = shiftjme(self.name,jshift,**kwargs)
    newvar   = deepcopy(self)
    newvar.name = newname # overwrite name
    if not kwargs.get('keepfile',False) and self.name!=newname:
      newvar.filename += jshift # overwrite file name
    return newvar
  
  def shiftname(self,vshift,**kwargs):
    """Shift name and return string only (without creating new Variable object)."""
    return shift(self.name,vshift,**kwargs)
  
  def blind(self,bmin=None,bmax=None,**kwargs):
    """Return selection string that blinds some window (bmin,bmax),
    making sure the cuts match the bin edges of some (nbins,xmin,xmax) binning."""
    verbosity = LOG.getverbosity(self,kwargs)
    if bmin==None:
      bmin = self.blindcuts[0]
    if bmax<bmin:
      bmax, bmin = bmin, bmax
    LOG.insist(bmax>bmin,'Variable.blind: "%s" has window a = %s <= %s = b !'%(self._name,bmin,bmax))
    blindcut = ""
    xlow, xhigh = bmin, bmax
    nbins, xmin, xmax = self.nbins, self.min, self.max
    if self.hasvariablebins():
      bins = self.bins
      for xval in bins:
        if xval>bmin: break
        xlow = xval
      for xval in reversed(bins):
        if xval<bmax: break
        xhigh = xval
    else:
      binwidth   = float(xmax-xmin)/nbins
      if xmin<bmin<xmax:
        bin, rem = divmod(bmin-xmin,binwidth)
        xlow     = bin*binwidth
      if xmin<bmax<xmax:
        bin, rem = divmod(bmax-xmin,binwidth)
        if rem>0:
          bin   += 1
        xhigh    = bin*binwidth
    blindcut = "(%s<%s || %s<%s)"%(self.name,xlow,xhigh,self.name)
    LOG.verb('Variable.blind: blindcut = "%s" for a (%s,%s) window and (%s,%s,%s) binning'%(blindcut,bmin,bmax,nbins,xmin,xmax),verbosity,2) 
    return blindcut
  
  def addoverflow(self,**kwargs):
    """Modify variable name in order to add the overflow to the last bin."""
    verbosity = LOG.getverbosity(self,kwargs)
    if self.hasvariablebins():
      width     = self.bins[-1]-self.bins[-2]
      threshold = self.bins[-2] + 0.90*width
    else:
      width     = (self.max-self.min)/float(self.nbins)
      threshold = self.max - 0.90*width
    self.name   = "min(%s,%s)"%(self._name,threshold)
    LOG.verb("Variable.addoverflow: '%s' -> '%s' for binning '%s'"%(self._name,self.name,self.getbins()),verbosity,2)
    return self.name
  
Var = Variable # short alias


def wrapvariable(*args,**kwargs):
  """Help function to wrap variable arguments into a Variable object."""
  if len(args)==4 or len(args)==5:
    return Variable(args) # (xvar,nxbins,xmin,xmax)
  elif len(args)==1 and isinstance(args[0],Variable):
    return args[0]
  LOG.warning('wrapvariable: Could not unwrap arguments "%s" to a Variable object. Returning None.'%args)
  return None
  

def unwrap_variable_bins(*args,**kwargs):
  """Help function to unwrap variable arguments to return variable name, number of bins,
  minumum and maximum x axis value."""
  if len(args)==4:
    return args # (xvar,nxbins,xmin,xmax)
  elif len(args)==1 and isintance(args[0],Variable):
    return args[0].unwrap()
  LOG.throw(IOError,'unwrap_variable_bins: Could not unwrap arguments "%s" to a Variable object.'%args)
  

def ensurevar(*args,**kwargs):
  """Help function to ensure arguments are one Variable object:
      - xvar, nxbins, xmin, xmax (str, int, float, float)
      - xvar, xbins (str, list)
      - var (str)
  """
  args = unwraplistargs(args)
  if len(args)==4:
    return Variable(*args) # (xvar,nxbins,xmin,xmax)
  elif len(args)==2 and islist(args[1]):
    return Variable(*args)  # (xvar,xbins)
  elif len(args)==1 and isinstance(args[0],Variable):
    return args[0]
  else:
    LOG.throw(IOError,'unwrap_variable_args: Could not unwrap arguments %s, len(args)=%d. Returning None.'%(args,len(args)))
  
