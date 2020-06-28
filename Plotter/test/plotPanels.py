#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Study behavior of text size in multipad canvasses
from TauFW.common.tools.file import ensuredir
from ROOT import gROOT, gPad, TCanvas, TH1D
gROOT.SetBatch(True)


def plotpanels(ratio,**kwargs):
  
  # SETTING
  width   = kwargs.get('width',   800   )
  height  = kwargs.get('height',  750   )
  lmargin = kwargs.get('lmargin', 1.    )
  outdir  = ensuredir("plots/")
  fname   = 'multipad_%sx%s_%s'%(width,height,str(ratio))
  fname   = outdir+fname.replace('.','p')+'.png'
  
  # CANVAS
  canvas = TCanvas('canvas','canvas',100,100,width,height)
  canvas.SetFillColor(0)
  canvas.SetBorderMode(0)
  canvas.SetFrameBorderMode(0)
  canvas.SetMargin(0.0,0.0,0.0,0.0) # LRBT
  canvas.Divide(2)
  pad1 = canvas.GetPad(1)
  pad2 = canvas.GetPad(2)
  pad1.SetPad('pad1','pad1',0.0,ratio,1.0,1.0)
  pad1.SetMargin(0.14*lmargin,0.04,0.11,0.08)
  pad1.SetFillColor(0)
  #pad1.SetFillStyle(4000) # transparant (for pdf)
  #pad1.SetFillStyle(0)
  #pad1.SetBorderMode(0)
  pad1.Draw()
  pad2.SetPad('pad2','pad2',0.0,0.0,1.0,ratio)
  pad2.SetMargin(0.14*lmargin,0.04,0.30,0.10)
  pad2.SetFillColor(0) #pad2.SetFillColorAlpha(0,0.0)
  #pad2.SetFillStyle(4000) # transparant (for pdf)
  #pad2.SetBorderMode(0)
  pad2.Draw()
  
  # SIZES
  # https://root.cern.ch/doc/master/classTPad.html
  TH, TW = pad1.GetWh()*pad1.GetHNDC(), pad1.GetWw()*pad1.GetWNDC()
  BH, BW = pad2.GetWh()*pad2.GetHNDC(), pad2.GetWw()*pad2.GetWNDC()
  TR     = TH/TW
  BR     = BH/BW
  TM     = max(TH,TW)
  BM     = max(BH,BW)
  Tm     = min(TH,TW)
  Bm     = min(BH,BW)
  print ">>> %6s: %8s %8s %8s %8s %8s %8s  %8s"%('pad','Wh','HNDC','Wh*HNDC','Ww','WNDC','Ww*WNDC','Wh*HNDC/Ww*WNDC')
  print ">>> %6s: %8.1f %8.3f %8.1f %8.1f %8.3f %8.1f"%(
             'canvas',canvas.GetWh(),canvas.GetHNDC(),canvas.GetWh()*canvas.GetHNDC(),
                      canvas.GetWw(),canvas.GetWNDC(),canvas.GetWw()*canvas.GetWNDC())
  print ">>> %6s: %8.1f %8.3f %8.1f %8.1f %8.3f %8.1f %10.3f"%(
             'pad1',pad1.GetWh(),pad1.GetHNDC(),pad1.GetWh()*pad1.GetHNDC(),
                    pad1.GetWw(),pad1.GetWNDC(),pad1.GetWw()*pad1.GetWNDC(),TR)
  print ">>> %6s: %8.1f %8.3f %8.1f %8.1f %8.3f %8.1f %10.3f"%(
             'pad2',pad2.GetWh(),pad2.GetHNDC(),pad2.GetWh()*pad2.GetHNDC(),
                    pad2.GetWw(),pad2.GetWNDC(),pad2.GetWw()*pad2.GetWNDC(),BR)
  #scale   = 1.0
  #scale   = 1./ratio
  #scale   = (1.-ratio)/ratio
  #scale   = (1.-ratio)/ratio if canvas.GetWh()<canvas.GetWw() else ratio/(1.-ratio)
  #scale   = TR/BR
  scale   = Tm/Bm
  #scale = float(H)/W if W>H else 1 # float(W)/H
  oscale  = 1./scale
  tsize   = 0.05
  bsize   = tsize*scale
  toffset = 1.2
  boffset = toffset*oscale
  #boffset = 1.0+(toffset-1)*oscale
  print ">>> 1/r=%.4f, (1-r)/r=%.4f, HNDC1/HNDC2=%.4f, WNDC1/WNDC2=%.4f, TR/BR=%.4f, TM/BM=%.4f, Tm/Bm=%.4f"%(
             1./ratio,(1.-ratio)/ratio,pad1.GetHNDC()/pad2.GetHNDC(),pad1.GetWNDC()/pad2.GetWNDC(),TR/BR,TM/BM,Tm/Bm)
  print ">>> tsize=%.4f, bsize=%.4f, scale=%.4f"%(tsize,bsize,scale)
  print ">>> toffset=%.4f, boffset=%.4f, scale=%.4f"%(toffset,boffset,oscale)
  
  # TOP HIST
  canvas.cd(1)
  thist = TH1D('top','top',10,0,100)
  thist.GetXaxis().SetTitle("X title")
  thist.GetYaxis().SetTitle("Y title")
  print ">>> thist.GetXaxis().GetTitleOffset()=%.4f"%(thist.GetXaxis().GetTitleOffset())
  print ">>> thist.GetYaxis().GetTitleOffset()=%.4f"%(thist.GetYaxis().GetTitleOffset())
  thist.GetXaxis().SetTitleSize(tsize)
  thist.GetYaxis().SetTitleSize(tsize)
  #thist.GetXaxis().SetTitleOffset(toffset)
  thist.GetYaxis().SetTitleOffset(toffset)
  thist.GetXaxis().SetLabelSize(tsize)
  thist.GetYaxis().SetLabelSize(tsize)
  thist.Draw()
  
  # BOTTOM HIST
  canvas.cd(2)
  bhist = thist.Clone('bottom')
  bhist.SetTitle('bottom')
  bhist.GetXaxis().SetTitleSize(bsize)
  bhist.GetYaxis().SetTitleSize(bsize)
  #thist.GetXaxis().SetTitleOffset(boffset)
  bhist.GetYaxis().SetTitleOffset(boffset)
  bhist.GetXaxis().SetLabelSize(bsize)
  bhist.GetYaxis().SetLabelSize(bsize)
  bhist.Draw()
  
  # FINISH
  canvas.SaveAs(fname)
  canvas.Close()
  print ">>> "
  

def main():
  for width in [300,600,900]:
    for height in [300,600,900]:
      for ratio in [0.33]: #,0.66]:
        plotpanels(ratio=ratio,height=height,width=width)
  

if __name__ == "__main__":
  main()
  
