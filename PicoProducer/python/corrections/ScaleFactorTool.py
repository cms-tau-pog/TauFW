# Author: Izaak Neutelings (November 2018)
import os, re
from TauFW.common.tools.root import ensureTFile
from TauFW.common.tools.log import Logger
LOG = Logger('ScaleFactorTool')


class ScaleFactor:
  
  def __init__(self, filename, histname, name="<noname>", ptvseta=True, verb=0):
    #print '>>> ScaleFactor.init("%s","%s",name="%s",ptvseta=%r)'%(filename,histname,name,ptvseta)
    self.name     = name
    self.ptvseta  = ptvseta
    self.filename = filename
    self.file, self.hist = self.gethist(filename,histname,verb=verb)
    self.getSF    = self.getSF_ptvseta if ptvseta else self.getSF_etavspt
  
  def gethist(self,filename,histname,verb=0):
    """Help function to retrieve histogram from ROOT file and check axis assignment."""
    LOG.verb("ScaleFactor.gethist(%s): Opening %s:%r..."%(self.name,filename,histname),verb,1)
    try:
      file = ensureTFile(filename)
    except OSError as error:
      if 'HTT' in filename and "does not exist" in filename:
        LOG.throw("OSError: %s You may have to do\n"%(error)+
          "  cd $CMSSW_BASE/src/TauFW/PicoProducer/data/lepton/\n"+
          "  rm -rf HTT\n"+
          "  git clone https://github.com/CMS-HTT/LeptonEfficiencies HTT")
      else:
        raise error
    hist = file.Get(histname)
    LOG.insist(hist,"ScaleFactor(%s): Histogram %r does not exist in %s"%(self.name,histname,filename))
    hist.SetDirectory(0)
    xmin, xmax = hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax()
    ymin, ymax = hist.GetYaxis().GetXmin(), hist.GetYaxis().GetXmax()
    LOG.verb("ScaleFactor.gethist(%s): xmin=%s, xmax=%s, ymin=%s, ymax=%s, ptvseta=%s"%(self.name,xmin,xmax,ymin,ymax,self.ptvseta),verb+2,2)
    if self.ptvseta: # x=eta, y=pt
      if xmax>7: # expect x=eta < 7
        LOG.warn("ScaleFactor.gethist(%s): Please check if x/y axes are assigned correctly as eta/pt (ptvseta=%r)! "%(self.name,self.ptvseta)+
                 "Found limits x=[%s,%s], y=[%s,%s]"%(xmin,xmax,ymin,ymax))
    else: # eta vs. pt: x=pt, y=eta
      if ymax>7: # expect y=eta < 7
        LOG.warn("ScaleFactor.gethist(%s): Please check if x/y axes are assigned correctly as pt/eta (ptvseta=%r)! "%(self.name,self.ptvseta)+
                 "Found limits x=[%s,%s], y=[%s,%s]"%(xmin,xmax,ymin,ymax))
    file.Close()
    return file, hist
  
  def __mul__(self, oScaleFactor):
    return ScaleFactorProduct(self, oScaleFactor)
  
  def getSF_ptvseta(self, pt, eta):
    """Get SF for a given pT, eta."""
    xbin = self.hist.GetXaxis().FindBin(eta)
    ybin = self.hist.GetYaxis().FindBin(pt)
    if xbin==0: xbin = 1
    elif xbin>self.hist.GetXaxis().GetNbins(): xbin -= 1
    if ybin==0: ybin = 1
    elif ybin>self.hist.GetYaxis().GetNbins(): ybin -= 1
    sf = self.hist.GetBinContent(xbin,ybin)
    #print "ScaleFactor(%s).getSF_ptvseta: pt = %6.2f, eta = %6.3f, sf = %6.3f"%(self.name,pt,eta,sf)
    return sf
  
  def getSF_etavspt(self, pt, eta):
    """Get SF for a given pT, eta."""
    xbin = self.hist.GetXaxis().FindBin(pt)
    ybin = self.hist.GetYaxis().FindBin(eta)
    if xbin==0: xbin = 1
    elif xbin>self.hist.GetXaxis().GetNbins(): xbin -= 1
    if ybin==0: ybin = 1
    elif ybin>self.hist.GetYaxis().GetNbins(): ybin -= 1
    sf = self.hist.GetBinContent(xbin,ybin)
    #print "ScaleFactor(%s).getSF_etavspt: pt = %6.2f, eta = %6.3f, sf = %6.3f"%(self.name,pt,eta,sf)
    return sf
    

class ScaleFactorHTT(ScaleFactor):
  
  def __init__(self, filename, graphname='ZMass', name="<noname>", verb=0):
    self.name      = name
    self.filename  = filename
    LOG.verb("ScaleFactor(%s): Opening %s:%r..."%(self.name,filename,graphname),verb,1)
    self.file      = ensureTFile(filename)
    self.hist_eta  = self.file.Get('etaBinsH')
    self.hist_eta.SetDirectory(0)
    self.effs_data = { }
    self.effs_mc   = { }
    for ieta in range(1,self.hist_eta.GetXaxis().GetNbins()+1):
      etalabel = self.hist_eta.GetXaxis().GetBinLabel(ieta)
      self.effs_data[etalabel] = self.file.Get(graphname+etalabel+"_Data")
      self.effs_mc[etalabel]   = self.file.Get(graphname+etalabel+"_MC")
    self.file.Close()
  
  def getSF(self, pt, eta):
    """Get SF for a given pT, eta."""
    #print pt, eta
    abseta = abs(eta)
    etabin = self.hist_eta.GetXaxis().GetBinLabel(min(self.hist_eta.GetXaxis().GetNbins(),self.hist_eta.GetXaxis().FindBin(abseta)))
    data   = self.effs_data[etabin].Eval(pt)
    mc     = self.effs_mc[etabin].Eval(pt)
    if mc==0:
      sf = 1.0
    else:
      sf = data/mc
    #print "ScaleFactorHTT(%s).getSF: pt = %6.2f, eta = %6.3f, data = %6.3f, mc = %6.3f, sf = %6.3f"%(self.name,pt,eta,data,mc,sf)
    return sf
  

class ScaleFactorProduct:
  
  def __init__(self, scaleFactor1, scaleFactor2, name=None):
    if name==None:
      self.name = scaleFactor1.name+'*'+scaleFactor2.name
    else:
      self.name = name
    #print '>>> ScaleFactor(%s).init'%(self.name)
    self.scaleFactor1 = scaleFactor1
    self.scaleFactor2 = scaleFactor2
    self.filename = "%s, %s"%(scaleFactor1.filename,scaleFactor2.filename)
  
  def getSF(self, pt, eta):
    return self.scaleFactor1.getSF(pt,eta)*self.scaleFactor2.getSF(pt,eta)
  

#def getBinsFromTGraph(graph):
#    """Get xbins from TGraph."""
#    x, y  = Double(), Double()
#    xlast  = None
#    xbins = [ ]
#    for i in range(0,graph.GetN()):
#      graph.GetPoint(i,x,y)
#      xlow = float(x) - graph.GetErrorXlow(i)
#      xup  = float(x) + graph.GetErrorXhigh(i)
#      if xlow>=xup:
#        print 'Warning! getBinsFromTGraph: Point i=%d of graph "%s": lower x value %.1f >= upper x value %.1f.'%(i,graph.GetName(),xlow,xup)
#      if xlast!=None and abs(xlast-xlow)>1e-5:
#        print 'Warning! getBinsFromTGraph: Point i=%d of graph "%s": lower x value %.1f does not conincide with upper x value of last point, %.1f.'%(i,graph.GetName(),xlow,xlast)
#      xbins.append(xlow)
#      xlast = xup
#    xbins.append(xlast)
#    return xbins
