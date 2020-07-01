# Author: Izaak Neutelings (June 2020)
# -*- coding: utf-8 -*-
import os, re
from math import log10
from TauFW.common.tools.utils import ensurelist, islist, isnumber
from TauFW.Plotter.plot.utils import *
from TauFW.Plotter.plot.strings import makelatex, maketitle, makehistname
from TauFW.Plotter.plot.Variable import Variable
from TauFW.Plotter.plot.Ratio import Ratio
import ROOT
from ROOT import gDirectory, gROOT, gPad, gStyle, TFile, TCanvas,\
                 TH1, TH1D, TH2, THStack, TGraph, TGraphAsymmErrors, TLine, TProfile,\
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


class Plot(object):
  """Class to automatically make CMS plot."""
  
  def __init__(self, *args, **kwargs):
    """
    Initialize with list of histograms:
      plot = Plot(hists)
    or with a variable (string or Variable object) as well:
      plot = Plot(variable,hists)
    """
    variable   = None
    hists      = None
    self.verbosity = LOG.getverbosity(kwargs)
    if len(args)==1 and islist(args[0]):
      hists    = None
    elif len(args)==2:
      variable = args[0]
      hists    = args[1]
    else:
      LOG.throw(IOError,"Plot: Wrong input %s"%(args))
    self.hists = hists
    frame      = kwargs.get('frame', self.hists[0] )
    if isinstance(variable,Variable):
      self.variable        = variable
      self.xtitle          = kwargs.get('xtitle',    variable.title     )
      self.xmin            = kwargs.get('xmin',      variable.xmin      )
      self.xmax            = kwargs.get('xmax',      variable.xmax      )
      self.ymin            = kwargs.get('ymin',      variable.ymin      )
      self.ymax            = kwargs.get('ymax',      variable.ymax      )
      self.rmin            = kwargs.get('rmin',      variable.rmin      )
      self.rmax            = kwargs.get('rmax',      variable.rmax      )
      self.binlabels       = kwargs.get('binlabels', variable.binlabels )
      self.logx            = kwargs.get('logx',      variable.logx      )
      self.logy            = kwargs.get('logy',      variable.logy      )
      self.ymargin         = kwargs.get('ymargin',   variable.ymargin   )
      self.logyrange       = kwargs.get('logyrange', variable.logyrange )
      self.position        = kwargs.get('position',  variable.position  )
      self.latex           = kwargs.get('latex',     False              )
      self.dividebybinsize = kwargs.get('dividebybinsize', variable.dividebybinsize)
    else:
      self.variable        = variable
      self.xtitle          = kwargs.get('xtitle', self.variable or frame.GetXaxis().GetTitle() )
      self.xmin            = kwargs.get('xmin', frame.GetXaxis().GetXmin() )
      self.xmax            = kwargs.get('xmax', frame.GetXaxis().GetXmax() )
      self.ymin            = kwargs.get('ymin',      None           )
      self.ymax            = kwargs.get('ymax',      None           )
      self.rmin            = kwargs.get('rmin',      None           )
      self.rmax            = kwargs.get('rmax',      None           )
      self.binlabels       = kwargs.get('binlabels', None           )
      self.logx            = kwargs.get('logx',      False          )
      self.logy            = kwargs.get('logy',      False          )
      self.ymargin         = kwargs.get('ymargin',   None           )
      self.logyrange       = kwargs.get('logyrange', None           )
      self.position        = kwargs.get('position',  ""             )
      self.latex           = kwargs.get('latex',     True           )
      self.dividebybinsize = kwargs.get('dividebybinsize', frame.GetXaxis().IsVariableBinSize())
    self.ytitle            = kwargs.get('ytitle',    frame.GetYaxis().GetTitle() )
    self.name              = kwargs.get('name',      None           ) or (self.hists[0].GetName() if self.hists else "noname")
    self.title             = kwargs.get('title',     None           )
    self.errband           = None
    self.ratio             = kwargs.get('ratio',     False          )
    self.append            = kwargs.get('append',    ""             )
    self.norm              = kwargs.get('norm',      False          )
    self.lcolors           = kwargs.get('lcolors',   _lcolors       )
    self.fcolors           = kwargs.get('fcolors',   _fcolors       )
    self.lstyles           = kwargs.get('lstyles',   _lstyles       )
    self.canvas            = None
    self.frame             = frame
    self.legend            = None
    self.texts             = [ ] # to save TLatex objects made by drawtext
    self.garbage           = [ ]
    
  
  def draw(self,*args,**kwargs):
    """Central method of Plot class: make plot with canvas, axis, error, ratio..."""
    # https://root.cern.ch/doc/master/classTHStack.html
    # https://root.cern.ch/doc/master/classTHistPainter.html#HP01e
    verbosity       = LOG.getverbosity(self,kwargs)
    xtitle          = (args[0] if args else self.xtitle) or ""
    ratio           = kwargs.get('ratio',           self.ratio           ) # make ratio plot
    square          = kwargs.get('square',          False                ) # square canvas
    lmargin         = kwargs.get('lmargin',         1.                   ) # canvas left margin
    rmargin         = kwargs.get('rmargin',         1.                   ) # canvas righ margin
    tmargin         = kwargs.get('tmargin',         1.                   ) # canvas bottom margin
    bmargin         = kwargs.get('bmargin',         1.                   ) # canvas top margin
    errbars         = kwargs.get('errbars',         True                 ) # add error bars to histogram
    staterr         = kwargs.get('staterr',         False                ) # create stat. error band
    sysvars         = kwargs.get('sysvars',         [ ]                  ) # create sys. error band from variations
    errtitle        = kwargs.get('errtitle',        None                 ) # title for error band
    norm            = kwargs.get('norm',            self.norm            ) # normalize all histograms
    title           = kwargs.get('title',           self.title           ) # title for legend
    xtitle          = kwargs.get('xtitle',          xtitle               )
    ytitle          = "A.U." if norm else "Events"
    ytitle          = kwargs.get('ytitle',          self.ytitle          ) or ytitle
    rtitle          = kwargs.get('rtitle',          "Ratio"              )
    latex           = kwargs.get('latex',           self.latex           )
    xmin            = kwargs.get('xmin',            self.xmin            )
    xmax            = kwargs.get('xmax',            self.xmax            )
    ymin            = kwargs.get('ymin',            self.ymin            )
    ymax            = kwargs.get('ymax',            self.ymax            )
    rmin            = kwargs.get('rmin',            self.rmin            ) or 0.45 # ratio ymin
    rmax            = kwargs.get('rmax',            self.rmax            ) or 1.55 # ratio ymax
    ratiorange      = kwargs.get('ratiorange',      None                 ) # ratio range around 1.0
    binlabels       = kwargs.get('binlabels',       self.binlabels       ) # list of alphanumeric bin labels
    ytitleoffset    = kwargs.get('ytitleoffset',    1.0                  )
    xtitleoffset    = kwargs.get('xtitleoffset',    1.0                  )
    logx            = kwargs.get('logx',            self.logx            )
    logy            = kwargs.get('logy',            self.logy            )
    ymargin         = kwargs.get('ymargin',         self.ymargin         ) # margin between hist maximum and plot's top
    logyrange       = kwargs.get('logyrange',       self.logyrange       ) # log(y) range from hist maximum to ymin
    grid            = kwargs.get('grid',            True                 )
    tsize           = kwargs.get('tsize',           _tsize               ) # text size for axis title
    pair            = kwargs.get('pair',            False                )
    triple          = kwargs.get('triple',          False                )
    ncols           = kwargs.get('ncols',           1                    ) # number of columns in legend
    lcolors         = kwargs.get('lcolors',         None                 ) or self.lcolors
    fcolors         = kwargs.get('fcolors',         None                 ) or self.fcolors
    lstyles         = kwargs.get('lstyle',          None                 )
    lstyles         = kwargs.get('lstyles',         lstyles              ) or self.lstyles
    lwidth          = kwargs.get('lwidth',          2                    ) # line width
    mstyle          = kwargs.get('mstyle',          None                 ) # marker style
    option          = kwargs.get('option',          'HIST'               ) # draw option for every histogram
    options         = kwargs.get('options',         [ ]                  ) # draw option list per histogram
    roption         = kwargs.get('roption',         None                 ) # draw option of ratio plot
    enderrorsize    = kwargs.get('enderrorsize',    2.0                  ) # size of line at end of error bar
    errorX          = kwargs.get('errorX',          True                 ) # horizontal error bars
    dividebybinsize = kwargs.get('dividebybinsize', self.dividebybinsize )
    lcolors         = ensurelist(lcolors)
    fcolors         = ensurelist(fcolors)
    lstyles         = ensurelist(lstyles)
    self.lcolors    = lcolors
    self.fcolors    = fcolors
    self.lstyles    = lstyles
    if not xmin:  xmin = self.xmin
    if not xmax:  xmax = self.xmax
    hists           = self.hists
    denom           = ratio if isinstance(ratio,int) and (ratio!=0) else False
    denom           = max(0,min(len(hists),kwargs.get('denom', denom ))) # denominator histogram in ratio plot
    
    # NORM
    if norm:
      normalize(self.hists)
    
    # DIVIDE BY BINSIZE
    if dividebybinsize:
      for i, oldhist in enumerate(self.hists):
        newhist = divideBinsByBinSize(oldhist,zero=True,zeroerrs=False)
        if oldhist!=newhist:
          LOG.verb("Plot.draw: replace %s -> %s"%(oldhist,newhist),verbosity,2)
          self.hists[i] = newhist
          self.garbage.append(oldhist)
      #if sysvars:
      #  histlist = sysvars.values() if isinstance(sysvars,dict) else sysvars
      #  for (histup,hist,histdown) in histlist:
      #    divideBinsByBinSize(histup,  zero=True,zeroerrs=False)
      #    divideBinsByBinSize(histdown,zero=True,zeroerrs=False)
      #    if hist not in self.hists:
      #      divideBinsByBinSize(hist,zero=True,zeroerrs=False)
    
    # DRAW OPTIONS
    if errbars:
      option = 'E0 '+option
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
    self.canvas = self.setcanvas(square=square,ratio=ratio,
                                 lmargin=lmargin,rmargin=rmargin,tmargin=tmargin,bmargin=bmargin)
    
    # DRAW
    self.canvas.cd(1)
    #self.frame.Draw('AXIS') # 'AXIS' breaks grid
    for i, (hist, option1) in enumerate(zip(hists,options)):
      if triple and i%3==2:
        option1 = 'E1'
      option1 += " SAME"
      hist.Draw(option1)
      LOG.verb("Plot.draw: i=%s, hist=%s, option%s"%(i,hist,option1),verbosity,2)
    
    # STYLE
    lhists, mhists = [ ], [ ]
    for hist, opt in zip(hists,options):
      if 'H' in opt: lhists.append(hist)
      else:          mhists.append(hist)
    self.setlinestyle(lhists,colors=lcolors,styles=lstyles,mstyle=mstyle,width=lwidth,pair=pair,triple=triple)
    self.setmarkerstyle(*mhists,colors=lcolors)
    
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
    self.setaxes(self.frame,*hists,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,logy=logy,logx=logx,
                 xtitle=xtitle,ytitle=ytitle,ytitleoffset=ytitleoffset,xtitleoffset=xtitleoffset,
                 binlabels=binlabels,ymargin=ymargin,logyrange=logyrange,main=ratio,grid=grid,latex=latex)
    
    # RATIO
    if ratio:
      self.canvas.cd(2)
      self.ratio = Ratio(*hists,errband=self.errband,denom=denom,drawzero=True,option=roption)
      self.ratio.draw(roption,xmin=xmin,xmax=xmax)
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
    if self.errband:
      deletehist(self.errband)
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
    verbosity = LOG.getverbosity(self,kwargs)
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
    ratiorange    = kwargs.get('ratiorange',   None             )
    binlabels     = kwargs.get('binlabels',    None             )
    intbins       = kwargs.get('intbins',      True             ) # allow integer binning
    logx          = kwargs.get('logx',         False            )
    logy          = kwargs.get('logy',         False            )
    ymargin       = kwargs.get('ymargin',      None             ) or (1.3 if logy else 1.2) # margin between hist maximum and plot's top
    logyrange     = kwargs.get('logyrange',    None             ) or 3 # log(y) range from hist maximum to ymin
    negativey     = kwargs.get('negativey',    True             ) # allow negative y values
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
    xlabelsize    = kwargs.get('xlabelsize',   _lsize           )*scale
    ylabelsize    = kwargs.get('ylabelsize',   _lsize           )*scale
    ytitleoffset  = kwargs.get('ytitleoffset', 1.0              )*1.26/scale
    xtitleoffset  = kwargs.get('xtitleoffset', 1.0              )*1.00
    xlabeloffset  = kwargs.get('xlabeloffset', 0.007            )
    if main:
      xtitlesize  = 0.0
      xlabelsize  = 0.0
    LOG.verb("Plot.setaxes: Binning (%s,%.1f,%.1f)"%(nbins,xmin,xmax),verbosity,2)
    
    if ratiorange:
      ymin, ymax  = 1-ratiorange, 1+ratiorange
    if intbins and nbins<15 and int(xmin)==xmin and int(xmax)==xmax and binwidth==1:
      LOG.verb("Plot.setaxes: Setting integer binning for (%s,%d,%d)!"%(nbins,xmin,xmax),verbosity,1)
      binlabels   = [str(i) for i in range(int(xmin),int(xmax)+1)]
      xlabelsize   *= 1.6
      xlabeloffset *= 0.88*scale
    if logy:
      ylabelsize   *= 1.08
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
        LOG.verb("Plot.setaxes: logy=%s, hmax=%.6g, magnitude(hmax)=%s, logyrange=%s, ymin=%.6g"%(
                                logy,hmax,magnitude(hmax),logyrange,ymin),verbosity+2,2)
      if ymax==None:
        if hmax>ymin>0:
          span = abs(log10(hmax/ymin))*ymargin
          ymax = ymin*(10**span)
          LOG.verb("Plot.setaxes: log10(hmax/ymin)=%.6g, span=%.6g, ymax=%.6g"%(log10(hmax/ymin),span,ymax),verbosity+2,2)
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
    frame.GetXaxis().SetRangeUser(xmin,xmax)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    
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
        LOG.warning("Plot.setaxes: len(binlabels)=%d < %d=nbins"%(len(binlabels),nbins))
      for i, binlabel in zip(range(1,nbins+1),binlabels):
        frame.GetXaxis().SetBinLabel(i,binlabel)
      #frame.GetXaxis().LabelsOption('h')
    
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
    
    if verbosity>=2:
      print ">>> Plot.setaxes: frame=%s"%(frame)
      print ">>> Plot.setaxes: hists=%s"%(hists)
      print ">>> Plot.setaxes: [hmin,hmax] = [%.6g,%.6g], [xmin,xmax] = [%.6g,%.6g], [ymin,ymax] = [%.6g,%.6g]"%(hmin,hmax,xmin,xmax,ymin,ymax)
      print ">>> Plot.setaxes: xtitlesize=%.4g, xlabelsize=%.4g, xtitleoffset=%.4g, xtitle=%r"%(xtitlesize,xlabelsize,xtitleoffset,xtitle)
      print ">>> Plot.setaxes: ytitlesize=%.4g, ylabelsize=%.4g, ytitleoffset=%.4g, ytitle=%r"%(ytitlesize,ylabelsize,ytitleoffset,ytitle)
      print ">>> Plot.setaxes: scale=%.4g, nxdivisions=%s, nydivisions=%s, ymargin=%.3f, logyrange=%.3f"%(scale,nxdivisions,nydivisions,ymargin,logyrange)
    if main:
      if any(a!=None and a!=b for a, b in [(self.xmin,xmin),(self.xmax,xmax)]):
        LOG.warning("Plot.setaxes: x axis range changed: [xmin,xmax] = [%.6g,%.6g] -> [%.6g,%.6g]"%(
                    self.xmin,self.xmax,xmin,xmax))
      if any(a!=None and a!=b for a, b in [(self.ymin,ymin),(self.ymax,ymax)]):
        LOG.warning("Plot.setaxes: y axis range changed: [ymin,ymax] = [%.6g,%.6g] -> [%.6g,%.6g]"%(
                    self.ymin,self.ymax,ymin,ymax))
      self.xmin, self.xmax = xmin, xmax
      self.ymin, self.ymax = ymin, ymax
    return xmin, xmax, ymin, ymax
    
  
  def drawlegend(self,**kwargs):
    """Create and draw legend."""
    #if not ratio:
    #  tsize *= 0.80
    #  signaltsize *= 0.80
    verbosity   = LOG.getverbosity(self,kwargs)
    hists       = self.hists
    scale       = 550./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    errstyle    = 'lep' if gStyle.GetErrorX() else 'ep'
    entries     = kwargs.get('entries',     [ ]            )
    bands       = kwargs.get('band',        [self.errband] ) # error bands
    bands       = ensurelist(bands,nonzero=True)
    bandentries = kwargs.get('bandentries', [ ]            )
    title       = kwargs.get('header',      None           )
    title       = kwargs.get('title',       title          )
    style       = kwargs.get('style',       None           )
    style0      = kwargs.get('style0',      None           ) # style of first histogram
    errstyle    = kwargs.get('errstyle',    errstyle       ) # style for an error point
    styles      = kwargs.get('styles',      [ ]            )
    position    = kwargs.get('pos',         None           ) # legend position
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
    tsize       = kwargs.get('tsize',       _lsize         )*scale
    twidth      = kwargs.get('twidth',      1.0            ) # scalefactor for legend width
    texts       = kwargs.get('text',        [ ]            ) # extra text below legend
    ncols       = kwargs.get('ncols',       1              ) # number of legend columns
    colsep      = kwargs.get('colsep',      0.06           ) # seperation between legend columns
    bold        = kwargs.get('bold',        True           ) # bold legend header
    texts       = ensurelist(texts,nonzero=True)
    entries     = ensurelist(entries,nonzero=False)
    bandentries = ensurelist(bandentries,nonzero=True)
    headerfont  = 62 if bold else 42
    
    # CHECK
    LOG.insist(self.canvas,"Canvas does not exist!")
    self.canvas.cd(1)
    
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
      elif 'E0' in hist.GetOption():
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
    L, R = gPad.GetLeftMargin(), gPad.GetRightMargin()
    T, B = gPad.GetTopMargin(),  gPad.GetBottomMargin()
    if width<0:  width  = 0.26*twidth
    if height<0: height = 1.10*tsize*nlines
    if ncols>1:  width *= ncols/(1-colsep)
    x2 = 0.86-R; x1 = x2 - width
    y2 = 0.90-T; y1 = y2 - height
    
    # POSITION
    if not position:
      position = 'left' if title else 'topleft'
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
    if x1_user!=None:
      x2 = x1 + width if x2_user==None else x2_user
    if y1_user!=None:
      y2 = y1 - height if y2_user==None else y2_user
    legend = TLegend(x1,y1,x2,y2)
    LOG.verb("Plot.drawlegend: position=%r, height=%.3f, width=%.3f, x1=%.3f, y1=%.3f, x2=%.3f, y2=%.3f"%(
                               position,height,width,x1,y1,x2,y2),verbosity,1)
    
    # MARGIN
    if ncols>=2:
      margin = 0.086/width
    else:
      margin = 0.042/width
    legend.SetMargin(margin)
    if verbosity>=2:
      print ">>> Plot.drawlegend: title=%r, texts=%s"%(title,texts)
      print ">>> Plot.drawlegend: hists=%s"%(hists)
      print ">>> Plot.drawlegend: entries=%s"%(entries)
      print ">>> Plot.drawlegend: styles=%s"%(styles)
      print ">>> Plot.drawlegend: nlines=%s, len(hists)=%s, len(texts)=%s, ncols=%s, margin=%s"%(
                                  nlines,len(hists),len(texts),ncols,margin)
    
    # STYLE
    if transparent: legend.SetFillStyle(0) # 0 = transparent
    else: legend.SetFillColor(0)
    legend.SetBorderSize(border)
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
      for hist1, entry1, style1 in columnize(zip(hists,entries,styles),ncols):
        for entry in entry1.split('\n'):
          legend.AddEntry(hist1,maketitle(entry),style1)
          hist1, style1 = 0, ''
    for line in texts:
      legend.AddEntry(0,maketitle(line),'')
    
    legend.Draw(option)
    self.legend = legend
    return legend
    
  
  def drawtext(self,*texts,**kwargs):
    """Draw TLaTeX text in the corner."""
    verbosity = LOG.getverbosity(self,kwargs)
    scale     = 550./min(gPad.GetWh()*gPad.GetHNDC(),gPad.GetWw()*gPad.GetWNDC())
    position  = kwargs.get('pos',      'topleft' )
    position  = kwargs.get('position', position  ).lower()
    tsize     = kwargs.get('tsize',    _lsize    )*scale
    bold      = kwargs.get('bold',     False     )
    xuser     = kwargs.get('x',        None      )
    yuser     = kwargs.get('y',        None      )
    texts     = unwraplistargs(texts)
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
    x = L + (1-L-R)*x if xuser==None else xuser
    y = B + (1-T-B)*y if yuser==None else yuser
    
    # LATEX
    latex = TLatex()
    latex.SetTextSize(tsize)
    latex.SetTextAlign(align)
    latex.SetTextFont(font)
    #latex.SetTextColor(kRed)
    latex.SetNDC(True)
    for i, line in enumerate(texts):
      yline = y-i*1.2*tsize
      latex.DrawLatex(x,yline,line)
      LOG.verb("Plot.drawcornertext: i=%d, x=%d, y=%d, text=%r"%(i,x,yline,line),verbosity,2)
    self.texts.append(latex)
    
    return latex
    
  
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
    
  
