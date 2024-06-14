# Author: Izaak Neutelings (May 2020)
from math import log10, floor
from TauFW.common.tools.log import underline
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TH1D


class Cutflow(object):
  """Container class for cutflow."""
  
  def __init__(self, histname, ncuts, **kwargs):
    self.hist    = TH1D('cutflow','cutflow',ncuts,0,ncuts)
    self.hist.GetXaxis().SetLabelSize(0.041)
    self.nextidx = 0
    self.cuts    = { }
  
  def addcut(self, name, title, index=None):
    if index==None:
      index = self.nextidx
      self.nextidx += 1
    assert all(index!=i for n,i in self.cuts.items()), "Index %d for %r already in use! Taken: %s"%(index,name,self.cuts)
    #assert not hasattr(self,name), "%s already has attribute '%s'!"%(self,name)
    #setattr(self,name,index)
    bin = 1+index # range 0-ncuts, bin numbers 1-(ncuts+1)
    self.hist.GetXaxis().SetBinLabel(bin,title)
    self.cuts[name] = index
    
  def getbincontent(self,bin):
    if isinstance(bin,str):
      bin = self.hist.GetXaxis().FindBin(bin)
    return self.hist.GetBinContent(bin)
  
  def fill(self, cut, *args):
    """Full histogram. Allow for possible weight."""
    assert cut in self.cuts, "Did not find cut '%s'! Choose from %s"%(cut,self.cuts)
    index = self.cuts[cut]
    self.hist.Fill(index,*args)
  
  def display(self,itot=None,nfinal=None,final="Final selection"):
    """Print cutflow."""
    if not self.cuts: return
    if itot==None:
      itot = self.cuts.get('none',1) # assume first bin has total number of processed events 
    ntot  = self.hist.GetBinContent(itot) # total number of processed events before any cuts
    nlast = (-999,ntot)
    #padcut = 3+max(len(c) for c in self.cuts) # padding
    values = [self.hist.GetBinContent(1+i) for k, i in self.cuts.items() if self.hist.GetBinContent(1+i)>0] # all values > 0
    maxval = max(abs(x) for x in values) if values else 0 # maximum value
    padevt = 4+(int(floor(log10(maxval))) if maxval>0 else 0) # pad all numbers of events
    padtot = 3+(int(floor(log10(ntot))) if ntot>0 else 0) # pad total number of events
    denstr = str(ntot).rjust(padtot) if ntot else " 0"
    print(underline("Cutflow:"+' '*(46+padevt+padtot),pre=">>> "))
    print(underline("%5s %5s / %5s = %-8s %-8s  %-23s"%( # header
      '','npass'.rjust(padevt),'ntot'.rjust(padtot),'abseff','releff','cut'),pre=">>> "))
    for cut, index in sorted(self.cuts.items(),key=lambda x: x[1]):
      nevts = self.hist.GetBinContent(1+index)
      title = self.hist.GetXaxis().GetBinLabel(1+index) or cut
      frac  = " "
      frac2 = " "
      if ntot:
        frac  = "= %6.2f%%"%(100.0*nevts/ntot) # absolute efficiency
        frac2 = "%4.2f%%"%(100.0*(nevts/nlast[1])) if nlast[1] and index==nlast[0]+1 else ' '  # relative efficiency w.r.t. last cut
      nomstr = ("%.1f"%nevts).rjust(padevt)
      #print ">>> %4d: %s / %s %s   %s"%(index,nomstr,denstr,frac,title) # without rel. eff.
      print(">>> %4d: %5s / %5s %s %8s   %s"%(index,nomstr,denstr,frac,frac2,title)) # with rel. eff.
      nlast = (index,nevts) # for next iteration
    if nfinal!=None:
      frac  = "= %6.2f%%"%(100.0*nfinal/ntot) if ntot else ' '
      nomstr = str(float(nfinal)).rjust(padevt)
      print(underline("%5s %5s / %5s %s %8s   %-23s"%('',nomstr,denstr,frac,'',final),pre=">>> "))
    
  
