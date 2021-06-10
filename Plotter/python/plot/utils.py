# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import os
from math import sqrt, floor
from array import array
from TauFW.common.tools.file import ensuredir, ensureTFile
from TauFW.common.tools.utils import isnumber, islist, ensurelist, unwraplistargs, quotestrs
from TauFW.common.tools.log import Logger
from TauFW.Plotter.plot import moddir
import TauFW.Plotter.plot.CMSStyle as CMSStyle
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gDirectory, gROOT, gStyle, gPad, TH1, TH2, TH1D, TH2D, THStack, TGraph, TGraphErrors, TGraphAsymmErrors, Double,\
                 kSolid, kDashed, kDotted, kBlack, kWhite
#moddir = os.path.dirname(__file__)
gROOT.SetBatch(True)
LOG = Logger('Plot')


def normalize(*hists,**kwargs):
  """Normalize histogram(s)."""
  hists = unwraplistargs(hists)
  scale = kwargs.get('scale',None) or 1.0
  for hist in hists:
    if hist.GetBinErrorOption()==TH1.kPoisson:
      hist.SetBinErrorOption(TH1.kNormal)
      hist.Sumw2()
    integral = hist.Integral()
    if integral:
      hist.Scale(scale/integral)
    else:
      LOG.warning("norm: Could not normalize; integral = 0!")
  

def getframe(pad,hist,xmin=None,xmax=None,**kwargs):
  """Help function to get frame."""
  verbosity = LOG.getverbosity(kwargs)
  garbage = [ ]
  if isinstance(hist,THStack):
    hist = hist.GetStack().Last()
  elif isinstance(hist,TGraph):
    hist = hist.GetHistogram()
    garbage.append(hist)
  xmin_ = hist.GetXaxis().GetXmin() if not xmin and xmin!=0 else xmin
  xmax_ = hist.GetXaxis().GetXmax() if not xmax and xmax!=0 else xmax
  frame = pad.DrawFrame(xmin_,hist.GetMinimum(),xmax_,hist.GetMaximum()) # 1000,xmin,xmax
  if hist not in garbage: #not hist.GetXaxis().IsVariableBinSize() # create identical binning
    xbins = resetbinning(hist.GetXaxis(),xmin,xmax,variable=True,verb=verbosity)
    LOG.verb("getframe: Resetting binning of frame: %r"%(xbins,),verbosity,2)
    frame.SetBins(*xbins) # reset binning
  close(garbage)
  return frame
  

def close(*hists,**kwargs):
  """Close histograms."""
  verbosity = LOG.getverbosity(kwargs)
  hists     = unwraplistargs(hists)
  for hist in hists:
    if isinstance(hist,THStack):
      if verbosity>1: print '>>> close: Deleting histograms from stack "%s"...'%(hist.GetName())
      for subhist in hist.GetStack():
        deletehist(subhist,**kwargs)
      deletehist(hist,**kwargs)
    else:
      deletehist(hist,**kwargs)
  

def gethist(hists,*searchterms,**kwargs):
  """Help function to get all samples corresponding to some name and optional label."""
  from TauFW.Plotter.plot.string import match
  verbosity   = LOG.getverbosity(kwargs)
  unique      = kwargs.get('unique', False )
  warning     = kwargs.get('warn',   True  )
  matches     = [ ]
  for hist in hists:
    if match(searchterms,hist.GetName(),**kwargs):
      matches.append(hist)
  if not matches and warning:
    LOG.warning("gethist: Did not find a historgram with searchterms %s..."%(quotestrs(searchterms)))
  elif unique:
    if len(matches)>1:
      LOG.warning("gethist: Found more than one match to %s. Using first match only: %s"%(
                  quotestrs(searchterms),quotestrs(h.GetName() for h in matches)))
    return matches[0]
  return matches
  

def deletehist(*hists,**kwargs):
  """Completely remove histograms from memory."""
  verbosity = LOG.getverbosity(kwargs)
  hists     = unwraplistargs(hists)
  for hist in hists:
    hclass  = hist.__class__.__name__
    hname   = hist.GetName() if hasattr(hist,'GetName') else None
    LOG.verb("deletehist: deleting %s %r"%(hclass,hname or hist),verbosity,3)
    #try:
    if hist:
      if hasattr(hist,'GetDirectory') and hist.GetDirectory()==None:
        hist.Delete()
      elif hname:
        gDirectory.Delete(hist.GetName())
      else:
        LOG.warning("deletehist: %s %s has no name!"%(hclass,hist))
    else:
      LOG.warning("deletehist: %s is already %s"%(hclass,hist))
    #except AttributeError:
    #  print ">>> AttributeError: "
    #  raise AttributeError
    del hist
  

def printhist(hist,min_=0,max_=None,**kwargs):
  """Help function to print bin errors."""
  nbins  = hist.GetNbinsX()
  minbin = kwargs.get('min',min_)
  maxbin = kwargs.get('max',max_) or nbins+1
  TAB = LOG.table("%6s %9.6g %9.2f %8.2f",**kwargs)
  TAB.printheader("ibin","xval","content","error",post=' '+repr(hist.GetName()))
  for ibin in range(minbin,maxbin+1):
    xval = hist.GetXaxis().GetBinCenter(ibin)
    TAB.printrow(ibin,xval,hist.GetBinContent(ibin),hist.GetBinError(ibin))
  

def grouphists(hists,searchterms,name=None,title=None,color=None,**kwargs):
  """Group histograms in a list corresponding to some searchterm, return their sum.
  E.g. grouphists(hists,['TT','ST'],'Top')
       grouphists(hists,['WW','WZ','ZZ'],'Diboson')"""
  verbosity      = LOG.getverbosity(kwargs)
  searchterms    = ensurelist(searchterms)
  replace        = kwargs.get('replace', False ) # replace grouped histograms with sum in list
  close          = kwargs.get('close',   False ) # close grouped histograms
  kwargs['verb'] = verbosity-1
  matches        = gethist(hists,*searchterms,warn=False,**kwargs) if searchterms else hists
  if not isinstance(color,int):
    import TauFW.Plotter.sample.SampleStyle as STYLE
    color = STYLE.sample_colors.get(name,color)
  histsum   = None
  if matches:
    if name==None:
      name  = matches[0].GetName()
    if title==None:
      title = matches[0].GetTitle() if name==None else name
    histsum = matches[0].Clone(name)
    histsum.SetTitle(title)
    if color:
      histsum.SetFillColor(color)
    for hist in matches[1:]:
      histsum.Add(hist)
    LOG.verb("grouphists: Grouping %s into %r"%(quotestrs(h.GetName() for h in matches),name),verbosity,2)
    if replace:
      hists.insert(hists.index(matches[0]),histsum)
      for hist in matches:
        hists.remove(hist)
        if close:
          deletehist(hist)
  else:
    LOG.warning("grouphists: Did not find a histogram with searchterms %s..."%(quotestrs(searchterms)))
  return histsum
  

def getTGraphYRange(graphs,ymin=+10e10,ymax=-10e10,margin=0.0):
  return getTGraphRange(graphs,min=ymin,max=ymax,margin=margin,axis='y')
  

def getTGraphRange(graphs,min=+10e10,max=-10e10,margin=0.0,axis='y'):
  """Get full y-range of a given TGraph object."""
  vmin, vmax = min, max
  graphs = ensurelist(graphs)
  if axis=='y':
    getUp  = lambda g,i: y+graph.GetErrorYhigh(i)
    getLow = lambda g,i: y-graph.GetErrorYlow(i)
  else:
    getUp  = lambda g,i: x+graph.GetErrorXhigh(i)
    getLow = lambda g,i: x-graph.GetErrorXlow(i)
  for graph in graphs:
    npoints = graph.GetN()
    x, y = Double(), Double()
    for i in xrange(0,npoints):
      graph.GetPoint(i,x,y)
      vup  = getUp(graph,i)
      vlow = getLow(graph,i)
      if vup >vmax: vmax = vup
      if vlow<vmin: vmin = vlow
  if margin>0:
    range = vmax-vmin
    vmax  += range*margin
    vmin  -= range*margin
  return (vmax,vmax)
  

def copystyle(hist1,hist2):
  """Copy the line, fill and marker style from another histogram."""
  hist1.SetFillColor(hist2.GetFillColor())
  hist1.SetFillColor(hist2.GetFillColor())
  hist1.SetFillStyle(hist2.GetFillStyle())
  hist1.SetLineColor(hist2.GetLineColor())
  hist1.SetLineStyle(hist2.GetLineStyle())
  hist1.SetLineWidth(hist2.GetLineWidth())
  hist1.SetMarkerSize(hist2.GetMarkerSize())
  hist1.SetMarkerColor(hist2.GetMarkerColor())
  hist1.SetMarkerStyle(hist2.GetMarkerStyle())
  

def seterrorbandstyle(hist,**kwargs):
  """Set the error band style for a histogram."""
  # https://root.cern.ch/doc/v608/classTAttFill.html#F2
  # 3001 small dots, 3003 large dots, 3004 hatched
  color = kwargs.get('color', None      )
  style = kwargs.get('style', 'hatched' )
  if   style in 'hatched': style = 3004
  elif style in 'dots':    style = 3002
  elif style in 'cross':   style = 3013
  if color==None:          color = kBlack
  hist.SetLineStyle(1) #0
  hist.SetMarkerSize(0)
  hist.SetLineColor(kWhite)
  hist.SetFillColor(color)
  hist.SetFillStyle(style)
  

def getbinedges(hist,**kwargs):
  """Get lower and upper edges of bins"""
  verbosity = LOG.getverbosity(kwargs)
  bins      = [ ]
  if isinstance(hist,TH1):
    for i in xrange(1,hist.GetXaxis().GetNbins()+1):
      low  = round(hist.GetXaxis().GetBinLowEdge(i),9)
      up   = round(hist.GetXaxis().GetBinUpEdge(i),9)
      bins.append((low,up))
  else:
    for i in xrange(0,hist.GetN()):
      x, y = Double(), Double()
      hist.GetPoint(i,x,y)
      low  = round(x-hist.GetErrorXlow(i),9)
      up   = round(x+hist.GetErrorXhigh(i),9)
      bins.append((low,up))
    bins.sort()
  return bins
  

def havesamebins(hist1,hist2,**kwargs):
  """Compare bins of x axes between two TH1 or TGraph objects."""
  verbosity = LOG.getverbosity(kwargs)
  errorX    = kwargs.get('errorX',gStyle.GetErrorX())
  if isinstance(hist1,TH1) and isinstance(hist2,TH1):
    if hist1.GetXaxis().IsVariableBinSize() or hist2.GetXaxis().IsVariableBinSize():
      xbins1 = hist1.GetXaxis().GetXbins()
      xbins2 = hist2.GetXaxis().GetXbins()
      if xbins1.GetSize()!=xbins2.GetSize():
        return False
      for i in xrange(xbins1.GetSize()):
        #print xbins1[i]
        if xbins1[i]!=xbins2[i]:
          return False
      return True
    else:
      return hist1.GetXaxis().GetXmin()==hist2.GetXaxis().GetXmin() and\
             hist1.GetXaxis().GetXmax()==hist2.GetXaxis().GetXmax() and\
             hist1.GetXaxis().GetNbins()==hist2.GetXaxis().GetNbins()
  else: # one is TGraph ?
    bins1 = getbinedges(hist1)
    bins2 = getbinedges(hist2)
    if bins1!=bins2 and errorX<=0: # only look at bin center
      bins1 = [ (a+b)/2 for a,b in bins1]
      bins2 = [ (a+b)/2 for a,b in bins2]
    if bins1!=bins2:
      print "bins1 =",bins1
      print "bins2 =",bins2
    return bins1==bins2
  

def gethistratio(histnum,histden,**kwargs):
  """Make the ratio of two TH1 histograms."""
  verbosity = LOG.getverbosity(kwargs)
  hname     = "ratio_%s-%s"%(histnum.GetName(),histden.GetName())
  hname     = kwargs.get('name',     hname )
  tag       = kwargs.get('tag',      ""    )
  yinf      = kwargs.get('yinf',     1e12  ) # if denominator is 0
  zero      = kwargs.get('zero',     True  ) # ratio=1 if both num and den bins are zero
  errorX    = kwargs.get('errorX', gStyle.GetErrorX() ) # horizontal error bars
  if tag:
    hname += tag
  if isinstance(histden,THStack):
    histden = histden.GetStack().Last() # should already have correct bin content and error
  if isinstance(histnum,THStack):
    histnum = histnum.GetStack().Last()
  rhist = histnum.Clone(hname)
  nbins = rhist.GetNcells() # GetNcells = GetNbinsX for TH1
  LOG.verb("gethistratio: Making ratio of %s w.r.t. %s"%(histnum,histden),verbosity,2)
  if havesamebins(histden,histnum,errorX=errorX): # sanity check binning is the same; works for TH1 and TH2
    #rhist.Divide(histden)
    TAB = LOG.table("%5d %9.3f %9.3f %9.3f %9.3f +- %7.3f",verb=verbosity,level=3)
    TAB.printheader("ibin","xval","yden","ynum","ratio","error")
    for ibin in xrange(0,nbins+2):
      yden    = histden.GetBinContent(ibin)
      ynum    = histnum.GetBinContent(ibin)
      enum    = histnum.GetBinError(ibin) #max(histnum.GetBinErrorLow(ibin),histnum.GetBinErrorUp(ibin))
      ratio   = 0.0
      erat    = 0.0
      if yden!=0:
        ratio = ynum/yden
        erat  = enum/yden
      elif zero:
        ratio = 1. if ynum==0 else yinf if ynum>0 else -yinf
      TAB.printrow(ibin,rhist.GetXaxis().GetBinCenter(ibin),yden,ynum,ratio,erat)
      rhist.SetBinContent(ibin,ratio)
      rhist.SetBinError(ibin,erat)
  else: # works only for TH1
    LOG.warning("gethistratio: %r and %r do not have the same bins..."%(histnum,histden))
    TAB = LOG.table("%5d %9.3f %9.3f %5d %9.3f %9.3f %5d %8.3f +- %7.3f",verb=verbosity,level=3)
    TAB.printheader("iden","xval","yden","inum","xval","ynum","ratio","error")
    for iden in range(0,nbins+2):
      xval    = histden.GetXaxis().GetBinCenter(iden)
      yden    = histden.GetBinContent(iden)
      inum    = histnum.GetXaxis().FindBin(xval)
      ynum    = histnum.GetBinContent(inum)
      enum    = histnum.GetBinError(inum) #max(histnum.GetBinErrorLow(inum),histnum.GetBinErrorUp(inum))
      ratio   = 0.0
      erat    = 0.0
      if yden!=0:
        ratio = ynum/yden
        erat  = enum/yden
      elif zero:
        ratio = 1.0 if ynum==0 else yinf if ynum>0 else -yinf
      TAB.printheader(iden,xval,yden,inum,histnum.GetXaxis().GetBinCenter(inum),ynum,ratio,erat)
      rhist.SetBinContent(iden,ratio)
      rhist.SetBinError(iden,erat)
  return rhist
  


def getgraphratio(graphnum,histden,**kwargs):
  """Make the ratio of a TGraph with a TH1 object on a bin-by-bin basis."""
  verbosity = LOG.getverbosity(kwargs)
  hname     = "ratio_%s-%s"%(graphnum.GetName() or 'graph',histden.GetName())
  hname     = kwargs.get('name',     hname )
  tag       = kwargs.get('tag',      ""    )
  eval      = kwargs.get('eval',     False ) # use interpolation
  yinf      = kwargs.get('yinf',     1e12  ) # if denominator is 0
  zero      = kwargs.get('zero',     True  ) # ratio=1 if both num and den bins are zero
  errorX    = kwargs.get('errorX',   gStyle.GetErrorX()  ) # horizontal error bars
  #color     = kwargs.get('color',    None  )
  nbins     = histden.GetXaxis().GetNbins()
  if tag:
    hname  += tag
  rgraph    = graphnum.__class__()
  rgraph.SetName(hname)
  copystyle(rgraph,graphnum)
  xpoints   = list(graphnum.GetX())
  ypoints   = list(graphnum.GetY())
  ir        = 0 # index ratio graph
  LOG.verb("getgraphratio: Making ratio of %s w.r.t. %s"%(graphnum,histden),verbosity,2)
  TAB = LOG.table("%4s %9s %9s  %4s %9s %9s  %4s %8s %-14s",
                  "%4d %9.5g %9.2f  %4d %9.5g %9.2f  %4d %8.2f +%5.2f  -%5.2f",verb=verbosity,level=3)
  TAB.printheader("ig","xval","yval","ibin","xval","yden","ig","ratio","error")
  if isinstance(histden,TH1):
    for ibin in range(0,nbins+2):
      xval = histden.GetXaxis().GetBinCenter(ibin)
      xerr = histden.GetXaxis().GetBinWidth(ibin)/2 if errorX else 0
      yden = histden.GetBinContent(ibin)
      ig   = -1
      if eval:
        ynum = graphnum.Eval(xval)
      elif xval in xpoints: # assume points coincide with histogram bin centers
        ig   = xpoints.index(xval)
        ynum = ypoints[ig]
      else:
        continue
      yerrupp = graphnum.GetErrorYhigh(ig) # -1 if graphnum is not TGraph(Asymm)Errors
      yerrlow = graphnum.GetErrorYlow(ig)  # -1 if graphnum is not TGraph(Asymm)Errors
      ratio   = 0.0
      rerrupp = 0.0
      rerrlow = 0.0
      if yden!=0:
        ratio   = ynum/yden
        rerrupp = yerrupp/yden
        rerrlow = yerrlow/yden
      elif zero:
        ratio = 1.0 if ynum==0 else yinf if ynum>0 else -yinf
      rgraph.SetPoint(ir,xval,ratio)
      if isinstance(rgraph,TGraphErrors):
        rgraph.SetPointError(ir,xerr,max(rerrupp,rerrlow))
      elif isinstance(rgraph,TGraphAsymmErrors):
        rgraph.SetPointError(ir,xerr,xerr,rerrlow,rerrupp)
      TAB.printrow(ig,xval,ynum,ibin,xval,yden,ir,ratio,rerrupp,rerrlow)
      ir += 1
  else:
    LOG.throw(IOError,"getgraphratio: Ratio between %s and %s not implemented..."%(graphnum,histden))
  return rgraph
  

def geterrorband(*hists,**kwargs):
  """Make an error band histogram for a list of histograms, or stack.
  Returns an TGraphAsymmErrors object."""
  verbosity = LOG.getverbosity(kwargs)
  hists     = unwraplistargs(hists)
  hists     = [h.GetStack().Last() if isinstance(h,THStack) else h for h in hists]
  sysvars   = kwargs.get('sysvars',     [ ]    ) # list of tuples with up/cent/down variation histograms
  name      = kwargs.get('name',        None   ) or "error_"+hists[0].GetName()
  title     = kwargs.get('title',       None   ) or ("Sys. + stat. unc." if sysvars else "Stat. unc.")
  color     = kwargs.get('color',       kBlack )
  hist0     = hists[0]
  nbins     = hist0.GetNbinsX()
  if sysvars and isinstance(sysvars,dict):
    sysvars = [v for k, v in sysvars.iteritems()]
  error = TGraphAsymmErrors()
  error.SetName(name)
  error.SetTitle(title)
  LOG.verb("geterrorband: Making error band for %s"%(hists),verbosity,2)
  TAB = LOG.table("%5s %7s %6s %10s %11s   %-20s   %-20s   %-20s",
                  "%5d %7.6g %6.6g %10.2f %11.2f   +%8.2f  -%8.2f   +%8.2f  -%8.2f   +%8.2f  -%8.2f",verb=verbosity,level=3)
  TAB.printheader("ibin","xval","xerr","nevts","sqrt(nevts)","statistical unc.","systematical unc.","total unc.")
  ip = 0
  for ibin in range(1,nbins+1):
    xval = hist0.GetXaxis().GetBinCenter(ibin)
    xerr = 0 if ibin in [0,nbins+1] else hist0.GetXaxis().GetBinWidth(ibin)/2
    yval = 0
    statlow2, statupp2 = 0, 0
    syslow2,  sysupp2  = 0, 0
    for hist in hists: # STATISTICS
      yval     += hist.GetBinContent(ibin)
      statlow2 += hist.GetBinErrorLow(ibin)**2
      statupp2 += hist.GetBinErrorUp(ibin)**2
    for histup, hist, histdown in sysvars: # SYSTEMATIC VARIATIONS
      syslow2  += (hist.GetBinContent(ibin)-histdown.GetBinContent(ibin))**2
      sysupp2  += (hist.GetBinContent(ibin)-histup.GetBinContent(ibin))**2
    ylow2, yupp2 = statlow2+syslow2, statupp2+sysupp2,
    error.SetPoint(ip,xval,yval)
    error.SetPointError(ip,xerr,xerr,sqrt(ylow2),sqrt(yupp2))
    TAB.printrow(ibin,xval,xerr,yval,sqrt(abs(yval)),sqrt(statupp2),sqrt(statlow2),sqrt(sysupp2),sqrt(syslow2),sqrt(yupp2),sqrt(ylow2))
    ip += 1
  seterrorbandstyle(error,color=color)
  #error.SetLineColor(hist0.GetLineColor())
  error.SetLineWidth(hist0.GetLineWidth()) # use draw option 'E2 SAME'
  return error
  

def dividebybinsize(hist,**kwargs):
  """Divide each bin by its bin width. If a histogram has assymmetric errors (e.g. data with Poisson),
  return a TGraphAsymmErrors instead."""
  verbosity = LOG.getverbosity(kwargs)
  LOG.verbose('dividebybinsize: "%s"'%(hist.GetName()),verbosity,2)
  zero     = kwargs.get('zero',     True ) # include bins that are zero in TGraph
  zeroerrs = kwargs.get('zeroerrs', True ) # include errors for zero bins
  errorX   = kwargs.get('errorX', gStyle.GetErrorX() ) # horizontal error bars
  nbins    = hist.GetXaxis().GetNbins()
  TAB = LOG.table("%5s %8.6g %8.6g %10.3f %9.4f %8.4f %8.4f %10.4f",verb=verbosity,level=3)
  TAB.printheader("ibin","xval","width","yval","yerr","yupp","ylow","yerr/width")
  if hist.GetBinErrorOption()==TH1.kPoisson: # make asymmetric Poisson errors (like for data)
    graph  = TGraphAsymmErrors()
    graph.SetName(hist.GetName()+"_graph")
    graph.SetTitle(hist.GetTitle())
    copystyle(graph,hist)
    ip = 0 # skip zero bins if not zero
    for ibin in xrange(1,nbins+1):
      xval  = hist.GetXaxis().GetBinCenter(ibin)
      width = hist.GetXaxis().GetBinWidth(ibin)
      xerr  = width/2 if errorX else 0
      yval  = hist.GetBinContent(ibin)
      yerr  = hist.GetBinError(ibin)
      yupp  = hist.GetBinErrorUp(ibin)
      ylow  = hist.GetBinErrorLow(ibin)
      TAB.printrow(ibin,xval,width,yval,yerr,yupp,ylow,yval/width)
      hist.SetBinContent(ibin,yval/width)
      hist.SetBinError(ibin,yerr/width)
      if yval!=0 or zero:
        graph.SetPoint(ip,xval,yval/width)
        if yval!=0 or zeroerrs:
          graph.SetPointError(ip,xerr,xerr,ylow/width,yupp/width)
        else:
          graph.SetPointError(ip,xerr,xerr,0,0)
        ip += 1
    return graph
  else:
    for ibin in xrange(0,nbins+2):
      xval  = hist.GetXaxis().GetBinCenter(ibin)
      width = hist.GetXaxis().GetBinWidth(ibin)
      yval  = hist.GetBinContent(ibin)
      yerr  = hist.GetBinError(ibin)
      hist.SetBinContent(ibin,yval/width)
      hist.SetBinError(ibin,yerr/width)
      TAB.printrow(ibin,xval,width,yval,yerr,hist.GetBinErrorUp(ibin),hist.GetBinErrorLow(ibin),yval/width)
  return hist
  

def addoverflow(*hists,**kwargs):
  """Add overflow to last bin(s)."""
  verbosity = LOG.getverbosity(kwargs)
  hists     = unwraplistargs(hists)
  merge     = kwargs.get('merge',False) # merge last and overflow bin(s), otherwise reset to 0
  LOG.verbose("addoverflow: %r (merge=%r)"%("', '".join(h.GetName() for h in hists),merge),verbosity,2)
  for hist in hists:
    LOG.verbose("addoverflow: %r"%(hist.GetName()),verbosity,3)
    if isinstance(hist,TH2):
      nxbins = hist.GetXaxis().GetNbins()
      nybins = hist.GetYaxis().GetNbins()
      bins = [(ix,nybins) for ix in range(1,nxbins)] +\
             [(nxbins,iy) for iy in range(1,nybins)] + [(nxbins,nybins)]
      for xbin, ybin in bins:
        yval   = hist.GetBinContent(xbin,ybin)    # last bin
        yerr2  = hist.GetBinError(xbin,ybin)**2   # last bin
        ofbins = [ ] # 1 or 3 overflow bins
        if xbin==nxbins:
          ofbins.append((xbin+1,ybin)) # add overflow in x
        if ybin==nybins:
          ofbins.append((xbin,ybin+1)) # add overflow in y
        if xbin==nxbins and ybin==nybins:
          ofbins.append((xbin+1,ybin+1))
        for xof, yof in ofbins:
          yval  += hist.GetBinContent(xof,yof) # overflow
          yerr2 += hist.GetBinError(xof,yof)**2 # overflow
        yerr = sqrt(yerr2)
        LOG.verbose("addoverflow: bin (%d,%d): %7.2f +- %6.2f -> %7.2f +- %6.2f"%(
          xbin,ybin,hist.GetBinContent(xbin,ybin),hist.GetBinError(xbin,ybin),yval,yerr),verbosity,3)
        hist.SetBinContent(xbin,ybin,yval)
        hist.SetBinError(xbin,ybin,yerr) # add in quadrature
        if merge: # merge last and overflow bin(s)
          for xof, yof in ofbins:
            hist.SetBinContent(xof,yof,yval)
            hist.SetBinError(xof,yof,sqrt(yerr2))
        else: # reset to 0
          for xof, yof in ofbins:
            hist.SetBinContent(xof,yof,0)
            hist.SetBinError(xof,yof,0)
    else:
      nbins  = hist.GetXaxis().GetNbins()
      yval   = hist.GetBinContent(nbins)    # last bin
      yerr2  = hist.GetBinError(nbins)**2   # last bin
      yval  += hist.GetBinContent(nbins+1)  # overflow
      yerr2 += hist.GetBinError(nbins+1)**2 # overflow
      yerr   = sqrt(yerr2)
      LOG.verbose("addoverflow: bin %d: %7.2f +- %6.2f -> %7.2f +- %6.2f"%(
        nbins,hist.GetBinContent(nbins),hist.GetBinError(nbins),yval,yerr),verbosity,3)
      hist.SetBinContent(nbins,yval)
      hist.SetBinError(nbins,yerr) # add in quadrature
      if merge: # merge last and overflow bin(s)
        hist.SetBinContent(nbins+1,yval)
        hist.SetBinError(nbins+1,sqrt(yerr2))
      else: # reset to 0
        hist.SetBinContent(nbins+1,0) # reset
        hist.SetBinError(nbins+1,0)
  return hists
  

def capoff(hist,ymin=None,ymax=None,verb=0):
  """Ensure bin content is within maximum & minimum value. Keep error."""
  ntot, nmin, nmax = 0, 0, 0
  for i in range(0,hist.GetNcells()+2):
    ntot += 1
    yval = hist.GetBinContent(i)
    if ymax and yval>ymax:
      yval = ymax # cap off
      nmax += 1
    elif ymin and yval<ymin:
      yval = ymin # cap off
      nmin += 1
    else:
      continue
    yerr = hist.GetBinError(i) # keep error
    hist.SetBinContent(i,yval)
    hist.SetBinError(i,yerr)
  if verb>=2:
    print ">>> capoff: Found %d/%d values < %s, and %d/%d values > %s for histogram %s"%(nmin,ntot,ymin,nmax,ntot,ymax,hist)
  return nmin+nmax # number of reset bins
  

def resetedges(oldedges,xmin=None,xmax=None,**kwargs):
  """Reset the range a list of bin edges."""
  newedges = list(oldedges)[:]
  if xmin!=None:
    LOG.insist(xmin<newedges[-1],"resetedges: xmin=%s >= last bin %s"%(xmin,newedges[-1]))
    for i, xlow in enumerate(newedges):
      if xmin<=xlow:
        #if i==0: i += 1 # reset lowest edge
        if xmin==xlow: i += 1
        newedges = [xmin]+newedges[i:]
        break
  if xmax!=None:
    LOG.insist(xmax>newedges[0],"resetedges: xmax=%s <= last bin %s"%(xmax,newedges[0]))
    for i, xup in enumerate(reversed(newedges)):
      if xmax>=xup:
        #if i==0: i += 1 # reset last edge
        if xmax==xup: i += 1
        newedges = newedges[:len(newedges)-i]+[xmax]
        break
  return newedges
  

def resetbinning(axis,xmin=None,xmax=None,variable=False,**kwargs):
  """Reset the range a list of bin edges for a given TAxis."""
  verbosity = LOG.getverbosity(kwargs)
  if axis.IsVariableBinSize():
    oldbins = (axis.GetNbins(),list(axis.GetXbins()))
    edges = resetedges(axis.GetXbins(),xmin,xmax)
    xbins = (len(edges)-1,array('d',edges))
  else: # constant width
    nbins = axis.GetNbins()
    xmin_, xmax_ = axis.GetXmin(), axis.GetXmax()
    oldbins = (nbins,xmin_,xmax_)
    width = (xmax_-xmin_)/nbins # original width
    xmin = xmin_ if xmin==None else xmin
    xmax = xmax_ if xmax==None else xmax
    if not variable and (xmax_-xmin)%width==0 and (xmax-xmin_)%width==0: # bin edges align
      nbins = (xmax-xmin)/width # new number of bins
      xbins = (nbins,xmin,xmax)
    else: # bin edges do not align; create a variable binning
      edges = [xmin_+width*i for i in range(0,nbins+1)] # original bin edges
      edges = resetedges(edges,xmin,xmax) # reset range
      xbins = (len(edges)-1,array('d',edges))
  LOG.verb("resetbinning: axis=%r, xbins=%r -> %r"%(axis,oldbins,xbins),verbosity,1)
  return xbins
  

def resetrange(oldhist,xmin=None,xmax=None,ymin=None,ymax=None,**kwargs):
  """Reset the range of a TH1 histogram and return new histogram. Useful to to draw a logarithmic
  plot, if lowest edge is 0, and xmin does not align with a bin edge."""
  verbosity = LOG.getverbosity(kwargs)
  LOG.verbose("setrange: xmin=%s, xmax=%s, %r"%(xmin,xmax,oldhist),verbosity,2)
  hname = "%s_resetrange"%(oldhist.GetName())
  def getbincenter(axis,ibin,amin=None,amax=None):
    """Help function to get bin center."""
    alow = axis.GetBinLowEdge(ibin)
    aup  = axis.GetBinUpEdge(ibin)
    if amin!=None and alow<amin<aup:
      aval = (amin+aup)/2. # make sure to find the right bin
    elif amax!=None and alow<amax<aup:
      aval = (amax+alow)/2. # make sure to find the right bin
    else:
      aval = axis.GetBinCenter(ibin)
    return aval
  if isinstance(oldhist,TH2):
    xbins = resetbinning(oldhist.GetXaxis(),xmin,xmax,verb=verbosity)
    ybins = resetbinning(oldhist.GetYaxis(),ymin,ymax,verb=verbosity)
    bins = xbins+ybins
    newhist = TH2D(hname,hname,*bins)
    if verbosity>=1:
      print ">>> resetrange: (nxbins,xmin,xmax) = (%s,%s,%s) -> (%s,%s,%s)"%(
        oldhist.GetXaxis().GetNbins(),oldhist.GetXaxis().GetXmin(),oldhist.GetXaxis().GetXmax(),
        newhist.GetXaxis().GetNbins(),newhist.GetXaxis().GetXmin(),newhist.GetXaxis().GetXmax())
      print ">>> resetrange: (nybins,ymin,ymax) = (%s,%s,%s) -> (%s,%s,%s)"%(
        oldhist.GetYaxis().GetNbins(),oldhist.GetYaxis().GetXmin(),oldhist.GetYaxis().GetXmax(),
        newhist.GetYaxis().GetNbins(),newhist.GetYaxis().GetXmin(),newhist.GetYaxis().GetXmax())
    for iyold in range(0,oldhist.GetYaxis().GetNbins()+2):
      for ixold in range(0,oldhist.GetXaxis().GetNbins()+2):
        xval  = getbincenter(oldhist.GetXaxis(),ixold,xmin,xmax)
        yval  = getbincenter(oldhist.GetYaxis(),iyold,ymin,ymax)
        ixnew = newhist.GetXaxis().FindBin(xval)
        iynew = newhist.GetYaxis().FindBin(yval)
        zval  = oldhist.GetBinContent(ixold,iyold)
        zerr  = oldhist.GetBinError(ixold,iyold)
        newhist.SetBinContent(ixnew,iynew,zval)
        newhist.SetBinError(ixnew,iynew,zerr)
        LOG.verb("resetrange: (x,y)=(%7.2f,%7.2f), (ix,iy)=(%2s,%2s) -> (%2s,%2s): %8.2f +- %7.2f"%(
          xval,yval,ixold,iyold,ixnew,iynew,zval,zerr),verbosity,2)
  else:
    xbins = resetbinning(oldhist.GetYaxis(),xmin,xmax,verb=verbosity)
    newhist = TH1D(hname,hname,*xbins)
    LOG.verb("resetrange: (nxbins,xmin,xmax) = (%s,%s,%s) -> (%s,%s,%s)"%(
      oldhist.GetXaxis().GetNbins(),oldhist.GetXaxis().GetXmin(),oldhist.GetXaxis().GetXmax(),
      newhist.GetXaxis().GetNbins(),newhist.GetXaxis().GetXmin(),newhist.GetXaxis().GetXmax()),verbosity,1)
    for ixold in range(0,oldhist.GetXaxis().GetNbins()+2):
      xval  = getbincenter(oldhist.GetXaxis(),ixold,xmin,xmax)
      ixnew = newhist.GetXaxis().FindBin(xval)
      zval  = oldhist.GetBinContent(ixold)
      zerr  = oldhist.GetBinError(ixold)
      newhist.SetBinContent(ixnew,zval)
      newhist.SetBinError(ixnew,zerr)
      LOG.verb("resetrange: x=%7.2f, ix=%2s -> %2s: %8.2f +- %7.2f"%(
        xval,ixold,ixnew,zval,zerr),verbosity,2)
  return newhist
  
