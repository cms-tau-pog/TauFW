# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
# Description: Class to automatically make CMS plot comparing histograms.
import os, re
from TauFW.common.tools.utils import ensurelist, islist, isnumber, repkey
from TauFW.common.tools.math import log10, magnitude, columnize, scalevec
from TauFW.Plotter.plot.utils import *
from TauFW.Plotter.plot.string import makelatex, maketitle, makehistname, estimatelen
from TauFW.Plotter.plot.Variable import Variable, Var
from TauFW.Plotter.plot.Ratio import Ratio
import ROOT
from ROOT import gDirectory, gROOT, gPad, gStyle, TFile, TCanvas,\
                 TH1, TH1D, TH2, TH2F, THStack, TGraph, TGraphAsymmErrors, TLine, TProfile,\
                 TLegend, TAxis, TGaxis, Double, TLatex, TBox, TColor,\
                 kBlack, kGray, kWhite, kRed, kBlue, kGreen, kYellow, kAzure, kCyan, kMagenta,\
                 kOrange, kPink, kSpring, kTeal, kViolet, kSolid, kDashed, kDotted
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
_lstyles = [ kSolid, kDashed, ] # kDotted ]
_lmargin = 0.145 # default left margin used in Plot.setcanvas, Plot.setaxes


class Plot(object):
  """Class to automatically make CMS plot comparing histograms."""
  
  def __init__(self, *args, **kwargs):
    """
    Initialize with list of histograms:
      Plot(hists)
    or with a variable (string or Variable object) as well:
      Plot(variable,hists)
    """
    variable   = None
    hists      = None
    self.verbosity = LOG.getverbosity(kwargs)
    if len(args)==1 and islist(args[0]):
      hists    = args[0] # list of histograms
    elif len(args)==2:
      variable = args[0] # string or Variable
      hists    = ensurelist(args[1]) # list of histograms
    else:
      LOG.throw(IOError,"Plot: Wrong input %s"%(args,))
    for hist in hists:
      if not hist or not isinstance(hist,TH1):
        LOG.throw(IOError,"Plot: Did not recognize histogram in input: %s"%(args,))
    if kwargs.get('clone',False):
      hists    = [h.Clone(h.GetName()+"_clone_Plot") for h in hists]
    self.hists = hists
    self.frame = kwargs.get('frame', None )
    frame      = self.frame or self.hists[0]
    if isinstance(variable,Variable):
      self.variable   = variable
      self.name       = kwargs.get('name',       variable.filename    )
      self.xtitle     = kwargs.get('xtitle',     variable.title       )
      self.xmin       = kwargs.get('xmin',       variable.xmin        )
      self.xmax       = kwargs.get('xmax',       variable.xmax        )
      self.ymin       = kwargs.get('ymin',       variable.ymin        )
      self.ymax       = kwargs.get('ymax',       variable.ymax        )
      self.rmin       = kwargs.get('rmin',       variable.rmin        )
      self.rmax       = kwargs.get('rmax',       variable.rmax        )
      self.ratiorange = kwargs.get('rrange',     variable.ratiorange  )
      self.binlabels  = kwargs.get('binlabels',  variable.binlabels   )
      self.logx       = kwargs.get('logx',       variable.logx        )
      self.logy       = kwargs.get('logy',       variable.logy        )
      self.ymargin    = kwargs.get('ymargin',    variable.ymargin     )
      self.logyrange  = kwargs.get('logyrange',  variable.logyrange   )
      self.position   = kwargs.get('position',   variable.position    )
      self.ncols      = kwargs.get('ncols',      variable.ncols       )
      self.latex      = kwargs.get('latex',      False                ) # already done by Variable.__init__
      self.dividebins = kwargs.get('dividebins', variable.dividebins  ) # divide each histogram bins by it bin size
    else:
      self.variable   = variable or frame.GetXaxis().GetTitle()
      self.name       = kwargs.get('name',       None                 )
      self.xtitle     = kwargs.get('xtitle',     self.variable        )
      self.xmin       = kwargs.get('xmin', frame.GetXaxis().GetXmin() )
      self.xmax       = kwargs.get('xmax', frame.GetXaxis().GetXmax() )
      self.ymin       = kwargs.get('ymin',       None                 )
      self.ymax       = kwargs.get('ymax',       None                 )
      self.rmin       = kwargs.get('rmin',       None                 )
      self.rmax       = kwargs.get('rmax',       None                 )
      self.ratiorange = kwargs.get('rrange',     None                 )
      self.binlabels  = kwargs.get('binlabels',  None                 )
      self.logx       = kwargs.get('logx',       False                )
      self.logy       = kwargs.get('logy',       False                )
      self.ymargin    = kwargs.get('ymargin',    None                 )
      self.logyrange  = kwargs.get('logyrange',  None                 )
      self.position   = kwargs.get('position',   ""                   )
      self.ncols      = kwargs.get('ncols',      None                 )
      self.latex      = kwargs.get('latex',      True                 )
      self.dividebins = kwargs.get('dividebins', frame.GetXaxis().IsVariableBinSize())
    self.ytitle       = kwargs.get('ytitle', frame.GetYaxis().GetTitle() or None )
    self.name         = self.name or (self.hists[0].GetName() if self.hists else "noname")
    self.title        = kwargs.get('title',      None                 )
    self.errband      = None
    self.ratio        = kwargs.get('ratio',      False                )
    self.append       = kwargs.get('append',     ""                   )
    self.norm         = kwargs.get('norm',       False                )
    self.lcolors      = kwargs.get('lcolors',    _lcolors             )
    self.fcolors      = kwargs.get('fcolors',    _fcolors             )
    self.lstyles      = kwargs.get('lstyles',    _lstyles             )
    self.canvas       = None
    self.legends      = [ ]
    self.texts        = [ ] # to save TLatex objects made by drawtext
    self.lines        = [ ]
    self.garbage      = [ ]
    
  
  def draw(self,*args,**kwargs):
    """Central method of Plot class: make plot with canvas, axis, error, ratio..."""
    # https://root.cern.ch/doc/master/classTHStack.html
    # https://root.cern.ch/doc/master/classTHistPainter.html#HP01e
    verbosity    = LOG.getverbosity(self,kwargs)
    xtitle       = (args[0] if args else self.xtitle) or ""
    ratio        = kwargs.get('ratio',        self.ratio      ) # make ratio plot
    cwidth       = kwargs.get('width',        None            ) # canvas width
    cheight      = kwargs.get('height',       None            ) # canvas height
    square       = kwargs.get('square',       False           ) # square canvas
    lmargin      = kwargs.get('lmargin',      1.              ) # canvas left margin
    rmargin      = kwargs.get('rmargin',      1.              ) # canvas righ margin
    tmargin      = kwargs.get('tmargin',      1.              ) # canvas bottom margin
    bmargin      = kwargs.get('bmargin',      1.              ) # canvas top margin
    errbars      = kwargs.get('errbars',      True            ) # add error bars to histogram
    staterr      = kwargs.get('staterr',      False           ) # create stat. error band
    sysvars      = kwargs.get('sysvars',      [ ]             ) # create sys. error band from variations
    errtitle     = kwargs.get('errtitle',     None            ) # title for error band
    norm         = kwargs.get('norm',         self.norm       ) # normalize all histograms
    xtitle       = kwargs.get('xtitle',       xtitle          ) # x axis title
    ytitle       = kwargs.get('ytitle',       self.ytitle     ) # y axis title (if None, automatically set by Plot.setaxis)
    rtitle       = kwargs.get('rtitle',       "Ratio"         ) # y axis title of ratio panel
    latex        = kwargs.get('latex',        self.latex      ) # automatically format strings as LaTeX with makelatex
    xmin         = kwargs.get('xmin',         self.xmin       )
    xmax         = kwargs.get('xmax',         self.xmax       )
    ymin         = kwargs.get('ymin',         self.ymin       )
    ymax         = kwargs.get('ymax',         self.ymax       )
    rmin         = kwargs.get('rmin',         self.rmin       ) or 0.45 # ratio ymin
    rmax         = kwargs.get('rmax',         self.rmax       ) or 1.55 # ratio ymax
    ratiorange   = kwargs.get('rrange',       self.ratiorange ) # ratio range around 1.0
    binlabels    = kwargs.get('binlabels',    self.binlabels  ) # list of alphanumeric bin labels
    labeloption  = kwargs.get('labeloption',  None            ) # 'h'=horizontal, 'v'=vertical
    xtitleoffset = kwargs.get('xtitleoffset', 1.0             )*bmargin # scale x title offset
    ytitleoffset = kwargs.get('ytitleoffset', 1.0             ) # scale y title offset
    xlabelsize   = kwargs.get('xlabelsize',   _lsize          ) # x label size
    ylabelsize   = kwargs.get('ylabelsize',   _lsize          ) # y label size
    logx         = kwargs.get('logx',         self.logx       )
    logy         = kwargs.get('logy',         self.logy       )
    ymargin      = kwargs.get('ymargin',      self.ymargin    ) # margin between hist maximum and plot's top
    logyrange    = kwargs.get('logyrange',    self.logyrange  ) # log(y) range from hist maximum to ymin
    grid         = kwargs.get('grid',         True            )
    tsize        = kwargs.get('tsize',        _tsize          ) # text size for axis title
    pair         = kwargs.get('pair',         False           )
    triple       = kwargs.get('triple',       False           )
    lcolors      = kwargs.get('colors',       None            )
    lcolors      = kwargs.get('lcolors',      lcolors         ) or self.lcolors # line colors
    fcolors      = kwargs.get('fcolors',      None            ) or self.fcolors # fill colors
    lstyles      = kwargs.get('style',        None            )
    lstyles      = kwargs.get('lstyle',       lstyles         )
    lstyles      = kwargs.get('lstyles',      lstyles         ) or self.lstyles # line styles
    lwidth       = kwargs.get('lwidth',       2               ) # line width
    mstyle       = kwargs.get('mstyle',       None            ) # marker style
    option       = kwargs.get('option',       'HIST'          ) # draw option for every histogram
    options      = kwargs.get('options',      [ ]             ) # draw option list per histogram
    roption      = kwargs.get('roption',      None            ) # draw option of ratio plot
    enderrorsize = kwargs.get('enderrorsize', 2.0             ) # size of line at end of error bar
    errorX       = kwargs.get('errorX',       True            ) # horizontal error bars
    dividebins   = kwargs.get('dividebins',   self.dividebins )
    lcolors      = ensurelist(lcolors)
    fcolors      = ensurelist(fcolors)
    lstyles      = ensurelist(lstyles)
    self.ratio   = ratio
    self.lcolors = lcolors
    self.fcolors = fcolors
    self.lstyles = lstyles
    if not xmin and xmin!=0: xmin = self.xmin
    if not xmax and xmax!=0: xmax = self.xmax
    hists        = self.hists
    denom        = ratio if isinstance(ratio,int) and (ratio!=0) else False
    denom        = max(0,min(len(hists),kwargs.get('denom', denom ))) # denominator histogram in ratio plot
    
    # NORMALIZE
    if norm:
      if ytitle==None:
        ytitle = "A.U."
      scale =  1.0 if isinstance(norm,bool) else norm
      normalize(self.hists,scale=scale)
    
    # DIVIDE BY BINSIZE
    if dividebins:
      for i, oldhist in enumerate(self.hists):
        newhist = dividebybinsize(oldhist,zero=True,zeroerrs=False)
        if oldhist!=newhist: # new hist is actually a TGraph
          LOG.verb("Plot.draw: replace %s -> %s"%(oldhist,newhist),verbosity,2)
          self.hists[i] = newhist
          self.garbage.append(oldhist)
      #if sysvars:
      #  histlist = sysvars.values() if isinstance(sysvars,dict) else sysvars
      #  for (histup,hist,histdown) in histlist:
      #    dividebybinsize(histup,  zero=True,zeroerrs=False)
      #    dividebybinsize(histdown,zero=True,zeroerrs=False)
      #    if hist not in self.hists:
      #      dividebybinsize(hist,zero=True,zeroerrs=False)
    
    # DRAW OPTIONS
    if errbars:
      option = 'E0 '+option #E01
      if not roption:
        roption = 'HISTE'
    if len(options)==0:
      options = [ option ]*len(hists)
      if staterr:
        options[0] = 'HIST' # E3'
    else:
      while len(options)<len(hists):
        options.append(options[-1])
    #if not self.histsD and staterr and errbars:
    #  i = denominator-1 if denominator>0 else 0
    #  options[i] = options[i].replace('E0','')
    gStyle.SetEndErrorSize(enderrorsize)
    if errorX:
      gStyle.SetErrorX(0.5)
    else:
      gStyle.SetErrorX(0)
    
    # CANVAS
    self.canvas = self.setcanvas(square=square,lower=ratio,width=cwidth,height=cheight,
                                 lmargin=lmargin,rmargin=rmargin,tmargin=tmargin,bmargin=bmargin)
    
    # STYLE
    lhists, mhists = [ ], [ ]
    for hist, opt in zip(hists,options):
      if 'H' in opt: lhists.append(hist)
      else:          mhists.append(hist)
    self.setlinestyle(lhists,colors=lcolors,styles=lstyles,mstyle=mstyle,width=lwidth,pair=pair,triple=triple)
    self.setmarkerstyle(*mhists,colors=lcolors)
    
    # DRAW FRAME
    self.canvas.cd(1)
    if not self.frame: # if not given by user
      self.frame = getframe(gPad,self.hists[0],xmin,xmax)
      #self.frame.Draw('AXIS') # 'AXIS' breaks GRID?
    elif self.frame!=self.hists[0]:
      self.frame.Draw('AXIS') # 'AXIS' breaks GRID?
    
    # DRAW LINE
    for line in self.lines:
      if line.pad==1:
        line.Draw("LSAME")
    
    # DRAW HISTS
    for i, (hist, option1) in enumerate(zip(hists,options)):
      if triple and i%3==2:
        option1 = 'E1'
      if 'SAME' not in option1: #i>0:
        option1 += " SAME"
      hist.Draw(option1)
      LOG.verb("Plot.draw: i=%s, hist=%s, option=%r"%(i,hist,option1),verbosity,2)
    
    # CMS STYLE
    if CMSStyle.lumiText:
      #mainpad = self.canvas.GetPad(1 if ratio else 0)
      CMSStyle.setCMSLumiStyle(gPad,0)
    
    # ERROR BAND
    if staterr or sysvars:
      #seterrorbandstyle(hists[0],fill=False)
      self.errband = geterrorband(self.hists[0],sysvars=sysvars,color=self.hists[0].GetLineColor(),
                                  name=makehistname("errband",self.name),title=errtitle)
      self.errband.Draw('E2 SAME')
    
    # AXES
    self.setaxes(self.frame,*hists,main=ratio,grid=grid,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,logy=logy,logx=logx,
                 xtitle=xtitle,ytitle=ytitle,ytitleoffset=ytitleoffset,xtitleoffset=xtitleoffset,xlabelsize=xlabelsize,
                 binlabels=binlabels,labeloption=labeloption,ymargin=ymargin,logyrange=logyrange,latex=latex)
    
    # RATIO
    if ratio:
      self.canvas.cd(2)
      self.ratio = Ratio(*hists,errband=self.errband,denom=denom,drawzero=True,option=roption)
      self.ratio.draw(roption,xmin=xmin,xmax=xmax)
      self.setaxes(self.ratio,grid=grid,xmin=xmin,xmax=xmax,ymin=rmin,ymax=rmax,logx=logx,
                   binlabels=binlabels,labeloption=labeloption,xlabelsize=xlabelsize,xtitleoffset=xtitleoffset,
                   center=True,nydiv=506,rrange=ratiorange,xtitle=xtitle,ytitle=rtitle,latex=latex)
      for line in self.lines:
        if line.pad==2:
          line.Draw("LSAME")
      self.canvas.cd(1)
    
  
  def saveas(self,*fnames,**kwargs):
    """Save plot, close canvas and delete the histograms."""
    save   = kwargs.get('save',   True  )
    close  = kwargs.get('close',  False )
    outdir = kwargs.get('outdir', ""    ) # output directory
    tag    = kwargs.get('tag',    ""    ) # extra tag for output file
    exts   = kwargs.get('ext',    [ ]   ) # [".png"]
    pdf    = kwargs.get('pdf',    False )
    exts   = ensurelist(exts)
    if pdf:
      exts.append(".pdf")
    if not fnames:
      fnames = [self.name+tag]
    if save:
      for fname in fnames:
        fname = os.path.join(outdir,repkey(fname,VAR=self.name,NAME=self.name,TAG=tag))
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
    
  
  def close(self,keep=False,**kwargs):
    """Close canvas and delete the histograms."""
    verbosity = LOG.getverbosity(self,kwargs)
    if self.canvas:
      self.canvas.Close()
    if not keep: # do not keep histograms
      for hist in self.hists:
        deletehist(hist)
    if self.errband:
      deletehist(self.errband)
    for line in self.lines:
      deletehist(line)
    for hist in self.garbage:
      deletehist(hist)
    if isinstance(self.ratio,Ratio):
      self.ratio.close()
    LOG.verb("closed\n>>>",verbosity,2)
    
  
  def setcanvas(self,**kwargs):
    """Make canvas and pads for ratio plots."""
    verbosity = LOG.getverbosity(self,kwargs)
    square  = kwargs.get('square',  False )
    lower   = kwargs.get('lower',   False ) # include lower panel
    split   = kwargs.get('split',   0.33  ) # split lower panel
    width_  = 900 if square else 800 # default
    width   = kwargs.get('width',   None  ) or width_
    height  = kwargs.get('height',  None  ) or (900 if square else 750 if lower else 600)
    wscale  = width_/float(width)
    lmargin = kwargs.get('lmargin', 1.    )*wscale # scale left margin
    rmargin = kwargs.get('rmargin', 1.    )*wscale # scale right margin
    tmargin = kwargs.get('tmargin', 1.    ) # scale top margin
    bmargin = kwargs.get('bmargin', 1.    ) # scale bottom margin
    pads    = kwargs.get('pads',    [ ]   ) # pass list as reference
    #if not CMSStyle.lumi_13TeV:
    #  tmargin *= 0.7
    if square:
      lmargin *= 1.15
      tmargin *= 0.90
      #rmargin *= 3.6
      #CMSStyle.relPosX = 0.15
    if verbosity>=2:
      print "Plot.setcanvas: square=%r, lower=%r, split=%r"%(square,lower,split)
      print "Plot.setcanvas: width=%s, height=%s"%(width,height)
      print "Plot.setcanvas: lmargin=%.5g, rmargin=%.5g, tmargin=%.5g, bmargin=%.5g"%(lmargin,rmargin,tmargin,bmargin)
    canvas = TCanvas('canvas','canvas',100,100,int(width),int(height))
    canvas.SetFillColor(0)
    #canvas.SetFillStyle(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameBorderMode(0)
    if lower:
      canvas.SetMargin(0.0,0.0,0.0,0.0) # LRBT
      canvas.Divide(2)
      canvas.cd(1)
      gPad.SetPad('pad1','pad1',0.0,split,1.0,1.0)
      gPad.SetMargin(_lmargin*lmargin,0.04*rmargin,0.029,0.075*tmargin)
      gPad.SetFillColor(0)
      gPad.SetFillStyle(4000) # transparant (for pdf)
      #gPad.SetFillStyle(0)
      gPad.SetBorderMode(0)
      gPad.Draw()
      canvas.cd(2)
      gPad.SetPad('pad2','pad2',0.0,0.0,1.0,split)
      gPad.SetMargin(_lmargin*lmargin,0.04*rmargin,0.355*bmargin,0.04)
      gPad.SetFillColor(0) #gPad.SetFillColorAlpha(0,0.0)
      gPad.SetFillStyle(4000) # transparant (for pdf)
      gPad.SetBorderMode(0)
      gPad.Draw()
      canvas.cd(1)
    else:
      canvas.SetMargin(_lmargin*lmargin,0.05*rmargin,0.145*bmargin,0.06*tmargin)
    return canvas
    
  
  def setaxes(self, *args, **kwargs):
    """Make axis."""
    verbosity = LOG.getverbosity(self,kwargs)
    hists     = [ ]
    binning   = [ ]
    lower     = False # lower panel (e.g. for ratio)
    for arg in args[:]:
      if hasattr(arg,'GetXaxis'):
        hists.append(arg)
      elif isinstance(arg,Ratio):
        lower = True
        hists.append(arg.frame)
      elif isnumber(arg):
        binning.append(arg)
    if not hists:
      LOG.warning("Plot.setaxes: No objects (TH1, TGraph, ...) given in args %s to set axis..."%(args))
      return 0, 0, 100, 100
    frame         = hists[0]
    if len(binning)>=2:
      xmin, xmax  = binning[:2]
    else:
      xmin, xmax  = frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax()
    nbins         = frame.GetXaxis().GetNbins()
    binwidth      = float(xmax-xmin)/nbins
    xmin          = kwargs.get('xmin',         xmin             )
    xmax          = kwargs.get('xmax',         xmax             )
    ymin          = kwargs.get('ymin',         None             )
    ymax          = kwargs.get('ymax',         None             )
    ratiorange    = kwargs.get('rrange',       None             )
    binlabels     = kwargs.get('binlabels',    None             ) # alphanumerical bin labels
    intbins       = kwargs.get('intbins',      True             ) # allow integer binning
    labeloption   = kwargs.get('labeloption',  None             ) # 'h'=horizontal, 'v'=vertical
    logx          = kwargs.get('logx',         False            )
    logy          = kwargs.get('logy',         False            )
    ymargin       = kwargs.get('ymargin',      None             ) or (1.3 if logy else 1.2) # margin between hist maximum and plot's top
    logyrange     = kwargs.get('logyrange',    None             ) or 3 # log(y) range from hist maximum to ymin
    negativey     = kwargs.get('negativey',    True             ) # allow negative y values
    xtitle        = kwargs.get('xtitle',       frame.GetTitle() )
    ytitle        = kwargs.get('ytitle',       None             )
    latex         = kwargs.get('latex',        True             ) # automatically format strings as LaTeX
    grid          = kwargs.get('grid',         False            )
    ycenter       = kwargs.get('center',       False            )
    nxdivisions   = kwargs.get('nxdiv',        510              )
    nydivisions   = kwargs.get('nydiv',        510              )
    main          = kwargs.get('main',         not lower        ) # main panel of ratio plot
    lower         = kwargs.get('lower',        lower            )
    scale         = 600./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    yscale        = 1.27/scale*gPad.GetLeftMargin()/_lmargin # ytitleoffset
    xtitlesize    = kwargs.get('xtitlesize',   _tsize           )*scale
    ytitlesize    = kwargs.get('ytitlesize',   _tsize           )*scale
    xlabelsize    = kwargs.get('xlabelsize',   _lsize           )*scale
    ylabelsize    = kwargs.get('ylabelsize',   _lsize           )*scale
    ytitleoffset  = kwargs.get('ytitleoffset', 1.0              )*yscale
    xtitleoffset  = kwargs.get('xtitleoffset', 1.0              )*1.00
    xlabeloffset  = kwargs.get('xlabeloffset', -0.008*scale if logx else 0.007 )
    if main:
      xtitlesize  = 0.0
      xlabelsize  = 0.0
    if latex:
      xtitle      = makelatex(xtitle)
    LOG.verb("Plot.setaxes: Binning (%s,%.1f,%.1f)"%(nbins,xmin,xmax),verbosity,2)
    if verbosity>=3:
      print "Plot.setaxes: main=%r, lower=%r, grid=%r, latex=%r"%(main,lower,grid,latex)
      print "Plot.setaxes: logx=%r, logy=%r, ycenter=%r, intbins=%r"%(logx,logy,ycenter,intbins)
      print "Plot.setaxes: nxdiv=%s, nydiv=%s"%(nxdivisions,nydivisions)
      print "Plot.setaxes: lmargin=%.5g, _lmargin=%.5g"%(gPad.GetLeftMargin(),_lmargin)
      print "Plot.setaxes: scale=%s, yscale=%s"%(scale,yscale)
      print "Plot.setaxes: xtitlesize=%.5g, ytitlesize=%.5g"%(xtitlesize,ytitlesize)
      print "Plot.setaxes: xlabelsize=%.5g, ylabelsize=%.5g"%(xlabelsize,ylabelsize)
      print "Plot.setaxes: xtitleoffset=%.5g, ytitleoffset=%.5g, xlabeloffset=%.5g"%(xtitleoffset,ytitleoffset,xlabeloffset)
    
    if ratiorange:
      ymin, ymax  = 1-ratiorange, 1+ratiorange
    if intbins and nbins<15 and int(xmin)==xmin and int(xmax)==xmax and binwidth==1:
      LOG.verb("Plot.setaxes: Setting integer binning for (%r,%s,%d,%d)!"%(xtitle,nbins,xmin,xmax),verbosity,1)
      binlabels   = [str(i) for i in range(int(xmin),int(xmax)+1)]
      xlabelsize   *= 1.6
      xlabeloffset *= 0.88*scale
    if logy:
      ylabelsize   *= 1.08
    if logx:
      xlabelsize   *= 1.08
    if binlabels:
      nxdivisions = 15
    
    # GET HIST MAX
    hmaxs = [ ]
    hmins = [ 0 ]
    if isinstance(frame,THStack):
      hmaxs.append(frame.GetMaximum())
      #frame = frame.GetStack().Last()
      for hist in hists:
        hmaxs.append(getTGraphYRange(hist)[1] if isinstance(hist,TGraph) else hist.GetMaximum())
    else:
      for hist in hists:
        ymin1, ymax1 = getTGraphYRange(hist) if isinstance(hist,TGraph) else hist.GetMinimum(), hist.GetMaximum()
        if negativey:
          hmins.append(ymin1)
        hmaxs.append(ymax1)
      if ymin==None:
        ymin = min(hmins)*(1.1 if ymin>0 else 0.9)
    hmax = max(hmaxs)
    hmin = min(hmins)
    
    # SET AXES RANGES
    if ymin==None:
      ymin = 0
    if logy:
      if not ymin or ymin<=0: # avoid zero or negative ymin for log plots
        ymin = 10**(magnitude(hmax)-logyrange) #max(0.1,10**(magnitude(ymax)-3))
        frame.SetMinimum(ymin)
        LOG.verb("Plot.setaxes: logy=%s, hmax=%6.6g, magnitude(hmax)=%s, logyrange=%s, ymin=%.6g"%(
                                logy,hmax,magnitude(hmax),logyrange,ymin),verbosity,2)
      if ymax==None:
        if hmax>ymin>0:
          span = abs(log10(hmax/ymin))*ymargin
          ymax = ymin*(10**span)
          LOG.verb("Plot.setaxes: log10(hmax/ymin)=%6.6g, span=%6.6g, ymax=%.6g"%(log10(hmax/ymin),span,ymax),verbosity,2)
        else:
          ymax = hmax*ymargin
      gPad.Update(); gPad.SetLogy()
    elif ymax==None:
      ymax = hmax*ymargin
    if logx:
      if not xmin: xmin = 0.1
      xmax *= 0.9999999999999
      gPad.Update(); gPad.SetLogx()
    if grid:
      gPad.SetGrid()
    #frame.GetXaxis().SetLimits(xmin,xmax)
    frame.GetXaxis().SetRangeUser(xmin,xmax)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    
    if ytitle==None:
      #ytitle = "Events"
      if "multiplicity" in xtitle.lower():
        ytitle = "Events"
      elif hmax<1.:
        ytitle = "A.U."
      else:
        for hist in hists:
          if isinstance(hist,TH1) and hist.GetName()!='hframe':
            hist0 = hist; break # default frame might have wrong binning
        else:
          hist0 = frame
        binwidth  = hist0.GetXaxis().GetBinWidth(0)
        binwidstr = ("%.3f"%binwidth).rstrip('0').rstrip('.')
        units     = re.findall(r' [\[(](.+)[)\]]',xtitle) #+ re.findall(r' (.+)',xtitle)
        if hist0.GetXaxis().IsVariableBinSize():
          if units:
            ytitle = "Events / "+units[-1]
          else:
            ytitle = "Events / bin size"
        elif units:
          if binwidth!=1:
            ytitle = "Events / %s %s"%(binwidstr,units[-1])
          else:
            ytitle = "Events / "+units[-1]
        elif binwidth!=1:
          ytitle = "Events / "+binwidstr
        else:
          ytitle = "Events"
        LOG.verb("Plot.setaxes: ytitle=%r, units=%s, binwidth=%s, binwidstr=%r"%(ytitle,units,binwidth,binwidstr),verbosity,2)
    
    # alphanumerical bin labels
    if binlabels:
      if len(binlabels)<nbins:
        LOG.warning("Plot.setaxes: len(binlabels)=%d < %d=nbins"%(len(binlabels),nbins))
      for i, binlabel in zip(range(1,nbins+1),binlabels):
        frame.GetXaxis().SetBinLabel(i,binlabel)
      if labeloption: # https://root.cern.ch/doc/master/classTAxis.html#a05dd3c5b4c3a1e32213544e35a33597c
        frame.GetXaxis().LabelsOption(labeloption) # 'h'=horizontal, 'v'=vertical
    
    # X axis
    frame.GetXaxis().SetTitleSize(xtitlesize)
    frame.GetXaxis().SetTitleOffset(xtitleoffset)
    frame.GetXaxis().SetLabelSize(xlabelsize)
    frame.GetXaxis().SetLabelOffset(xlabeloffset)
    frame.GetXaxis().SetNdivisions(nxdivisions)
    frame.GetXaxis().SetTitle(xtitle)
    
    # Y axis
    if ymax>=1e4:
      ylabelsize *= 0.95
    if ycenter:
      frame.GetYaxis().CenterTitle(True)
    frame.GetYaxis().SetTitleSize(ytitlesize)
    frame.GetYaxis().SetTitleOffset(ytitleoffset)
    frame.GetYaxis().SetLabelSize(ylabelsize)
    frame.GetYaxis().SetNdivisions(nydivisions)
    frame.GetYaxis().SetTitle(ytitle)
    gPad.RedrawAxis()
    gPad.Update()
    
    if verbosity>=1:
      print ">>> Plot.setaxes: xtitle=%r, [hmin,hmax] = [%.6g,%.6g], [xmin,xmax] = [%.6g,%.6g], [ymin,ymax] = [%.6g,%.6g]"%(
                               xtitle,hmin,hmax,xmin,xmax,ymin,ymax)
    elif verbosity>=2:
      print ">>> Plot.setaxes: frame=%s"%(frame)
      print ">>> Plot.setaxes: hists=%s"%(hists)
      print ">>> Plot.setaxes: [hmin,hmax] = [%.6g,%.6g], [xmin,xmax] = [%.6g,%.6g], [ymin,ymax] = [%.6g,%.6g]"%(hmin,hmax,xmin,xmax,ymin,ymax)
      print ">>> Plot.setaxes: xtitlesize=%4.4g, xlabelsize=%4.4g, xtitleoffset=%4.4g, xtitle=%r"%(xtitlesize,xlabelsize,xtitleoffset,xtitle)
      print ">>> Plot.setaxes: ytitlesize=%4.4g, ylabelsize=%4.4g, ytitleoffset=%4.4g, ytitle=%r"%(ytitlesize,ylabelsize,ytitleoffset,ytitle)
      print ">>> Plot.setaxes: scale=%4.4g, nxdivisions=%s, nydivisions=%s, ymargin=%.3f, logyrange=%.3f"%(scale,nxdivisions,nydivisions,ymargin,logyrange)
    if main or not lower:
      #if any(a!=None and a!=b for a, b in [(self.xmin,xmin),(self.xmax,xmax)]):
      #  LOG.warning("Plot.setaxes: x axis range changed: [xmin,xmax] = [%6.6g,%6.6g] -> [%6.6g,%6.6g]"%(
      #              self.xmin,self.xmax,xmin,xmax))
      #if any(a!=None and a!=b for a, b in [(self.ymin,ymin),(self.ymax,ymax)]):
      #  LOG.warning("Plot.setaxes: y axis range changed: [ymin,ymax] = [%6.6g,%6.6g] -> [%6.6g,%6.6g]"%(
      #              self.ymin,self.ymax,ymin,ymax))
      self.xmin, self.xmax = xmin, xmax
      self.ymin, self.ymax = ymin, ymax
    else:
      self.rmin, self.rmax = ymin, ymax
    return xmin, xmax, ymin, ymax
    
  
  def drawlegend(self,position=None,**kwargs):
    """Create and draw legend.
    Legend position can be controlled in several ways
      drawlegend(position)
      drawlegend(position=position)
    where position is a string which can contain the horizontal position, e.g.
      'left', 'center', 'right', 'L', 'C', 'R', 'x=0.3', ...
    where 'x' is the position (between 0 an 1) of the left side in the frame.
    The position string can also contain the vertical position as e.g.
      'top', 'middle', 'bottom', 'T', 'M', 'B', 'y=0.3', ...
    where 'y' is the position (between 0 an 1) of the top side in the frame.
    Instead of the strings, the exact legend coordinates can be controlled with
    the keywords x1, x2, y1 and y2, or, x1, y1, width and height:
      drawlegend(x1=0.2,width=0.4)
      drawlegend(x1=0.2,width=0.4,y1=0.9,height=0.4)
      drawlegend(x1=0.2,x2=0.6,y1=0.9,y2=0.4)
    These floats are normalized to the axis frame, ignoring the canvas margins:
    x=0 is the left, x=1 is the right, y=0 is the bottom and y=1 is the top side.
    Values less than 0, or larger than 1, will put the legend outside the frame.
    """
    #if not ratio:
    #  tsize *= 0.80
    #  signaltsize *= 0.80
    verbosity   = LOG.getverbosity(self,kwargs)
    hists       = self.hists
    errstyle    = 'lep' if gStyle.GetErrorX() else 'ep'
    entries     = kwargs.get('entries',     [ ]            )
    bands       = kwargs.get('band',        [self.errband] ) # error bands
    bands       = ensurelist(bands,nonzero=True)
    bandentries = kwargs.get('bandentries', [ ]            )
    title       = kwargs.get('header',      None           )
    title       = kwargs.get('title',       title          ) # legend header/title
    latex       = kwargs.get('latex',       True           ) # automatically format strings as LaTeX
    style       = kwargs.get('style',       None           )
    style0      = kwargs.get('style0',      None           ) # style of first histogram
    errstyle    = kwargs.get('errstyle',    errstyle       ) # style for an error point
    styles      = kwargs.get('styles',      [ ]            )
    position    = kwargs.get('pos',         position       ) # legend position
    position    = kwargs.get('position',    position       ) or self.position
    option      = kwargs.get('option',      ''             )
    border      = kwargs.get('border',      False          )
    transparent = kwargs.get('transparent', True           )
    x1_user     = kwargs.get('x1',          None           ) # legend left side
    x2_user     = kwargs.get('x2',          None           ) # legend right side
    y1_user     = kwargs.get('y1',          None           ) # legend top side
    y2_user     = kwargs.get('y2',          None           ) # legend bottom side
    width       = kwargs.get('width',       -1             ) # legend width
    height      = kwargs.get('height',      -1             ) # legend height
    tsize       = kwargs.get('tsize',       _lsize         ) # text size
    twidth      = kwargs.get('twidth',      None           ) or 1 # scalefactor for legend width
    theight     = kwargs.get('theight',     None           ) or 1 # scalefactor for legend height
    texts       = kwargs.get('text',        [ ]            ) # extra text below legend
    ncols       = kwargs.get('ncol',        self.ncols     )
    ncols       = kwargs.get('ncols',       ncols          ) or 1 # number of legend columns
    colsep      = kwargs.get('colsep',      0.06           ) # seperation between legend columns
    bold        = kwargs.get('bold',        True           ) # bold legend header
    panel       = kwargs.get('panel',       1              ) # panel (top=1, bottom=2)
    texts       = ensurelist(texts,nonzero=True)
    entries     = ensurelist(entries,nonzero=False)
    bandentries = ensurelist(bandentries,nonzero=True)
    headerfont  = 62 if bold else 42
    
    # CHECK
    LOG.insist(self.canvas,"Canvas does not exist!")
    oldpad = gPad
    self.canvas.cd(panel)
    scale  = 485./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    xscale = 800./gPad.GetWw()
    tsize *= scale # text size
    
    # ENTRIES
    #if len(bandentries)==len(bands) and len(entries)>len(hists):
    #  for band, bandtitle in zip(band,bandentries):
    #    entries.insert(hists.index(band),bandtitle)
    while len(entries)<len(hists):
      entries.append(hists[len(entries)].GetTitle())
    while len(bandentries)<len(bands):
      bandentries.append(bands[len(bandentries)].GetTitle())
    hists   = hists + bands
    entries = entries + bandentries
    if latex:
      title   = maketitle(title)
      entries = [maketitle(e) for e in entries]
      texts   = [maketitle(t) for t in texts]
    maxlen  = estimatelen([title]+entries+texts)
    
    # STYLES
    if style0:
      styles[0] = style0
    while len(styles)<len(hists):
      hist = hists[len(styles)]
      if hist in bands:
        styles.append('f')
      elif style!=None:
        styles.append(style)
      elif hasattr(hist,'GetFillStyle') and hist.GetFillStyle()>0:
        styles.append('f')
      elif 'E0' in hist.GetOption() or 'E1' in hist.GetOption():
        styles.append(errstyle)
      else:
        styles.append('lp')
    
    # NUMBER of LINES
    nlines = sum([1+e.count('\n') for e in entries])
    #else:       nlines += 0.80
    if texts:   nlines += sum([1+t.count('\n') for t in texts])
    if ncols>1: nlines /= float(ncols)
    if title:   nlines += 1 + title.count('\n')
    
    # DIMENSIONS
    if width<0:  width  = twidth*xscale*max(0.22,min(0.60,0.036+0.016*maxlen))
    if height<0: height = theight*1.34*tsize*nlines
    if ncols>1:  width *= ncols/(1-colsep)
    x2 = 0.90; x1 = x2 - width
    y1 = 0.92; y2 = y1 - height
    
    # POSITION
    if position==None:
      position = ""
    position = position.replace('left','L').replace('center','C').replace('right','R').replace( #.lower()
                                'top','T').replace('middle','M').replace('bottom','B')
    if not any(c in position for c in 'TMBy'): # set default vertical
      position += 'T'
    if not any(c in position for c in 'LCRx'): # set default horizontal
      position += 'RR' if ncols>1 else 'R' # if title else 'L'
    
    if 'C'     in position:
      if   'R' in position: center = 0.57
      elif 'L' in position: center = 0.43
      else:                 center = 0.50
      x1 = center-width/2; x2 = center+width/2
    elif 'LL'  in position: x1 = 0.03; x2 = x1 + width
    elif 'L'   in position: x1 = 0.08; x2 = x1 + width
    elif 'RR'  in position: x2 = 0.97; x1 = x2 - width
    elif 'R'   in position: x2 = 0.92; x1 = x2 - width
    elif 'x='  in position:
      x1 = float(re.findall(r"x=(\d\.\d+)",position)[0])
      x2 = x1 + width
    if 'M'     in position:
      if   'T' in position: middle = 0.57
      elif 'B' in position: middle = 0.43
      else:                 middle = 0.50
      y1 = middle-height/2; y2 = middle+height/2
    elif 'TT'  in position: y2 = 0.97; y1 = y2 - height
    elif 'T'   in position: y2 = 0.92; y1 = y2 - height
    elif 'BB'  in position: y1 = 0.03; y2 = y1 + height
    elif 'B'   in position: y1 = 0.08; y2 = y1 + height
    elif 'y='  in position:
      y2 = float(re.findall(r"y=(\d\.\d+)",position)[0]);
      y1 = y2 - height
    if x1_user!=None:
      x1 = x1_user
      x2 = x1 + width if x2_user==None else x2_user
    if y1_user!=None:
      y1 = y1_user
      y2 = y1 - height if y2_user==None else y2_user
    L, R = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    X1, X2 = L+(1-L-R)*x1, L+(1-L-R)*x2 # convert frame to canvas coordinates
    Y1, Y2 = B+(1-T-B)*y1, B+(1-T-B)*y2 # convert frame to canvas coordinates
    legend = TLegend(X1,Y1,X2,Y2)
    LOG.verb("Plot.drawlegend: position=%r, height=%.3f, width=%.3f, (x1,y1,x2,y2)=(%.2f,%.2f,%.2f,%.2f), (X1,Y1,X2,Y2)=(%.2f,%.2f,%.2f,%.2f)"%(
                               position,height,width,x1,y1,x2,y2,X1,Y1,X2,Y2),verbosity,1)
    
    # MARGIN
    if ncols>=2:
      margin = 0.090/width
    else:
      margin = 0.044/width
    legend.SetMargin(margin)
    
    # STYLE
    if transparent:
      legend.SetFillStyle(0) # 0 = transparent
    else:
      legend.SetFillColor(0)
    legend.SetBorderSize(border)
    legend.SetTextSize(tsize)
    legend.SetTextFont(headerfont) # bold for title
    if ncols>1:
      legend.SetNColumns(ncols)
      legend.SetColumnSeparation(colsep)
    
    # HEADER
    if title:
      legend.SetHeader(title)
    legend.SetTextFont(42) # no bold for entries
    
    # ENTRIES
    if hists:
      for hist1, entry1, style1 in columnize(zip(hists,entries,styles),ncols):
        for entry in entry1.split('\n'):
          LOG.verb("Plot.drawlegend: Add entry (%r,%r,%r)"%(hist1,entry,style1),verbosity,2)
          legend.AddEntry(hist1,entry,style1)
          hist1, style1 = 0, ''
    for line in texts:
      legend.AddEntry(0,line,'')
    
    if verbosity>=2:
      print ">>> Plot.drawlegend: title=%r, texts=%s, latex=%s"%(title,texts,latex)
      print ">>> Plot.drawlegend: hists=%s"%(hists)
      print ">>> Plot.drawlegend: entries=%s"%(entries)
      print ">>> Plot.drawlegend: styles=%s"%(styles)
      print ">>> Plot.drawlegend: nlines=%s, len(hists)=%s, len(texts)=%s, ncols=%s, margin=%s"%(
                                  nlines,len(hists),len(texts),ncols,margin)
    
    legend.Draw(option)
    self.legends.append(legend)
    oldpad.cd()
    return legend
    
  
  def drawtext(self,*texts,**kwargs):
    """
    Draw TLaTeX text in the corner.
      drawtext(str text)
      drawtext(str text, str text, ...)
      drawtext(list texts)
    Text position can be controlled in several ways
      drawlegend(text,position=position)
    where position is a string which can contain the horizontal position, e.g.
      'left', 'center', 'right', 'L', 'C', or 'R'
    The position string can also contain the vertical position as e.g.
      'top', 'middle', 'bottom', 'T', 'M', or 'B'
    Instead of the strings, the exact coordinates can be controlled with
    the keywords x and y:
      drawtext(x=0.2,y=0.8)
    These floats are normalized to the axis frame, ignoring the canvas margins:
    x=0 is the left, x=1 is the right, y=0 is the bottom and y=1 is the top side.
    Values less than 0, or larger than 1, will put the text outside the frame.
    """
    verbosity  = LOG.getverbosity(self,kwargs)
    position   = kwargs.get('pos',      None )
    position   = kwargs.get('position', position  ) or 'topleft' #.lower()
    tsize      = kwargs.get('size',     _lsize    ) # text size
    tsize      = kwargs.get('tsize',    tsize     ) # text size
    theight    = kwargs.get('theight',  None      ) or 1
    bold       = kwargs.get('bold',     False     ) # bold text
    dolatex    = kwargs.get('latex',    True      ) # automatically format strings as LaTeX
    xuser      = kwargs.get('x',        None      ) # horizontal position
    yuser      = kwargs.get('y',        None      ) # vertical position
    ndc        = kwargs.get('ndc',      True      ) # normalized coordinates
    align_user = kwargs.get('align',    None      ) # text line
    panel      = kwargs.get('panel',    1         ) # panel (top=1, bottom=2)
    texts      = unwraplistargs(texts)
    if not any(t!="" for t in texts):
      return None
    
    # CHECK
    LOG.insist(self.canvas,"Canvas does not exist!")
    self.canvas.cd(panel)
    scale  = 485./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    tsize *= scale # text size
    
    # POSITION
    font  = 62 if bold else 42
    align = 13 # 10*horiz. + vert.: https://root.cern.ch/doc/master/classTAttText.html#T1
    position = position.replace('left','L').replace('center','C').replace('right','R').replace( #.lower()
                                'top','T').replace('middle','M').replace('bottom','B')
    if 'R' in position:
      x, align = 0.95, 30 # right
    if 'C' in position:
      x, align = 0.50, 20 # center
    else:
      x, align = 0.05, 10 # left
    if 'B' in position:
      y = 0.05; align += 1 # bottom
    if 'M' in position:
      y = 0.50; align += 2 # middle
    else:
      y = 0.95; align += 3 # top
    if 'x='  in position:
      x = float(re.findall(r"x=(\d\.\d+)",position)[0])
    if 'y='  in position:
      y = float(re.findall(r"y=(\d\.\d+)",position)[0])
    if xuser!=None: x = xuser
    if yuser!=None: y = yuser
    if align_user!=None: align = align_user
    L, R  = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B  = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    if ndc:
      x = L+(1-L-R)*x # convert frame to canvas coordinates
      y = B+(1-T-B)*y # convert frame to canvas coordinates
    
    # LATEX
    latex = TLatex()
    latex.SetTextSize(tsize)
    latex.SetTextAlign(align)
    latex.SetTextFont(font)
    #latex.SetTextColor(kRed)
    latex.SetNDC(ndc)
    for i, line in enumerate(texts):
      if dolatex:
        line = maketitle(line)
      yline = y-i*theight*1.2*tsize
      latex.DrawLatex(x,yline,line)
      LOG.verb("Plot.drawcornertext: i=%d, x=%.2f, y=%.2f, text=%r"%(i,x,yline,line),verbosity,2)
    self.texts.append(latex)
    
    return latex
    
  
  def drawline(self,x1,y1,x2,y2,color=kBlack,style=kSolid,**kwargs):
    """Draw line on canvas. If it already exists, draw now on top,
    else draw later in Plot.draw on bottom."""
    pad  = kwargs.get('pad', 1 ) # 1: main, 2: ratio
    line = TGraph(2) #TLine(xmin,1,xmax,1)
    line.SetPoint(0,x1,y1)
    line.SetPoint(1,x2,y2)
    line.SetLineColor(color)
    line.SetLineStyle(style)
    line.pad = pad
    if self.canvas:
      oldpad = gPad
      self.canvas.cd(pad)
      line.Draw("LSAME")
      oldpad.cd()
    self.lines.append(line)
    return line
    
  
  def drawbins(self,bins,text=True,y=0.96,**kwargs):
    """Divide xaxis into bins with extra lines, e.g. for unrolled 2D plots."""
    verbosity = LOG.getverbosity(self,kwargs)
    title = kwargs.get('title',       ""    )
    size  = kwargs.get('size',        0.025 )
    align = kwargs.get('align',       23    )
    axis  = kwargs.get('axis',        'x'   )
    addof = kwargs.get('addoverflow', False ) # last bin is infinity
    xmin, xmax = self.xmin, self.xmax
    if isinstance(bins,Variable):
      nbins = bins.nbins
    elif islist(bins):
      nbins = len(bins)-1
    else:
      text  = False
      nbins = bins
    for ip in [1,2]:
      if ip==2 and not self.ratio: continue
      ymin, ymax = (self.ymin, self.ymax) if ip==1 else (self.rmin, self.rmax)
      for i in range(0,nbins):
        if i>=1:
          if axis=='x':
            x = xmin + (xmax-xmin)*i/nbins
            coords = (x,ymin,x,ymax)
          else:
            y = ymin + (ymax-ymin)*i/nbins
            coords = (xmin,y,xmax,y)
          LOG.verb("Plot.drawbins: coords=%r"%(coords,),verbosity,2)
          self.drawline(*coords,color=kRed,style=kDashed,pad=ip)
        if text and ip==1:
          pad = self.canvas.GetPad(ip) if self.ratio else self.canvas
          if axis=='x':
            logy = pad.GetLogy()>0
            x = xmin + (xmax-xmin)*(i+0.5)/nbins
            y_ = scalevec(ymin,ymax,y,log=logy)
          else:
            logx = pad.GetLogx()>0
            x = scalevec(xmin,xmax,y,log=logx)
            y_ = ymin + (ymax-ymin)*(i+0.5)/nbins
          if isinstance(bins,Variable):
            y1, y2 = bins.getedge(i), bins.getedge(i+1) # edges mass bin
          else:
            y1, y2 = bins[i], bins[i+1] # edges mass bin
          if addof and i==nbins-1:
            btext = "[%d,#infty]"%(y1) # mass bin text
          else:
            btext = "[%d,%d]"%(y1,y2) # mass bin text
          if isinstance(text,str) and i==0:
            btext = text+" #in "+btext
          LOG.verb("Plot.drawbins: text=%r, (x,y)=(%s,%s)"%(btext,x,y),verbosity,2)
          self.drawtext(btext,x=x,y=y_,ndc=False,tsize=size,align=align)
    
  
  def setlinestyle(self,hists,**kwargs):
    """Set the line style for a list of histograms."""
    verbosity    = LOG.getverbosity(self,kwargs)
    pair         = kwargs.get('pair',         False  )
    triple       = kwargs.get('triple',       False  )
    colors       = kwargs.get('color',        None   )
    colors       = kwargs.get('colors',       colors ) or self.lcolors
    style        = kwargs.get('style',        True   )
    styles       = style if islist(style) else None
    styles       = kwargs.get('styles',       styles ) or self.lstyles
    width        = kwargs.get('width',        2      )
    offset       = kwargs.get('offset',       0      )
    mstyle       = kwargs.get('mstyle',       None   )
    styles       = ensurelist(styles)
    LOG.verb("Plot.setlinestyle: width=%s, colors=%s, styles=%s"%(width,colors,styles),verbosity,2)
    if mstyle==None:
      mstyle = triple or pair
    for i, hist in enumerate(hists):
      hist.SetFillStyle(0)
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
    hists   = unwraplistargs(hists)
    reset   = kwargs.get('reset',  False ) # only set if not kBlack or kWhite
    line    = kwargs.get('line',   True  )
    fcolors = kwargs.get('colors', None  ) or self.fcolors
    icol    = 0
    for hist in hists:
      #print hist.GetFillColor()
      if not reset and hist.GetFillColor() not in [kBlack,kWhite]:
        continue
      #color = getColor(hist.GetName() )
      color = fcolors[icol%len(fcolors)]
      icol += 1
      hist.SetFillColor(color)
      if line:
        hist.SetLineColor(kBlack)
    
  
