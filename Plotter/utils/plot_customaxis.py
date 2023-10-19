#! /usr/bin/env python3
# Author: Izaak Neutelings (October 2023)
# Description: Plot custom axis
print(">>> Importing ROOT...")
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, TCanvas, TF1, TGaxis,\
                 kBlack, kRed, kBlue, kGreen
gROOT.SetBatch(True)       # don't open GUI windows
gStyle.SetOptTitle(False)  # don't make title on top of histogram
gStyle.SetOptStat(False)   # don't make stat. box
print(">>> Done importing...")


def plot_customaxis_log(verb=0):
  """Plot with custom logarithmic y axis, but with ticks linearly spaced."""
  print(">>> plot_customaxis_log")
  
  # FUNCTION
  fname = "plot_customaxis_log"
  xmin, xmax = 2, 5  # x = mass
  ymin, ymax = 4, 25 # y = mass
  xtitle = "Mass x [GeV]"
  ytitle = "Mass y [GeV]"
  
  # PLOT
  canvas = TCanvas('canvas','canvas',100,100,1000,800) # XYWH
  canvas.SetMargin(0.10,0.02,0.11,0.02) # LRBT
  canvas.SetLogy()
  canvas.SetTicks(1,0) # draw ticks on opposite side
  
  # FRAME
  tsize = 0.050
  lsize = 0.044
  ysize = 0.98*lsize # for logarithmic axis label
  frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
  ###frame.SetMinimum(ymin)
  ###frame.SetMaximum(ymax)
  ###frame.GetYaxis().SetRangeUser(ymin,ymax)
  frame.GetXaxis().SetTitle(xtitle)
  #frame.GetYaxis().SetTitle(ytitle)
  frame.GetYaxis().SetTitle("") # hide y axis
  frame.GetXaxis().SetTitleOffset(0.97)
  frame.GetYaxis().SetTitleOffset(1.03)
  frame.GetXaxis().SetTitleSize(tsize)
  #frame.GetYaxis().SetTitleSize(tsize)
  frame.GetYaxis().SetTitleSize(0) # hide y axis
  frame.GetXaxis().SetLabelSize(lsize)
  #frame.GetYaxis().SetLabelSize(ysize)
  frame.GetYaxis().SetLabelSize(0) # hide y axis
  frame.GetYaxis().SetTickLength(0) # hide y axis
  
  # DRAW FUNCTION
  f1 = TF1('f1',"x",xmin,xmax)
  f2 = TF1('f2',"x*x",xmin,xmax)
  f1.SetLineColor(kRed)
  f2.SetLineColor(kBlue)
  for f in [f1,f2]:
    #f.SetTitle(f";{xtitle};{ytitle}")
    f.SetLineWidth(3)
    f.Draw('L SAME')
  
  # LEFT Y AXIS
  fy = TF1('fy',"log(x)",ymin,ymax) # scale logarithmically, while keeping ticks at linear equidistance
  #yaxis = TGaxis(gPad.GetUxmin(),gPad.GetUymax(),gPad.GetUxmax(),gPad.GetUymax(),'fy',1004,'-')
  yaxis = TGaxis(xmin,ymin,xmin,ymax,'fy',1004,'-')
  yaxis.SetLineWidth(1)
  yaxis.SetLineColor(kRed)
  yaxis.SetTextFont(42)
  yaxis.SetTextColor(kRed)
  yaxis.SetTitle(ytitle)
  yaxis.SetTitleSize(lsize)
  yaxis.SetLabelFont(42)
  yaxis.SetLabelColor(kRed)
  yaxis.SetLabelSize(ysize)
  yaxis.SetLabelOffset(6e-3)
  yaxis.Draw()
  
  # RIGHT Y AXIS
  #yaxis2 = TGaxis(gPad.GetUxmin(),gPad.GetUymax(),gPad.GetUxmax(),gPad.GetUymax(),'fy',1004,'+')
  yaxis2 = TGaxis(xmax,ymin,xmax,ymax,'fy',1004,'+')
  yaxis2.SetLineColor(kBlue)
  yaxis2.SetTitleSize(0)
  yaxis2.SetLabelSize(0)
  yaxis2.Draw()
  
  # SAVE
  #canvas.RedrawAxis()
  canvas.SaveAs(fname+".png")
  #canvas.SaveAs(fname+".pdf")
  canvas.Close()
  

def plot_customaxis_pval(verb=0):
  """Plot p-value vs. significance."""
  print(">>> plot_customaxis_pval")
  from math import log10, ceil
  from ROOT import RooStats
  
  # FUNCTION
  fname = "plot_customaxis_pval"
  xmin, xmax = 0, 5.25   # x = significance
  ymin, ymax = 1e-7, 0.6 # y = p-value
  pmin, pmax = RooStats.SignificanceToPValue(xmin), RooStats.SignificanceToPValue(xmax) # x = p-value
  emin, emax = int(ceil(log10(pmax))), int(ceil(log10(pmin))) # exponents of p-values
  xtitle  = "Significance"
  #xtitle2 = "Log_{#lower[-0.2]{10}}(p-value)"
  xtitle2 = "p-value"
  ytitle  = "p-value"
  print(f">>> plot_customaxis_pval: xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}")
  print(f">>> plot_customaxis_pval: pmin={pmin}, pmax={pmax}, emin={emin}, emax={emax}")
  
  # PLOT
  canvas = TCanvas('canvas','canvas',100,100,1000,800) # XYWH
  canvas.SetMargin(0.11,0.03,0.11,0.12) # LRBT
  canvas.SetLogy()
  canvas.SetTicks(0,1) # draw ticks on opposite side
  
  # FRAME
  tsize = 0.050
  lsize = 0.044
  ysize = 0.98*lsize # for logarithmic axis label
  frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
  ###frame.SetMinimum(ymin)
  ###frame.SetMaximum(ymax)
  ###frame.GetYaxis().SetRangeUser(ymin,ymax)
  frame.GetXaxis().SetTitle(xtitle)
  frame.GetYaxis().SetTitle(ytitle)
  frame.GetXaxis().SetTitleOffset(0.98)
  frame.GetYaxis().SetTitleOffset(1.08)
  frame.GetXaxis().SetTitleSize(tsize)
  frame.GetYaxis().SetTitleSize(tsize)
  frame.GetXaxis().SetLabelSize(lsize)
  frame.GetYaxis().SetLabelSize(ysize)
  
  # CUSTOM AXIS on top
  fx = TF1('fx',"RooStats::PValueToSignificance(TMath::Power(10,x))",log10(pmax),log10(pmin)) # p-value
  xaxis = TGaxis(xmin,ymax,xmax,ymax,'fx',510,'-')
  xaxis.SetLineWidth(1)
  xaxis.SetLineColor(kRed)
  xaxis.SetTextFont(42)
  xaxis.SetTextColor(kRed)
  xaxis.SetTitleSize(tsize)
  xaxis.SetTitleOffset(1.08)
  xaxis.SetTitle(xtitle2)
  xaxis.SetLabelFont(42)
  xaxis.SetLabelColor(kRed)
  xaxis.SetLabelSize(lsize)
  xaxis.SetLabelOffset(7e-4)
  xaxis.Draw()
  
  # CUSTOM TICK LABELS
  for e in range(emin,emax):
    xlab = "%.1g"%(10**e) if e>=-1 else "10^{%s}"%e
    print(f">>> plot_customaxis_pval: e={e} => xlab={xlab!r}")
    xaxis.ChangeLabel(e,-1,-1,-1,-1,-1,xlab)
  
  # DRAW FUNCTION
  f1 = TF1('f1',"RooStats::SignificanceToPValue(x)",xmin,xmax) # p-value
  f1.SetLineColor(kRed)
  #f.SetTitle(f";{xtitle};{ytitle}")
  f1.SetLineWidth(3)
  f1.Draw('L SAME')
  
  # SAVE
  #canvas.RedrawAxis()
  canvas.SaveAs(fname+".png")
  #canvas.SaveAs(fname+".pdf")
  canvas.Close()
  

def main():
  plot_customaxis_log()
  plot_customaxis_pval()
  

if __name__ == "__main__":
  main()
  print(">>> Done!")
  
