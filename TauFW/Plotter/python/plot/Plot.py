# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
# Description: Class to automatically make CMS plot comparing histograms.
import os, re
#import ctypes # for passing by reference
from TauFW.common.tools.utils import ensurelist, islist, isnumber, repkey
from TauFW.common.tools.math import log10, magnitude, columnize, scalevec, ceil
from TauFW.Plotter.plot.utils import *
from TauFW.Plotter.plot.string import makelatex, maketitle, makehistname, estimatelen
from TauFW.Plotter.plot.Variable import Variable, Var
from TauFW.Plotter.plot.Ratio import Ratio
import ROOT
from ROOT import gDirectory, gROOT, gPad, gStyle, TCanvas, TH1, TH1D, THStack, TGraph, TLine,\
                 TLegend, TGaxis, TLatex, TBox, TColor,\
                 kBlack, kGray, kWhite, kRed, kBlue, kGreen, kYellow, kAzure, kCyan, kMagenta,\
                 kOrange, kPink, kSpring, kTeal, kViolet, kSolid, kDashed, kDotted
gROOT.SetBatch(True)
#gStyle.SetEndErrorSize(0)
#whiteTransparent  = TColor(4000, 0.9, 0.9, 0.9, "kWhiteTransparent", 0.5)
#kWhiteTransparent = 4000

# CMS style
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
_mstyles = [ 8 ]
_lmargin = 0.148 # default left margin used in Plot.setcanvas, Plot.setaxes


class Plot(object):
  """Class to automatically make CMS plot comparing histograms."""
  
  def __init__(self, *args, **kwargs):
    """
    Initialize with list of histograms:
      Plot(hists)
      Plot(hist1,hist2,...)
    or with a variable (string or Variable object) as well:
      Plot(variable,hists)
      Plot(variable,hist1,hist2,...)
    """
    self.verbosity = LOG.getverbosity(kwargs)
    
    # PARSE ARGUMENTS: variable & (list of) histogram(s)
    variable   = None
    hists      = None
    vargs      = [ ] # string / Variable arguments
    hargs      = [ ] # other arguments
    for arg in args: # sort arguments by type
      if isinstance(arg,(str,Variable)):
        if variable==None:
          variable = arg
        else: # expect at most one string/Variable
          LOG.warn("Plot.__init__: Got extra, unrecognized: %r... Ignoring..."%(arg,))
      else: # assume histogram or list of histograms
        hargs.append(arg)
    if len(hargs)==1 and islist(hargs[0]):
      hargs = hargs[0] # list of histograms
    if len(hargs)==0:
      LOG.throw(IOError,"Plot.__init__: Found no input histograms... Need at least 1. Got: %r"%(args,))
    elif len(hargs)>=1 and all(isinstance(h,(TH1,TGraph)) for h in hargs):
      hists = hargs[:] # list of histograms
    else: # unrecognized arguments
      LOG.throw(IOError,"Plot.__init__: Wrong input %s"%(args,))
    ###if any(not h or not isinstance(h,(TH1,TGraph)) for h in hists) or not hists:
    ###  LOG.throw(IOError,"Plot.__init__: Did not recognize histogram in input: %s"%(args,))
    if kwargs.get('clone',False):
      hists    = [h.Clone(h.GetName()+"_clone_Plot%d"%i) for i, h in enumerate(hists)]
    self.hists = hists
    self.frame = kwargs.get('frame', None ) # only store if specified by user
    
    # OTHER SETTINGS
    frame      = self.frame or self.hists[0] # use local frame to set defaults
    binlabels  = frame.GetXaxis().GetLabels()
    binlabels  = [str(s) for s in binlabels] if binlabels else None
    if isinstance(variable,Variable):
      self.variable   = variable
      self.hasvarbins = variable.dividebins
      self.name       = kwargs.get('name',       variable.filename   )
      self.xtitle     = kwargs.get('xtitle',     variable.title      )
      self.xmin       = kwargs.get('xmin',       variable.xmin       )
      self.xmax       = kwargs.get('xmax',       variable.xmax       )
      self.ymin       = kwargs.get('ymin',       variable.ymin       )
      self.ymax       = kwargs.get('ymax',       variable.ymax       )
      self.rmin       = kwargs.get('rmin',       variable.rmin       ) # ratio ymin
      self.rmax       = kwargs.get('rmax',       variable.rmax       ) # ratio ymax
      self.ratiorange = kwargs.get('rrange',     variable.ratiorange )
      self.binlabels  = kwargs.get('binlabels',  variable.binlabels or binlabels )
      self.logx       = kwargs.get('logx',       variable.logx       )
      self.logy       = kwargs.get('logy',       variable.logy       )
      self.ymargin    = kwargs.get('ymargin',    variable.ymargin    )
      self.logyrange  = kwargs.get('logyrange',  variable.logyrange  )
      self.position   = kwargs.get('position',   variable.position   )
      self.ncols      = kwargs.get('ncols',      variable.ncols      )
      self.latex      = kwargs.get('latex',      False               ) # already done by Variable.__init__
      self.dividebins = kwargs.get('dividebins', self.hasvarbins     ) # divide each histogram bins by it bin size
    else:
      if isinstance(frame,TGraph) and not ('xmin' in kwargs or 'xmax' in kwargs):
        xmin, xmax = getTGraphRange(frame,axis='x',verb=self.verbosity-2)
      else:
        xmin, xmax = frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax() 
      self.variable   = variable or frame.GetXaxis().GetTitle()
      self.hasvarbins = frame.GetXaxis().IsVariableBinSize()
      self.name       = kwargs.get('name',       None                )
      self.xtitle     = kwargs.get('xtitle',     self.variable       )
      self.xmin       = kwargs.get('xmin',       xmin                )
      self.xmax       = kwargs.get('xmax',       xmax                )
      self.ymin       = kwargs.get('ymin',       None                )
      self.ymax       = kwargs.get('ymax',       None                )
      self.rmin       = kwargs.get('rmin',       None                ) # ratio ymin
      self.rmax       = kwargs.get('rmax',       None                ) # ratio ymax
      self.ratiorange = kwargs.get('rrange',     None                )
      self.binlabels  = kwargs.get('binlabels',  binlabels           )
      self.logx       = kwargs.get('logx',       False               )
      self.logy       = kwargs.get('logy',       False               )
      self.ymargin    = kwargs.get('ymargin',    None                )
      self.logyrange  = kwargs.get('logyrange',  None                )
      self.position   = kwargs.get('position',   ""                  )
      self.ncols      = kwargs.get('ncols',      None                )
      self.latex      = kwargs.get('latex',      True                )
      self.dividebins = kwargs.get('dividebins', False               ) # divide content / y values by bin size
    self.ytitle       = kwargs.get('ytitle', frame.GetYaxis().GetTitle() or None )
    self.name         = self.name or (self.hists[0].GetName() if self.hists else "noname")
    self.title        = kwargs.get('title',      None                )
    self.errband      = None
    self.ratio        = kwargs.get('ratio',      False               )
    self.append       = kwargs.get('append',     ""                  )
    self.norm         = kwargs.get('norm',       False               )
    self.lcolors      = kwargs.get('colors',     None                ) or _lcolors[:]  # line colors
    self.lcolors      = kwargs.get('lcolors',    None                ) or self.lcolors # line colors alias
    self.fcolors      = kwargs.get('fcolors',    None                ) or _fcolors[:]  # fill colors
    self.lstyles      = kwargs.get('lstyles',    None                ) or _lstyles[:]  # line styles
    self.mstyles      = kwargs.get('mstyles',    None                ) #or _mstyles[:]  # marker styles
    self.canvas       = None
    self.legends      = [ ]
    self.errbands     = [ ]
    self.texts        = [ ] # to save TLatex objects made by drawtext
    self.lines        = [ ]
    self.boxes        = [ ]
    self.garbage      = [ ]
    
  
  def draw(self,*args,**kwargs):
    """Central method of Plot class: make plot with canvas, axis, error, ratio..."""
    # https://root.cern.ch/doc/master/classTHStack.html
    # https://root.cern.ch/doc/master/classTHistPainter.html#HP01e
    verbosity    = LOG.getverbosity(self,kwargs)
    xtitle       = (args[0] if args else self.xtitle) or ""
    cwidth       = kwargs.get('width',        None            ) # canvas width
    cheight      = kwargs.get('height',       None            ) # canvas height
    square       = kwargs.get('square',       False           ) # square canvas
    lmargin      = kwargs.get('lmargin',      1.              ) # canvas left margin
    rmargin      = kwargs.get('rmargin',      1.              ) # canvas righ margin
    tmargin      = kwargs.get('tmargin',      1.              ) # canvas bottom margin
    bmargin      = kwargs.get('bmargin',      1.              ) # canvas top margin
    norm         = kwargs.get('norm',         self.norm       ) # normalize all histograms
    xtitle       = kwargs.get('xtitle',       xtitle          ) # x axis title
    ytitle       = kwargs.get('ytitle',       self.ytitle     ) # y axis title (if None, automatically set by Plot.setaxis)
    rtitle       = kwargs.get('rtitle',       "Ratio"         ) # y axis title of ratio panel
    latex        = kwargs.get('latex',        self.latex      ) # automatically format strings as LaTeX with makelatex
    xtitleoffset = kwargs.get('xtitleoffset', 1.0             )*bmargin
    ytitleoffset = kwargs.get('ytitleoffset', 1.0             )
    rtitleoffset = kwargs.get('rtitleoffset', 1.0             )
    tsize        = kwargs.get('tsize',        _tsize          ) # text size for axis title
    xtitlesize   = kwargs.get('xtitlesize',   tsize           ) # x title size
    ytitlesize   = kwargs.get('ytitlesize',   tsize           ) # y title size
    rtitlesize   = kwargs.get('rtitlesize',   tsize           ) # ratio title size
    labelsize    = kwargs.get('labelsize',    _lsize          ) # label size
    xlabelsize   = kwargs.get('xlabelsize',   labelsize       ) # x label size
    ylabelsize   = kwargs.get('ylabelsize',   labelsize       ) # y label size
    binlabels    = kwargs.get('binlabels',    self.binlabels  ) # list of alphanumeric bin labels
    labeloption  = kwargs.get('labeloption',  None            ) # 'h'=horizontal, 'v'=vertical
    ycenter      = kwargs.get('ycenter',      False           ) # center y title
    xmin         = kwargs.get('xmin',         self.xmin       )
    xmax         = kwargs.get('xmax',         self.xmax       )
    ymin         = kwargs.get('ymin',         self.ymin       )
    ymax         = kwargs.get('ymax',         self.ymax       )
    rmin         = kwargs.get('rmin',         self.rmin       ) # ratio ymin
    if not rmin and rmin!=0:
      rmin = 0.45 # default
    rmax         = kwargs.get('rmax',         self.rmax       ) or 1.55 # ratio ymax
    ratiorange   = kwargs.get('rrange',       self.ratiorange ) # ratio range around 1.0
    ratio        = kwargs.get('ratio',        self.ratio      ) # make ratio plot
    lowerpanels  = int(ratio) if isinstance(ratio,bool) else 1 if isinstance(ratio,int) else False
    lowerpanels  = kwargs.get('lowerpanels',  lowerpanels     ) # number of lower panels (default 1 if ratio is True or int)
    denom        = ratio if not isinstance(ratio,bool) and isinstance(ratio,int) and (ratio!=0) else -1 # assume last histogram is denominator
    denom        = kwargs.get('den',          denom           ) # index of common denominator histogram in ratio plot (count from 1)
    denom        = kwargs.get('denom',        denom           ) # alias
    num          = kwargs.get('num',          None            ) # index of common numerator histogram in ratio plot (count from 1)
    rhists       = kwargs.get('rhists',       self.hists      ) # custom histogram argument for ratio plot
    iband        = denom if isinstance(denom,int) else -1
    nxdiv        = kwargs.get('nxdiv',        None            ) # tick divisions of x axis
    nydiv        = kwargs.get('nydiv',        None            ) # tick divisions of y axis
    nrdiv        = kwargs.get('nrdiv',        506             ) # tick divisions of y axis of ratio panel
    logx         = kwargs.get('logx',         self.logx       )
    logy         = kwargs.get('logy',         self.logy       )
    ymargin      = kwargs.get('ymarg',        self.ymargin    ) # alias
    ymargin      = kwargs.get('ymargin',      ymargin         ) # margin between hist maximum and plot's top
    logyrange    = kwargs.get('logyrange',    self.logyrange  ) # log(y) range from hist maximum to ymin
    grid         = kwargs.get('grid',         True            )
    rgrid        = kwargs.get('rgrid',        grid            ) # grid for ratio panel
    tsize        = kwargs.get('tsize',        _tsize          ) # text size for axis title
    pair         = kwargs.get('pair',         False           ) # group histograms in pairs
    triple       = kwargs.get('triple',       False           ) # group histograms in triplets
    lcolors      = kwargs.get('color',        None            ) # alias
    lcolors      = kwargs.get('colors',       lcolors         ) # alias
    setcols      = kwargs.get('setcols',      True            ) # set line colors (automatically)
    lcolors      = kwargs.get('lcolors',      lcolors         ) or self.lcolors # line colors
    fcolors      = kwargs.get('fcolors',      None            ) or self.fcolors # fill colors
    lstyles      = kwargs.get('style',        None            ) # line styles
    lstyles      = kwargs.get('styles',       lstyles         ) # line styles alias
    lstyles      = kwargs.get('lstyle',       lstyles         ) # line styles alias
    lstyles      = kwargs.get('lstyles',      lstyles         ) or self.lstyles # line styles alias
    mstyles      = kwargs.get('mstyle',       None            ) # alias
    mstyles      = kwargs.get('mstyles',      mstyles         ) or self.mstyles # marker styles
    msizes       = kwargs.get('msize',        None            ) # alias
    msizes       = kwargs.get('msizes',       msizes          ) # marker style
    lwidth       = kwargs.get('lwidth',       2               ) # line width
    option       = kwargs.get('option',       'HIST'          ).upper() # draw option for every histogram
    options      = kwargs.get('options',      [ ]             ) or [ ] # list of individual draw options for each histogram
    roption      = kwargs.get('roption',      None            ) # draw option of ratio plot
    drawden      = kwargs.get('drawden',      False           ) # draw denominator in ratio plot
    errbars      = kwargs.get('errbars',      not options     ) # add error bars to histogram
    staterr      = kwargs.get('staterr',      False           ) # create stat. error band
    sysvars      = kwargs.get('sysvars',      [ ]             ) # create sys. error band from variations
    iband        = kwargs.get('iband',        iband           ) # index of histogram to make error band for (count from 1)
    errtitle     = kwargs.get('errtitle',     None            ) # title for error band
    enderrorsize = kwargs.get('enderrorsize', 2.0             ) # size of line at end of error bar
    errorX       = kwargs.get('errorX',       self.hasvarbins and not 'HIST' in option ) # horizontal error bars
    dividebins   = kwargs.get('dividebins',   self.dividebins ) # divide content / y values by bin size
    lcolors      = ensurelist(lcolors or [ ])
    fcolors      = ensurelist(fcolors or [ ])
    lstyles      = ensurelist(lstyles or [ ])
    hists        = self.hists
    self.norm    = norm
    self.ratio   = ratio
    self.lcolors = lcolors
    self.fcolors = fcolors
    self.lstyles = lstyles
    if not xmin and xmin!=0: xmin = self.xmin
    if not xmax and xmax!=0: xmax = self.xmax
    if isinstance(iband,int): # shift by 1
      if iband<0:
        iband = max(1,len(hists)+iband+1)
      iband = max(0,min(len(hists)-1,iband-1))
    if verbosity>=1:
      print(">>> Plot.draw: hists=%r, ratio=%r, norm=%r, dividebins=%r"%(hists,ratio,norm,dividebins))
      print(">>> Plot.draw: xtitle=%r, ytitle=%r, rtitle=%r"%(xtitle,ytitle,rtitle))
      print(">>> Plot.draw: xmin=%s, xmax=%s, ymin=%s, ymax=%s, rmin=%s, rmax=%s"%(xmin,xmax,ymin,ymax,rmin,rmax))
    
    # DIVIDE BY BINSIZE
    if dividebins:
      LOG.verb("Plot.draw: dividebins=%r"%(dividebins),verbosity,2)
      for i, oldhist in enumerate(hists[:]):
        newhist = dividebybinsize(oldhist,zero=True,zeroerrs=False,poisson=False,verb=verbosity)
        if oldhist!=newhist: # new hist is actually a TGraph
          LOG.verb("Plot.draw: replace %s -> %s"%(oldhist,newhist),verbosity,2)
          hists[i] = newhist
          self.garbage.append(oldhist)
      #if sysvars:
      #  histlist = sysvars.values() if isinstance(sysvars,dict) else sysvars
      #  for (histup,hist,histdown) in histlist:
      #    dividebybinsize(histup,  zero=True,zeroerrs=False,verb=verbosity-2)
      #    dividebybinsize(histdown,zero=True,zeroerrs=False,verb=verbosity-2)
      #    if hist not in hists:
      #      dividebybinsize(hist,zero=True,zeroerrs=False,verb=verbosity-2)
    
    # RESET XMIN & BINNING
    if logx and xmin==0: # reset xmin in binning if logx
      frame = self.frame or self.hists[0]
      xmin = 0.35*frame.GetXaxis().GetBinWidth(1)
      xbins = getbinning(frame,xmin,xmax,variable=True,verb=verbosity) # new binning with xmin>0
      xbins = getbinning(frame,xmin,xmax,variable=True,verb=verbosity) # new binning with xmin>0
      LOG.verb("Plot.draw: Resetting xmin=0 -> %s in binning of all histograms (logx=%r, frame=%r): xbins=%r"%(
        xmin,logx,frame,xbins),verbosity,1)
      for hist in hists:
        if hist and isinstance(hist,TH1):
          hist.SetBins(*xbins) # set xmin>0 to plot correctly with logx
      if self.frame and self.frame.GetXaxis().GetXmin()<=0.0:
        self.frame = None # use getframe below
    
    # NORMALIZE
    if norm:
      if ytitle==None:
        ytitle = "A.U."
      scale = 1.0 if isinstance(norm,bool) else norm # can be list
      normalize(hists,scale=scale)
    
    # DRAW OPTIONS
    # https://root.cern/doc/master/classTHistPainter.html#HP01a
    # https://root.cern.ch/doc/master/classTGraphPainter.html#GrP1
    setmstyle = False
    if errbars and 'E' not in option and not roption:
      roption = 'E1 HIST'
    if len(options)==0:
      for hist in hists:
        option_ = option # default option for all hists
        if isinstance(hist,TGraph):
          option_ = option_.replace('HIST','').strip() or 'PE0'
          if errbars and 'E' not in option_:
            option_ = 'E0 '+option_ # ensure error bars
        elif errbars and 'E' not in option_:
          option_ = 'E1 '+option_ #E01 # ensure error bars
        if 'P' in option_:
          setmstyle = True
        options.append(option_) # one option per hist
      if staterr and isinstance(iband,int): #and not isinstance(,TGraph):
        if isinstance(hists[iband],TGraph):
          options[iband] = options[iband].replace('E','').replace('3','') #'HIST' # 'E3'
        else:
          options[iband] = 'HIST' # 'E3'
    else: # ensure same number of options as number of hists
      while len(options)<len(hists):
        options.append(options[-1]) # copy last style
    #if not self.histsD and staterr and errbars:
    #  i = denominator-1 if denominator>0 else 0
    #  options[i] = options[i].replace('E0','')
    gStyle.SetEndErrorSize(enderrorsize) # extra perpendicular line at end of error bars ('E1')
    gStyle.SetErrorX(0.5*float(errorX)) # horizontal error bars
    LOG.verb("Plot.draw: options=%r, errbars=%r, ratio=%r, denom=%r, iband=%r"%(options,errbars,ratio,denom,iband),verbosity,2)
    LOG.verb("Plot.draw: enderrorsize=%r, errorX=%r"%(enderrorsize,errorX),verbosity,2)
    
    # CANVAS
    self.canvas = self.setcanvas(square=square,lower=lowerpanels,width=cwidth,height=cheight,
                                 lmargin=lmargin,rmargin=rmargin,tmargin=tmargin,bmargin=bmargin)
    
    # STYLE
    if setmstyle and not mstyles and not isinstance(mstyles,bool): # match marker styles
      mstyles = [ ]
      for hist, option_ in zip(hists,options):
        if isinstance(hist,TGraph):
          opt = 'data' if 'P' in option_ else 'hist' if 'E' in option_ else 'none'
          mstyles.append(opt)
        elif 'E1' in option_ and enderrorsize>0:
          mstyles.append('hist') # ensure extra perpendicular line at end of error bars ('E1')
        else:
          mstyles.append('none') # no marker at all
    if not (isinstance(lstyles,bool) and lstyles==False):
      self.setlinestyle(hists,colors=lcolors,styles=lstyles,mstyle=mstyles,width=lwidth,pair=pair,triple=triple,setcols=setcols)
    if mstyles:
      self.setmarkerstyle(*hists,mstyle=mstyles,msizes=msizes)
    
    # DRAW FRAME
    mainpad = self.canvas.cd(1)
    if not self.frame: # if not given by user
      self.frame = getframe(mainpad,hists[0],xmin,xmax,variable=False,verb=verbosity-1)
      self.frame.Draw('AXIS')
    elif isinstance(self.frame,TGraph):
      self.frame = getframe(mainpad,self.frame,xmin,xmax,variable=False,verb=verbosity-1)
      self.frame.Draw() # 'AXIS' breaks grid in combination with TGraph for some reason !?
    else: #if frame!=hists[0]:
      self.frame.Draw('AXIS')
    
    # DRAW LINE
    for line in self.lines:
      if line.pad==1:
        line.Draw(line.option)
    for box in self.boxes:
      if box.pad==1:
        box.Draw(box.option)
    
    # DRAW HISTS
    LOG.verb("Plot.draw: frame=%r, options=%r"%(self.frame,options),verbosity,2)
    for i, (hist, option_) in enumerate(zip(hists,options)):
      if triple and i%3==2:
        option_ = 'E1'
      if 'SAME' not in option_: #i>0:
        option_ += " SAME"
      hist.Draw(option_)
      #if hasattr(hist,'SetOption'):
      hist.SetOption(option_) # for choosing default line style and legend symbol
      LOG.verb("Plot.draw: i=%s, hist=%r, option=%r"%(i,hist,option_),verbosity,2)
    
    # CMS STYLE
    if CMSStyle.lumiText:
      #mainpad = self.canvas.GetPad(1 if ratio else 0)
      CMSStyle.setCMSLumiStyle(mainpad,0,verb=verbosity-2)
    
    # ERROR BAND
    if staterr or sysvars:
      #seterrorbandstyle(hists[0],fill=False)
      errhist = iband if isinstance(iband,TH1) else hists[iband]
      LOG.verb("Plot.draw: errhist=%r"%(errhist),verbosity,2)
      self.errband = geterrorband(errhist,sysvars=sysvars,color=errhist.GetLineColor(),title=errtitle,
                                  name=makehistname("errband",self.name),verb=verbosity)
      self.errband.Draw('E2 SAME')
    
    # AXES
    drawx = not bool(ratio)
    self.setaxes(self.frame,*hists,drawx=drawx,grid=grid,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,logy=logy,logx=logx,nxdiv=nxdiv,nydiv=nydiv,
                 xtitle=xtitle,ytitle=ytitle,xtitlesize=xtitlesize,ytitlesize=ytitlesize,latex=latex,center=ycenter,logyrange=logyrange,
                 ytitleoffset=ytitleoffset,xtitleoffset=xtitleoffset,xlabelsize=xlabelsize,ylabelsize=ylabelsize,
                 dividebins=dividebins,binlabels=binlabels,labeloption=labeloption,ymargin=ymargin,verb=verbosity)
    
    # RATIO
    if ratio:
      drawx = (lowerpanels<=1)
      lines = [l for l in self.lines if l.pad==2]
      boxes = [b for b in self.boxes if b.pad==2]
      self.canvas.cd(2) # go to ratio panel
      self.ratio = Ratio(*rhists,errband=self.errband,denom=denom,num=num,drawzero=True,drawden=drawden,option=roption,verb=verbosity)
      self.ratio.draw(roption,xmin=xmin,xmax=xmax,lines=lines,boxes=boxes)
      self.setaxes(self.ratio,drawx=drawx,grid=rgrid,xmin=xmin,xmax=xmax,ymin=rmin,ymax=rmax,logx=logx,nxdiv=nxdiv,nydiv=nrdiv,
                   xtitle=xtitle,ytitle=rtitle,xtitlesize=xtitlesize,ytitlesize=rtitlesize,center=True,
                   xtitleoffset=xtitleoffset,ytitleoffset=rtitleoffset,xlabelsize=xlabelsize,ylabelsize=ylabelsize,
                   binlabels=binlabels,labeloption=labeloption,rrange=ratiorange,latex=latex,verb=verbosity)
      self.canvas.cd(1) # go back to main pad
    
    return self.canvas
    
  
  def saveas(self,*fnames,**kwargs):
    """Save plot, close canvas and delete the histograms."""
    save   = kwargs.get('save',   True  )
    close  = kwargs.get('close',  False )
    outdir = kwargs.get('outdir', ""    ) # output directory
    tag    = kwargs.get('tag',    ""    ) # extra tag for output file
    exts   = kwargs.get('ext',    [ ]   ) # list of extension [".png"]
    exts   = kwargs.get('exts',   exts  ) # alias
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
            fname = re.sub(r"\.?(png|pdf|jpg|gif|eps|tiff?|cc?|root)?$",ext,fname,count=1,flags=re.IGNORECASE)
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
      LOG.verb("Plot.close: Closing canvas...",verbosity,3)
      self.canvas.Close()
    if not keep: # do not keep histograms
      if verbosity>=3:
        hlist = ', '.join(repr(h) for h in self.hists)
        print(">>> Plot.close: Deleting histograms: %s..."%(hlist))
      for hist in self.hists:
        deletehist(hist,**kwargs)
    if self.errband:
      LOG.verb("Plot.close: Deleting error band...",verbosity,3)
      deletehist(self.errband)
    for line in self.lines:
      LOG.verb("Plot.close: Deleting line...",verbosity,3)
      deletehist(line,**kwargs)
    for hist in self.garbage:
      LOG.verb("Plot.close: Deleting garbage...",verbosity,3)
      deletehist(hist,**kwargs)
    if isinstance(self.ratio,Ratio):
      LOG.verb("Plot.close: Deleting ratio...",verbosity,3)
      self.ratio.close()
    LOG.verb("closed\n>>>",verbosity,2)
    
  
  def setcanvas(self,**kwargs):
    """Make canvas and pads for ratio plots."""
    verbosity = LOG.getverbosity(self,kwargs)
    square    = kwargs.get('square',  False  ) # square (main panel)
    lower     = kwargs.get('lower',   False  ) # include lower panel (boolean, integer, list/tuple of floats)
    splits    = 1./3. if lower in [1,True] else [0.20,0.28] if lower==2 else lower
    splits    = kwargs.get('split',   splits ) or splits # height of lower panel as fraction of canvas height
    if lower: # lower panel
      splits   = ensurelist(splits) # list of splits, e.g. [0.33] or [0.25,0.25]
      splitsum = sum(splits) # Sum of height of lower panels as total fraction of canvas height
      assert splitsum<1, "Sum of height of lower panels as total fraction of canvas height must be less than 1! Got %r"%(splits)
      height_  = (850 if square else 500)/(1.-splitsum) # default canvas height
      width_   = 850 if square else 800 # default canvas width
    else: # no lower panel
      height_  = 900 if square else 600 # default canvas height
      width_   = 900 if square else 800 # default canvas width
    width   = kwargs.get('width',   None   ) or width_  # canvas width
    height  = kwargs.get('height',  None   ) or height_ # canvas height
    wscale  = width_/float(width)   # correction factor to default margin
    hscale  = height_/float(height) # correction factor to default margin
    lmargin = kwargs.get('lmargin', 1.     )*wscale # scale left margin
    rmargin = kwargs.get('rmargin', 1.     )*wscale # scale right margin
    tmargin = kwargs.get('tmargin', 1.     )*hscale # scale top margin
    bmargin = kwargs.get('bmargin', 1.     )*hscale # scale bottom margin
    pads    = kwargs.get('pads',    [ ]    ) # pass list as reference
    if square:
      lmargin *= 1.15
      tmargin *= 0.90
      #rmargin *= 3.6
    if verbosity>=2:
      print(">>> Plot.setcanvas: square=%r, lower=%r, splits=%r"%(square,lower,splits))
      print(">>> Plot.setcanvas: width=%s, height=%s"%(width,height))
      print(">>> Plot.setcanvas: lmargin=%.5g, rmargin=%.5g, tmargin=%.5g, bmargin=%.5g"%(lmargin,rmargin,tmargin,bmargin))
    canvas = TCanvas('canvas','canvas',100,100,int(round(width)),int(round(height)))
    canvas.SetFillColor(0)
    #canvas.SetFillStyle(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameBorderMode(0)
    if lower: # add lower panel(s)
      assert len(splits)>=1
      canvas.SetMargin(0.0,0.0,0.0,0.0) # LRBT
      canvas.Divide(1+len(splits))
      mainpad = canvas.cd(1)
      mainpad.SetPad('mainpad','mainpad',0.0,sum(splits),1.0,1.0) # xlow,ylow,xup,yup
      mainpad.SetMargin(_lmargin*lmargin,0.04*rmargin,0.029,0.075*tmargin) # LRBT
      mainpad.SetFillColor(0)
      mainpad.SetFillStyle(4000) # transparant (for pdf)
      #mainpad.SetFillStyle(0)
      mainpad.SetTicks(1,1)
      mainpad.SetBorderMode(0)
      mainpad.Draw()
      for i, split in enumerate(splits): # loop over lower panels top to bottom
        assert isinstance(split,float), "Split must be float! Got: %r"%(split)
        pname = "lowerpad"+str(i+1)
        ylow, yup = sum(splits[i+1:]), sum(splits[i:])
        tmargin_ = 9.9/(height*split)
        bmargin_ = (12 if i+1<len(splits) else 87.9*bmargin)/(height*split)
        if verbosity>=2:
          print(">>> Plot.setcanvas: panel=%r, ylow=%.5g, yup=%.5g, bmargin_=%.5g, tmargin_=%.5g"%(pname,ylow,yup,bmargin_,tmargin_))
        lowpad = canvas.cd(2+i)
        lowpad.SetPad(pname,pname,0.0,ylow,1.0,yup) # xlow,ylow,xup,yup
        lowpad.SetMargin(_lmargin*lmargin,0.04*rmargin,bmargin_,tmargin_) # LRBT
        lowpad.SetFillColor(0) #lowpad.SetFillColorAlpha(0,0.0)
        lowpad.SetFillStyle(4000) # transparant (for pdf)
        lowpad.SetBorderMode(0)
        lowpad.SetTicks(1,1)
        lowpad.Draw()
      canvas.cd(1)
    else:
      canvas.SetMargin(_lmargin*lmargin,0.05*rmargin,0.145*bmargin,0.06*tmargin) # LRBT
      canvas.SetTicks(1,1)
    return canvas
    
  
  def setaxes(self, *args, **kwargs):
    """Make axis."""
    verbosity = LOG.getverbosity(self,kwargs)
    hists     = [ ]
    binning   = [ ]
    drawx     = False # lower panel (e.g. for ratio)
    for arg in args[:]:
      if hasattr(arg,'GetXaxis'):
        hists.append(arg)
      elif isinstance(arg,Ratio):
        drawx = True
        hists.append(arg.frame)
      elif isnumber(arg):
        binning.append(arg)
    if not hists:
      LOG.warn("Plot.setaxes: No objects (TH1, TGraph, ...) given in args %s to set axis..."%(args))
      return 0, 0, 100, 100
    frame         = hists[0]
    if len(binning)>=2:
      xmin, xmax  = binning[0], binning[-1]
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
    intbins       = kwargs.get('intbins',      not binlabels    ) # allow integer binning
    labeloption   = kwargs.get('labeloption',  None             ) # 'h'=horizontal, 'v'=vertical
    logx          = kwargs.get('logx',         False            )
    logy          = kwargs.get('logy',         False            )
    ymargin       = kwargs.get('ymarg',        None             ) # alias
    ymargin       = kwargs.get('ymargin',      ymargin          ) or (1.3 if logy else 1.2) # margin between hist maximum and plot's top
    logyrange     = kwargs.get('logyrange',    None             ) or 3 # log(y) range from hist maximum to ymin
    negativey     = kwargs.get('negativey',    True             ) # allow negative y values
    xtitle        = kwargs.get('xtitle',       frame.GetTitle() )
    ytitle        = kwargs.get('ytitle',       None             )
    latex         = kwargs.get('latex',        True             ) # automatically format strings as LaTeX
    grid          = kwargs.get('grid',         False            )
    ycenter       = kwargs.get('center',       False            ) # center y title
    nxdivisions   = kwargs.get('nxdiv',        None             ) or 510 # tick divisions of x axis
    nydivisions   = kwargs.get('nydiv',        None             ) or 510 # tick divisions of y axis
    dividebins    = kwargs.get('dividebins',   False            ) # divide content / y values by bin size
    drawx         = kwargs.get('drawx',        drawx            ) # draw x title and labels
    scale         = 600./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC()) # automatic scaling (e.g. for lower panel)
    yscale        = 1.27/scale*gPad.GetLeftMargin()/_lmargin # ytitleoffset
    xtitlesize    = kwargs.get('xtitlesize',   _tsize           )*scale
    ytitlesize    = kwargs.get('ytitlesize',   _tsize           )*scale
    labelsize     = kwargs.get('labelsize',    _lsize           )
    xlabelsize    = kwargs.get('xlabelsize',   labelsize        )*scale
    ylabelsize    = kwargs.get('ylabelsize',   labelsize        )*scale
    ytitleoffset  = kwargs.get('ytitleoffset', 1.0              )*yscale
    xtitleoffset  = kwargs.get('xtitleoffset', 1.0              )*1.00
    xlabeloffset  = kwargs.get('xlabeloffset', -0.008*scale if logx else 0.007 )
    ylabeloffset  = kwargs.get('ylabeloffset', 0.004*yscale if logy else 0.007 )
    if not drawx:
      xtitlesize  = 0.0
      xlabelsize  = 0.0
    if latex:
      xtitle      = makelatex(xtitle)
    LOG.verb("Plot.setaxes: frame=%r with binning (%s,%.6g,%.6g), "%(frame,nbins,xmin,xmax),verbosity,2)
    if verbosity>=3:
      print(">>> Plot.setaxes: drawx=%r, grid=%r, latex=%r"%(drawx,grid,latex))
      print(">>> Plot.setaxes: logx=%r, logy=%r, ycenter=%r, intbins=%r, nxdiv=%s, nydiv=%s"%(logx,logy,ycenter,intbins,nxdivisions,nydivisions))
      print(">>> Plot.setaxes: lmargin=%.5g, _lmargin=%.5g, scale=%s, yscale=%s"%(gPad.GetLeftMargin(),_lmargin,scale,yscale))
    
    if ratiorange:
      ymin, ymax  = 1.-ratiorange, 1.+ratiorange
    if intbins and nbins<15 and int(xmin)==xmin and int(xmax)==xmax and binwidth==1:
      LOG.verb("Plot.setaxes: Setting integer binning for (%r,%d,%.2f,%.2f)!"%(xtitle,nbins,xmin,xmax),verbosity,2)
      binlabels   = [str(i) for i in range(int(xmin),int(xmax)+1)]
      xlabelsize   *= 1.6
      xlabeloffset *= 0.88*scale
    elif binlabels:
      xlabelsize   *= 1.6 if nbins<=5 else 1.1
      xlabeloffset *= 0.88*scale
    if logy:
      ylabelsize   *= 1.08
    if logx:
      xlabelsize   *= 1.08
    if binlabels:
      nxdivisions = 15
    if verbosity>=3:
      print(">>> Plot.setaxes: xtitlesize=%.5g, ytitlesize=%.5g, xlabelsize=%.5g, ylabelsize=%.5g"%(xtitlesize,ytitlesize,xlabelsize,ylabelsize))
      print(">>> Plot.setaxes: xtitleoffset=%.5g, ytitleoffset=%.5g, xlabeloffset=%.5g, ylabeloffset=%.5g"%(xtitleoffset,ytitleoffset,xlabeloffset,ylabeloffset))
    
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
        ymin1, ymax1 = getTGraphYRange(hist) if isinstance(hist,TGraph) else (hist.GetMinimum(),hist.GetMaximum())
        if negativey:
          hmins.append(ymin1)
        hmaxs.append(ymax1)
      if ymin==None:
        ymin = min(hmins)
        ymin *= 1.1 if ymin<0 else 0.9 # add 10% margin
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
      if not xmin:
        xmin = 0.35*frame.GetXaxis().GetBinWidth(1)
      xmax *= 0.9999999999999
      gPad.Update(); gPad.SetLogx()
    if grid:
      gPad.SetGrid()
    #frame.GetXaxis().SetLimits(xmin,xmax)
    frame.GetXaxis().SetRangeUser(xmin,xmax)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    
    # SET Y AXIS TITLE
    if ytitle==None:
      #ytitle = "Events"
      if any(s in xtitle.lower() for s in ["multiplicity","number"]):
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
        units     = re.findall(r' [\[(]([^,><\]\)]+)[)\]]',xtitle) #+ re.findall(r' (.+)',xtitle)
        units     = units[-1] if units else "units" # use "unit(s)" for dimensionless variable
        # https://twiki.cern.ch/twiki/bin/viewauth/CMS/Internal/PubGuidelines#Figures_and_tables
        if dividebins:
          if units=='units':
            ytitle = "Events / unit"
          else:
            ytitle = "Events / "+units # e.g. "Events / GeV", "Events / cm"
        elif hist0.GetXaxis().IsVariableBinSize():
          ytitle = "Events / bin" # variable binning without dividing bin content by bin width
        elif units:
          if binwidth!=1:
            ytitle = "Events / %s %s"%(binwidstr,units) # e.g. "Events / 2 GeV", "Events / 0.5 cm", "Events / 0.1 units"
          elif units=='units':
            ytitle = "Events / unit"
          else:
            ytitle = "Events / "+units # e.g. "Events / GeV", "Events / cm"
        else: # should not happen, as units is always defined
          ytitle = "Events"
        LOG.verb("Plot.setaxes: ytitle=%r, units=%s, binwidth=%s, binwidstr=%r, dividebins=%r"%(
                 ytitle,units,binwidth,binwidstr,dividebins),verbosity,2)
    
    # alphanumerical bin labels
    if binlabels:
      if len(binlabels)<nbins:
        LOG.warn("Plot.setaxes: len(binlabels)=%d < %d=nbins"%(len(binlabels),nbins))
      for i, binlabel in zip(range(1,nbins+1),binlabels):
        frame.GetXaxis().SetBinLabel(i,binlabel)
      if labeloption: # https://root.cern.ch/doc/master/classTAxis.html#a05dd3c5b4c3a1e32213544e35a33597c
        frame.GetXaxis().LabelsOption(labeloption) # 'h'=horizontal, 'v'=vertical
    
    # SET X axis
    frame.GetXaxis().SetTitleSize(xtitlesize)
    frame.GetXaxis().SetTitleOffset(xtitleoffset)
    frame.GetXaxis().SetLabelSize(xlabelsize)
    frame.GetXaxis().SetLabelOffset(xlabeloffset)
    frame.GetXaxis().SetNdivisions(nxdivisions)
    frame.GetXaxis().SetTitle(xtitle)
    
    # SET Y axis
    if ymax>=1e4:
      ylabelsize *= 0.95
    if ycenter:
      frame.GetYaxis().CenterTitle(True)
    frame.GetYaxis().SetTitleSize(ytitlesize)
    frame.GetYaxis().SetTitleOffset(ytitleoffset)
    frame.GetYaxis().SetLabelOffset(ylabeloffset)
    frame.GetYaxis().SetLabelSize(ylabelsize)
    frame.GetYaxis().SetNdivisions(nydivisions)
    frame.GetYaxis().SetTitle(ytitle)
    gPad.RedrawAxis()
    gPad.Update()
    
    if verbosity>=1:
      print(">>> Plot.setaxes: xtitle=%r, [hmin,hmax] = [%.6g,%.6g], [xmin,xmax] = [%.6g,%.6g], [ymin,ymax] = [%.6g,%.6g]"%(
                               xtitle,hmin,hmax,xmin,xmax,ymin,ymax))
    elif verbosity>=2:
      print(">>> Plot.setaxes: frame=%s"%(frame))
      print(">>> Plot.setaxes: hists=%s"%(hists))
      print(">>> Plot.setaxes: [hmin,hmax] = [%.6g,%.6g], [xmin,xmax] = [%.6g,%.6g], [ymin,ymax] = [%.6g,%.6g]"%(hmin,hmax,xmin,xmax,ymin,ymax))
      print(">>> Plot.setaxes: xtitlesize=%4.4g, xlabelsize=%4.4g, xtitleoffset=%4.4g, xtitle=%r"%(xtitlesize,xlabelsize,xtitleoffset,xtitle))
      print(">>> Plot.setaxes: ytitlesize=%4.4g, ylabelsize=%4.4g, ytitleoffset=%4.4g, ytitle=%r"%(ytitlesize,ylabelsize,ytitleoffset,ytitle))
      print(">>> Plot.setaxes: scale=%4.4g, nxdivisions=%s, nydivisions=%s, ymargin=%.3f, logyrange=%.3f"%(scale,nxdivisions,nydivisions,ymargin,logyrange))
    if gPad.GetNumber()==1: # assume this is the main pad
      #if any(a!=None and a!=b for a, b in [(self.xmin,xmin),(self.xmax,xmax)]):
      #  LOG.warn("Plot.setaxes: x axis range changed: [xmin,xmax] = [%6.6g,%6.6g] -> [%6.6g,%6.6g]"%(
      #              self.xmin,self.xmax,xmin,xmax))
      #if any(a!=None and a!=b for a, b in [(self.ymin,ymin),(self.ymax,ymax)]):
      #  LOG.warn("Plot.setaxes: y axis range changed: [ymin,ymax] = [%6.6g,%6.6g] -> [%6.6g,%6.6g]"%(
      #              self.ymin,self.ymax,ymin,ymax))
      self.xmin, self.xmax = xmin, xmax
      self.ymin, self.ymax = ymin, ymax
    else:
      self.rmin, self.rmax = ymin, ymax
    return xmin, xmax, ymin, ymax
    
  
  def drawlegend(self,position=None,printmean=False,**kwargs):
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
    errstyle    = 'lep' if gStyle.GetErrorX() else 'ep'
    hists       = kwargs.get('hists',       self.hists[:]  )
    entries     = kwargs.get('entries',     [ ]            )
    reverse     = kwargs.get('reverse',     False          ) # reverse order of hists
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
    x1_user     = kwargs.get('x',           None           ) # alias
    x1_user     = kwargs.get('x1',          x1_user        ) # legend left side
    x2_user     = kwargs.get('x2',          None           ) # legend right side
    y1_user     = kwargs.get('y',           None           ) # alias
    y1_user     = kwargs.get('y1',          y1_user        ) # legend top side
    y2_user     = kwargs.get('y2',          None           ) # legend bottom side
    width       = kwargs.get('width',       -1             ) # legend width
    height      = kwargs.get('height',      -1             ) # legend height
    tsize       = kwargs.get('tsize',       _lsize         ) # text size
    twidth      = kwargs.get('twidth',      None           ) or 1 # scalefactor for legend width
    theight     = kwargs.get('theight',     None           ) or 1 # scalefactor for legend height
    texts       = kwargs.get('text',        [ ]            ) # extra text below legend
    margin      = kwargs.get('margin',      1.0            ) # scale legend margin
    ncols       = kwargs.get('ncol',        self.ncols     )
    ncols       = kwargs.get('ncols',       ncols          ) or 1 # number of legend columns
    colsep      = kwargs.get('colsep',      0.06           ) # seperation between legend columns
    bold        = kwargs.get('bold',        True           ) # bold legend header
    pad         = kwargs.get('panel',       1              ) # panel (top/main=1, bottom/ratio=2)
    pad         = kwargs.get('pad',         pad            ) # pad (top/main=1, bottom/ratio=2)
    texts       = ensurelist(texts,nonzero=True)
    entries     = ensurelist(entries,nonzero=False)
    bandentries = ensurelist(bandentries,nonzero=True)
    headerfont  = 62 if bold else 42
    
    # CHECK
    LOG.insist(self.canvas,"Canvas does not exist!")
    oldpad = gPad
    self.canvas.cd(pad)
    scale  = 485./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    xscale = 800./gPad.GetWw()
    tsize *= scale # text size
    
    # ENTRIES
    if reverse: # reverse order in legend
      hists.reverse()
    #if len(bandentries)==len(bands) and len(entries)>len(hists):
    #  for band, bandtitle in zip(band,bandentries):
    #    entries.insert(hists.index(band),bandtitle)
    while len(entries)<len(hists):
      if printmean:
        entries.append(hists[len(entries)].GetTitle() + ':  %0.3f' %hists[len(entries)].GetMean())
      else:
        entries.append(hists[len(entries)].GetTitle())
    while len(bandentries)<len(bands):
      bandentries.append(bands[len(bandentries)].GetTitle())
    hists   = hists + bands
    entries = entries + bandentries
    if latex:
      title   = maketitle(title)
      entries = [maketitle(e) for e in entries]
      texts   = [maketitle(t) for t in texts]
    maxlen = estimatelen([title]+entries+texts)
    
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
        if 'HIST' in hist.GetOption() and 'l' not in errstyle:
          styles.append('l'+errstyle)
        elif isinstance(hist,(TGraphErrors,TGraphAsymmErrors)): # vertical error bars
          styles.append('l'+errstyle)
        else:
          styles.append(errstyle)
      else:
        styles.append('lp')
    
    # NUMBER of LINES
    nlines = sum([1+e.count('\n') for e in entries])
    #else:       nlines += 0.80
    if texts:   nlines += sum([1+t.count('\n') for t in texts])
    if ncols>1: nlines  = int(ceil(nlines/float(ncols)))
    if title:   nlines += 1 + title.count('\n')
    
    # LEGEND DIMENSIONS
    if width<0: # automatic width
      width  = twidth*(tsize/_lsize)*xscale*max(0.22,min(0.60,0.036+0.016*maxlen))
      if ncols>1:
        width *= ncols/(1-colsep)
    if height<0:
      height = theight*0.0643*(tsize/_lsize)*nlines
    x2 = 0.90; x1 = x2 - width
    y1 = 0.92; y2 = y1 - height
    
    # POSITION
    if position==None:
      position = ""
    position = position.replace('left','L').replace('center','C').replace('right','R').replace( #.lower()
                                'top','T').replace('middle','M').replace('bottom','B')
    if not any(c in position for c in 'TMBy'): # set default vertical
      if 'L' in position:
        y1_user = 0.89 # move down default left legend because of corner text
      else:
        position += 'T'
    if not any(c in position for c in 'LCRx'): # set default horizontal
      position += 'RR' if ncols>1 else 'R' # if title else 'L'
    
    # HORIZONTAL X COORDINATES
    if x1_user!=None:
      x1 = x1_user
      x2 = x1 + width if x2_user==None else x2_user
    elif 'C'   in position: # horizontal center
      if   'R' in position: center = 0.57 # right of center
      elif 'L' in position: center = 0.43 # left of center
      else:                 center = 0.50 # center
      x1 = center-width/2; x2 = center+width/2
    elif 'LL'  in position: x1 = 0.03; x2 = x1 + width # far left
    elif 'L'   in position: x1 = 0.08; x2 = x1 + width # left
    elif 'RR'  in position: x2 = 0.97; x1 = x2 - width # far right
    elif 'R'   in position: x2 = 0.92; x1 = x2 - width # right
    elif 'x='  in position: # horizontal coordinate set by user
      x1 = float(re.findall(r"x=(\d\.\d+)",position)[0])
      x2 = x1 + width
    
    # VERTICAL Y COORDINATES
    if y1_user!=None:
      y1 = y1_user
      y2 = y1 - height if y2_user==None else y2_user
    elif 'M'   in position: # vertical middle
      if   'T' in position: middle = 0.57 # above middle
      elif 'B' in position: middle = 0.43 # below middle
      else:                 middle = 0.50 # exact middle
      y1 = middle-height/2; y2 = middle+height/2
    elif 'TT'  in position: y2 = 0.97; y1 = y2 - height # far top
    elif 'T'   in position: y2 = 0.92; y1 = y2 - height # top
    elif 'BB'  in position: y1 = 0.03; y2 = y1 + height # far bottom
    elif 'B'   in position: y1 = 0.08; y2 = y1 + height # bottom
    elif 'y='  in position: # vertical coordinate set by user
      y2 = float(re.findall(r"y=(\d\.\d+)",position)[0]);
      y1 = y2 - height
    
    # CONVERT TO NORMALIZED CANVAS COORDINATES
    L, R = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    X1, X2 = L+(1-L-R)*x1, L+(1-L-R)*x2
    Y1, Y2 = B+(1-T-B)*y1, B+(1-T-B)*y2
    legend = TLegend(X1,Y1,X2,Y2)
    LOG.verb("Plot.drawlegend: position=%r, height=%.3f, width=%.3f, (x1,y1,x2,y2)=(%.2f,%.2f,%.2f,%.2f), (X1,Y1,X2,Y2)=(%.2f,%.2f,%.2f,%.2f)"%(
                               position,height,width,x1,y1,x2,y2,X1,Y1,X2,Y2),verbosity,1)
    
    # MARGIN
    if ncols>=3:
      margin *= 0.045*ncols/width
    elif ncols==2:
      margin *= 0.090/width
    else:
      margin *= 0.044/width
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
      for hist_, entry_, style_ in columnize(zip(hists,entries,styles),ncols):
        if '$INT' in entry_: # add histogram integral in entry
          intstr = "%+.1f"%hist_.Integral()
          LOG.verb("Plot.drawlegend: Replace '$INT' with %r in %r"%(intstr,entry_),verbosity,3)
          entry_ = entry_.replace('$INT',"%+.1f"%num)
        if '$FRAC' in entry_ and hists[0].Integral()>0: # add relative difference in entry
          num, den = hist_.Integral(), hists[0].Integral()
          frac = "%+.1f%%"%(100.*(num/den-1.))
          LOG.verb("Plot.drawlegend: Replace '$FRAC' with %r (num=%s, den=%s) in %r"%(frac,num,den,entry_),verbosity,3)
          entry_ = entry_.replace('$FRAC',frac)
        for entry in entry_.split('\n'): # break lines
          LOG.verb("Plot.drawlegend: Add entry: %r, %r, %r"%(hist_,entry,style_),verbosity,2)
          legend.AddEntry(hist_,entry,style_)
          hist_, style_ = 0, '' # for next line
    for line in texts:
      legend.AddEntry(0,line,'')
    
    if verbosity>=2:
      print(">>> Plot.drawlegend: title=%r, texts=%s, latex=%s"%(title,texts,latex))
      print(">>> Plot.drawlegend: hists=%s"%(hists))
      print(">>> Plot.drawlegend: entries=%s"%(entries))
      print(">>> Plot.drawlegend: styles=%s, style=%s, errstyle=%s"%(styles,style,errstyle))
      print(">>> Plot.drawlegend: nlines=%s, len(hists)=%s, len(texts)=%s, ncols=%s, margin=%s, xscale=%s"%(
                                  nlines,len(hists),len(texts),ncols,margin,xscale))
    
    legend.Draw(option)
    self.legends.append(legend)
    oldpad.cd() # return to previous pad to not interfere with other operations
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
    position   = kwargs.get('pos',      None     )
    position   = kwargs.get('position', position ) or 'topleft' #.lower()
    tsize      = kwargs.get('size',     _lsize   ) # text size
    tsize      = kwargs.get('tsize',    tsize    ) # text size
    theight    = kwargs.get('theight',  None     ) or 1 # scale line height
    color      = kwargs.get('color',    kBlack   ) # text color
    bold       = kwargs.get('bold',     False    ) # bold text
    angle      = kwargs.get('angle',    0        ) # text angle
    dolatex    = kwargs.get('latex',    True     ) # automatically format strings as LaTeX
    xuser      = kwargs.get('x',        None     ) # horizontal position
    yuser      = kwargs.get('y',        None     ) # vertical position
    ndc        = kwargs.get('ndc',      True     ) # normalized coordinates
    align_user = kwargs.get('align',    None     ) # text line
    pad        = kwargs.get('panel',    1        ) # panel (top/main=1, bottom/ratio=2)
    pad        = kwargs.get('pad',      pad      ) # pad (top/main=1, bottom/ratio=2)
    texts      = unpacklistargs(texts)
    i = 0
    while i<len(texts):
      line = texts[i]
      if '\n' in line:
        lines = line.replace('\\n','').split('\n')
        texts = texts[:i]+lines+texts[i+1:]
        i += len(lines)
      else:
        i += 1
    if not any(t!="" for t in texts):
      return None
    
    # CHECK
    LOG.insist(self.canvas,"Canvas does not exist! Did you call Plot.draw?")
    oldpad = gPad
    self.canvas.cd(pad)
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
    latex.SetTextColor(color)
    latex.SetTextAngle(angle)
    latex.SetNDC(ndc)
    for i, line in enumerate(texts):
      if dolatex:
        line = maketitle(line)
      yline = y-i*theight*1.2*tsize
      latex.DrawLatex(x,yline,line)
      LOG.verb("Plot.drawtext: i=%d, x=%.2f, y=%.2f, text=%r"%(i,x,yline,line),verbosity,2)
    self.texts.append(latex)
    oldpad.cd() # return to previous pad to not interfere with other operations
    
    return latex
    
  
  def drawline(self,x1,y1,x2,y2,color=kBlack,style=kSolid,width=1,pad=1,redraw=True):
    """Draw line on canvas. If the canvas already exists, draw now on top of existing objects,
    else draw later in Plot.draw on in background."""
    if x1=='min': x1 = self.xmin
    if x2=='max': x2 = self.xmax
    if y1=='min': y1 = self.ymin # if available after Plot.draw
    if y2=='max': y2 = self.ymax # if available after Plot.draw
    line = TGraph(2) #TLine(xmin,1,xmax,1) # use TGraph to stay inside frame
    line.SetPoint(0,x1,y1)
    line.SetPoint(1,x2,y2)
    line.SetLineColor(color)
    line.SetLineStyle(style)
    line.SetLineWidth(width)
    line.pad = pad # 1: main, 2: ratio (typically)
    line.option = 'LSAME'
    if self.canvas:
      oldpad = gPad
      self.canvas.cd(pad) # 1: main, 2: ratio (typically)
      line.Draw(line.option)
      if redraw: # redraw axis on top of lines
        gPad.RedrawAxis()
      oldpad.cd() # return to previous pad to not interfere with other operations
    self.lines.append(line)
    return line
    
  
  def drawbox(self,x1,y1,x2,y2,color=kRed,style=1001,pad=1,redraw=True):
    """Draw box on canvas. If the canvas already exists, draw now on top of existing objects,
    else draw later in Plot.draw on in background."""
    if x1=='min': x1 = self.xmin
    if x2=='max': x2 = self.xmax
    if y1=='min': y1 = self.ymin # if available after Plot.draw
    if y2=='max': y2 = self.ymax # if available after Plot.draw
    box = TGraph(4) #TLine(xmin,1,xmax,1) # use TGraph to stay inside frame
    points = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)] # box corners (cyclic)
    for i, (x,y) in enumerate(points):
      box.SetPoint(i,x,y)
    box.SetLineWidth(2)
    box.SetLineStyle(kSolid)
    box.SetLineColor(color)
    box.SetFillStyle(style)
    box.SetFillColor(color)
    box.pad = pad # 1: main, 2: ratio (typically)
    box.option = 'FSAME'
    if self.canvas:
      oldpad = gPad
      self.canvas.cd(pad) # 1: main, 2: ratio (typically)
      graph.Draw(box.option)
      if redraw: # redraw axis on top of box
        gPad.RedrawAxis()
      oldpad.cd() # return to previous pad to not interfere with other operations
    self.boxes.append(box)
    return box
    
  
  def drawbins(self,bins,text=True,y=0.96,**kwargs):
    """Divide x axis into bins with extra lines, e.g. for unrolled 2D plots."""
    verbosity = LOG.getverbosity(self,kwargs)
    title   = kwargs.get('title',       ""    )
    size    = kwargs.get('size',        0.025 )
    align   = kwargs.get('align',       23    )
    axis    = kwargs.get('axis',        'x'   )
    ioffset = kwargs.get('ioffset',     0     )
    addof   = kwargs.get('addoverflow', False ) # last bin is infinity
    xmin, xmax = self.xmin, self.xmax
    if isinstance(bins,Variable):
      nbins = bins.nbins
    elif islist(bins):
      nbins = len(bins)-1
    else:
      text  = False
      nbins = bins
    if ioffset>0:
      nbins -= ioffset
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
            y1 = bins.getedge(ioffset+i) # edges mass bin
            y2 = bins.getedge(ioffset+i+1)
          else:
            y1 = bins[ioffset+i] # edges mass bin
            y2 = bins[ioffset+i+1]
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
    setcols      = kwargs.get('setcols',      True   )
    style        = kwargs.get('style',        True   )
    styles       = style if islist(style) else None
    styles       = kwargs.get('styles',       styles ) or self.lstyles # alias
    widths       = kwargs.get('width',        2      )
    offset       = kwargs.get('offset',       0      )
    mstyle       = kwargs.get('mstyle',       None   ) or triple or pair
    styles       = ensurelist(styles)
    widths       = ensurelist(widths)
    LOG.verb("Plot.setlinestyle: widths=%r, colors=%r, styles=%r, mstyle=%r"%(widths,colors,styles,mstyle),verbosity,2)
    for i, hist in enumerate(hists):
      hist.SetFillStyle(0)
      if triple:
        if setcols:
          hist.SetLineColor(colors[(i//3)%len(colors)])
        hist.SetLineStyle(styles[i%min(3,len(styles))])
        hist.SetMarkerSize(0.6)
        hist.SetMarkerColor(hist.GetLineColor()+1)
      elif pair:
        color = colors[(i//2)%len(colors)]
        if color>300 and i%2==1:
          color += 1 # make darker
        if setcols:
          hist.SetLineColor(colors[(i//2)%len(colors)])
        hist.SetLineStyle(styles[i%min(2,len(styles))])
        hist.SetMarkerColor(color)
        if i%2==1: hist.SetMarkerSize(0.6)
        else:      hist.SetMarkerSize(0.0)
      else:
        if setcols:
          hist.SetLineColor(colors[i%len(colors)])
          hist.SetMarkerSize(0.6)
          hist.SetMarkerColor(hist.GetLineColor()+1)
        if style:
          if isinstance(style,bool):
            hist.SetLineStyle(styles[i%len(styles)])
          else:
            hist.SetLineStyle(style)
      if widths:
        hist.SetLineWidth(widths[i%len(widths)])
      if triple and i%3==2:
        #if hasattr(hist,'SetOption'):
        hist.SetOption('E1')
        #hist.SetLineWidth(0)
        hist.SetLineStyle(kSolid)
        hist.SetLineColor(hist.GetMarkerColor())
      elif not mstyle: # no markers
        hist.SetMarkerStyle(8)   # marker needed to allow line through end of error bars
        hist.SetMarkerSize(0.01) # make invisible
    
  
  def setmarkerstyle(self, *hists, **kwargs):
    """Set the marker style for a list of histograms."""
    verbosity = LOG.getverbosity(self,kwargs)
    mstyles   = kwargs.get('mstyle',  None    ) # alias
    mstyles   = kwargs.get('mstyles', mstyles ) or self.mstyles or _mstyles[:] # marker styles
    msizes    = kwargs.get('msize',   None    ) # alias
    msizes    = kwargs.get('msizes',  msizes  ) # marker size
    if not mstyles:
      return
    mstyles = ensurelist(mstyles)
    assert mstyles
    while len(mstyles)<len(hists): # ensure same length
      mstyles.append(mstyles[-1])
    if msizes: # only set if not None or empty list ([ ])
      msizes = ensurelist(msizes)
      while len(msizes)<len(hists): # ensure same length
        msizes.append(msizes[-1])
    LOG.verb("Plot.setmarkerstyle: mstyles=%r, msizes=%r"%(mstyles,msizes),verbosity,2)
    for i, (hist, mstyle) in enumerate(zip(hists,mstyles)):
      msize = None
      mcolor = hist.GetLineColor() #+1
      if islist(mstyle) and len(style)==2:
        mstyle, msize = mstyle
      elif isinstance(mstyle,str):
        if 'data' in mstyle.lower():
          mstyle, msize = 8, 0.9
        elif 'none' in mstyle.lower():
          mstyle, msize = 0, 0.0
        else: # e.g. 'hist'
          mstyle, msize = 8, 0.01
      elif mstyle==None:
        mstyle, msize = 0, 0.0
      elif isinstance(mstyle,int):
        msize = 0.9
      if msizes: # overwrite
        msize = msizes[i]
      hist.SetMarkerStyle(mstyle)
      hist.SetMarkerColor(mcolor)
      if msize!=None:
        hist.SetMarkerSize(msize)
      LOG.verb("Plot.setmarkerstyle: hist=%r, mstyle=%r, msize=%r, color=%r"%(hist,mstyle,msize,mcolor),verbosity,2)
    
  
  def setfillstyle(self, *hists, **kwargs):
    """Set the fill style for a list of histograms."""
    verbosity = LOG.getverbosity(self,kwargs)
    hists   = unpacklistargs(hists)
    reset   = kwargs.get('reset',  False ) # if reset==False: only set color if not kBlack or kWhite
    line    = kwargs.get('line',   True  )
    fcolors = kwargs.get('colors', None  ) or self.fcolors
    icol    = 0
    for hist in hists:
      #print(hist.GetFillColor())
      if not reset and hist.GetFillColor() not in [kBlack,kWhite]:
        continue
      #color = getColor(hist.GetName() )
      color = fcolors[icol%len(fcolors)]
      icol += 1
      hist.SetFillColor(color)
      if hist.GetFillStyle()<1001:
        hist.SetFillStyle(1001)
      if line:
        hist.SetLineColor(kBlack)
      LOG.verb("Plot.setfillstyle: hist=%r, icol=%s, color=%s"%(hist, icol, color),verbosity,2)
    
