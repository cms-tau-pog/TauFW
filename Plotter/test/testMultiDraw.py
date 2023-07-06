#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Efficiently draw multiple histograms with one loop over all events in a TTree
#              This script adds the MultiDraw method to the TTree class when it is imported.
# Source:
#   https://github.com/pwaller/minty/blob/master/minty/junk/MultiDraw.py
from time import time
import os, re
from array import array
from TauFW.common.tools.file import ensuredir
from ROOT import gROOT, gSystem, gDirectory, TFile, TTree, TH1D, TH2D, gRandom, TColor
from TauFW.Plotter.plot.utils import LOG
from TauFW.Plotter.plot.MultiDraw import MultiDraw
#from test.pseudoSamples import makesamples
from pseudoSamples import makesamples


def singledraw(tree,variables,selections,predefine=False,outdir='plots'):
  """Fill histograms from tree sequentially."""
  start = time()
  fname = "%s/testMultiDraw.root"%(outdir)
  file  = TFile(fname,'RECREATE')
  hists = [ ]
  print(">>> singledraw: Filling histograms with TTree::Draw for %s..."%(fname))
  for i, (selection, weight) in enumerate(selections):
    cut = "(%s)*%s"%(selection,weight)
    print(">>>   cut=%r"%(cut))
    print(">>>   \033[4m  %-18s %10s %12s %10s %12s   %s\033[0m"%("varname","mean","std. dev.","entries","integral","draw command"+' '*16))
    for variable in variables:
      varname = variable[0]
      binning = variable[1:]
      hname   = varname.replace('+','_').replace('(','').replace(')','')
      if len(binning)==1: hname += "_var"
      hname   = "%s_sel%d_single"%(hname,i+1)
      if len(binning)==3: # constant binning
        nbins, xmin, xmax = binning
      elif len(binning)==1: # variable binning
        bins  = list(binning[0])
        nbins = len(bins)-1
        xmin, xmax = bins[0], bins[-1]
        binning = (nbins,array('d',bins))
      else:
        raise IOError("Wrong binning: %s"%(binning))
      if predefine or len(binning)<3:
        hist = TH1D(hname,hname,*binning)
        dcmd = "%s >> %s"%(varname,hname)
        tree.Draw(dcmd,cut,'gOff')
        hists.append(hist)
      else:
        dcmd = "%s >> %s(%s,%s,%s)"%(varname,hname,nbins,xmin,xmax)
        tree.Draw(dcmd,cut,'gOff')
        hist = gDirectory.Get(hname)
      hists.append(hist)
      print(">>>     %-18r %10.2f %12.2f %10d %12.1f   %r"%(varname,hist.GetMean(),hist.GetStdDev(),hist.GetEntries(),hist.Integral(),dcmd))
    for hist in hists:
      hist.Write(hist.GetName(),TH1D.kOverwrite)
  file.Close()
  dtime = time()-start
  print(">>>   Took %.2fs"%(dtime))
  return dtime
  

def multidraw(tree,variables,selections,predefine=False,outdir='plots'):
  """Fill histograms from tree in parallel with MultiDraw."""
  start = time()
  fname = "%s/testMultiDraw.root"%(outdir)
  file  = TFile(fname,'RECREATE')
  hists = [ ]
  print(">>> multidraw: Filling histograms with MultiDraw for %s..."%(fname))
  for i, (selection, weight) in enumerate(selections):
    cut = "(%s)*%s"%(selection,weight)
    print(">>>   cut=%r"%(cut))
    varexps = [ ]
    for variable in variables:
      varname = variable[0]
      binning = variable[1:]
      hname   = varname.replace('+','_').replace('(','').replace(')','')
      if len(binning)==1: hname += "_var"
      hname   = "%s_sel%d_single"%(hname,i+1)
      if len(binning)==3: # constant binning
        nbins, xmin, xmax = binning
      elif len(binning)==1: # variable binning
        bins  = list(binning[0])
        nbins = len(bins)-1
        xmin, xmax = bins[0], bins[-1]
        binning = (nbins,array('d',bins))
      else:
        raise IOError("Wrong binning: %s"%(binning))
      if predefine or len(binning)<3:
        hist = TH1D(hname,hname,*binning)
        dcmd = "%s >> %s"%(varname,hname)
        varexps.append(dcmd)
        hists.append(hist)
      else:
        dcmd = "%s >> %s(%s,%s,%s)"%(varname,hname,nbins,xmin,xmax)
        varexps.append(dcmd)
    results = tree.MultiDraw(varexps,cut,hists=hists)
    assert len(varexps)==len(results), "Mismatch between histograms (%s) and draw commands (%s)!"%(results,varexps)
    print(">>>   \033[4m  %-18s %10s %12s %10s %12s   %s\033[0m"%("varname","mean","std. dev.","entries","integral","draw command"+' '*16))
    for variable, dcmd, hist in zip(variables,varexps,results):
      varname = variable[0]
      assert hist.GetName() in dcmd, "Mismatch between histogram (%r) and draw command (%r)!"%(hist.GetName(),dcmd)
      print(">>>     %-18r %10.2f %12.2f %10d %12.1f   %r"%(varname,hist.GetMean(),hist.GetStdDev(),hist.GetEntries(),hist.Integral(),dcmd))
      hist.Write(hist.GetName(),TH1D.kOverwrite)
  file.Close()
  dtime = time()-start
  print(">>>   Took %.2fs"%(dtime))
  return dtime
  

def multidraw2D(tree,variables,selections,predefine=False,outdir='plots'):
  """Fill 2D histograms from tree in parallel with MultiDraw."""
  start = time()
  fname = "%s/testMultiDraw.root"%(outdir)
  file  = TFile(fname,'RECREATE')
  hists = [ ]
  print(">>> multidraw2D: Filling histograms with MultiDraw for %s..."%(fname))
  for i, (selection, weight) in enumerate(selections):
    cut = "(%s)*%s"%(selection,weight)
    print(">>>   cut=%r"%(cut))
    varexps = [ ]
    for xvar, nxbins, xmin, xmax, yvar, nybins, ymin, ymax in variables:
      hname = ("%s_%s_sel%d_single"%(xvar,yvar,i+1)).replace('+','_').replace('(','').replace(')','')
      if predefine:
        hist = TH2D(hname,hname,nxbins,xmin,xmax,nybins,ymin,ymax)
        dcmd = "%s:%s >> %s"%(yvar,xvar,hname)
        varexps.append(dcmd)
        hists.append(hist)
      else:
        dcmd = "%s:%s >> %s(%d,%s,%s,%d,%s,%s)"%(yvar,xvar,hname,nbins,xmin,xmax)
        varexps.append(dcmd)
    results = tree.MultiDraw(varexps,cut,hists=hists)
    assert len(varexps)==len(results), "Mismatch between histograms (%s) and draw commands (%s)!"%(results,varexps)
    print(">>>   \033[4m  %-14s %-14s %10s %12s %10s %12s   %s\033[0m"%("xvar","yvar","mean","std. dev.","entries","integral","draw command"+' '*16))
    for variable, dcmd, hist in zip(variables,varexps,results):
      xvar = variable[0]
      yvar = variable[4]
      assert hist.GetName() in dcmd, "Mismatch between histogram (%r) and draw command (%r)!"%(hist.GetName(),dcmd)
      print(">>>     %-14r %-14r %10.2f %12.2f %10d %12.1f   %r"%(xvar,yvar,hist.GetMean(1),hist.GetStdDev(1),hist.GetEntries(),hist.Integral(),dcmd))
      hist.Write(hist.GetName(),TH1D.kOverwrite)
  file.Close()
  dtime = time()-start
  print(">>>   Took %.2fs"%(dtime))
  return dtime
  

def main():
  nevts      = 1000000
  predefine  = True #and False # initialize histogram before calling filling
  sample     = 'ZTT' #'Data'
  outdir     = ensuredir('plots')
  filedict   = makesamples(nevts,sample=sample,outdir=outdir)
  file, tree = filedict[sample]
  nevts      = tree.GetEntries()
  print(">>> Using pseudo data %s..."%(file.GetName()))
  
  variables = [
    ('m_vis',            20,  0, 140),
    ('m_vis',            [0,20,40,50,60,65,70,75,80,85,90,95,100,110,130,160,200]),
    ('pt_1',             40,  0, 120),
    ('pt_2',             40,  0, 120),
    ('pt_1+pt_2',        40,  0, 200),
    ('eta_1',            30, -3,   3),
    ('eta_2',            30, -3,   3),
    ('min(eta_1,eta_2)', 30, -3,   3),
    ('njets',            10,  0,  10),
  ]
  
  variables2D = [
    ('pt_1',  50,  0, 100, 'pt_2',  50,  0, 100),
    ('pt_1',  50,  0, 100, 'eta_1', 50, -3,   3),
    ('pt_2',  50,  0, 100, 'eta_2', 50, -3,   3),
    ('eta_1', 50, -3,   3, 'eta_1', 50, -3,   3),
    ('pt_1',  50,  0, 100, 'm_vis', 50,  0, 150),
    ('pt_2',  50,  0, 100, 'm_vis', 50,  0, 150),
  ]
  
  selections = [
    ('pt_1>30 && pt_2>30 && abs(eta_1)<2.4 && abs(eta_2)<2.4', "weight"),
  ]
  
  dtime1 = singledraw(tree,variables,selections,outdir=outdir,predefine=predefine)
  dtime2 = multidraw(tree,variables,selections,outdir=outdir,predefine=predefine)
  dtime3 = multidraw2D(tree,variables2D,selections,outdir=outdir,predefine=predefine)
  file.Close()
  print(">>> Result: MultiDraw is %.2f times faster than TTree::Draw for %s events and %s variables!"%(dtime1/dtime2,nevts,len(variables)))
  

if __name__ == '__main__':
  main()
  print(">>> Done!")
  
