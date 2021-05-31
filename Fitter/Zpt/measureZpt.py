#! /usr/bin/env python
# Author: Izaak Neutelings (January 2021)
# Description: Script to measure Z pt reweighting based on dimuon events
#   ./measureZpt.py -y 2018
from utils import *
from TauFW.Plotter.plot.Plot2D import Plot2D
gSystem.Load('RooUnfold/libRooUnfold.so')
from ROOT import RooUnfoldResponse, RooUnfoldBinByBin, kRed, kDashed

ptitle   = "p_{T}(#mu#mu) [GeV]"
mtitle   = "m_{#mu#mu} [GeV]"
baseline = "q_1*q_2<0 && iso_1<0.15 && iso_1<0.15 && !extraelec_veto && !extramuon_veto && m_vis>20"
Zmbins0  = [20,30,40,50,60,70,80,85,88,89,89.5,90,90.5,91,91.5,92,93,94,95,100,110,120,180,500,1000]
Zmbins1  = [20,70,91,110,150,200,300,500,800,1500]
ptbins0  = [0,5,10,15,20,25,30,35,40,45,50,60,70,100,140,200,300,500,1000]
ptbins1  = [0,5,15,30,50,100,200,500,1000]
nurbins  = (len(Zmbins1)-1)*(len(ptbins1)-1) # number of 2D bins (excl. under-/overflow)
urbins0  = (nurbins,1,1+nurbins) # unrolled


def measureZptmass_unfold(samples,outdir='weights',plotdir=None,parallel=True,tag=""):
  """Measure Z pT weights in dimuon pT and mass by unfolding.
  Unroll 2D histogram using the Unroll.cxx macro to 1D histogram (with integer bin numbers)."""
  LOG.header("measureZptmass_unfold()")
  gROOT.ProcessLine(".L ../../Plotter/python/macros/Unroll.cxx+O")
  from ROOT import Unroll
  
  # SETTINGS
  hname     = 'zptmass'
  fname     = "%s/%s_weight_$CAT%s.root"%(outdir,hname,tag)
  pname     = "%s/%s_$CAT%s.png"%(plotdir or outdir,hname,tag)
  outdir    = ensuredir(outdir) #repkey(outdir,CHANNEL=channel,ERA=era))
  stitle    = "Z boson unfolding weight"
  logx      = True #and False
  logy      = True #and False
  logz      = True #and False
  method    = None #'QCD'
  verbosity = 1
  dysample  = samples.get('DY',unique=True)
  
  # SELECTIONS
  selections = [
    Sel('baseline', baseline),
  ]
  xvar_reco = Var('pt_ll',  ptbins1,"Reco-level "+ptitle) # pt_mumu
  yvar_reco = Var('m_ll',   Zmbins1,"Reco-level "+mtitle) # m_mumu
  xvar_gen  = Var('pt_moth',ptbins1,"Gen-level "+ptitle) # Z boson pt
  yvar_gen  = Var('m_moth', Zmbins1,"Gen-level "+mtitle) # Z boson mass
  bvar_reco = Var('Unroll::GetBin(pt_ll,m_ll)',"Reco-level bin(p_{T}^{#mu#mu},m_{#mu#mu})",*urbins0) # unroll bin number
  bvar_gen  = Var('Unroll::GetBin(pt_moth,m_moth)',"Gen-level bin(p_{T}^{Z},m_{Z})",*urbins0) # unroll bin number
  print ">>> %d 2D bins = %d pt bins x %d mass bins"%(bvar_reco.nbins,xvar_reco.nbins,yvar_reco.nbins)
  
  for selection in selections:
    LOG.color(selection.title,col='green')
    print ">>> selection: %r"%(selection.selection)
    for var in [xvar_reco,xvar_gen,yvar_reco,yvar_gen,bvar_reco,bvar_gen]:
      var.changecontext(selection.selection)
    fname_ = repkey(fname,CAT=selection.filename).replace('_baseline',"")
    
    print ">>> Unfold reco-level weights as a function of %s"%(xvar_reco.title)
    outfile = ensureTFile(fname_,'UPDATE')
    ctrldir = ensureTDirectory(outfile,"control",cd=False)
    
    # DY HISTOGRAMS
    print ">>> Creating DY distributions..."
    dyhist2D_reco = dysample.gethist2D(xvar_reco,yvar_reco,selection,split=False,parallel=parallel)
    dyhist2D_gen  = dysample.gethist2D(xvar_gen, yvar_gen ,selection,split=False,parallel=parallel)
    Unroll.SetBins(dyhist2D_reco,verbosity) # set bin axes for Unroll.GetBin
    
    # RECO HISTOGRAMS
    print ">>> Creating reco-level distributions..."
    hists = samples.gethists(bvar_reco,selection,split=False,blind=False,method=method,signal=False,parallel=parallel)
    obshist, exphist, dyhist, bkghist = getdyhist(hname,hists,"_reco",verb=2)
    dyhist_gen = dysample.gethist(bvar_gen,selection,split=False,parallel=parallel)
    
    # OBSERVED DY = DATA - BKG
    obsdyhist = obshist.Clone(hname+"_obsdy")
    obsdyhist.SetBinErrorOption(obshist.kNormal)
    obsdyhist.Add(bkghist,-1)
    
    # 4D RESPONSE MATRIX unrolled to 2D via Unroll::GetBin
    print ">>> Creating response matrix..."
    resphist = dysample.gethist2D(bvar_reco,bvar_gen,selection,split=False,parallel=False) # parallel fails for many bins
    
    # UNFOLD
    print ">>> Creating RooUnfoldResponse..."
    resp   = RooUnfoldResponse(dyhist,dyhist_gen,resphist)
    print ">>> Creating RooUnfoldBinByBin..."
    unfold = RooUnfoldBinByBin(resp,obsdyhist)
    #unfold.unfold()
    print ">>> Creating Hreco..."
    dyhist_unf = unfold.Hreco()
    sfhist1D = dyhist_unf.Clone(hname+"_weight")
    sfhist1D.Divide(dyhist_gen)
    dyhist2D_unf = Unroll.RollUp(dyhist_unf,hname+"_dy_unfold_2D",dyhist2D_reco)
    sfhist2D     = Unroll.RollUp(sfhist1D,  hname+"_weight_2D",dyhist2D_reco)
    
    # WRITE
    print ">>> Writing histograms to %s..."%(outfile.GetPath())
    outfile.cd()
    writehist(sfhist2D,     hname+"_weight",      "Z boson unfolding weight",xvar_gen.title,yvar_gen.title,stitle)
    ctrldir.cd()
    writehist(obshist,      hname+"_obs_reco",    "Observed",           bvar_reco.title,"Events")
    writehist(exphist,      hname+"_exp_reco",    "Expected",           bvar_reco.title,"Events")
    writehist(bkghist,      hname+"_bkg_reco",    "Exp. background",    bvar_reco.title,"Events")
    writehist(dyhist,       hname+"_dy_reco",     "Drell-Yan reco",     bvar_reco.title,"Events")
    writehist(dyhist2D_reco,hname+"_dy_reco2D",   "Drell-Yan reco",     xvar_reco.title,yvar_reco.title, "Events")
    writehist(obsdyhist,    hname+"_obsdy_reco",  "Obs. - bkg.",        bvar_reco.title,"Events")
    writehist(dyhist_gen,   hname+"_dy_gen",      "Drell-Yan generator",bvar_gen.title, "Events")
    writehist(dyhist2D_gen, hname+"_dy_gen2D",    "Drell-Yan generator",xvar_gen.title,yvar_gen.title, "Events")
    writehist(dyhist_unf,   hname+"_dy_unfold",   "Drell-Yan unfolded", bvar_gen.title, "Events")
    writehist(dyhist2D_unf, hname+"_dy_unfold_2D","Drell-Yan unfolded", xvar_gen.title,yvar_gen.title,"Events")
    writehist(resphist,     hname+"_dy_response", "Response matrix",    bvar_gen.title,bvar_reco.title,"Events")
    writehist(sfhist1D,     hname+"_weight_1D",   "Z boson unfolding weight (unrolled)",xvar_reco.title,stitle)
    writehist(sfhist2D,     hname+"_weight_2D",   "Z boson unfolding weight",xvar_gen.title,yvar_gen.title,stitle)
    
    # PLOT - weight 1D
    print ">>> Plotting..."
    rline  = (bvar_reco.min,1.,bvar_reco.max,1.)
    pname_ = repkey(pname,CAT="weight_1D_"+selection.filename).replace('_baseline',"")
    plot   = Plot(bvar_reco,sfhist1D,dividebins=False)
    plot.draw(logx=False,xmin=1.0,ymin=0.2,ymax=1.8)
    plot.drawline(*rline,color=kRed,title=stitle)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    for i in range(1,yvar_reco.nbins):
      x = bvar_reco.min + (bvar_reco.max-bvar_reco.min)*i/yvar_reco.nbins
      plot.drawline(x,0.2,x,1.8,color=kRed,style=kDashed,title=stitle)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight_1D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - weight 2D
    pname_ = repkey(pname,CAT="weight_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_reco,yvar_gen,sfhist2D)
    plot.draw(logx=logx,logy=logy,xmin=1.0,ztitle="Events")
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("weight_2D",gStyle.kOverwrite)
    plot.close()
    
    ## PLOT - Drell-Yan xvar distribution
    #pname_ = repkey(pname,CAT="dy_"+selection.filename+xvar_reco.filename).replace('_baseline',"")
    #plot   = Plot(xvar_reco,dyhist2D_reco,clone=True,dividebins=True,ratio=True)
    #plot.draw(ptitle,logx=logx,logy=logy,xmin=1.0,title="Events / GeV",style=1)
    #for i in range(1,yvar_reco.nbins):
    #  x = bvar_reco.min + (bvar_reco.max-bvar_reco.min)*i/yvar_reco.nbins
    #  plot.drawline(x,plot.ymin,x,plot.ymax,color=kRed,style=kDashed,title=stitle)
    #plot.drawlegend()
    #plot.drawtext(selection.title)
    #plot.saveas(pname_,ext=['.png','.pdf'])
    #plot.canvas.Write("dy",gStyle.kOverwrite)
    #plot.close()
    
    # PLOT - Drell-Yan distributions
    pname_ = repkey(pname,CAT="dy_"+selection.filename).replace('_baseline',"")
    plot   = Plot(bvar_reco,[dyhist,obsdyhist,dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    plot.draw(ptitle,logx=False,logy=logy,xmin=1.0,ymin=10,title="Events / GeV",style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    for ip in [1,2]:
      ymin, ymax = (plot.ymin, plot.ymax) if ip==1 else (plot.rmin, plot.rmax)
      for i in range(1,yvar_reco.nbins):
        x = bvar_reco.min + (bvar_reco.max-bvar_reco.min)*i/yvar_reco.nbins
        plot.drawline(x,ymin,x,ymax,color=kRed,style=kDashed,title=stitle,pad=ip)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions - normalized
    pname_ = repkey(pname,CAT="dy_norm_"+selection.filename).replace('_baseline',"")
    plot   = Plot(bvar_reco,[dyhist,obsdyhist,dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    plot.draw(ptitle,logx=False,logy=logy,xmin=1.0,ymin=0.005,norm=True,style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    for ip in [1,2]:
      ymin, ymax = (plot.ymin, plot.ymax) if ip==1 else (plot.rmin, plot.rmax)
      for i in range(1,yvar_reco.nbins):
        x = bvar_reco.min + (bvar_reco.max-bvar_reco.min)*i/yvar_reco.nbins
        plot.drawline(x,ymin,x,ymax,color=kRed,style=kDashed,title=stitle,pad=ip)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy_norm",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Drell-Yan gen-level distribution
    pname_ = repkey(pname,CAT="dy_gen_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_gen,yvar_gen,dyhist2D_gen)
    plot.draw(logx=logx,logy=logy,logz=logz,ztitle="Events")
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("dy_gen_2D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Drell-Yan reco-level distribution
    pname_ = repkey(pname,CAT="dy_reco_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_reco,yvar_reco,dyhist2D_reco)
    plot.draw(logx=logx,logy=logy,logz=logz,ztitle="Events")
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("dy_reco_2D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Response matrix
    pname_ = repkey(pname,CAT="response_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(bvar_reco,bvar_gen,resphist)
    plot.draw(logx=False,logy=False,logz=logz,ztitle="Events")
    for i in range(1,yvar_gen.nbins): # horizontal lines
      y = bvar_gen.min + (bvar_gen.max-bvar_gen.min)*i/yvar_gen.nbins
      plot.drawline(bvar_reco.min,y,bvar_reco.max,y,color=kRed,style=kDashed,title=stitle)
    for i in range(1,yvar_reco.nbins): # vertical lines
      x = bvar_reco.min + (bvar_reco.max-bvar_reco.min)*i/yvar_reco.nbins
      plot.drawline(x,bvar_gen.min,x,bvar_gen.max,color=kRed,style=kDashed,title=stitle)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("response_matrix",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Obs. / Exp.
    pname_ = repkey(pname,CAT="data-mc_"+selection.filename).replace('_baseline',"")
    plot   = Stack(bvar_reco,obshist,hists.exp)
    plot.draw(logx=False,logy=logy,ymin=10,title="Events / GeV")
    plot.drawlegend()
    plot.drawtext(selection.title)
    for ip in [1,2]:
      ymin, ymax = (plot.ymin, plot.ymax) if ip==1 else (plot.rmin, plot.rmax)
      for i in range(1,yvar_reco.nbins):
        x = bvar_reco.min + (bvar_reco.max-bvar_reco.min)*i/yvar_reco.nbins
        plot.drawline(x,ymin,x,ymax,color=kRed,style=kDashed,title=stitle,pad=ip)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("data_mc",gStyle.kOverwrite)
    plot.close()
    
    # CLOSE
    close([exphist,bkghist,obsdyhist]) #sfhist,obshist,+hist.exp
    outfile.Close()
    print ">>> "


def measureZpt_unfold(samples,outdir='weights',plotdir=None,parallel=True,tag=""):
  """Measure Z pT weights in dimuon pT by unfolding."""
  LOG.header("measureZpt_unfold()")
  
  # SETTINGS
  hname    = 'zpt'
  fname    = "%s/%s_weight_$CAT%s.root"%(outdir,hname,tag)
  pname    = "%s/%s_$CAT%s.png"%(plotdir or outdir,hname,tag)
  outdir   = ensuredir(outdir) #repkey(outdir,CHANNEL=channel,ERA=era))
  stitle   = "Z boson unfolding weight"
  logx     = True #and False
  logy     = True #and False
  logz     = True #and False
  method   = None #'QCD'
  dysample = samples.get('DY',unique=True)
  
  # SELECTIONS
  selections = [
    Sel('baseline', baseline),
    #Sel('m_{mumu} > 200 GeV',               baseline+" && m_vis>200", fname="mgt200"),
  ]
  #xvar = Var('m_ll', Zmbins, mtitle)
  xvar_reco = Var('pt_ll',  ptbins0,"Reco-level "+ptitle,cbins={'njets50==0':ptbins1}) # pt_mumu
  xvar_gen  = Var('pt_moth',ptbins0,"Gen-level "+ptitle,cbins={'njets50==0':ptbins1}) # Z boson pt
  
  for selection in selections:
    LOG.color(selection.title,col='green')
    print ">>> %s"%(selection.selection)
    xvar_reco.changecontext(selection.selection)
    xvar_gen.changecontext(selection.selection)
    fname_ = repkey(fname,CAT=selection.filename).replace('_baseline',"")
    
    print ">>> Unfold reco-level weights as a function of %s"%(xvar_reco.title)
    outfile = ensureTFile(fname_,'UPDATE')
    ctrldir = ensureTDirectory(outfile,"control",cd=False)
    
    # HISTOGRAMS
    hists = samples.gethists(xvar_reco,selection,split=False,blind=False,method=method,
                             signal=False,parallel=parallel)
    obshist, exphist, dyhist, bkghist = getdyhist(hname,hists,"_reco",verb=2)
    dyhist_gen = dysample.gethist(xvar_gen,selection,split=False,parallel=parallel,weight="")
    #histSF_gaps = histSF.Clone("gaps")
    #setContentRange(histSF,0.0,3.0)
    #fillTH2Gaps(histSF,axis='x')
    #setContentRange(histSF,0.2,3.0)
    #extendContent(histSF)
    
    # OBSERVED DY = DATA - BKG
    obsdyhist = obshist.Clone(hname+"_obsdy"+tag)
    obsdyhist.SetBinErrorOption(obshist.kNormal)
    obsdyhist.Add(bkghist,-1)
    
    # RESPONSE MATRIX
    resphist = dysample.gethist2D(xvar_reco,xvar_gen,selection,split=False,parallel=parallel)
    
    # UNFOLD
    print ">>> Creating RooUnfoldResponse..."
    resp   = RooUnfoldResponse(dyhist,dyhist_gen,resphist)
    print ">>> Creating RooUnfoldBinByBin..."
    unfold = RooUnfoldBinByBin(resp,obsdyhist)
    #unfold.unfold()
    print ">>> Creating Hreco..."
    dyhist_unf = unfold.Hreco()
    sfhist = dyhist_unf.Clone(hname+"_weight")
    sfhist.Divide(dyhist_gen)
    
    # WRITE
    print ">>> Writing histograms to %s..."%(outfile.GetPath())
    outfile.cd()
    writehist(sfhist,    hname+"_weight","Z boson unfolding weight", xvar_reco.title,stitle)
    ctrldir.cd()
    writehist(obshist,   hname+"_obs_reco",   "Observed",           xvar_reco.title,"Events")
    writehist(exphist,   hname+"_exp_reco",   "Expected",           xvar_reco.title,"Events")
    writehist(bkghist,   hname+"_bkg_reco",   "Exp. background",    xvar_reco.title,"Events")
    writehist(dyhist,    hname+"_dy_reco",    "Drell-Yan reco",     xvar_reco.title,"Events")
    writehist(obsdyhist, hname+"_obsdy_reco", "Obs. - bkg.",        xvar_reco.title,"Events")
    writehist(dyhist_gen,hname+"_dy_gen",     "Drell-Yan generator",xvar_gen.title, "Events")
    writehist(dyhist_unf,hname+"_dy_unfold",  "Drell-Yan unfolded", xvar_gen.title, "Events")
    writehist(resphist,  hname+"_dy_response","Response matrix",    xvar_reco.title,xvar_gen.title,"Events")
    
    # PLOT - weight
    print ">>> Plotting..."
    rline  = (xvar_reco.min,1.,xvar_reco.max,1.)
    pname_ = repkey(pname,CAT="weight_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,sfhist,dividebins=False)
    plot.draw(logx=logx,xmin=1.0,ymin=0.2,ymax=1.8)
    plot.drawline(*rline,color=kRed,title=stitle)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions
    pname_ = repkey(pname,CAT="dy_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,[dyhist,obsdyhist,dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    plot.draw(ptitle,logx=logx,logy=logy,xmin=1.0,title="Events / GeV",style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions - normalized
    pname_ = repkey(pname,CAT="dy_norm_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,[dyhist,obsdyhist,dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    plot.draw(ptitle,logx=logx,logy=logy,xmin=1.0,norm=True,style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy_norm",gStyle.kOverwrite)
    plot.close()
    
    #### PLOT - Drell-Yan distributions - gen vs. unfolded
    ###pname_ = repkey(pname,CAT="dy_gen_"+selection.filename).replace('_baseline',"")
    ###plot   = Plot(xvar_gen,[dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    ###plot.draw(logx=logx,logy=True,xmin=1.0,title="Events / GeV")
    ###plot.drawlegend()
    ###plot.drawtext(selection.title)
    ###plot.saveas(pname_,ext=['.png','.pdf'])
    ###plot.canvas.Write("dy_gen",gStyle.kOverwrite)
    ###plot.close()
    ###
    #### PLOT - Drell-Yan distributions - gen vs. unfolded - normalized
    ###pname_ = repkey(pname,CAT="dy_gen_norm_"+selection.filename).replace('_baseline',"")
    ###plot   = Plot(xvar_gen,[dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    ###plot.draw(logx=logx,logy=True,xmin=1.0,norm=True)
    ###plot.drawlegend()
    ###plot.drawtext(selection.title)
    ###plot.saveas(pname_,ext=['.png','.pdf'])
    ###plot.canvas.Write("dy_gen_norm",gStyle.kOverwrite)
    ###plot.close()
    
    # PLOT 2D - Response matrix
    pname_ = repkey(pname,CAT="response_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_reco,xvar_gen,resphist)
    plot.draw(logx=logx,logy=logy,logz=logz,xmin=1.0,ztitle="Events")
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("response_matrix",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Obs. / Exp.
    pname_ = repkey(pname,CAT="data-mc_"+selection.filename).replace('_baseline',"")
    plot   = Stack(xvar_reco,obshist,hists.exp)
    plot.draw(logx=logx,logy=logy,xmin=1.0,title="Events / GeV")
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("data_mc",gStyle.kOverwrite)
    plot.close()
    
    # CLOSE
    close([exphist,bkghist,obsdyhist]) #sfhist,obshist,+hist.exp
    outfile.Close()
    print ">>> "
    


def main(args):
  channel  = 'mumu'
  eras     = args.eras
  parallel = args.parallel
  outdir   = "weights" #/$ERA"
  plotdir  = "weights/$ERA"
  fname    = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  tag      = ""
  for era in eras:
    tag_   = tag+'_'+era
    setera(era) # set era for plot style and lumi-xsec normalization
    outdir_  = ensuredir(repkey(outdir,ERA=era))
    plotdir_ = ensuredir(repkey(plotdir,ERA=era))
    samples  = getsampleset(channel,era,fname=fname,dyweight="",dy="")
    #measureZpt_unfold(samples,outdir=outdir_,plotdir=plotdir_,parallel=parallel,tag=tag_)
    measureZptmass_unfold(samples,outdir=outdir_,plotdir=plotdir_,parallel=parallel,tag=tag_)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Measure Z pT reweighting in dimuon events with RooUnfold."""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['2017'], action='store',
                                         help="set era" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print ">>> Done."
  
