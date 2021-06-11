# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.plot.MultiThread import MultiProcessor


class MergedSample(Sample):
  """
  Class to join a list of Sample objects to make one histogram with the Plot class.
  Initialize as
    - MergedSample(str name)
    - MergedSample(str name, str title)
    - MergedSample(str name, list samples)
    - MergedSample(str name, str title, list samples)
  """
  
  def __init__(self, *args, **kwargs):
    name, title, samples = unwrap_MergedSamples_args(*args,**kwargs)
    Sample.__init__(self,name,title,"",**kwargs)
    self.samples = samples
    if self.samples:
      self.init(samples[0],**kwargs)
  
  def init(self, sample, **kwargs):
    """Set some relevant attributes (inherited from the Sample class) with a given sample."""
    self.filename     = sample.filename
    self.treename     = sample.treename
    self.isdata       = sample.isdata
    self.isembed      = sample.isembed
    self.isexp        = sample.isexp
    self.issignal     = sample.issignal
    self.lumi         = sample.lumi
    self.cutflow      = sample.cutflow
    self.fillcolor    = kwargs.get('color',    self.fillcolor) or sample.fillcolor
    self.linecolor    = kwargs.get('linecolor',self.linecolor) or sample.linecolor
  
  def __len__(self):
    """Return number of samples."""
    return len(self.samples)
  
  def __iter__(self):
    """Start iteration over samples."""
    for sample in self.samples:
      yield sample
  
  def __add__(self,sample):
    """Start iteration over samples."""
    self.add(sample)
  
  def add(self, sample, **kwargs):
    """Add Sample object to list of samples."""
    if not self.samples:
      self.init(sample)
    self.samples.append(sample)
  
  def row(self,pre="",indent=0,justname=25,justtitle=25,merged=True,split=True,colpass=False):
    """Returns string that can be used as a row in a samples summary table."""
    xsec     = "%.2f"%self.xsec if self.xsec>0 else ""
    nevts    = "%.1f"%self.nevents if self.nevents>=0 else ""
    sumw     = "%.1f"%self.sumweights if self.sumweights>=0 else ""
    norm     = "%.4f"%self.norm
    split_   = split and len(self.splitsamples)>0
    name     = self.name.ljust(justname-indent)
    title    = self.title.ljust(justtitle)
    if merged:
      string = ">>> %s%s %s %10s %12s %17s %9s  %s" %\
               (pre,name,title,xsec,nevts,sumw,norm,self.extraweight)
      if "├─ " in pre or "└─ " in pre or indent==0:
        pline = color("│  ") if colpass else "│  " # line passing merged samples
        subpre = pre.replace("├─ ",pline).replace("└─ ",' '*3)
      else:
        subpre = pre+' '*3
      #print "indent=%r, pre=%r, subpre=%r, split_=%r, colpass=%r"%(indent,pre,subpre,split_,colpass)
      for i, sample in enumerate(self.samples):
        islast   = i+1>=len(self.samples)
        subpre_  = subpre + ("└─ " if (islast and not split_) else "├─ ")
        colpass_ = split_ and islast
        #print "i=%r, subpre_=%r, islast=%r, colpass_=%r"%(i,subpre_,islast,colpass_)
        string  += "\n" + sample.row(pre=subpre_,indent=indent+3,justname=justname,justtitle=justtitle,split=split,colpass=colpass_)
    else:
      string = ">>> %s%s %s"%(pre,name,title)
    if split_:
      string += self.splitrows(indent=indent,justname=justname,justtitle=justtitle)
    return string
  
  def clone(self,*args,**kwargs):
    """Shallow copy."""
    samename     = kwargs.get('samename', False )
    deep         = kwargs.get('deep',     False )
    close        = kwargs.get('close',    False )
    #samples      = kwargs.get('samples',  False )
    strings      = [a for a in args if isinstance(a,str)]
    name         = args[0] if len(args)>0 else self.name + ("" if samename else  "_clone" )
    title        = args[1] if len(args)>1 else self.title+ ("" if samename else " (clone)")
    samples      = [s.clone(samename=samename,deep=deep) for s in self.samples] if deep else self.samples[:]
    splitsamples = [ ]
    for oldsplitsample in self.splitsamples:
      if deep:
        newsplitsample = oldsplitsample.clone(samename=samename,deep=deep)
        if isinstance(newsplitsample,MergedSample):
          # splitsamples.samples should have same objects as self.samples !!!
          for subsample in oldsplitsample.samples:
            if subsample in self.samples:
              newsplitsample.samples[oldsplitsample.samples.index(subsample)] = samples[self.samples.index(subsample)]
        splitsamples.append(newsplitsample)
      else:
        splitsamples.append(oldsplitsample)
    newdict                 = self.__dict__.copy()
    newdict['name']         = name
    newdict['title']        = title
    newdict['samples']      = samples
    newdict['splitsamples'] = splitsamples
    newdict['cuts']         = kwargs.get('cuts',   self.cuts      )
    newdict['weight']       = kwargs.get('weight', self.weight    )
    newdict['extraweight']  = kwargs.get('extraweight', self.extraweight )
    newdict['fillcolor']    = kwargs.get('color',  self.fillcolor )
    newsample               = type(self)(name,title,*samples,**kwargs)
    newsample.__dict__.update(newdict)
    if close:
      newsample.close()
    LOG.verb('MergedSample.clone: name=%r, title=%r, color=%s, cuts=%r, weight=%r'%(
             newsample.name,newsample.title,newsample.fillcolor,newsample.cuts,newsample.weight),level=2)
    return newsample
  
  def getcutflow(self,cutflow=None):
    """Get cutflow histogram from file."""
    if not cutflow:
      cutflow = self.cutflow()
    cfhist = None
    for sample in self.samples:
      hist  = sample.getcutflow()
      if not hist: continue
      scale = sample.norm*sample.scale*sample.upscale
      if cfhist:
        cfhist.Add(hist,scale)
      else:
        cfhist = hist.Clone('cutflow_total')
        cfhist.Scale(scale)
      deletehist(hist)
    if not cfhist:
      LOG.warning("MergedSample.getcutflow: Could not find cutflow histogram %r for %s!"%(cutflow,sample))
    return cfhist
  
  def getentries(self, selection, **kwargs):
    """Get number of events for a given selection string."""
    verbosity          = LOG.getverbosity(kwargs)
    norm               = kwargs.get('norm', True ) # normalize to cross section
    norm               = self.norm if norm else 1.
    parallel           = kwargs.get('parallel',       False                )
    kwargs['cuts']     = joincuts(kwargs.get('cuts'), self.cuts            )
    kwargs['weight']   = joinweights(kwargs.get('weight', ""), self.weight ) # pass weight down
    kwargs['scale']    = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
    kwargs['parallel'] = False
    
    # GET NUMBER OF EVENTS
    nevents = 0
    if parallel and len(self.samples)>1:
      processor = MultiProcessor()
      for sample in self.samples:
        processor.start(sample.getentries,(selection,),kwargs)        
      for process in processor:
        nevents += process.join()
    else:
      for sample in self.samples:
        nevents += sample.getentries(selection,**kwargs)
    
    # PRINT
    if verbosity>=3:
      print ">>>\n>>> MergedSample.getentries: %s"%(color(self.name,color="grey"))
      print ">>>   entries: %d"%(nevents)
      print ">>>   scale: %.6g (scale=%.6g, norm=%.6g)"%(scale,self.scale,self.norm)
      print ">>>   %r"%(cuts)
    
    return nevents
  
  def gethist(self, *args, **kwargs):
    """Create and fill histgram for multiple samples. Overrides Sample.gethist."""
    variables, selection, issingle = unwrap_gethist_args(*args)
    verbosity        = LOG.getverbosity(kwargs)
    name             = kwargs.get('name',           self.name            )
    name            += kwargs.get('tag',            ""                   )
    title            = kwargs.get('title',          self.title           )
    parallel         = kwargs.get('parallel',       False                )
    kwargs['cuts']   = joincuts(kwargs.get('cuts'), self.cuts            )
    kwargs['weight'] = joinweights(kwargs.get('weight', ""), self.weight ) # pass weight down
    kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
    
    # HISTOGRAMS
    allhists = [ ]
    hargs    = (variables, selection)
    hkwargs  = kwargs.copy()
    if parallel and len(self.samples)>1:
      hkwargs['parallel'] = False
      processor = MultiProcessor()
      for sample in self.samples:
        processor.start(sample.gethist,hargs,hkwargs,name=sample.title)        
      for process in processor:
        allhists.append(process.join())
    else:
      for sample in self.samples:
        if 'name' in kwargs: # prevent memory leaks
          hkwargs['name']  = makehistname(kwargs.get('name',""),sample.name)
        allhists.append(sample.gethist(*hargs,**hkwargs))
    
    # SUM
    sumhists = [ ]
    if any(len(subhists)<len(variables) for subhists in allhists):
      LOG.error("MergedSample.gethist: len(subhists) = %s < %s = len(variables)"%(len(subhists),len(variables)))
    for ivar, variable in enumerate(variables):
      subhists = [subhists[ivar] for subhists in allhists]
      sumhist  = None
      for subhist in subhists:
        if sumhist==None:
          sumhist = subhist.Clone(makehistname(variable.filename,name))
          sumhist.SetTitle(title)
          sumhist.SetDirectory(0)
          sumhist.SetLineColor(self.linecolor)
          sumhist.SetFillColor(kWhite if self.isdata or self.issignal else self.fillcolor)
          sumhist.SetMarkerColor(self.fillcolor)
          sumhists.append(sumhist)
        else:
          sumhist.Add(subhist)
      if verbosity>=4:
        printhist(sumhist,pre=">>>   ")
      deletehist(subhists)
    
    # PRINT
    if verbosity>=2:
      nentries, integral = -1, -1
      for sumhist in sumhists:
        if sumhist.GetEntries()>nentries:
          nentries = sumhist.GetEntries()
          integral = sumhist.Integral()
      print ">>>\n>>> MergedSample.gethist - %s"%(color(name,color="grey"))
      print ">>>    entries: %d (%.2f integral)"%(nentries,integral)
    
    if issingle:
      return sumhists[0]
    return sumhists
  
  def gethist2D(self, *args, **kwargs):
    """Create and fill 2D histgram for multiple samples. Overrides Sample.gethist2D."""
    variables, selection, issingle = unwrap_gethist2D_args(*args)
    verbosity        = LOG.getverbosity(kwargs)
    name             = kwargs.get('name',               self.name+"_merged" )
    name            += kwargs.get('tag',                ""                  )
    title            = kwargs.get('title',              self.title          )
    parallel         = kwargs.get('parallel',           False                )
    kwargs['cuts']   = joincuts(kwargs.get('cuts'),     self.cuts           )
    kwargs['weight'] = joinweights(kwargs.get('weight', ""), self.weight    ) # pass scale down
    kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
    if verbosity>=2:
      print ">>>\n>>> MergedSample.gethist2D: %s: %s"%(color(name,color="grey"), self.fnameshort)
      #print ">>>    norm=%.4f, scale=%.4f, total %.4f"%(self.norm,kwargs['scale'],self.scale)
    
    # HISTOGRAMS
    allhists = [ ]
    hargs    = (variables, selection)
    hkwargs  = kwargs.copy()
    if parallel and len(self.samples)>1:
      hkwargs['parallel'] = False
      processor = MultiProcessor()
      for sample in self.samples:
        processor.start(sample.gethist2D,hargs,hkwargs,name=sample.title)        
      for process in processor:
        allhists.append(process.join())
    else:
      for sample in self.samples:
        if 'name' in kwargs: # prevent memory leaks
          hkwargs['name']  = makehistname(kwargs.get('name',""),sample.name)
        allhists.append(sample.gethist2D(*hargs,**hkwargs))
    
    # SUM
    sumhists = [ ]
    if any(len(subhists)<len(variables) for subhists in allhists):
      LOG.error("MergedSample.gethist2D: len(subhists) = %s < %s = len(variables)"%(len(subhists),len(variables)))
    for ivar, (xvariable,yvariable) in enumerate(variables):
      subhists = [subhists[ivar] for subhists in allhists]
      sumhist  = None
      for subhist in subhists:
        if sumhist==None:
          hname = makehistname("%s_vs_%s"%(xvariable.filename,yvariable.filename),name)
          sumhist = subhist.Clone(hname)
          sumhist.SetTitle(title)
          sumhist.SetDirectory(0)
          sumhist.SetLineColor(self.linecolor)
          sumhist.SetFillColor(kWhite if self.isdata or self.issignal else self.fillcolor)
          sumhist.SetMarkerColor(self.fillcolor)
          sumhists.append(sumhist)
        else:
          sumhist.Add(subhist)
      if verbosity>=4:
        printhist(sumhist,pre=">>>   ")
      deletehist(subhists)
    
    if issingle:
      return sumhists[0]
    return sumhists
  

def unwrap_MergedSamples_args(*args,**kwargs):
  """
  Help function to unwrap arguments for MergedSamples initialization:
    MergedSample(str name)
    MergedSample(str name, str title)
    MergedSample(str name, list samples)
    MergedSample(str name, str title, list samples)
  where samples is a list of Sample objects.
  Returns a sample name, title and a list of Sample objects:
    (str name, str, title, list samples)
  """
  strings = [ ]
  name    = "noname"
  title   = ""
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
    name = strings[0]
  elif len(strings)>1:
    name, title = strings[:2]
  elif len(samples)>1:
    name, title = '-'.join([s.name for s in samples]), ', '.join([s.title for s in samples])
  LOG.verb("unwrap_MergedSamples_args: name=%r, title=%r, samples=%s"%(name,title,samples),level=3)
  return name, title, samples
  
