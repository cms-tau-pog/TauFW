# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
import os, re
from TauFW.Plotter.sample.utils import *
from TauFW.common.tools.math import round2digit, reldiff
from TauFW.common.tools.RDataFrame import RDF, RDataFrame, AddRDFColumn
from TauFW.Plotter.sample.ResultDict import ResultDict, MeanResult # for containing RDataFRame RResultPtr
from TauFW.Plotter.sample.HistSet import HistSetDict, StackDict
from TauFW.Plotter.plot.string import *
from TauFW.Plotter.plot.utils import deletehist, printhist
from TauFW.Plotter.sample.SampleStyle import *
from ROOT import TTree, TFile


class Sample(object):
  """
  Sample class to
  - hold all relevant sample information: file, name, cross section, number of events,
    type, extra weight, extra scale factor, color, ...
  - calculate and set normalization (norm) based on integrated luminosity, cross section
    and number of events
  - create and fill histograms from tree
  - split histograms into components (e.g. based on some (generator-level) selections)
  Initialize as
    Sample(str name, str filename )
    Sample(str name, str title, str filename )
    Sample(str name, str title, str filename, float xsec )
    Sample(str name, str title, str filename, float xsec, int nevts )
  """
  
  def __init__(self, name, *args, **kwargs):
    import TauFW.Plotter.sample.utils as GLOB
    LOG.setverbosity(kwargs) # set global verbosity
    title    = ""
    filename = ""
    xsec     = -1.0
    nevts    = -1
    strargs  = [a for a in args if isinstance(a,str)]
    numargs  = [a for a in args if isnumber(a)]
    if len(strargs)==1:
      filename = strargs[0]
    elif len(strargs)==2:
      title    = strargs[0]
      filename = strargs[1]
    else:
      LOG.throw(IOError,"Sample.__init__: Invalid arguments; no filename was given: %r"%(args,))
    if len(numargs)==1:
      xsec  = numargs[0]
    elif len(numargs)>=2:
      xsec  = numargs[0]
      nevts = numargs[1]
    self.name         = name                            # short name to use for files, histograms, etc.
    self.title        = title or gettitle(name,name)    # title for histogram entries
    self.filename     = filename                        # file name with tree
    self.xsec         = xsec                            # cross section in units of pb
    self.fnameshort   = '/'.join(self.filename.split('/')[-3:]) # short file name for printing
    self.samples      = [self]                          # same as MergedSample
    self.splitsamples = [ ]                             # samples when splitting into subsamples
    self.treename     = kwargs.get('tree',         None         ) or 'tree'
    self.nevents      = kwargs.get('nevts',        nevts        ) # "raw" number of events
    self.nexpevts     = kwargs.get('nexp',         -1           ) # number of events you expect to be processed (to check for missing events)
    self.sumweights   = kwargs.get('sumw',         self.nevents ) # sum (generator) weights
    self.binnevts     = kwargs.get('binnevts',     None         ) or 1  # cutflow bin with total number of (unweighted) events
    self.binsumw      = kwargs.get('binsumw',      None         ) or 17 # cutflow bin with total sum of weight
    self.cutflow      = kwargs.get('cutflow',      'cutflow'    ) # name of the cutflow histogram to get nevents
    self.lumi         = kwargs.get('lumi',         GLOB.lumi    ) # integrated luminosity
    self.norm         = kwargs.get('norm',         None         ) # lumi*xsec/binsumw normalization
    self.scale        = kwargs.get('scale',        1.0          ) # scales factor (e.g. for W+Jets renormalization)
    self.upscale      = kwargs.get('upscale',      1.0          ) # drawing up/down scaling
    self._scale       = self.scale # back up scale to overwrite previous renormalizations
    self.weight       = kwargs.get('weight',       ""           ) # common weights
    self.extraweight  = kwargs.get('extraweight',  ""           ) # extra weights particular to this sample
    self.cuts         = kwargs.get('cuts',         ""           ) # extra cuts particular to this sample
    self.channel      = kwargs.get('channel',      ""           ) # channel
    self.isdata       = kwargs.get('data',         False        ) # flag for observed data
    self.issignal     = kwargs.get('signal',       False        ) # flag for (new physics) signal
    self.isembed      = kwargs.get('embed',        False        ) # flag for embedded sample
    self.isexp        = kwargs.get('exp',          self.isembed ) or not (self.isdata or self.issignal) # background MC (expected SM process)
    self.blinddict    = kwargs.get('blind',        { }          ) # blind data in some given range, e.g. blind={xvar:(xmin,xmax)}
    self.fillcolor    = kwargs.get('color',        None         ) or (kWhite if self.isdata else self.setcolor()) # fill color
    self.linecolor    = kwargs.get('lcolor',       kBlack       ) # line color
    self.tags         = kwargs.get('tags',         [ ]          ) # extra tags to be used for matching of search termsMergedSample
    self.aliases      = kwargs.get('alias',        { }          ) # aliases to be added to tree
    self.branchsels   = kwargs.get('branchsel',    [ ]          ) # branch selections, e.g. ['drop *track*', 'keep track_pt']
    if not isinstance(self.aliases,dict):
      self.aliases[self.aliases[0]] = self.aliases[1] # assume tuple, e.g. alias=('sf',"0.95")
    if not isinstance(self,MergedSample):
      file = ensureTFile(self.filename) # check file
      file.Close()
      if self.isdata:
        self.setnevents(self.binnevts,self.binsumw,cutflow=self.cutflow)
      elif not self.isembed: #self.xsec>=0:
        if self.nevents<0:
          self.setnevents(self.binnevts,self.binsumw,cutflow=self.cutflow) # set nevents and sumweights from cutflow histogram
        if self.sumweights<0:
          self.sumweights = self.nevents # set sumweights to nevents (assume genweight==1)
        if self.norm==None:
          self.normalize(lumi=self.lumi,xsec=self.xsec,sumw=self.sumweights)
    if self.norm==None:
      self.norm = 1.0
  
  def __str__(self):
    """Returns string."""
    return self.name
  
  def __repr__(self):
    """Returns string representation."""
    #return '<%s.%s(%r,%r) at %s>'%(self.__class__.__module__,self.__class__.__name__,self.name,self.title,hex(id(self)))
    return '<%s(%r,%r) at %s>'%(self.__class__.__name__,self.name,self.title,hex(id(self)))
  
  @staticmethod
  def printheader(title=None,merged=True,justname=25,justtitle=25):
    if title!=None:
      print(">>> %s"%(title))
    name   = "Sample name".ljust(justname)
    title  = "title".ljust(justtitle)
    if merged:
      print(">>> \033[4m%s %s %10s %12s %17s %9s  %s\033[0m"%(
                 name,title,"xsec [pb]","nevents","sumweights","norm","weight"+' '*8))
    else:
      print(">>> \033[4m%s %s %s\033[0m"%(name,title+' '*5,"Extra cut"+' '*18))
    
  def printrow(self,**kwargs):
    print(self.row(**kwargs))
  
  def row(self,pre="",indent=0,justname=25,justtitle=25,merged=True,split=True,colpass=False):
    """Returns string that can be used as a row in a samples summary table"""
    name   = self.name.ljust(justname-indent)
    title  = self.title.ljust(justtitle)
    string = ">>> %s%s %s %10.2f %12.1f %17.1f %9.4f  %s"%(
             pre,name,title,self.xsec,self.nevents,self.sumweights,self.norm,self.extraweight)
    if split:
      string += self.splitrows(indent=indent,justname=justname,justtitle=justtitle)
    return string
    
  def splitrows(self,indent=0,justname=25,justtitle=25):
    """Get split rows."""
    string    = ""
    if self.splitsamples:
      justtitle = max(justtitle,max(len(s.title) for s in self.splitsamples)+1)
      for i, sample in enumerate(self.splitsamples):
        name    = sample.name.ljust(justname-indent-3)
        title   = sample.title.ljust(justtitle+3)
        subpre  = ' '*indent+"├─ " if i<len(self.splitsamples)-1 else "└─ "
        string += "\n>>> "+color("%s%s %s %s"%(subpre,name,title,sample.cuts))
    return string
  
  def printobjs(self,title="",file=False):
    """Print all sample objects recursively."""
    if isinstance(self,MergedSample):
      print(">>> %s%r"%(title,self))
      for sample in self.samples:
        sample.printobjs(title+"  ",file=file)
    elif file:
      print(">>> %s%r %s"%(title,self,self.filename))
    else:
      print(">>> %s%r"%(title,self))
    if self.splitsamples:
      print(">>> %s  Split samples:"%(title))
      for sample in self.splitsamples:
        sample.printobjs(title+"    ",file=file)
  
  def get_max_name_len(self,indent=0):
    """Help function for SampleSet.printtable to make automatic columns."""
    if isinstance(self,MergedSample):
      namelens = [len(self.name)]
      for sample in self.samples:
        namelens.append(indent+sample.get_max_name_len(indent=indent+3))
      return max(namelens)
    return indent+len(self.name)
  
  def get_max_title_len(self):
    """Help function for SampleSet.printtable to make automatic columns."""
    if isinstance(self,MergedSample):
      namelens = [len(self.title)]
      for sample in self.samples:
        namelens.append(sample.get_max_title_len())
      return max(namelens)
    return len(self.title)
  
  def getfile(self):
    LOG.verb("Sample.getfile: Opening file %r..."%(self.filename),level=3)
    file = ensureTFile(self.filename)
    return file
  
  def get_file_and_tree(self,**kwargs):
    """Create and return a new TFile and TTree without saving to self for thread safety."""
    verbosity = LOG.getverbosity(kwargs)
    file = self.getfile()
    tree = file.Get(self.treename)
    if not tree or not isinstance(tree,TTree):
      LOG.throw(IOError,'Sample.get_file_and_tree: Could not find tree %r for %r in %s!'%(self.treename,self.name,self.filename))
    setaliases(tree,verb=verbosity-1,**self.aliases)
    selectbranches(tree,self.branchsels,verb=verbosity)
    return file, tree
  
  def getentries_from_tree(self,cut=None):
    file  = self.getfile()
    if cut==None:
      nevts = file.Get(self.treename).GetEntries()
    else:
      nevts = file.Get(self.treename).GetEntries(cut)
    file.Close()
    return nevts
  
  def gethist_from_file(self,hname,tag="",close=True,**kwargs):
    """Get histogram from file. Add histograms together if merged sample."""
    verbosity = LOG.getverbosity(kwargs)
    indent = kwargs.get('indent', ''   )
    incl   = kwargs.get('incl',   True ) # use inclusive sample (if stitched and available)
    scale  = kwargs.get('scale',  1.0  ) # extra scale factor
    mode   = kwargs.get('mode',   None ) # if mode=='sumw': add samples together with normalized weights
    hist   = None
    if verbosity>=2:
      print(">>> Sample.gethist_from_file: %s%r, %r, mode=%r, incl=%r"%(indent,self.name,hname,mode,incl))
    if isinstance(self,MergedSample):
      #print(">>> Sample.getHistFromFile: %sincl=%r, sample_incl=%r"%(indent,incl,self.sample_incl))
      if incl and self.sample_incl: # only get histogram from inclusive sample
        if verbosity>=2:
          print(">>> Sample.gethist_from_file: %sOnly use inclusive sample %r!"%(indent,self.sample_incl.name))
        hist = self.sample_incl.gethist_from_file(hname,tag=tag,indent=indent+"  ",incl=False,verb=verbosity)
        hist.SetDirectory(0)
      else: # add histograms from each sub sample
        samples = self.samples[:]
        sumw = 0 # total sum of weights
        for i, sample in enumerate(samples):
          sumw_ = sample.sumweights or sample.nevents
          if sample.xsec>0 and sumw_>0:
            sumw += sample.xsec/sumw_
        scale *= 1./sumw if sumw>0 and mode=='sumw' else 1.0 # normalize by cross section / sumw
        for sample in samples:
          tag_  = "%s_tmp_%d"%(tag,i)
          hist_ = sample.gethist_from_file(hname,tag=tag_,indent=indent+"  ",mode=mode,incl=incl,scale=scale,verb=verbosity)
          if hist==None:
            hist = hist_.Clone(hname+tag)
            hist.SetDirectory(0)
          elif hist_:
            hist.Add(hist_)
            deletehist(hist_)
    else: # single sample
      file  = self.getfile()
      fname = file.GetPath()
      hist  = file.Get(hname)
      sumw  = self.sumweights or self.nevents
      norm  = self.xsec/sumw if self.xsec>0 and sumw>0 else 1.0
      if hist:
        hist.SetName(hname+tag)
        hist.SetDirectory(0)
      else:
        #print(file, hist)
        LOG.warning("Sample.gethist_from_file: Could not find %r in %s!"%(hname,self.filename))
      if file and close:
        file.Close()
      if hist and mode=='sumw' and norm>0:
        if verbosity>=2:
          print(">>> Sample.gethist_from_file:   %s%r: scale=%s, norm=%s, %s"%(indent,self.name,scale,norm,fname)) #,hist)
          print(">>> Sample.gethist_from_file:   %sbin 5 = %s, xsec=%s, nevts=%s, sumw=%s"%(indent,hist.GetBinContent(5),self.xsec,self.nevents,self.sumweights))
        hist.Scale(scale*norm)
        if verbosity>=2:
          print(">>> Sample.gethist_from_file:   %sbin 5 = %s after normalization"%(indent,hist.GetBinContent(5)))
    return hist
  
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
    verbosity    = LOG.getverbosity(kwargs)
    samename     = kwargs.get('samename', False )
    deep         = kwargs.get('deep',     False ) # deep copy (create new Sample objects)
    splitsamples = [s.clone(samename=samename,deep=deep) for s in self.splitsamples] if deep else self.splitsamples[:]
    if name==None:
      name = self.name + ("" if samename else  "_clone" )
    if title==None:
      title = self.title
    if filename==None:
      filename = self.filename
    kwargs['isdata']        = self.isdata
    kwargs['isembed']       = self.isembed
    kwargs['norm']          = self.norm # prevent automatic norm computation without xsec
    newdict                 = self.__dict__.copy()
    newdict['name']         = name
    newdict['title']        = title
    newdict['splitsamples'] = splitsamples
    newdict['cuts']         = kwargs.get('cuts',   self.cuts      )
    newdict['weight']       = kwargs.get('weight', self.weight    )
    newdict['extraweight']  = kwargs.get('extraweight', self.extraweight )
    newdict['fillcolor']    = kwargs.get('color',  self.fillcolor )
    newsample               = type(self)(name,title,filename,**kwargs)
    newsample.__dict__.update(newdict) # overwrite defaults
    LOG.verb('Sample.clone: name=%r, title=%r, color=%s, cuts=%r, weight=%r'%(
             newsample.name,newsample.title,newsample.fillcolor,newsample.cuts,newsample.weight),verbosity,2)
    return newsample
  
  def appendfilename(self,filetag,nametag=None,titletag=None,**kwargs):
    """Append filename (in front .root)."""
    verbosity     = LOG.getverbosity(kwargs)
    oldfilename   = self.filename
    newfilename   = oldfilename if filetag in oldfilename else oldfilename.replace(".root",filetag+".root")
    LOG.verb('Sample.appendfilename(%r,%r): %r -> %r'%(filetag,titletag,oldfilename,newfilename),verbosity,2)
    self.filename = newfilename
    if nametag==None:
      nametag     = filetag
    if titletag==None:
      titletag    = nametag
    self.name    += nametag
    self.title   += titletag
    if not isinstance(self,MergedSample):
      norm_old    = self.norm
      sumw_old    = self.sumweights
      nevts_old   = self.nevents
      if self.isdata:
        self.setnevents(self.binnevts,self.binsumw,cutflow=self.cutflow)
      if self.isembed:
        pass
      elif self.xsec>=0:
        self.setnevents(self.binnevts,self.binsumw,cutflow=self.cutflow)
        #self.normalize(lumi=self.lumi) # can affect scale computed by stitching
      if reldiff(sumw_old,self.sumweights)>0.02 or reldiff(sumw_old,self.sumweights)>0.02:
        LOG.warn("Sample.appendfilename: file %s has a different number of processed events (sumw=%s, nevts=%s, norm=%s, xsec=%s, lumi=%s) than %s (sumw=%s, nevts=%s, norm=%s)!"%\
                 (self.filename,self.sumweights,self.nevents,self.norm,self.xsec,self.lumi,oldfilename,sumw_old,nevts_old,norm_old))
    elif ':' not in self.filename and not os.path.isfile(self.filename):
      LOG.warn('Sample.appendfilename: file %s does not exist!'%(self.filename))
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.appendfilename(filetag,nametag,titletag,**kwargs)
    for sample in self.splitsamples:
      sample.appendfilename(filetag,nametag,titletag,**kwargs)
  
  def setfilename(self,filename):
    """Set filename."""
    self.filename   = filename
    self.fnameshort = '/'.join(self.filename.split('/')[-3:])
    return self.filename
  
  def __add__(self,sample):
    """Add Sample object to list of samples and return MergedSample."""
    return self.add(sample) # overloaded in MergedSample
  
  def add(self, *args, **kwargs):
    """Add Sample object to list of samples and return MergedSample."""
    samples   = [self]+list(args)
    newsample = MergedSample(kwargs.get('name',self.name),kwargs.get('title',self.title),samples)
    return newsample
  
  def __mul__(self, scale):
    """Multiply scale, or add extra weight (that can be string or Selection object)."""
    if isnumber(scale): # multiply scale
      #self.setscale(scale)
      self.multiplyscale(scale)
    elif isinstance(scale,str): # add extra weight
      self.addextraweight(scale)
    return self
  
  def getcutflow(self,cutflow=None):
    """Get cutflow histogram from file."""
    if not cutflow:
      cutflow = self.cutflow
    file = self.getfile()
    hist = file.Get(cutflow)
    if hist:
      hist.SetDirectory(0)
    else:
      LOG.warn("Sample.getcutflow: Could not find cutflow histogram %r in %s!"%(cutflow,self.filename))
    file.Close()
    return hist
  
  def setnevents(self,binnevts=None,binsumw=None,cutflow=None):
    """Automatically set number of events from the cutflow histogram."""
    if not cutflow:
      cutflow = self.cutflow
    file   = self.getfile()
    cfhist = file.Get(cutflow)
    if binnevts==None: binnevts = self.binnevts
    if binsumw==None:  binsumw  = self.binsumw
    if not cfhist:
      if self.nevents>0:
        if self.sumweights<=0:
          self.sumweights = self.nevents
        LOG.warn("Sample.setnevents: Could not find cutflow histogram %r in %s! nevents=%.1f, sumweights=%.1f"%(cutflow,self.filename,self.nevents,self.sumweights))
      else:
        LOG.throw(IOError,"Sample.setnevents: Could not find cutflow histogram %r in %s!"%(cutflow,self.filename))
    self.nevents    = cfhist.GetBinContent(binnevts)
    self.sumweights = cfhist.GetBinContent(binsumw)
    if self.nevents<=0:
      LOG.warn("Sample.setnevents: Bin %d of %r to retrieve nevents is %s<=0!"
                  "In initialization, please specify the keyword 'binnevts' to select the right bin, or directly set the number of events with 'nevts'."%(binnevts,self.nevents,cutflow))
    if self.sumweights<=0:
      LOG.warn("Sample.setnevents: Bin %d of %r to retrieve sumweights is %s<=0!"
                  "In initialization, please specify the keyword 'binsumw' to select the right bin, or directly set the number of events with 'sumw'."%(binsumw,self.sumweights,cutflow))
      self.sumweights = self.nevents
    if 0<self.nevents<self.nexpevts*0.97: # check for missing events
      LOG.warn('Sample.setnevents: Sample %r has significantly fewer events (%d) than expected (%d).'%(self.name,self.nevents,self.nexpevts))
    return self.nevents
  
  def normalize(self,lumi=None,xsec=None,sumw=None,**kwargs):
    """Calculate and set the normalization for simulation as lumi*xsec/sumw,
    where sumw is the sum of generator event weights."""
    norm     = 1.
    if lumi==None: lumi = self.lumi
    if xsec==None: xsec = self.xsec
    if sumw==None: sumw = self.sumweights or self.nevents
    if self.isdata:
      LOG.warn('Sample.normalize: Ignoring data sample %r'%(self.name))
    elif lumi<=0 or xsec<=0 or sumw<=0:
      LOG.warn('Sample.normalize: Cannot normalize %r: lumi=%s, xsec=%s, sumw=%s'%(self.name,lumi,xsec,sumw))
    else:
      norm = lumi*xsec*1000/sumw # 1000 to convert pb -> fb
      LOG.verb('Sample.normalize: Normalize %r sample to lumi*xsec*1000/sumw = %.5g*%.5g*1000/%.5g = %.5g!'%(self.name,lumi,xsec,sumw,norm),level=2)
    if norm<=0:
      LOG.warn('Sample.normalize: Calculated normalization for %r sample is %.5g <= 0 (lumi=%.5g,xsec=%.5g,nevts=%.5g)!'%(self.name,norm,lumi,xsec,N_events))
    self.norm = norm
    return norm
  
  def multiplyscale(self,scale,**kwargs):
    """Multiply scale, including split samples."""
    verbosity = LOG.getverbosity(kwargs)
    oldscale = self.scale
    newscale = oldscale*scale
    LOG.verb("Sample.multiplyscale: %s, scale %s -> %s"%(self.name,oldscale,newscale),verbosity,level=2)
    self.scale = newscale
    for sample in self.splitsamples:
      sample.scale = newscale
    return newscale
  
  def setscale(self,scale):
    """Set scale, including split samples."""
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
    
  def stylehist(self,hist,**kwargs):
    """Style histogram."""
    if hasattr(hist,'SetFillColor'): # avoid errors in edge cases
      fcolor = kwargs.get('color',  self.fillcolor ) # fill color
      lcolor = kwargs.get('lcolor', self.linecolor ) # line color
      hist.SetLineColor(lcolor)
      hist.SetFillColor(kWhite if self.isdata or self.issignal else fcolor)
      hist.SetMarkerColor(lcolor)
    return hist
  
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
      LOG.verb('Sample.addweight: before: %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
      self.weight = joinweights(self.weight, weight)
      LOG.verb('                  after:  %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
    for sample in self.splitsamples:
        sample.addweight(weight)
  
  def addextraweight(self, weight):
    """Add extra weight. Join with existing weight if it exists."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.addextraweight(weight)
    else:
      LOG.verb('Sample.addextraweight: before: %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
      self.extraweight = joinweights(self.extraweight, weight)
      LOG.verb('                       after:  %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
    for sample in self.splitsamples:
      sample.addextraweight(weight)
    return self.extraweight
  
  def setweight(self, weight, extraweight=False):
    """Set weight, overwriting all previous ones."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.setweight(weight)
    else:
      LOG.verb('Sample.setweight: before: %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
      self.weight = weight
      LOG.verb('                  after:  %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
    for sample in self.splitsamples:
        sample.setweight(weight)
  
  def setextraweight(self, weight):
    """Set extra weight, overwriting all previous ones."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.setextraweight(weight)
    else:
      LOG.verb('Sample.setextraweight: before: %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
      self.extraweight = weight
      LOG.verb('                       after:  %s, weight=%r, extraweight=%r'%(self,self.weight,self.extraweight),level=3)
    for sample in self.splitsamples:
        sample.setextraweight(weight)
  
  def replaceweight(self, oldweight, newweight, **kwargs):
    """Replace weight."""
    verbosity = LOG.getverbosity(kwargs)
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.replaceweight(oldweight,newweight,**kwargs)
    else:
      if oldweight in self.weight:
        LOG.verb('Sample.replaceweight: before %r'%(self.weight),verbosity,2)
        self.weight = self.weight.replace(oldweight,newweight)
        LOG.verb('                      after  %r'%(self.weight),verbosity,2)
      if oldweight in self.extraweight:
        LOG.verb('Sample.replaceweight: before %r'%(self.extraweight),verbosity,2)
        self.extraweight = self.extraweight.replace(oldweight,newweight)
        LOG.verb('                      after  %r'%(self.extraweight),verbosity,2)
  
  def addalias(self, alias, formula, **kwargs):
    """Add alias for TTree."""
    verbosity = LOG.getverbosity(kwargs)
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.addalias(alias,formula,**kwargs)
    else:
      LOG.verb('Sample.addalias: %r: %r -> %r'%(self,alias,formula),verbosity,2)
      self.aliases[alias] = formula
      LOG.verb('Sample.addalias: %r: aliases = %s'%(self,self.aliases),verbosity,4)
  
  def addaliases(self, verb=0, **aliases):
    """Add (dictionary of) aliases for TTree."""
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.addaliases(verb=verb,**aliases)
    else:
      LOG.verb('Sample.addaliases: %r: new aliases = %r'%(self,aliases),verb,2)
      self.aliases.update(aliases)
      LOG.verb('Sample.addaliases: %r: updated aliases = %r'%(self,self.aliases),verb,4)
  
  def split(self,*splitlist,**kwargs):
    """Split sample into different components with some cuts, e.g.
      sample.split(('ZTT',"Real tau","genmatch_2==5"),
                   ('ZJ', "Fake tau","genmatch_2!=5"))
    """
    verbosity    = LOG.getverbosity(kwargs)
    color_dict   = kwargs.get('colors', { }) # dictionary with colors
    splitlist    = unpacklistargs(splitlist)
    splitsamples = [ ]
    for i, info in enumerate(splitlist): #split_dict.items()
      name  = "%s_split%d"%(self.name,i)
      if len(info)>=3:
        name, title, cut = info[:3]
      elif len(info)==2:
        name, cut = info[0], info[1]
        title = sample_titles.get(name,name) # from SampleStyle
      cuts   = joincuts(self.cuts,cut)
      color  = color_dict.get(name,getcolor(name))
      sample = self.clone(name,title,cuts=cuts,color=color) # make clone of self
      #LOG.verb('Sample.clone: name=%r, title=%r, color=%s, cuts=%r, weight=%r'%(
      #         newsample.name,newsample.title,newsample.fillcolor,newsample.cuts,newsample.weight),1)
      splitsamples.append(sample)
    if self.splitsamples:
      LOG.warn(f"Sample.split: Overwriting existing splitsamples! {self.splitsamples} -> {splitsamples}")
    self.splitsamples = splitsamples # save list of split samples
    return splitsamples
  
  def getrdframe(self,variables,selections,**kwargs):
    """Create RDataFrame for list of selections and variables.
    The basic structure is:
    
      rdframe = RDataFrame(treename,filename)
      for selection in selections:
        rdf_sel = rdframe.Filter(selection)
        rdf_sel = rdf_sel.Define("sam_wgt","genweight*idweight*0.23") # common event weight
        for variable in variables:
          rdf_var = rdf_sel.Filter(variable.cut)
          result  = rdf_var.Histo1D(hmodel,variable.name,weight)
          res_dict[selection][variable][self] = result # RDF.RResultPtr<TH1D>
    
    If the histograms should be split into subcomponents of the sample,
    
      rdframe = RDataFrame(treename,filename)
      for selection in selections:
        rdf_sel = rdframe.Filter(selection)
        for sample in subsamples:
          rdf_sam = rdf_sel.Filter(sample.cut) # add sample-specific cut
          rdf_sel = rdf_sel.Define("sam_wgt","genweight*idweight*0.23") # common event weight
          for variable in variables:
            rdf_var = rdf_sam.Filter(variable.cut)
            result  = rdf_var.Histo1D(hmodel,variable.name,weight)
            res_dict[selection][variable][sample] = result # RDF.RResultPtr<TH1D>
    
    The filtered RDF rdf_sel can be reused by a parent MergedSample via rdf_dict.
    In this way the event loop only has to be run once on the same file.
    
    Two-dimensional histograms are allowed if a tuple of two variables are passed:
    
      ...
        for xvar, yvar in variables: # list of 2-tuples which are pairs of Variable objects
          rdf_var = rdf_sel.Filter(xvar.cut)
          result  = rdf_var.Histo2D(hmodel2d,xvar.name,yvar.name,weight)
          res_dict[selection][variable][self] = result # RDF.RResultPtr<TH2D>
      ...
    
    """
    verbosity     = LOG.getverbosity(kwargs)
    name          = kwargs.get('name',     self.name   ) # hist name
    name         += kwargs.get('tag',      ""          ) # tag for hist name
    title         = kwargs.get('title',    self.title  ) # hist title
    norm          = kwargs.get('norm',     True        ) # normalize to cross section
    norm          = self.norm if norm else 1.0
    scale         = kwargs.get('scale',     1.0        ) * self.scale * norm # total scale
    split         = kwargs.get('split',    False       ) and len(self.splitsamples)>=1 # split sample into components (e.g. with cuts on genmatch)
    blind         = kwargs.get('blind',    self.isdata ) # blind data in some given range: self.blinddict={xvar:(xmin,xmax)}
    rdf_dict      = kwargs.get('rdf_dict', None        ) # reuse RDF for the same filename / selection (used for optimizing split MergedSamples)
    task          = kwargs.get('task',     ""          ) # task name for progress bar
    nthreads      = kwargs.get('nthreads', None        ) # number of threads: serial if nthreads==0 or 1, default 8 if nthreads==True
    domean        = kwargs.get('mean',     False       ) # get mean of given variables instead of histograms
    dosumw        = kwargs.get('sumw',     False       ) # get sum of event weights (e.g. for cutflows)
    replaceweight = kwargs.get('replaceweight', None   ) # replace weight, e.g. replaceweight=('idweight_2','idweightUp_2')
    preselection  = kwargs.get('preselect', None       ) # pre-selection string (common pre-filter, before aliases all other selections)
    alias_dict    = self.aliases
    if hasattr(preselection,'selection'): # ensure string
      preselection = preselection.selection
    if 'alias' in kwargs: # update alias dictionary
      alias_dict  = alias_dict.copy()
      alias_dict.update(kwargs['alias'])
    extracuts     = joincuts(kwargs.get('cuts',""),kwargs.get('extracuts',""))
    samples       = self.splitsamples if split else [self]
    rdfkey_main   = (self.treename,self.filename)
    rdfkey_alias  = (self.treename,self.filename,'alias') # for common preselection & aliases
    if verbosity>=1:
      LOG.verb("Sample.getrdframe: Creating RDataFrame for %s ('%s'): %s, split=%r, extracuts=%r, presel=%r"%(
               color(name,'grey',b=True),color(title,'grey',b=True),self.filename,split,extracuts,preselection),verbosity,1)
      LOG.verb("Sample.getrdframe:   Total scale=%.6g (scale=%.6g, norm=%.6g, xsec=%.6g, nevents=%.6g, sumw=%.6g)"%(
               scale,self.scale,self.norm,self.xsec,self.nevents,self.sumweights),verbosity,1)
    
    # SET NTHREADS (NOTE: set before creating RDataFrame!)
    if nthreads!=None:
      RDF.SetNumberOfThreads(nthreads) # see TauFW/common/python/tools/RDataFrame.py
    
    # SELECTIONS
    rdframe = None # main RDataFrame, initialize during iteration if needed
    rdframe_alias = None # RDataFrame with aliases (common for all selections)
    res_dict = ResultDict() # { selection : { variable: { sample: RDF.RResultPtr<TH1D> } } } }
    for selection in selections:
      LOG.verb("Sample.getrdframe:   Selection %r: '%s' (extracuts=%r, sample.cuts=%r)"%(
        selection.filename,color(selection.selection,'grey'),extracuts,self.cuts),verbosity,1)
      
      # PARSE COMMON SELECTION STRING
      cuts = selection.selection
      if rdf_dict==None and extracuts: # if RDataFrame is shared (rdf_dict!=None), extra cuts are applied later
        cuts = joincuts(cuts,extracuts) # apply now to minimize number of filters
      if not split and self.cuts: # if split, extra cuts are applied later per subsample
        cuts = joincuts(cuts,self.cuts) # apply now to minimize number of filters
      
      ##### REUSE RDataFrame to optimize event loop for same file ########################################
      rdfkey_sel = (self.filename,cuts,tuple(variables)) # key for finding common RDataFrame in rdf_dict
      variables_ = [ ] # list of variables filtered for this selection
      expr_dict  = { } # expression -> unique name of RDF column
      if rdf_dict!=None and rdfkey_sel in rdf_dict:
        # NOTE: It is assumed that the variables are correctly filtered and defined in expr_dict
        # NOTE: It is assumed that the preselection & aliases (if any) are exactly the same as defined earlier
        variables_, expr_dict, rdf_sel = rdf_dict[rdfkey_sel] # reuse RDataFrame for same file, selection and variable list
        LOG.verb("Sample.getrdframe:   Reusing RDataFrame %r (cuts=%r)..."%(rdf_sel,cuts),verbosity,2)
      
      ##### CREATE NEW RDataFrame ########################################################################
      else:
        
        # CREATE main RDataFrame
        if rdframe==None:
          if rdf_dict!=None and rdfkey_main in rdf_dict:
            rdframe = rdf_dict[rdfkey_main] # reuse shared RDataFrame for improved performance
          else: # create main RDataFrame common to all selections
            rdframe = RDataFrame(self.treename,self.filename) # save for next iteration on selection
            nevts = self.getentries_from_tree() # get total number of events to process
            RDF.AddProgressBar(rdframe,nevts,(f" ({task})" if task else '')+f": {name}")
            if rdf_dict!=None:
              rdf_dict[rdfkey_main] = rdframe # store for reuse & reporting, etc.
        
        # ADD PRESELECTION & ALIASES to main RDataFrame
        if rdf_dict!=None and rdfkey_alias in rdf_dict:
          rdframe_alias = rdf_dict[rdfkey_alias] # reuse shared RDataFrame (with preselection & aliases) for improved performance
        elif rdframe_alias==None: # create for first time
          rdframe_alias = rdframe
          if preselection: # apply common preselection/filter (before aliases!)
            LOG.verb("Sample.getrdframe:   Adding common preselection %r..."%(preselection),verbosity,1)
            rdframe_alias = rdframe_alias.Filter(preselection)
          for alias, expr in alias_dict.items(): # define aliases as new columns (assume used downstream in selection, variable, and/or weight) !
            rdframe_alias, _ = AddRDFColumn(rdframe_alias,expr,alias,expr_dict=expr_dict,exact=True,verb=verbosity-3)
          if rdf_dict!=None:
            rdf_dict[rdfkey_alias] = rdframe_alias # store for reuse
        
        # SELECTIONS: Add common filter
        rdf_sel = rdframe_alias # RDataFrame specific to this selection (filter)
        if cuts: # add fiter
          #LOG.verb("Sample.getrdframe:   Applying filter for cuts=%r..."%(cuts),verbosity,3)
          rdf_sel = rdf_sel.Filter(cuts,repr(selection.selection))
        
        # VARIABLES: (1) Filter variables, and (2) define common variables
        for variable in variables:
          if isinstance(variable,tuple): # unpack variable pair
            xvar, yvar = variable # for 2D histograms
          else: # assume single Variable object
            xvar = variable # for 1D histgrams
            yvar = None
          
          # 1. FILTER variables for this selection
          plot_var = xvar.plotfor(selection,data=self.isdata,verb=verbosity-4)
          plot_sel = selection.plotfor(xvar,verb=verbosity-4)
          if not plot_var or not plot_sel:
            LOG.verb("Sample.getrdframe:   Ignoring %r (plot_var=%r, plot_sel=%r, isdata=%r)..."%(
                     xvar.name,plot_var,plot_sel,self.isdata),verbosity,4)
            continue # do not plot this variable
          variables_.append(variable) # plot this variable
          
          # 2. COMPILE mathematical expressions & DEFINE unique column name that can be reused,
          #    reuse column name from expr_dict if already defined
          for var in [xvar,yvar]:
            if var==None: continue
            rdf_sel, _ = AddRDFColumn(rdf_sel,var,"_rdf_var",expr_dict=expr_dict,verb=verbosity-3)
        
        if not dosumw and not variables_: # no variables made it past the filters
          LOG.verb("Sample.getrdframe:   No variables! Ignoring...",verbosity,2)
          continue
        if len(expr_dict)>=1:
          LOG.verb("Sample.getrdframe:   Defined columns %s"%(', '.join("%r=%r"%(v,k) for k, v in expr_dict.items())),verbosity,2)
        
        # STORE RDataFrame for reuse
        if rdf_dict!=None and rdfkey_sel not in rdf_dict: # store for first time
          LOG.verb("Sample.getrdframe:   Storing RDataFrame %r (cuts=%r) for reuse..."%(rdf_sel,cuts),verbosity,2)
          rdf_dict[rdfkey_sel] = (variables_,expr_dict,rdf_sel)
      
      ##### CREATED / REUSED RDataFrame ##################################################################
      
      # APPLY EXTRA CUTS if RDataFrame is shared
      if rdf_dict!=None and extracuts:
        LOG.verb("Sample.getrdframe:   Applying filter for extracuts=%r..."%(extracuts),verbosity,1)
        rdf_sel = rdf_sel.Filter(extracuts,"Extra %r"%extracuts)
      
      # RUN over subsamples (to allow for splitting)
      for sample in samples:
        
        # SET SCALE
        scale_ = scale # (extra scales) * (cross section normalization)
        name_  = name
        title_ = title
        if sample!=self:
          name_  = kwargs.get('name',sample.name) + kwargs.get('tag',"")
          title_ = kwargs.get('title',sample.title) # hist title
          if self.scale==sample.scale and self.norm==sample.norm: # exact same scale: omit redundant information to reduce verbosity
            LOG.verb("Sample.getrdframe:   Subsample %s ('%s') with cuts=%r, scale=%.6g (same)"%(
              color(name_,'grey',b=True),color(title_,'grey',b=True),sample.cuts,scale),verbosity,1)
          else: # different scale ! Include full list of scale values for debugging
             norm_  = sample.norm if kwargs.get('norm',True) else 1.0
             scale_ = kwargs.get('scale',1.0)*sample.scale*norm_
             LOG.verb("Sample.getrdframe:   Subsample %s with cuts=%r, scale=%.6g (different: scale=%.6g, norm=%.6g, xsec=%.6g, nevents=%.6g, sumw=%.6g)"%(
               color(sample.name,'grey',b=True),sample.cuts,scale_,sample.scale,sample.norm,sample.xsec,sample.nevents,sample.sumweights),verbosity,1)
        
        # ADD sample-specific CUTS (if split, e.g. by genmatch)
        rdf_sam = rdf_sel # RDataFrame specific to this (sub)sample
        if split: # add filters of sample-specific cuts
          if sample.cuts:
            rdf_sam = rdf_sam.Filter(sample.cuts,"Split %r"%sample.cuts)
          else: # should not happen ! Split samples should always have some cut, otherwise, what is the point? :p
            LOG.warn("Sample.getrdframe: Preparing subsample %r, but no cuts were defined!"%(sample))
        
        # ADD WEIGHTS: common + selection + sample-specific
        # NOTE: key-word 'weight' is also applied to data samples
        wname = "" # weight column name
        wexpr = joinweights(kwargs.get('weight',""),sample.weight,sample.extraweight,selection.weight,scale_)
        if replaceweight: # replace patterns, e.g. replaceweight=('idweight_2','idweightUp_2')
          wexpr = replacepattern(wexpr,replaceweight)
        if wexpr: # if mathematical expression: compile & define column in RDF with unique column name
          rdf_sam, wname = AddRDFColumn(rdf_sam,wexpr,"_rdf_sam_wgt",verb=verbosity-4)
        if wname and verbosity>=1:
          LOG.verb("Sample.getrdframe:   Common/sample/selection weight: %s=%r"%(wname,wexpr),verbosity,1)
        
        # COMPUTE SUM OF WEIGHTS
        res_sumw = None
        if dosumw:
          LOG.verb("Sample.getrdframe:     Booking sum of weights %s=%r"%(wname,wexpr),verbosity,1)
          res_sumw = rdf_sam.Sum(wname) # RDF.RResultPtr<double>
          res_dict.add(selection,'sumw',sample,res_sumw) # add to result dict
        
        # VARIABLES: book histograms
        for variable in variables_:
          if isinstance(variable,tuple): # unpack variable pair
            xvar, yvar = variable # for 2D histograms
            yvar.changecontext(selection,verb=verbosity-2)
            yname = expr_dict.get(yvar.name,yvar.name) # get unique column name for this variable
          else: # assume single Variable object
            xvar  = variable # for 1D histograms
            yvar  = None
            yname = None
          xvar.changecontext(selection,verb=verbosity-2)
          xname = expr_dict.get(xvar.name,xvar.name) # get unique column name for this variable
          
          # PREPARE cuts & weights (only from xvar to keep it simple, ignore yvar's weights & cuts)
          rdf_var = rdf_sam # RDataFrame specific to this variable
          wname2  = wname # column name for total event weight
          if self.isdata: # add data-specific weights, and blinding cuts
            wexpr2  = joinweights(wname,xvar.dataweight) # add variable-specific weight for data
            cut_var = xvar.cut
            if blind:
              blindcuts = xvar.blind(blinddict=self.blinddict) # ensure the cuts match the bin edges
              cut_var = joincuts(xvar.cut,xvar.blindcuts) # add blinding cuts (if applicable)
          else: # add MC-specific weight
            wexpr2  = joinweights(wname,xvar.weight) # add variable-specific weight for MC
            cut_var = xvar.cut
          if cut_var: # add filter to RDataFrame
            rdf_var = rdf_var.Filter(cut_var,"Var %r"%cut_var)
          if wexpr2 and wexpr2!=wname2: # if mathematical expression: compile & define column in RDF with unique column name
            rdf_var, wname2 = AddRDFColumn(rdf_var,wexpr2,"_rdf_var_wgt",verb=verbosity-3) # ensure unique column name
          
          # BOOK MEANs
          if domean:
            if verbosity>=1:
              xvarstr = repr(xvar.name)+("" if xvar.name==xname else " (%r)"%(xname))
              LOG.verb("Sample.getrdframe:     Booking mean of xvar %s with cuts=%r, sumw=%r..."%(
                       xvarstr,cut_var,res_sumw),verbosity,1)
            if dosumw: # to be normalized to sum-of-weights by MergedResults
              mean   = rdf_var.Mean(xname)
              result = MeanResult(mean,res_sumw)
            else:
              result = rdf_var.Mean(xname)
          
          # BOOK 1D histograms
          elif yvar==None:
            hname  = makehistname(xvar,name_) # histogram name
            hmodel = xvar.gethistmodel(hname,title_) # arguments for initiation of an TH1D object (RDF.TH1DModel)
            if verbosity>=1:
              xvarstr = repr(xvar.name)+("" if xvar.name==xname else " (%r)"%(xname))
              wgtstr  = repr(wname2)+("" if wname==wname2 else " (%r)"%(wexpr2))
              LOG.verb("Sample.getrdframe:     Booking hist %r for xvar %s with wgt=%s, cuts=%r..."%(
                       hname,xvarstr,wgtstr,cut_var),verbosity,1)
            if wname2: # apply no weight
              result = rdf_var.Histo1D(hmodel,xname,wname2)
            else: # no weight
              result = rdf_var.Histo1D(hmodel,xname)
          
          # BOOK 2D histograms
          else:
            hname  = makehistname(yvar,'vs',xvar,name_) # histogram name
            hmodel = xvar.gethistmodel2D(yvar,hname,title_) # arguments for initiation of an TH2D object (RDF.TH2DModel)
            if verbosity>=1:
              wgtstr  = repr(wname2)+("" if wname==wname2 else " (%r)"%(wexpr2))
              LOG.verb("Sample.getrdframe:     Booking 2D hist %r for (xvar,yvar)=(%r,%r) with wgt=%s, cuts=%r..."%(
                       hname,xvar.name,yvar.name,wgtstr,cut_var),verbosity,1)
            if wname2: # apply no weight
              result = rdf_var.Histo2D(hmodel,xname,yname,wname2)
            else: # no weight
              result = rdf_var.Histo2D(hmodel,xname,yname)
          
          #print(">>> Sample.getrdframe:     Adding to results: sel={selection!r}, var={variable!r}, sam={sample!r}, res={result!r}")
          res_dict.add(selection,variable,sample,result) # add RDF.RResultPtr<TH1D> to dict
    
    return res_dict
  
  def getsumw(self, *args, **kwargs):
    """Compute sum-of-weights for a given lists of selections
    with RDataFrame and return a dictionary of double values."""
    verbosity = LOG.getverbosity(kwargs)
    LOG.verb("Sample.getsumw: args=%r"%(args,),verbosity,1)
    
    # SUM-OF-WEIGHTS without selections
    if not args:
      if isinstance(self,MergedSample):
        sumw = sum(s.getsumw() for s in self.samples)
        self.sumweights = sumw
      else:
        sumw = self.sumweights
      LOG.verb('Sample.getsumw: %r %.10g'%(self.name,sumw),verbosity,level=2)
      return sumw
    
    # APPLY SELECTIONS
    _, selections, issinglesel = unpack_sellist_args(*args)
    split = kwargs.get('split',False) # split sample into components (e.g. with cuts on genmatch)
    
    # GET & RUN RDATAFRAMES
    kwargs['sumw'] = True
    rdf_dict = kwargs.setdefault('rdf_dict',{ }) # optimization & debugging: reuse RDataFrames for the same filename / selection
    res_dict = self.getrdframe([ ],selections,**kwargs)
    if verbosity>=3: # print RDFs RDF.RResultPtr<double>
      print(">>> Sample.getsumw: Got res_dict:")
      res_dict.display() # print full dictionary
    res_dict.run(graphs=True,rdf_dict=rdf_dict,verb=verbosity)
    
    # CONVERT to & RETURN nested dictionaries of means: { selection: { variable: { sample: float } } }
    single     = (not split) # return { selection: { variable: float } } instead
    hists_dict = res_dict.gethists(single=(not split),style=True,clean=True)
    return hists_dict.results(singlevar=True,singlesel=issinglesel)
  
  def getmean(self, *args, **kwargs):
    """Compute mean of variables and selections with RDataFrame and return a dictionary of histograms."""
    kwargs['mean'] = True
    if isinstance(self,MergedSample):
      kwargs['popvar'] = 'sumw' if kwargs.get('sumw',True) else None # remove 'sumw' from returned dictionary
      kwargs['sumw']   = True # force because the sum-of-weights is needed to sum means correctly
    return self.gethist(*args,**kwargs) # use same function
  
  def gethist(self, *args, **kwargs):
    """Create and fill histograms for given lists of variables and selections
    with RDataFrame and return a dictionary of histograms."""
    verbosity = LOG.getverbosity(kwargs)
    LOG.verb("Sample.gethist: args=%r"%(args,),verbosity,1)
    LOG.verb("Sample.gethist: kwargs=%r"%(kwargs,),verbosity,3)
    if kwargs.get('2d',False): # assume Variable arguments for 2D histograms
      variables, selections, issinglevar, issinglesel = unpack_gethist2D_args(*args)
    else: # assume Variable arguments only for 1D histograms
      variables, selections, issinglevar, issinglesel = unpack_gethist_args(*args)
    split  = kwargs.get('split', False) # split sample into components (e.g. with cuts on genmatch)
    popvar = kwargs.get('popvar',None ) # remove variable from returned dictionary (used by getmean)
    
    # GET & RUN RDATAFRAMES
    rdf_dict = kwargs.setdefault('rdf_dict',{ }) # optimization & debugging: reuse RDataFrames for the same filename / selection
    res_dict = self.getrdframe(variables,selections,**kwargs)
    if verbosity>=3: # print RDFs RResultPtr<TH1>
      print(">>> Sample.gethist: Got res_dict:")
      res_dict.display() # print full dictionary
    res_dict.run(graphs=True,rdf_dict=rdf_dict,verb=verbosity)
    
    # CONVERT to & RETURN nested dictionaries of histograms: { selection: { variable: { sample: TH1 } } }
    single     = (not split) # return { selection: { variable: TH1 } } instead
    hists_dict = res_dict.gethists(single=single,style=True,clean=True)
    if verbosity>=3: # print yields
      hists_dict.display(nvars=(1 if split else -1))
    return hists_dict.results(singlevar=issinglevar,singlesel=issinglesel,popvar=popvar)
  
  def getstack(self, *args, thstack=False, **kwargs):
    """Create and fill histograms for given lists of variables and selections,
    and construct TauFW Stack of sample's subcomponents.
    Return a StackDict of TauFW Stack objects."""
    kwargs['split'] = True # force splitting into subcomponents (e.g. gen-level cuts), if available
    variables, selections, issinglevar, issinglesel = unpack_gethist_args(*args)
    hists_dict = self.gethist(*args, **kwargs) # { selection: { variable: { sample: TH1 } } }
    #histset_dict = HistSetDict.init_from_dict(hists_dict,style=True,clean=False) # convert to HistSetDict as intermediate step
    stacks = StackDict.init_from_HistDict(hists_dict,singlevar=issinglevar,singlesel=issinglesel,thstack=thstack,**kwargs)
    return stacks # return StackDict: { Stack : (Variable, Selection) }
  
  def getTHStack(self, *args, **kwargs):
    """Get THStack of sample's subcomponents. Return StackDict of ROOT THStack objects."""
    kwargs['thstack'] = True
    return self.getstack(*args, **kwargs) # return StackDict: { THStack : (Variable, Selection) }
  
  def gethist2D(self, *args, **kwargs):
    """Create and fill 2D histograms for given lists of variables and selections
    with RDataFrame and return a dictionary of histograms."""
    kwargs['2d'] = True
    return self.gethist(*args,**kwargs) # use same function
  
  def match(self, *terms, **kwargs):
    """Check if search terms match the sample's name, title and/or tags."""
    labels = [self.name,self.title]+self.tags
    return match(terms,labels,**kwargs)
  

def Data(*args,**kwargs):
  kwargs['data'] = True
  kwargs['exp']  = False
  return Sample(*args,**kwargs)
  

def MC(*args,**kwargs):
  kwargs['data'] = False
  kwargs['exp']  = True
  return Sample(*args,**kwargs)
  

from TauFW.Plotter.sample.MergedSample import MergedSample
