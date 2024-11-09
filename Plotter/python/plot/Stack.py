# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
# Description: Class to automatically make CMS plot comparing data to expectation (as a stack)
# Sources:
#   https://twiki.cern.ch/twiki/bin/view/CMS/PoissonErrorBars
#   https://twiki.cern.ch/twiki/bin/view/CMS/StatComWideBins
#   https://twiki.cern.ch/twiki/bin/view/CMS/DataMCComparison
from TauFW.Plotter.plot.Plot import *
from TauFW.Plotter.plot.Plot import _tsize, _lsize


class Stack(Plot):
  """Class to automatically make CMS plot comparing data to expectation (as a stack)."""
  
  def __init__(self, variable, datahist, exphists, sighists=[ ], **kwargs):
    """
    Initialize as:
      plot = Stack(variable,datahist,exphists,sighists)
    with 
    - variable: string or Variable object
    - datahist: single TH1 or TGraph object of observed data
    - exphists: list of TH1 objects for expected processes (to be stacked)
    - sighists: list of TH1 objects for signals (to be overlayed as line)
    """
    self.verbosity = LOG.getverbosity(kwargs)
    
    # PARSE ARGUMENTS: variable & (list of) histogram(s)
    self.datahist = datahist
    self.exphists = ensurelist(exphists)
    self.sighists = ensurelist(sighists)
    if kwargs.get('clone',False):
      if self.datahist:
        self.datahist = self.datahist.Clone(self.datahist.GetName()+"_clone_Stack")
      self.exphists = [h.Clone(h.GetName()+"_clone_Stack") for h in self.exphists]
      self.sighists = [h.Clone(h.GetName()+"_clone_Stack") for h in self.sighists]
    if self.datahist:
      self.hists = [self.datahist]+self.exphists+self.sighists
    else:
      self.hists = self.exphists+self.sighists
    
    # OTHER SETTINGS
    kwargs['clone'] = False
    self.ratio      = kwargs.setdefault('ratio', bool(self.datahist) )
    args = (self.hists,) if variable==None else (variable,self.hists)
    super(Stack,self).__init__(*args,**kwargs) # reuse Plot.__init__ for common settings 
    self.dividebins = kwargs.get('dividebins', self.hasvarbins ) # divide each histogram bins by it bin size
    if self.verbosity>=3:
      print(">>> Stack.__init__: datahist=%s"%(self.datahist))
      print(">>> Stack.__init__: exphists=%s"%(self.exphists))
      print(">>> Stack.__init__: sighists=%s"%(self.sighists))
    
  
  def draw(self,*args,**kwargs):
    """Central method of Plot class: make plot with canvas, axis, error, ratio..."""
    # https://root.cern.ch/doc/master/classTHStack.html
    # https://root.cern.ch/doc/master/classTHistPainter.html#HP01e
    verbosity    = LOG.getverbosity(self,kwargs)
    xtitle       = (args[0] if args else self.xtitle) or ""
    square       = kwargs.get('square',       False           ) # square canvas
    cwidth       = kwargs.get('width',        None            ) # canvas width
    cheight      = kwargs.get('height',       None            ) # canvas height
    lmargin      = kwargs.get('lmargin',      1.              ) # canvas left margin
    rmargin      = kwargs.get('rmargin',      1.              ) # canvas righ margin
    tmargin      = kwargs.get('tmargin',      1.              ) # canvas bottom margin
    bmargin      = kwargs.get('bmargin',      1.              ) # canvas top margin
    errbars      = kwargs.get('errbars',      False           ) # add error bars to histogram
    staterr      = kwargs.get('staterr',      True            ) # create stat. error band
    sysvars      = kwargs.get('sysvars',      [ ]             ) # create sys. error band from variations
    multibands   = kwargs.get('multibands',   False           ) # create stat. error band for each histogram in stack
    errtitle     = kwargs.get('errtitle',     None            ) # title for error band
    norm         = kwargs.get('norm',         self.norm       ) # normalize all histograms
    sigscales    = kwargs.get('sigscale',     None            ) # scale signal histograms (after normalization)
    fraction     = kwargs.get('fraction',     False           ) # draw fraction stack in ratio plot
    xtitle       = kwargs.get('xtitle',       xtitle          ) # x axis title
    ytitle       = kwargs.get('ytitle',       self.ytitle     ) # y axis title (if None, automatically set by Plot.setaxis)
    rtitle       = kwargs.get('rtitle',       "Obs. / Exp."   ) # y axis title of ratio panel
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
    rmin         = kwargs.get('rmin',         self.rmin       ) or (0.0 if fraction else 0.45) # ratio ymin
    rmax         = kwargs.get('rmax',         self.rmax       ) or 1.55 # ratio ymax
    ratiorange   = kwargs.get('rrange',       self.ratiorange ) # ratio range around 1.0
    ratio        = kwargs.get('ratio',        self.ratio      ) # make ratio plot
    lowerpanels  = kwargs.get('lowerpanels',  int(ratio)      ) # number of lower panels
    denom        = int(ratio) if isinstance(ratio,int) and (ratio!=0) else 1 # assume first histogram is denominator (i.e. stack)
    denom        = kwargs.get('den',          denom           ) # index of common denominator histogram in ratio plot (count from 1)
    denom        = kwargs.get('denom',        denom           ) # alias
    num          = kwargs.get('num',          None            ) # index of common numerator histogram in ratio plot (count from 1)
    rhists       = kwargs.get('rhists',       None            ) # custom histogram argument for ratio plot
    nxdiv        = kwargs.get('nxdiv',        None            ) # tick divisions of x axis
    nydiv        = kwargs.get('nydiv',        None            ) # tick divisions of y axis
    nrdiv        = kwargs.get('nrdiv',        506             ) # tick divisions of y axis of ratio panel
    logx         = kwargs.get('logx',         self.logx       )
    logy         = kwargs.get('logy',         self.logy       )
    ymargin      = kwargs.get('ymarg',        self.ymargin    ) # alias
    ymargin      = kwargs.get('ymargin',      ymargin         ) # margin between hist maximum and plot's top
    logyrange    = kwargs.get('logyrange',    self.logyrange  ) # log(y) range from hist maximum to ymin
    grid         = kwargs.get('grid',         False           )
    pair         = kwargs.get('pair',         False           )
    triple       = kwargs.get('triple',       False           )
    lcolors      = kwargs.get('lcolors',      None            ) or self.lcolors
    fcolors      = kwargs.get('fcolors',      None            ) or self.fcolors
    resetcolors  = kwargs.get('resetcolors', 'fcolors' in kwargs )
    lstyles      = kwargs.get('lstyle',       None            )
    lstyles      = kwargs.get('lstyles',      lstyles         ) or self.lstyles
    lwidth       = kwargs.get('lwidth',       2               ) # line width
    mstyle       = kwargs.get('mstyle',       None            ) # marker style
    option       = kwargs.get('option',       'HIST'          ) # draw option for stack
    soption      = kwargs.get('soption',      'HIST'          ) # draw option for signal histograms
    doption      = kwargs.get('doption',      'E1'            ) # draw option for data histograms
    roption      = kwargs.get('roption',      None            ) # draw option of ratio plot
    enderrorsize = kwargs.get('enderrorsize', 2.0             ) # size of line at end of error bar
    errorX       = kwargs.get('errorX',       self.hasvarbins ) # no horizontal error bars, unless variable bin size (CMS style)
    dividebins   = kwargs.get('dividebins',   self.dividebins ) # divide content / y values by bin size
    drawdata     = kwargs.get('drawdata',     True            ) and bool(self.datahist)
    drawsignal   = kwargs.get('drawsignal',   True            ) and bool(self.sighists)
    reverse      = kwargs.get('reversestack', False           ) # stack bottom to top reversed w.r.t. legend
    lcolors      = ensurelist(lcolors)
    fcolors      = ensurelist(fcolors)
    lstyles      = ensurelist(lstyles)
    self.ratio   = ratio
    self.lcolors = lcolors
    self.fcolors = fcolors
    self.lstyles = lstyles
    if not xmin and xmin!=0: xmin = self.xmin
    if not xmax and xmax!=0: xmax = self.xmax
    if verbosity>=2:
      print(">>> Stack.draw: xtitle=%r, ytitle=%r"%(xtitle,ytitle))
      print(">>> Stack.draw: xmin=%s, xmax=%s, ymin=%s, ymax=%s, rmin=%s, rmax=%s"%(xmin,xmax,ymin,ymax,rmin,rmax))
    
    # NORMALIZE
    if norm: # normalize data hist and stack
      if ytitle==None:
        ytitle = "A.U."
      scale = 1.0 if isinstance(norm,bool) else norm # can be list
      normalize(self.datahist,scale=scale)
      normalize(self.exphists,scale=scale,tosum=True) # normalize to sum of hist integrals
      if self.sighists:
        normalize(self.sighists,scale=scale)
    
    # SCALE SIGNAL HISTS
    if sigscales and sigscales!=None:
      sigscales = ensurelist(sigscales)
      while len(sigscales)<len(self.sighists):
        sigscales.append(sigscales[-1])
      for sighist, sigscale in zip(self.sighists,sigscales):
        sighist.Scale(sigscale)
    
    # DIVIDE BY BINSIZE
    if dividebins:
      LOG.verb("Stack.draw: dividebins=%r"%(dividebins),verbosity,2)
      datahists = [self.datahist]
      for hlist in [datahists,self.exphists,self.sighists]:
        for i, oldhist in enumerate(hlist):
          dograph = (oldhist==self.datahist) # only create graph for observed data histogram
          newhist = dividebybinsize(oldhist,zero=True,zeroerrs=False,errorX=errorX,graph=dograph,verb=verbosity)
          if dograph and oldhist!=newhist:
            LOG.verb("Stack.draw: replace %s -> %s"%(oldhist,newhist),verbosity,2)
            hlist[i] = newhist
            #if oldhist in self.hists:
            #  self.hists[self.hists.index(oldhist)] = newhist
            self.garbage.append(oldhist)
      if self.datahist:
        self.datahist = datahists[0]
        self.hists = [self.datahist]+self.exphists+self.sighists
      else: # do not include data hists
        self.hists = self.exphists+self.sighists
      #if sysvars:
      #  histlist = sysvars.values() if isinstance(sysvars,dict) else sysvars
      #  for (histup,hist,histdown) in histlist:
      #    dividebybinsize(histup,  zero=True,zeroerrs=False,verb=verbosity-2)
      #    dividebybinsize(histdown,zero=True,zeroerrs=False,verb=verbosity-2)
      #    if hist not in self.hists:
      #      dividebybinsize(hist,zero=True,zeroerrs=False,verb=verbosity-2)
    
    # RESET XMIN & BINNING
    if logx and xmin==0: # reset xmin in binning if logx
      frame = self.frame or self.exphists[0] or self.datahist
      xmin = 0.35*frame.GetXaxis().GetBinWidth(1)
      xbins = getbinning(frame,xmin,xmax,variable=True,verb=verbosity) # new binning with xmin>0
      LOG.verb("Plot.draw: Resetting xmin=0 -> %s in binning of all histograms (logx=%r, frame=%r): xbins=%r"%(
        xmin,logx,frame,xbins),verbosity,1)
      for hist in self.exphists+self.sighists+[self.datahist]:
        if hist and isinstance(hist,TH1):
          hist.SetBins(*xbins) # set xmin>0 to plot correctly with logx
      if self.frame and self.frame.GetXaxis().GetXmin()<=0.0:
        self.frame = None # use getframe below
    
    # DRAW OPTIONS
    gStyle.SetEndErrorSize(enderrorsize) # extra line at end of error bars
    gStyle.SetErrorX(0.5*float(errorX)) # horizontal error bars
    LOG.verb("Stack.draw: enderrorsize=%r, errorX=%r"%(enderrorsize,errorX),verbosity,2)
    
    # CANVAS
    self.canvas = self.setcanvas(square=square,lower=lowerpanels,width=cwidth,height=cheight,
                                 lmargin=lmargin,rmargin=rmargin,tmargin=tmargin,bmargin=bmargin)
    
    # STYLE
    self.setfillstyle(self.exphists,reset=resetcolors) # before adding to THStack!
    for hist in self.exphists:
      hist.SetMarkerStyle(1)
    if drawsignal:
      self.setlinestyle(self.sighists,colors=lcolors,styles=lstyles,mstyle=mstyle,width=lwidth,pair=pair,triple=triple)
    #if drawdata:
    #  self.setmarkerstyle(self.datahist)
    
    # CREATE STACK
    stack = THStack(makehistname('stack',self.name),"") # stack (expected)
    self.stack = stack
    if reverse: # stack bottom to bottom top; reversed w.r.t. legend
      for hist in self.exphists:
        stack.Add(hist)
    else: # stack top to bottom to match order in legend
      for hist in reversed(self.exphists):
        stack.Add(hist)
    
    # DRAW FRAME
    mainpad = self.canvas.cd(1)
    if not self.frame: # if not given by user
      self.frame = getframe(mainpad,self.exphists[0],xmin,xmax,variable=True)
      self.frame.Draw('][') # 'AXIS' breaks grid in combination with TGraph sometimes !?
    else:
      self.frame.Draw('AXIS ][') # 'AXIS' breaks grid in combination with TGraph sometimes !?
    LOG.verb("Plot.draw: Drawn frame=%r"%(self.frame),verbosity,2)
    
    # DRAW LINE
    for line in self.lines:
      if line.pad==1:
        line.Draw(line.option)
    for box in self.boxes:
      if box.pad==1:
        box.Draw(box.option)
    
    # DRAW
    LOG.verb("Stack.draw: Drawing stack %r with option=%r"%(stack,option+' SAME'),verbosity,2)
    stack.Draw(option+' SAME')
    if drawsignal: # signal
      soption += " SAME"
      for hist in self.sighists:
        LOG.verb("Stack.draw: draw signal %r with soption=%r"%(hist,soption),verbosity,2)
        hist.Draw(soption)
        hist.SetOption(soption) # for legend and ratio
    if drawdata: # data
      self.datahist.SetFillStyle(0)
      if not isinstance(self.datahist,TH1):
        doption += 'PE0'
      doption += ' SAME'
      LOG.verb("Stack.draw: Drawing data %r with doption=%r"%(self.datahist,doption),verbosity,2)
      self.datahist.Draw(doption+' SAME')
      self.datahist.SetOption(doption+' SAME') # for legend and ratio (NOTE: TGraph.SetOption defined in utils.py)
    
    # CMS STYLE
    if CMSStyle.lumiText:
      CMSStyle.setCMSLumiStyle(mainpad,0,verb=verbosity-2)
    
    # ERROR BAND
    boption = 'E2 SAME'
    if staterr or sysvars:
      self.errband = geterrorband(self.exphists,name=makehistname("errband",self.name),title=errtitle,sysvars=sysvars)
      if not multibands: # do not draw, but keep for ratio and/or legend
        LOG.verb("Stack.draw: Drawing errorband %r with boption=%r"%(self.errband,boption),verbosity,2)
        self.errband.Draw(boption)
    if multibands:
      for i, hist in enumerate(self.exphists):
        fstyle = 3004 if i%2==0 else 3005
        errband = geterrorband(hist,yhist=stack.GetStack().At(i),name=makehistname("errband",hist),title=errtitle,style=fstyle)
        LOG.verb("Stack.draw: Drawing errorband %r with boption=%r"%(self.errband,boption),verbosity,2)
        errband.Draw(boption)
        self.errbands.append(errband)
    
    # AXES
    drawx = not bool(ratio)
    self.setaxes(self.frame,*self.hists,drawx=drawx,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,logy=logy,logx=logx,main=ratio,grid=grid,nxdiv=nxdiv,nydiv=nydiv,
                 xtitle=xtitle,ytitle=ytitle,xtitlesize=xtitlesize,ytitlesize=ytitlesize,ytitleoffset=ytitleoffset,xtitleoffset=xtitleoffset,
                 xlabelsize=xlabelsize,ylabelsize=ylabelsize,binlabels=binlabels,labeloption=labeloption,
                 dividebins=dividebins,latex=latex,center=ycenter,ymargin=ymargin,logyrange=logyrange)
    
    # RATIO
    if ratio:
      drawx = (lowerpanels<=1)
      lines = [l for l in self.lines if l.pad==2] # draw first
      boxes = [b for b in self.boxes if b.pad==2] # draw first
      self.canvas.cd(2) # go to ratio panel
      if rhists==None: # if not set by user, use default
        rhists = [stack]+self.sighists+[self.datahist] # default: use stack as denominator (denom=1)
      else: # histograms for ratio set by user
        while 'stack' in rhists: # replace 'stack' string with actual THStack object
          rhists[rhists.index('stack')] = stack
        while 'data' in rhists: # replace 'data' string with actual TH1/TGraph object
          rhists[rhists.index('data')] = self.datahist
      self.ratio = Ratio(*rhists,denom=denom,num=num,errband=self.errband,
                         drawzero=True,errorX=errorX,fraction=fraction,verb=verbosity)
      self.ratio.draw(xmin=xmin,xmax=xmax,data=True,lines=lines,boxes=boxes)
      self.setaxes(self.ratio,drawx=drawx,xmin=xmin,xmax=xmax,ymin=rmin,ymax=rmax,logx=logx,nxdiv=nxdiv,nydiv=nrdiv,
                   xtitle=xtitle,ytitle=rtitle,xtitlesize=xtitlesize,ytitlesize=rtitlesize,xtitleoffset=xtitleoffset,ytitleoffset=rtitleoffset,
                   xlabelsize=xlabelsize,ylabelsize=ylabelsize,binlabels=binlabels,labeloption=labeloption,
                   center=True,rrange=ratiorange,grid=grid,latex=latex)
      self.canvas.cd(1) # go back to main pad
