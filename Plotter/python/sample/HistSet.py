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
  
  def __init__(self, data=None, exp=None, sig=None, var=None, sel=None):
    #print(">>> HistSet.__init__: var=%r, sel=%r"%(var,sel))
    self.data = data # data histogram
    self.exp  = exp or [ ] # list of background histograms (Drell-Yan, ttbar, W+jets, ...), to be stacked
    self.sig  = sig or [ ] # list of signal histograms (for new physics searches)
    self.var  = var  # variable object
    self.sel  = sel  # selection object for changing variable context
    if isinstance(data,dict): # data = { sample: hist } dictionary
      self.data = None
      for sample, hist in data.items():
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
        variable1: HistSet,
        variable2: HistSet,
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
            TAB.printheader("Integral","Entries","Ave. weight","Hist name    ")
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
        if len(results[sel])>=2:
          LOG.warn("HistDict.results: singlevar=%r, singlesel=%r, but found more than one selection key in self._dict=%r"%(
            singlevar,singlesel,self._dict))
        if len(results[sel])==0: # no variables/hists
          results.pop(sel) # delete nested dictionary
        else:
          varkey = list(results[sel].keys())[0] # get first (and only?) key
          results[sel] = results[sel][varkey]
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