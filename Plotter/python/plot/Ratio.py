# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/view/CMS/PoissonErrorBars
#   https://twiki.cern.ch/twiki/bin/view/CMS/StatComWideBins
#   https://twiki.cern.ch/twiki/bin/view/CMS/DataMCComparison
import os, re
from TauFW.Plotter.plot.utils import *
import ROOT
from ROOT import gStyle, gPad, TH1, THStack, TProfile, TGraph, TGraphAsymmErrors, TLine


class Ratio(object):
  """Class to make bundle histograms (ratio, stat. error on MC and line) for ratio plot."""
  
  def __init__(self, histden, *histnums, **kwargs):
    """Make a ratio of two histograms bin by bin. Second hist may be a stack, to do data / MC stack."""
    verbosity      = LOG.getverbosity(kwargs)
    self.ratios    = [ ]
    self.errband   = None
    self.title     = kwargs.get('title',       "ratio"     )
    self.line      = kwargs.get('line',        True        )
    self.drawzero  = kwargs.get('drawzero',    True        ) # draw ratio of two zero bins as 1
    self.garbage   = [ ]
    errband        = kwargs.get('errband',     None        ) # error band (e.g. stat. and/or sys. unc.)
    option         = kwargs.get('option',      ""          )
    denom          = kwargs.get('denom',       None        ) # histogram as denominator (count from 1)
    errorX         = kwargs.get('errorX', gStyle.GetErrorX() ) # horizontal error bars
    histnums       = unwraplistargs(histnums)
    
    # SETUP NUMERATOR/DENOMINATOR
    if len(histnums)==0:
      LOG.warning("Ratio.init: No histogram to compare with!")
    elif denom not in [0,1,None]: # change denominator histogram
      histnums.insert(0,histden)
      if denom>1:
        denom = min(max(0,denom-1),len(histnums)-1)
      elif abs(denom)>len(histnums):
        denom = 0
      histden = histnums[denom]
      histnums.remove(histden)
    if isinstance(histden,THStack):
      histden = histden.GetStack().Last() # should have correct bin content and error
    #elif isinstance(histden,TGraph):
    #  LOG.error("Ratio.init: TGraph not implemented")
    #elif isinstance(histden,TProfile):
    #  histtemp = histden.ProjectionX(histden.GetName()+"_px",'E')
    #  copystyle(histtemp,histden)
    #  histden = histtemp
    #  self.garbage.append(histtemp)
    LOG.verb("Ratio.init: denom=%s, histden=%s, histnums=%s, errband=%s"%(denom,histden,histnums,errband),verbosity,2)
    
    # MAKE RATIOS
    for i, histnum in enumerate(histnums):
      tag = str(i)
      if isinstance(histnum,TH1) or isinstance(histnum,THStack):
        ratio = gethistratio(histnum,histden,tag=tag,drawzero=self.drawzero,errorX=errorX)
      elif isinstance(histnum,TGraph):
        LOG.warning("Ratio.init: TGraph ratio not validated! Please check verbose output...")
        ratio = getgraphratio(histnum,histden,tag=tag,drawzero=self.drawzero,errorX=errorX)
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
      copystyle(ratio,histnum)
      ratio.SetFillStyle(0)
      self.ratios.append(ratio)
    
    # MAKE ERROR BAND RATIO
    if isinstance(errband,TGraphAsymmErrors):
      self.errband = getgraphratio(errband,histden,errorX=True)
      copystyle(self.errband,errband)
      #seterrorbandstyle(self.errband,style='hatched',color=errband.GetFillColor())
    
    self.histden = histden
    self.frame   = self.histden.Clone("frame_ratio_%s"%(self.histden.GetName()))
    self.frame.Reset() # make empty
    self.frame.SetLineColor(0)
    self.frame.SetLineWidth(0)
    self.frame.SetMarkerSize(0)
    
  
  def draw(self, option=None, **kwargs):
    """Draw all objects."""
    verbosity   = LOG.getverbosity(kwargs,self)
    ratios      = self.ratios
    xmin        = kwargs.get('xmin',    self.frame.GetXaxis().GetXmin() )
    xmax        = kwargs.get('xmax',    self.frame.GetXaxis().GetXmax() )
    ymin        = kwargs.get('ymin',    0.5     )
    ymax        = kwargs.get('ymax',    1.5     )
    data        = kwargs.get('data',    False   )
    ytitle      = kwargs.get('ytitle',  "Obs. / Exp." if data else "Ratio" )
    xtitle      = kwargs.get('xtitle',  ""      )
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
    frame.GetYaxis().SetNdivisions(506)
    #frame.SetNdivisions(505)
    frame.Draw('HIST') # 'AXIS' breaks grid
    
    if self.errband:
      self.errband.Draw('2 SAME')
    
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
    
    for ratio in self.ratios:
      ratio.SetMaximum(ymax*1e10)
      if option:
        roption = option
      elif (ratio.GetLineWidth()==0 or 'E' in ratio.GetOption()) and ratio.GetMarkerSize()>0:
        roption = ratio.GetOption() if 'E' in ratio.GetOption() else 'E'
      else:
        roption = 'HIST' if isinstance(ratio,TH1) else 'PE0'
      roption += 'SAME'
      ratio.Draw(roption)
      LOG.verb("Ratio.draw: ratio=%s, roption=%r"%(ratio,roption),verbosity,2)
    
    return frame
    
  
  def close(self):
    """Delete the histograms."""
    for ratio in self.ratios:
      deletehist(ratio)
    if self.frame:
      deletehist(self.frame)
    if self.errband:
      deletehist(self.errband)
    if self.line:
      deletehist(self.line)
    for rubbish in self.garbage:
      deletehist(rubbish)
    
  
