# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
import os, re
from TauFW.Plotter.sample.utils import *
from TauFW.Plotter.plot.strings import *
from TauFW.Plotter.plot.utils import deletehist, printhist, round2digit
from TauFW.Plotter.plot.Variable import Variable
from TauFW.Plotter.sample.SampleStyle import *
from TauFW.Plotter.plot.MultiDraw import MultiDraw
from ROOT import TTree


class Sample(object):
  """
  Sample class to
  - hold all relevant sample information: file, name, cross section, number of events,
    type, extra weight, extra scale factor, color, ...
  - calculate and set normalization (norm) based on integrated luminosity, cross section
    and number of events
  - create and fill histograms from tree
  - split histograms into components (e.g. based on some (generator-level) selections)
  """
  
  def __init__(self, name, title, filename, xsec=-1.0, **kwargs):
    import TauFW.Plotter.sample.utils as GLOB
    LOG.setverbosity(kwargs)
    self.name         = name                            # short name to use for files, histograms, etc.
    self.title        = title                           # title for histogram entries
    self.xsec         = xsec                            # cross section in units of pb
    self.filename     = filename                        # file name with tree
    self.fnameshort   = os.path.basename(self.filename) # short file name for printing
    self._file        = None                            # TFile file
    self._tree        = None                            # TTree tree
    self.splitsamples = [ ]                             # samples when splitting into subsamples
    self.treename     = kwargs.get('tree',         None         ) or 'tree'
    self.nevents      = kwargs.get('nevts',        -1           ) # "raw" number of events
    self.nexpevts     = kwargs.get('nexp',         -1           ) # number of events you expect to be processed for check
    self.sumweights   = kwargs.get('sumw',         self.nevents ) # sum weights
    self.binnevts     = kwargs.get('binnevts',      1           ) # cutflow bin with total number of (unweighted) events
    self.binsumw      = kwargs.get('binsumw',      15           ) # cutflow bin with total sum of weight
    self.lumi         = kwargs.get('lumi',         GLOB.lumi    ) # integrated luminosity
    self.norm         = kwargs.get('norm',         1.0          ) # lumi*xsec/binsumw normalization
    self.scale        = kwargs.get('scale',        1.0          ) # scales factor (e.g. for W+Jets renormalization)
    self.upscale      = kwargs.get('upscale',      1.0          ) # drawing up/down scaling
    self._scale       = self.scale # back up scale to overwrite previous renormalizations
    self.weight       = kwargs.get('weight',       ""           ) # weights
    self.extraweight  = kwargs.get('extraweight',  ""           ) # extra weights particular to this sample
    self.cuts         = kwargs.get('cuts',         ""           ) # extra cuts particular to this sample
    self.channel      = kwargs.get('channel',      ""           ) # channel
    self.isdata       = kwargs.get('data',         False        ) # flag for observed data
    self.issignal     = kwargs.get('signal',       False        ) # flag for (new physics) signal
    self.isembed      = kwargs.get('embed',        False        ) # flag for embedded sample
    self.isexp        = kwargs.get('exp',          self.isembed ) or not (self.isdata or self.issignal) # background MC (expected SM process)
    self.blinddict    = kwargs.get('blind',        { }          ) # blind data in some given range, e.g. blind={xvar:(xmin,xmax)}
    self.fillcolor    = kwargs.get('color',        None         ) or self.setcolor() # fill color
    self.linecolor    = kwargs.get('lcolor',       kBlack       ) # line color
    if not isinstance(self,MergedSample):
      file = ensureTFile(self.filename) # check file
      file.Close()
      if self.isdata:
        self.setnevents(self.binnevts,self.binsumw)
      elif not self.isembed: #self.xsec>=0:
        self.setnevents(self.binnevts,self.binsumw)
        self.normalize(lumi=self.lumi,xsec=self.xsec,sumw=self.sumweights)
      if 0<self.nevents<self.nexpevts*0.97:
         LOG.warning('Sample: Sample %r has significantly fewer events (%d) than expected (%d).'%(self.name,self.nevents,self.nexpevts))
  
  def __str__(self):
    """Returns string."""
    return self.name
  
  def __repr__(self):
    """Returns string representation."""
    #return '<%s.%s(%r,%r) at %s>'%(self.__class__.__module__,self.__class__.__name__,self.name,self.title,hex(id(self)))
    return '<%s(%r,%r) at %s>'%(self.__class__.__name__,self.name,self.title,hex(id(self)))
  
  @staticmethod
  def printheader():
    print ">>> \033[4m%-21s %-26s %12s %11s %11s %10s  %s\033[0m"%(
               "Sample name","title","xsec [pb]","nevents","sumweights","norm","weight"+' '*8)
  
  def printrow(self,**kwargs):
    print self.row(**kwargs)
  
  def row(self,pre="",indent=0):
    """Returns string that can be used as a row in a samples summary table"""
    name = self.name.ljust(21-indent)
    return ">>> %s%s %-26s %12s %11s %11s %10.3s  %s"%(
            pre,name,self.title,self.xsec,self.nevents,self.sumweights,self.norm,self.extraweight)
  
  def printobjs(self,title=""):
    """Print all sample objects recursively."""
    print ">>> %s%r"%(title,self)
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.printobjs(title+"  ")
    if self.splitsamples:
      print ">>> %s  Split samples:"%(title)
      for sample in self.splitsamples:
        sample.printobjs(title+"    ")
  
  @property
  def file(self):
    return self.getfile()
  
  @file.setter
  def file(self, value):
    self._file = value
  
  def getfile(self,refresh=False):
    if not self._file:
      LOG.verb("Sample.getfile: Opening file %s..."%(self.filename),level=2)
      self._file = ensureTFile(self.filename)
    elif refresh:
      LOG.verb("Sample.getfile: Closing and opening file %s..."%(self.filename),level=2)
      self._file.Close()
      self._file = ensureTFile(self.filename)
    return self._file
  
  def get_newfile_and_tree(self):
    """Create and return a new TFile and TTree without saving to self for thread safety."""
    file = ensureTFile(self.filename,'READ')
    tree = file.Get(self.treename)
    if not tree or not isinstance(tree,TTree):
      LOG.throw(IOError,'Sample.get_newfile_and_tree: Could not find tree %r for %r in %s!'%(self.treename,self.name,self.filename))
    return file, tree
  
  @property
  def tree(self):
    if not self.file:
      LOG.verb("Sample.tree: Opening file %s to get tree %r..."%(self.filename,self.treename),level=2)
      self._tree = self.file.Get(self.treename)
    elif self._tree and isinstance(self._tree,TTree):
      LOG.verb("Sample.tree: Getting existing tree %s..."%(self._tree),level=2)
    else:
      LOG.verb("Sample.tree: No valid tree (%s). Retrieving tree %r from file %s..."%(self._tree,self.treename,self.filename),level=2)
      self._tree = self.file.Get(self.treename)
    return self._tree
  
  @tree.setter
  def tree(self, value):
    self._tree = value
  
  def __copy__(self):
    cls = self.__class__
    result = cls.__new__(cls)
    result.__dict__.update(self.__dict__)
    return result
  
  def __deepcopy__(self, memo):
    cls = self.__class__
    result = cls.__new__(cls)
    memo[id(self)] = result
    for key, val in self.__dict__.items():
        setattr(result, key, deepcopy(val, memo))
    return result
  
  def clone(self,name=None,title=None,filename=None,**kwargs):
    """Shallow copy."""
    if name==None:
      name = self.name  + ("" if samename else  "_clone" )
    if title==None:
      title = self.title
    if filename==None:
      filename = self.filename
    samename                = kwargs.get('samename', False )
    deep                    = kwargs.get('deep',     False ) # deep copy
    close                   = kwargs.get('close',    False ) # keep new sample closed for memory space
    splitsamples            = [s.clone(samename=samename,deep=deep) for s in self.splitsamples] if deep else self.splitsamples[:]
    kwargs['isdata']        = self.isdata
    kwargs['isembed']       = self.isembed
    newsample               = type(self)(name,title,filename,**kwargs)
    newdict                 = self.__dict__.copy()
    newdict['name']         = name
    newdict['title']        = title
    newdict['splitsamples'] = splitsamples
    if deep and self.file: # force new, separate file
      newdict['file'] = None #ensureTFile(self.file.GetName())
    newsample.__dict__.update(newdict)
    #LOG.verb('Sample.clone: %r, weight = %r'%(newsample.name,newsample.weight),1)
    if close:
      newsample.close()
    return newsample
  
  ###def appendFileName(self,file_app,**kwargs):
  ###  """Append filename (in front of globalTag or .root)."""
  ###  verbosity     = LOG.getverbosity(kwargs)
  ###  title_app     = kwargs.get('title_app',  "" )
  ###  title_tag     = kwargs.get('title_tag',  "" )
  ###  title_veto    = kwargs.get('title_veto', "" )
  ###  oldfilename   = self.filename
  ###  if globalTag:
  ###    newfilename = oldfilename if file_app in oldfilename else oldfilename.replace(globalTag,file_app+globalTag)
  ###  else:
  ###    newfilename = oldfilename if file_app in oldfilename else oldfilename.replace(".root",file_app+".root")
  ###  LOG.verb('replacing %r with %r'%(oldfilename,self.filename),verbosity,3)
  ###  self.filename = newfilename
  ###  if file_app  not in self.name:
  ###    self.name  += file_app
  ###  if title_app not in self.title and not (title_veto and re.search(title_veto,self.title)):
  ###    self.title += title_app
  ###  if self.file:
  ###    #reopenTree = True if self._tree else False
  ###    self.file.Close()
  ###    self.file = ensureTFile(self.filename)
  ###    #if reopenTree: self.tree = self.file.Get(self.treename)
  ###  if not isinstance(self,MergedSample):
  ###    norm_old  = self.norm
  ###    N_old     = self.sumweights
  ###    N_unw_old = self.nevents
  ###    if self.isdata:
  ###      self.setnevents(self.binnevts,self.binsumw)
  ###    if self.isembed:
  ###      pass
  ###    elif self.xsec>=0:
  ###      self.setnevents(self.binnevts,self.binsumw)
  ###      #self.normalize(lumi=self.lumi) # can affect scale computed by stitching
  ###    if (N_old>0 and abs(N_old-self.sumweights)/float(N_old)>0.02) or (N_unw_old>0 and abs(N_unw_old-self.nevents)/float(N_unw_old)>0.02):
  ###      LOG.warning('Sample.appendFileName: file %s has a different number of events (N=%s, N_unw=%s, norm=%s, xsec=%s, lumi=%s) than %s (N=%s, N_unw=%s, norm=%s)! '%\
  ###        (self.filename,self.sumweights,self.nevents,self.norm,self.xsec,self.lumi,oldfilename,N_old,N_unw_old,norm_old))
  ###    ###if norm_old and abs(norm_old-self.norm)/float(norm_old)>0.02:
  ###    ###  LOG.warning('Sample.appendFileName: file %s has a different number of normalization (N=%s, N_unw=%s, norm=%s, xsec=%s, lumi=%s) than %s (N=%s, N_unw=%s, norm=%s)! '%\
  ###    ###    (self.filename,self.sumweights,self.nevents,self.norm,self.xsec,self.lumi,oldfilename,N_old,N_unw_old,norm_old))
  ###  elif ':' not in self.filename and not os.path.isfile(self.filename):
  ###    LOG.warning('Sample.appendFileName: file %s does not exist!'%(self.filename))
  ###  if isinstance(self,MergedSample):
  ###    for sample in self.samples:
  ###      sample.appendFileName(file_app,**kwargs)
  ###  for sample in self.splitsamples:
  ###      sample.appendFileName(file_app,**kwargs)
  
  def setfilename(self,filename):
    """Set filename."""
    self.filename = filename
    self.fnameshort  = '/'.join(self.filename.split('/')[-2:])
    return self.filename
  
  def reload(self,**kwargs):
    """Close and reopen file. Use it to free up and clean memory."""
    verbosity = LOG.getverbosity(kwargs)
    if self.file:
      if verbosity>3:
        LOG.verb('Sample.reload: closing and deleting %s with content:'%(self.file.GetName()),verbosity,2)
        self.file.ls()
      self.file.Close()
      del self.file
      self.file = None
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.reload(**kwargs)
    else:
      if self.filename:
        self.file = TFile.Open(self.filename)
    for sample in self.splitsamples:
        sample.reload(**kwargs)
  
  def open(self,**kwargs):
    """Open file. Use it to free up and clean memory."""
    self.reload(**kwargs)
  
  def close(self,**kwargs):
    """Close file. Use it to free up and clean memory."""
    verbosity = LOG.getverbosity(kwargs)
    if self.file:
      if verbosity>1:
        LOG.verb('Sample.close: closing and deleting %s with content:'%(self.file.GetName()),verbosity,3)
        self.file.ls()
      self.file.Close()
      del self.file
      self.file = None
    for sample in self.splitsamples:
      sample.close(**kwargs)
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.close(**kwargs)
  
  #def __add__(self, sample):
  #  """Add samples into MergedSamples."""
  #  if isinstance(sample,Sample):
  #    mergedsample = MergedSample(self,sample)
  #    return self
  #  return None
  
  def __mul__(self, scale):
   """Multiply selection with some weight (that can be string or Selection object)."""
   if isnumber(scale):
     self.setscale(scale)
     return self
   return None
  
  def setnevents(self,binnevts=None,binsumw=None,cutflow='cutflow'):
    """Automatocally set number of events from the cutflow histogram."""
    file   = self.getfile()
    cfhist = file.Get(cutflow)
    if binnevts==None: binnevts = self.binnevts
    if binsumw==None:  binsumw  = self.binsumw
    if not cfhist:
      errstr = 'Could not find cutflow histogram %r in %s!'%(cutflow,self.filename)
      if self.nevents>0:
        if self.sumweights<=0:
          self.sumweights = self.nevents
        LOG.warning("Could not find cutflow histogram %r in %s! nevents=%.1f, sumweights=%.1f"%(cutflow,self.filename,self.nevents,self.sumweights))
      else:
        LOG.throw(IOError,"Could not find cutflow histogram %r in %s!"%(cutflow,self.filename))
    self.nevents    = cfhist.GetBinContent(binnevts)
    self.sumweights = cfhist.GetBinContent(binsumw)
    file.Close()
    return self.nevents
  
  def normalize(self,lumi=None,xsec=None,sumw=None,**kwargs):
    """Calculate and set the normalization for simulation as lumi*xsec/sumw,
    where sumw is the sum of generator event weights."""
    norm     = 1.
    if lumi==None: lumi = self.lumi
    if xsec==None: xsec = self.xsec
    if sumw==None: sumw = self.sumweights or self.nevents
    if self.isdata:
      LOG.warning('Sample.normalize: Ignoring data sample %r'%(self.name))
    elif lumi<=0 or xsec<=0 or sumw<=0:
      LOG.warning('Sample.normalize: Cannot normalize %r: lumi=%s, xsec=%s, sumw=%s'%(self.name,lumi,xsec,sumw))
    else:
      norm = lumi*xsec*1000/sumw # 1000 to convert pb -> fb
      LOG.verb('Sample.normalize: Normalize %r sample to lumi*xsec*1000/sumw = %.5g*%.5g*1000/%.5g = %.5g!'%(self.name,lumi,xsec,sumw,norm),level=2)
    if norm<=0:
      LOG.warning('Sample.normalize: Calculated normalization for %r sample is %.5g <= 0 (lumi=%.5g,xsec=%.5g,nevts=%.5g)!'%(self.name,norm,lumi,xsec,N_events))
    self.norm = norm
    return norm
  
  def setscale(self,scale):
    """Set scale, incl. for split samples."""
    self.scale = scale
    for sample in self.splitsamples:
      sample.scale = scale
  
  def resetscale(self,scale=1.0,**kwargs):
    verbosity = LOG.getverbosity(kwargs)
    """Reset scale to BU scale."""
    if scale!=1. or self.scale!=self._scale:
      LOG.verb("Sample.resetscale: %s"%(self.name),verbosity,level=2)
      oldscale   = self.scale
      self.scale = self._scale*scale # only rescale top sample
      LOG.verb("     scale = %s -> %s"%(oldscale,self.scale),verbosity,level=2)
    for sample in self.splitsamples:
        sample.resetscale(1.0,**kwargs) # only rescale top sample
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.resetscale(1.0,**kwargs) # only rescale top sample
  
  def setcolor(self,color=None):
    """Set sample color, if no color is given, based on name."""
    if color:
      self.fillcolor = color if isnumber(color) else getcolor(color)
    else:
      self.fillcolor = getcolor(self)
    return self.fillcolor
  
  def addcuts(self, cuts):
    """Add cuts. Join with existing cuts if they exist."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.addcuts(cuts)
    else:
      LOG.verb('Sample.addcuts: %s, join cuts %r with %r'%(self,self.cuts,cuts),level=2)
      self.cuts = joincuts(self.cuts,cuts)
    for sample in self.splitsamples:
        sample.addcuts(cuts)
  
  def addweight(self, weight):
    """Add weight. Join with existing weight if it exists."""
    #LOG.verb('Sample.addweight: combine weights %r with %r'%(self.weight,weight),1)
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.addweight(weight)
    else:
      LOG.verb('Sample.addweight: before: %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
      self.weight = joinweights(self.weight, weight)
      LOG.verb('                  after:  %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
    for sample in self.splitsamples:
        sample.addweight(weight)
  
  def addextraweight(self, weight):
    """Add extra weight. Join with existing weight if it exists."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.addextraweight(weight)
    else:
      LOG.verb('Sample.addextraweight: before: %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
      self.extraweight = joinweights(self.extraweight, weight)
      LOG.verb('                       after:  %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
    for sample in self.splitsamples:
      sample.addextraweight(weight)
  
  def setweight(self, weight, extraweight=False):
    """Set weight, overwriting all previous ones."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.setweight(weight)
    else:
      LOG.verb('Sample.setweight: before: %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
      self.weight = weight
      LOG.verb('                  after:  %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
    for sample in self.splitsamples:
        sample.setweight(weight)
  
  def setextraweight(self, weight):
    """Set extra weight, overwriting all previous ones."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.setextraweight(weight)
    else:
      LOG.verb('Sample.setextraweight: before: %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
      self.extraweight = weight
      LOG.verb('                       after:  %s, self.weight = %r, self.extraweight = %r'%(self,self.weight,self.extraweight),level=2)
    for sample in self.splitsamples:
        sample.setextraweight(weight)
  
  def replaceweight(self, oldweight, newweight):
    """Replace weight."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.replaceweight(oldweight,newweight)
    else:
      if oldweight in self.weight:
        LOG.verb('Sample.replaceweight: before %r'%(self.weight))
        self.weight = self.weight.replace(oldweight,newweight)
        LOG.verb('                      after  %r'%(self.weight))
      if oldweight in self.extraweight:
        LOG.verb('Sample.replaceweight: before %r'%(self.extraweight))
        self.extraweight = self.extraweight.replace(oldweight,newweight)
        LOG.verb('                      after  %r'%(self.extraweight))
  
  def split(self,*splitlist,**kwargs):
    """Split sample into different components with some cuts, e.g.
      sample.split(('ZTT',"Real tau","genmatch_2==5"),
                   ('ZJ', "Fake tau","genmatch_2!=5"))
    """
    verbosity      = LOG.getverbosity(kwargs)
    splitlist      = unwraplistargs(splitlist)
    splitsamples   = [ ]
    for i, info in enumerate(reversed(splitlist)): #split_dict.items()
      name  = "%s_split%d"%(self.name,i)
      if len(info)>=3:
        name, title, cut = info[:3]
      elif len(info)==2:
        name, cut = info[0], info[1]
        title = sample_titles.get(name,name) # from SampleStyle
      sample       = self.clone(name,title)
      sample.cuts  = joincuts(self.cuts,cut)
      sample.color = getcolor(sample)
      splitsamples.append(sample)
    self.splitsamples = splitsamples # save list of split samples
    return splitsamples
  
  def gethist(self, *args, **kwargs):
    """Create and fill a histogram from a tree."""
    variables, selection, issingle = unwrap_gethist_args(*args)
    verbosity  = LOG.getverbosity(kwargs)
    scale      = kwargs.get('scale',    1.0            ) * self.scale * self.norm
    name       = kwargs.get('name',     self.name      ) # hist name
    name      += kwargs.get('tag',      ""             ) # tag for hist name
    title      = kwargs.get('title',    self.title     ) # hist title
    blind      = kwargs.get('blind',    None           ) # blind data in some given range, e.g. blind={xvar:(xmin,xmax)}
    fcolor     = kwargs.get('color',    self.fillcolor ) # fill color
    lcolor     = kwargs.get('lcolor',   self.linecolor ) # line color
    #replaceweight = kwargs.get('replaceweight', None )
    undoshifts = self.isdata and (any('Up' in v.name or 'Down' in v.name for v in variables)
                                  or 'Up' in selection or 'Down' in selection)
    drawopt = 'E0' if self.isdata else 'HIST'
    drawopt = kwargs.get('option', drawopt ) + 'gOff'
    
    # SELECTION STRING & WEIGHTS
    if self.isdata:
      weight = joinweights(self.weight,self.extraweight,kwargs.get('weight',""))
    else:
      weight = joinweights(self.weight,self.extraweight,kwargs.get('weight',"")) #,selection.weight)
    cuts     = joincuts(selection,self.cuts,kwargs.get('cuts',""),kwargs.get('extracuts',"")) #selection.selection
    #if replaceweight:
    #  if len(replaceweight)==2 and not isList(replaceweight[0]):
    #    replaceweight = [replaceweight]
    #  for pattern, substitution in replaceweight:
    #    LOG.verb('Sample.gethist: replacing weight: before %r'%weight,verbosity,2)
    #    weight = re.sub(pattern,substitution,weight)
    #    weight = weight.replace("**","*").strip('*')
    #    LOG.verb('Sample.gethist: replacing weight: after  %r'%weight,verbosity,2)
    cuts = joincuts(cuts,weight=weight)
    
    # PREPARE HISTOGRAMS
    hists   = [ ]
    varexps = [ ]
    for variable in variables:
      
      # VAREXP
      hname  = makehistname(variable.filename,name)
      varcut = ""
      if self.isdata and (blind or variable.blindcuts or variable.cut or variable.weightdata):
        blindcuts = ""
        if blind:
          if isinstance(blind,tuple) and len(blind)==2:
            blindcuts = variable.blind(*blind)
          elif variable.name_ in self.blinddict:
            blindcuts = variable.blind(*self.blinddict[variable.name_])
        elif variable.blindcuts:
          blindcuts = variable.blindcuts
        varcut = joincuts(blindcuts,variable.cut,weight=variable.weightdata)
      elif not self.isdata and (variable.cut or variable.weight):
        varcut = joincuts(variable.cut,weight=variable.weight)
      if varcut:
        varexp = (variable.drawcmd(hname),varcut)
      else:
        varexp = variable.drawcmd(hname)
      if undoshifts:
        varexp = undoshift(varexp)
      varexps.append(varexp)
      
      # HISTOGRAM
      hist = variable.gethist(hname,title,sumw2=(not self.isdata),poisson=self.isdata)
      hist.SetDirectory(0)
      hists.append(hist)
    
    # FILL HISTOGRAMS
    if varexps:
      file, tree = self.get_newfile_and_tree() # create new file and tree for thread safety
      out = tree.MultiDraw(varexps,cuts,drawopt,hists=hists)
      file.Close()
    
    # FINISH
    nentries = 0
    integral = 0
    for variable, hist in zip(variables,hists):
      if scale!=1.0:   hist.Scale(scale)
      if scale==0.0:   LOG.warning("Scale of %s is 0!"%self.name)
      if verbosity>=3: printhist(hist)
      hist.SetLineColor(lcolor)
      hist.SetFillColor(kWhite if self.isdata or self.issignal else fcolor)
      hist.SetMarkerColor(lcolor)
      if hist.GetEntries()>nentries:
        nentries = hist.GetEntries()
        integral = hist.Integral()
    
    # PRINT
    if verbosity>=2:
      print ">>>\n>>> Sample.gethist: %s, %s"%(color(self.name,color="grey"),self.fnameshort)
      print ">>>   entries: %d (%.2f integral)"%(nentries,integral)
      print ">>>   scale: %.6g (scale=%.6g, norm=%.6g)"%(scale,self.scale,self.norm)
      print ">>>   %r"%(cuts)
      if verbosity>=3:
        for var, varexp in zip(variables,varexps):
          print '>>>   Variable %r: varexp=%r'%(var.name,varexp)
          #print '>>>   Variable %r: cut=%r, weight=%r, varexp=%r'%(var.name,var.cut,var.weight,varexp)
    
    if issingle:
      return hists[0]
    return hists
  
  def gethist2D(self, *args, **kwargs):
    """Create and fill a 2D histogram from a tree."""
    variables, selection, issingle = unwrap_gethist_args_2D(*args)
    verbosity = LOG.getverbosity(kwargs)
    scale     = kwargs.get('scale',         1.0        ) * self.scale * self.norm
    name      = kwargs.get('name',          self.name  )
    name     += kwargs.get('tag',           ""         )
    title     = kwargs.get('title',         self.title )
    drawopt   = 'COLZ'
    drawopt   = 'gOff'+kwargs.get('option', drawopt    )
    
    # CUTS
    if self.isdata:
      weight  = joinweights(self.weight,self.extraweight,kwargs.get('weight',""))
    else:
      weight  = joinweights(self.weight,self.extraweight,kwargs.get('weight',""),selection) #.weight
    cuts      = joincuts(selection,self.cuts,kwargs.get('cuts',""),kwargs.get('extracuts',""),weight=weight) #.selection
    
    # PREPARE
    hists     = [ ]
    varexps   = [ ]
    for xvar, yvar in variables:
      
      # VAREXP
      hname = makehistname("%s_vs_%s"%(xvar.filename,yvar.filename),name)
      if xvar.cut or yvar.cut or ((xvar.weight or yvar.weight) and not self.isdata):
        if self.isdata:
          varcut = joincuts(xvar.cut,yvar.cut)
        else:
          varweight = joinweights(xvar.weight,yvar.weight)
          varcut = joincuts(xvar.cut,yvar.cut,weight=varweight)
        varexp = (xvar.drawcmd2D(yvar,hname),varcut)
      else:
        varexp = xvar.drawcmd2D(yvar,hname)
      varexps.append(varexp)
      
      # HISTOGRAM
      hist = xvar.gethist2D(yvar,hname,title,sumw2=(not self.isdata),poisson=self.isdata)
      hist.SetDirectory(0)
      hists.append(hist)
      hist.SetOption(drawopt)
    
    # DRAW
    file, tree = self.get_newfile_and_tree() # create new file and tree for thread safety
    out = tree.MultiDraw(varexps,cuts,drawopt,hists=hists)
    file.Close()
    
    # FINISH
    nentries = 0
    integral = 0
    for variable, hist in zip(variables,hists):
      if scale!=1.0:   hist.Scale(scale)
      if scale==0.0:   LOG.warning("Scale of %s is 0!"%self.name)
      if verbosity>=3: printhist(hist)
      if hist.GetEntries()>nentries:
        nentries = hist.GetEntries()
        integral = hist.Integral()
    
    # PRINT
    if verbosity>=2:
      print ">>>\n>>> Sample.gethist2D - %s: %s"%(color(name,color="grey"),self.fnameshort)
      print ">>>   scale: %.6g (scale=%.6g, norm=%.6g)"%(scale,self.scale,self.norm)
      print ">>>   entries: %d (%.2f integral)"%(nentries,integral)
      print ">>>   %s"%cuts
    
    if issingle:
      return hists[0]
    return hists
  
  def match(self, *terms, **kwargs):
    """Check if search terms match the sample's name, title and/or tags."""
    terms = [l for l in terms if l!='']
    if not terms:
      return False
    found  = True
    regex  = kwargs.get('regex', False   ) # use regexpr patterns
    excl   = kwargs.get('excl',  True    ) # match only one term
    start  = kwargs.get('start', False   ) # match only beginning
    labels = [self.name,self.title]+self.tags
    for searchterm in terms:
      if not regex:
        searchterm = re.sub(r"(?<!\\)\+",r"\+",searchterm) # replace + with \+
        searchterm = re.sub(r"([^\.])\*",r"\1.*",searchterm) # replace * with .*
      if start:
        searchterm = '^'+searchterm
      if excl:
        for label in labels:
          matches = re.findall(searchterm,label)
          if matches:
            break
        else:
          return False # none of the labels contain the searchterm
      else: # inclusive
        for label in labels:
          matches = re.findall(searchterm,label)
          if matches:
            return True # one of the searchterm has been found
    return exclusive
  

def Data(*args,**kwargs):
  kwargs['isdata'] = True
  kwargs['isexp']  = False
  return Sample(*args,**kwargs)
  

def MC(*args,**kwargs):
  kwargs['isdata'] = False
  kwargs['isexp']  = True
  return Sample(*args,**kwargs)
  

from TauFW.Plotter.sample.MergedSample import MergedSample