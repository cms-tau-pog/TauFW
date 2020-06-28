# Author: Izaak Neutelings (June 2020)
# -*- coding: utf-8 -*-
import os, re
from TauFW.common.tools.utils import ensurelist, islist, isnumber
from TauFW.Plotter.plot.utils import *
from TauFW.Plotter.plot.strings import maketitle, makelatex
from TauFW.Plotter.plot.Ratio import Ratio
import ROOT
from ROOT import gDirectory, gROOT, gPad, gStyle, TFile, TCanvas, TPad, TPaveText,\
                 TH1, TH1D, TH2, THStack, TGraph, TGraphAsymmErrors, TLine, TProfile,\
                 TLegend, TAxis, TGaxis, Double, TLatex, TBox, TColor,\
                 kBlack, kGray, kWhite, kRed, kBlue, kGreen, kYellow, kAzure, kCyan, kMagenta,\
                 kOrange, kPink, kSpring, kTeal, kViolet, kSolid, kDashed, kDotted
from math import sqrt, pow, log, log10, floor, ceil
gROOT.SetBatch(True)
#gStyle.SetEndErrorSize(0)
#whiteTransparent  = TColor(4000, 0.9, 0.9, 0.9, "kWhiteTransparent", 0.5)
#kWhiteTransparent = 4000

# CMS style
#TGaxis.SetExponentOffset(-0.074,0.015,'y')
CMSStyle.extraText    = "Preliminary"
#CMSStyle.cmsTextSize  = 0.75
#CMSStyle.lumiTextSize = 0.70
#CMSStyle.relPosX      = 0.12
CMSStyle.outOfFrame   = True
CMSStyle.lumi_13TeV   = ""
CMSStyle.setTDRStyle()

# https://root.cern.ch/doc/master/classTColor.html
# http://imagecolorpicker.com/nl
_tsize   = 0.060 # text size for axis titles
_lsize   = 0.048 # text size for axis labels and legend
_lcolors = [ kRed+1, kAzure+5, kGreen+2, kOrange+1, kMagenta-4, kYellow+1,
             kRed-9, kAzure-4, kGreen-2, kOrange+6, kMagenta+3, kYellow+2 ]
_fcolors = [ kRed-2, kAzure+5,
             kMagenta-3, kYellow+771, kOrange-5,  kGreen-2,
             kRed-7, kAzure-9, kOrange+382,  kGreen+3,  kViolet+5, kYellow-2 ]
             #kYellow-3
_lstyles = [ kSolid, kDashed, kDotted ]


class Plot(object):
  """Class to automatically make CMS plot."""
  
  def __init__(self, *args, **kwargs):
    """
    Initialize with list of histograms:
      plot = Plot(hists)
    or with a variable (string or Variable object) as well:
      plot = Plot(variable,hists)
    """
    variable       = None
    hists          = None
    self.verbosity = LOG.getverbosity(kwargs)
    if len(args)==1 and islist(args[0]):
      hists        = None
    elif len(args)==2:
      variable     = args[0]
      hists        = args[1]
    else:
      LOG.throw(IOError,"Plot: Wrong input %s"%(args))
    self.hists     = hists
    self.title     = kwargs.get('title', None )
    frame          = self.hists[0]
    #if isinstance(variable,Variable):
    #  self.variable         = variable
    #  self.xtitle           = kwargs.get('xtitle',    variable.title     )
    #  self.xmin             = kwargs.get('xmin',      variable.xmin      )
    #  self.xmax             = kwargs.get('xmax',      variable.xmax      )
    #  self.ymin             = kwargs.get('ymin',      variable.ymin      )
    #  self.ymax             = kwargs.get('ymax',      variable.ymax      )
    #  self.rmin             = kwargs.get('rmin',      variable.rmin      )
    #  self.rmax             = kwargs.get('rmax',      variable.rmax      )
    #  self.binlabels        = kwargs.get('binlabels', variable.binlabels )
    #  self.logx             = kwargs.get('logx',      variable.logx      )
    #  self.logy             = kwargs.get('logy',      variable.logy      )
    #  self.ymargin          = kwargs.get('ymargin',   variable.ymargin   )
    #  self.logyrange        = kwargs.get('logyrange', variable.logyrange )
    #  self.position         = kwargs.get('position',  variable.position  )
    #  self.latex            = kwargs.get('latex',     False              )
    #  self.divideByBinSize  = kwargs.get('divideByBinSize', variable.divideByBinSize)
    #else:
    if True:
      self.variable         = variable
      self.xtitle           = kwargs.get('xtitle', self.variable or frame.GetXaxis().GetTitle() )
      self.xmin             = kwargs.get('xmin', frame.GetXaxis().GetXmin() )
      self.xmax             = kwargs.get('xmax', frame.GetXaxis().GetXmax() )
      self.ymin             = kwargs.get('ymin',      None           )
      self.ymax             = kwargs.get('ymax',      None           )
      self.rmin             = kwargs.get('rmin',      None           )
      self.rmax             = kwargs.get('rmax',      None           )
      self.binlabels        = kwargs.get('binlabels', None           )
      self.logx             = kwargs.get('logx',      False          )
      self.logy             = kwargs.get('logy',      False          )
      self.ymargin          = kwargs.get('ymargin',   1.90 if self.logy else 1.18 )
      self.logyrange        = kwargs.get('logyrange', None           )
      self.position         = kwargs.get('position',  ""             )
      self.latex            = kwargs.get('latex',     True           )
      self.divideByBinSize  = kwargs.get('divideByBinSize', frame.GetXaxis().IsVariableBinSize())
    self.ytitle             = kwargs.get('ytitle',    frame.GetYaxis().GetTitle() )
    self.error              = None
    self.errorband          = None
    self.ratio              = kwargs.get('ratio',     False          )
    self.append             = kwargs.get('append',    ""             )
    self.norm               = kwargs.get('norm',      False          )
    self.canvas             = None
    self.frame              = frame
    self.legend             = None
    self.garbage            = [ ]
    
  
  def plot(self,*args,**kwargs):
    """Central method of Plot class: make plot with canvas, axis, error, ratio..."""
    # https://root.cern.ch/doc/master/classTHStack.html
    # https://root.cern.ch/doc/master/classTHistPainter.html#HP01e
    vartitle        = args[0] if args else self.xtitle or ""
    ratio           = kwargs.get('ratio',           self.ratio           )
    square          = kwargs.get('square',          False                )
    residue         = kwargs.get('residue',         False                )
    lmargin         = kwargs.get('lmargin',         1.                   )
    rmargin         = kwargs.get('rmargin',         1.                   )
    tmargin         = kwargs.get('tmargin',         1.                   )
    bmargin         = kwargs.get('bmargin',         1.                   )
    errorbars       = kwargs.get('errorbars',       True                 )
    staterror       = kwargs.get('staterror',       False                )
    sysvars         = kwargs.get('sysvars',         [ ]                  )
    norm            = kwargs.get('norm',            self.norm            )
    title           = kwargs.get('title',           self.title           )
    xtitle          = kwargs.get('xtitle',          vartitle             )
    ytitle          = "A.U." if norm else "Events"
    ytitle          = kwargs.get('ytitle',          self.ytitle          ) or ytitle
    rtitle          = kwargs.get('rtitle',          "Ratio"              )
    latex           = kwargs.get('latex',           self.latex           )
    xmin            = kwargs.get('xmin',            self.xmin            )
    xmax            = kwargs.get('xmax',            self.xmax            )
    ymin            = kwargs.get('ymin',            self.ymin            )
    ymax            = kwargs.get('ymax',            self.ymax            )
    rmin            = kwargs.get('rmin',            self.rmin            ) or 0.45
    rmax            = kwargs.get('rmax',            self.rmax            ) or 1.55
    ratiorange      = kwargs.get('ratiorange',      None                 )
    binlabels       = kwargs.get('binlabels',       self.binlabels       )
    ytitleoffset    = kwargs.get('ytitleoffset',    1.0                  )
    xtitleoffset    = kwargs.get('xtitleoffset',    1.0                  )
    logx            = kwargs.get('logx',            self.logx            )
    logy            = kwargs.get('logy',            self.logy            )
    ymargin         = kwargs.get('ymargin',         self.ymargin         )
    logyrange       = kwargs.get('logyrange',       self.logyrange       )
    grid            = kwargs.get('grid',            True                 )
    tsize           = kwargs.get('tsize',           _tsize               )
    text            = kwargs.get('text',            [ ]                  ) # extra text for legend
    errortitle      = kwargs.get('errortitle',      "Stat. unc."         )
    pair            = kwargs.get('pair',            False                )
    triple          = kwargs.get('triple',          False                )
    ncols           = kwargs.get('ncols',           1                    )
    lcolors         = kwargs.get('lcolors',         None                 )
    lstyles         = kwargs.get('lstyles',         None                 )
    lstyles         = kwargs.get('lstyle',          lstyles              )
    lwidth          = kwargs.get('lwidth',          2                    )
    mstyle          = kwargs.get('mstyle',          None                 )
    roption         = kwargs.get('roption',         'PEZ0'               )
    option          = kwargs.get('option',          'HIST'               )
    options         = kwargs.get('options',         [ ]                  )
    enderrorsize    = kwargs.get('enderrorsize',    2.0                  )
    errorX          = kwargs.get('errorX',          True                 ) # horizontal error bars
    divideByBinSize = kwargs.get('divideByBinSize', self.divideByBinSize )
    if errorbars: option = 'E0 '+option
    if not xmin:  xmin = self.xmin
    if not xmax:  xmax = self.xmax
    hists           = self.hists
    denominator     = ratio if isinstance(ratio,int) and (ratio!=0) else False
    denominator     = max(0,min(len(hists),kwargs.get('denom', denominator )))
    
    # NORM
    if norm:
      normalize(self.hists)
      if not ytitle: ytitle = "A.U."
    
    # DIVIDE BY BINSIZE
    if divideByBinSize:
      for i, hist in enumerate(self.hists):
        graph = divideBinsByBinSize(hist,zero=True,zeroErrors=False)
        if hist!=graph:
          self.hists[i] = graph
          self.garbage.append(hist)
    
    # DRAW OPTIONS
    if len(options)==0:
      options = [ option ]*len(hists)
    else:
      while len(options)<len(hists):
        options.append(options[-1])
    #if not self.histsD and staterror and errorbars:
    #  i = denominator-1 if denominator>0 else 0
    #  options[i] = options[i].replace('E0','')
    gStyle.SetEndErrorSize(enderrorsize)
    if not errorX:
      gStyle.SetErrorX(0)
    else:
      gStyle.SetErrorX(0.5)
    
    # CANVAS
    self.canvas = self.setcanvas(square=square,ratio=ratio,
                                 lmargin=lmargin,rmargin=rmargin,tmargin=tmargin,bmargin=bmargin)
    
    # DRAW
    self.canvas.cd(1)
    for i, (hist, option1) in enumerate(zip(hists,options)):
      if triple and i%3==2:
        hist.SetOption('E1')
        hist.Draw('E1 SAME')
      else:
        hist.Draw(option1+' SAME')
    
    # STYLE
    lhists, mhists = [ ], [ ]
    for hist, opt in zip(hists,options):
      if 'H' in opt: lhists.append(hist)
      else:          mhists.append(hist)
    self.setlinestyle(lhists,colors=lcolors,style=lstyles,mstyle=mstyle,width=lwidth,pair=pair,triple=triple)
    self.setmarkerstyle(*mhists,colors=lcolors)
    
    # CMS LUMI
    if CMSStyle.lumiText:
      #mainpad = self.canvas.GetPad(1 if ratio else 0)
      CMSStyle.setCMSLumiStyle(gPad,0)
    
    ## ERROR BAND
    #if staterror:
    #  stathist = self.histsB if stack else self.histsB[denominator-1] if denominator>1 else self.histsB[0] #if not self.histsD
    #  self.errorband = makeErrorBand(stathist,name=makeHistName("errorband",self.name),title=errortitle,sysvars=sysvars)
    #  self.errorband.Draw('E2 SAME')
    
    # AXES
    self.setaxes(self.frame,*hists,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,ymargin=ymargin,binlabels=binlabels,
                 xtitle=xtitle,ytitle=ytitle,main=ratio,
                 ytitleoffset=ytitleoffset,xtitleoffset=xtitleoffset,
                 logyrange=logyrange,logy=logy,logx=logx,grid=grid,latex=latex)
    
    # RATIO
    if ratio:
      self.canvas.cd(2)
      roption = 'HISTE' if errorbars else option
      self.ratio = Ratio(*hists,staterror=staterror,error=self.errorband,denominator=denominator,drawzero=True,option=roption)
      self.ratio.Draw(roption,xmin=xmin,xmax=xmax)
      self.setaxes(self.ratio,xmin=xmin,xmax=xmax,ymin=rmin,ymax=rmax,logx=logx,binlabels=binlabels,center=True,nydiv=506,
                   ratiorange=ratiorange,xtitle=xtitle,ytitle=rtitle,xtitleoffset=xtitleoffset,grid=grid,latex=latex)
      self.canvas.cd(1)
    
  
  def saveas(self,*fnames,**kwargs):
    """Save plot, close canvas and delete the histograms."""
    save  = kwargs.get('save',  True  )
    close = kwargs.get('close', False )
    exts  = kwargs.get('ext',   [ ]   ) #[".png"]
    pdf   = kwargs.get('pdf',   False )
    exts  = ensurelist(exts)
    if pdf:
      exts.append(".pdf")
    if save:
      for fname in fnames:
        if exts:
          for ext in ensurelist(exts):
            if not ext.startswith('.'):
              ext = '.'+ext
            fname = re.sub(r"\.?(png|pdf|jpg|gif|eps|tiff?|cc?|root)?$",ext,fname,re.IGNORECASE)
            self.canvas.SaveAs(fname)
        elif not any(fname.lower().endswith('.'+e) for e in ['png','pdf','jpg','gif','eps','tif','tiff','c','root']):
          self.canvas.SaveAs(fname+".png")
        else:
          self.canvas.SaveAs(fname)
    if close:
      self.close()
    
  
  def close(self):
    """Close canvas and delete the histograms."""
    if self.canvas:
      self.canvas.Close()
    for hist in self.hists:
      deletehist(hist)
    if self.errorband:
      deletehist(self.errorband)
    if self.error:
      deletehist(self.error)
    for hist in self.garbage:
      deletehist(hist)
    if self.ratio:
      self.ratio.close()
    
  
  def setcanvas(self,**kwargs):
    """Make canvas and pads for ratio plots."""
    square  = kwargs.get('square',  False )
    double  = kwargs.get('ratio',   False ) # include lower panel
    width   = kwargs.get('width',   900 if square else 800 if double else 800 )
    height  = kwargs.get('height',  900 if square else 750 if double else 600 )
    lmargin = kwargs.get('lmargin', 1.    )
    rmargin = kwargs.get('rmargin', 1.    )
    tmargin = kwargs.get('tmargin', 1.    )
    bmargin = kwargs.get('bmargin', 1.    )
    pads    = kwargs.get('pads',    [ ]   ) # pass list as reference
    #if not CMSStyle.lumi_13TeV:
    #  tmargin *= 0.7
    if square:
      lmargin *= 1.15
      tmargin *= 0.90
      #rmargin *= 3.6
      #CMSStyle.relPosX = 0.15
    canvas = TCanvas('canvas','canvas',100,100,width,height)
    canvas.SetFillColor(0)
    #canvas.SetFillStyle(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameBorderMode(0)
    if double:
      canvas.SetMargin(0.0,0.0,0.0,0.0) # LRBT
      canvas.Divide(2)
      canvas.cd(1)
      gPad.SetPad('pad1','pad1',0.0,0.33,1.0,1.0)
      gPad.SetMargin(0.145*lmargin,0.04*rmargin,0.029,0.07*tmargin)
      gPad.SetFillColor(0)
      gPad.SetFillStyle(4000) # transparant (for pdf)
      #gPad.SetFillStyle(0)
      gPad.SetBorderMode(0)
      gPad.Draw()
      canvas.cd(2)
      gPad.SetPad('pad2','pad2',0.0,0.0,1.0,0.33)
      gPad.SetMargin(0.145*lmargin,0.04*rmargin,0.355*bmargin,0.04)
      gPad.SetFillColor(0) #gPad.SetFillColorAlpha(0,0.0)
      gPad.SetFillStyle(4000) # transparant (for pdf)
      gPad.SetBorderMode(0)
      gPad.Draw()
      canvas.cd(1)
    else:
      canvas.SetMargin(0.145*lmargin,0.05*rmargin,0.145*bmargin,0.06*tmargin)
    return canvas
    
  
  def setaxes(self, *args, **kwargs):
    """Make axis."""
    verbosity = LOG.getverbosity(kwargs)
    hists     = [ ]
    binning   = [ ]
    for arg in args[:]:
      if hasattr(arg,'GetXaxis'):
        hists.append(arg)
      elif isinstance(arg,Ratio):
        hists.append(arg.frame)
      elif isnumber(arg):
        binning.append(arg)
    if not hists:
      LOG.warning("setaxes: No objects (TH1, TGraph, ...) given in args %s to set axis..."%(args))
      return 0, 0, 100, 100
    frame         = hists[0]
    if len(binning)>=2:
      xmin, xmax  = binning[:2]
    else:
      xmin, xmax  = frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax()
    nbins         = frame.GetXaxis().GetNbins()
    binwidth      = float(xmax-xmin)/nbins
    ymin, ymax    = None, None
    xmin          = kwargs.get('xmin',         xmin             )
    xmax          = kwargs.get('xmax',         xmax             )
    ymin          = kwargs.get('ymin',         ymin             )
    ymax          = kwargs.get('ymax',         ymax             )
    ratiorange    = kwargs.get('ratiorange',   None             )
    binlabels     = kwargs.get('binlabels',    None             )
    intbins       = kwargs.get('intbins',      True             )
    logx          = kwargs.get('logx',         False            )
    logy          = kwargs.get('logy',         False            )
    ymargin       = kwargs.get('ymargin',      1.80 if logy else 1.16 )
    logyrange     = kwargs.get('logyrange',    None             ) or 3
    negativeY     = kwargs.get('negativeY',    True             )
    xtitle        = kwargs.get('xtitle',       frame.GetTitle() )
    ytitle        = kwargs.get('ytitle',       ""               )
    grid          = kwargs.get('grid',         False            )
    ycenter       = kwargs.get('center',       False            )
    nxdivisions   = kwargs.get('nxdiv',        510              )
    nydivisions   = kwargs.get('nydiv',        510              )
    main          = kwargs.get('main',         False            ) # main panel of ratio plot
    scale         = 600./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    xtitlesize    = kwargs.get('xtitlesize',   _tsize           )*scale
    ytitlesize    = kwargs.get('ytitlesize',   _tsize           )*scale
    xlabelsize    = kwargs.get('xlabelsize',   0.075 if binlabels else _lsize)*scale
    ylabelsize    = kwargs.get('ylabelsize',   _lsize           )*scale
    ytitleoffset  = kwargs.get('ytitleoffset', 1.0              )*1.30/scale
    xtitleoffset  = kwargs.get('xtitleoffset', 1.0              )*1.00
    if main:
      xtitlesize  = 0.0
      xlabelsize  = 0.0
    LOG.verb("setaxes: Binning (%s,%.1f,%.1f)"%(nbins,xmin,xmax),verbosity,2)
    
    if ratiorange:
      ymin, ymax  = 1-ratiorange, 1+ratiorange
    if binlabels:
      nxdivisions = 15
    elif intbins and nbins<15 and int(xmin)==xmin and int(xmax)==xmax and binwidth==1:
      LOG.verb("setaxes: Setting integer binning for (%s,%d,%d)!"%(nbins,xmin,xmax),verbosity,1)
      binlabels   = [str(i) for i in range(int(xmin),int(xmax)+1)]
    
    if isinstance(frame,THStack):
      maxs = [ frame.GetMaximum() ]
      #frame = frame.GetStack().Last()
      for hist in hists:
        maxs.append(getTGraphYRange(hist)[1] if isinstance(hist,TGraph) else hist.GetMaximum())
      if ymax==None: ymax = max(maxs)*ymargin #ceilToSignificantDigit(max(maxs)*ymargin,digits=2)
    else:
      mins = [ 0 ]
      maxs = [   ]
      for hist in hists:
        ymin1, ymax1 = getTGraphYRange(hist) if isinstance(hist,TGraph) else hist.GetMinimum(), hist.GetMaximum()
        if negativeY: mins.append(ymin1)
        maxs.append(ymax1)
      if ymin==None: ymin = min(mins)*(1.1 if ymin>0 else 0.9)
      if ymax==None: ymax = max(maxs)*ymargin #ceilToSignificantDigit(max(maxs)*ymargin,digits=2)
    
    if logy:
      #if not ymin: ymin = 0.1
      if not ymin: ymin = 10**(magnitude(ymax)-logyrange) #max(0.1,10**(magnitude(ymax)-3))
      gPad.Update(); gPad.SetLogy()
    if logx:
      if not xmin: xmin = 0.1
      xmax *= 0.9999999999999
      gPad.Update(); gPad.SetLogx()
    if grid:
      gPad.SetGrid()
    frame.GetXaxis().SetRangeUser(xmin,xmax)
    if ymin!=None: frame.SetMinimum(ymin)
    else:          frame.SetMinimum(0.0)
    if ymax!=None: frame.SetMaximum(ymax)
    if ymax>=10000: ylabelsize *= 0.95
    
    if not ytitle:
      #ytitle = "Events"
      if "multiplicity" in xtitle.lower():
        ytitle = "Events"
      elif frame.GetXaxis().IsVariableBinSize():
        ytitle = "Events / GeV"
      else:
        ytitle = ("Events / %.3f"%frame.GetXaxis().GetBinWidth(0)).rstrip("0").rstrip(".")
        units = re.findall(r' \[(.+)\]',xtitle) #+ re.findall(r' (.+)',xtitle)
        if units:
          if ytitle[-2]==" 1":
            ytitle = ytitle[:-2]
          ytitle += " "+units[0]
        elif ytitle[-4:]==" / 1":
          ytitle = ytitle[:-4]
    
    # alphanumerical bin labels
    if binlabels:
      if len(binlabels)<nbins:
        LOG.warning("setaxes: len(binlabels)=%d < %d=nbins"%(len(binlabels),nbins))
      for i, binlabel in zip(range(1,nbins+1),binlabels):
        frame.GetXaxis().SetBinLabel(i,binlabel)
      #frame.GetXaxis().LabelsOption('h')
    
    # X axis
    frame.GetXaxis().SetLabelSize(xlabelsize)
    frame.GetXaxis().SetTitleSize(xtitlesize)
    frame.GetXaxis().SetTitleOffset(xtitleoffset)
    frame.GetXaxis().SetNdivisions(nxdivisions)
    frame.GetXaxis().SetTitle(xtitle)
    
    # Y axis
    if ycenter:
      frame.GetYaxis().CenterTitle(True)
    frame.GetYaxis().SetLabelSize(ylabelsize)
    frame.GetYaxis().SetTitleSize(ytitlesize)
    frame.GetYaxis().SetTitleOffset(ytitleoffset)
    frame.GetYaxis().SetNdivisions(nydivisions)
    frame.GetYaxis().SetTitle(ytitle)
    
    return xmin, xmax, ymin, ymax
    
  
  def setlegend(self,**kwargs):
    """Make legend."""
    #if not ratio:
    #  tsize *= 0.80
    #  signaltsize *= 0.80
    verbosity   = LOG.getverbosity(kwargs)
    hists       = self.hists
    scale       = 550./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    entries     = kwargs.get('entries',      [ ]                )
    bands       = kwargs.get('error',        [ ]                ) # error bands
    bands       = ensurelist(bands,nonzero=True)
    bandentries = kwargs.get('errorentries', bands[0].GetTitle() if bands else [ ] )
    title       = kwargs.get('title',        ""                 ) or ""
    style       = kwargs.get('style',        'lp'               )
    style0      = kwargs.get('style0',       None               )
    styles      = kwargs.get('styles',       [style]*len(hists) )
    position    = kwargs.get('position',     self.position      )
    option      = kwargs.get('option',       ''                 )
    transparent = kwargs.get('transparent',  True               )
    x1          = kwargs.get('x1',           0                  )
    x2          = kwargs.get('x2',           0                  )
    y1          = kwargs.get('y1',           0                  )
    y2          = kwargs.get('y2',           0                  )
    width       = kwargs.get('width',        -1                 )
    height      = kwargs.get('height',       -1                 )
    tsize       = kwargs.get('tsize',        _lsize             )*scale
    twidth      = kwargs.get('twidth',       1.0                )
    texts       = kwargs.get('text',         [ ]                )
    ncols       = kwargs.get('ncols',        1                  )
    colsep      = kwargs.get('colsep',       0.06               )
    bold        = kwargs.get('bold',         True               )
    texts       = ensurelist(texts,nonzero=True)
    bandentries = ensurelist(bandentries,nonzero=True)
    headerfont  = 62 if bold else 42
    
    # CHECK
    LOG.insist(self.canvas,"Canvas does not exist!")
    self.canvas.cd(1)
    
    # STYLES
    if style0:
      styles[0] = style0
      for hist in bands:
        styles.append('f')
    
    # ENTRIES
    #if len(bandentries)==len(bands) and len(entries)>len(hists):
    #  for band, bandtitle in zip(band,bandentries):
    #    entries.insert(hists.index(band),bandtitle)
    if len(entries)<len(hists):
      for i, hist in enumerate(hists):
        if len(entries)<i+1:
          entries.append(hist.GetTitle())
    if len(bandentries)<len(bands):
      for i, hist in enumerate(bands):
        if len(bandentries)<i+1:
          bandentries.append(hist.GetTitle())
    hists   = hists + bands
    entries = entries + bandentries
    
    # NUMBER of LINES
    nlines = sum([1+e.count('splitline') for e in entries])
    #else:       nlines += 0.80
    if texts:   nlines += sum([1+t.count('splitline') for t in texts])
    if ncols>1: nlines /= float(ncols)
    if title:   nlines += 1 + title.count('splitline')
    
    # DIMENSIONS
    L, R = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    if width<0:  width  = 0.26*twidth
    if height<0: height = 1.10*tsize*nlines
    if ncols>1:  width *= ncols/(1-colsep)
    x2 = 0.86-R; x1 = x2 - width
    y2 = 0.90-T; y1 = y2 - height
    
    # POSITION
    if not position:
      position = 'top' if title else 'topleft'
    position = position.lower()
    if   'leftleft'     in position: x1 = 0.04+L; x2 = x1 + width
    elif 'rightright'   in position: x2 = 0.94-R; x1 = x2 - width
    elif 'center'       in position:
      if 'right'        in position: center = (1+L-R)/2 + 0.075
      elif 'left'       in position: center = (1+L-R)/2 - 0.075
      else:                          center = (1+L-R)/2
      x1 = center-width/2; x2 = center+width/2
    elif 'left'         in position: x1 = 0.10+L; x2 = x1 + width
    elif 'right'        in position: x2 = 0.88-R; x1 = x2 - width
    elif 'x='           in position:
      x1 = float(re.findall(r"x=(\d\.\d+)",position)[0])
      x1 = L + (1-L-R)*x1; x2 = x1 + width
    if   'bottombottom' in position: y1 = 0.02+B; y2 = y1 + height
    elif 'bottom'       in position: y1 = 0.08+B; y2 = y1 + height
    elif 'toptop'       in position: y2 = 0.98-T; y1 = y2 - height
    elif 'top'          in position: y2 = 0.95-T; y1 = y2 - height
    elif 'middle'       in position:
      middle = (1+B-T)/2
      x1 = middle-height/2; x2 = middle+height/2
    elif 'y='           in position:
      y2 = float(re.findall(r"y=(\d\.\d+)",position)[0]);
      y2 = B + (1-T-B)*y2; y1 = y2 - height
    legend = TLegend(x1,y1,x2,y2)
    LOG.verb("setaxes: position=%r, height=%.3f, width=%.3f, x1=%.3f, y1=%.3f, x2=%.3f, y2=%.3f"%(
                       position,height,width,x1,y1,x2,y2),verbosity,1)
    
    # MARGIN
    if ncols>=2:
      margin = 0.086/width
    else:
      margin = 0.042/width
    legend.SetMargin(margin)
    if verbosity>=1:
      print ">>> setaxes: title=%r, texts=%s"%(title,texts)
      print ">>> setaxes: hists=%s"%(hists)
      print ">>> setaxes: entries=%s"%(entries)
      print ">>> setaxes: nlines=%s, len(hists)=%s, len(texts)=%s, ncols=%s, margin=%s"%(
                          nlines,len(hists),len(texts),ncols,margin)
    
    # STYLE
    if transparent: legend.SetFillStyle(0) # 0 = transparent
    else: legend.SetFillColor(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(tsize)
    legend.SetTextFont(headerfont) # bold for title
    if ncols>1:
      legend.SetNColumns(ncols)
      legend.SetColumnSeparation(colsep)
    
    # HEADER
    if title:
      legend.SetHeader(maketitle(title))
    legend.SetTextFont(42) # no bold for entries
    
    # ENTRIES
    if hists:
      for hist, entry, style in columnize(zip(hists,entries,styles),ncols):
        if "splitline" in entry:
          entry1, entry2 = re.findall(r"#splitline{(.*)}{(.*)}",entry)[0]
          legend.AddEntry(hist,maketitle(entry1),style)
          legend.AddEntry(   0,maketitle(entry2),'')
        else:
          legend.AddEntry(hist,maketitle(entry),style)
    for line in texts:
      legend.AddEntry(0,maketitle(line),'')
    
    legend.Draw(option)
    self.legend = legend
    return legend
    
  
  def setcornertext(self,*texts,**kwargs):
    ## CORNER TEXT
    scale    = 550./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    position = kwargs.get('position', 'topleft' ).lower()
    tsize    = kwargs.get('tsize',    _lsize    )*scale
    bold     = kwargs.get('bold',     False     )
    texts    = unwrapargs(texts)
    if not any(t!="" for t in texts):
      return None
    
    # POSITION
    font     = 62 if bold else 42
    align    = 13
    L, R     = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B     = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    if 'right' in position:
      x, align = 0.96, 30
    else:
      x, align = 0.05, 10
    if 'bottom' in position:
      y = 0.05; align += 1
    else:
      y = 0.95; align += 3
    #x1 = float(re.findall(r"x=(\d\.\d+)",position)[0])
    #y2 = float(re.findall(r"y=(\d\.\d+)",position)[0]);
    x = L + (1-L-R)*x
    y = B + (1-T-B)*y
    
    # LATEX
    latex = TLatex()
    latex.SetTextSize(tsize)
    latex.SetTextAlign(align)
    latex.SetTextFont(font)
    #latex.SetTextColor(kRed)
    latex.SetNDC(True)
    for i, line in enumerate(texts):
      latex.DrawLatex(x,y-i*1.2*tsize,line)
    return latex
    
  
  def setlinestyle(self,hists,**kwargs):
    """Set the line style for a list of histograms."""
    pair         = kwargs.get('pair',         False  )
    triple       = kwargs.get('triple',       False  )
    colors       = kwargs.get('color',        None   )
    colors       = kwargs.get('colors',       colors ) or _lcolors
    style        = kwargs.get('style',        True   )
    styles       = kwargs.get('styles',       None   ) or _lstyles
    width        = kwargs.get('width',        2      )
    offset       = kwargs.get('offset',       0      )
    style_offset = kwargs.get('style_offset', 0      )
    mstyle       = kwargs.get('mstyle',       None   )
    if mstyle==None:
      mstyle = triple or pair
    for i, hist in enumerate(hists):
      hist.SetFillColor(0)
      if triple:
        hist.SetLineColor(colors[(i//3)%len(colors)])
        hist.SetLineStyle(styles[i%3])
        hist.SetMarkerSize(0.6)
        hist.SetMarkerColor(hist.GetLineColor()+1)
      elif pair:
        hist.SetLineColor(colors[(i//2)%len(colors)])
        hist.SetLineStyle(styles[i%2])
        hist.SetMarkerColor(hist.GetLineColor()+1)
        if i%2==1: hist.SetMarkerSize(0.6)
        else:      hist.SetMarkerSize(0.0)
      else:
        hist.SetLineColor(colors[i%len(colors)])
        hist.SetMarkerSize(0.6)
        hist.SetMarkerColor(hist.GetLineColor()+1)
        if style:
          if isinstance(style,bool):
            hist.SetLineStyle(styles[i%len(styles)])
          else:
            hist.SetLineStyle(style)
      hist.SetLineWidth(width)
      if triple and i%3==2:
        hist.SetOption('E1')
        #hist.SetLineWidth(0)
        hist.SetLineStyle(kSolid)
        hist.SetLineColor(hist.GetMarkerColor())
      elif not mstyle:
        hist.SetMarkerSize(0)
    
  
  def setmarkerstyle(self, *hists, **kwargs):
    """Set the marker style for a list of histograms."""
    pass
    
  
  def setfillstyle(self, *hists, **kwargs):
    """Set the fill style for a list of histograms."""
    pass
    
  

