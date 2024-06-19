#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import os, sys, re, glob
import numpy, copy
from array import array
from argparse import ArgumentParser
from plotParabola_POI_region import measurepoi, ensureDirectory, ensureTFile
from ROOT import gROOT, gPad, gStyle, TFile, TCanvas, TLegend, TLatex, TF1, TH2F, TGraph, TLine, TColor,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, kBlackBody, kTemperatureMap
from TauFW.Plotter.sample.utils import CMSStyle
from math import sqrt, log, ceil, floor
from itertools import combinations
import yaml

gROOT.SetBatch(True)
#gROOT.SetBatch(False)
gStyle.SetOptTitle(0)


DIR_DC      = "input"

# CMS style
CMSStyle.setTDRStyle()

# COLOR palette, see core/base/src/TColor.cxx
red   = array('d',[ 0.80, 0.90, 1.00, 0.60, 0.02, ])
green = array('d',[ 0.20, 0.80, 1.00, 0.80, 0.20, ])
blue  = array('d',[ 0.10, 0.60, 1.00, 0.90, 0.65, ])
stops = array('d',[i/(len(red)-1.) for i in xrange(0,len(red))])
FI    =  TColor.CreateGradientColorTable(len(red), stops, red, green, blue, 100)
kMyTemperature = array('i',[ FI+i for i in xrange(100)])
gStyle.SetPalette(100,kMyTemperature)

DIR         = "output"
PLOTS_DIR   = "postfit"

def plotCorrelation(channel,var,region,year,*parameters,**kwargs):
    """Calculate and plot correlation between parameters."""
    print green("\n>>> plotCorrelation %s, %s"%(region, var))
    if len(parameters)==1 and isinstance(parameters[0],list): parameters = parameters[0]
    parameters  = [p.replace('$CAT',region).replace('$CHANNEL',channel) for p in list(parameters)]
    
    title       = kwargs.get('title',     ""                )
    name        = kwargs.get('name',      ""                )
    indir       = kwargs.get('indir',     "output_%s"%year  )
    outdir      = indir.replace('output', 'postfit') #kwargs.get('outdir',    "postfit_%s"%year )
    tag         = kwargs.get('tag',       ""                )
    plotlabel   = kwargs.get('plotlabel', ""                )
    order       = kwargs.get('order',     False             )
    poi         = kwargs.get('poi',       ""                )
    era         = "%s-13TeV"%year
    filename    = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,region,tag,era)
    ensureDirectory(outdir)
    print '>>>Plotcorelation   file "%s"'%(filename)

    tes         = measurepoi(filename,poi, region=region)
    tes_name = "%s_%s"%(poi,region) #combine DM
    # HISTOGRAM
    parlist = getParameters(filename,parameters)
    if order:
      parlist.sort(key=lambda x: -x.sigma)
    N       = len(parlist)     
    hist    = TH2F("corr","corr",N,0,N,N,0,N)
    
    iPOI = -1 # save position of POI (here: TES)
    for i in xrange(N): # diagonal
      hist.SetBinContent(i+1,N-i,1.0)
      hist.GetXaxis().SetBinLabel(1+i,parlist[i].title)
      hist.GetYaxis().SetBinLabel(N-i,parlist[i].title)
      #if parlist[i].title == "tes":
      if parlist[i].title == tes_name:  
          iPOI = i
    for xi, yi in combinations(range(N),2): # off-diagonal
      r = parlist[xi].corr(parlist[yi],tes,parlist[iPOI])
      hist.SetBinContent(1+xi,N-yi,r)
      hist.SetBinContent(1+yi,N-xi,r)
      #print "%20s - %20s: %5.3f"%(par1,par2,r)
      #hist.Fill(par1.title,par2.title,r)
      #hist.Fill(par2.title,par1.title,r)
    
    # SCALE
    canvasH  = 160+64*max(10,N)
    canvasW  = 300+70*max(10,N)
    scaleH   =  800./canvasH
    scaleW   = 1000./canvasW
    scaleF   = 640./(canvasH-160)
    tmargin  = 0.06
    bmargin  = 0.14
    lmargin  = 0.22
    rmargin  = 0.12
    
    canvas = TCanvas('canvas','canvas',100,100,canvasW,canvasH)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  tmargin ); canvas.SetBottomMargin( bmargin )
    canvas.SetLeftMargin( lmargin ); canvas.SetRightMargin( rmargin )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    
    frame = hist
    frame.GetXaxis().SetLabelSize(0.054*scaleF)
    frame.GetYaxis().SetLabelSize(0.072*scaleF)
    frame.GetZaxis().SetLabelSize(0.034)
    frame.GetXaxis().SetLabelOffset(0.005)
    frame.GetYaxis().SetLabelOffset(0.003)
    frame.GetXaxis().SetNdivisions(508)
    #gStyle.SetPalette(kBlackBody)
    #frame.SetContour(3);
    gStyle.SetPaintTextFormat(".2f")
    frame.SetMarkerSize(1.5*scaleF)
    #frame.SetMarkerColor(kRed)
    
    hist.Draw('COLZ TEXT')
    
    # TEXT
    if title:
      latex = TLatex()
      latex.SetTextSize(0.045)
      latex.SetTextAlign(33)
      latex.SetTextFont(42)
      latex.DrawLatexNDC(0.96*lmargin,0.80*bmargin,title)
    
    CMSStyle.setCMSLumiStyle(canvas,0)
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvasname = "%s/postfit-correlation_%s_%s%s%s"%(outdir,var,region,tag,plotlabel)
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".root")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    


def getParameters(filename,*parameters,**kwargs):
    """Make lists for parameters."""
    if len(parameters)==1 and isinstance(parameters[0],list): parameters = parameters[0]
    file      = TFile(filename)
    tree      = file.Get('limit')
    N         = tree.GetEntries()
    #tree.GetListOfBranches()
    parlist = [ ]
    for parameter in parameters:
      branch = parameter
      #print branch
      # TODO: regex
      if not tree.GetBranch(branch):
        warning('getListsForParameters: Did not find "%s" branch!'%(branch))
        continue
      parlist.append(Parameter(branch))
    for event in tree:
      for parameter in parlist:
        parameter.append(getattr(event,parameter.name))
    for parameter in parlist:
      parameter.set()
    return parlist
    


def writeParametersFitVal(channel,var,region,year,*parameters,**kwargs):
    """Write the value of the parameter after the fit in a txt file"""
    print green("\n>>> Write parameter %s, %s"%(region, var))

    # define the parameter
    if len(parameters)==1 and isinstance(parameters[0],list): parameters = parameters[0]
    parameters  = [p.replace('$CAT',region).replace('$CHANNEL',channel) for p in list(parameters)]
    print(parameters)


    # get variables
    indir       = kwargs.get('indir',     "output_%s"%year  )
    tag         = kwargs.get('tag',       ""                )
    poi         = kwargs.get('poi',       ""                )
    era         = "%s-13TeV"%year
    filename    = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,region,tag,era)
    outdir      = indir.replace('output', 'postfit') #kwargs.get('outdir',    "postfit_%s"%year )
    outfile = "%s/FitparameterValues_%s_%s_%s.txt" %(outdir,tag,era,region)
    
    # remove file to not append to it 
    if os.path.exists(outfile):
        os.remove(outfile)

    ensureDirectory(outdir)

    # Get tes values
    tes         = measurepoi(filename,poi, region=region)
    tes_name = "%s_%s"%(poi,region) #combine DM
    
    # Get the lsit of parameter
    parameters  = [p.replace('$CAT',region).replace('$CHANNEL',channel) for p in list(parameters)]
    parlist = getParameters(filename,parameters)

    print(parlist)

    parVal = 0 
    N = len(parlist) # Number of parameters 
    iPOI = -1 # save position of POI in the parlist(here: TES)

    for ipar in range(N):
      if parlist[ipar].title == tes_name:  
        iPOI = ipar

    for ipar in range(N):
      parVal = parlist[ipar].getfitVal(tes,parlist[iPOI])
      print("%s : %s" %(parlist[ipar].title,parVal )) 
      # Write parameter title and value for each region to outdir
      with open(outfile, 'a') as file:
        file.write("%s : %s\n" %(parlist[ipar].title,parVal ))
        print("Writing in file %s" %(outfile))


    file.close()


class Parameter(object):
    """Parameter."""
    
    def __init__(self, name, varlist=None, **kwargs):
        self.name  = name
        self.title = formatParameter(name)
        self.list  = varlist if varlist else [ ]
        self.N     = None
        self.mean  = None
        self.sigma = None
        self.fitVal = None
        
    def __str__(self):
        return self.title
        
    def append(self,val):
        self.list.append(val)
        
    def set(self):
        self.N     = len(self.list)
        self.mean  = sum(self.list) / float(self.N)
        self.sigma = sqrt(sum((x-self.mean)**2 for x in self.list)/float(self.N-1)) 
    def corr(self,opar,poiBestFit,poi):
        """Correlation coefficient with another parameter."""
        covariance = 0
        N = 0
        for x, y, z in zip(self.list,opar.list,poi.list):
            # only consider points within 2 sigma range of tes around its min
            # assume best fit-value of tes is 1
            if abs(z-poiBestFit) < poi.sigma:
                covariance += (x-self.mean)*(y-opar.mean)
                N +=1
        covariance /= float(N-1)
        return covariance/(self.sigma*opar.sigma)
        
    def getfitVal(self,poiBestFit,poi):
        for paramVal, poiVal in zip(self.list,poi.list):
          #print("poiVal = ", poiVal)
          #print("poiBestFit = ", poiBestFit)
          if poiVal == poiBestFit :
            self.fitVal = paramVal
        #print(self.title, self.fitVal)
        return self.fitVal



def plotPostFitValues(channel,var,region,year,paramfull_list,*parameters,**kwargs):
    """Draw post-fit values for parameter using MultiDimFit and FitDiagnostics output."""
    print green("\n>>> plotPostFitValues %s, %s"%(region, var))
    if len(parameters)==1 and isinstance(parameters[0],list): parameters = parameters[0]
    
    parameters  = [p.replace('$CAT',region).replace('$CHANNEL',channel) for p in list(parameters)]

    
    title       = kwargs.get('title',     ""    )
    name        = kwargs.get('name',      ""    )
    indir       = kwargs.get('indir',     "output_%s"%year  )
    outdir      = indir.replace('output', 'postfit') #kwargs.get('outdir',    "postfit_%s"%year )
    tag         = kwargs.get('tag',       ""    )
    plotlabel   = kwargs.get('plotlabel', ""    )
    poi         = kwargs.get('poi',       ""    )
    compareFD   = kwargs.get('compareFD', False ) and N==1
    era         = "%s-13TeV"%year
    isBBB       = any("_bin_" in p for p in parameters)
    filename    = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,region,tag,era)
    filenamesFD = '%s/fitDiagnostics.%s_%s-%s%s-%s_TES*p*.root'%(indir,channel,var,region,tag,era)
    ensureDirectory(outdir)
    if not name:
      name = formatParameter(parameters[0]).replace('_'+region,'')
    if len(parameters)>1:
      name = "comparison_%s"%(name) #re.sub(r"bin_\d+","bin",name)
    canvasname = "%s/postfit-%s_%s_%s%s%s"%(outdir,name,var,region,tag,plotlabel)
    print '>>>   file "%s"'%(filename)

    
    graphs      = [ ]
    graphsFD    = [ ]
    tvals       = [ ]
    pvals       = [ -2.2, +2.2 ]
    tes         = measurepoi(filename,poi, region=region)
    tes_name = "%s_%s"%(poi,region) #combine DM
    for parameter in parameters[:]:
      #graph = getTGraphOfParameter(filename,'tes',parameter,xvals=tvals,yvals=pvals)
      graph = getTGraphOfParameter(filename,tes_name,parameter,xvals=tvals,yvals=pvals) # combine DM
      if graph:
        graphs.append(graph)
      else:
        parameters.remove(parameter)
      if compareFD:
        graphFD = getTGraphOfParameter_FD(filenamesFD,parameter,xvals=tvals,yvals=pvals)
        if graphFD: graphsFD.append(graphFD)    
    if len(parameters)!=len(graphs):
      warning("plotPostFitValues: len(parameters) = %d != %d = len(graphs)"%(len(parameters),len(graphs)))
      exit(1) 
    N           = len(parameters)
    compareFD   = compareFD and len(graphsFD)>0
    #parameters  = [formatParameter(p).replace('_'+region,'') for p in parameters]
    graphsleg   = columnize(graphs,3)     if N>6 else columnize(graphs,2)     if N>3 else graphs # reordered for two columns
    paramsleg   = columnize(parameters,3) if N>6 else columnize(parameters,2) if N>3 else parameters # reordered for two columns
    
    if poi == 'tes':
      xtitle  = 'tau energy scale'
    if poi == 'tid_SF':
      xtitle  = 'tau identification scale factor'
    ytitle  = "%s post-fit value"%(parameters[0] if N==1 else "MultiDimFit")
    print('*tvals: ', tvals)
    print('*pvals: ', pvals)
    xmin, xmax = min(tvals), max(tvals)
    ymin, ymax = min(pvals), max(pvals)
    colors  = [ kBlack, kBlue, kRed, kGreen, kMagenta, kOrange, kTeal, kAzure+2, kYellow-3 ]
    
    canvas = TCanvas("canvas","canvas",100,100,800,650)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.13 )
    canvas.SetLeftMargin( 0.11 ); canvas.SetRightMargin(  0.05 )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    
    maxmargin = 0.18*abs(ymax-ymin)
    minmargin = 0.20*abs(ymax-ymin) #(0.20 if N<5 else 0.10*ceil(N/2))
    ymin   = 0.0 if ymin>=0 else ymin-minmargin
    ymax   = ymax + minmargin
    
    textsize   = 0.045 if N==1 else 0.036
    lineheight = 0.055 if N==1 else 0.045
    x1, width  = 0.42, 0.25
    y1, height = 0.15, lineheight*(ceil(N/3.) if N>6 else ceil(N/2.) if N>3 else N)
    if title:     height += lineheight
    if compareFD: height += lineheight
    if   N>6:
      if isBBB: width = 0.62; x1 = 0.25
      else:     width = 0.70; x1 = 0.20
    elif N>3:   width = 0.52; x1 = 0.36
    legend = TLegend(x1,y1,x1+width,y1+height)
    legend.SetTextSize(textsize)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)
    if title:
      legend.SetTextFont(62)
      legend.SetHeader(title) 
    legend.SetTextFont(42)
    if N>6:
      legend.SetNColumns(3)
      legend.SetColumnSeparation(0.02)
    elif N>3:
      legend.SetNColumns(2)
      legend.SetColumnSeparation(0.03)
    
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.050)
    frame.GetXaxis().SetLabelOffset(0.01)
    frame.GetYaxis().SetLabelOffset(0.01)
    frame.GetXaxis().SetTitleOffset(0.98)
    frame.GetYaxis().SetTitleOffset(0.84)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetXaxis().SetTitle(xtitle)
    
    for i, (parameter,graph) in enumerate(zip(parameters,graphs)):
      graph.SetLineColor(colors[i%len(colors)])
      graph.SetLineWidth(2)
      graph.SetLineStyle(1)
      graph.Draw('LSAME')
    
    for parameter,graph in zip(paramsleg,graphsleg):
      if N==1:
        legend.AddEntry(graph, "MultiDimFit", 'l')
      else:
        legend.AddEntry(graph, parameter, 'l')
    if tes_name not in paramfull_list: paramfull_list.append(tes_name) 
    parlist = getParameters(filename,paramfull_list)

    latex = TLatex()
    # Get aprameter value 
    paramVal = 0 
    N = len(parlist) # Number of parameters 
    iPOI = -1 # save position of POI in the parlist(here: TES)

    for ipar in range(N):
      print("parlist[ipar].title = ",parlist[ipar].title  )
      print("tes_name = ", tes_name)
      if parlist[ipar].title == tes_name:  
          iPOI = ipar
          print("iPOI= ",iPOI)

    for ipar in range(N):
      if parlist[ipar].title == parameter:
        parVal = parlist[ipar].getfitVal(tes,parlist[iPOI])
        print("%s : %s" %(parlist[ipar].title,parVal )) 
        latex.DrawLatex(tes-0.04*(xmax-xmin),ymax-0.09*(ymax-ymin),parameter+" = %.3f"%parVal) #combine DM


    line = TLine(tes, ymin, tes, ymax)
    #line.SetLineWidth(1)
    line.SetLineStyle(7)
    line.Draw('SAME')
    latex.SetTextSize(0.045)
    latex.SetTextAlign(13)
    latex.SetTextFont(42)
    #latex.DrawLatex(tes+0.02*(xmax-xmin),ymax-0.04*(ymax-ymin),"tes = %.3f"%tes)
    latex.DrawLatex(tes-0.04*(xmax-xmin),ymax-0.03*(ymax-ymin),tes_name+" = %.3f"%tes) #combine DM
    # latex.DrawLatex(0.920,1.2,tes_name+" = %.3f"%tes) #combine DM  
    # latex.DrawLatex(0.920,0.2,parameter+" = %s"%paramVal) #combine DM

    if compareFD:
      graphFD.SetLineColor(kBlue)
      graphFD.SetLineWidth(2)
      graphFD.SetLineStyle(2)
      graphFD.Draw('LSAME')
      legend.AddEntry(graphFD, "FitDiagnostics", 'l')
    
    legend.Draw()
    
    CMSStyle.setCMSLumiStyle(canvas,0)	
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".root")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    

def getTGraphOfParameter(filename,xbranch,ybranch,**kwargs):
    """Make TGraph with xbranch vs. ybranch."""
    xvals  = kwargs.get('xvals',[ ])
    yvals  = kwargs.get('yvals',[ ])
    file   = TFile(filename)
    tree   = file.Get('limit')
    N      = tree.GetEntries()
    graph  = TGraph(N)
    if not tree.GetBranch(xbranch):
      warning('getTGraphOfParameter: Did not find "%s" branch!'%(xbranch))
      return None
    if not tree.GetBranch(ybranch):
      warning('getTGraphOfParameter: Did not find "%s" branch!'%(ybranch))
      return None
    xyvals = [ (getattr(e,xbranch),getattr(e,ybranch)) for e in tree ]
    xyvals = sorted(xyvals,key=lambda p: p[0])
    for i, (x,y) in enumerate(xyvals):
      graph.SetPoint( i, x, y )
      if x not in xvals:
        xvals.append(x)
      yvals.append(y)
    return graph
    

def getTGraphOfParameter_FD(filepattern,ybranch,**kwargs):
    """Make TGraph from fitDiagnostics files."""
    xvals     = kwargs.get('xvals',[ ])
    yvals     = kwargs.get('yvals',[ ])
    filenames = sorted(glob.glob(filepattern))
    N         = len(filenames)
    graph     = TGraph(N)
    if N<3:
      print 'Error! getTGraphOfParameter_FD: Did not get more than two "%s" files (%d)'%(filepattern,N)
      return None
    for i, filename in enumerate(filenames):
      tes  = getTES(filename)
      if tes==None: continue
      file = TFile(filename)
      tree = file.Get('tree_fit_sb')
      if not tree.GetBranch(ybranch):
        warning('getTGraphOfParameter: Did not find "%s" branch!'%(ybranch))
        return None
      tree.GetEntry(0)
      x, y = tes, getattr(tree,ybranch)
      graph.SetPoint( i, x, y )
      if x not in xvals:
        xvals.append(x)
      yvals.append(y)
    return graph

def formatParameter(param):
    """Helpfunction to format nuisance parameter."""
    param = param.replace("CMS_","").replace("ttbar_","").replace("ztt_","").replace("_mt_13TeV","").replace("_mt","").replace("_13TeV","")
    return param
    
def getTES(string):
    matches = re.findall("_TES(\dp\d*)",string)
    if not matches:
      print 'Error! getTES: Did not find valid patttern to extract TES from "%s"'%(string)
      return None
    return float(matches[0].replace('p','.'))
    
def columnize(list,ncol=2):
    """Transpose lists into n columns, e.g. [1,2,3,4,5,6,7] -> [1,5,2,6,3,7,4] for ncol=2."""
    parts   = partition(list,ncol)
    collist = [ ]
    row     = 0
    while len(collist)<len(list):
      for part in parts:
        if row<len(part): collist.append(part[row])
      row += 1
    return collist
    
def partition(list,nparts):
    """Partion list into n chunks, as evenly sized as possible."""
    nleft    = len(list)
    divider  = float(nparts)
    parts    = [ ]
    findex   = 0
    for i in range(0,nparts): # partition recursively
      nnew   = int(ceil(nleft/divider))
      lindex = findex + nnew
      parts.append(list[findex:lindex])
      nleft   -= nnew
      divider -= 1
      findex   = lindex
      #print nnew
    return parts
    
def green(string,**kwargs):
  return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string
  
def warning(string,**kwargs):
  print ">>> \033[1m\033[93m%sWarning!\033[0m\033[93m %s\033[0m"%(kwargs.get('pre',""),string)
  
def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory %s"%dirname

convert  = lambda t: int(t) if t.isdigit() else t
alphanum = lambda k: [convert(c) for c in re.split('([0-9]+)',k)]
def sortStringWithNumbers(list):
  """Sort list of strings containing numbers."""
  return sorted(list,key=alphanum)

def findBranches(filename,searchterm):
  """Find all branches with some pattern."""
  file       = TFile(filename,'READ')
  tree       = file.Get('limit')
  branches   = [ ]
  searchterm = searchterm.replace('*',".*")
  
  for branch in sortStringWithNumbers([b.GetName() for b in tree.GetListOfBranches()]):
    if re.search(searchterm,branch):
      branches.append(branch)
  return branches

def chunkify(list,nmax,overlap=0,complete=False):
  """Divide list in evenly sized chunks."""
  if not list: return [ ]
  complete  = complete or overlap
  nentries0 = len(list)
  nchunks   = int(ceil(float(nentries0)/nmax))
  nentries, nextra = divmod(nentries0,nchunks)
  chunks    = [ ]
  ilast     = 0
  #print nchunks, nmax, nextra
  for ichunk in xrange(nchunks):
    n = nentries+1 if ichunk<nextra else nentries
    ifirst = ilast
    ilast  = ilast + n
    if complete and n<nmax:
      if ichunk==0:
        chunk = list[ifirst:ilast+(nmax-n)]
      elif ichunk==nchunks-1:
        chunk = list[ifirst-(nmax-n):ilast]
      else:
        chunk = list[ifirst-int(ceil((nmax-n)/2.)):ilast+int(floor((nmax-n)/2.))]
    else:
      chunk = list[ifirst:ilast]
    chunks.append(chunk)
  return chunks
  
def getBBBList(channel,var,region,year,process,**kwargs):
    """Get list of all BBB nuisance parameter for a proces."""
    indir    = kwargs.get('indir', "output_%s"%year)
    era      = "%s-13TeV"%year
    tag      = kwargs.get('tag', "" )
    filename = '%s/higgsCombine.%s_%s-%s%s-%s.MultiDimFit.mH90.root'%(indir,channel,var,region,tag,era)
    bbblist  = findBranches(filename,process) #[int(re.findall(r"\d+",b)[-1]) for b in findBranches(filename,process)]
    return bbblist
    
def getChunkifiedBBBLists(channel,var,region,year,process,**kwargs):
    """Get list of all BBB nuisance parameter for a proces, chunked into smaller overlapping list."""
    bbblist = getBBBList(channel,var,region,year,process,**kwargs)
    chunks  = chunkify(bbblist,9,complete=(len(bbblist)>9))
    return chunks
    


def main(args):
    
    print "Using configuration file: %s"%args.config
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    ensureDirectory(PLOTS_DIR)
    year      = args.year
    poi       = args.poi
    lumi      = 36.5 if year=='2016' else 41.4 if (year=='2017' or year=='UL2017') else 59.5 if (year=='2018' or year=='UL2018') else 19.5 if year=='UL2016_preVFP' else 16.8
    channel   = setup["channel"].replace("mu","m").replace("tau","t")
    tag       = setup["tag"] if "tag" in setup else ""
    tag += args.extratag
    indir = args.indir
    CMSStyle.setCMSEra(year)

    # Leave hard-coded this part as this is purely a plotting choice
    nuisances = [ #"eff_t_$CAT", "trackedParam_tid_SF_DM0","trackedParam_tid_SF_DM10", "trackedParam_tid_SF_pt1","trackedParam_tid_SF_pt2","trackedParam_tid_SF_pt3",
                 "trackedParam_tid_SF_DM0","trackedParam_tid_SF_DM10", "xsec_dy", "norm_wj",
                  "shape_jTauFake", "rate_jTauFake", "xsec_tt", "trackedParam_tes_DM0","trackedParam_tes_DM1","trackedParam_tes_DM10","trackedParam_tes_DM11" ]
    compare   = {
      "norm":
          [ "eff_m", "xsec_tt", "xsec_st", "norm_qcd", "lumi", "xsec_vv", "norm_qcd", "rate_jTauFake_DM0", "rate_jTauFake_DM1","rate_jTauFake_DM10","rate_jTauFake_DM11","muonFakerate_DM0","muonFakerate_DM1","muonFakerate_DM10","muonFakerate_DM11"
        ],
      "norm":
        [ "xsec_tt", "xsec_st", "norm_qcd", "lumi", "xsec_vv", "norm_qcd"
        ],
      "shapes":
        ["shape_mTauFake_DM0_pt1","shape_mTauFake_DM0_pt2","shape_mTauFake_DM0_pt3", "shape_mTauFake_DM0_pt4",
         "shape_mTauFake_DM1_pt1","shape_mTauFake_DM1_pt2","shape_mTauFake_DM1_pt3", "shape_mTauFake_DM1_pt4",
         "shape_mTauFake_DM10_pt1","shape_mTauFake_DM10_pt2","shape_mTauFake_DM10_pt3", "shape_mTauFake_DM10_pt4",
         "shape_mTauFake_DM11_pt1","shape_mTauFake_DM11_pt2","shape_mTauFake_DM11_pt3", "shape_mTauFake_DM11_pt4",
         "shape_jTauFake_DM0_pt1","shape_jTauFake_DM0_pt2","shape_jTauFake_DM0_pt3", "shape_jTauFake_DM0_pt4",
         "shape_jTauFake_DM1_pt1","shape_jTauFake_DM1_pt2","shape_jTauFake_DM1_pt3", "shape_jTauFake_DM1_pt4",
         "shape_jTauFake_DM10_pt1","shape_jTauFake_DM10_pt2","shape_jTauFake_DM10_pt3", "shape_jTauFake_DM10_pt4",
         "shape_jTauFake_DM11_pt1","shape_jTauFake_DM11_pt2","shape_jTauFake_DM11_pt3", "shape_jTauFake_DM11_pt4",
         "shape_dy"
        ],
      "rateParam":
        [ "trackedParam_xsec_dy", "trackedParam_sf_W_DM0_pt1","trackedParam_sf_W_DM0_pt2","trackedParam_sf_W_DM0_pt3", "trackedParam_sf_W_DM1_pt1","trackedParam_sf_W_DM1_pt2","trackedParam_sf_W_DM1_pt3", "trackedParam_sf_W_DM10_pt1", "trackedParam_sf_W_DM10_pt2","trackedParam_sf_W_DM10_pt3","trackedParam_sf_W_DM11_pt1", "trackedParam_sf_W_DM11_pt2","trackedParam_sf_W_DM11_pt3"
        ],
      "tid":
      ["trackedParam_tid_SF_DM0_pt1", "trackedParam_tid_SF_DM0_pt2", "trackedParam_tid_SF_DM0_pt3","trackedParam_tid_SF_DM0_pt4",
      "trackedParam_tid_SF_DM1_pt1","trackedParam_tid_SF_DM1_pt2", "trackedParam_tid_SF_DM1_pt3","trackedParam_tid_SF_DM1_pt4",
      "trackedParam_tid_SF_DM10_pt1","trackedParam_tid_SF_DM10_pt2", "trackedParam_tid_SF_DM10_pt3","trackedParam_tid_SF_DM10_pt4",
      "trackedParam_tid_SF_DM11_pt1","trackedParam_tid_SF_DM11_pt2", "trackedParam_tid_SF_DM11_pt3","trackedParam_tid_SF_DM11_pt4"]
}
    fulllist  = [
      "tes_DM0_pt1","tes_DM0_pt2", "tes_DM0_pt3","tes_DM0_pt4","tes_DM1_pt1","tes_DM1_pt2","tes_DM1_pt3","tes_DM1_pt4",
      "tes_DM10_pt1","tes_DM10_pt2","tes_DM10_pt3","tes_DM10_pt4",
      "tes_DM11_pt1","tes_DM11_pt2","tes_DM11_pt3","tes_DM11_pt4",
      "trackedParam_xsec_dy","trackedParam_sf_W_DM0_pt1", "trackedParam_sf_W_DM0_pt2",  "trackedParam_sf_W_DM0_pt3", "trackedParam_sf_W_DM0_pt4",
      "trackedParam_sf_W_DM1_pt1", "trackedParam_sf_W_DM1_pt2",  "trackedParam_sf_W_DM1_pt3", "trackedParam_sf_W_DM1_pt4",
      "trackedParam_sf_W_DM10_pt1", "trackedParam_sf_W_DM10_pt2",  "trackedParam_sf_W_DM10_pt3", "trackedParam_sf_W_DM10_pt4",
      "trackedParam_sf_W_DM11_pt1", "trackedParam_sf_W_DM11_pt2",  "trackedParam_sf_W_DM11_pt3", "trackedParam_sf_W_DM11_pt4",
      "trackedParam_tid_SF_DM0_pt1","trackedParam_tid_SF_DM0_pt2", "trackedParam_tid_SF_DM0_pt3","trackedParam_tid_SF_DM0_pt4",
      "trackedParam_tid_SF_DM1_pt1","trackedParam_tid_SF_DM1_pt2", "trackedParam_tid_SF_DM1_pt3","trackedParam_tid_SF_DM1_pt4",
      "trackedParam_tid_SF_DM10_pt1","trackedParam_tid_SF_DM10_pt2", "trackedParam_tid_SF_DM10_pt3","trackedParam_tid_SF_DM10_pt4",
      "trackedParam_tid_SF_DM11_pt1","trackedParam_tid_SF_DM11_pt2", "trackedParam_tid_SF_DM11_pt3","trackedParam_tid_SF_DM11_pt4",
      "shape_dy", 
      "xsec_tt", "xsec_st", "norm_qcd", "lumi", "xsec_vv", "norm_qcd", "eff_m"
    ]
    procsBBB  = [ 'QCD', 'W', 'TTT', 'ZTT' ] # 'JTF' ]

    for var in setup["observables"]:
        variable = setup["observables"][var]
        for r in setup["observables"][var]["scanRegions"]:
            region = r # r listed for each observable defined in regions
            varTitle = var
            if "title" in variable:
                varTitle = variable["title"]
            regionTitle = r
            if "title" in region: 
                region["title"]
            title = "%s, %s"%(varTitle,regionTitle)
            tes_name = "%s_%s"%(poi,r)            

            # COMPARE nuisances
            for name, parameters in compare.iteritems():
                plotPostFitValues(channel,var,r,year,fulllist,*parameters,name=name,tag=tag,compareFD=False,title=title,poi=poi)
            
            # BIN-BY-BIN
            for process in procsBBB:
                bbblists = getChunkifiedBBBLists(channel,var,r,year,process,tag=tag)
                for bbblist in bbblists:
                    plotPostFitValues(channel,var,r,year,fulllist,*bbblist,tag=tag,compareFD=False,title=title,poi=poi)
            
            # CORRELATION
            correlate = [tes_name] + fulllist + getBBBList(channel,var,r,year,'ZTT',tag=tag)
            #plotCorrelation(channel,var,r,year,correlate,tag=tag,title=title,poi=poi)

            # Write parameter values 
            writeParametersFitVal(channel,var,r,year,fulllist,tag=tag,title=title,poi=poi)
          



if __name__ == '__main__':

    argv = sys.argv
    description = '''This script makes datacards with CombineHarvester.'''
    parser = ArgumentParser(prog="LowMassDiTau_Harvester",description=description,epilog="Succes!")
    parser.add_argument('-y', '--year', dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018', 'UL2018_v10','2022_postEE','2022_preEE', '2023C', '2023D'], type=str, default='2017', action='store', help="select year")
    parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup" )
    parser.add_argument('-e', '--extra-tag', dest='extratag', type=str, default="", action='store', metavar="TAG", help="extra tag for output files")
    parser.add_argument('-r', '--shift-range', dest='shiftRange', type=str, default="0.940,1.060", action='store', metavar="RANGE", help="range of TES shifts")
    parser.add_argument('-p', '--pdf', dest='pdf', default=False, action='store_true', help="save plot as pdf as well")
    parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true', help="set verbose")
    parser.add_argument('-poi', '--poi',         dest='poi', default='poi', type=str, action='store', help='use this parameter of interest')
    parser.add_argument('-i', '--indir',         dest='indir', type=str, help='indir')
    args = parser.parse_args()


    main(args)
    print ">>>\n>>> done\n"
    


