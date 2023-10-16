#! /usr/bin/env python
# Author: Izaak Neutelings (April 2021)
# https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/102x/test/diffNuisances.py
import re
from array import array
from ROOT import gROOT, gPad, gStyle, TFile, TCanvas, TLegend, TLatex, TH1F, TLine, TColor,\
                 kBlack, kGray, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, kBlackBody
import TauFW.Plotter.plot.CMSStyle as CMSStyle
from math import log10, ceil, floor
gROOT.SetBatch(True)
gStyle.SetOptTitle(0)

# CUSTOM COLOR PALETTE, see core/base/src/TColor.cxx
red   = array('d',[ 0.80, 0.90, 1.00, 0.60, 0.02, ])
green = array('d',[ 0.20, 0.80, 1.00, 0.80, 0.20, ])
blue  = array('d',[ 0.10, 0.60, 1.00, 0.90, 0.65, ])
stops = array('d',[i/(len(red)-1.) for i in xrange(0,len(red))])
FI    =  TColor.CreateGradientColorTable(len(red), stops, red, green, blue, 100)
kMyTemperature = array('i',[ FI+i for i in xrange(100)])
gStyle.SetPalette(100,kMyTemperature)


def plotCorrelationHist(fname,**kwargs):
  """Draw correlation of nuisance parameters from FitDiagnostics output."""
  print(green("\n>>> plotCorrelationHist"))
  pois       = kwargs.get('poi',    "r"        )
  filters    = kwargs.get('filter', [ ]        )
  nbins      = kwargs.get('nbins',  40         )
  xmin       = kwargs.get('xmin',   -1         )
  xmax       = kwargs.get('xmax',   1          )
  title      = kwargs.get('title',  ""         )
  name       = kwargs.get('name',   ""         )
  indir      = kwargs.get('indir',  "output"   )
  outdir     = kwargs.get('outdir', "plots"    )
  xtitle     = kwargs.get('xtitle', "Correlation to signal strength r"  )
  ytitle     = kwargs.get('ytitle', "Nuisance parameters" )
  tag        = kwargs.get('tag',    ""         )
  ptag       = kwargs.get('ptag',   ""         )
  logy       = kwargs.get('logy',   True       )
  ensuredir(outdir)
  pname = "%s/correlation-%s%s%s"%(outdir,name,tag,ptag)
  colors = [ kBlue, kRed, kGreen, kMagenta, kOrange, kTeal, kAzure+2, kYellow-3 ]
  if not isinstance(pois,list):
    pois = [pois]
  if not isinstance(filters,list):
    filters = [filters]
  for i, filter in enumerate(filters):
    filters[i] = re.compile(filter)
  
  file  = ensureTFile(fname)
  fits  = [
    #('fit_b',"B-only"), # r fixed in B-only...
    ('fit_s',"S+B"),
  ]
  hists = [ ]
  cuts  = { c: 0 for c in [0.10,0.25,0.5,0.75] }
  pcut  = 0.15 # for printing
  for fitname, fittitle in fits:
    print(">>> File %s:%s"%(fname,fitname))
    fit   = file.Get(fitname) # fit results
    if not fit:
      warning(">>>   Could not get %r!"%(fit))
    hist  = TH1F("corr_"+fitname,fittitle,nbins,-1.,1.)
    #hist.SetDirectory(0)
    hists.append(hist)
    fpars = fit.floatParsFinal()
    npars = fpars.getSize()
    rpars = [ ] # list of POIs for correlation computation
    for poi in pois:
      npars_ = 0
      print(">>> Looking for %r..."%(poi))
      if any(c in poi for c in '.*+()[]'): # assume regexp
        exp_poi = re.compile(poi)
        for i in range(npars): # find all matches to POI regexp
          rpar = fpars.at(i)
          if rpar in rpars: continue # no double counting
          if not exp_poi.search(rpar.GetName()): continue # no match
          rpars.append(rpar)
          npars_ += 1
        print(">>> Found %d parameters for %r"%(npars_,poi))
      else: # find by exact name
        rpar = fpars.find(poi)
        rpars.append(rpar)
    print(">>> Number of POIs for correlation: %d"%(len(rpars)))
    #corrs = fit.correlation(rpar)
    #corrs = fit.correlation(poi)
    for i in range(npars):
    #for i in range(corrs.getSize()):
      # https://root.cern/doc/v610/classRooFitResult.html#a4b3c891a43f776fbe33bafbaaa2708de
      npar = fpars.at(i)
      if filters and not any(f.search(npar.GetName()) for f in filters): continue
      ridx = rpars.index(npar)+1 if npar in rpars else 0 # avoid double counting multiple POIs (assume same order)
      #print(len(rpars[ridx:]), ridx, npar.GetName())
      for rpar in rpars[ridx:]: # get correlation to each POI
        #if npar==rpar: continue # redundant with ridx
        corr = fit.correlation(rpar,npar)
        for cut in cuts: # cut 'n count
          if abs(corr)>cut:
            cuts[cut] += 1
        if abs(corr)>pcut: # print
          print(">>>   %+6.3f > %.2f:  %s to %s"%(corr,pcut,npar.GetName(),rpar.GetName()))
        #corr = corrs.at(i)
        #print(i, corr, rpar, npar)
        hist.Fill(corr)
  
  ymargin = 1.15
  if logy:
    ymin = 0.6
    hmax = max(ymargin*h.GetMaximum() for h in hists)
    span = ymargin*abs(log10(hmax/ymin))
    ymax = ymin*(10**span)
  else:
    ymin = 0
    ymax = max(1.15*h.GetMaximum() for h in hists)
  canvas = TCanvas("canvas","canvas",100,100,800,650)
  canvas.SetFillColor(0)
  canvas.SetBorderMode(0)
  canvas.SetFrameFillStyle(0)
  canvas.SetFrameBorderMode(0)
  canvas.SetMargin(0.11,0.05,0.13,0.07) # LRBT
  canvas.SetTickx(0)
  canvas.SetTicky(0)
  canvas.SetGrid()
  if logy:
    canvas.SetLogy()
  
  #textsize   = 0.045 if npars==1 else 0.036
  #lineheight = 0.055 if npars==1 else 0.045
  #x1, width  = 0.42, 0.25
  #y1, height = 0.15, lineheight*(ceil(npars/3.) if npars>6 else ceil(npars/2.) if npars>3 else npars)
  #if title:
  #  height += lineheight
  #if npars>6:
  #  if isBBB: width = 0.62; x1 = 0.25
  #  else:     width = 0.70; x1 = 0.20
  #elif npars>3: 
  #  width = 0.52; x1 = 0.36
  #legend = TLegend(x1,y1,x1+width,y1+height)
  #legend.SetTextSize(textsize)
  #legend.SetBorderSize(0)
  #legend.SetFillStyle(0)
  #legend.SetFillColor(0)
  #if title:
  #  legend.SetTextFont(62)
  #  legend.SetHeader(title) 
  #legend.SetTextFont(42)
  
  frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
  frame.GetYaxis().SetTitleSize(0.060)
  frame.GetXaxis().SetTitleSize(0.060)
  frame.GetXaxis().SetLabelSize(0.050)
  frame.GetYaxis().SetLabelSize(0.050)
  frame.GetXaxis().SetLabelOffset(0.01)
  frame.GetYaxis().SetLabelOffset(0.001 if logy else 0.01)
  frame.GetXaxis().SetTitleOffset(0.96)
  frame.GetYaxis().SetTitleOffset(0.90 if logy else 0.86)
  frame.GetXaxis().SetNdivisions(508)
  frame.GetYaxis().SetTitle(ytitle)
  frame.GetXaxis().SetTitle(xtitle)
  
  for i, hist in enumerate(hists):
    hist.SetLineColor(colors[i%len(colors)])
    hist.SetLineWidth(2)
    hist.SetMarkerColor(colors[i%len(colors)])
    hist.SetMarkerSize(1)
    hist.SetLineStyle(1)
    hist.Draw('HIST SAME')
  
  #for param in paramsleg:
  #  legend.AddEntry(graphs[param],formatParameter(param),'lep')
  #legend.Draw()
  
  # CUTS
  latex = TLatex()
  latex.SetTextSize(0.045)
  latex.SetNDC() # normalized coordinates
  ntot = hist.GetEntries()
  x1 = 0.14
  x2 = x1 + 0.23+0.02*floor(log10(ntot))
  y1 = 0.90
  if title:
    latex.SetTextAlign(13)
    latex.SetTextFont(62)
    latex.DrawLatex(x1,y1,title)
    y1 -= 0.055
  latex.SetTextFont(42)
  for i, cut in enumerate(sorted(cuts.keys())):
    npass = cuts[cut]
    latex.SetTextAlign(13)
    #latex.DrawLatex(0.14,0.89-0.05*i,"|#rho| > %.2f:"%(cut,npass))
    latex.DrawLatex(x1,y1,"|#rho| > %.2f:"%(cut))
    latex.SetTextAlign(33)
    latex.DrawLatex(x2,y1,"%d/%d"%(npass,ntot))
    y1 -= 0.052
  
  CMS_lumi.relPosX = 0.12
  CMS_lumi.CMS_lumi(canvas,13,0)
  gPad.SetTicks(1,1)
  gPad.Modified()
  frame.Draw('SAMEAXIS')
  canvas.RedrawAxis()
  canvas.SaveAs(pname+".png")
  canvas.SaveAs(pname+".pdf")
  canvas.Close()
  file.Close()


def drawCorrelationMatrix(hist,pname,**kwargs):
  """Help function to plot correlation matrix."""
  print(">>> drawCorrelationMatrix(%r)"%(pname))
  zmin   = kwargs.get('zmin',   -100.0     )
  zmax   = kwargs.get('zmax',   100.0      )
  title  = kwargs.get('title',  ""         )
  name   = kwargs.get('name',   ""         )
  indir  = kwargs.get('indir',  "output"   )
  outdir = kwargs.get('outdir', "plots"    )
  ztitle = kwargs.get('ztitle', "Correlation [%]"  ) # #rho
  tag    = kwargs.get('tag',    ""         )
  ptag   = kwargs.get('ptag',   ""         )
  logz   = kwargs.get('logz',   True       )
  msize  = kwargs.get('msize',  1.0        )
  xtitle = kwargs.get('xtitle', "Bin"      )
  ytitle = kwargs.get('ytitle', xtitle     )
  ndiv   = kwargs.get('ndiv',   0          ) # 508
  xcats  = kwargs.get('xcats',  [ ]        )
  ycats  = kwargs.get('ycats',  [ ]        )
  nxbins = hist.GetXaxis().GetNbins()
  nybins = hist.GetYaxis().GetNbins()
  
  # SCALE
  canvasH  = 180+42*max(22,nybins)
  canvasW  = 310+55*max(22,nxbins)
  scaleH   =  800./canvasH
  scaleW   = 1000./canvasW
  scaleF   = 600./(canvasH-160)
  tmargin  = 0.053
  bmargin  = 0.14
  lmargin  = 0.14
  rmargin  = 0.16
  xlsize   = min(0.050*scaleF,0.03) # x label size
  ylsize   = min(0.056*scaleF,0.03) # x label size
  dsize    = min(0.15*scaleF,0.03) # divider size
  print(">>>   canvas %d x %d"%(canvasW,canvasH))
  print(">>>   scaleF=%.5g, scaleH=%.5g, scaleW=%.5g"%(scaleF,scaleH,scaleW))
  
  canvas = TCanvas('canvas','canvas',100,100,canvasW,canvasH)
  canvas.SetFillColor(0)
  canvas.SetBorderMode(0)
  canvas.SetFrameFillStyle(0)
  canvas.SetFrameBorderMode(0)
  canvas.SetMargin(lmargin,rmargin,bmargin,tmargin) # LRBT
  canvas.SetTicks(1,1)
  canvas.SetGrid(0,0)
  canvas.cd()
  
  frame = hist
  frame.GetXaxis().SetLabelSize(0.050*scaleF)
  frame.GetYaxis().SetLabelSize(0.056*scaleF)
  frame.GetZaxis().SetLabelSize(0.055*scaleF)
  frame.GetZaxis().SetLabelSize(0.030)
  frame.GetXaxis().SetLabelOffset(0.005*scaleF)
  frame.GetYaxis().SetLabelOffset(0.003*scaleF)
  frame.GetXaxis().SetTickLength(0)
  frame.GetYaxis().SetTickLength(0)
  frame.GetXaxis().SetNdivisions(ndiv,False)
  frame.GetYaxis().SetNdivisions(ndiv,False)
  frame.GetXaxis().SetTitleSize(0.042)
  frame.GetYaxis().SetTitleSize(0.042)
  frame.GetZaxis().SetTitleSize(0.042)
  frame.GetXaxis().SetTitleOffset(1.4)
  frame.GetYaxis().SetTitleOffset(1.5)
  frame.GetZaxis().SetTitleOffset(1.1) #97*rmargin/0.16
  frame.GetXaxis().SetTitle(xtitle)
  frame.GetYaxis().SetTitle(ytitle)
  frame.GetZaxis().SetTitle(ztitle)
  frame.GetZaxis().CenterTitle(True)
  #gStyle.SetPalette(kBlackBody)
  #frame.SetContour(3);
  #gStyle.SetPaintTextFormat(".3g")
  gStyle.SetPaintTextFormat(".0f")
  frame.SetMarkerSize(1.4*scaleF*msize)
  #frame.SetMarkerColor(kRed)
  frame.SetMinimum(zmin)
  frame.SetMaximum(zmax)
  hist.Draw('COLZ TEXT')
  
  # DIVIDERS
  lines = [ ]
  texts = [ ]
  xbody = 1.-lmargin-rmargin
  ybody = 1.-tmargin-bmargin
  dx    = (4.9*xlsize+0.6*dsize)*nxbins/xbody
  dy    = (4.2*ylsize+0.7*dsize)*nybins/ybody
  #print(">>> dsize=%s, xlsize=%s, nxbins=%s, xbody=%s => dx=%s"%(dsize,xlsize,nxbins,xbody,dx))
  #print(">>> dsize=%s, ylsize=%s, nybins=%s, ybody=%s => dy=%s"%(dsize,ylsize,nybins,ybody,dy))
  if xcats:
    latex = TLatex()
    latex.SetTextSize(dsize)
    latex.SetTextFont(42)
    latex.SetTextColor(kRed+1)
    latex.SetTextAlign(21)
    latex.SetTextAngle(0)
    texts.append(latex)
    for i, (x, cat) in enumerate(xcats):
      xnext = xcats[i+1][0] if i+1<len(xcats) else nxbins
      #ymin, ymax = -0.8./scaleF, nybins
      ymin, ymax = -dx, nybins
      latex.DrawLatex((x+xnext)/2,ymin,cat)
      if x>0:
        #TLine.DrawLineNDC(x,0,x,nbins)
        line = TLine(x,ymin,x,ymax)
        line.SetLineWidth(3)
        line.SetLineColor(kRed+1)
        line.Draw('SAME')
        lines.append(line) # store in memory
  if ycats:
    latex = TLatex()
    latex.SetTextSize(dsize)
    latex.SetTextFont(42)
    latex.SetTextColor(kRed+1)
    latex.SetTextAlign(23)
    latex.SetTextAngle(90)
    texts.append(latex)
    for i, (y, cat) in enumerate(ycats):
      ynext = ycats[i+1][0] if i+1<len(ycats) else nybins
      xmin, xmax = -dy, nxbins
      latex.DrawLatex(xmin,(y+ynext)/2,cat)
      if x>0:
        line = TLine(xmin,y,xmax,y)
        line.SetLineWidth(5)
        line.SetLineColor(kRed+1)
        line.Draw('SAME')
        lines.append(line) # store in memory
  
  # TEXT
  if title:
    latex = TLatex()
    latex.SetTextSize(0.038)
    latex.SetTextAlign(11)
    latex.SetTextFont(42)
    latex.SetTextAngle(0)
    y = 0.1*bmargin
    for line in title.split('\n'):
      latex.DrawLatexNDC(0.1*lmargin,y,line)
      y -= 0.05
    texts.append(latex)
  
  CMS_lumi.relPosX = 0.14
  CMS_lumi.CMS_lumi(canvas,13,0)
  canvas.SetTicks(1,1)
  canvas.SetGrid(0,0)
  canvas.Modified()
  frame.Draw('SAMEAXIS')
  
  canvas.SaveAs(pname+".png")
  for line in lines:
    line.SetLineWidth(1)
  canvas.SaveAs(pname+".pdf")
  canvas.Close()
  
