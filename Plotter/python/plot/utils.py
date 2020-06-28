# Author: Izaak Neutelings (June 2020)
# -*- coding: utf-8 -*-
from TauFW.common.tools.utils import islist, ensurelist, unwrapargs
from TauFW.common.tools.log import Logger
import TauFW.Plotter.plot.CMSStyle as CMSStyle
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gDirectory, gROOT, TH1, TGraphAsymmErrors, kBlack, kWhite
gROOT.SetBatch(True)
LOG = Logger('Plot')



def frange(start,end,step):
  """Return a list of numbers between start and end, for a given stepsize."""
  flist = [start]
  next = start+step
  while next<end:
    flist.append(next)
    next += step
  return flist
  

def columnize(oldlist,ncol=2):
  """Transpose lists into n columns, useful for TLegend,
  e.g. [1,2,3,4,5,6,7] -> [1,5,2,6,3,7,4] for ncol=2."""
  if ncol<2:
    return oldlist
  parts   = partition(oldlist,ncol)
  collist = [ ]
  row     = 0
  assert len(parts)>0, "len(parts)==0"
  while len(collist)<len(oldlist):
    for part in parts:
      if row<len(part): collist.append(part[row])
    row += 1
  return collist
  

def partition(list,nparts):
  """Partion list into n chunks, as evenly sized as possible."""
  nleft    = len(list)
  divider  = float(nparts)
  parts    = [ ]
  findex   = 0
  for i in range(0,nparts): # partition recursively
    nnew   = int(ceil(nleft/divider))
    lindex = findex + nnew
    parts.append(list[findex:lindex])
    nleft   -= nnew
    divider -= 1
    findex   = lindex
    #print nnew
  return parts
  

def normalize(*hists,**kwargs):
  """Normalize histogram."""
  hists = unwrapargs(hists)
  for hist in hists:    
    if hist.GetBinErrorOption()==TH1.kPoisson:
      hist.SetBinErrorOption(TH1.kNormal)
      hist.Sumw2()
    integral = hist.Integral()
    if integral:
      hist.Scale(1./integral)
    else:
      LOG.warning("norm: Could not normalize; integral = 0!")
  

def close(*hists,**kwargs):
  """Close histograms."""
  verbosity = LOG.getverbosity(kwargs)
  hists     = unwrapargs(hists)
  for hist in hists:
    if isinstance(hist,THStack):
      if verbosity>1: print '>>> close: Deleting histograms from stack "%s"...'%(hist.GetName())
      for subhist in hist.GetStack():
        deletehist(subhist,**kwargs)
      deletehist(hist,**kwargs)
    else:
      deletehist(hist,**kwargs)
  

def deletehist(*hists,**kwargs):
  """Completely remove histograms from memory."""
  verbosity = LOG.getverbosity(kwargs)
  hists     = unwrapargs(hists)
  for hist in hists:
    if verbosity>1: print '>>> deletehist: deleting histogram "%s"'%(hist.GetName())
    #try:
    if hist:
      if hasattr(hist,'GetDirectory') and hist.GetDirectory()==None:
        hist.Delete()
      elif hist.GetName():
        gDirectory.Delete(hist.GetName())
      else:
        LOG.warning("deletehist: object %s has no name!"%(hist))
    else:
      LOG.warning("deletehist: histogram is already %s"%(hist))
    #except AttributeError:
    #  print ">>> AttributeError: "
    #  raise AttributeError
    del hist
  

def divideBinsByBinSize(hist,**kwargs):
  """Divide each bin by its bin width."""
  verbosity = LOG.getVerbosity(kwargs)
  LOG.verbose('divideByBinSize: "%s"'%(hist.GetName()),verbosity,2)
  if hist.GetBinErrorOption()==TH1.kPoisson:
    zero       = kwargs.get('zero',       True)
    zeroErrors = kwargs.get('zeroErrors', True)
    graph = TGraphAsymmErrors()
    graph.SetName(hist.GetName()+"_graph")
    graph.SetTitle(hist.GetTitle())
    copyStyle(graph,hist)
    ip = 0 # skip zero bins
    if verbosity>=2:
      print ">>> %10s %10s %10s %10s %10s"%("binc","bine","bine/binc","bineh","binel")
    for i in xrange(0,hist.GetXaxis().GetNbins()+1):
      binc  = hist.GetBinContent(i)
      bine  = hist.GetBinError(i)
      bineh = hist.GetBinErrorUp(i)
      binel = hist.GetBinErrorLow(i)
      if verbosity>=2:
        if binc!=0:
          print ">>> %10.4f %10.4f %10.4f %10.4f %10.4f"%(binc,bine,bine/binc,bineh,binel)
        else:
          print ">>> %10.4f %10.4f %10s %10.4f %10.4f"%(binc,bine,None,bineh,binel)
      width = hist.GetXaxis().GetBinWidth(i)
      xval  = hist.GetXaxis().GetBinCenter(i)
      hist.SetBinContent(i,binc/width)
      hist.SetBinError(i,bine/width)
      if binc!=0 or zero:
        graph.SetPoint(ip,xval,binc/width)
        if binc!=0 or zeroErrors:
          graph.SetPointError(ip,width/2,width/2,binel/width,bineh/width)
        else:
          graph.SetPointError(ip,width/2,width/2,0,0)
        ip += 1
    return graph
  else:
    for i in xrange(0,hist.GetXaxis().GetNbins()+2):
      binc  = hist.GetBinContent(i)
      bine  = hist.GetBinError(i)
      if verbosity>=2:
        if binc!=0:
          print ">>> %10.4f %10.4f %10.4f %10.4f %10.4f"%(binc,bine,bine/binc,hist.GetBinErrorUp(i),hist.GetBinErrorLow(i))
        else:
          print ">>> %10.4f %10.4f %10s %10.4f %10.4f"%(binc,bine,None,hist.GetBinErrorUp(i),hist.GetBinErrorLow(i))
      width = hist.GetBinWidth(i)
      hist.SetBinContent(i,binc/width)
      hist.SetBinError(i,bine/width)
  return hist
  

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
  color = kwargs.get('color', kBlack    )
  style = kwargs.get('style', 'hatched' )
  if   style in 'hatched': style = 3004
  elif style in 'dots':    style = 3002
  elif style in 'cross':   style = 3013
  hist.SetLineStyle(1) #0
  hist.SetMarkerSize(0)
  hist.SetLineColor(kWhite)
  hist.SetFillColor(color)
  hist.SetFillStyle(style)
  
