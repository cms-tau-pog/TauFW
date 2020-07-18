#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test SampleStyle.py
#   test/testStyle.py -v2
from TauFW.Plotter.sample.utils import LOG, STYLE, CMSStyle, ensuredir, ensurelist
#import TauFW.Plotter.sample.SampleStyle as STYLE
from ROOT import TCanvas, TLegend, gStyle, TH1F, kBlack
gStyle.SetErrorX(0)


def testCMSera():
  """Test setCMSera"""
  LOG.header("testCMSera")
  erasets = [
   '7', '8', '2012', (7,8),
   2016, 2017, 2018, (2016,2017,2018), 'Run2',
   'Phase2',
  ]
  for eras in erasets:
    eras   = ensurelist(eras)
    args   = ','.join(repr(y) for y in eras)
    result = CMSStyle.setCMSEra(*eras)
    print ">>> CMSStyle.setCMSera(%s) = %r"%(args,result)
  

def checklegend(samples,tag=""):
  """Check legend entries: colors, titles, ..."""
  # https://root.cern.ch/doc/master/classTLegend.html
  LOG.header("checklegend"+tag.replace(' ',''))
  output = ensuredir('plots')
  fname  = "%s/testStyle_legend%s"%(output,tag)
  #height = 0.05*(len(samples))
  xdim   = 550
  ydim   = 50*(len(samples)+2)
  #width  = 0.4
  #x1, y1 = 0.1, 0.9
  print ">>> Canvas: %sx%s (nsamples=%d)"%(xdim,ydim,len(samples))
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
  canvas.SaveAs(fname+".pdf")
  canvas.Close()
  

def main():
  
  testCMSera()
  checklegend([
    'Data',
    'DY', #ZTT', 'ZL', 'ZJ',
    'W', 'QCD', 'JTF',
    'Top',
    'TT', 'ST',
    'VV',
  ])
  checklegend([
    'ZTT', 'ZL', 'ZJ',
    'TTT', 'TTL', 'TTJ',
    'STT', 'STL', 'STJ',
  ],tag="_split")
  checklegend(['ZTT_DM0','ZTT_DM1','ZTT_DM10','ZTT_DM11','ZTT_other'],tag="_DMs")
  

if __name__ == "__main__":
  main()
  print ">>>\n>>> Done."
  
