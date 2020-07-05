# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
#import os, re
#from TauFW.Plotter.plot.Variable import Variable
#from TauFW.Plotter.sample.SampleStyle import *
from TauFW.Plotter.sample.Sample import *
#from ROOT import TTree


class MergedSample(Sample):
  """Class to join a list of Sample objects to make one histogram with the Plot class."""
  
  def __init__(self, *args, **kwargs):
    name, title, samples = unwrap_MergedSamples_args(*args,**kwargs)
    self.samples = samples
    Sample.__init__(self,name,title,"",**kwargs)
    if self.samples:
      self.init(samples[0])
  
  def init(self, sample, **kwargs):
    """Set some relevant attributes (inherited from the Sample class) with a given sample."""
    self.filename     = sample.filename
    self._treename    = sample.treename
    self.issignal     = sample.issignal
    self.isdata       = sample.isdata
    self.dtype        = sample.dtype
    self.lumi         = sample.lumi
    self.fillcolor    = sample.fillcolor
    self.linecolor    = sample.linecolor
  
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
  
  def row(self,pre="",indent=0):
    """Returns string that can be used as a row in a samples summary table."""
    xsec   = "%.2f"%self.xsec if self.xsec>0 else ""
    nevts  = "%i"%self.nevents if self.nevents>=0 else ""
    sumw   = "%i"%self.sumweights if self.sumweights>=0 else ""
    norm   = "%.3f"%self.norm
    name   = self.name.ljust(21-indent)
    string = ">>> %s%s %-26s %12s %11s %11s %10.3s  %s" %\
             (pre,name,self.title,xsec,nevts,sumw,norm,self.extraweight)
    for i, sample in enumerate(self.samples):
      subpre  = ' '*indent+("├─ " if i<len(self.samples)-1 else "└─ ")
      string += "\n" + sample.row(pre=subpre,indent=indent+3)
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
    newsample               = type(self)(name,title,*samples,**kwargs)
    newsample.__dict__.update(newdict)
    if close:
      newsample.close()
    return newsample
  
  def gethist(self, *args, **kwargs):
    """Create and fill histgram for multiple samples. Overrides Sample.gethist."""
    variables, selection, issingle = unwrap_gethist_args(*args)
    verbosity        = LOG.getverbosity(kwargs)
    name             = kwargs.get('name',           self.name+"_merged"  )
    name            += kwargs.get('tag',            ""                   )
    title            = kwargs.get('title',          self.title           )
    parallel         = kwargs.get('parallel',       False                )
    kwargs['cuts']   = joincuts(kwargs.get('cuts'), self.cuts            )
    kwargs['weight'] = joinweights(kwargs.get('weight', ""), self.weight ) # pass weight down
    kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
    
    # HISTOGRAMS
    allhists = [ ]
    garbage  = [ ]
    hargs    = (variables, selection)
    hkwargs  = kwargs.copy()
    if parallel and len(self.samples)>1:
      hkwargs['parallel'] = False
      processor = MultiProcessor()
      for sample in self.samples:
        processor.start(sample.hist,hargs,hkwargs,name=sample.title)        
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
      LOG.error("MergedSample.hist: len(subhists) = %s < %s = len(variables)"%(len(subhists),len(variables)))
    for ivar, variable in enumerate(variables):
      subhists = [subhists[ivar] for subhists in allhists]
      sumhist  = None
      for subhist in subhists:
        if sumhist==None:
          sumhist = subhist.Clone("%s_%s"%(variable.filename,name))
          sumhist.SetTitle(title)
          sumhist.SetDirectory(0)
          sumhist.SetLineColor(self.linecolor)
          sumhist.SetFillColor(self.fillcolor)
          sumhist.SetMarkerColor(self.fillcolor)
          sumhists.append(sumhist)
        else:
          sumhist.Add(subhist)      
      if verbosity>=3:
        printhist(sumhist)
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
    variables, selection, issingle = unwrap_gethist_args(*args)
    verbosity        = LOG.getverbosity(kwargs)
    name             = kwargs.get('name',               self.name+"_merged" )
    name            += kwargs.get('tag',                ""                  )
    title            = kwargs.get('title',              self.title          )
    kwargs['cuts']   = joincuts(kwargs.get('cuts'),     self.cuts           )
    kwargs['weight'] = joinweights(kwargs.get('weight', ""), self.weight    ) # pass scale down
    kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
    if verbosity>=2:
      print ">>>\n>>> MergedSample.gethist2D: %s: %s"%(color(name,color="grey"), self.fnameshort)
      #print ">>>    norm=%.4f, scale=%.4f, total %.4f"%(self.norm,kwargs['scale'],self.scale)
    
    # HISTOGRAMS
    hists = [ ]
    garbage = [ ]
    for sample in self.samples:
      if 'name' in kwargs: # prevent memory leaks
        kwargs['name']  = makehistname(kwargs.get('name',""),sample.name)
      subhists = sample.gethist2D(variables,selection,**kwargs)
      if hists==[ ]:
        for (xvariable,yvariable), subhist in zip(variables,subhists):
          #hist = subhist.Clone("%s_vs_%s_%s"%(xvariable.filename,yvariable.filename,name))
          subhist.SetName("%s_vs_%s_%s"%(xvariable.filename,yvariable.filename,name))
          subhist.SetTitle(title)
          subhist.SetDirectory(0)
          hists.append(subhist)
      else:
        for hist, subhist in zip(hists,subhists):
          hist.Add(subhist)
          garbage.append(subhist)
    deletehist(garbage)
    
    if issingle:
      return hists[0]
    return hists
  
