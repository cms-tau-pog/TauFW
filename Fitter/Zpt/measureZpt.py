#! /usr/bin/env python
# Author: Izaak Neutelings (May 2021)
# Description: Script to measure Z pt reweighting based on dimuon events
#   ./measureZpt.py -y 2018
from utils import *
from TauFW.Plotter.plot.Plot2D import Plot2D, addoverflow, capoff
from TauFW.common.tools.math import scalevec
gSystem.Load('RooUnfold/libRooUnfold.so')
from ROOT import RooUnfoldResponse, RooUnfoldBinByBin, RooUnfoldBayes

ptitle   = "p_{T}(#mu#mu)" # [GeV]"
mtitle   = "m_{#mu#mu}" # [GeV]"
pgtitle  = "Z p_{T}"
mgtitle  = "m_{#mu#mu}" #"m_{Z}"
baseline = "q_1*q_2<0 && iso_1<0.15 && iso_2<0.15 && !extraelec_veto && !extramuon_veto && m_ll>20"
Zmbins0  = [20,30,40,50,60,70,80,85,88,89,89.5,90,90.5,91,91.5,92,93,94,95,100,110,120,180,500,1000]
Zmbins1  = [10,50,70,91,110,150,200,400,800,1500]
ptbins0  = [0,3,6,8,10,12,15,20,25,30,35,40,45,50,60,70,100,140,200,300,500,1000]
ptbins1  = [0,5,10,15,30,50,100,200,500,1000]


def measureZptmass_unfold(samples,outdir='weights',plotdir=None,parallel=True,tag="",verb=0):
  """Measure Z pT weights in dimuon pT and mass by unfolding.
  Unroll 2D histogram using the Unroll.cxx macro to 1D histogram (with integer bin numbers)."""
  LOG.header("measureZptmass_unfold()")
  gROOT.ProcessLine(".L ../../Plotter/python/macros/Unroll.cxx+O")
  from ROOT import Unroll
  
  # SETTINGS
  niter     = 4 # number of iterations in RooUnfoldBayes
  kterm     = (len(Zmbins1)-1)*(len(ptbins1)-1)/2. # kterm in RooUnfoldSvd
  hname     = 'zptmass'
  fname     = "%s/%s_weights_$CAT%s.root"%(outdir,hname,tag)
  pname     = "%s/%s_$CAT%s.png"%(plotdir or outdir,hname,tag)
  outdir    = ensuredir(outdir) #repkey(outdir,CHANNEL=channel,ERA=era))
  stitle    = "Z boson unfolding weight"
  stitle_reco = "Z boson reco. weight"
  width     = 1200 # canvas width for 1D unrolled plots
  bsize     = 0.039 # size of bin text in 1D unrolled plots
  position  = 'RR;y=0.91' # legend position in 1D unrolled plots
  logx      = True #and False
  logy      = True #and False
  logz      = True #and False
  addof     = True #and False # add overflow
  method    = None #'QCD'
  dysample  = samples.get('DY',unique=True)
  
  # SELECTIONS
  selections = [
    Sel('Baseline #mu#mu', baseline, fname="baseline"),
  ]
  
  # VARIABLES
  nurbins  = (len(Zmbins1)-1)*(len(ptbins1)-1) # number of 2D bins (excl. under-/overflow)
  urbins0  = (nurbins,1,1+nurbins) # unrolled
  urlabels1 = [str(i) if i%(len(ptbins1)-1)==1 or i in [nurbins] else " " for i in range(1,nurbins+1)]
  urlabels2 = [str(i) if i%(len(Zmbins1)-1)==1 or i in [nurbins] else " " for i in range(1,nurbins+1)]
  xvar_reco   = Var('pt_ll',  ptbins1,"Reconstructed "+ptitle,logx=logx,logy=logy,addof=addof) # reconstructed pt_mumu
  yvar_reco   = Var('m_ll',   Zmbins1,"Reconstructed "+mtitle,logx=logx,logy=logy,addof=addof) # reconstructed m_mumu
  xvar_gen    = Var('pt_moth',ptbins1,"Generated "+pgtitle,logx=logx,logy=logy,addof=addof) # generated Z boson pt
  yvar_gen    = Var('m_moth', Zmbins1,"Generated "+mgtitle,logx=logx,logy=logy,addof=addof) # generated Z boson mass
  bvar_reco   = Var('Unroll::GetBin(pt_ll,m_ll,0,1)',"Reconstructed %s bin"%(ptitle),*urbins0,units=False,labels=urlabels1) # unroll bin number
  bvar_gen    = Var('Unroll::GetBin(pt_moth,m_moth,0,1)',"Generated %s bin"%(pgtitle),*urbins0,units=False,labels=urlabels1) # unroll bin number
  bvar_reco_T = Var('Unroll::GetBin(pt_ll,m_ll,1,1)',"Reconstructed %s bin"%(mtitle),*urbins0,units=False,labels=urlabels2) # unroll bin number, transposed
  print ">>> 2D bins: %d = %d pt bins x %d mass bins"%(bvar_reco.nbins,xvar_reco.nbins,yvar_reco.nbins)
  
  for selection in selections:
    LOG.color(selection.title,col='green')
    print ">>> selection: %r"%(selection.selection)
    for var in [xvar_reco,xvar_gen,yvar_reco,yvar_gen,bvar_reco,bvar_gen]:
      var.changecontext(selection.selection)
    fname_ = repkey(fname,CAT=selection.filename).replace('_baseline',"")
    
    print ">>> Unfold reconstruction-level weights as a function of %s vs. %s"%(yvar_reco.title,xvar_reco.title)
    outfile = ensureTFile(fname_,'UPDATE')
    ctrldir = ensureTDirectory(outfile,"control",cd=False)
    
    # DY 2D HISTOGRAMS - for checks, and setting axes in unrolling
    print ">>> Creating DY 2D distributions..."
    dyhist2D_reco = dysample.gethist2D(xvar_reco,yvar_reco,selection,split=False,parallel=parallel)
    dyhist2D_gen  = dysample.gethist2D(xvar_gen, yvar_gen ,selection,split=False,parallel=parallel)
    Unroll.SetBins(dyhist2D_reco,verb) # set bin axes for Unroll.GetBin
    #addoverflow([dyhist2D_reco,dyhist2D_gen],verb=verb) # use Variable.addoverflow instead
    
    # RECO HISTOGRAMS 1D - for checks
    print ">>> Creating reconstruction-level 1D distributions..."
    xhists = samples.gethists(xvar_reco,selection,split=False,blind=False,method=method,signal=False,parallel=parallel)
    yhists = samples.gethists(yvar_reco,selection,split=False,blind=False,method=method,signal=False,parallel=parallel)
    #addoverflow(xhists.all()+yhists.all(),verb=verb) # use Variable.addoverflow instead
    
    # RECO HISTOGRAMS 2D - unrolled
    print ">>> Creating reconstruction-level 2D distributions (unrolled)..."
    hists = samples.gethists(bvar_reco,selection,split=False,blind=False,method=method,signal=False,parallel=parallel)
    obshist, exphist, dyhist, bkghist, obsdyhist = getdyhist(hname,hists,"_reco",verb=verb)
    
    # GEN HISTOGRAMS 2D - unrolled
    print ">>> Creating generator-level 2D distributions (unrolled)..."
    dyhist_gen = dysample.gethist(bvar_gen,selection,split=False,parallel=parallel)
    
    # TRANSPOSE - for checks
    print ">>> Transpose unrolled 2D histograms..."
    obshist_T = Unroll.Transpose(obshist,dyhist2D_reco,verb)
    histsexp_T = [Unroll.Transpose(h,dyhist2D_reco,verb) for h in hists.exp]
    
    # 4D RESPONSE MATRIX - unrolled to 2D via Unroll::GetBin
    print ">>> Creating response matrix..."
    resphist = dysample.gethist2D(bvar_reco,bvar_gen,selection,split=False,parallel=False) # parallel fails for many bins
    
    # UNFOLD
    print ">>> Creating RooUnfoldResponse..."
    resp   = RooUnfoldResponse(dyhist,dyhist_gen,resphist)
    #print ">>> Unfolding with RooUnfoldBinByBin..."
    #unfold = RooUnfoldBinByBin(resp,obsdyhist)
    print ">>> Unfolding with RooUnfoldBayes..."
    unfold = RooUnfoldBayes(resp,obsdyhist,niter)
    #unfold.unfold()
    print ">>> Creating Hreco..."
    dyhist_unf = unfold.Hreco()
    
    # CREATE ZPT WEIGHTS
    print ">>> Creating Z pt weights..."
    ratio = dyhist_unf.Integral()/dyhist_gen.Integral()
    print ">>> (Unfolded DY) / (Generated DY) = %.4f"%(ratio)
    sfhist1D = dyhist_unf.Clone(hname+"_weight")
    sfhist1D.Divide(dyhist_gen)
    sfhist1D.Scale(1./ratio)
    
    # RECO WEIGHT
    ratio = obsdyhist.Integral()/dyhist.Integral()
    print ">>> (Observed DY) / (Reconstructed DY) = %.4f"%(ratio)
    sfhist1D_reco = obsdyhist.Clone(hname+"_weight_reco")
    sfhist1D_reco.Divide(dyhist)
    sfhist1D_reco.Scale(1./ratio) # remove normalization effect
    
    # RATIO WEIGHT
    rathist1D = sfhist1D_reco.Clone(hname+"_weight_ratio")
    rathist1D.Divide(sfhist1D) # (reco weight) / (unfolded weight)
    capoff(sfhist1D_reco,0.3,1.7,verb=verb+1) # cap off large values
    capoff(sfhist1D,0.3,1.7,verb=verb+1) # cap off large values
    print ">>> Convert 1D unrolled weights back to 2D..."
    dyhist2D_unf  = Unroll.RollUp(dyhist_unf,hname+"_dy_unfold_2D",dyhist2D_reco,verb)
    sfhist2D      = Unroll.RollUp(sfhist1D,  hname+"_weight_2D",dyhist2D_reco,verb)
    sfhist2D_reco = Unroll.RollUp(sfhist1D_reco,hname+"_weight_reco_2D",dyhist2D_reco,verb)
    
    # WRITE
    print ">>> Writing histograms to %s..."%(outfile.GetPath())
    outfile.cd()
    writehist(sfhist2D,     hname+"_weight",      "Unfolded Z boson weight",xvar_gen.title,yvar_gen.title,stitle,verb=1)
    writehist(sfhist2D_reco,hname+"_recoweight",  "Reco. Z boson weight",xvar_reco.title,yvar_reco.title,stitle_reco,verb=1)
    ctrldir.cd()
    writehist(obshist,      hname+"_obs_reco",    "Observed",           bvar_reco.title,"Events")
    writehist(exphist,      hname+"_exp_reco",    "Expected",           bvar_reco.title,"Events")
    writehist(bkghist,      hname+"_bkg_reco",    "Exp. background",    bvar_reco.title,"Events")
    writehist(dyhist,       hname+"_dy_reco",     "Drell-Yan reco.",    bvar_reco.title,"Events")
    writehist(dyhist2D_reco,hname+"_dy_reco2D",   "Drell-Yan reco.",    xvar_reco.title,yvar_reco.title, "Events")
    writehist(obsdyhist,    hname+"_obsdy_reco",  "Obs. - bkg.",        bvar_reco.title,"Events")
    writehist(dyhist_gen,   hname+"_dy_gen",      "Drell-Yan generator",bvar_gen.title, "Events")
    writehist(dyhist2D_gen, hname+"_dy_gen2D",    "Drell-Yan generator",xvar_gen.title,yvar_gen.title, "Events")
    writehist(dyhist_unf,   hname+"_dy_unfold",   "Drell-Yan unfolded", bvar_gen.title, "Events")
    writehist(dyhist2D_unf, hname+"_dy_unfold2D", "Drell-Yan unfolded", xvar_gen.title,yvar_gen.title,"Events")
    writehist(resphist,     hname+"_dy_response", "Response matrix",    bvar_gen.title,bvar_reco.title,"Events")
    writehist(sfhist1D,     hname+"_weight1D",    "Unfolded Z boson weight (unrolled)",xvar_reco.title,stitle)
    writehist(sfhist2D,     hname+"_weight2D",    "Unfolded Z boson weight",xvar_gen.title,yvar_gen.title,stitle)
    writehist(sfhist1D_reco,hname+"_recoweight1D","Reco. Z boson weight (unrolled)",xvar_reco.title,stitle_reco)
    writehist(sfhist2D_reco,hname+"_recoweight2D","Reco. Z boson weight",xvar_reco.title,yvar_reco.title,stitle_reco)
    writehist(rathist1D,    hname+"_ratio_weight","Reco. weight / Unf. weight (unrolled)",xvar_reco.title,"Reco. weight / Unf. weight")
    
    # PLOT 1D - Unrolled unfolded weight 1D
    print ">>> Plotting..."
    rline  = (bvar_reco.min,1.,bvar_reco.max,1.)
    pname_ = repkey(pname,CAT="weight_1D_"+selection.filename).replace('_baseline',"")
    plot   = Plot(bvar_gen,sfhist1D,dividebins=False)
    plot.draw(logx=False,logy=False,logz=False,xmin=1.0,ymin=0.2,ymax=1.8,width=width,
              style=1,grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawline(*rline,color=kBlue)
    plot.drawtext("Unfolded weight, %s"%(selection.title),y=0.91)
    plot.drawbins(yvar_reco,y=0.96,size=bsize,text="m_{#mu#mu}",addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight_1D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Rolled up unfolded weight 2D
    pname_ = repkey(pname,CAT="weight_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_gen,yvar_gen,sfhist2D)
    plot.draw(logx=logx,logy=logy,logz=False,xmin=2.0,zmin=0.2,zmax=1.8,ztitle="Unfolded Z boson weight")
    #plot.drawlegend()
    plot.drawtext(selection.title,size=0.052)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("weight_2D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled reco. weight 1D
    rline  = (bvar_reco.min,1.,bvar_reco.max,1.)
    pname_ = repkey(pname,CAT="weight_reco_1D_"+selection.filename).replace('_baseline',"")
    plot   = Plot(bvar_reco,sfhist1D_reco,dividebins=False)
    plot.draw(logx=False,logy=False,logz=False,xmin=1.0,ymin=0.2,ymax=1.8,width=width,
              style=1,grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawline(*rline,color=kBlue)
    plot.drawtext("Reco. weight, %s"%(selection.title),y=0.91)
    plot.drawbins(yvar_reco,y=0.96,size=bsize,text="m_{#mu#mu}",addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight_reco_1D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Rolled up reco. weight 2D
    pname_ = repkey(pname,CAT="weight_reco_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_reco,yvar_reco,sfhist2D_reco)
    plot.draw(logx=logx,logy=logy,logz=False,xmin=2.0,zmin=0.2,zmax=1.8,ztitle="Reco. Z boson weight")
    #plot.drawlegend()
    plot.drawtext(selection.title,size=0.052)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("weight_reco_2D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled ratio of Reco. weight / Unfolded weight
    rline  = (bvar_reco.min,1.,bvar_reco.max,1.)
    pname_ = repkey(pname,CAT="ratio_weight_1D_"+selection.filename).replace('_baseline',"")
    plot   = Plot(bvar_reco,rathist1D,dividebins=False)
    plot.draw(logx=False,logy=False,logz=False,xmin=1.0,ymin=0.2,ymax=1.8,width=width,
              style=1,grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawline(*rline,color=kBlue)
    plot.drawtext(selection.title,y=0.91)
    plot.drawbins(yvar_reco,y=0.96,size=bsize,text="m_{#mu#mu}",addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("ratio_weight_1D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - xvar Drell-Yan 1D distribution
    catstr = "data-mc_%s_%s"%(selection.filename,xvar_reco.filename)
    pname_ = repkey(pname,CAT=catstr).replace('_baseline',"")
    plot   = Stack(xvar_reco,xhists.data,xhists.exp,dividebins=True,ratio=True)
    plot.draw(logx=logx,logy=logy,xmin=1.,ymin=1e-1,ytitle="Events / GeV",style=1)
    plot.drawlegend('RR')
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("data_mc_%s"%(xvar_reco.filename),gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - yvar Drell-Yan 1D distribution
    catstr = "data-mc_%s_%s"%(selection.filename,yvar_reco.filename)
    pname_ = repkey(pname,CAT=catstr).replace('_baseline',"")
    plot   = Stack(yvar_reco,yhists.data,yhists.exp,dividebins=True,ratio=True)
    plot.draw(logx=logx,logy=logy,xmin=15.,ymin=1e-1,ytitle="Events / GeV",style=1)
    plot.drawlegend('R')
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("data_mc_%s"%(yvar_reco.filename),gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled Obs. / Exp.
    for hist in [obshist]+hists.exp:
      Unroll.DivideByBinSize(hist,dyhist2D_reco,False,verb)
    pname_ = repkey(pname,CAT="data-mc_"+selection.filename).replace('_baseline',"")
    plot   = Stack(bvar_reco,obshist,hists.exp,clone=True)
    plot.draw(logx=False,logy=logy,ymin=1e-2,width=width,ytitle="Events / GeV",
              grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawlegend(position)
    plot.drawtext(selection.title,y=0.91)
    plot.drawbins(yvar_reco,y=0.96,size=bsize,text=mtitle,addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("data_mc",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled Obs. / Exp.  1D unrolled - transposed
    for hist in [obshist_T]+histsexp_T:
      Unroll.DivideByBinSize(hist,dyhist2D_reco,True,verb)
    pname_ = repkey(pname,CAT="data-mc_"+selection.filename+"_transposed").replace('_baseline',"")
    #xtitle = bvar_reco.title.replace(ptitle,mtitle) #"Reconstructed %s bin"%(mtitle)
    plot   = Stack(bvar_reco_T,obshist_T,histsexp_T)
    plot.draw(logx=False,logy=logy,ymin=1e-2,width=width,ytitle="Events / GeV",
              grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawlegend(position)
    plot.drawtext(selection.title,y=0.91)
    plot.drawbins(xvar_reco,y=0.96,size=0.94*bsize,text=ptitle,addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("data_mc_transposed",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled Drell-Yan distributions
    dyhists = [dyhist,obsdyhist,dyhist_gen,dyhist_unf]
    dyhists_T = [Unroll.Transpose(h,dyhist2D_reco,verb) for h in dyhists]
    for hist in dyhists:
      Unroll.DivideByBinSize(hist,dyhist2D_reco,False,verb)
    pname_ = repkey(pname,CAT="dy_"+selection.filename).replace('_baseline',"")
    xtitle = bvar_reco.title.replace("Reconstructed ","") # comparing generated to reconstructed
    plot   = Plot(bvar_reco,dyhists,clone=True,dividebins=True,ratio=True)
    plot.draw(logx=False,logy=logy,xmin=1.0,ymin=1e-2,width=width,xtitle=xtitle,ytitle="Events / GeV",
              style=1,grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawlegend('RR;y=0.9')
    plot.drawtext(selection.title,y=0.91)
    plot.drawbins(yvar_reco,y=0.96,size=bsize,text=mtitle,addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled Drell-Yan distributions - transposed
    for hist in dyhists_T:
      Unroll.DivideByBinSize(hist,dyhist2D_reco,True,verb)
    pname_ = repkey(pname,CAT="dy_transposed_"+selection.filename).replace('_baseline',"")
    xtitle = bvar_reco_T.title.replace("Reconstructed ","")
    plot   = Plot(bvar_reco_T,dyhists_T,clone=True,dividebins=True,ratio=True)
    plot.draw(logx=False,logy=logy,xmin=1.,ymin=1e-2,width=width,xtitle=xtitle,ytitle="Events / GeV",
              style=1,grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawlegend('RR;y=0.9')
    plot.drawtext(selection.title,y=0.91)
    plot.drawbins(xvar_reco,y=0.96,size=0.94*bsize,text=ptitle,addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy_transposed",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 1D - Unrolled Drell-Yan distributions - normalized
    pname_ = repkey(pname,CAT="dy_norm_"+selection.filename).replace('_baseline',"")
    xtitle = bvar_reco.title.replace("Reconstructed ","")
    plot   = Plot(bvar_reco,dyhists,clone=True,dividebins=True,ratio=True)
    plot.draw(logx=False,logy=logy,xmin=1.,ymin=1e-4,width=width,xtitle=xtitle,norm=True,
              style=1,grid=False,xlabelsize=0.072,labeloption='h')
    plot.drawlegend(position)
    plot.drawtext(selection.title,y=0.91)
    plot.drawbins(yvar_reco,y=0.96,size=bsize,text=mtitle,addoverflow=True)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy_norm",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Drell-Yan generator distribution
    pname_ = repkey(pname,CAT="dy_gen_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_gen,yvar_gen,dyhist2D_gen)
    plot.draw(logx=logx,logy=logy,logz=logz,xmin=2.,ymin=30.,zmin=1.,ztitle="Events")
    plot.drawtext("%s, Drell-Yan"%(selection.title),size=0.052)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("dy_gen_2D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Drell-Yan reconstructed distribution
    pname_ = repkey(pname,CAT="dy_reco_2D_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(xvar_reco,yvar_reco,dyhist2D_reco,clone=True)
    plot.draw(logx=logx,logy=logy,logz=logz,xmin=2.,ymin=30.,zmin=1.,ztitle="Events")
    plot.drawtext("%s, Drell-Yan"%(selection.title),size=0.052)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("dy_reco_2D",gStyle.kOverwrite)
    plot.close()
    
    # PLOT 2D - Unrolled response matrix (4D)
    pname_ = repkey(pname,CAT="response_"+selection.filename).replace('_baseline',"")
    plot   = Plot2D(bvar_reco,bvar_gen,resphist)
    plot.draw(logx=False,logy=False,width=1000,zmin=1.,logz=logz,ztitle="Events",
              grid=False,labelsize=0.040,xlabeloption='h')
    plot.drawbins(yvar_gen, y=0.96,text=False,axis='y')
    plot.drawbins(yvar_reco,y=0.96,text=False,axis='x')
    #plot.drawlegend()
    plot.drawtext("Response matrix, %s"%(selection.title),size=0.052)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("response_matrix",gStyle.kOverwrite)
    plot.close()
    
    # CLOSE
    close([obshist,exphist,bkghist,dyhist2D_reco]+dyhists+dyhists_T+hists.exp) #sfhist
    if verb>=1:
      outfile.ls()
      #ctrldir.ls()
    outfile.Close()
    print ">>> "
  

def measureZpt_unfold(samples,outdir='weights',plotdir=None,parallel=True,tag="",verb=0):
  """Measure Z pT weights in dimuon pT by unfolding."""
  LOG.header("measureZpt_unfold()")
  
  # SETTINGS
  niter    = 4 # number of iterations in RooUnfoldBayes
  kterm    = len(ptbins0)/2. # kterm in RooUnfoldSvd
  hname    = 'zpt'
  fname    = "%s/%s_weights_$CAT%s.root"%(outdir,hname,tag)
  pname    = "%s/%s_$CAT%s.png"%(plotdir or outdir,hname,tag)
  outdir   = ensuredir(outdir) #repkey(outdir,CHANNEL=channel,ERA=era))
  stitle   = "Z boson unfolding weight"
  stitle_reco = "Z boson reco. weight"
  addof    = True #and False
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
  xvar_reco = Var('pt_ll',  ptbins0,"Reconstructed "+ptitle,cbins={'njets50==0':ptbins1},addof=addof) # reconstructed pt_mumu
  xvar_gen  = Var('pt_moth',ptbins0,"Generated "+ptitle,cbins={'njets50==0':ptbins1},addof=addof) # generated Z boson pt
  
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
    obshist, exphist, dyhist, bkghist, obsdyhist = getdyhist(hname,hists,"_reco",verb=2)
    dyhist_gen = dysample.gethist(xvar_gen,selection,split=False,parallel=parallel,weight="")
    #histSF_gaps = histSF.Clone("gaps")
    #setContentRange(histSF,0.0,3.0)
    #fillTH2Gaps(histSF,axis='x')
    #setContentRange(histSF,0.2,3.0)
    #extendContent(histSF)
    
    # RESPONSE MATRIX
    resphist = dysample.gethist2D(xvar_reco,xvar_gen,selection,split=False,parallel=parallel)
    
    # UNFOLD
    print ">>> Creating RooUnfoldResponse..."
    resp   = RooUnfoldResponse(dyhist,dyhist_gen,resphist)
    #print ">>> Unfolding with RooUnfoldBinByBin..."
    #unfold = RooUnfoldBinByBin(resp,obsdyhist)
    print ">>> Unfolding with RooUnfoldBayes..."
    unfold = RooUnfoldBayes(resp,obsdyhist,niter)
    #unfold.unfold()
    print ">>> Creating Hreco..."
    dyhist_unf = unfold.Hreco()
    
    # UNFOLDED WEIGHT
    ratio = dyhist_unf.Integral()/dyhist_gen.Integral()
    print ">>> (Unfolded DY) / (Generated DY) = %.4f"%(ratio)
    sfhist = dyhist_unf.Clone(hname+"_weight")
    sfhist.Divide(dyhist_gen)
    sfhist.Scale(1./ratio) # remove normalization effect
    
    # RECO WEIGHT
    ratio = obsdyhist.Integral()/dyhist.Integral()
    print ">>> (Observed DY) / (Reconstructed DY) = %.4f"%(ratio)
    sfhist_reco = obsdyhist.Clone(hname+"_weight_reco")
    sfhist_reco.Divide(dyhist) # (obs. DY) / (sim. DY)
    sfhist_reco.Scale(1./ratio) # remove normalization effect
    
    # RATIO WEIGHT
    rathist = sfhist_reco.Clone(hname+"_weight_ratio")
    rathist.Divide(sfhist) # (reco weight) / (unfolded weight)
    capoff(sfhist,0.4,1.6,verb=verb+1) # cap off large values
    capoff(sfhist_reco,0.4,1.6,verb=verb+1) # cap off large values
    
    # WRITE
    print ">>> Writing histograms to %s..."%(outfile.GetPath())
    outfile.cd()
    writehist(sfhist,      hname+"_weight","Z boson unfolding weight", xvar_reco.title,stitle)
    writehist(sfhist_reco, hname+"_recoweight","Z boson unfolding weight",xvar_reco.title,stitle_reco)
    ctrldir.cd()
    writehist(obshist,     hname+"_obs_reco",   "Observed",            xvar_reco.title,"Events")
    writehist(exphist,     hname+"_exp_reco",   "Expected",            xvar_reco.title,"Events")
    writehist(bkghist,     hname+"_bkg_reco",   "Exp. background",     xvar_reco.title,"Events")
    writehist(dyhist,      hname+"_dy_reco",    "Drell-Yan reco",      xvar_reco.title,"Events")
    writehist(obsdyhist,   hname+"_obsdy_reco", "Obs. - bkg.",         xvar_reco.title,"Events")
    writehist(dyhist_gen,  hname+"_dy_gen",     "Drell-Yan generator", xvar_gen.title, "Events")
    writehist(dyhist_unf,  hname+"_dy_unfold",  "Drell-Yan unfolded",  xvar_gen.title, "Events")
    writehist(resphist,    hname+"_dy_response","Response matrix",     xvar_reco.title,xvar_gen.title,"Events")
    writehist(rathist,     hname+"_ratio_weight","Reco. weight / Unf. weight",xvar_gen.title,"Reco. weight / Unf. weight")
    
    # PLOT - weight
    print ">>> Plotting..."
    rline  = (xvar_gen.min,1.,xvar_gen.max,1.)
    pname_ = repkey(pname,CAT="weight_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_gen,sfhist,dividebins=False)
    plot.draw(logx=logx,xmin=1.0,ymin=0.2,ymax=1.8)
    plot.drawline(*rline,color=kRed,title=stitle)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - reco. weight
    rline  = (xvar_reco.min,1.,xvar_reco.max,1.)
    pname_ = repkey(pname,CAT="weight_reco_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,sfhist_reco,dividebins=False)
    plot.draw(logx=logx,xmin=1.0,ymin=0.2,ymax=1.8)
    plot.drawline(*rline,color=kRed,title=stitle_reco)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("weight_reco",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - ratio weight
    rline  = (xvar_reco.min,1.,xvar_reco.max,1.)
    pname_ = repkey(pname,CAT="ratio_weight_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,rathist,dividebins=False)
    plot.draw(logx=logx,xmin=1.0,ymin=0.6,ymax=1.4)
    plot.drawline(*rline,color=kBlue,title=stitle_reco)
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("ratio_weight",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions
    dyhists = [dyhist,obsdyhist,dyhist_gen,dyhist_unf]
    pname_ = repkey(pname,CAT="dy_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,dyhists,clone=True,dividebins=True,ratio=True)
    plot.draw(logx=logx,logy=logy,xmin=1.0,ytitle="Events / GeV",style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Drell-Yan distributions - normalized
    pname_ = repkey(pname,CAT="dy_norm_"+selection.filename).replace('_baseline',"")
    plot   = Plot(xvar_reco,dyhists,clone=True,dividebins=True,ratio=True)
    plot.draw(logx=logx,logy=logy,xmin=1.0,norm=True,style=1)
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    plot.canvas.Write("dy_norm",gStyle.kOverwrite)
    plot.close()
    
    #### PLOT - Drell-Yan distributions - gen vs. unfolded
    ###pname_ = repkey(pname,CAT="dy_gen_"+selection.filename).replace('_baseline',"")
    ###plot   = Plot(xvar_gen,[dyhist_gen,dyhist_unf],clone=True,dividebins=True,ratio=True)
    ###plot.draw(logx=logx,logy=True,xmin=1.0,ytitle="Events / GeV")
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
    plot.draw(logx=logx,logy=logy,logz=logz,xmin=1.5,ymin=1.5,zmin=1,ztitle="Events")
    #plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("response_matrix",gStyle.kOverwrite)
    plot.close()
    
    # PLOT - Obs. / Exp.
    pname_ = repkey(pname,CAT="data-mc_"+selection.filename).replace('_baseline',"")
    plot   = Stack(xvar_reco,obshist,hists.exp)
    plot.draw(logx=logx,logy=logy,xmin=1.0,ytitle="Events / GeV")
    plot.drawlegend()
    plot.drawtext(selection.title)
    plot.saveas(pname_,ext=['.png','.pdf'])
    gStyle.Write('style',gStyle.kOverwrite)
    plot.canvas.Write("data_mc",gStyle.kOverwrite)
    plot.close()
    
    # CLOSE
    close([exphist,bkghist]+dyhists) #sfhist,obshist,+hist.exp
    outfile.Close()
    print ">>> "
    

def main(args):
  channel   = 'mumu'
  eras      = sorted(args.eras,key=lambda x: x.count('UL')) # do UL last
  parallel  = args.parallel
  verbosity = args.verbosity
  methods   = args.methods
  outdir    = "weights" #/$ERA"
  plotdir   = "weights/$ERA"
  fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  tag       = ""
  for era in eras:
    if 'UL' in era: # UL has no DY*JetsToLL_M-10to50
      global Zmbins0, Zmbins1, baseline
      print ">>> Editing Zmbins0, Zmbins1, and baseline!"
      if 10 in Zmbins0: Zmbins0.remove(10)
      if 10 in Zmbins1: Zmbins1.remove(10)
      baseline = baseline.replace("m_ll>20","m_ll>50")
      print ">>> Zmbins0 = %s"%(Zmbins0)
      print ">>> Zmbins1 = %s"%(Zmbins1)
      print ">>> baseline = %r"%(baseline)
    tag_   = tag+'_'+era
    setera(era) # set era for plot style and lumi-xsec normalization
    outdir_  = ensuredir(repkey(outdir,ERA=era))
    plotdir_ = ensuredir(repkey(plotdir,ERA=era))
    samples  = getsampleset(channel,era,fname=fname,dyweight="",dy="")
    if 1 in methods:
      measureZpt_unfold(samples,outdir=outdir_,plotdir=plotdir_,parallel=parallel,tag=tag_,verb=verbosity) # 1D
    if 2 in methods:
      measureZptmass_unfold(samples,outdir=outdir_,plotdir=plotdir_,parallel=parallel,tag=tag_,verb=verbosity) # 2D
    samples.close() # close all sample files to clean memory
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Measure Z pT reweighting in dimuon events with RooUnfold."""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='+', default=['2017'], action='store', #choices=['2016','2017','2018','UL2017']
                                         help="set era" )
  parser.add_argument('-m', '--method',  dest='methods', type=int, nargs='+', default=[1,2], action='store',
                                         help="methods: 1=1D (Z pT), 2=2D (Z pT and mass)" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print ">>> Done."
  
