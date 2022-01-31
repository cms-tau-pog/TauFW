# Author: Izaak Neutelings (May 2020)
from math import log10, floor
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
    assert all(index!=i for n,i in self.cuts.iteritems()), "Index %d for %r already in use! Taken: %s"%(index,name,self.cuts)
    #assert not hasattr(self,name), "%s already has attribute '%s'!"%(self,name)
    #setattr(self,name,index)
    bin = 1+index # range 0-ncuts, bin numbers 1-(ncuts+1)
    self.hist.GetXaxis().SetBinLabel(bin,title)
    self.cuts[name] = index
  
  def fill(self, cut, *args):
    """Full histogram. Allow for possible weight."""
    assert cut in self.cuts, "Did not find cut '%s'! Choose from %s"%(cut,self.cuts)
    index = self.cuts[cut]
    self.hist.Fill(index,*args)
  
  def display(self,nfinal=None,final="Final selection"):
    """Print cutflow."""
    if not self.cuts: return
    print ">>> Cutflow:"
    ntot = self.hist.GetBinContent(1)
    #padcut = 3+max(len(c) for c in self.cuts)
    values = [self.hist.GetBinContent(1+i) for k, i in self.cuts.items() if self.hist.GetBinContent(1+i)>0] # all values > 0
    padevt = 4+(int(floor(log10(max(values)))) if values else 0)
    denstr = str(ntot).rjust(int(floor(log10(ntot)))+2) if ntot else " 0"
    for cut, index in sorted(self.cuts.items(),key=lambda x: x[1]):
      nevts = self.hist.GetBinContent(1+index)
      title = self.hist.GetXaxis().GetBinLabel(1+index) or cut
      frac  = "= %6.2f%%"%(100.0*nevts/ntot) if ntot else " "
      nomstr = str(nevts).rjust(padevt)
      print ">>> %4d: %s / %s %s   %s"%(index,nomstr,denstr,frac,title) #.rjust(padcut)
    if nfinal!=None:
      frac  = "= %6.2f%%"%(100.0*nfinal/ntot) if ntot else " "
      nomstr = str(float(nfinal)).rjust(padevt)
      print ">>> %5s %s / %s %s   %s"%("",nomstr,denstr,frac,final)
    
  