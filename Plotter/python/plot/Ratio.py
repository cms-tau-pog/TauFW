# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/view/CMS/PoissonErrorBars
#   https://twiki.cern.ch/twiki/bin/view/CMS/StatComWideBins
#   https://twiki.cern.ch/twiki/bin/view/CMS/DataMCComparison
import os, re
from TauFW.common.tools.root import rootrepr
from TauFW.Plotter.plot.utils import *
from TauFW.Plotter.plot.string import makehistname
import ROOT
from ROOT import TH1, TProfile, TLine


class Ratio(object):
  """Class to make bundle histograms (ratio, stat. error on MC and line) for ratio plot."""
  
  def __init__(self, *hists, **kwargs):
    """Make a ratio of two histograms bin by bin. Second hist may be a stack, to do data / MC stack.
    Initiate as:
      Ratio(hnum,hden)               # hnum / hden and 1 = hden / hden
      Ratio( h1,h2,...,hN)           # hists[i]   / hists[-1],  where hists=[h1,h2,...]
      Ratio([h1,h2,...,hN])          # hists[i]   / hists[-1],  where hists=[h1,h2,...]
      Ratio( h1,h2,...,hN ,denom=X)  # hists[i]   / hists[X-1], where hists=[h1,h2,...]
      Ratio([h1,h2,...,hN],denom=X)  # hists[i]   / hists[X-1], where hists=[h1,h2,...]
      Ratio( h1,h2,...,hN ,num=X)    # hists[X-1] / hists[X-1], where hists=[h1,h2,...]
      Ratio([h1,h2,...,hN],num=X)    # hists[X-1] / hists[X-1], where hists=[h1,h2,...]
      Ratio([hnum1,...], hden)       # hnums[i] / hden
      Ratio([hnum1,...],[hden1,...]) # hnums[i] / hdens[i]
      Ratio( hnum,      [hden1,...]) # hnum     / hdens[i]
    """
    verbosity     = LOG.getverbosity(kwargs)
    self.ratios   = [ ]
    self.errband  = None
    self.drawden  = kwargs.get('drawden',     False       ) # draw denominator (with error bars)
    self.title    = kwargs.get('title',       "ratio"     )
    self.line     = kwargs.get('line',   not self.drawden ) # draw line at 1.0
    self.drawzero = kwargs.get('drawzero',    True        ) # draw ratio of two zero bins as 1
    errband       = kwargs.get('errband',     None        ) # draw error band (e.g. stat. and/or sys. unc.)
    errbars       = kwargs.get('errbars',     False       ) # draw error bars
    option        = kwargs.get('option',      ""          )
    num           = kwargs.get('num',         None        ) # index of common numerator histogram (count from 1)
    denom         = kwargs.get('den',         None        ) # index of common denominator histogram (count from 1)
    denom         = kwargs.get('denom',       None        ) # alias
    errorX        = kwargs.get('errorX', gStyle.GetErrorX() ) # horizontal error bars
    fraction      = kwargs.get('fraction',    None        ) # make stacked fraction from stack (normalize each bin to 1)
    hists         = unpacklistargs(hists) # ensure list of histograms
    LOG.verb("Ratio.init: hists=%s, denom=%s, num=%s, drawden=%r, errband=%r"%(
      rootrepr(hists),rootrepr(denom),rootrepr(num),self.drawden,errband),verbosity,1)
    
    # CONVERT SPECIAL OBJECTS
    for i, hist in enumerate(hists[:]):
      if isinstance(hist,THStack): # convert TStack to TH1D
        if isinstance(fraction,bool) and fraction: # only once
          fraction = normalizebins(hist) # create stack with normalized bins
        hists[i] = hist.GetStack().Last() # should have correct bin content and error
      ###elif isinstance(hist,TGraph):
      ###  LOG.error("Ratio.init: TGraph not implemented")
      elif isinstance(hist,TProfile):
        histtemp = hist.ProjectionX(hist.GetName()+"_projx",'E')
        copystyle(histtemp,hist)
        hists[i] = histtemp
        self.garbage.append(histtemp) # delete at end
    
    # SET NUMERATOR & DENOMINATOR INDEX
    denom_is_hist = isinstance(denom,(TH1,THStack,list,tuple))
    num_is_hist = isinstance(num,(TH1,THStack,list,tuple))
    if denom_is_hist and num_is_hist:
      hists = [num,denom]
      denom = len(hists)-1
      num = None
    elif denom_is_hist:
      hists = [hists,denom]
      denom = len(hists)-1
    elif num_is_hist:
      hists = [num,hists]
      num = None
    elif num!=None: # single numerator, use other histograms as denominator
      LOG.insist(isinstance(num,int),"Numerator index must be integer! Got num=%r..."%(num))
      if num<0: # convert to positive number
        num = max(0,len(hists)+num)
      else: # shift by 1 to get index in list
        num = max(0,num-1)
        if num>=len(hists):
          LOG.warn("Ratio.init: Warning index num = %d >= %d = len(hists)! Setting to last index..."%(num,len(hists)))
          num = len(hists)-1
    elif denom==None or isinstance(denom,bool): # use last histogram by default
      denom = len(hists)-1
    else:
      LOG.insist(isinstance(denom,int),"Denominator index must be integer! Got denom=%r..."%(denom))
      if denom<0: # convert to positive number
        denom = max(0,len(hists)+denom)
      else: # shift by 1 to get index in list
        denom = max(0,denom-1)
        if denom>=len(hists):
          LOG.warn("Ratio.init: Warning index denom = %d >= %d = len(hists)! Setting to last index..."%(denom,len(hists)))
          denom = len(hists)-1
    
    # ASSIGN HISTOGRAMS as NUMERATOR or DENOMINATOR
    histnums = [ ]
    histdens = [ ]
    if len(hists)<=0:
      LOG.warn("Ratio.init: No histogram to compare with!")
    elif len(hists)==1:
      histnums = [hists[0]]
      histdens = [hists[0]]
    elif len(hists)==2 and any(islist(h) for h in hists): # at least one out of two arguments is a list
      histnums = hists[0]
      histdens = hists[1]
      if islist(histnums) and islist(histdens): # Ratio([hnum1,...],[hden1,...])
        while len(histnums)>len(histdens): # ensure same length
          histdens.append(histdens[-1])
      elif islist(histnums): # Ratio([hnum1,...],hden) -> single denominator
        histdens = [histdens]*len(histnums)
      elif islist(histdens): # Ratio(hnum,[hden1,...]) -> single numerator
        histnums = [histnums]*len(histdens)
    elif num!=None: # single numerator
      histdens = hists[:num] + hists[num+1:] # remove numerator
      histnum  = hists[num]
      if self.drawden: # include denominator histogram in numerator list
        histdens.insert(0,histnum) # reinsert as first item to draw first
      histnums = [histnum]*len(histdens) # match number of numerators for zip loop below
    else: # single denominator
      histnums = hists[:denom] + hists[denom+1:] # remove denominator
      histden  = hists[denom]
      if self.drawden: # include denominator histogram in numerator list
        histnums.insert(0,histden) # reinsert as first item to draw first
      histdens = [histden]*len(histnums) # match number of numerators for zip loop below
    LOG.verb("Ratio.init: histnums=%s, histdens=%s, denom=%r, num=%r"%(
      rootrepr(histnums),rootrepr(histdens),denom,num),verbosity,2)
    
    # MAKE RATIOS
    if len(histnums)!=len(histdens):
      LOG.warn("Ratio.init: len(histnums) = %s != %s = len(histdens)"%(len(histnums),len(histdens)))
    for i, (histnum,histden) in enumerate(zip(histnums,histdens)):
      tag = str(i)
      if histnum==None or histden==None:
        LOG.warn("Ratio.init: Cannot make ratio for histnum=%r / histden=%r (i=%s)! Ignoring..."%(histnum,histden,i))
        continue
      if isinstance(histnum,(TH1,THStack)):
        ratio = gethistratio(histnum,histden,tag=tag,drawzero=self.drawzero,errorX=errorX)
      elif isinstance(histnum,TGraph):
        #LOG.warn("Ratio.init: TGraph ratio not validated! Please check verbose output...")
        ratio = getgraphratio(histnum,histden,tag=tag,drawzero=self.drawzero,errorX=errorX)
      #if isinstance(hist,TH1) and 'h' in option.lower():
      #  ratio = hist.Clone("ratio_%s-%s_%d"%(histden.GetName(),hist.GetName(),i))
      #  ratio.Reset()
      #else:
      #  ratio = TGraphAsymmErrors()
      #  copystyle(ratio,hist)
      #  ratio.SetName("ratio_%s-%s_%d"%(histden.GetName(),hist.GetName(),i))
      #  ratio.SetTitle(self.title)
      copystyle(ratio,histnum if num==None else histden)
      ratio.SetFillStyle(0)
      self.ratios.append(ratio)
    
    # MAKE ERROR BAND RATIO
    if isinstance(errband,bool) and errband: # get error band for denominator histogram
      errband = geterrorband(histdens[0],name=makehistname("errband",histdens[0]))
    if isinstance(errband,TGraphAsymmErrors):
      self.errband = getgraphratio(errband,histdens[0],errorX=True)
      copystyle(self.errband,errband)
      #seterrorbandstyle(self.errband,style='hatched',color=errband.GetFillColor())
    
    # STORE
    self.frame    = histdens[0] if num==None else histnums[0] # use as frame
    self.fraction = fraction
    #self.frame   = self.histden.Clone("frame_ratio_%s"%(self.histden.GetName()))
    #self.frame.Reset() # make empty
    #self.frame.SetLineColor(0)
    #self.frame.SetLineWidth(0)
    #self.frame.SetMarkerSize(0)
    self.garbage = [self.fraction,self.errband]
    
  
  def draw(self, option=None, **kwargs):
    """Draw all objects."""
    verbosity   = LOG.getverbosity(kwargs,self)
    ratios      = self.ratios
    if isinstance(self.frame,TH1):
      xmin      = self.frame.GetXaxis().GetXmin()
      xmax      = self.frame.GetXaxis().GetXmax()
    else: # assume TGraph(Asymm)(Errors)
      xvals     = self.frame.GetX()
      xmin      = min(xvals)
      xmax      = max(xvals)
    xmin        = kwargs.get('xmin',   xmin  )
    xmax        = kwargs.get('xmax',   xmax  )
    ymin        = kwargs.get('ymin',   0.5   ) #default = 0.5
    ymax        = kwargs.get('ymax',   1.5   ) #default = 1.5
    data        = kwargs.get('data',   False )
    xtitle      = kwargs.get('xtitle', ""    )
    ytitle      = kwargs.get('ytitle', "Obs. / Exp." if data else "Ratio" )
    size        = 1.0 if data else 0.0 #0.9
    #self.frame  = gPad.DrawFrame(xmin,ymin,xmax,ymax)
    frame       = getframe(gPad,self.frame,xmin=xmin,xmax=xmax)
    self.garbage.append(frame)
    
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
    
    if self.fraction:
      self.fraction.Draw('HIST SAME')
    
    if self.errband:
      self.errband.Draw('2 SAME')
    
    if self.line:
      self.line = TGraph(2) #TLine(xmin,1,xmax,1)
      self.line.SetPoint(0,xmin,1.)
      self.line.SetPoint(1,xmax,1.)
      if data:
        self.line.SetLineColor(12)
        self.line.SetLineWidth(1)
        self.line.SetLineStyle(2)
      else:
        self.line.SetLineColor(self.frame.GetLineColor())
        self.line.SetLineWidth(self.frame.GetLineWidth())
        self.line.SetLineStyle(1)
      self.line.Draw('LSAME') # only draw line if a histogram has been drawn!
      self.garbage.append(self.line)
    
    for ratio in self.ratios:
      ratio.SetMaximum(ymax*1e10)
      if option:
        roption = option
      elif (ratio.GetLineWidth()==0 or 'E' in ratio.GetOption()) and ratio.GetMarkerSize()>0.05:
        roption = ratio.GetOption() if 'E' in ratio.GetOption() else 'E'
      else:
        roption = 'HIST' if isinstance(ratio,TH1) else 'PE0'
      roption += 'SAME'
      ratio.Draw(roption)
      LOG.verb("Ratio.draw: ratio=%s, roption=%r"%(ratio,roption),verbosity,2)
    
    self.frame = frame
    return frame
    
  
  def close(self):
    """Delete the histograms."""
    for ratio in self.ratios:
      deletehist(ratio)
    for rubbish in self.garbage:
      if not rubbish: continue
      if isinstance(rubbish,THStack):
        for hist in rubbish.GetHists():
          deletehist(hist)
      else:
        deletehist(rubbish)
    
  
