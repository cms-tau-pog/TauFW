# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
import os, re
from math import sqrt
from copy import copy, deepcopy
from TauFW.Plotter.sample.utils import *
from TauFW.Plotter.sample.HistSet import HistSet
from TauFW.Plotter.plot.string import makelatex, maketitle, makehistname
from TauFW.Plotter.plot.Variable import Variable
from TauFW.Plotter.plot.Stack import Stack
from TauFW.Plotter.plot.MultiThread import MultiProcessor
from TauFW.common.tools.LoadingBar import LoadingBar



class SampleSet(object):
  """Collect samples into one set to draw histgrams from trees for data/MC comparisons,
  and allow data-driven background estimations.
  """
  
  def __init__(self, *args, **kwargs):
    datasample = None
    expsamples = [ ]
    sigsamples = [ ]
    if len(args)==2:
      datasample, expsamples = args[0], list(args[1])
    elif len(args)==3:
      datasample, expsamples, sigsamples = args[0], list(args[1]), list(args[2])
    elif len(args)==1 or len(args)>3:
      expsamples = unwraplistargs(args)
    if datasample and not isinstance(datasample,Sample):
      LOG.throw(IOError,"SampleSet.__init__: Did not recognize data sample: %s"%(datasample))
    if expsamples and not (isinstance(expsamples,list) and all(isinstance(s,Sample) for s in expsamples)):
      LOG.throw(IOError,"SampleSet.__init__: Did not recognize expected (MC) sample: %s"%(expsamples))
    self.datasample     = datasample # data sample
    self.expsamples     = expsamples # background sample (exp. SM process like Drell-Yan, ttbar, W+jets, ...)
    self.sigsamples     = sigsamples # signal samples (for new physics searches)
    self.verbosity      = LOG.getverbosity(kwargs)
    self.name           = kwargs.get('name',       ""   )
    self.label          = kwargs.get('label',      ""   )
    self.channel        = kwargs.get('channel',    ""   )
    self.loadingbar     = kwargs.get('loadingbar', True ) and self.verbosity<=1
    self.ignore         = kwargs.get('ignore',     [ ]  )
    self.sharedsamples  = kwargs.get('shared',     [ ]  ) # shared samples with set variation to reduce number of files
    #self.shiftQCD       = kwargs.get('shiftQCD',   0    )
    #self.weight         = kwargs.get('weight',     ""   ) # use Sample objects to store weight !
    self.closed         = False
    self.nplots         = 0 # counter to clean and refresh memory once in a while
  
  def __str__(self):
    """Returns string representation of Sample object."""
    return ', '.join(repr(s.name) for s in [self.datasample]+self.mcsamples if s)
  
  def __add__(self,oset):
    """Add SampleSet objects together into a new one.
    Merge samples for better efficiency when using parallel drawing."""
    lumi = self.datasample.lumi + oset.datasample.lumi
    
    # OBSERVED DATA
    datasamples  = self.datasample.samples + oset.datasample.samples
    newdatasample = MergedSample(self.datasample.name,self.datasample.title,datasamples,
                                 isdata=True,isexp=False,lumi=lumi)
    
    # EXPECTED (MC)
    newexpsamples = [ ]
    osamples = oset.expsamples[:] # only merge samples once
    for sample in self.expsamples: # assume 1-to-1 matching of samples
      subsamples = sample.samples[:]
      splitsamples = sample.splitsamples
      for osample in osamples:
        if sample.name==osample.name:
          subsamples.extend(osample.samples)
          osamples.remove(osample) # only match once
          if not splitsamples and osample.splitsamples:
            splitsamples = osample.splitsamples
          break
      else:
        LOG.warn("SampleSet.__add__: Could not match sample %r to %s"%(sample,osamples))
      newsample = MergedSample(sample.name,sample.title,subsamples,
                               isdata=False,isexp=sample.isexp,isembed=sample.isembed,lumi=lumi)
      if splitsamples: # split again
        for ssample in splitsamples:
          newssample = newsample.clone(ssample.name,ssample.title,cuts=ssample.cuts,color=ssample.fillcolor)
          newsample.splitsamples.append(newssample)
      newexpsamples.append(newsample)
    if osamples:
      LOG.warn("SampleSet.__add__: Not all samples were matched:"%(osamples))
      newexpsamples.extend(osamples)
    newset = SampleSet(newdatasample,newexpsamples,name=self.name,
                       label=self.label,loadingbar=self.loadingbar)
    return newset
  
  def printobjs(self,title="",file=False):
    for sample in self.samples:
      sample.printobjs(title="",file=file)
  
  def printtable(self,title=None,merged=True,split=True):
    """Print table of all samples."""
    import TauFW.Plotter.sample.utils as GLOB
    if not title:
      name = self.name+" samples" if self.name else "Samples"
      print ">>>\n>>> %s with integrated luminosity L = %s / fb at sqrt(s) = 13 TeV"%(name,GLOB.lumi)
    justname  = 2+max(s.get_max_name_len() for s in self.samples)
    justtitle = 2+max(s.get_max_title_len() for s in self.samples)
    Sample.printheader(title,justname=justname,justtitle=justtitle,merged=merged)
    for sample in self.samples:
      sample.printrow(justname=justname,justtitle=justtitle,merged=merged,split=split)
    print ">>> "
  
  def __iter__(self):
    """Start iteration over samples."""
    for sample in self.samples:
      yield sample
  
  def __len__(self):
    """Return number of samples."""
    return len(self.samples)
  
  @property
  def samples(self):
    """Getter for "samples" attribute of SampleSet."""
    if self.datasample:
      return [self.datasample]+self.expsamples+self.sigsamples
    else:
      return self.expsamples+self.sigsamples
  
  #@samples.setter
  #def samples(self, value):
  #  """Setter for "samples" attribute."""
  #  datasample, expsamples, sigsamples = None, [ ], [ ]
  #  for sample in value:
  #    if   sample.isdata:   datasample = sample
  #    elif sample.issignal: sigsamples.append(sample)
  #    else:                 expsamples.append(sample)
  #  self.datasample, self.expsamples, self.sigsamples = datasample, expsamples, sigsamples
  #  LOG.warn("SampleSet.samples: No setter for \"samples\" attribute available!")
  
  @property
  def mcsamples(self):
    return self.expsamples + self.sigsamples
  
  @mcsamples.setter
  def mcsamples(self, value):
    expsamples, sigsamples = [ ], [ ]
    for sample in value:
      if sample.issignal:
        sigsamples.append(sample)
      else:
        expsamples.append(sample)
    self.expsamples, self.sigsamples = expsamples, sigsamples
  
  def index(self,sample):
    """Return index of sample."""
    return self.samples.index(sample)
  
  def replace(self,oldsample,*newsamples,**kwargs):
    """Replace sample with one or more samples."""
    if not newsamples:
      LOG.warn("SampleSet.replace: No samples given to replace %r!"%oldsample.title)
      return
    newsamples = unwraplistargs(newsamples)
    samples = self.samples #getattr(self,"samples"+kwargs.get('type','B'))
    if len(newsamples)==1 and islist(newsamples[0]):
      newsamples = newsamples[0]
    if oldsample in samples[:]:
      index = samples.index(oldsample)
      samples.remove(oldsample)
      for newsample in newsamples:
        samples.insert(index,newsample)
        index += 1
    else:
      LOG.warn("SampleSet.replace: Sample %r not in the list!"%oldsample.title)
      for newsample in newsamples:
        self.samples.append(newsample)
  
  def settreename(self,treename):
    """Set tree name for each sample to draw histograms with."""
    for sample in self.samples:
      sample.settreename(treename)
  
  #def setcolors(self):
  #  """Set colors for each sample. Check if each color is used uniquely."""
  #  verbosity = LOG.getverbosity(kwargs)
  #  usedcols  = [ ]
  #  # CHECK SPLIT
  #  for sample in self.samples:
  #    if sample.color is kBlack:
  #      LOG.warn("SamplesSet.setcolors: %s"%sample.name)
  #    if sample.color in usedcols:
  #      # TODO: check other color
  #      sample.setcolor()
  #      LOG.warn("SamplesSet.setcolors: Color used twice!")
  #    else:
  #      usedcols.append(sample.color)
  #
  
  def replaceweight(self, oldweight, newweight):
    """Replace weight."""
    for sample in self.samples:
      sample.replaceweight(oldweight, newweight)
  
  def open(self,**kwargs):
    """Help function to open all files in samples list."""
    for sample in self.samples:
      sample.open(**kwargs)
    self.closed = False
  
  def close(self,**kwargs):
    """Help function to close all files in samples list, to clean memory"""
    shared = kwargs.get('shared', False)
    for sample in self.samples:
      if shared and sample in self.sharedsamples: continue
      sample.close(**kwargs)
    self.closed = True
  
  def reload(self,**kwargs):
    """Help function to reload all files in samples list."""
    for sample in self.samples:
      sample.reload(**kwargs)
    self.closed = False
  
  def refresh(self,**kwargs):
    """Open/reopen files to refresh file memories after some amount of plots have been made."""
    verbosity = LOG.getverbosity(kwargs)
    now       = kwargs.get('now',  False ) # refresh right now
    step      = kwargs.get('step', 20    ) # threshold of number of plots made before actual refreshing
    kwargs['verbosity'] = verbosity
    gROOT.cd()
    if now or (self.nplots>step and self.nplots>0):
      if verbosity>=1:
        LOG.warn('SampleSet.refresh: refreshing memory (nplots=%d, gDirectory=%r)'%(self.nplots,gDirectory.GetName()))
        gDirectory.ls()
      self.reload(**kwargs)
      self.nplots = 0
  
  def clone(self,name="",**kwargs):
    """Shift samples in samples set by creating new samples with new filename/titlename."""
    filter        = kwargs.get('filter',      False       ) # filter out 
    share         = kwargs.get('share',       False       ) # share other samples (as opposed to cloning them)
    app           = kwargs.get('app',         "clone"     )
    close         = kwargs.get('close',       False       )
    deep          = kwargs.get('deep',        True        )
    filterterms   = filter if islist(filter) else ensurelist(filter) if isinstance(filter,str) else [ ]
    shareterms    = share  if islist(share)  else ensurelist(share)  if isinstance(share,str)  else [ ]
    datasample    = None
    expsamples    = [ ]
    sigsamples    = [ ]
    sharedsamples = [ ]
    for sample in self.expsamples:
      if filter and sample.match(*filterterms,incl=False):
        if share:
          newsample = sample
          sharedsamples.append(newsample)
        else:
          newsample = sample.clone(samename=True,deep=deep)
        expsamples.append(newsample)
      elif not filter:
        if share or (shareterms and sample.match(*shareterms,incl=False)):
          newsample = sample
          sharedsamples.append(newsample)
        else:
          newsample = sample.clone(samename=True,deep=deep)
        expsamples.append(newsample)
    for sample in self.sigsamples:
      if filter and sample.match(*filterterms,incl=False):
        if share:
          newsample = sample
          sharedsamples.append(newsample)
        else:
          newsample = sample.clone(samename=True,deep=deep)
        expsamples.append(newsample)
      elif not filter:
        if share or (shareterms and sample.match(*shareterms,incl=False)):
          newsample = sample
          sharedsamples.append(newsample)
        else:
          newsample = sample.clone(samename=True,deep=deep)
        sigsamples.append(newsample)
    if not filter:
      datasample = self.datasample
      sharedsamples.append(datasample)
    kwargs['shared']    = sharedsamples
    kwargs['name']      = name
    kwargs['shiftQCD']  = self.shiftQCD
    kwargs['label']     = self.label
    kwargs['channel']   = self.channel
    kwargs['verbosity'] = self.verbosity
    newset = SampleSet(datasample,expsamples,sigsamples,**kwargs)
    newset.closed = close
    return newset
  
  def changecontext(self,*args):
    """Help function to change context of variable object."""
    #variables  = [a for a in args if isinstance(a,Variable)]
    #selections = [a for a in args if isinstance(a,Selection) or isSelectionString(a)]
    variables, selection, issingle = unwrap_gethist_args(*args)
    invariables = variables[:]
    for var in variables:
      if not var.plotfor(selection,self.channel): # or not selection.plotfor(var)
         print ">>> plotstack: ignoring %s for %s"%(var.printbins(),selection) #.title
         invariables.remove(var)
         continue
      var.changecontext(selection.selection,self.channel)
    return invariables, selection, issingle
  
  def getstack(self, *args, **kwargs):
    """Create and fill histograms for each given variable,
    and create a Plot object to plot a stack."""
    self.refresh()
    variables, selection, issingle = self.changecontext(*args)
    result = self.gethists(variables,selection,**kwargs)
    stacks = { }
    self.nplots += len(result.vars)
    for args in result:
      stack = Stack(*args,**kwargs)
      if issingle:
        return stack # Stack
      else:
        stacks[stack] = args[0]
    return stacks # dictionary: Stack -> Variable
  
  def getTHStack(self, *args, **kwargs):
    """Get stack of backgrounds histogram."""
    name   = kwargs.get('name',"stack")
    kwargs.update({'data':False, 'signal':False, 'exp':True})
    variables, selection, issingle = self.changecontext(*args)
    result = self.gethists(variables,selection,**kwargs)
    stacks = { }
    self.nplots += len(result.vars)
    for var in result.vars:
      stack = THStack(name,name)
      for hist in reversed(result.exp[var]):
        stack.Add(hist)
      if issingle:
        return stack # TH1Stack
      else:
        stacks[stack] = var
    return stacks # dictionary: THStack -> Variable
  
  def getdatahist(self, *args, **kwargs):
    """Create and fill histograms of background simulations and make a stack."""
    name   = kwargs.get('name',"data")
    kwargs.update({'data':True, 'mc':False, 'signal':False, 'exp':False})
    var    = self.changecontext(*args)
    result = self.gethists(*args,**kwargs)
    return result.data
  
  def gethists(self, *args, **kwargs):
    """Create and fill histograms for all samples and return lists of histograms."""
    verbosity     = LOG.getverbosity(kwargs)
    if verbosity>=1:
      print ">>> gethists"
    variables, selection, issingle = unwrap_gethist_args(*args)
    datavars      = filter(lambda v: v.data,variables)    # filter out gen-level variables
    dodata        = kwargs.get('data',          True    ) # create data hists
    domc          = kwargs.get('mc',            True    ) # create expected (SM background) hists
    doexp         = kwargs.get('exp',           domc    ) # create expected (SM background) hists
    dosignal      = kwargs.get('signal',        domc and self.sigsamples ) # create signal hists (for new physics searches)
    weight        = kwargs.get('weight',        ""      ) # extra weight (for MC only)
    dataweight    = kwargs.get('dataweight',    ""      ) # extra weight for data
    replaceweight = kwargs.get('replaceweight', None    ) # replace substring of weight
    split         = kwargs.get('split',         True    ) # split samples into components
    blind         = kwargs.get('blind',         True    ) # blind data in some given range: blind={xvar:(xmin,xmax)}
    scaleup       = kwargs.get('scaleup',       0.0     ) # scale up histograms
    reset         = kwargs.get('reset',         False   ) # reset scales
    parallel      = kwargs.get('parallel',      False   ) # create and fill hists in parallel
    tag           = kwargs.get('tag',           ""      )
    method        = kwargs.get('method',        None    ) # data-driven method; 'QCD_OSSS', 'QCD_ABCD', 'JTF', 'FakeFactor', ...
    imethod       = kwargs.get('imethod',       -1      ) # position on list; -1 = last (bottom of stack)
    filters       = kwargs.get('filter',        None    ) or [ ] # filter these samples
    vetoes        = kwargs.get('veto',          None    ) or [ ] # filter out these samples
    #makeJTF       = kwargs.get('JTF',           False   ) and data
    #nojtf         = kwargs.get('nojtf',         makeJTF ) and data
    #keepWJ        = kwargs.get('keepWJ',        False   )
    #makeQCD       = kwargs.get('QCD',           False   ) and data and not makeJTF
    #ratio_WJ_QCD  = kwargs.get('ratio_WJ_QCD_SS', False   )
    #QCDshift      = kwargs.get('QCDshift',      0.0     )
    #QCDrelax      = kwargs.get('QCDrelax',      False   )
    #JTFshift      = kwargs.get('JTFshift',      [ ]     )
    sysvars       = kwargs.get('sysvars',       { }     ) # list or dict to be filled up with systematic variations
    addsys        = kwargs.get('addsys',        True    )
    task          = kwargs.get('task',          "Creating histograms" ) # task title for loading bar
    #saveto        = kwargs.get('saveto',        ""     ) # save to TFile
    #file          = createFile(saveto,text=cuts) if saveto else None
    filters       = ensurelist(filters)
    vetoes        = ensurelist(vetoes)
    if method and not hasattr(self,method):
      ensuremodule(method,'Plotter.methods') # load SampleSet class method
    
    # FILTER
    samples = [ ]
    for sample in self.samples:
      if not dosignal and sample.issignal: continue
      if not dodata   and sample.isdata:   continue
      if split and sample.splitsamples:
        subsamples = sample.splitsamples
      else:
        subsamples = [sample] # sample itself
      for subsample in subsamples:
        if filters and not subsample.match(*filters): continue
        if vetoes  and subsample.match(*vetoes): continue
        samples.append(subsample)
    #if nojtf:
    #  samples = [s for s in samples if not ((not keepWJ and s.match('WJ',"W*J","W*j")) or "gen_match_2==6" in s.cuts or "genPartFlav_2==0" in s.cuts)]
    
    # INPUT / OUTPUT
    mcargs     = (variables,selection)
    dataargs   = (datavars, selection)
    expkwargs  = { 'tag':tag, 'weight': weight, 'replaceweight': replaceweight, 'verbosity': verbosity, } #'nojtf': nojtf 
    sigkwargs  = { 'tag':tag, 'weight': weight, 'replaceweight': replaceweight, 'verbosity': verbosity, 'scaleup': scaleup }
    datakwargs = { 'tag':tag, 'weight': dataweight, 'verbosity': verbosity, 'blind': blind, 'parallel': parallel }
    result     = HistSet(variables,dodata,doexp,dosignal) # container for dictionaries of histogram (list): data, exp, signal
    if not variables:
      LOG.warn("Sample.gethists: No variables to make histograms for...")
      return result
    
    # PRINT
    bar = None
    if verbosity>=2:
      if not ('QCD' in task or 'JFR' in task):
        LOG.header("Creating histograms for %s"%selection) #.title
      print ">>> variables: %s"%(quotestrs([v.filename for v in variables]))
      #print ">>> split=%s, makeQCD=%s, makeJTF=%s, nojtf=%s, keepWJ=%s"%(split,makeQCD,makeJTF,nojtf,keepWJ)
      print '>>>   with extra weights "%s" for MC and "%s" for data'%(weight,dataweight)
    elif self.loadingbar and verbosity<=1:
      bar = LoadingBar(len(samples),width=16,pre=">>> %s: "%(task),counter=True,remove=True) # %s: selection.title
    
    # GET HISTOGRAMS (PARALLEL)
    if parallel:
      expproc  = MultiProcessor()
      sigproc  = MultiProcessor()
      dataproc = MultiProcessor()
      for sample in samples:
        if reset: sample.resetscale()
        if sample.name in self.ignore: continue
        if dosignal and sample.issignal: # SIGNAL
          sigproc.start(sample.gethist,mcargs,sigkwargs,name=sample.title)
        elif doexp and sample.isexp:     # EXPECTED (SM BACKGROUND)
          expproc.start(sample.gethist,mcargs,expkwargs,name=sample.title)
        elif dodata and sample.isdata:   # DATA
          dataproc.start(sample.gethist,dataargs,datakwargs,name=sample.title)
      for dtype, processor, varset in [('exp',expproc,variables),('sig',sigproc,variables),('data',dataproc,datavars)]:
        for process in processor:
          if bar: bar.message(process.name)
          newhists = process.join()
          for var, hist in zip(varset,newhists): # assume match variables -> histograms
            if dtype=='data':
              getattr(result,dtype)[var] = hist
            else:
              getattr(result,dtype)[var].append(hist)
          if bar: bar.count("%s done"%process.name)
    
    # GET HISTOGRAMS (SEQUENTIAL)
    else:
      for sample in samples:
        if bar:   bar.message(sample.title)
        if reset: sample.resetscale()
        if sample.name in self.ignore:
          if bar: bar.count("%s skipped"%sample.title)
          continue
        if dosignal and sample.issignal: # SIGNAL
          hists = sample.gethist(*mcargs,**sigkwargs)
          for var, hist in zip(variables,hists):
            result.signal[var].append(hist)
        elif doexp and sample.isexp:     # EXPECTED (SM BACKGROUND)
          hists = sample.gethist(*mcargs,**expkwargs)
          for var, hist in zip(variables,hists):
            result.exp[var].append(hist)
        elif dodata and sample.isdata:   # DATA
          hists = sample.gethist(*mcargs,**datakwargs)
          for var, hist in zip(datavars,hists):
            result.data[var] = hist
        if bar: bar.count("%s done"%sample.title)
    
    # EXTRA METHODS
    if method:
      hists = getattr(self,method)(*dataargs,**kwargs)
      for var, hist in zip(datavars,hists):
        idx = imethod if imethod>=0 else len(result.exp[var])+1+imethod
        result.exp[var].insert(idx,hist)
    
    ## SAVE histograms
    #if file:
    #  file.cd()
    #  for hist in histsD + result.exp + result.exp:
    #    hist.GetXaxis().SetTitle(var)
    #    hist.Write(hist.GetName())
    #    #file.Write(hist.GetName())
    #  file.Close()
    
    # YIELDS
    if verbosity>=2 and len(variables)>0:
      var = variables[0]
      print ">>> selection:"
      print ">>>  %r"%(selection.selection)
      print ">>> yields: "
      TAB = LOG.table("%11.1f %11.2f    %r")
      TAB.printheader("entries","integral","hist name")
      totint = 0
      totent = 0
      if dodata and result.data[var]:
        TAB.printrow(result.data[var].Integral(),result.data[var].GetEntries(),result.data[var].GetName())
      for hist in result.exp[var]:
        totint += hist.Integral()
        totent += hist.GetEntries()
        TAB.printrow(hist.Integral(),hist.GetEntries(),hist.GetName())
      TAB.printrow(totint,totent,"total exp.")
      if dosignal:
        for hist in result.signal[var]:
          TAB.printrow(hist.Integral(),hist.GetEntries(),hist.GetName())
    
    if issingle:
      result.setsingle()
      return result # HistSet with single result.data histogram, result.exp list of histograms
    return result # HistSet with result.data dictionary of histograms, result.exp dictionary of list of histograms
  
  def gethists2D(self, *args, **kwargs):
    """Create and fill histograms for all samples and return lists of histograms."""
    variables, selection, issingle = unwrap_gethist2D_args(*args)
    verbosity  = LOG.getverbosity(kwargs)
    dodata     = kwargs.get('data',       True     ) # create data hists
    domc       = kwargs.get('mc',         True     ) # create expected (SM background) hists
    doexp      = kwargs.get('exp',        domc     ) # create expected (SM background) hists
    dosignal   = kwargs.get('signal',     domc and self.sigsamples ) # create signal hists (for new physics searches)
    weight     = kwargs.get('weight',     ""       ) # extra weight (for MC only)
    dataweight = kwargs.get('dataweight', ""       ) # extra weight for data
    tag        = kwargs.get('tag',        ""       )
    #makeJTF    = kwargs.get('JFR',        False    )
    #nojtf      = kwargs.get('nojtf',      makeJTF  )
    task       = kwargs.get('task',       "making histograms" )
    
    
    # INPUT / OUTPUT
    args       = (variables,selection)
    expkwargs  = { 'tag':tag, 'weight': weight, 'verbosity': verbosity } #, 'nojtf': nojtf
    sigkwargs  = { 'tag':tag, 'weight': weight, 'verbosity': verbosity }
    datakwargs = { 'tag':tag, 'weight': dataweight, 'verbosity': verbosity }
    result     = HistSet(variables,dodata,doexp,dosignal)
    if not variables:
      LOG.warn("Sample.gethists: No variables to make histograms for...")
      return result
    
    # FILTER
    samples = [ ]
    for sample in self.samples:
      if not dodata and sample.isdata:
        continue
      samples.append(sample)
    #if nojtf:
    #  samples = [s for s in samples if not (s.match('WJ',"W*J","W*j") or "gen_match_2==6" in s.cuts or "genPartFlav_2==0" in s.cuts)]
    
    # GET HISTOGRAMS
    bar = None
    if self.loadingbar and verbosity<=1:
      bar = LoadingBar(len(samples),width=16,pre=">>> %s: "%(task),counter=True,remove=True)
    for sample in samples:
      if bar:   bar.message(sample.title)
      if sample.name in self.ignore:
        if bar: bar.count("%s skipped"%sample.title)
        continue
      if dosignal and sample.issignal: # SIGNAL
        hists = sample.gethist2D(*args,**sigkwargs)
        for variable, hist in zip(variables,hists):
          result.signal[variable].append(hist)
      elif doexp and sample.isexp:     # EXPECTED (SM BACKGROUND)
        hists = sample.gethist2D(*args,**expkwargs)
        for variable, hist in zip(variables,hists):
          result.exp[variable].append(hist)
      elif dodata and sample.isdata:   # DATA
        hists = sample.gethist2D(*args,**datakwargs)
        for variable, hist in zip(variables,hists):
          result.data[variable].append(hist)
      if bar: bar.count("%s done"%sample.name)
    
    ## ADD JTF
    #if makeJTF:
    #    print "CHECK IMPLEMENTATION!"
    #    hists = self.jetFakeRate2D(*args,tag=tag,weight=weight,verbosity=verbosity)
    #    for variable, hist in zip(variables,hists):
    #      histsB[variable].insert(0,hist)
    
    if issingle:
      result.setsingle()
      return result
    return result
  
  def resetscales(self,*searchterms,**kwargs):
    """Reset scale of sample."""
    scale = kwargs.get('scale')
    samples = self.get(*searchterms,**kwargs)
    if islist(samples):
      for sample in samples:
        sample.resetscale(scale=scale)
    elif isinstance(samples,Sample):
      samples.resetscale(scale=scale)
    else:
      LOG.ERROR("SampleSet.resetscales: Found sample is not a list or Sample or list object!")
    return samples
  
  def has(self,*searchterms,**kwargs):
    """Return true if sample set contains a sample corresponding to given searchterms."""
    kwargs.setdefault('warn',False)
    result = self.get(*searchterms,**kwargs)
    found = isinstance(result,Sample) or len(result)!=0
    return found
  
  def remove(self,*searchterms,**kwargs):
    samples = self.get(*searchterms,**kwargs)
    for sample in samples:
      self.samples.remove(sample)
  
  def get(self,*searchterms,**kwargs):
    return getsample(self.samples,*searchterms,**kwargs)
  
  def getexp(self,*searchterms,**kwargs):
    return getsample_with_flag(self.expsamples,'isexp',*searchterms,**kwargs)
  
  #def getmc(self,*searchterms,**kwargs):
  #  return getsample_with_flag(self.mcsamples,'ismc',*searchterms,**kwargs)
  
  def getsignal(self,*searchterms,**kwargs):
    return getsample_with_flag(self.sigsamples,'issignal',*searchterms,**kwargs)
  
  def join(self,*searchterms,**kwargs):
    self.mcsamples = join(self.mcsamples,*searchterms,**kwargs)
  
  def stitch(self,*searchterms,**kwargs):
    self.mcsamples = stitch(self.mcsamples,*searchterms,**kwargs)
  
  def replace(self,mergedsample):
    """Help function to replace sample in the same position."""
    oldindex = len(self.samples)
    for sample in mergedsample:
      index = self.samples.index(sample)
      if index<oldindex:
        oldindex = index
      self.samples.remove(sample)
    self.samples.insert(oldindex,mergedsample)
  
  def rename(self,*args,**kwargs):
    """Rename sample, e.g. sampleset.rename('WJ','W')"""
    verbosity        = LOG.getverbosity(kwargs)
    LOG.insist(len(args)>=2,"SampleSet.rename: need more than two strings! Got %s"%(args,))
    strings          = [arg for arg in args if isinstance(arg,str)]
    searchterms      = strings[:-1]
    name             = strings[-1]
    warn             = kwargs.setdefault('warn',False)
    kwargs['unique'] = True
    sample           = self.get(*searchterms,**kwargs)
    if sample:
      LOG.verb("SampleSet.rename: %r -> %r"%(sample.name,name),verbosity,2)
      sample.name    = name
    elif warn:
      LOG.warn("SampleSet.rename: Could not find sample with searchterms '%s' to rename to %r"%(quotestrs(searchterms),name))
    else:
      LOG.verb("SampleSet.rename: Could not find sample with searchterms '%s' to rename to %r"%(quotestrs(searchterms),name),verbosity,2)
  
  def split(self,*args,**kwargs):
    """Split sample into different components with some cuts, e.g.
      sampleset.split('DY',[
         ('ZTT',"Real tau","genmatch_2==5"),
         ('ZJ', "Fake tau","genmatch_2!=5"),
      ])
    """
    verbosity        = LOG.getverbosity(kwargs)
    LOG.verb("SampleSet.split: splitting %s"%(self.name),verbosity,1)
    searchterms      = [arg for arg in args if isinstance(arg,str)]
    splitlist        = [arg for arg in args if islist(arg)        ][0]
    kwargs['unique'] = True
    sample           = self.get(*searchterms,**kwargs)
    if sample:
      sample.split(splitlist,**kwargs)
    else:
      LOG.warn("SampleSet.split: Could not find sample with searchterms '%s'"%(quotestrs(searchterms)))
  
  def shift(self,searchterms,filetag,nametag=None,titletag=None,**kwargs):
    """Shift samples in samples set by creating new samples with new filename/titlename."""
    verbosity     = LOG.getverbosity(kwargs)
    LOG.verb("Sample.shift(%r,%r,%r)"%(searchterms,filetag,titletag),verbosity,1)
    filter        = kwargs.get('filter',      False       ) # filter non-matched samples out
    share         = kwargs.get('share',       False       ) # reduce memory by sharing non-matched samples (as opposed to cloning)
    split         = kwargs.get('split',       False       ) # also look in split samples
    close         = kwargs.get('close',       False       )
    kwargs.setdefault('name',      filetag.lstrip('_')      )
    kwargs.setdefault('label',     filetag                  )
    kwargs.setdefault('channel',   self.channel             )
    searchterms   = ensurelist(searchterms)
    all           = searchterms==['*']
    datasample    = None
    expsamples    = [ ]
    sigsamples    = [ ]
    sharedsamples = [ ]
    def appendfilename(sample_):
      """Help function to append filename for a single sample."""
      newsample = sample_.clone(samename=True,deep=True)
      newsample.appendfilename(filetag,nametag,titletag,verb=verbosity)
      if close:
        newsample.close()
      return newsample
    for oldsamples, newsamples in [(self.expsamples,expsamples),(self.sigsamples,sigsamples)]:
      for sample in oldsamples:
        newsample = None
        if all or sample.match(*searchterms,incl=True):
          newsample = appendfilename(sample)
        elif split and any(s for s in sample.splitsamples if s.match(*searchterms,incl=True)):
          newsample = sample.clone(samename=True,deep=True)
          for i, subsample in enumerate(newsample.splitsamples[:]):
            if subsample.match(*searchterms,incl=True):
              newsample.splitsamples[i] = appendfilename(subsample)
            elif share:
              newsubsample = newsample.splitsamples[i]
              newsample.splitsamples[i] = sample.splitsamples[i]
              newsubsample.close()
        if newsample==None and not filter:
          newsample = sample if share else sample.clone(samename=True,deep=True,close=True)
          if share:
            sharedsamples.append(newsample)
        if newsample!=None:
          newsamples.append(newsample)
    if not filter:
      datasample = self.datasample
      sharedsamples.append(datasample)
    kwargs['shared'] = sharedsamples
    newset = SampleSet(datasample,expsamples,sigsamples,**kwargs)
    newset.closed = close
    return newset
  
  def shiftweight(self,searchterms,newweight,titletag="",**kwargs):
    """Shift samples in samples set by creating new samples with new weight."""
    filter          = kwargs.get('filter',      False       ) # filter other samples
    share           = kwargs.get('share',       False       ) # share other samples (as opposed to cloning them)
    extra           = kwargs.get('extra',       True        ) # replace extra weight
    if not islist(searchterms):
      searchterms = [ searchterms ]
    datasample      = None
    expsamples      = [ ]
    sigsamples      = [ ]
    for sample in self.expsamples:
      if sample.match(*searchterms,incl=False):
        newsample = sample.clone(samename=True,deep=True)
        #LOG.verb('SampleSet.shiftweight: "%s" - weight "%s", extra weight "%s"'%(newsample.name,newsample.weight,newsample.extraweight),1)
        if extra:
          newsample.setextraweight(newweight)
        else:
          newsample.addweight(newweight)
        #LOG.verb('SampleSet.shiftweight: "%s" - weight "%s", extra weight "%s"'%(newsample.name,newsample.weight,newsample.extraweight),1)
        expsamples.append(newsample)
      elif not filter:
        newsample = sample if share else sample.clone(samename=True,deep=True)
        expsamples.append(newsample)
    for sample in self.sigsamples:
      if sample.match(*searchterms,incl=False):
        newsample = sample.clone(samename=True,deep=True)
        if extra:
          newsample.setextraweight(newweight)
        else:
          newsample.addweight(newweight)
        sigsamples.append(newsample)
      elif not filter:
        newsample = sample if share else sample.clone(samename=True,deep=True)
        sigsamples.append(newsample)
    if not filter:
        datasample = self.datasample
    return SampleSet(datasample,expsamples,sigsamples,**kwargs)
  
