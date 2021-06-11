# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
import os, re
from TauFW.Plotter.sample.utils import *
from TauFW.common.tools.math import round2digit, reldiff
from TauFW.Plotter.plot.string import *
from TauFW.Plotter.plot.utils import deletehist, printhist
from TauFW.Plotter.sample.SampleStyle import *
from TauFW.Plotter.plot.MultiDraw import MultiDraw
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
    LOG.setverbosity(kwargs)
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
    self.fnameshort   = os.path.basename(self.filename) # short file name for printing
    self._file        = None                            # TFile file
    self._tree        = None                            # TTree tree
    self.samples      = [self]                          # same as MergedSample
    self.splitsamples = [ ]                             # samples when splitting into subsamples
    self.treename     = kwargs.get('tree',         None         ) or 'tree'
    self.nevents      = kwargs.get('nevts',        nevts        ) # "raw" number of events
    self.nexpevts     = kwargs.get('nexp',         -1           ) # number of events you expect to be processed for check for missing events
    self.sumweights   = kwargs.get('sumw',         self.nevents ) # sum (generator) weights
    self.binnevts     = kwargs.get('binnevts',     None         ) or 1  # cutflow bin with total number of (unweighted) events
    self.binsumw      = kwargs.get('binsumw',      None         ) or 17 # cutflow bin with total sum of weight
    self.cutflow      = kwargs.get('cutflow',      'cutflow'    ) # name of the cutflow histogram to get nevents
    self.lumi         = kwargs.get('lumi',         GLOB.lumi    ) # integrated luminosity
    self.norm         = kwargs.get('norm',         None         ) # lumi*xsec/binsumw normalization
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
    self.fillcolor    = kwargs.get('color',        None         ) or (kBlack if self.isdata else self.setcolor()) # fill color
    self.linecolor    = kwargs.get('lcolor',       kBlack       ) # line color
    self.tags         = kwargs.get('tags',         [ ]          ) # extra tags to be used for matching of search terms
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
      print ">>> %s"%(title)
    name   = "Sample name".ljust(justname)
    title  = "title".ljust(justtitle)
    if merged:
      print ">>> \033[4m%s %s %10s %12s %17s %9s  %s\033[0m"%(
                 name,title,"xsec [pb]","nevents","sumweights","norm","weight"+' '*8)
    else:
      print ">>> \033[4m%s %s %s\033[0m"%(name,title+' '*5,"Extra cut"+' '*18)
    
  
  def printrow(self,**kwargs):
    print self.row(**kwargs)
  
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
      print ">>> %s%r"%(title,self)
      for sample in self.samples:
        sample.printobjs(title+"  ",file=file)
    elif file:
      print ">>> %s%r %s"%(title,self,self.filename)
    else:
      print ">>> %s%r"%(title,self)
    if self.splitsamples:
      print ">>> %s  Split samples:"%(title)
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
  
  @property
  def file(self):
    return self.getfile()
  
  @file.setter
  def file(self, value):
    self._file = value
  
  def getfile(self,refresh=False):
    if not self._file:
      LOG.verb("Sample.getfile: Opening file %s..."%(self.filename),level=3)
      self._file = ensureTFile(self.filename)
    elif refresh:
      LOG.verb("Sample.getfile: Closing and opening file %s..."%(self.filename),level=3)
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
      LOG.verb("Sample.tree: Opening file %s to get tree %r..."%(self.filename,self.treename),level=3)
      self._tree = self.file.Get(self.treename)
    elif self._tree and isinstance(self._tree,TTree):
      LOG.verb("Sample.tree: Getting existing tree %s..."%(self._tree),level=3)
    else:
      LOG.verb("Sample.tree: No valid tree (%s). Retrieving tree %r from file %s..."%(self._tree,self.treename,self.filename),level=3)
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
    verbosity    = LOG.getverbosity(kwargs)
    samename     = kwargs.get('samename', False )
    deep         = kwargs.get('deep',     False ) # deep copy
    close        = kwargs.get('close',    False ) # keep new sample closed for memory space
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
    if deep and self.file: # force new, separate file
      newdict['file'] = None #ensureTFile(self.file.GetName())
    newsample               = type(self)(name,title,filename,**kwargs)
    newsample.__dict__.update(newdict) # overwrite defaults
    LOG.verb('Sample.clone: name=%r, title=%r, color=%s, cuts=%r, weight=%r'%(
             newsample.name,newsample.title,newsample.fillcolor,newsample.cuts,newsample.weight),verbosity,2)
    if close:
      newsample.close()
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
    if self.file:
      self.file.Close()
      self.file   = ensureTFile(self.filename)
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
        LOG.warning('Sample.appendfilename: file %s has a different number of events (sumw=%s, nevts=%s, norm=%s, xsec=%s, lumi=%s) than %s (N=%s, N_unw=%s, norm=%s)! '%\
          (self.filename,self.sumweights,self.nevents,self.norm,self.xsec,self.lumi,oldfilename,sumw_old,nevts_old,norm_old))
    elif ':' not in self.filename and not os.path.isfile(self.filename):
      LOG.warning('Sample.appendfilename: file %s does not exist!'%(self.filename))
    if isinstance(self,MergedSample):
      for sample in self.samples:
        sample.appendfilename(filetag,nametag,titletag,**kwargs)
    for sample in self.splitsamples:
      sample.appendfilename(filetag,nametag,titletag,**kwargs)
  
  def setfilename(self,filename):
    """Set filename."""
    self.filename = filename
    self.fnameshort  = '/'.join(self.filename.split('/')[-2:])
    return self.filename
  
  def reload(self,**kwargs):
    """Close and reopen file. Use it to free up and clean memory."""
    verbosity = LOG.getverbosity(kwargs)
    if self.file:
      if verbosity>=4:
        print "Sample.reload: closing and deleting %s with content:"%(self.file.GetName())
        self.file.ls()
      self.file.Close()
      del self._file
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
      if verbosity>=4:
        print "Sample.close: closing and deleting %s with content:"%(self.file.GetName())
        self.file.ls()
      self.file.Close()
      del self._file
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
  
  def getcutflow(self,cutflow=None):
    """Get cutflow histogram from file."""
    if not cutflow:
      cutflow = self.cutflow
    file = self.getfile()
    hist = file.Get(cutflow)
    if hist:
      hist.SetDirectory(0)
    else:
      LOG.warning("Sample.getcutflow: Could not find cutflow histogram %r in %s!"%(cutflow,self.filename))
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
        LOG.warning("Sample.setnevents: Could not find cutflow histogram %r in %s! nevents=%.1f, sumweights=%.1f"%(cutflow,self.filename,self.nevents,self.sumweights))
      else:
        LOG.throw(IOError,"Sample.setnevents: Could not find cutflow histogram %r in %s!"%(cutflow,self.filename))
    self.nevents    = cfhist.GetBinContent(binnevts)
    self.sumweights = cfhist.GetBinContent(binsumw)
    if self.nevents<=0:
      LOG.warning("Sample.setnevents: Bin %d of %r to retrieve nevents is %s<=0!"
                  "In initialization, please specify the keyword 'binnevts' to select the right bin, or directly set the number of events with 'nevts'."%(binnevts,self.nevents,cutflow))
    if self.sumweights<=0:
      LOG.warning("Sample.setnevents: Bin %d of %r to retrieve sumweights is %s<=0!"
                  "In initialization, please specify the keyword 'binsumw' to select the right bin, or directly set the number of events with 'sumw'."%(binsumw,self.sumweights,cutflow))
      self.sumweights = self.nevents
    if 0<self.nevents<self.nexpevts*0.97: # check for missing events
      LOG.warning('Sample.setnevents: Sample %r has significantly fewer events (%d) than expected (%d).'%(self.name,self.nevents,self.nexpevts))
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
  
  def split(self,*splitlist,**kwargs):
    """Split sample into different components with some cuts, e.g.
      sample.split(('ZTT',"Real tau","genmatch_2==5"),
                   ('ZJ', "Fake tau","genmatch_2!=5"))
    """
    verbosity    = LOG.getverbosity(kwargs)
    color_dict   = kwargs.get('colors', { }) # dictionary with colors
    splitlist    = unwraplistargs(splitlist)
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
    self.splitsamples = splitsamples # save list of split samples
    return splitsamples
  
  def getentries(self, selection, **kwargs):
    """Get number of events for a given selection string."""
    verbosity  = LOG.getverbosity(kwargs)
    norm       = kwargs.get('norm', True ) # normalize to cross section
    norm       = self.norm if norm else 1.
    scale      = kwargs.get('scale', 1.0 ) * self.scale * norm # pass False or 0 for no scaling of MC events
    if not isinstance(selection,Selection):
      selection = Selection(selection)
    if self.isdata:
      weight = joinweights(self.weight,self.extraweight,kwargs.get('weight',""))
    else:
      weight = joinweights(selection.weight,self.weight,self.extraweight,kwargs.get('weight',""))
    cuts     = joincuts(selection.selection,self.cuts,kwargs.get('cuts',""),kwargs.get('extracuts',""))
    cuts = joincuts(cuts,weight=weight)
    
    # GET NUMBER OF EVENTS
    file, tree = self.get_newfile_and_tree() # create new file and tree for thread safety
    nevents    = tree.GetEntries(cuts)
    if scale:
     nevents  *= scale
    file.Close()
    
    # PRINT
    if verbosity>=3:
      print ">>>\n>>> Sample.getentries: %s, %s"%(color(self.name,color="grey"),self.fnameshort)
      print ">>>   entries: %d"%(nevents)
      print ">>>   scale: %.6g (scale=%.6g, norm=%.6g)"%(scale,self.scale,self.norm)
      print ">>>   %r"%(cuts)
    
    return nevents
  
  def gethist(self, *args, **kwargs):
    """Create and fill a histogram from a tree."""
    variables, selection, issingle = unwrap_gethist_args(*args)
    verbosity  = LOG.getverbosity(kwargs)
    norm       = kwargs.get('norm',     True           ) # normalize to cross section
    norm       = self.norm if norm else 1
    scale      = kwargs.get('scale',    1.0            ) * self.scale * norm
    name       = kwargs.get('name',     self.name      ) # hist name
    name      += kwargs.get('tag',      ""             ) # tag for hist name
    title      = kwargs.get('title',    self.title     ) # hist title
    blind      = kwargs.get('blind',    self.isdata    ) # blind data in some given range, e.g. blind={xvar:(xmin,xmax)}
    fcolor     = kwargs.get('color',    self.fillcolor ) # fill color
    lcolor     = kwargs.get('lcolor',   self.linecolor ) # line color
    replaceweight = kwargs.get('replaceweight', None ) # replace weight, e.g. replaceweight=('idweight_2','idweightUp_2')
    undoshifts = self.isdata and (any('Up' in v.name or 'Down' in v.name for v in variables)
                                  or 'Up' in selection or 'Down' in selection)
    undoshifts = kwargs.get('undoshifts', undoshifts   ) # remove up/down from variable names
    drawopt = 'E0' if self.isdata else 'HIST'
    drawopt = kwargs.get('option', drawopt ) + 'gOff'
    
    # SELECTION STRING & WEIGHTS
    if self.isdata:
      weight = joinweights(self.weight,self.extraweight,kwargs.get('weight',""))
    else:
      weight = joinweights(selection.weight,self.weight,self.extraweight,kwargs.get('weight',""))
    cuts = joincuts(selection.selection,self.cuts,kwargs.get('cuts',""),kwargs.get('extracuts',""))
    if undoshifts: # remove up/down from variable names in selection string
      cuts = undoshift(cuts)
    if replaceweight:
      if len(replaceweight) in [2,3] and not islist(replaceweight[0]):
        replaceweight = [replaceweight]
      for wargs in replaceweight:
        if len(wargs)>=3:
          pattern, newweight, regexp = wargs[:3]
        else:
          pattern, newweight, regexp = wargs[0], wargs[1], False
        LOG.verb('Sample.gethist: replacing weight: before %r'%weight,verbosity,3)
        if regexp:
          weight = re.sub(pattern,newweight,weight)
        else:
          weight = weight.replace(pattern,newweight)
        weight = weight.replace("**","*").strip('*')
        LOG.verb('Sample.gethist: replacing weight: after  %r'%weight,verbosity,3)
    cuts = joincuts(cuts,weight=weight)
    
    # PREPARE HISTOGRAMS
    hists   = [ ]
    varexps = [ ]
    for variable in variables:
      
      # VAREXP
      hname  = makehistname(variable,name) # $VAR_$NAME
      varcut = ""
      if self.isdata and (blind or variable.blindcuts or variable.cut or variable.dataweight):
        blindcuts = ""
        if blind:
          if isinstance(blind,tuple) and len(blind)==2:
            blindcuts = variable.blind(*blind)
          elif variable._name in self.blinddict:
            blindcuts = variable.blind(*self.blinddict[variable._name])
          elif variable.blindcuts:
            blindcuts = variable.blindcuts
        varcut = joincuts(blindcuts,variable.cut,weight=variable.dataweight)
      elif not self.isdata and (variable.cut or variable.weight):
        varcut = joincuts(variable.cut,weight=variable.weight)
      if varcut:
        varexp = (variable.drawcmd(hname,undoshift=undoshifts),varcut)
      else:
        varexp = variable.drawcmd(hname,undoshift=undoshifts)
      varexps.append(varexp)
      
      # HISTOGRAM
      hist = variable.gethist(hname,title,sumw2=(not self.isdata),poisson=self.isdata)
      hist.SetDirectory(0)
      hists.append(hist)
    
    # FILL HISTOGRAMS
    LOG.insist(len(variables)==len(varexps)==len(hists),
               "Number of variables (%d), variable expressions (%d) and histograms (%d) must be equal!"%(len(variables),len(varexps),len(hists)))
    if varexps:
      try:
        file, tree = self.get_newfile_and_tree() # create new file and tree for thread safety
        out = tree.MultiDraw(varexps,cuts,drawopt,hists=hists)
        file.Close()
      except KeyboardInterrupt:
        LOG.throw(KeyboardInterrupt,"Interrupted Sample.gethist for %r (%d histogram%s)"%(self.name,len(varexps),'' if len(varexps)==1 else 's'))
    
    # FINISH
    nentries = 0
    integral = 0
    for variable, hist in zip(variables,hists):
      if scale!=1.0:   hist.Scale(scale)
      if scale==0.0:   LOG.warning("Scale of %s is 0!"%self.name)
      hist.SetLineColor(lcolor)
      hist.SetFillColor(kWhite if self.isdata or self.issignal else fcolor)
      hist.SetMarkerColor(lcolor)
      if hist.GetEntries()>nentries:
        nentries = hist.GetEntries()
        integral = hist.Integral()
    
    # PRINT
    if verbosity>=3:
      print ">>>\n>>> Sample.gethist: %s, %s"%(color(self.name,color="grey"),self.fnameshort)
      print ">>>   entries: %d (%.2f integral)"%(nentries,integral)
      print ">>>   scale: %.6g (scale=%.6g, norm=%.6g)"%(scale,self.scale,self.norm)
      print ">>>   %r"%(cuts)
      if verbosity>=4:
        for var, varexp, hist in zip(variables,varexps,hists):
          print '>>>   Variable %r: varexp=%r, entries=%d, integral=%d'%(var.name,varexp,hist.GetEntries(),hist.Integral())
          #print '>>>   Variable %r: cut=%r, weight=%r, varexp=%r'%(var.name,var.cut,var.weight,varexp)
          if verbosity>=5:
            printhist(hist,pre=">>>   ")
      
    
    if issingle:
      return hists[0]
    return hists
  
  def gethist2D(self, *args, **kwargs):
    """Create and fill a 2D histogram from a tree."""
    variables, selection, issingle = unwrap_gethist2D_args(*args)
    verbosity = LOG.getverbosity(kwargs)
    scale     = kwargs.get('scale', 1.0        ) * self.scale * self.norm
    name      = kwargs.get('name',  self.name  )
    name     += kwargs.get('tag',   ""         )
    title     = kwargs.get('title', self.title )
    drawopt   = 'COLZ'
    drawopt   = 'gOff'+kwargs.get('option', drawopt    )
    
    # CUTS
    if self.isdata:
      weight  = joinweights(self.weight,self.extraweight,kwargs.get('weight',""))
    else:
      weight  = joinweights(selection.weight,self.weight,self.extraweight,kwargs.get('weight',""))
    cuts      = joincuts(selection.selection,self.cuts,kwargs.get('cuts',""),kwargs.get('extracuts',""),weight=weight)
    
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
    LOG.insist(len(variables)==len(varexps)==len(hists),
               "Number of variables (%d), variable expressions (%d) and histograms (%d) must be equal!"%(len(variables),len(varexps),len(hists)))
    if varexps:
      try:
        file, tree = self.get_newfile_and_tree() # create new file and tree for thread safety
        out = tree.MultiDraw(varexps,cuts,drawopt,hists=hists)
        file.Close()
      except KeyboardInterrupt:
        LOG.throw(KeyboardInterrupt,"Interrupted Sample.gethist for %r (%d histogram%s)"%(self.name,len(varexps),'' if len(varexps)==1 else 's'))
    
    # FINISH
    nentries = 0
    integral = 0
    for variable, hist in zip(variables,hists):
      if scale!=1.0:   hist.Scale(scale)
      if scale==0.0:   LOG.warning("Scale of %s is 0!"%self.name)
      if hist.GetEntries()>nentries:
        nentries = hist.GetEntries()
        integral = hist.Integral()
    
    # PRINT
    if verbosity>=2:
      print ">>>\n>>> Sample.gethist2D - %s: %s"%(color(name,color="grey"),self.fnameshort)
      print ">>>   scale: %.6g (scale=%.6g, norm=%.6g)"%(scale,self.scale,self.norm)
      print ">>>   entries: %d (%.2f integral)"%(nentries,integral)
      print ">>>   %s"%cuts
      if verbosity>=4:
        for var, varexp, hist in zip(variables,varexps,hists):
          print '>>>   Variables (%r,%r): varexp=%r, entries=%d, integral=%d'%(var[0].name,var[1].name,varexp,hist.GetEntries(),hist.Integral())
          #print '>>>   Variable %r: cut=%r, weight=%r, varexp=%r'%(var.name,var.cut,var.weight,varexp)
          if verbosity>=5:
            printhist(hist,pre=">>>   ")
    
    if issingle:
      return hists[0]
    return hists
  
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
