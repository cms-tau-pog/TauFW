# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
# Description: Container class for histgrams lists to separate those of observed data from MC.
from TauFW.Plotter.plot.Stack import Stack, THStack, TH1


def integratehist(hist):
  if hist.InheritsFrom('TH2'):
    return hist.Integral(0,hist.GetXaxis().GetNbins()+1,0,hist.GetYaxis().GetNbins()+1)
  else:
    return hist.Integral(0,hist.GetXaxis().GetNbins()+1)


class HistSet(object):
  """Container class for histgrams lists to separate those of observed data from MC."""
  
  def __init__(self, data=None, exp=None, sig=None, var=None, sel=None, style=False):
    #print(">>> HistSet.__init__: var=%r, sel=%r"%(var,sel))
    self.data = data # single data TH1D histogram
    self.exp  = exp or [ ] # list of background TH1D histograms (Drell-Yan, ttbar, W+jets, ...), to be stacked
    self.sig  = sig or [ ] # list of signal TH1D histograms (for new physics searches), to be overlaid
    self.var  = var  # Variable object
    self.sel  = sel  # Selection object for changing variable context
    if isinstance(data,dict): # data = { sample: hist } dictionary
      self.data = None
      for sample, hist in data.items():
        if style: # set fill/line/marker color
          sample.stylehist(hist)
        if sample.isdata: # observed data
          self.data = hist
        elif sample.issignal: # signal
          self.sig.append(hist)
        else: # exp (background)
          self.exp.append(hist)
  
  def __iter__(self):
    """Return iterator over all histograms dictionary."""
    if self.data:
      yield self.data
    for hist in self.exp:
      yield hist
    for hist in self.sig:
      yield hist
  
  def all(self):
    """Return list of all histgrams."""
    return list(iter(self))
  
  def display(self):
    """Print tables of histogram yields (for debugging)."""
    TAB = LOG.table("%13.2f %13d %13.3f   %r")
    TAB.printheader("Integral","Entries","Ave. weight","Hist name    ")
    totent = 0
    totint = 0
    def row(hist):
      hint, hent = integratehist(hist), hist.GetEntries()
      return (hint, hent, hint/hent if hent!=0 else -1, hist.GetName())
    if self.data:
      TAB.printrow(*row(self.data))
    for hist in self.exp:
      hint, hent, wgt, name = row(hist)
      TAB.printrow(hint,hent,wgt,name)
      totent += hint
      totint += hent
    TAB.printrow(totint,totent,totint/totent if totent!=0 else -1,"total exp.")
    for hist in self.sig:
      TAB.printrow(*row(hist))
    return totent, totint
    
  def getstack(self, var=None, context=None, **kwargs):
    """Create and return a Stack object."""
    verb = kwargs.get('verb', 0)
    if var==None: # for initiation of Plot object
      var = self.var
    if self.sel!=None and context==None: # for setting context of Variable object
      context = self.sel
    LOG.verb("HistSet.getstack: context=%r, var=%r, self.var=%r, self.sel=%r"%(context,var,self.var,self.sel),verb,2)
    if context!=None and hasattr(var,'changecontext'):
      var.changecontext(context,verb=verb)
    stack = Stack(var,self.data,self.exp,self.sig,**kwargs)
    return stack # return Stack object
  
  def getTHStack(self, name='stack', **kwargs):
    """Create and return a THStack of backgrounds histograms."""
    stack = THStack(name,name)
    for hist in reversed(self.exp):
      stack.Add(hist)
    return stack # return THStack object
  

class HistDict(object):
  """Container class for nested dictionaries of TH1 objects.
  HistDict is basically a set of nested dictionaries plus some helper functions:
    hist_dict = {
      selection1: {
        variable1: TH1,
        variable2: TH1,
      }
    }
  """
  
  def __init__(self,histdict=None,**kwargs):
    if histdict==None:
      histdict = { } # create new empty dictionary
    self._dict = histdict # { selection : { variable: HistSet } }
  
  @staticmethod
  def init_from_dict(result_dict,single=False,style=True,clean=False):
    """Static method to initiate HistDict from given ResultDict."""
    #print(f">>> HistDict.init_from_dict: single={single!r}, style={style!r}, clean={clean!r}, result_dict={result_dict}")
    hist_dict = HistDict() # { selection : { variable: { sample: TH1 } } }
    for sel in result_dict:
      hist_dict[sel] = { }
      for var in list(result_dict[sel].keys()):
        samples = list(result_dict[sel][var].keys()) # sample key list
        if len(samples)==0: # no samples / histogram for these selection/variable keys
          LOG.warn(f"HistDict.init_from_ResultDict: Found no sample key for sel={sel!r}, "
                   f"var={var!r} in result_dict={result_dict!r}... Ignoring...")
        elif single and len(samples)>=2: # expected exactly one key, but got two or more...
          LOG.warn(f"HistDict.init_from_ResultDict: single={single!r}, but found more than one sample key for "
                   f"sel={sel!r}, var={var!r} ({samples!r}) in result_dict={result_dict!r}... Only getting the first...")
          samples = [samples[0]] # reduce to single sample
        for sample in samples:
          result = result_dict[sel][var][sample]
          if isinstance(result,TH1):
            hist = result
          else: # assume RDF.RResultPtr<TH1D> or MergedResult
            # NOTE: This triggers event loop if not run before !
            # NOTE: If MergedResult, its histograms are (recursively) summed
            hist = result.GetValue() # get values via RDF.RResultPtr<TH1D>.GetValue or MergedResult.GetValue
          if style: # set fill/line/marker color
            sample.stylehist(hist)
          if single: # return single histogram { selection : { variable: TH1 } }
            hist_dict[sel][var] = hist
            break # only keep first sample key
          else: # return { selection : { variable: { sample: TH1 } } }
            hist_dict[sel].setdefault(var,{ })[sample] = hist
        if clean: # remove nested dictionary to clean memory
          result_dict[sel].pop(var,None)
    return hist_dict
  
  def __getitem__(self,selection):
    """Get nested dict for given selection key (do not create one if not exists)."""
    return self._dict.get(selection,None) # should be dict
  
  def __setitem__(self,selection,value):
    """Set nested dict of given selection key."""
    self._dict[selection] = value # should be dict
  
  def __len__(self):
    """Return number of selection x variables."""
    return sum(len(self._dict[s][v].values() for s in self._dict for v in self._dict[s]))
  
  def __iter__(self):
    """Return iterator over results dictionary."""
    return iter(self._dict)
  
  def display(self,nvars=1):
    """Print tables of histogram yields (for debugging)."""
    for sel in self._dict:
      for i, var in enumerate(self._dict[sel]):
        if nvars>=1 and i>=nvars: break
        histset = self._dict[sel][var]
        #print(f"histset={histset!r}")
        vstr = "(%r,%r)"%(var[0].filename,var[1].filename) if isinstance(var,tuple) else\
               repr(var.filename) if hasattr(var,'filename') else repr(var)
        if isinstance(histset,dict) and any(isinstance(h,TH1) for h in histset.values()): # { sample: hist }
          histset = HistSet(histset) # convert dictionary to HistSet for easy display
        if isinstance(histset,HistSet):
          print(">>> Histogram yields for selection %r, variable %s:"%(sel.selection,vstr))
          histset.display()
        elif isinstance(histset,TH1): # TH1 histogram
          hist = histset
          if i==0: # only print first time
            print(">>> Histogram yields for selection %r, variable %s:"%(sel.selection,vstr))
            TAB = LOG.table("%13.2f %13d %13.3f   %r")
            TAB.printheader("Integral","Entries","Ave. weight","Hist name      ")
          hint, hent = integratehist(hist), hist.GetEntries()
          TAB.printrow(hint, hent, hint/hent if hent!=0 else -1, hist.GetName())
        elif isinstance(histset,dict): # assume { sample: number value }
          for sample, value in histset.items():
            if i==0: # only print first time
              print(">>> Number value:")
              TAB = LOG.table("%15.4f  %-15s %-15s %r")
              TAB.printheader("Number","Sample","Variable","Selection"+' '*20)
            TAB.printrow(value,sample.name,vstr,sel.selection)
        else: # assume { sample: number value }
          value = histset
          if i==0: # only print first time
            print(">>> Number value:")
            TAB = LOG.table("%15.4f  %-15s %r")
            TAB.printheader("Number","Variable","Selection"+' '*20)
          TAB.printrow(value,vstr,sel.selection)
  
  def insert(self,hist_dict,idx=-1,verb=0):
    """Insert histograms per selection/variable."""
    for selection in hist_dict:
      assert selection in self._dict, "HistDict.insert: Unrecognized selection %r... hist_dict=%r, self._dict=%r"%(selection,hist_dict,self._dict)
      for variable in hist_dict[selection]:
        assert variable in self._dict[selection], "HistDict.insert: Unrecognized variable %r for selection%r... hist_dict=%r, self._dict=%r"%(
          variable,selection,hist_dict,self._dict)
        hist = hist_dict[selection][variable] # TH1D histogram
        idx_ = idx if idx>=0 else len(self._dict[selection][variable].exp)+1+idx # if index negative: count from end of list
        LOG.verb("HistDict.insert: Inserting=%r at index %r (%r)"%(hist,idx_,idx),verb,2)
        self._dict[selection][variable].exp.insert(idx_,hist)
  
  def results(self,singlevar=False,singlesel=False,popvar=None):
    """Return simple nested dictionaries. { selection: { variable: HistSet } }
    Convert for just a single variable (issinglevar==True), and/or single selection (issinglesel==True)."""
    results = self._dict
    if popvar!=None: # remove variable from dictionary (used by Sample.getmean)
      for sel in results:
        results[sel].pop(popvar,None)
    if singlevar: # convert result to { selection: HistSet }
      for sel in results.keys():
        varkeys = list(results[sel].keys())
        if len(varkeys)>=2:
          LOG.warn(f"HistDict.results: singlevar={singlevar!r}, singlesel={singlesel!r}, but found more than one variable key ({varkeys}) in self._dict={self._dict}")
        if len(varkeys)==0: # no variables/hists at all !
          results.pop(sel) # delete empty nested dictionary
        else:
          varkey = varkeys[0] # get first (and only?) key
          results[sel] = results[sel][varkey] # replace nested dictionary with its only value
    if singlesel: # convert result to { variable: HistSet } or if singlevar==True: a single HistSet
      if len(results)>=2:
        LOG.warn(f"HistDict.results: singlevar=%r, singlesel=%r, but found more than one selection key in self._dict=%r"%(
          singlevar,singlesel,self._dict))
      if len(results)==0: # no selections at all !
        results = HistSet() if isinstance(self,HistSetDict) else None # empty hist set
      else:
        selkey  = list(results.keys())[0] # get first (and only?) key
        results = results[selkey] # get single nested dictionary or HistSet
    return results
  

class HistSetDict(HistDict):
  """Container class for nested dictionaries of HistSet objects.
  HistSetDict is basically a set of nested dictionaries plus some helper functions:
    hist_dict = {
      selection1: {
        variable1: HistSet,
        variable2: HistSet,
      }
    }
  """
  
  @staticmethod
  def init_from_dict(result_dict,style=True,clean=False):
    """Static method to initiate HistDict from given ResultDict."""
    #print(f">>> HistDict.init_from_dict: style={style!r}, clean={clean!r}, result_dict={result_dict}")
    histset_dict = HistSetDict() # { selection : { variable: { sample: HistSet } } }
    for sel in result_dict:
      histset_dict[sel] = { }
      for var in list(result_dict[sel].keys()):
        histset = HistSet(var=var,sel=sel)
        for sample, result in result_dict[sel][var].items():
          if isinstance(result,TH1):
            hist = result
          else: # assume RDF.RResultPtr<TH1D> or MergedResult
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
          result_dict[sel].pop(var,None)
    return histset_dict
  

class StackDict(dict):
  """Container class for a nested dictionary of Stack or THStack objects.
  StackDict is basically a set of nested dictionaries plus some helper functions:
    stack_dict = { selection: { variable: stack } }
  This class is used by Sample(Set).getstack & Sample(Set).getTHStack and is meant
  to gives the user some flexibility on how to iterate of stack objects in few lines.
  If you iterate over a StackDict, it will yield the stack objects, e.g.
    for stack in stack_dict:
      stack.draw()
  If you use StackDict.items, it will yield also a 2-tuple of the respective (variable,selection):
    for stack, (variable,selection) in stack_dict.items():
      stack.draw()
  If you use StackDict.keys or StackDict.selections, it will yield the selections keys instead:
    for selection in stack_dict.selections():
      for variable in stack_dict[selection]:
        stack_dict[selection][variable].draw()
  """
  
  def __init__(self,stacks,**kwargs):
    self.update(stacks) # self = { selection : { variable: { stack } } } }
  
  @staticmethod
  def init_from_HistDict(histset_dict,singlevar=False,singlesel=False,thstack=False,style=False,**kwargs):
    """Static method to initiate StackDict from given HistDict or HistSetDict.
    Called in Sample(Set).getstack & Sample(Set).getTHStack.
    If there's a single stack for a single pair of variables and selections,
    return single Stack/THStack object instead."""
    stacks = { }
    for selection in histset_dict:
      for variable, histset in histset_dict[selection].items():
        if isinstance(histset,dict):
          histset = HistSet(histset,style=style) # convert { sample: TH1 } to HistSet
        if thstack: # ROOT THStack object
          stack = histset.getTHStack(**kwargs) # create ROOT THStack object
        else: # TauFW Stack object
          stack = histset.getstack(var=variable,context=selection,**kwargs) # create Stack object
        if singlevar and singlesel:
          return stack # return single Stack/THStack object instead of StackDict
        stacks.setdefault(selection,{ })[variable] = stack # { selection : { variable: { stack } } } }
    return StackDict(stacks,**kwargs)
  
  def selections(self):
    """Return list of selection keys (instead of Stack/THStack objects)."""
    return list(dict.keys(self))
  
  def __iter__(self):
    """Return iterator over stacks. Yield just Stack/THStack object."""
    for stack, _ in self.items():
      yield stack
  
  def items(self):
    """Return iterator over dictionary. Yield (stack,(variable,selection))"""
    for selection in self.keys():
      for variable in self[selection]:
        stack = self[selection][variable]
        yield (stack,(variable,selection))
  

from TauFW.Plotter.sample.utils import LOG