#! /usr/bin/env python
# Author: Izaak Neutelings (December 2021)
# Description: Script to compare Z pT plots from the ROOT files
from TauFW.Plotter.sample.utils import setera
from TauFW.Plotter.plot.Plot import Plot, Var, LOG, close #, getconstanthist
from TauFW.common.tools.file import ensuredir, ensureTFile, ensureTDirectory
from TauFW.common.tools.string import repkey
from ROOT import gStyle, gROOT, gSystem, gDirectory, kRed, kBlue, kDashed
ptitle   = "p_{#kern[-0.1]{#lower[-0.1]{T}}}"
mtitle   = "m_{#mu#mu}"
pgtitle  = "Z p_{#kern[-0.1]{#lower[-0.1]{T}}}"
mgtitle  = "m_{#mu#mu}"

def compareZptmass(fname,outdir=None,tag="",verb=0):
  """Compare Z pT plots."""
  LOG.header("compareZptmass()")
  
  # SETTINGS
  era      = 2018
  file     = ensureTFile(fname,'READ')
  hname    = 'zptmass'
  pname    = "%s/compare_%s_$CAT%s.png"%(outdir,hname,tag)
  outdir   = ensuredir(outdir) #repkey(outdir,CHANNEL=channel,ERA=era))
  title    = "m_{mumu} > 110 GeV"
  stitle   = "Z boson unfolding weight"
  width    = 1200 # canvas width for 1D unrolled plots
  bsize    = 0.039 # size of bin text in 1D unrolled plots
  position = 'RR;y=0.91' # legend position in 1D unrolled plots
  logx     = True and False
  logy     = True and False
  logz     = True and False
  ratio    = True #and False
  setera(era) # set era for plot style and lumi-xsec normalization
  
  # VARIABLES
  Zmbins1  = [110,150,200,400,600,1500]
  ptbins1  = [0,3,5,7,11,15,30,50,100,200,500,1000]
  nurbins  = (len(Zmbins1)-1)*(len(ptbins1)-1) # number of 2D bins (excl. under-/overflow)
  xvar     = Var('pt_moth',ptbins1,"Generated "+pgtitle,logx=logx,logy=logy) # generated Z boson pt
  yvar     = Var('m_moth', Zmbins1,"Generated "+mgtitle,logx=logx,logy=logy) # generated Z boson mass
  urbins   = (nurbins,1,1+nurbins) # unrolled
  urlabels = [str(i) if i%(len(ptbins1)-1)==1 or i in [nurbins] else " " for i in range(1,nurbins+1)]
  bvar     = Var('Unroll::GetBin(pt_moth,m_moth,0,1)',"Generated %s bin"%(pgtitle),*urbins,units=False,labels=urlabels) # unroll bin number
  
  systs = [
    "",
    "_syst_tt_up","_syst_tt_down",
    #"_syst_dy_up","_syst_dy_down"
  ]
  hists = [ ]
  histnom = None
  for syst in systs:
    hname = "control/zptmass%s_weight1D"%(syst)
    hist  = file.Get(hname)
    if syst:
      htitle = syst.replace('_syst','').replace('_',' ').strip()
      htitle = htitle.replace('tt','ttbar').replace('dy','DY')
    else:
      htitle = "Nominal"
      histnom = hist
    hist.SetTitle(htitle)
    hists.append(hist)
    if not hist:
      file.ls()
      raise IOError("compareZptmass: Did not find %r in %r"%(hname,fname))
  if histnom:
    err = 0.5
    histup = histnom.Clone(histnom.GetName()+"_up") # 1.5*hnom-0.5
    histdn = histnom.Clone(histnom.GetName()+"_dn") # 0.5*hnom+0.5
    #histup2 = histnom.Clone(histnom.GetName()+"_up_pow") # hnom^2
    #histdn2 = histnom.Clone(histnom.GetName()+"_dn_pow") # hnom^0.5
    histup.SetTitle("%d%% up"%(100.0*err))
    histdn.SetTitle("%d%% down"%(100.0*err))
    #histup2.SetTitle("^2")
    #histdn2.SetTitle("^0.5")
    ###hconst = getconstanthist(histnom,1.0,tag="one")
    ###histup.Scale(1.5)
    ###histdn.Scale(0.5)
    ###histup.Add(hconst,-0.5)
    ###histdn.Add(hconst,+0.5)
    for ibin in xrange(0,histnom.GetXaxis().GetNbins()+2):
      yval = histnom.GetBinContent(ibin)
      histup.SetBinContent(ibin,(1+err)*yval-err)
      histdn.SetBinContent(ibin,(1-err)*yval+err)
      #histup2.SetBinContent(ibin,yval**2.0)
      #histdn2.SetBinContent(ibin,yval**0.5)
    hists.extend([histup,histdn]) #,histup2,histdn2
  for hist in hists:
    if hist!=histnom: # set errors to zero, except for nominal histogram
      for ibin in xrange(0,hist.GetXaxis().GetNbins()+2):
        hist.SetBinError(ibin,0.0)
  
  # PLOT 1D - Unrolled unfolded weight 1D
  print ">>> Plotting..."
  rline  = ('min',1.,'max',1.)
  pname_ = repkey(pname,CAT="weight_1D")
  plot   = Plot(bvar,hists,dividebins=False)
  plot.draw(logx=False,logy=False,logz=False,xmin=1.0,ymin=0.2,ymax=1.8,width=width,
            style=1,grid=False,xlabelsize=0.072,labeloption='h',ratio=ratio)
  plot.drawlegend('CR',twidth=0.5)
  plot.drawline(*rline,color=kBlue)
  plot.drawtext("Unfolded weight, %s"%(title),y=0.91)
  plot.drawbins(yvar,y=0.96,size=bsize,text="m_{#mu#mu}",addoverflow=True)
  plot.saveas(pname_,ext=['.png','.pdf'])
  plot.close()
  
  file.Close()
  print ">>> "
  

def main(args):
  verbosity = args.verbosity
  fname     = "weights/zptmass_weights_mgt110_2018.root"
  outdir    = "plots"
  compareZptmass(fname,outdir=outdir,tag="",verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Compare Z pT plots from the ROOT files."""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  #parser.add_argument('-y', '--era',     dest='eras', nargs='+', default=['2017'], action='store', #choices=['2016','2017','2018','UL2017']
  #                                       help="set era" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print ">>> Done."
  
