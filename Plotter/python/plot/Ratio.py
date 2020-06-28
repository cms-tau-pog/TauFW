# Author: Izaak Neutelings (June 2020)
# -*- coding: utf-8 -*-
import os, re
from TauFW.common.tools.utils import ensurelist, islist
from TauFW.Plotter.plot.utils import *
import ROOT
from ROOT import gDirectory, gPad, gStyle, TCanvas, TPad, TH1, TH1D, THStack, TProfile,\
                 TGraph, TGraphAsymmErrors, TLine, Double, kSolid, kDashed, kDotted
from math import sqrt


def getbinedges(hist):
  """Get lower and upper edges of bins"""
  verbosity = LOG.getverbosity(kwargs)
  bins      = [ ]
  if isinstance(hist,TH1):
    for i in xrange(1,hist.GetXaxis().GetNbins()+1):
      low  = round(hist.GetXaxis().GetBinLowEdge(i),9)
      up   = round(hist.GetXaxis().GetBinUpEdge(i),9)
      bins.append((low,up))
  else:
    for i in xrange(1,hist.GetN()):
      x, y = Double(), Double()
      hist.GetPoint(i,x,y)
      low  = round(x-hist.GetErrorXlow(i),9)
      up   = round(x+hist.GetErrorXhigh(i),9)
      bins.append((low,up))
    bins.sort()
  return bins
  

def havesamebins(hist1,hist2,**kwargs):
  """Compare x axes of two histograms."""
  verbosity = LOG.getverbosity(kwargs)
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
  else: # one is TGraph or TGraphAsymmErrors ?
    bins1 = getbinedges(hist1)
    bins2 = getbinedges(hist2)
    if bins1!=bins2:
      print "bins1 =",bins1
      print "bins2 =",bins2
    return bins1==bins2
  

def dividehist(histnum,histden,**kwargs):
  """Make the ratio of two TH1 histograms."""
  verbosity = LOG.getverbosity(kwargs)+2
  hname     = "ratio_%s-%s"%(histnum.GetName(),histden.GetName())
  hname     = kwargs.get('name',     hname )
  tag       = kwargs.get('tag',      ""    )
  yinf      = kwargs.get('yinf',     1e12  ) # if denominator is 0
  drawzero  = kwargs.get('drawzero', True  ) # ratio=1 if both num and den bins are zero
  if tag:
    hname += tag
  if isinstance(histden,THStack):
    histden = histden.GetStack().Last() # should already have correct bin content and error
  if isinstance(histnum,THStack):
    histnum = histnum.GetStack().Last()
  rhist = histnum.Clone(hname)
  nbins = rhist.GetNcells() # GetNcells = GetNbinsX for TH1
  LOG.verb("dividehist: Making ratio of %s w.r.t. %s"%(histnum,histden),verbosity,2)
  if havesamebins(histden,histnum): # works for TH1 and TH2
    #rhist.Divide(histden)
    LOG.verb("%5s %9s %9s %9s %9s"%("ibin","xval","den","num","ratio"),verbosity,2)
    for ibin in xrange(0,nbins+2):
      den     = histden.GetBinContent(ibin)
      num     = histnum.GetBinContent(ibin)
      enum    = histnum.GetBinError(ibin) #max(histnum.GetBinErrorLow(ibin),histnum.GetBinErrorUp(ibin))
      ratio   = 0.0
      erat    = 0.0
      if den!=0:
        ratio = num/den
        erat  = enum/den
      elif drawzero:
        ratio = 1. if num==0 else yinf if num>0 else -yinf
      LOG.verb("%5d %9.3f %9.3f %9.3f %9.3f"%(ibin,rhist.GetXaxis().GetBinCenter(ibin),den,num,ratio),verbosity,2)
      rhist.SetBinContent(ibin,ratio)
      rhist.SetBinError(ibin,erat)
  else: # works only for TH1
    LOG.warning("dividehist: %r and %r do not have the same bins..."%(histnum,histden))
    LOG.verb("%5s %9s %9s %5s %9s %9s %5s %9s"%("iden","xval","den","inum","xval","num","ratio"),verbosity,2)
    for iden in range(0,nbins+2):
      xval    = histden.GetXaxis().GetBinCenter(iden)
      den     = histden.GetBinContent(iden)
      inum    = histnum.GetXaxis().FindBin(xval)
      num     = histnum.GetBinContent(inum)
      enum    = histnum.GetBinError(inum) #max(histnum.GetBinErrorLow(inum),histnum.GetBinErrorUp(inum))
      ratio   = 0.0
      erat    = 0.0
      if den!=0:
        ratio = num/den
        erat  = enum/den
      elif drawzero:
        ratio = 1.0 if num==0 else yinf if num>0 else -yinf
      LOG.verb("%5d %9.3f %9.3f %5d %9.3f %9.3f %5d %9.3f"%(
               iden,xval,den,inum,histnum.GetXaxis().GetBinCenter(inum),num,ratio),verbosity,2)
      rhist.SetBinContent(iden,ratio)
      rhist.SetBinError(iden,erat)
  return rhist
  

class Ratio(object):
  """Class to make bundle histograms (ratio, stat. error on MC and line) for ratio plot."""
  
  def __init__(self, histden, *histnums, **kwargs):
    """Make a ratio of two histograms bin by bin. Second hist may be a stack, to do data / MC stack."""
    
    self.ratios   = [ ]
    self.error    = None
    self.title    = kwargs.get('title',       "ratio"     )
    self.line     = kwargs.get('line',        True        )
    self.drawzero = kwargs.get('drawzero',    True        ) # draw ratio of two zero bins as 1
    self.garbage  = [ ]
    error         = kwargs.get('error',       None        )
    staterror     = kwargs.get('staterror',   True        ) # recalculate stat. err.
    option        = kwargs.get('option',      ""          )
    denom         = kwargs.get('denom',       -1          )
    histnums      = list(unwrapargs(histnums))
    errorX        = 0 if gStyle.GetErrorX()==0 else 1
    
    # SETUP NUMERATOR/DENOMINATOR
    if len(histnums)==0:
      LOG.warning("Ratio.init: No histogram to compare with!")
    elif denom not in [0, 1]:
      histnums.insert(0,histden)
      if denom>1:
        denom = min(max(0,denom-1),len(histnums)-1)
      elif abs(denom)>len(histnums):
        denom = 0
      histden = histnums[denom]
      histnums.remove(histden)
      #self.line = False
    if isinstance(histden,THStack):
      histden = histden.GetStack().Last() # should have correct bin content and error
    #elif isinstance(histden,TGraph):
    #  LOG.error("Ratio.init: TGraph not implemented")
    #elif isinstance(histden,TProfile):
    #  histtemp = histden.ProjectionX(histden.GetName()+"_px",'E')
    #  copystyle(histtemp,histden)
    #  histden = histtemp
    #  self.garbage.append(histtemp)
    
    # MAKE RATIOS
    for i, histnum in enumerate(histnums):
      tag = str(i)
      if isinstance(histnum,TH1) or isinstance(histnum,THStack):
        ratio = dividehist(histnum,histden,tag=tag,drawzero=self.drawzero)
      #elif isinstance(hist,TGraph):
      #  LOG.warning("Ratio.init: TGraph not tested")
      #elif isinstance(hist,TProfile):
      #  histtemp = hist.ProjectionX(hist.GetName()+"_projx",'E')
      #  copystyle(histtemp,hist)
      #  hist = histtemp
      #  self.garbage.append(histtemp)
      #if isinstance(hist,TH1) and 'h' in option.lower():
      #  ratio = hist.Clone("ratio_%s-%s_%d"%(histden.GetName(),hist.GetName(),i))
      #  ratio.Reset()
      #else:
      #  ratio = TGraphAsymmErrors()
      #  copystyle(ratio,hist)
      #  ratio.SetName("ratio_%s-%s_%d"%(histden.GetName(),hist.GetName(),i))
      #  ratio.SetTitle(self.title)
      self.ratios.append(ratio)
    self.histden = histden
    self.frame   = self.histden.Clone("frame_ratio_%s"%(self.histden.GetName()))
    self.frame.SetLineColor(0)
    self.frame.SetLineWidth(0)
    self.frame.SetMarkerSize(0)
    self.frame.Reset()
    nbins = histden.GetNbinsX()
    
    # MAKE ERROR BAND
    #if isinstance(error,TGraphAsymmErrors):
    #  self.error  = error.Clone()
    #  self.error.SetName("ratio_error")
    #elif staterror:
    #  self.error  = TGraphAsymmErrors() #nbins+2)
    #  self.error.SetName("ratio_stat_error")
    
  
  def Draw(self, *args, **kwargs):
    """Draw all objects."""
    
    ratios      = self.ratios
    option      = args[0] if len(args)>0 else 'PEZ0'
    xmin        = kwargs.get('xmin',    self.frame.GetXaxis().GetXmin() )
    xmax        = kwargs.get('xmax',    self.frame.GetXaxis().GetXmax() )
    ymin        = kwargs.get('ymin',    0.5                             )
    ymax        = kwargs.get('ymax',    1.5                             )
    ytitle      = kwargs.get('ytitle',  "ratio"                         ) #"data / M.C."
    xtitle      = kwargs.get('xtitle',  ""                              )
    data        = kwargs.get('data',    True                            )
    size        = 1.0 if data else 0.0 #0.9
    #self.frame  = gPad.DrawFrame(xmin,ymin,xmax,ymax)
    frame       = self.frame
    
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetXaxis().SetTitle(xtitle)
    #frame.GetYaxis().SetLabelSize(0.10)
    #frame.GetXaxis().SetLabelSize(0.11)
    #frame.GetYaxis().SetTitleSize(0.12)
    #frame.GetXaxis().SetTitleSize(0.10)
    #frame.GetYaxis().CenterTitle(True)
    #frame.GetYaxis().SetTitleOffset(0.5)
    frame.GetXaxis().SetRangeUser(xmin,xmax)
    frame.GetYaxis().SetRangeUser(ymin,ymax)
    #frame.GetYaxis().SetNdivisions(505)
    #frame.SetNdivisions(505)
    frame.Draw('AXIS')
    
    if self.error:
      setErrorBandStyle(self.error,style='hatched')
      self.error.Draw('2 SAME')
    
    if self.line:
      self.line = TLine(xmin,1,xmax,1)
      if data:
        self.line.SetLineColor(12)
        self.line.SetLineWidth(1)
        self.line.SetLineStyle(2)
      else:
        self.line.SetLineColor(self.histden.GetLineColor())
        self.line.SetLineWidth(self.histden.GetLineWidth())
        self.line.SetLineStyle(1)
      self.line.Draw('SAME') # only draw line if a histogram has been drawn!
    
    for i, ratio in enumerate(self.ratios):
      ratio.SetMaximum(ymax*10.e10)
      if (ratio.GetLineWidth()==0 or 'E' in ratio.GetOption()) and ratio.GetMarkerSize()>0:
        if 'E' in ratio.GetOption():
          ratio.Draw(ratio.GetOption()+'SAME')
        else:
          ratio.Draw('E SAME')
      else:
        ratio.Draw(option+'SAME')
    
    return frame
    
  
  def close(self):
    """Delete the histograms."""
    for ratio in self.ratios:
      deletehist(ratio)
    if self.frame:
      deletehist(self.frame)
    if self.error:
      deletehist(self.error)
    if self.line:
      deletehist(self.line)
    for rubbish in self.garbage:
      deletehist(rubbish)
    
  
