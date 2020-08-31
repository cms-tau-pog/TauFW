#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test SampleStyle.py
#   test/testLatex.py -v2 && eog plots/testLatex.png
from TauFW.Plotter.plot.utils import LOG, ensuredir
from TauFW.Plotter.plot.string import makelatex
from ROOT import TCanvas, TPaveText


def checklatex(texts,tag=""):
  """Check legend entries: colors, titles, ..."""
  # https://root.cern.ch/doc/master/classTPaveText.html
  LOG.header("checklegend"+tag.replace('_',' '))
  output = ensuredir('plots')
  fname  = "%s/testLatex%s"%(output,tag)
  xdim   = 500
  ydim   = 50*(len(texts)+2.5)
  print ">>> Canvas: %sx%s (nlines=%d)"%(xdim,ydim,len(texts))
  canvas = TCanvas('canvas','canvas',xdim,int(ydim))
  #pave1  = TPaveText(0.0,0,0.5,1,'ARC') #,'BR')
  pave2  = TPaveText(0.04,0.04,0.96,0.96) #'ARC') #,'BR')
  #pave1.SetBorderSize(0)
  pave2.SetBorderSize(0)
  #pave1.SetTextAlign(12)
  pave2.SetTextAlign(12)
  #pave1.SetTextFont(42)
  pave2.SetTextFont(42)
  #pave1.SetFillColor(0)
  pave2.SetFillColor(0)
  #pave1.SetCornerRadius(0.05)
  #pave2.SetCornerRadius(0.05)
  #pave1.SetMargin(0.12)
  #pave1.SetTextSize(tsize)
  #pave2.Copy(pave1)
  for line in texts:
    latex = makelatex(line)
    print ">>> %r -> %r"%(line,latex)
    #pave1.AddText(line)
    pave2.AddText(latex)
  #pave1.Draw()
  pave2.Draw()
  canvas.SaveAs(fname+".png")
  #canvas.SaveAs(fname+".pdf")
  canvas.Close()
  

def main():
  
  checklatex([
    'pt','pT','PT','p_t','p_T','P_t','P_T',
    "Forward jet pt", "Forward jet pt (|eta|<2.5)",
    "Forward jet eta", "Forward jet eta (pt>30)", "Forward jet eta (pt > 30 GeV)",
  ],tag='_pt')
  checklatex([
    'mt','mT','MT','m_t','m_T','M_t','M_T',
  ],tag='_mt')
  checklatex([
    'st','sT','ST','s_t','s_T','S_t','S_T',
    'stmet','STMET',
    'pt_1+pt_2+jpt_1', 'pt_1+pt_2+jpt_1+met'
  ],tag='_st')
  checklatex([
    'Z -> tautau',
    'Z -> tautau_h',
    'Z -> tauhtauh',
    'Z -> tau_htau_h',
    'Z -> tautau_{h}',
    'Z -> tau_mutau_{h}',
    'Z -> tau_mu tau_{h}',
    '{Z -> tau_mu tau_h}',
  ],tag='_ZTT')
  checklatex([
    'pt_1 / pt_2',
    'pt_1 + pt_2',
    'min(pt_1,pt_2)',
    'mt(mu,tau)',
  ],tag='_recursive')
  checklatex([
    'mutau',
    'etau',
    'tautau',
    'mutau_h',
    'tau_htau_h',
    'tau_{h}tau_{h}',
    'mutau: baseline',
    'tau_{h}tau_{h}: baseline',
  ],tag='_text')
  checklatex([
    "DR", "dR", "DeltaR", "Drell-Yan",
    "DR_mutau_h",
    "DR_etau_h",
    "DR_tautau",
    "DR_tauhtauh",
    "DR_tau_htau_h",
    "DR_emu",
  ],tag='_DR')
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''Script to test the Plot class for comparing histograms.'''
  parser = ArgumentParser(prog="testLatex",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  print ">>>\n>>> Done."
  
