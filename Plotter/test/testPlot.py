#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test script for Plot class
#   python3 test/testPlot.py -v2 && eog plots/test/testPlot*.png
from TauFW.Plotter.plot.utils import LOG, ensuredir, deletehist
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
from TauFW.common.tools.root import rootrepr
from ROOT import gRandom, TH1F, TGraph, TGraphErrors,\
                 kSolid, kDashed, kDotted, kBlue, kGreen, kRed, kBlack


def testPlot_init(xtitle,hists,norm=False,clone=False):
  """Test Plot.__init__ with different arguments."""
  from TauFW.Plotter.plot.Plot import Var
  
  # SETTING
  outdir = ensuredir("plots/test/")
  fname  = outdir+"testPlot_init"
  if clone:
    fname += "_clone" # clone each histogram
  if norm:
    fname += "_norm" # normalize each histogram
  
  # CREATE DIFFERENT ARGUMENTS
  xvar  = Var('x',xtitle,100,0,100)
  hists1 = clonehists(hists,t='a')
  hists2 = clonehists(hists,t='b')
  #graphs = hists2graphs(hists)
  h1, h2, h3 = hists2[:3] # assume at least three
  argset = [
    (hists1),
    (h1,h2,h3),
  ]
  for i, x in enumerate([xtitle,xvar],1):
    hists1 = clonehists(hists,t='c%s'%i)
    hists2 = clonehists(hists,t='d%s'%i)
    h1, h2, h3 = hists2[:3] # assume at least three
    argset += [
      (x,hists1),
      (x,h1,h2,h3),
    ]
  
  # PLOT
  for i, args in enumerate(argset,1):
    fname_ = "%s_%s"%(fname,i)
    LOG.header("%s"%(fname_))
    print(">>> args=%s"%(rootrepr(args)))
    print(">>> norm=%r, clone=%r"%(norm,clone))
    plot = Plot(*args,norm=norm,clone=clone)
    plot.draw(ratio=False)
    #plot.drawtext(text)
    plot.saveas(fname_+".png")
    plot.close()
    print('')
  

def plothist(xtitle,hists,ratio=False,logy=False,logx=False,norm=False,cwidth=None,pre="",tag="",**kwargs):
  """Plot comparison of histograms."""
  
  # SETTING
  outdir   = ensuredir("plots/test/")
  fname    = outdir+"testPlot"+pre
  if ratio:
    fname += "_ratio"
  if logy:
    fname += "_logy"
  if logx:
    fname += "_logx"
  if norm:
    fname += "_norm" # normalize each histogram
  if cwidth:
    fname += "_W%d"%(cwidth)
  fname   += tag
  rrange   = 0.5
  lwidth   = 0.2             # legend width
  position = 'topright'      # legend position
  header   = "Gaussians"     # legend header
  text     = "#mu#tau_{h}"   # corner text
  grid     = True #and False
  kwargs.setdefault('staterr', True and False) # add uncertainty band to first histogram
  if not kwargs.get('pair',False) and not kwargs.get('triple',False):
    kwargs.setdefault('lstyle',1) # solid lines
  
  # PLOT
  LOG.header(fname)
  print(">>> norm=%r, ratio=%r, logy=%r, logx=%r, cwidth=%r"%(norm,ratio,logy,logx,cwidth))
  plot = Plot(xtitle,hists,norm=norm)
  plot.draw(ratio=ratio,logy=logy,logx=logx,ratiorange=rrange,width=cwidth,grid=grid,**kwargs)
  plot.drawlegend(position,header=header,width=lwidth)
  plot.drawtext(text)
  plot.saveas(fname+".png")
  plot.saveas(fname+".pdf")
  #plot.saveas(fname+".C")
  #plot.saveas(fname+".png",fname+".C")
  #plot.saveas(fname,ext=['png','pdf'])
  plot.close()
  print('')
  

def createhists(nhist=3,nbins=50,sigma=10,graph=False):
  """Create some histograms of gaussian distributions."""
  xmin   = 0
  xmax   = 100
  nevts  = 10000
  rrange = 0.5
  hists  = [ ]
  gRandom.SetSeed(1777)
  for i in range(1,nhist+1):
    mu     = 50.+sigma/5.*(i-nhist/2.)
    hname  = "hist%d"%(i)
    htitle = "#mu = %s, #sigma = %s"%(mu,sigma)
    hist   = TH1F(hname,hname,nbins,xmin,xmax)
    for j in range(nevts):
      hist.Fill(gRandom.Gaus(mu,sigma))
    hists.append(hist)
  if graph:
    return hists2graphs(hists)
  return hists
  

def clonehists(hists,t=''):
  """Clone histogram with unique name."""
  return [h.Clone(h.GetName()+"_clone%s%s"%(i,t)) for i, h in enumerate(hists,1)]
  

def hists2graphs(hists):
  """Convert histogram to TGraphErrors."""
  graphs = [ ]
  for hist in hists:
    graph = TGraphErrors()
    graph.SetName(hist.GetName().replace('hist','graph'))
    graph.SetTitle(hist.GetTitle().replace('hist','graph'))
    for ip in range(hist.GetXaxis().GetNbins()):
      ibin = ip+1
      x, y = hist.GetXaxis().GetBinCenter(ibin), hist.GetBinContent(ibin)
      w, e = hist.GetXaxis().GetBinWidth(ibin)/2, hist.GetBinError(ibin)
      #print(ip,ibin,x,y,w,e)
      graph.SetPoint(ip,x,y)
      graph.SetPointError(ip,w,e)
    graphs.append(graph)
  return graphs
  

def main():
  
  CMSStyle.setCMSEra(2018)
  xtitle = "p_{T}^{MET} [GeV]"
  #xtitle = "Leading jet p_{T} [GeV]"
  ratios  = [True,False]
  logxs   = [True,False]
  logys   = [True,False]
  norms   = [True,False]
  cwidths = [800,500,1400]
  
  # TEST PLOTTING ROUTINE with different combination of common style options
  #plothist(variable,hists,ratio=False,logy=False)
  if 'hist' in args.methods:
    for ratio in ratios:
      for logy in logys:
        #if logy and ratio: continue # reduce number of plots produced
        for logx in logxs:
          for norm in norms:
            for cwidth in cwidths:
              if (norm or logy or logx) and cwidth!=800: continue # reduce number of plots produced
              #for cwidth in [None,1000]:
              hists = createhists()
              plothist(xtitle,hists,ratio=ratio,logy=logy,logx=logx,norm=norm,cwidth=cwidth)
  
  # TEST FRAME
  #plothist(variable,hists,ratio=False,logy=False)
  if 'frame' in args.methods:
    kwargset = [
#       { 'tag': "_x10-max", 'logx': False, 'xmin': 10 },
#       { 'tag': "_x10-200", 'logx': False, 'xmin': 10, 'xmax': 200, },
      { 'tag': "", 'logx': True  },
      { 'tag': "_x10-max", 'logx': True, 'xmin': 10, },
      { 'tag': "_x10-200", 'logx': True, 'xmin': 10, 'xmax': 200, },
    ]
    for kwargs in kwargset:
      hists = createhists(4,nbins=20,sigma=25)
      plothist(xtitle,hists,pre='_frame',ratio=True,logy=False,rmin=0,rmax=3,**kwargs)
  
  # TEST DRAW STYLES
  #plothist(variable,hists,ratio=False,logy=False)
  if 'style' in args.methods:
    lcols  = [ kBlue+1, kRed+1, kGreen+1, kBlack ]
    kwargset = [
      { 'tag': "" },
      { 'tag': "_lcols", 'colors': lcols },
      { 'tag': "_lcols_staterr", 'colors': lcols, 'staterr': True },
      { 'tag': "_lcols_mstyles1", 'colors': lcols, 'lstyle': False, 'mstyle': ['data'] },
      { 'tag': "_lcols_mstyles2", 'colors': lcols, 'lstyle': False, 'mstyle': ['data','hist'] },
      { 'tag': "_lcols_mstyles3", 'colors': lcols, 'lstyle': False, 'mstyle': ['hist','hist','hist','data'], 'options': ['HIST','HIST','HIST','E0'] },
      { 'tag': "_pairs", 'colors': lcols, 'pair': True },
      { 'tag': "_triple", 'colors': lcols, 'triple': True, 'mstyle': [kSolid,kDashed,kDotted] },
    ]
    for kwargs in kwargset:
      nhists = 6 if kwargs.get('triple',False) else 4
      hists  = createhists(nhists,nbins=25)
      graphs = hists2graphs(hists)
      plothist(xtitle,hists,pre='_style_hist',ratio=True,logy=False,**kwargs)
      if 'options' in kwargs:
        kwargs['options'] = [o.replace('E0','PE0').replace('HIST','').strip() for o in kwargs['options']]
      plothist(xtitle,graphs,pre='_style_graph',ratio=True,logy=False,**kwargs)
  
  # TEST PLOTTING ROUTINE for GRAPHS
  if 'graph' in args.methods:
    for ratio in ratios:
      for logy in logys:
        #if (ratio or logy) and cwidth!=800: continue # reduce number of plots produced
        graphs = hists2graphs(createhists())
        plothist(xtitle,graphs,pre="_graph",ratio=ratio,logy=logy,norm=False)
  
  # TEST INITIATION with different arguments
  if 'init' in args.methods:
    for clone in [True,False]:
      for norm in [True,False]:
        hists = createhists(3)
        testPlot_init(xtitle,hists,norm=norm,clone=clone)
        deletehist(hists)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  methods = ['hist','graph','init','style','frame'] # different unit tests
  description = '''Script to test the Plot class for comparing histograms.'''
  parser = ArgumentParser(description=description,epilog="Good luck!")
  parser.add_argument('-m', '--method',  dest='methods', choices=methods, nargs='+', default=methods,
                                         help="method to test" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0,
                                         help="set verbosity level" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  
