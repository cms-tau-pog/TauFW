#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test testCMSStyle.py
#   test/testCMSStyle.py -v2
import os, sys
#from TauFW.Plotter.sample.utils import LOG, STYLE, CMSStyle, ensuredir, ensurelist # decouple script from TauFW
#import TauFW.Plotter.sample.SampleStyle as STYLE
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, TCanvas, TLegend, TH1F, kBlack
gROOT.SetBatch(True)      # don't open GUI windows
gStyle.SetOptStat(False)  # don't make stat. box
gStyle.SetOptTitle(False) # don't make title on top of histogram
gStyle.SetErrorX(0)       # size of horizontal error bars
if not os.path.exists("CMSStyle.py"):
  sys.path.append(os.path.join(os.environ['CMSSW_BASE'],"src/TauFW/Plotter/python/plot"))
import CMSStyle
CMSStyle.setTDRStyle() # set once


def ensurelist(arg,verb=0):
  """Ensure argument is actually a list."""
  return arg if isinstance(arg,(list,tuple)) else [arg]
  

def ensuredir(dname,verb=0):
  """Make directory if it does not exist."""
  if dname and not os.path.exists(dname):
    if verb>=1:
      print(">>> Making directory %s..."%(dname))
    os.makedirs(dname)
  return dname
  

def testCMSera(verb=0):
  """Test setCMSera"""
  #LOG.header("testCMSera")
  print(">>> testCMSera")
  erasets = [
   '7', '8', '2012', (7,8),
   2016, 2017, 2018, (2016,2017,2018), 'Run2',
   'Phase2',
  ]
  for eras in erasets:
    eras   = ensurelist(eras)
    args   = ','.join(repr(y) for y in eras)
    result = CMSStyle.setCMSEra(*eras,verb=verb)
    print(">>> CMSStyle.setCMSera(%s) = %r"%(args,result))
  

def testCMSlogo(iPosX=0,width=800,height=750,lmargin=0.14,rmargin=0.04,tmargin=0.06,out=True,verb=0,**kwargs):
  """Test setCMSLumiStyle for logo placement."""
  print(">>> testCMSlogo: iPosX=%r, width=%r, height=%r, lmargin=%r, rmargin=%r, tmargin=%r, out=%r"%(
    iPosX,width,height,lmargin,rmargin,tmargin,out))
  
  # SETTING
  bmargin = 0.10
  outdir  = ensuredir("plots/")
  fname   = 'testCMSStyle_CMSlogo_pos%s_%sx%s_L%s-R%s-T%s'%(iPosX,width,height,lmargin,rmargin,tmargin)
  if out:
    fname += "_out"
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
  R, M, m = H/W, max(H,W), min(H,W)
  print(">>> %6s: %8s %8s %8s %8s %8s %8s  %8s"%('pad','Wh','HNDC','Wh*HNDC','Ww','WNDC','Ww*WNDC','Wh*HNDC/Ww*WNDC'))
  print(">>> %6s: %8.1f %8.3f %8.1f %8.1f %8.3f %8.1f"%(
             'canvas',canvas.GetWh(),canvas.GetHNDC(),canvas.GetWh()*canvas.GetHNDC(),
                      canvas.GetWw(),canvas.GetWNDC(),canvas.GetWw()*canvas.GetWNDC()))
  
  # HIST
  hist = TH1F('hist','hist',10,0,100)
  hist.GetXaxis().SetTitle("X title")
  hist.GetYaxis().SetTitle("Y title")
  hist.GetXaxis().SetTitleSize(0.045)
  hist.GetYaxis().SetTitleSize(0.045)
  hist.GetXaxis().SetLabelSize(0.040)
  hist.GetYaxis().SetLabelSize(0.040)
  hist.Draw()
  
  # CMS STYLE
  CMSStyle.outOfFrame = out
  result = CMSStyle.setCMSEra(2018)
  CMSStyle.setCMSLumiStyle(canvas,iPosX,verb=verb+2)
  
  # FINISH
  canvas.SaveAs(fname)
  canvas.Close()
  print(">>> ")
  

def checklegend(samples,tag=""):
  """Check legend entries: colors, titles, ..."""
  from TauFW.Plotter.sample.utils import LOG, STYLE
  #import TauFW.Plotter.sample.SampleStyle as STYLE
  # https://root.cern.ch/doc/master/classTLegend.html
  LOG.header("checklegend"+tag.replace(' ',''))
  #print(">>> checklegend: samples=%r"%(samples,))
  output = ensuredir('plots')
  fname  = "%s/testStyle_legend%s"%(output,tag)
  #height = 0.05*(len(samples))
  xdim   = 550
  ydim   = 50*(len(samples)+2)
  #width  = 0.4
  #x1, y1 = 0.1, 0.9
  print(">>> Canvas: %sx%s (nsamples=%d)"%(xdim,ydim,len(samples)))
  canvas = TCanvas('canvas','canvas',xdim,ydim)
  #legend = TLegend(x1,y1,x1+width,y1-height)
  legend = TLegend(0,0,1,1)
  legend.SetBorderSize(0)
  legend.SetMargin(0.12)
  #legend.SetTextSize(tsize)
  #legend.SetNColumns(ncols)
  #legend.SetColumnSeparation(colsep)
  #legend.SetHeader("HTT style",'C')
  legend.SetTextFont(42) # bold for title
  hists = [ ]
  for sample in samples:
    color = STYLE.getcolor(sample,verb=2)
    title = STYLE.gettitle(sample,latex=True,verb=2)
    style = 'ep' if 'Data' in sample else 'f'
    hist  = TH1F(sample,title,1,0,1)
    hist.SetFillColor(color)
    #hist.SetLineColor(kBlack)
    hist.SetLineWidth(2)
    hist.SetMarkerColor(kBlack)
    #hist.SetMarkerStyle(1)
    legend.AddEntry(hist,title,style)
    if 'Data' in sample: hist.Draw('E1')
    hists.append(hist)
  legend.Draw()
  canvas.SaveAs(fname+".png")
  #canvas.SaveAs(fname+".pdf")
  canvas.Close()
  

def main(args):
  verbosity = args.verbosity
  testCMSera(verb=verbosity)
  
  for ipos, out in [(0,True),(11,False)]:
    for width in [600,900]:
      for height in [600,900]:
        for lmargin in [0.07,0.14]: #,0.20]:
          for rmargin in [0.04,0.08]: #,0.16]:
            for tmargin in [0.03,0.06]: #,0.16]:
              testCMSlogo(ipos,width,height,lmargin,rmargin,tmargin,out=out,verb=verbosity)
  ###for ipos in [0,1,2,3,10,11,12,22,33]:
  ###  testCMSlogo(ipos,800,600,0.14,0.04)
  
  ###checklegend([
  ###  'Data',
  ###  'DY', #ZTT', 'ZL', 'ZJ',
  ###  'W', 'QCD', 'JTF',
  ###  'Top',
  ###  'TT', 'ST',
  ###  'VV',
  ###])
  ###checklegend([
  ###  'ZTT', 'ZL', 'ZJ',
  ###  'TTT', 'TTL', 'TTJ',
  ###  'STT', 'STL', 'STJ',
  ###],tag="_split")
  ###checklegend(['ZTT_DM0','ZTT_DM1','ZTT_DM10','ZTT_DM11','ZTT_other'],tag="_DMs")
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test CMSStyle module."""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done.")
  
