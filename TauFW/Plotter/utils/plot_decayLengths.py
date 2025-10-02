#! /usr/bin/env python3
# Author: Izaak Neutelings (October 2023)
# Description: Plot decay length for given mass and lifetime range
# Instructions:
# Animate:
#    convert -delay 15 -loop 0 -density 600 -despeckle -dispose previous `ls -1 /eos/user/i/ineuteli/www/forCMG/decaylength_*.png | sort -V` -resize 600 -coalesce -layers optimize decayLengths.gif
print(">>> Importing ROOT...")
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gSystem, gStyle, TCanvas, TH2F, TF1, TF2, TGaxis, TLine, TLatex,\
  kBlack, kRed, kBlue, kGreen, kMagenta, kSpring, kOrange
gROOT.SetBatch(True)       # don't open GUI windows
gStyle.SetOptTitle(False)  # don't make title on top of histogram
gStyle.SetOptStat(False)   # don't make stat. box
print(">>> Done importing...")


def plot_decay_length(pc=50,verb=0):
  
  # FUNCTIONS
  xmin, xmax = 2, 20      # x = mass m
  ymin, ymax = 1e-3, 1e4  # y = lifetime ctau
  zmin, zmax = 1e-2, 1e4  # z = decay length L
  ymid = 3e0 # split for extension with finer granularity on log scale
  form = f"max({1.05*zmin},({pc}/x)*y)"
  f2 = TF2('f2',form,xmin,xmax,ymid,ymax)
  f3 = TF2('f3',form,xmin,xmax,ymin,ymid) # extend for finer granularity
  xtitle = "Mass m_{N} [GeV/c^{#lower[0.25]{2}}]"
  ytitle = "Lifetime c#tau_{#lower[-0.05]{0}} [mm]"
  ztitle = "Decay length L = #gamma#betac#tau_{#lower[-0.25]{0}} (pc = %s GeV) [mm]"%(pc)
  f2.SetTitle(f";{xtitle};{ytitle};{ztitle}")
  f2.SetNpy(10000) # increase number of drawing points
  f3.SetNpy(10000) # increase number of drawing points
  f2.SetContour(200) # increase number of contour levels
  f3.SetContour(200) # increase number of contour levels
  
  # FRAME
  tsize = 0.050
  lsize = 0.044
  ysize = 0.98*lsize # for logarithmic axis label
  fname = f"decayLength_{pc}"
  frame = TH2F('frame',f";{xtitle};{ytitle};{ztitle}",10,xmin,xmax,10,ymin,ymax)
  frame.SetBinContent(2,2,30)
  #zmin = f3.GetMinimum()
  #zmax = f2.GetMaximum()
  print(f">>> plot_decay_length: f2.GetMinimum()={f2.GetMinimum()}, f2.GetMaximum()={f2.GetMaximum()}")
  print(f">>> plot_decay_length: f3.GetMinimum()={f3.GetMinimum()}, f3.GetMaximum()={f3.GetMaximum()}")
  #f2.SetMinimum(zmin)
  #f3.SetMinimum(zmin)
  #f2.SetMaximum(zmax)
  #f3.SetMaximum(zmax)
  frame.SetContour(200)
  frame.SetMinimum(zmin)
  frame.SetMaximum(zmax)
  frame.GetYaxis().SetRangeUser(ymin,ymax)
  #f2.GetZaxis().SetRangeUser(zmin,zmax)
  #f3.GetZaxis().SetRangeUser(zmin,zmax)
  frame.GetZaxis().SetRangeUser(zmin,zmax)
  print(f">>> plot_decay_length: xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}, zmin={zmin}, zmax={zmax}")
  frame.GetXaxis().SetTitleOffset(0.97)
  frame.GetYaxis().SetTitleOffset(1.03)
  frame.GetZaxis().SetTitleOffset(1.15)
  frame.GetZaxis().SetLabelOffset(1e-8)
  frame.GetZaxis().CenterTitle()
  frame.GetXaxis().SetTitleSize(tsize)
  frame.GetYaxis().SetTitleSize(tsize)
  frame.GetZaxis().SetTitleSize(tsize)
  frame.GetXaxis().SetLabelSize(lsize)
  frame.GetYaxis().SetLabelSize(ysize)
  frame.GetZaxis().SetLabelSize(ysize)
  #frame.GetXaxis().SetNdivisions(510,False)
  
  # LINE
  lcol  = kRed+1
  latex = TLatex()
  latex.SetTextFont(42)
  latex.SetTextAlign(31)
  latex.SetTextSize(0.85*lsize)
  latex.SetNDC(False)
  latex.SetTextAngle(3)
  latex.SetTextColor(lcol)
  lines = [ ]
  for L, text in [
    (1e-2,"10 #mum"),(1e-1,"100 #mum"),(1e0,"1 mm"),
    (1e1,"1 cm"),
    (1e2,"10 cm"),(1e3,"1 m"),(1e4,"10 m"),
  ]: # mm
    line = TF1(f'f1_{L}',f"x*{L}/{pc}",xmin,xmax)
    line.SetLineWidth(2)
    line.SetLineColor(lcol)
    line.SetTitle(f"L = {text}")
    lines.append(line)
  
  # PLOT
  lmarg, tmarg = 0.11, 0.025 #0.12
  canvas = TCanvas('canvas','canvas',100,100,1000,800) # XYWH
  canvas.SetMargin(lmarg,0.17,0.12,tmarg) # LRBT
  canvas.SetLogy()
  canvas.SetLogz()
  canvas.SetTicks(1,1)
  frame.Draw('COLZ')
  f2.Draw('COL SAME')
  f3.Draw('COL SAME')
  
  # LINES & TEXT
  for line in lines:
    line.Draw('LSAME')
    x = xmin+0.96*(xmax-xmin)
    y = line.Eval(x)
    if y>ymin and y<0.6*ymax:
      y *= (1.28 if '#mu' in line.GetTitle() else 1.18) # shift up
      latex.DrawLatex(x,y,line.GetTitle())
  latex.SetTextAlign(13)
  latex.SetTextSize(0.045)
  latex.SetTextAngle(0)
  latex.SetTextColor(kBlack)
  latex.SetNDC(True) # normalized coordinates
  latex.DrawLatex(lmarg+0.04,0.96-tmarg,f"pc = {pc} GeV")
  
  #### TOP AXIS
  ###f_ax = TF1('f_ax',f"{pc}/x",float(pc)/xmax,float(pc)/xmin)
  ###axis = TGaxis(xmin,ymax,xmax,ymax,'f_ax',1004,'-')
  ####axis.SetNdivisions(1004,False)
  ###axis.SetLabelFont(42)
  ###axis.SetTextFont(42)
  ###axis.SetTextColor(kBlue+3)
  ###axis.SetLineWidth(1)
  ###axis.SetLineColor(kBlue+3)
  ###axis.SetLabelSize(lsize)
  ###axis.SetTitleSize(tsize)
  ###axis.SetTitle("#gamma#beta = %s GeV / mc^{#lower[0.2]{2}}"%(pc))
  ###axis.SetLabelOffset(2e-3)
  ###axis.Draw()
  
  # SAVE
  canvas.RedrawAxis()
  canvas.SaveAs(fname+".png")
  canvas.SaveAs(fname+".pdf")
  canvas.Close()
  

def main():
  pcs = [
    10, 20, 30,
    40, 50,
    60,
  ]
  pcs = list(range(1,61))
  for pc in pcs:
    plot_decay_length(pc,verb=2)
  

if __name__ == "__main__":
  main()
  print(">>> Done.")
  
