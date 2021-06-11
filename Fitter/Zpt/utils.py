#! /usr/bin/env python
# Author: Izaak Neutelings (May 2021)
# Description: Help functions for Z pT measurment
from config.samples import *
from TauFW.common.tools.file import ensuredir, ensureTFile, ensureTDirectory
from TauFW.Plotter.plot.Stack import Stack, Plot, LOG, close
from ROOT import gStyle, gROOT, gSystem, gDirectory, kRed, kBlue, kDashed


def writehist(hist,name,title,xtitle,ytitle,ztitle=None,verb=0):
  """Help function to write a histogram to a file."""
  hist.SetTitle(title)
  hist.GetXaxis().SetTitle(xtitle)
  hist.GetYaxis().SetTitle(ytitle)
  if ztitle:
    hist.GetZaxis().SetTitle(ztitle)
  if verb>=1:
    print ">>> writehist: Writing %r as %r to %s"%(hist.GetName(),name,gDirectory.GetPath())
  hist.Write(name,hist.kOverwrite)
  

def getdyhist(hname,hists,tag="",verb=0):
  """Separate DY from other background histograms and
  create data/MC weight histogram."""
  obsname = hname+"_obs"+tag
  expname = hname+"_exp"+tag
  dyname  = hname+"_dy"+tag
  bkgname = hname+"_bkg"+tag
  dyhist  = None # signal Drell-Yan
  exphist = None # all expected, incl. DY
  bkghist = None # all expected backgrounds, excl. DY
  if verb>=1:
    print ">>> getdyhist: Adding %r to %r..."%(hists.data.GetName(),obsname)
  obshist = hists.data # observed data
  obshist.SetName(obsname)
  obshist.SetTitle("Observed")
  
  # SEPARATE DRELL-YAN & BACKGROUNDS
  for hist in hists.exp:
  
    # EXPECTED (DY + BACKGROUNDS)
    if not exphist:
      if verb>=1:
        print ">>> getdyhist: Cloning %r to %r..."%(hist.GetName(),expname)
      exphist = hist.Clone(expname)
      exphist.SetTitle("Expected")
    else:
      if verb>=1:
        print ">>> getdyhist: Adding %r to %r..."%(hist.GetName(),expname)
      exphist.Add(hist)
    
    # DRELL-YAN
    if any(d in hist.GetName() for d in ['DY',"Drell-Yan",'ZMM']):
      if not dyhist:
        if verb>=1:
          print ">>> getdyhist: Cloning %r to %r..."%(hist.GetName(),dyname)
        dyhist = hist.Clone(dyname)
        #dyhist.SetName(dyname)
        #dyhist.SetTitle(dyname)
      else:
        LOG.fatal("Found more than one DY hist: %s and %s in %s"%(dyhist,hist,hists.exp))
   
    # BACKGROUNDS
    else:
      if not bkghist:
        if verb>=1:
          print ">>> getdyhist: Cloning %r to %r..."%(hist.GetName(),bkgname)
        bkghist = hist.Clone(bkgname)
        bkghist.SetTitle("Background")
      else:
        if verb>=1:
          print ">>> getdyhist: Adding %r to %r..."%(hist.GetName(),bkgname)
        bkghist.Add(hist)
  
  # GET OBS. DY = OBS. DATA - BKG
  obsdyhist = obshist.Clone(hname+"_obsdy"+tag) # DATA - BKG
  obsdyhist.SetBinErrorOption(obshist.kNormal)
  obsdyhist.Add(bkghist,-1)
  
  # SANITY CHECK
  if verb>=1:
    print ">>> getdyhist: %9s %11s %11s %11s %11s %11s"%("","Obs.","Exp.","Drell-Yan","Background","DY+Bkg")
    print ">>> getdyhist: %9s %11.1f %11.1f %11.1f %11.1f %11.1f"%(
      "Integral",obshist.Integral(),exphist.Integral(),dyhist.Integral(),bkghist.Integral(),dyhist.Integral()+bkghist.Integral())
    print ">>> getdyhist: %9s %11.1f %11.1f %11.1f %11.1f %11.1f"%(
      "Entries", obshist.GetEntries(),exphist.GetEntries(),dyhist.GetEntries(),bkghist.GetEntries(),dyhist.GetEntries()+bkghist.GetEntries())
    ratio = dyhist.Integral()/obsdyhist.Integral() # check for over-/underestimation in ratio
    print ">>> getdyhist: Exp. DY / Obs. DY = %.1f / %.1f = %.4f"%(dyhist.Integral(),obsdyhist.Integral(),ratio)
  
  return obshist, exphist, dyhist, bkghist, obsdyhist
  

def getsfhist(hname,obshist,exphist,dyhist,bkghist,obsdyhist=None,tag=""):
  # WEIGHTS = ( DATA - BKG ) / DY = ( DATA - MC + DY ) / DY
  #sfhist  = ( obshist - bkghist ) / dyhist
  if obsdyhist==None:
    obsdyhist = obshist.Clone(hname+"_obsdy"+tag) # DATA - BKG
    obsdyhist.SetBinErrorOption(obshist.kNormal)
    obsdyhist.Add(bkghist,-1)
  sfhist = obsdyhist.Clone(hname+"_weights"+tag) # ( DATA - BKG ) / DY
  sfhist.Divide(dyhist)
  sfhist.SetName(hname+"_weights"+tag)
  sfhist.SetTitle(hname+"_weights"+tag)
  
  # NORMALIZE numerator and denominator, s.t. weight only has a shape effect
  intobs = obshist.Integral()
  intexp = exphist.Integral()
  intdy  = dyhist.Integral()
  intbkg = bkghist.Integral()
  intnum = intobs - intbkg
  scale  = intnum/intdy
  print ">>>   all obs. data = %.1f, all MC = %.1f (DY = %.1f, other = %.1f)"%(intobs,intexp,intdy,intbkg)
  print ">>>   => ratio = ( obs. data - other MC ) / ( DY MC ) = %.1f / %.1f = %.3f"%(intnum,intdy,scale)
  sfhist.Scale(1./scale)
  
  return sfhist
  
