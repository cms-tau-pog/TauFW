# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/view/CMS/PoissonErrorBars
#   https://twiki.cern.ch/twiki/bin/view/CMS/StatComWideBins
#   https://twiki.cern.ch/twiki/bin/view/CMS/DataMCComparison
import os, re
from TauFW.Plotter.plot.utils import *
from TauFW.Plotter.plot.string import makehistname
import ROOT
from ROOT import TH1, TProfile, TLine


class Ratio(object):
  """Class to make bundle histograms (ratio, stat. error on MC and line) for ratio plot."""
  
  def __init__(self, *hists, **kwargs):
    """Make a ratio of two histograms bin by bin. Second hist may be a stack, to do data / MC stack.
    There are several ways to initiate this object, depending on which histograms/stacks/graphs
    should be taken as numerator and which should be taken as denominator:
      Ratio(hnum,hden)               # hnum / hden and 1 = hden / hden
      Ratio( h1,h2,...,hN)           # hists[i]   / hists[-1]
      Ratio([h1,h2,...,hN])          # hists[i]   / hists[-1]
      Ratio( h1,h2,...,hN ,denom=X)  # hists[i]   / hists[X-1]
      Ratio([h1,h2,...,hN],denom=X)  # hists[i]   / hists[X-1]
      Ratio( h1,h2,...,hN ,num=X)    # hists[X-1] / hists[i]
      Ratio([h1,h2,...,hN],num=X)    # hists[X-1] / hists[i]
      Ratio([hnum1,...], hden)       # hnums[i] / hden,     single & common den histogram
      Ratio([hnum1,...],[hden1,...]) # hnums[i] / hdens[i], pairwise num/den histograms
      Ratio( hnum,      [hden1,...]) # hnum     / hdens[i], single & common num histogram
    where
      hists = [h1,h2,...,hN] is a python list of histograms/stacks/graphs,
      index X is a single integer between 1<=X<=N, and
      index i loops between 0<=i<=N-1.
    """
    self.verbosity = LOG.getverbosity(kwargs)
    self.ratios    = [ ]
    self.errband   = None
    self.drawden   = kwargs.get('drawden',     False       ) # draw denominator (with error bars)
    self.title     = kwargs.get('title',       "ratio"     ) # title for ratio histogram/graph
    self.line      = kwargs.get('line',   not self.drawden ) # draw line at 1.0
    self.drawzero  = kwargs.get('drawzero',    True        ) # draw ratio of two zero bins as 1
    errband        = kwargs.get('errband',     None        ) # draw error band (e.g. stat. and/or sys. unc.)
    errbars        = kwargs.get('errbars',     False       ) # draw error bars
    option         = kwargs.get('option',      ""          ) # draw option
    num            = kwargs.get('num',         None        ) # index of common numerator histogram (count from 1)
    denom          = kwargs.get('den',         None        ) # index of common denominator histogram (count from 1)
    denom          = kwargs.get('denom',       None        ) # alias
    errorX         = kwargs.get('errorX', gStyle.GetErrorX() ) # horizontal error bars
    fraction       = kwargs.get('fraction',    None        ) # make stacked fraction from stack (normalize each bin to 1)
    hists          = unpacklistargs(hists) # ensure list of histograms
    LOG.verb("Ratio.init: hists=%r, denom=%r, num=%r, drawden=%r, errband=%r"%(
      hists,denom,num,self.drawden,errband),self.verbosity,1)
    
    # CONVERT SPECIAL OBJECTS
    for i, hist in enumerate(hists[:]):
      if isinstance(hist,THStack): # convert TStack to TH1D
        if isinstance(fraction,bool) and fraction: # only once
          fraction = normalizebins(hist) # create stack with normalized bins
        hists[i] = hist.GetStack().Last() # should have correct bin content and error
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
    LOG.verb("Ratio.init: histnums=%r, histdens=%r, denom=%r, num=%r"%(
      histnums,histdens,denom,num),self.verbosity,2)
    
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
        ratio = getgraphratio(histnum,histden,tag=tag,drawzero=self.drawzero,errorX=kwargs.get('errorX',True))
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
    #self.frame    = self.histden.Clone("frame_ratio_%s"%(self.histden.GetName()))
    #self.frame.Reset() # make empty
    #self.frame.SetLineColor(0)
    #self.frame.SetLineWidth(0)
    #self.frame.SetMarkerSize(0)
    if isinstance(self.frame,TH1): # set default xmin/xmax
      self.xmin  = self.frame.GetXaxis().GetXmin()
      self.xmax  = self.frame.GetXaxis().GetXmax()
    else: # assume TGraph(Asymm)(Errors)
      xvals     = self.frame.GetX()
      self.xmin = min(xvals)
      self.xmax = max(xvals)
    self.garbage  = [self.fraction,self.errband]
    
  
  def draw(self, option=None, **kwargs):
    """Draw all objects."""
    verbosity = LOG.getverbosity(kwargs,self)
    ratios = self.ratios
    xmin   = kwargs.get('xmin', self.xmin  )
    xmax   = kwargs.get('xmax', self.xmax  )
    ymin   = kwargs.get('ymin',   0.5      ) #default = 0.5
    ymax   = kwargs.get('ymax',   1.5      ) #default = 1.5
    data   = kwargs.get('data',   False    )
    line   = kwargs.get('line',  self.line ) # draw horizontal line
    lines  = kwargs.get('lines',  [ ]      ) # draw other lines
    boxes  = kwargs.get('boxes',  [ ]      ) # draw boxes
    yline  = kwargs.get('yline',  1.0      ) # y coordinate of line
    xtitle = kwargs.get('xtitle', ""       )
    ytitle = kwargs.get('ytitle', "Obs. / Exp." if data else "Ratio" )
    size   = 1.0 if data else 0.0 #0.9
    frame  = getframe(gPad,self.frame,xmin=xmin,xmax=xmax,verb=verbosity)
    self.garbage.append(frame)
    LOG.verb("Ratio.draw: (xmin,xmax,ymin,ymax)=(%.3g,%.3g,%.3g,%.3g), option=%r, frame=%r, data=%r"%(
             xmin,xmax,ymin,ymax,option,frame,data),verbosity,2)
    
    # FRAME
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
    
    # DRAW OTHER
    if self.fraction: # stacked fraction histograms
      self.fraction.Draw('HIST SAME')
    if self.errband: # uncertainty band
      self.errband.Draw('2 SAME')
    for box in boxes:
      box.Draw(box.option)
    for line in lines:
      line.Draw(line.option)
    
    # HORIZONTAL LINE
    if line or not isinstance(line,bool): # horizontal line at y = yline
      self.line = TGraph(2) #TLine(xmin,1,xmax,1) # use TGraph to stay inside frame
      self.line.SetPoint(0,xmin,yline)
      self.line.SetPoint(1,xmax,yline)
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
    
    # DRAW ACTUAL RATIOS
    if self.ratios: # draw actual ratio(s) histograms/graphs
      self.drawratios(option)
    
    self.frame = frame
    self.xmin  = xmin
    self.xmax  = xmax
    return frame
    
  
  def drawratios(self, option=None, **kwargs):
    """Help function to just draw ratios."""
    verbosity = LOG.getverbosity(kwargs,self)
    for ratio in self.ratios:
      goption = ratio.GetOption() if hasattr(ratio,'GetOption') else '' # previous
      ratio.SetMaximum(1e50)
      if option!=None: # user option
        roption = option
      elif (ratio.GetLineWidth()==0 or 'E' in goption) and ratio.GetMarkerSize()>0.05:
        roption = goption if 'E' in goption else 'E'
      else: # '][' prevents the first/last vertical bars to 0
        roption = '][ HIST' if isinstance(ratio,TH1) else 'PE0'
      if isinstance(ratio,TGraph):
        roption = roption.replace('HIST','P').strip() or 'PE0'
      roption += 'SAME'
      ratio.Draw(roption)
      LOG.verb("Ratio.draw: ratio=%r, goption=%r, roption=%r"%(ratio,goption,roption),verbosity,2)
    if kwargs.get('redraw',False):
      gPad.RedrawAxis()
    return self.ratios
    
  
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

  
