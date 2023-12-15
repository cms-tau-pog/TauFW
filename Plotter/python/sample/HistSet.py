# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
# Description: Container class for histgrams lists to separate those of observed data from MC.
from TauFW.Plotter.plot.Stack import Stack, THStack


class HistSet(object):
  """Container class for histgrams lists to separate those of observed data from MC."""
  
  def __init__(self, data=None, exp=[ ], sig=[ ], var=None, sel=None):
    #print(">>> HistSet.__init__: var=%r, sel=%r"%(var,sel))
    self.data = None # data histograms
    self.exp  = [ ]  # background histograms (Drell-Yan, ttbar, W+jets, ...), to be stacked
    self.sig  = [ ]  # signal histograms (for new physics searches)
    self.var  = var  # variable object
    self.sel  = sel  # selection object for changing variable context
  
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
  
  def getstack(self, var=None, context=None, **kwargs):
    """Create and return a Stack object."""
    verb = kwargs.get('verb', 0)
    if var==None:
      var = self.var
    if self.sel!=None and context==None:
      context = self.sel
    LOG.verb("HistSet.getstack: context=%r, var=%r, self.var=%r, self.sel=%r"%(context,var,self.var,self.sel),verb,2)
    if context!=None and hasattr(var,'changecontext'):
      var.changecontext(context,verb=verb)
    stack = Stack(var,self.data,self.exp,self.sig,**kwargs)
    return stack
  
  def getTHStack(self, context=None, **kwargs):
    """Create and return a THStack of backgrounds histograms."""
    sname = kwargs.get('name',"stack")
    stack = THStack(sname,sname)
    for hist in reversed(self.exp):
      stack.Add(hist)
    return stack # THStack
  

class HistDict(object):
  """Container class for nested dictionaries of HistSets.
  HistDict is basically a set of nested dictionaries plus some helper functions:
    hist_dict = {
      selection1: {
        variable1: HistSet
        variable2: HistSet
      }
    }
  """
  
  def __init__(self,res_dict=None,**kwargs):
    self._dict = { } # { selection : { variable: HistSet } }
  
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
        if i>=nvars: break
        print(">>> Histogram yields for selection %r:"%(sel.selection))
        TAB = LOG.table("%13.2f %13d %13.3f   %r")
        TAB.printheader("Integral","Entries","Ave. weight","Hist name    ")
        totent = 0
        totint = 0
        histset = self._dict[sel][var]
        def row(hist):
          hint, hent = hist.Integral(0,hist.GetXaxis().GetNbins()+1), hist.GetEntries()
          return (hint, hent, hint/hent, hist.GetName())
        if histset.data:
          TAB.printrow(*row(histset.data))
        for hist in histset.exp:
          totent += hist.GetEntries()
          totint += hist.Integral()
          TAB.printrow(*row(hist))
        TAB.printrow(totint,totent,totint/totent,"total exp.")
        for hist in histset.sig:
          TAB.printrow(*row(hist))
  
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
  
  def results(self,singlevar=False,singlesel=False):
    """Return simple nested dictionaries.
    Convert for just a single variable, and/or single selection."""
    results = self._dict
    if singlevar: # convert result to { selection: HistSet }
      for sel in results.keys():
        if len(results[sel])>=2:
          LOG.warn("HistDict.results: singlevar=%r, singlesel=%r, but found more than one selection key in self._dict=%r"%(
            singlevar,singlesel,self._dict))
        if len(results[sel])==0: # no variables/hists
          results.pop(sel) # delete nested dictionary
        else:
          varkey = list(results[sel].keys())[0] # get first (and only?) key
          results[sel] = results[varkey]
    if singlesel: # convert result to { variable: HistSet } or if singlevar==True: a single HistSet
      if len(results)>=2:
        LOG.warn("HistDict.results: singlevar=%r, singlesel=%r, but found more than one selection key in self._dict=%r"%(
          singlevar,singlesel,self._dict))
      if len(results)==0: # no selections
        results = HistSet() # empty hist set
      else:
        selkey  = list(results.keys())[0] # get first (and only?) key
        results = results[selkey] # get single nested dictionary or HistSet
    return results
  

from TauFW.Plotter.sample.utils import LOG