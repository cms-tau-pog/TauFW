#! /usr/bin/env python
# Author: Izaak Neutelings (May 2021)
# Description:
#   Test Unroll.cxx macro to unroll 2D histogram in TTree::Draw() to 1D histogram
#   with bin bin numbers, excluding under/overflow.
#   E.g. 2D histogram (4x5):
#     +----+----+----+----+----+
#   y | 16 | 17 | 18 | 19 | 20 |
#     +----+----+----+----+----+
#     | 11 | 12 | 13 | 14 | 15 |
#     +----+----+----+----+----+
#     |  6 |  7 |  8 |  9 | 10 |
#     +----+----+----+----+----+
#     |  1 |  2 |  3 |  4 |  5 |
#     +----+----+----+----+----+--> x axis
#
#   Unrolled 1D histogram:
#     +---+---+---+---+---+--     --+----+
#     | 1 | 2 | 3 | 4 | 5 |   ...   | 20 |
#     +---+---+---+---+---+--     --+----+--> x axis
#     1   2   3   4   5   6        20   21
#
import os, re
from time import time
from ROOT import gROOT, gDirectory, gStyle, TFile, TCanvas, TTree, TH1D, TH2D, TLatex, TLine,\
                 kDashed, kRed, kBlue
gStyle.SetOptTitle(False)
gStyle.SetOptStat(False)
gROOT.SetBatch(True)
gROOT.ProcessLine(".L python/macros/Unroll.cxx+O")
from ROOT import Unroll
vardict = { # convert TTree variable names
  "pt_ll": "pt_mumu", "pt_moth": "Zpt",
  "m_vis": "m_mumu",  "m_moth":  "Zmass",
}
titledict = { # convert TTree variable names
  "pt_ll": "p_{T}^{#mu#mu}", "pt_moth": "Z p_{T}",
  "m_vis": "m_{#mu#mu}",     "m_moth":  "Z mass",
}


def red(string):
  return "\033[31m%s\033[0m"%string
  

def test_unroll(fname,xvars,yvars,cut="",verb=0):
  """Test unrolling of 2D histogram and create 4D response matrix."""
  if verb>=1:
    print ">>> test_unroll(%s)"%(fname)
  start  = time()
  file   = TFile(fname,'READ')
  assert file and not file.IsZombie(), "Could not open %s"%(fname)
  tree   = file.Get('tree')
  assert tree and tree.GetEntries()>10, "Could find TTree 'tree' in %s"%(fname)
  hists  = [ ]
  xvar1, xvar2 = xvars[:2]
  yvar1, yvar2 = yvars[:2]
  #xbins  = xvars[2:]
  #ybins  = yvars[2:]
  nxbins, xmin, xmax = xvars[2:]
  nybins, ymin, ymax = yvars[2:]
  #nxbins, nybins = xbins[0], ybins[0]
  nbins      = nxbins*nybins
  hname2d    = "testUnroll_%s-%s"%(vardict.get(yvar1,yvar1),vardict.get(xvar1,xvar1))
  hname2dcpp = "testUnroll_%s-%s_rolledup_cpp"%(vardict.get(yvar1,yvar1),vardict.get(xvar1,xvar1))
  hname4d    = "testUnroll_response"
  hnamepy    = "%s_unrolled_py"%(hname2d)
  hnamecpp   = "%s_unrolled_cpp"%(hname2d)
  xtitle     = titledict.get(xvar1,xvar1)
  ytitle     = titledict.get(yvar1,yvar1)
  xtitle1d   = "bin(%s,%s)"%(xtitle,ytitle)
  xtitle4d   = "bin(%s,%s)"%(titledict.get(xvar2,xvar2),titledict.get(yvar2,yvar2))
  ytitle4d   = xtitle1d
  
  # CREATE HISTOGRAMS
  #hist1  = TH1D(hname1,hname1,*xbins)
  histpy = TH1D(hnamepy,hnamepy,nbins,1,1+nbins) # unrolled
  hist2d = TH2D(hname2d,hname2d,nxbins,xmin,xmax,nybins,ymin,ymax) #*(xbins+ybins)
  hist4d = TH2D(hname4d,hname4d,nbins,1,1+nbins,nbins,1,1+nbins) # response / migration matrix
  tree.Draw("%s:%s >> %s"%(yvar1,xvar1,hname2d),cut,'gOFF')
  Unroll.SetBins(hist2d,verb) # set axis for unrolling in Unroll::GetBin
  histcpp = Unroll.Unroll(hist2d,hnamecpp,False,verb) # unrolled
  tree.Draw("Unroll::GetBin(%s,%s) >> %s"%(xvar1,yvar1,hnamepy),cut,'gOFF') # unrolled
  tree.Draw("Unroll::GetBin(%s,%s):Unroll::GetBin(%s,%s) >> %s"%(xvar2,yvar2,xvar1,yvar1,hname4d),cut,'gOFF') # x: reco, y: gen
  hist2dcpp = Unroll.RollUp(histcpp,hname2dcpp,hist2d,verb) # rolled up
  #hist = TH2F(hname,hname,nbins,xmin,xmax)
  #tree.Draw("%s:%s >> %s"%(xvar,yvar,hname),"(%s)*%s"%(cut,weight),'gOFF')
  
  # DRAW
  for vars in [xvars,yvars]:
    nabins, amin, amax = vars[2:]
    for avar in vars[:2]:
      hname  = "testUnroll_%s"%(vardict.get(avar,avar))
      hist1d = TH1D(hname,hname,nabins,amin,amax)
      tree.Draw("%s >> %s"%(avar,hname),cut,'gOFF')
      atitle = titledict.get(avar,avar)
      draw(hist1d,atitle)
  draw(histpy, xtitle1d,nbins=nybins) # rolled up
  draw(histcpp,xtitle1d,nbins=nybins) # rolled up
  draw2d(hist2d,   xtitle,ytitle,number=True) # original
  draw2d(hist2dcpp,xtitle,ytitle,number=True) # rolled back up
  draw2d(hist4d,xtitle4d,ytitle4d,nxbins=nybins,nybins=nybins) # response matrix
  
  # TEST Unroll::GetBin
  nx, ny = 2*nxbins, 2*nybins # number of points to scan
  xbinw = float(xmax-xmin)/nx
  ybinw = float(ymax-ymin)/ny
  print ">>> nxbins=%s, xmin=%s, xmax=%s"%(nxbins,xmin,xmax)
  print ">>> nybins=%s, ymin=%s, ymax=%s"%(nybins,ymin,ymax)
  print ">>> nx=%s, xbinw=%s, ny=%s, ybinw=%s"%(nx,xbinw,ny,ybinw)
  xvals = [xmin+xbinw*i for i in range(-2,nx+3)]
  yvals = [ymin+ybinw*i for i in range(-2,ny+3)]
  #xvals = [-1,0,1,10,50,100,200]
  #yvals = [-1,0,1,10,50,100,200]
  print ">>>"
  print ">>> %7s |"%(r'y\x') + ' '.join("%6s"%x for x in xvals)
  print ">>> %8s+"%('-'*7) + '-'*7*len(xvals)
  for y in yvals:
    #print ">>> %7s |"%x+' '.join("%6s"%(Unroll.GetBin(x,y)) for x in xvals)
    row = ">>> %7s |"%y
    for x in xvals:
      bin = Unroll.GetBin(x,y)
      str = "%6s "%(bin)
      if bin<1 or bin>=nxbins*nybins+1:
        str = red(str)
      row += str
    print row
  print ">>>"
  
  print ">>> Took %.2fs"%(time()-start)
  

def draw(hist,xtitle,nbins=0):
  """Draw 1D histogram."""
  tsize = 0.045
  lines = [ ]
  canvas = TCanvas('canvas','canvas',100,100,1200,800)
  canvas.SetMargin(0.09,0.02,0.11,0.02) # LRBT
  canvas.SetLogy()
  hist.SetMaximum(1.8*hist.GetMaximum())
  hist.SetMinimum(2)
  hist.GetXaxis().SetTitle(xtitle)
  hist.GetYaxis().SetTitle("Events")
  hist.GetXaxis().SetTitleSize(tsize)
  hist.GetYaxis().SetTitleSize(tsize)
  hist.GetXaxis().SetLabelSize(0.9*tsize)
  hist.GetYaxis().SetLabelSize(0.9*tsize)
  hist.GetXaxis().SetTitleOffset(1.05)
  hist.GetYaxis().SetTitleOffset(1.00)
  #hist.SetMinimum(ymin)
  #hist.SetMaximum(ymax)
  hist.SetLineColor(kBlue)
  hist.SetLineWidth(2)
  #hist.SetMarkerSize(size)
  #hist.SetMarkerColor(color)
  #hist.SetMarkerStyle(8)
  hist.Draw('HIST')
  if nbins>0: # divide with nlines
    xmin, xmax = hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax()
    ymin, ymax = hist.GetMinimum(), hist.GetMaximum()
    for i in range(1,nbins):
      x = xmin+(xmax-xmin)*i/nbins
      line = TLine(x,ymin,x,ymax)
      line.SetLineColor(kRed)
      line.SetLineStyle(kDashed)
      line.SetLineWidth(1)
      line.Draw()
      lines.append(line)
  canvas.SaveAs(hist.GetName()+".png")
  #canvas.SaveAs(hist.GetName()+".pdf")
  canvas.Close()
  

def draw2d(hist,xtitle,ytitle,number=False,nxbins=0,nybins=0):
  """Draw 2D histogram."""
  tsize = 0.045
  lines = [ ]
  xmin, xmax = hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax()
  ymin, ymax = hist.GetYaxis().GetXmin(), hist.GetYaxis().GetXmax()
  canvas = TCanvas('canvas','canvas',100,100,900,800)
  canvas.SetMargin(0.11,0.16,0.10,0.02) # LRBT
  canvas.SetLogz()
  hist.GetXaxis().SetTitle(xtitle)
  hist.GetYaxis().SetTitle(ytitle)
  hist.GetZaxis().SetTitle("Events")
  hist.GetXaxis().SetTitleSize(tsize)
  hist.GetYaxis().SetTitleSize(tsize)
  hist.GetZaxis().SetTitleSize(tsize)
  hist.GetXaxis().SetLabelSize(0.9*tsize)
  hist.GetYaxis().SetLabelSize(0.9*tsize)
  hist.GetZaxis().SetLabelSize(0.9*tsize)
  hist.GetXaxis().SetTitleOffset(1.04)
  hist.GetYaxis().SetTitleOffset(1.14)
  hist.GetZaxis().SetTitleOffset(1.08)
  hist.Draw('COLZ')
  if number:
    latex = TLatex()
    latex.SetTextSize(0.8*tsize)
    latex.SetTextAlign(22)
    latex.SetTextFont(62)
    latex.SetTextColor(kRed)
    for ix in range(1,hist.GetXaxis().GetNbins()+1):
      x = hist.GetXaxis().GetBinCenter(ix)
      for iy in range(1,hist.GetYaxis().GetNbins()+1):
        y = hist.GetYaxis().GetBinCenter(iy)
        latex.DrawLatex(x,y,str(Unroll.GetBin(x,y)))
  if nxbins>0: # divide with nlines
    for i in range(1,nxbins):
      x = xmin+(xmax-xmin)*i/nxbins
      line = TLine(x,ymin,x,ymax)
      line.SetLineColor(kRed)
      line.SetLineStyle(kDashed)
      line.SetLineWidth(1)
      line.Draw()
      lines.append(line)
  if nybins>0: # divide with nlines
    for i in range(1,nybins):
      y = ymin+(ymax-ymin)*i/nybins
      line = TLine(xmin,y,xmax,y)
      line.SetLineColor(kRed)
      line.SetLineStyle(kDashed)
      line.SetLineWidth(2)
      line.Draw()
      lines.append(line)
  canvas.RedrawAxis()
  canvas.SaveAs(hist.GetName()+".png")
  #canvas.SaveAs(hist.GetName()+".pdf")
  canvas.Close()
  

def main():
  #print ">>> main()"
  fname = "test/DYJetsToLL_M-50_mumu.root"
  xvars = ('m_vis', 'm_moth',   5, 60, 110) # xreco, xgen, nxbins, xmin, xmax
  yvars = ('pt_ll', 'pt_moth', 10,  0, 150) # yreco, ygen, nybins, ymin, ymax
  cut   = ""
  test_unroll(fname,xvars,yvars,cut,verb=1)
  

if __name__ == '__main__':
    main()
    print ">>> Done"
    
