#! /usr/bin/env python
# Author: Izaak Neutelings (July 2021)
# Description: Quick 'n dirty test of macros
import os, re
from TauFW.common.tools.log import header
from TauFW.Plotter.sample.utils import loadmacro, setera
from TauFW.Plotter.plot.string import makehistname
from TauFW.Plotter.plot.Plot import Plot
from ROOT import gROOT, TFile, TH1D


def testUtils():
  """Test utils.C macro."""
  print header("testUtils")
  
  # LOAD MACRO
  gROOT.ProcessLine(".L python/macros/utils.C+O")
  #loadmacro("python/macros/pileup.C")
  from ROOT import TLorentzVector, TVector3
  from ROOT import DeltaPhi, DeltaPhi2Pi, DeltaR, Mom, InvMass
  
  # CHECK InvMass
  ptvals  = [ 10, 30, 100 ]
  mvals   = [ 0, 10, 30, 100 ]
  phivals = [ 0.0, 1.5, ] #3.0 ]
  etavals = [ 0.0, 1.5, ] #3.0 ]
  tlvs    = [(pt,e,p,m) for pt in ptvals for m in mvals for e in etavals for p in phivals if pt>m]
  print ">>> %7s %5s %5s %6s %8s %8s %8s | %6s %5s %5s %6s %8s %8s %8s | %10s %10s %10s %9s"%(
    'pt1','eta1','phi1','m1','p1','tlv1.P','tlv1.E','pt2','eta2','phi2','m2','p2','tlv2.P','tlv2.E','InvMass','tlv.M','diff [%]','tlv.E')
  for pt1, eta1, phi1, m1 in tlvs:
    for pt2, eta2, phi2, m2 in tlvs:
      tlv1  = TLorentzVector()
      tlv2  = TLorentzVector()
      tlv1.SetPtEtaPhiM(pt1,eta1,phi1,m1)
      tlv2.SetPtEtaPhiM(pt2,eta2,phi2,m2)
      tlv   = tlv1+tlv2
      invm1 = InvMass(pt1,eta1,phi1,m1,pt2,eta2,phi2,m2)
      invm2 = tlv.M() # compare to ROOT
      mdiff = 100.0*(invm1-invm2)
      p1    = Mom(pt1,eta1)
      p2    = Mom(pt2,eta2)
      print ">>> %7.2f %5.2f %5.2f %6.2f %8.2f %8.2f %8.2f | %6.2f %5.2f %5.2f %6.2f %8.2f %8.2f %8.2f | %10.5f %10.5f %10.7f %9.3f"%(
                 pt1,eta1,phi1,m1,p1,tlv1.P(),tlv1.E(),pt2,eta2,phi2,m2,p2,tlv2.P(),tlv2.E(),invm1,tlv.M(),mdiff,tlv.E())
  print ">>> "
  
  # CHECK DeltaPhi, DeltaR
  phivals = [ 0.0, 1.5, 2.5, ] #3.0 ]
  etavals = [ 0.0, 1.5, 2.5, ] #3.0 ]
  vecs    = [(e,p) for e in etavals for p in phivals]
  print ">>> %7s %5s %5s %5s | %8s %11s %11s | %8s %9s"%(
    'eta1','phi1','eta2','phi2','DeltaPhi','V3.DeltaPhi','DeltaPhi2Pi','DeltaR','V3.DeltaR')
  for eta1, phi1 in vecs:
    for eta2, phi2 in vecs:
      dphi1 = DeltaPhi(phi1,phi2)
      dphi2 = DeltaPhi2Pi(phi1,phi2)
      dR    = DeltaR(eta1,phi1,eta2,phi2)
      vec1  = TVector3()
      vec2  = TVector3()
      vec1.SetPtEtaPhi(10.,eta1,phi1)
      vec2.SetPtEtaPhi(10.,eta2,phi2)
      print ">>> %7.2f %5.2f %5.2f %5.2f | %8.4f %11.4f %11.4f | %8.4f %9.4f"%(
                 eta1,phi1,eta2,phi2,dphi1,vec1.DeltaPhi(vec2),dphi2,dR,vec1.DeltaR(vec2))
  print ">>> "
  

def testPileup():
  """Test pileup.C macro."""
  print header("testPileup")
  
  # LOAD MACRO
  gROOT.ProcessLine(".L python/macros/pileup.C+O")
  #loadmacro("python/macros/pileup.C")
  from ROOT import loadPU, getPUWeight
  
  # LOAD SF
  npvs = [ # must be integers
    10, 20, 25, 28, 30, 35, 40, 45, 50, 60, 70,
  ]
  indir = "../PicoProducer/data/pileup/"
  fnamesets = [
    ("",""),
    (indir+"Data_PileUp_UL2016_preVFP_69p2.root",indir+"MC_PileUp_UL2016_preVFP_Summer19.root"),
  ]
  for fname_data, fname_mc in fnamesets:
    if fname_data or fname_mc:
      loadPU(fname_data,fname_mc)
    else:
      loadPU()
    print ">>> data=%r, mc=%r"%(fname_data,fname_mc)
    print ">>> %7s %9s"%('npv','data/mc')
    for npv in npvs:
      weight = getPUWeight(npv)
      print ">>> %7d %9.4f"%(npv,weight)
    print ">>> "
  

def testTopPtWeight():
  """Test topptweight.C macro."""
  print header("testTopPtWeight")
  
  # LOAD MACRO
  gROOT.ProcessLine(".L python/macros/topptweight.C+O")
  #loadmacro("python/macros/topptweight.C")
  from ROOT import getTopPtSF, getTopPtWeight
  from ROOT import getTopPtSF_NNLO, getTopPtWeight_NNLO
  
  # LOAD SF
  pts1 = [
    10, 20, 50, 100, 200, 500, 1000
  ]
  pts2 = [
    0, 10, 50, 100, 300
  ]
  funcs = [
    ('Data/MC', getTopPtSF,      getTopPtWeight     ),
    ('NNLO/NLO',getTopPtSF_NNLO, getTopPtWeight_NNLO),
  ]
  for title, sffunc, weightfunc in funcs:
    print ">>> "+title
    print ">>> %11s %9s %9s %9s %15s %10s"%('pt1','pt2','sf(pt1)','sf(pt2)','sf(pt1)*sf(pt2)','weight')
    for pt1 in pts1:
      sf1 = sffunc(pt1)
      for pt2 in pts2:
        if pt1>pt2: continue
        sf2 = sffunc(pt2)
        weight1 = sf1*sf2
        weight2 = weightfunc(pt1,pt2)
        print ">>> %11.1f %9.1f %9.4f %9.4f %15.4f %10.4f"%(pt1,pt2,sf1,sf2,weight1,weight2)
    print ">>> "
    

def testTauIDSF():
  """Test tauIDSF.C macro."""
  print header("testTauIDSF")
  
  # LOAD MACRO
  gROOT.ProcessLine(".L python/macros/tauIDSF.C+O")
  #loadmacro("python/macros/tauIDSF.C")
  from ROOT import loadTauIDSF, getTauIDSF
  #from ROOT import TIDNom, TIDUp, TIDDown # enum
  
  # LOAD SF
  sffile = "/t3home/ineuteli/eos/public/forTAU/TauID_SF_dm_DeepTau2017v2p1VSjet_2016Legacy_ptgt20.root"
  hname  = "Medium"
  loadTauIDSF(sffile,hname)
  print ">>> %4s %9s %9s %9s %9s"%('dm','sf(dm)','sf(dm,0)','sf(dm,-1)','sf(dm,+1)') #,'sf(dm,Up)','sf(dm,Down)')
  for dm in range(0,14):
    sf    = getTauIDSF(dm,5)
    sf0   = getTauIDSF(dm,5,0)
    sfdn  = getTauIDSF(dm,5,-1)
    sfup  = getTauIDSF(dm,5,+1)
    sfdn2 = getTauIDSF(dm,5,-1)
    #sfup2 = getTauIDSF(dm,TIDUp)
    #sfdn2 = getTauIDSF(dm,TIDDown)
    print ">>> %4s %9.4f %9.4f %9.4f %9.4f"%(dm,sf,sf0,sfdn,sfup) #,sfdn2,sfup2)
  
  # LOAD TREE
  setera(2016)
  fname = "/scratch/ineuteli/analysis/UL2018/DY/DYJetsToLL_M-50_mutau.root"
  file = TFile(fname)
  tree = file.Get("tree")
  
  # SET ALIASES
  aliases = [
    # bug: https://github.com/root-project/root/pull/3797
    #("sf_dm","getTauIDSF(dm_2,genmatch_2)"), # does not work !?
    #("sf_dm","getTauIDSF(dm_2,genmatch_2,0)"), # does not work !?
    ("sf_dm","getTauIDSF(dm_2,5,+0)"), # works
    ("sf_dm","getTauIDSF(dm_2,genmatch_2,+0)"), # works
    ("sf_dmUp","getTauIDSF(dm_2,genmatch_2,+1)"),
    ("sf_dmDown","getTauIDSF(dm_2,genmatch_2,-1)"),
  ]
  for alias, expr in aliases:
    print '>>> tree.SetAlias("%s","%s")'%(alias,expr)
    tree.SetAlias(alias,expr)
  
  # DRAW HISTOGRAMS
  cut = "q_1*q_2<0 && iso_1<0.15 && idMedium_1 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
  sfs = [
    #"getTauIDSF(dm_2)",
    ##"getTauIDSF(dm_2,genmatch_2,0)",
    #"getTauIDSF(dm_2,genmatch_2,1)",
    #"getTauIDSF(dm_2,genmatch_2,-1)",
    ##"getTauIDSF(dm_2,genmatch_2,%d)"%(TIDUp),
    ##"getTauIDSF(dm_2,genmatch_2,TIDUp)",
    "sf_dm",     # alias
    "sf_dmUp",   # alias
    "sf_dmDown", # alias
  ]
  hists = [ ]
  for sf in sfs:
    hname = makehistname("testhist_",sf)
    hist = TH1D(hname,sf,25,50,150)
    dcmd = "m_vis >> %s"%(hname)
    print '>>> tree.Draw(%s,"(%s)*%s")'%(dcmd,cut,sf)
    out = tree.Draw(dcmd,"(%s)*%s"%(cut,sf),'gOff')
    print out
    hists.append(hist)
  
  # PLOT HISTOGRAMS
  plot = Plot("m_vis",hists)
  plot.draw(ratio=True,rmin=0.9,rmax=1.1)
  plot.drawlegend()
  plot.saveas("plots/testMacros_tauIDSF.png")
  plot.close()
  

def testLoadHist():
  """Test loadHist.C macro."""
  print header("testLoadHist")
  
  # LOAD MACRO
  gROOT.ProcessLine(".L python/macros/loadHist.C+O")
  #loadmacro("python/macros/loadHist.C")
  from ROOT import loadHist, getBin
  
  # LOAD SF
  sffile = "/t3home/ineuteli/eos/public/forTAU/TauID_SF_dm_DeepTau2017v2p1VSjet_2016Legacy_ptgt20.root"
  hname  = "Medium"
  loadHist(sffile,hname)
  print ">>> %4s %9s %9s %9s %9s"%('dm','sf(dm)','sf(dm,0)','sf(dm,-1)','sf(dm,+1)')
  for dm in range(0,14):
    sf    = getBin(dm)
    sf0   = getBin(dm,0)
    sfdn  = getBin(dm,-1)
    sfup  = getBin(dm,+1)
    sfdn2 = getBin(dm,-1)
    print ">>> %4s %9.4f %9.4f %9.4f %9.4f"%(dm,sf,sf0,sfdn,sfup)
  
  # LOAD TREE
  setera(2016)
  fname = "/scratch/ineuteli/analysis/UL2018/DY/DYJetsToLL_M-50_mutau.root"
  file = TFile(fname)
  tree = file.Get("tree")
  
  # SET ALIASES
  aliases = [
    #("sf_dm","getBin(dm_2)"), # does not work !?
    #("sf_dm","getBin(dm_2,0)"), # does not work !?
    ("sf_dm","getBin(dm_2,+0)"), # works
    ("sf_dmUp","getBin(dm_2,+1)"),
    ("sf_dmDown","getBin(dm_2,-1)"),
  ]
  for alias, expr in aliases:
    print '>>> tree.SetAlias("%s","%s")'%(alias,expr)
    tree.SetAlias(alias,expr)
  
  # DRAW HISTOGRAMS
  cut  = "q_1*q_2<0 && iso_1<0.15 && idMedium_1 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
  sfs = [
    #"getBin(dm_2)",
    ##"getBin(dm_2,0)",
    #"getBin(dm_2,1)",
    #"getBin(dm_2,-1)",
    "sf_dm",     # alias
    "sf_dmUp",   # alias
    "sf_dmDown", # alias
  ]
  hists = [ ]
  for sf in sfs:
    hname = makehistname("testhist_",sf)
    hist = TH1D(hname,sf,25,50,150)
    dcmd = "m_vis >> %s"%(hname)
    print '>>> tree.Draw(%s,"(%s)*%s")'%(dcmd,cut,sf)
    out = tree.Draw(dcmd,"(%s)*%s"%(cut,sf),'gOff')
    print out
    hists.append(hist)
  
  # PLOT HISTOGRAMS
  plot = Plot("m_vis",hists)
  plot.draw(ratio=True,rmin=0.9,rmax=1.1)
  plot.drawlegend()
  plot.saveas("plots/testMacros_loadHist.png")
  plot.close()
  

def main():
  testUtils()
  testPileup()
  testTopPtWeight()
  testTauIDSF()
  testLoadHist()
  

if __name__ == '__main__':
    main()
    print ">>> Done"
    
