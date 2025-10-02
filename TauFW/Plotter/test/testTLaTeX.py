#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test testTLaTeX.py
#   test/testTLaTeX.py -v2
import os, sys
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, TCanvas, TLatex, TH1F, kBlack
gROOT.SetBatch(True)      # don't open GUI windows
gStyle.SetOptStat(False)  # don't make stat. box
gStyle.SetOptTitle(False) # don't make title on top of histogram
gStyle.SetErrorX(0)       # size of horizontal error bars
  

def ensuredir(dname,verb=0):
  """Make directory if it does not exist."""
  if dname and not os.path.exists(dname):
    if verb>=1:
      print(">>> Making directory %s..."%(dname))
    os.makedirs(dname)
  return dname
  

def testCMSlogo(iPosX=0,width=800,height=750,lmargin=0.14,rmargin=0.04,tmargin=0.06,verb=0,**kwargs):
  """Test setCMSLumiStyle for logo placement."""
  print(">>> testCMSlogo: iPosX=%r, width=%r, height=%r, lmargin=%r, rmargin=%r, tmargin=%r"%(
    iPosX,width,height,lmargin,rmargin,tmargin))
  
  # SETTING
  bmargin = 0.10
  outdir  = ensuredir("plots/")
  fname   = 'testTLaTeX_CMSlogo_pos%s_%sx%s_L%s-R%s-T%s'%(iPosX,width,height,lmargin,rmargin,tmargin)
  fname   = outdir+fname.replace('.','p')+'.png'
  
  # CANVAS
  canvas = TCanvas('canvas','canvas',100,100,width,height)
  canvas.SetFillColor(0)
  canvas.SetBorderMode(0)
  canvas.SetFrameBorderMode(0)
  canvas.SetMargin(lmargin,rmargin,bmargin,tmargin) # LRBT
  canvas.SetFillColor(0)
  
  # SIZES
  # https://root.cern.ch/doc/master/classTPad.html
  H, W = canvas.GetWh()*canvas.GetHNDC(), canvas.GetWw()*canvas.GetWNDC()
  #R, M, m = H/W, max(H,W), min(H,W)
  #print(">>> %6s: %8s %8s %8s %8s %8s %8s  %8s"%('pad','Wh','HNDC','Wh*HNDC','Ww','WNDC','Ww*WNDC','Wh*HNDC/Ww*WNDC'))
  #print(">>> %6s: %8.1f %8.3f %8.1f %8.1f %8.3f %8.1f"%(
  #           'canvas',canvas.GetWh(),canvas.GetHNDC(),canvas.GetWh()*canvas.GetHNDC(),
  #                    canvas.GetWw(),canvas.GetWNDC(),canvas.GetWw()*canvas.GetWNDC()))
  
  # HIST
  hist = TH1F('hist','hist',10,0,100)
  hist.GetXaxis().SetTitle("X title")
  hist.GetYaxis().SetTitle("Y title")
  hist.GetXaxis().SetTitleSize(0.045)
  hist.GetYaxis().SetTitleSize(0.045)
  hist.GetXaxis().SetLabelSize(0.040)
  hist.GetYaxis().SetLabelSize(0.040)
  hist.Draw()
  
  # TEXT SETTINGS
  cmsText        = "CMS"
  extraText      = "Preliminary"
  cmsTextFont    = 61 # 60: Arial bold (helvetica-bold-r-normal)
  extraTextFont  = 52 # 50: Arial italics (helvetica-medium-o-normal)
  lumiTextOffset = 0.20
  cmsTextSize    = 1.00
  extraOverCmsTextSize = 0.78
  extraTextSize  = extraOverCmsTextSize*cmsTextSize
  
  # POSITION SETTINGS
  relPosX = 0.045
  l       = canvas.GetLeftMargin()
  t       = canvas.GetTopMargin()
  scale   = float(H)/W if W>H else 1 # float(W)/H
  relPosX = relPosX*(42*t*scale)*(cmsTextSize/0.84) # scale
  
  # CMS LOGO
  latex = TLatex()
  latex.SetNDC()
  latex.SetTextAngle(0)
  latex.SetTextColor(kBlack)
  latex.SetTextFont(cmsTextFont)
  latex.SetTextAlign(11) # bottom left
  latex.SetTextSize(cmsTextSize*t)
  latex.DrawLatex(l,1-t+lumiTextOffset*t,cmsText)
  
  # EXTRA TEXT
  posX = l + relPosX
  posY = 1 - t + lumiTextOffset*t
  latex.SetTextFont(extraTextFont)
  latex.SetTextSize(extraTextSize*t)
  latex.SetTextAlign(11) # bottom left
  print(">>> l=%r, relPosX=%r, posX=%r"%(l,relPosX,posX))
  import ctypes
  w, h = ctypes.c_uint(), ctypes.c_uint()
  latex.GetBoundingBox(w,h)
  print(">>> latex.GetXsize()=%r, latex.GetXsize()=%r"%(latex.GetXsize(),(w.value,h.value)))
  latex.DrawLatex(posX,posY,extraText)
  
  # FINISH
  canvas.SaveAs(fname)
  canvas.Close()
  print(">>> ")
  

def main(args):
  verbosity = args.verbosity
  for ipos, out in [(0,True),(11,False)]:
    for width in [600,900]:
      for height in [600,900]:
        for lmargin in [0.07,0.14]: #,0.20]:
          for rmargin in [0.04,0.08]: #,0.16]:
            for tmargin in [0.03,0.06]: #,0.16]:
              testCMSlogo(ipos,width,height,lmargin,rmargin,tmargin,verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test TLaTeX module."""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done.")
  
