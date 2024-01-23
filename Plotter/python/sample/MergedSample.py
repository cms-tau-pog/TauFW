# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.plot.MultiThread import MultiProcessor
from TauFW.Plotter.sample.ResultDict import ResultDict # for containing RDataFRame RResultPtr
import ROOT
#ROOT.ROOT.EnableThreadSafety() # for multithreading
#ROOT.ROOT.EnableImplicitMT() # for multithreading


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
    name, title, samples = unpack_MergedSamples_args(*args,**kwargs)
    Sample.__init__(self,name,title,"",**kwargs)
    self.samples = samples  # list of merged samples
    self.sample_incl = None # keep track of inclusive sample in stitching
    if self.samples:
      self.init(samples[0],**kwargs)
  
  def init(self, sample, **kwargs):
    """Set some relevant attributes (inherited from the Sample class) with a given sample."""
    self.filename  = sample.filename
    self.treename  = sample.treename
    self.isdata    = sample.isdata
    self.isembed   = sample.isembed
    self.isexp     = sample.isexp
    self.issignal  = sample.issignal
    self.cutflow   = sample.cutflow
    self.fillcolor = kwargs.get('color',    self.fillcolor) or sample.fillcolor
    self.linecolor = kwargs.get('linecolor',self.linecolor) or sample.linecolor
    self.lumi      = kwargs.get('lumi',     sample.lumi)
  
  def __len__(self):
    """Return number of samples."""
    return len(self.samples)
  
  def __iter__(self):
    """Start iteration over samples."""
    for sample in self.samples:
      yield sample
  
  def __add__(self,sample):
    """Add Sample object to list of samples."""
    return self.add(sample)
  
  def add(self, sample, **kwargs):
    """Add Sample object to list of samples."""
    if not self.samples: # initiated for the first time based on newly added sample
      self.init(sample)
    self.samples.append(sample)
    return self
  
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
    deep         = kwargs.get('deep',     False ) # deep copy (create new Sample objects)
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
  
  def getrdframe(self,variables,selections,**kwargs):
    """Create RDataFrames for list of variables and selections."""
    verbosity = LOG.getverbosity(kwargs)
    name      = kwargs.get('name',   self.name ) # hist name
    name     += kwargs.get('tag',    ""        ) # tag for hist name
    scales    = kwargs.get('scales', None      ) # list of scale factors, one for each subsample
    split     = kwargs.get('split',  False     ) and len(self.splitsamples)>=1 # split sample into components (e.g. with cuts on genmatch)
    scale     = kwargs.get('scale', 1.0) * self.scale * self.norm # common scale to pass down
    
    # PREPARE SETTING for subsamples
    hkwargs = kwargs.copy()
    if not split and 'title' not in kwargs:
      hkwargs['title']  = self.title # set default histogram title
    hkwargs['split']    = False # do not split anymore in subsamples
    hkwargs['cuts']     = joincuts(kwargs.get('cuts'), self.cuts )
    hkwargs['scale']    = scale # pass common scale down
    hkwargs['weight']   = joinweights(kwargs.get('weight', ""),self.weight) # pass weight down
    hkwargs['rdf_dict'] = kwargs.get('rdf_dict', { } ) # optimization & debugging: reuse RDF for the same filename / selection in all subsamples
    LOG.verb("MergedSample.getrdframe: Creating RDataFrame for %s ('%s'), cuts=%r, weight=%r, scale=%r, nsamples=%r, split=%r"%(
             color(name,'grey',b=True),color(self.title,'grey',b=True),
             hkwargs['cuts'],hkwargs['weight'],hkwargs['scale'],len(self.samples),split),verbosity,1)
    
    # CREATE RDataFrames per SUBSAMPLE
    res_dict = ResultDict() # { selection : { variable: { subsample: hist } } } }
    samples  = self.splitsamples if split else self.samples
    for i, subsample in enumerate(samples):
      if 'name' in kwargs: # prevent memory leaks (confusing of histograms)
        hkwargs['name'] = makehistname(kwargs['name'],subsample.name)
      if scales: # apply extra scale factor per subsample
        hkwargs['scale'] = scale*scales[i] # assume scales is a length with the samen length as samples
        LOG.verb("MergedSample.getrdframe: Scaling subsample %r by %s (total %s)"%(subsample.name,scales[i],scale),verbosity,1)
      res_dict += subsample.getrdframe(variables,selections,**hkwargs)
    if not split: # merge RDF.RResultPtr<T> into MergedResults list so they can be added coherently later
      hname = name if 'name' in kwargs else "$VAR_"+name # histogram name
      res_dict.merge(self,name=hname,title=self.title,verb=verbosity) # { selection : { variable: { self: hist } } } }
    
    return res_dict
  

def unpack_MergedSamples_args(*args,**kwargs):
  """
  Help function to unpack arguments for MergedSamples initialization:
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
  #args    = unpacklistargs(args)
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
  LOG.verb("unpack_MergedSamples_args: name=%r, title=%r, samples=%s"%(name,title,samples),level=3)
  return name, title, samples
  
