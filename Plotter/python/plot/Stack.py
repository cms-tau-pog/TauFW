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
    - datahist: single TH1 or TGraph object
    - exphists: list of TH1s for expected processes
    - sighists: list of TH1s for signals
    """
    self.verbosity = LOG.getverbosity(kwargs)
    #variable       = None
    #hists          = None
    #if len(args)==1 and islist(args[0]):
    #  hists        = None
    #elif len(args)==2:
    #  variable     = args[0]
    #  hists        = args[1]
    #else:
    #  LOG.throw(IOError,"Plot: Wrong input %s"%(args))
    self.datahist   = datahist
    self.exphists   = ensurelist(exphists)
    self.sighists   = ensurelist(sighists)
    if kwargs.get('clone',False):
      self.datahist = self.datahist.Clone(self.datahist.GetName()+"_clone_Stack")
      self.exphists = [h.Clone(h.GetName()+"_clone_Stack") for h in self.exphists]
      self.sighists = [h.Clone(h.GetName()+"_clone_Stack") for h in self.sighists]
    self.hists      = [self.datahist]+self.exphists+self.sighists
    kwargs['clone'] = False
    self.ratio      = kwargs.setdefault('ratio', True )
    super(Stack,self).__init__(variable,self.hists,**kwargs)
    
  
  def draw(self,*args,**kwargs):
    """Central method of Plot class: make plot with canvas, axis, error, ratio..."""
    # https://root.cern.ch/doc/master/classTHStack.html
    # https://root.cern.ch/doc/master/classTHistPainter.html#HP01e
    verbosity    = LOG.getverbosity(self,kwargs)
    xtitle       = (args[0] if args else self.xtitle) or ""
    ratio        = kwargs.get('ratio',        self.ratio      ) # make ratio plot
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
    errtitle     = kwargs.get('errtitle',     None            ) # title for error band
    norm         = kwargs.get('norm',         self.norm       ) # normalize all histograms
    xtitle       = kwargs.get('xtitle',       xtitle          ) # x axis title
    ytitle       = kwargs.get('ytitle',       self.ytitle     ) # y axis title (if None, automatically set by Plot.setaxis)
    rtitle       = kwargs.get('rtitle',       "Obs. / Exp."   ) # y axis title of ratio panel
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
    ytitleoffset = kwargs.get('ytitleoffset', 1.0             )
    xtitleoffset = kwargs.get('xtitleoffset', 1.0             )*bmargin
    xlabelsize   = kwargs.get('xlabelsize',   _lsize          ) # x label size
    ylabelsize   = kwargs.get('ylabelsize',   _lsize          ) # y label size
    logx         = kwargs.get('logx',         self.logx       )
    logy         = kwargs.get('logy',         self.logy       )
    ymargin      = kwargs.get('ymargin',      self.ymargin    ) # margin between hist maximum and plot's top
    logyrange    = kwargs.get('logyrange',    self.logyrange  ) # log(y) range from hist maximum to ymin
    grid         = kwargs.get('grid',         False           )
    tsize        = kwargs.get('tsize',        _tsize          ) # text size for axis title
    pair         = kwargs.get('pair',         False           )
    triple       = kwargs.get('triple',       False           )
    ncols        = kwargs.get('ncols',        1               ) # number of columns in legend
    lcolors      = kwargs.get('lcolors',      None            ) or self.lcolors
    fcolors      = kwargs.get('fcolors',      None            ) or self.fcolors
    lstyles      = kwargs.get('lstyle',       None            )
    lstyles      = kwargs.get('lstyles',      lstyles         ) or self.lstyles
    lwidth       = kwargs.get('lwidth',       2               ) # line width
    mstyle       = kwargs.get('mstyle',       None            ) # marker style
    option       = kwargs.get('option',       'HIST'          ) # draw option
    doption      = kwargs.get('doption',      'E1'            ) # draw option for data
    roption      = kwargs.get('roption',      None            ) # draw option of ratio plot
    enderrorsize = kwargs.get('enderrorsize', 2.0             ) # size of line at end of error bar
    errorX       = kwargs.get('errorX',       False           ) # no horizontal error bars for CMS style
    dividebins   = kwargs.get('dividebins',   self.dividebins ) # divide each histogram bins by it bin size
    drawdata     = kwargs.get('drawdata',     True            ) and bool(self.datahist)
    drawsignal   = kwargs.get('drawsignal',   True            ) and bool(self.sighists)
    lcolors      = ensurelist(lcolors)
    fcolors      = ensurelist(fcolors)
    lstyles      = ensurelist(lstyles)
    self.ratio   = ratio
    self.lcolors = lcolors
    self.fcolors = fcolors
    self.lstyles = lstyles
    hists        = self.hists
    
    # DIVIDE BY BINSIZE
    if dividebins:
      datahists = [self.datahist]
      for hlist in [datahists,self.exphists,self.sighists]:
        for i, oldhist in enumerate(hlist):
          newhist = dividebybinsize(oldhist,zero=True,zeroerrs=False,errorX=errorX)
          if oldhist!=newhist:
            LOG.verb("Plot.draw: replace %s -> %s"%(oldhist,newhist),verbosity,2)
            hlist[i] = newhist
            #if oldhist in self.hists:
            #  self.hists[self.hists.index(oldhist)] = newhist
            self.garbage.append(oldhist)
      self.datahist = datahists[0]
      self.hists    = [self.datahist]+self.exphists+self.sighists
      #if sysvars:
      #  histlist = sysvars.values() if isinstance(sysvars,dict) else sysvars
      #  for (histup,hist,histdown) in histlist:
      #    dividebybinsize(histup,  zero=True,zeroerrs=False)
      #    dividebybinsize(histdown,zero=True,zeroerrs=False)
      #    if hist not in self.hists:
      #      dividebybinsize(hist,zero=True,zeroerrs=False)
    
    # DRAW OPTIONS
    gStyle.SetEndErrorSize(enderrorsize)
    if errorX:
      gStyle.SetErrorX(0.5)
    else:
      gStyle.SetErrorX(0) # 'XE0' should also work
    
    # CANVAS
    self.canvas = self.setcanvas(square=square,lower=ratio,width=cwidth,height=cheight,
                                 lmargin=lmargin,rmargin=rmargin,tmargin=tmargin,bmargin=bmargin)
    
    # CREATE STACK
    stack = THStack(makehistname('stack',self.name),"") # stack (expected)
    self.stack = stack
    for hist in reversed(self.exphists): # stacked bottom to top
      stack.Add(hist)
    
    # DRAW FRAME
    self.canvas.cd(1)
    if not self.frame: # if not given by user
      self.frame = getframe(gPad,stack,xmin,xmax)
      #self.frame.Draw('AXIS') # 'AXIS' breaks GRID?
    else:
      self.frame.Draw('AXIS') # 'AXIS' breaks GRID?
    
    # DRAW LINE
    for line in self.lines:
      if line.pad==1:
        line.Draw("LSAME")
    
    # DRAW
    stack.Draw('HIST SAME')
    if drawsignal: # signal
      for hist in self.sighists:
        hist.Draw(option+" SAME")
        hist.SetOption(option+" SAME") # for legend and ratio
    if drawdata: # data
      self.datahist.SetFillStyle(0)
      if isinstance(self.datahist,TH1):
        self.datahist.Draw(doption+' SAME')
        self.datahist.SetOption(doption+' SAME') # for legend and ratio
      else:
        self.datahist.Draw(doption+'PE0 SAME')
        self.datahist.GetOption = lambda: 'PE0 SAME' # for legend and ratio
    
    # STYLE
    if stack:
      self.setfillstyle(self.exphists)
      for hist in self.exphists:
        hist.SetMarkerStyle(1)
    if drawsignal:
      self.setlinestyle(self.sighists,colors=lcolors,styles=lstyles,mstyle=mstyle,width=lwidth,pair=pair,triple=triple)
    if drawdata:
      self.setmarkerstyle(self.datahist)
    
    # CMS STYLE
    if CMSStyle.lumiText:
      CMSStyle.setCMSLumiStyle(gPad,0)
    
    # ERROR BAND
    if staterr or sysvars:
      self.errband = geterrorband(self.exphists,name=makehistname("errband",self.name),title=errtitle,sysvars=sysvars)
      self.errband.Draw('E2 SAME')
    
    # AXES
    self.setaxes(self.frame,*hists,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,logy=logy,logx=logx,main=ratio,
                 xtitle=xtitle,ytitle=ytitle,ytitleoffset=ytitleoffset,xlabelsize=xlabelsize,xtitleoffset=xtitleoffset,
                 binlabels=binlabels,labeloption=labeloption,ymargin=ymargin,logyrange=logyrange,grid=grid,latex=latex)
    
    # RATIO
    if ratio:
      self.canvas.cd(2)
      histden    = stack
      histnums   = [self.datahist]+self.sighists
      self.ratio = Ratio(histden,histnums,errband=self.errband,drawzero=True,errorX=errorX,option=roption)
      self.ratio.draw(xmin=xmin,xmax=xmax,data=True)
      self.setaxes(self.ratio,xmin=xmin,xmax=xmax,ymin=rmin,ymax=rmax,logx=logx,center=True,nydiv=506,
                   binlabels=binlabels,labeloption=labeloption,xlabelsize=xlabelsize,xtitleoffset=xtitleoffset,
                   rrange=ratiorange,xtitle=xtitle,ytitle=rtitle,grid=grid,latex=latex)
      for line in self.lines:
        if line.pad==2:
          line.Draw("LSAME")
      self.canvas.cd(1)
    

#def isListOfHists(args):
#  """Help function to test if list of arguments is a list of histograms."""
#  if not islist(args):
#    return False
#  for arg in args:
#    if not (isinstance(arg,TH1) or isinstance(arg,TGraphAsymmErrors)):
#      return False
#  return True
  

# def unwrapHistogramLists(*args):
#   """Help function to unwrap arguments for initialization of Plot object in order:
#      1) variable, 2) data, 3), backgrounds, 4) signals."""
#   args = list(args)
#   variable = None
#   varname  = ""
#   binning  = [ ]
#   for arg in args[:]:
#     if isinstance(arg,Variable) and not variable:
#       variable = arg
#       args.remove(arg)
#       break
#     if isinstance(arg,str):
#       varname = arg
#       args.remove(arg)
#     if isNumber(arg):
#       args.remove(arg)
#       binning.append(arg)
#   if not variable and len(binning)>2:
#     variable(varname,*binning[:3])
#   
#   if isListOfHists(args):
#       return variable, [ ], args, [ ]
#   if len(args)==1:
#     if isListOfHists(args[0]):
#       return variable, [ ], args[0], [ ]
#   if len(args)==2:
#     args0 = args[0]
#     if isListOfHists(args[0]) and len(args[0])==1:
#       args0 = args0[0]
#     if isinstance(args0,TH1) and isListOfHists(args[1]):
#       return variable, [args0], args[1], [ ]
#   if len(args)==3:
#     if args[0]==None: args[0] = [ ]
#     if isinstance(args[0],TH1) and isListOfHists(args[1]) and isListOfHists(args[2]):
#       return variable, [args[0]], args[1], args[2]
#     if isListOfHists(args[0]) and isListOfHists(args[1]) and isListOfHists(args[2]):
#       return variable, args[0], args[1], args[2]
#   print error('unwrapHistogramLists: Could not unwrap "%s"'%(args))
#   exit(1)

