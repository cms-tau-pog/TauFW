# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (November 2023)
# Description: Container class for RDF results.
import os, time
from TauFW.common.tools.string import took
from TauFW.common.tools.root import rootrepr
from TauFW.common.tools.log import color
from TauFW.common.tools.RDataFrame import ROOT, RDF, RDataFrame, printRDFReport


class MeanResult():
  """Store a mean and sum-of-weights as pair of RDF.RResultPtr<double> objects,
  so they can be added to other means correctly later by MergedResults."""
  
  def __init__(self,mean,sumw=None):
    self.mean  = mean # RDF.RResultPtr<double>
    self._sumw = sumw # RDF.RResultPtr<double> or 0
    self.sumw  = 0
  
  def __repr__(self):
    return "<MeanResult(%r,%r)>"%(self.mean,self.sumw)
  
  def GetValue(self):
    """Call GetValue."""
    if self._sumw!=None:
      self.sumw = self._sumw.GetValue() # convert to double
    return self.mean.GetValue()
  

class MergedResult():
  """Container class for list of RDF.RResultPtr<T> (and other MergedResult) objects.
  If MergedResult.GetValue is called, it will add together the results.
  NOTE: Calling MergedResult.GetValue triggers the RDataFrame event loop if not run before."""
  
  def __init__(self,results=None,**kwargs):
    self._list = [ ] if results==None else list(results) # list of RDF.RResultPtr<T> objects
    self.name  = kwargs.get('name',  None ) # name  for merged histogram
    self.title = kwargs.get('title', None ) # title for merged histogram
    self.verb  = kwargs.get('verb',  0    ) # verbosity level
    self.sumw  = 0 # for weighted-sum of MeanResult values
  
  def __len__(self):
    return len(self._list)
  
  def __repr__(self):
    return "<MergedResult(%s)>"%(', '.join(repr(r) for r in self._list))
  
  def __iter__(self):
    """Return iterator over results list.
    For ResultDict.items -> ResultDict.results -> ResultDict.run -> RDF.RunGraphs."""
    for result in self._list:
      if isinstance(result,MergedResult):
        for subresult in result: # note: can be recursive
          yield subresult
      elif isinstance(result,MeanResult):
        yield result.mean
        if result._sumw:
          yield result._sumw
      else:
        yield result
  
  def append(self,result):
    """Add RDF.RResultPtr<T> or MergedResult to list."""
    self._list.append(result)
    return result
  
  def GetValue(self,verb=0):
    """Call GetValue for each object and add together.
    Return sum."""
    totsumw = 0 # weighted normalization for MeanResult
    sumobj  = None
    verb    = max(self.verb,verb)
    for result in self._list: # iterate over RDF.RResultPtr<T> (or other MergedResult) objects
      obj  = result.GetValue() # NOTE: This triggers event loop if not run before !
      sumw = result.sumw if hasattr(result,'sumw') else 0 # sum-of-weights for normalization
      if sumobj==None: # initialize sumobj
        if sumw==0:
          LOG.verb("MergedResult.GetValue: sumobj = %s, new (name,title)=(%r,%r)"%(rootrepr(obj),self.name,self.title),verb,2)
          sumobj = obj
        else: # weighted number
          LOG.verb("MergedResult.GetValue: sumobj = %s*%s, new (name,title)=(%r,%r)"%(sumw,obj,self.name,self.title),verb,2)
          sumobj  = sumw*obj # weighted (total sum will be normalized)
          totsumw = sumw # for later normalization
        if isinstance(self.name,str) and hasattr(sumobj,'SetName'):
          sumobj.SetName(self.name)
        if isinstance(self.title,str) and hasattr(sumobj,'SetTitle'):
          sumobj.SetTitle(self.title)
      elif hasattr(obj,'Add'): # add other object, e.g. a TH1
        LOG.verb("MergedResult.GetValue: sumobj.Add(%s)"%(rootrepr(obj)),verb,2)
        sumobj.Add(obj)
      elif sumw==0: # add a number (or any object with __add__ operator), e.g. an integer / floating number
        LOG.verb("MergedResult.GetValue: sumobj += %s"%(rootrepr(obj)),verb,2)
        sumobj += obj
      else: # add a weighted number
        LOG.verb("MergedResult.GetValue: sumobj += %s*%s"%(sumw,obj),verb,2)
        sumobj  += sumw*obj # weighted (total sum will be normalized)
        totsumw += sumw # for later normalization
    if totsumw!=0: # normalize final result to total sum-of-weights
      LOG.verb("MergedResult.GetValue: sumobj *= 1./%s (normalizing to sum-of-weights)"%(totsumw),verb,2)
      sumobj *= 1./totsumw # normalize
      self.sumw = totsumw # save for next GetValue step in recursion
    return sumobj
  

class ResultDict(): #object
  """Container class for a dictionary of RDF results (RDF.RResultPtr<T>).
  ResultDict is basically a set of nested dictionaries plus some helper functions:
    results_dict = {
      selection1: {
        variable1: {
          sample1: RDF.RResultPtr<T>, # where T = TH1D, etc.
          sample2: RDF.RResultPtr<T>,
        }
      }
    }
  This class allows to you to
  1) collect a number of RDF.RResultPtr<T>, organized by selection, variable, and sample;
  2) trigger the RDataFrame event loop for all results simultaneously with ResultDict.run();
  3) retrieve the results (e.g. booked T=TH1D histograms) with ResultDict.itervalues().
  """
  
  def __init__(self,res_dict=None,**kwargs):
    self._dict = { } # { selection : { variable: { sample: RDF.RResultPtr<T> } } } }
    if res_dict!=None: # assume dict or ResultDict
      self.update(res_dict,**kwargs)
  
  def __repr__(self):
    return repr(self._dict)
  
  def display(self,pre=">>>   ",compact=1):
    for sel in self._dict:
      print("%s%r:"%(pre,sel.filename))
      for j, var in enumerate(self._dict[sel]):
        vkey = "(%r,%r)"%(var[0].filename,var[1].filename) if isinstance(var,tuple) else\
               repr(var.filename) if hasattr(var,'filename') else repr(var)
        if compact==0: # new line per sample
          print("%s  %s:"%(pre,vkey))
          for sample, result in self._dict[sel][var].items():
            name = color(sample.name,'grey',b=True)
            print("%s    '%s': %s"%(pre,name,result))
        else: # group samples into a list in one line
          print("%s  %s: { %s }"%(pre,vkey,
            ', '.join("'%s': %r"%(color(s.name,'grey',b=True),r)
                      for s, r in self._dict[sel][var].items())))
    return self
  
  def __getitem__(self,selection):
    """Get nested dict for given selection key (do not create one if not exists)."""
    return self._dict.get(selection,None) # should be dict
  
  def __setitem__(self,selection,value):
    """Set nested dict of given selection key."""
    self._dict[selection] = value # should be dict
  
  def __len__(self):
    """Return number of result objects."""
    #return sum(len(self._dict[s][v]) for s in self._dict for v in self._dict[s])
    return sum(sum((len(r) if isinstance(r,MergedResult) else 1) for r in self._dict[s][v].values())
               for s in self._dict for v in self._dict[s])
  
  def __iter__(self):
    """Return iterator over results dictionary.
    Yields two keys (selection, variable), two lists (Samples, and the values of RDF.RResultPtr<T>).
    Note: This triggers the RDataFrame event loop if it has not run before."""
    return self.itervalues(value=True,context=True)
  
  def keys(self):
    return self._dict.keys()
  
  def items(self,value=False,context=True,clean=False,style=True,verb=0):
    """Return iterator over results dictionary.
    Yields three keys (selection, variable, sample), one value (RDF.RResultPtr<T>).
    Note: This triggers the RDataFrame event loop it has not run before and if value==True."""
    for sel in self._dict:
      for var in self._dict[sel].keys():
        if context and hasattr(var,'changecontext'):
          var.changecontext(sel,verb=verb)
        for sample, result in self._dict[sel][var].items():
          if value: # get values via RDF.RResultPtr.GetValue or MergedResult.GetValue
            # NOTE: This triggers event loop if not run before !
            # NOTE: If MergedResult, its values are (recursively) summed
            value = result.GetValue()
            if style: # set fill/line/marker color
              sample.stylehist(value)
            yield sel, var, sample, value # 3 keys, 1 value
          elif isinstance(result,MergedResult):
            for subresult in result: # note: can be recursive
              yield sel, var, sample, subresult # 3 keys, 1 value (RDF.RResultPtr)
          else: # assume RDF.RResultPtr<T>
            yield sel, var, sample, result # 3 keys, 1 value
        if clean: # remove nested dictionary to clean memory
          self._dict[sel].pop(var,None)
  
  def itervalues(self,value=True,context=True,clean=False,style=True,verb=0):
    """Return iterator over results dictionary.
    Yields two keys (selection, variable), two lists (Samples, and the values of RDF.RResultPtr<T>).
    Note: This triggers the RDataFrame event loop it has not run before and if value==True."""
    for sel in self._dict:
      for var in list(self._dict[sel].keys()):
        if context and hasattr(var,'changecontext'):
          var.changecontext(sel,verb=verb)
        samples = [ ] # list of Sample objects
        values  = [ ] # list of RDF.RResultPtr<T> (value==False) or its value (value==True)
        for sample, result in self._dict[sel][var].items():
          samples.append(sample) # ensure order preserved w.r.t. values list
          if value: # get values via RDF.RResultPtr.GetValue or MergedResult.GetValue
            # NOTE: This triggers event loop if not run before !
            # NOTE: If MergedResult, its values are summed
            value = result.GetValue()
            if style: # set fill/line/marker color
              sample.stylehist(value)
            values.append(value)
          else: # return RDF.RResultPtr<T> values
            values.append(result)
        yield sel, var, samples, values # 2 keys, 2 lists
        if clean: # remove nested dictionary to clean memory
          self._dict[sel].pop(var,None)
  
  def iterhists(self,*args,**kwargs):
    """Alias of itervalues for human readability."""
    return self.itervalues(*args,**kwargs)
  
  def gethists(self,single=False,style=True,clean=False):
    """Organize histograms into HistSet."""
    hist_dict = HistDict() # { selection : { variable: { sample: TH1 } } }
    for sel in self._dict:
      hist_dict[sel] = { }
      for var in list(self._dict[sel].keys()):
        keys = list(self._dict[sel][var].keys()) # sample key list
        if len(keys)==0: # no samples / histogram for these selection/variable keys
          LOG.warn("ResultDict.gethists: Found no sample key for sel=%r, var=%r in self._dict=%r... Ignoring..."%(
            sel,var,self._dict))
        elif single: # return single histogram { selection : { variable: TH1 } }
          if len(keys)>=2: # expected exactly one key, but got two or more...
            LOG.warn("ResultDict.gethists: single=%r, but found more than one sample key for sel=%r, var=%r (%r) in self._dict=%r... Only getting the first"%(
              single,keys,sel,var,self._dict))
          sample = keys[0] # only keep first sample key
          hist = self._dict[sel][var][sample].GetValue() # get values via RDF.RResultPtr<TH1D>.GetValue or MergedResult.GetValue
          if style: # set fill/line/marker color
            sample.stylehist(hist)
          hist_dict[sel][var] = hist
        else: # return multiple sample-histograms with { selection : { variable: { sample: TH1 } } }
          hist_dict[sel][var] = { }
          for sample in keys:
            hist = self._dict[sel][var][sample].GetValue() # get values via RDF.RResultPtr<TH1D>.GetValue or MergedResult.GetValue
            if style: # set fill/line/marker color
              sample.stylehist(hist)
            hist_dict[sel][var][sample] = hist
        if clean: # remove nested dictionary to clean memory
          self._dict[sel].pop(var,None)
    return hist_dict
  
  def gethistsets(self,style=True,clean=False):
    """Organize histograms into HistSet objects."""
    histset_dict = HistDict() # { selection : { variable: HistSet } }
    for sel in self._dict:
      histset_dict[sel] = { }
      for var in list(self._dict[sel].keys()):
        histset = HistSet(var=var,sel=sel)
        for sample, result in self._dict[sel][var].items():
          # NOTE: This triggers event loop if not run before !
          # NOTE: If MergedResult, its histograms are (recursively) summed
          hist = result.GetValue() # get values via RDF.RResultPtr<TH1D>.GetValue or MergedResult.GetValue
          if style: # set fill/line/marker color
            sample.stylehist(hist)
          if sample.isdata: # observed data
            histset.data = hist
          elif sample.issignal: # signal
            histset.sig.append(hist)
          else: # exp (background)
            histset.exp.append(hist)
        histset_dict[sel][var] = histset
        if clean: # remove nested dictionary to clean memory
          self._dict[sel].pop(var,None)
    return histset_dict
  
  def results(self):
    """Return simple list of results, used in ResultDict.run to trigger RDataFrame
    event loop simultaneously with RDF.RunGraphs."""
    results = [r[-1] for r in self.items()]
    return results
  
  def __add__(self,new_res_dict):
    """Update dictionary with other dictionary."""
    #print(">>> ResultDict.__add__")
    return self.update(new_res_dict)
  
  def update(self,new_res_dict,warn=True):
    """Update dictionary with other dictionary."""
    #print(">>> ResultDict.update %r\n>>> with %r"%(self,new_res_dict))
    assert isinstance(new_res_dict,(dict,ResultDict)),\
      "ResultDict.update only takes dictionaries or other ResultDict instances! Got: %r"%(new_res_dict)
    for sel in new_res_dict.keys(): # LEVEL 1: loop over selections
      self._dict.setdefault(sel,{ }) # create nested dictionary if it does not exists yet
      for var in new_res_dict[sel]: # LEVEL 2: loop over variables
        self._dict[sel].setdefault(var,{ }) # create nested dictionary if it does not exists yet
        for sample in new_res_dict[sel][var]: # LEVEL 3: loop over samples
          if warn and sample in self._dict[sel][var]: # give warning about overwriting
            LOG.warn("ResultDict.update: Overwriting result of sample %r for sel=%r, var=%r"%(sample,sel,var))
          self._dict[sel][var][sample] = new_res_dict[sel][var][sample]
    return self
  
  def add(self,*args,**kwargs):
    """Add new result."""
    #print(">>> ResultDict.add(%r)"%(args,))
    if len(args)==4: # add one new result for (selection,variable,sample)
      sel, var, sample, result = args
      self._dict.setdefault(sel,{ }).setdefault(var,{ }) # create nested dictionaries if it does not exists yet
      if kwargs.get('warn',True) and sample in self._dict[sel][var]: # give warning about overwriting
        LOG.warn("ResultDict.add: Overwriting result of sample %r for sel=%r, var=%r"%(sample,sel,var))
      self._dict[sel][var][sample] = result
      return result
    elif len(args)==1 and isinstance(args[0],(dict,ResultDict)): # add new ResultDict
      return self.update(args[0],**kwargs) # update self._dict iteratively
    else:
      raise IOError("ResultDict.add: Did not recognize arguments: %r"%(args,))
  
  def merge(self,sample,name=None,title=None,verb=0):
    """Merge results into MergedResult so they can be summed later into a single object for a MergedSample.
    Replace last nested dictionary for multiple samples into dictionary with one given MergedSample."""
    nterms = -1 # count number of elements, to ensure consistent for all results
    LOG.verb("ResultDict.merge: Merge results for %r"%(sample),verb,2)
    for sel in self._dict:
      for var in self._dict[sel]:
        LOG.verb("ResultDict.merge: Merge %r: %r"%(sample,list(self._dict[sel][var].values())),verb,3)
        vname   = "%s_vs_%s"%(var[1].filename,var[0].filename) if isinstance(var,tuple) else\
                  var.filename if hasattr(var,'filename') else str(var)
        hname   = name.replace('$VAR',vname) if isinstance(name,str) else name
        results = MergedResult(self._dict[sel][var].values(),name=hname,title=title,verb=verb)
        self._dict[sel][var] = { sample: results } # replace nested dictionary with on sample
        if nterms<=0: # set first time
          nterms = len(results)
        elif len(results)!=nterms: # number of results inconsistent !
          LOG.warn("ResultDict.merge: Number of results is inconsistent! Expected %s terms, got %s for sel=%r, var=%r"%(
            nterms,len(results),sel,var))
    return self
  
  @staticmethod
  def setnthreads(*args,**kwargs):
    """Set number of threads via RDF namespace (see TauFW/common/python/tools/RDataFrame.py)."""
    return RDF.SetNumberOfThreads(*args,**kwargs)
  
  def run(self,graphs=True,rdf_dict=None,dot=False,verb=0):
    """Run RDataFrame events loops (filling histograms, etc.)."""
    
    # PREPARE REPORTS & DOT GRAPH
    reports = [ ]
    if (dot or verb>=2) and isinstance(rdf_dict,dict): # add RDataFrame reports of selections
      for keys, value in rdf_dict.items():
        if len(keys)==2 and isinstance(value,RDataFrame):
          reports.append((keys[1],value.Report()))
          if dot: # make graphical representation of RDataFrame's structure
            if isinstance(dot,str): # print to file
              name  = keys[1].split('/')[-1].replace('.root','')
              fname = dot.replace('$NAME',name)
              print(">>> ResultDict.run: dot for %r, print to dot=%r"%(keys[1],fname))
              RDF.SaveGraph(value,fname)
            else: # print to screen
              print(">>> ResultDict.run: dot for %r, dot=%r"%(keys[1],dot))
              RDF.SaveGraph(value) # display with e.g. https://edotor.net
    
    # RUN ALL RDATAFRAMES
    results = self.results() # get list of RDF.RResultPtr<T> objects
    start = time.time(), time.process_time() # wall-clock & CPU time
    if not results:
      LOG.warn("ResultDict.run: Did not get any results to run... self._dict=%r"%(self._dict))
    elif graphs: # should be faster for large number of results in parallel
      LOG.verb("ResultDict.run: Start RunGraphs of %s results with %s threads..."%(len(results),ROOT.GetThreadPoolSize()),verb,1)
      RDF.RunGraphs(results) # run results concurrently
    else: # trigger sequentially (might be slower)
      LOG.verb("ResultDict.run: Start GetValue of %s RDF results with %s threads..."%(len(results),ROOT.GetThreadPoolSize()),verb,1)
      for result in results: # run results one-by-one
        result.GetValue() # trigger event loop
    RDF.StopProgressBar(" in %s with %s threads"%(took(*start),ROOT.GetThreadPoolSize()))
    
    # PRINT REPORTS
    for fname, report in reports:
      print(">>> ResultDict.run: Report %r:"%(fname))
      printRDFReport(report,reorder=True)
    
    return self
    

from TauFW.Plotter.sample.utils import LOG
from TauFW.Plotter.sample.HistSet import HistSet, HistDict # to contain histograms
