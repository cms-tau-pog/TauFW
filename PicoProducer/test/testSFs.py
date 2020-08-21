#! /usr/bin/env python
# Author: Izaak Neutelings (December 2018)
import time
start0 = time.time()
print
print ">>> importing modules..."
from TauFW.common.tools.log import Logger
LOG = Logger("testSF")

start1 = time.time()
from ROOT import TFile
print ">>>   imported ROOT classes after %.1f seconds"%(time.time()-start1)

start1 = time.time()
from TauFW.PicoProducer.corrections.ScaleFactorTool import *
print ">>>   imported ScaleFactorTool classes after %.1f seconds"%(time.time()-start1)

start1 = time.time()
from TauFW.PicoProducer.corrections.MuonSFs import *
print ">>>   imported MuonSFs classes after %.1f seconds"%(time.time()-start1)

start1 = time.time()
from TauFW.PicoProducer.corrections.ElectronSFs import *
print ">>>   imported ElectronSFs classes after %.1f seconds"%(time.time()-start1)

start1 = time.time()
from TauFW.PicoProducer.corrections.TauTriggerSFs import *
print ">>>   imported TauTriggerSFs classes after %.1f seconds"%(time.time()-start1)

start1 = time.time()
from TauFW.PicoProducer.corrections.BTagTool import *
print ">>>   imported BTagTool classes after %.1f seconds"%(time.time()-start1)

start1 = time.time()
from TauFW.PicoProducer.corrections.PileupTool import *
print ">>>   imported PileupTool classes after %.1f seconds"%(time.time()-start1)
print ">>>   imported everything after %.1f seconds"%(time.time()-start0)
print ">>> "

# PATHS
path       = 'data/lepton/'
pathHTT_mu = 'data/lepton/HTT/Muon/Run2017/'
pathHTT_el = 'data/lepton/HTT/Electron/Run2017/'

# MATRIX
def printtable(name,method,ptvals=None,etavals=None):
  start2 = time.time()
  if ptvals==None:
    ptvals  = [ 10., 20., 21., 22., 24., 26., 27., 34., 35., 36., 40., 60., 156., 223., 410., 560. ]
  if etavals==None:
    etavals = [ 0.0, 0.5, 1.1, 1.9, 2.3, 2.4, 2.8, 3.4 ]
    etavals = [-eta for eta in reversed(etavals)]+etavals
  print ">>>   %s:"%name
  TAB = LOG.table("%9.2f"+" %9.2f"*len(etavals)+"  ")
  #print ">>>    %10s"%('pt\eta')+' '.join('%10.2f'%eta for eta in etavals)
  TAB.printheader("pt\eta",*[str(eta) for eta in etavals])
  for pt in ptvals:
    #print ">>>    %10.2f"%(pt)+' '.join('%10.3f'%method(pt,eta) for eta in etavals)
    TAB.printrow(pt,*[method(pt,eta) for eta in etavals])
  print ">>>   got %d SFs in %.3f seconds"%(len(ptvals)*len(etavals),time.time()-start2)
  print ">>> "
  

def muonPOG():
  LOG.header("muonPOG")
  
  # TRIGGER (Muon POG)
  start1 = time.time()
  print ">>> initializing trigger SFs from Muon POG..."
  sftool_trig = ScaleFactor(path+"MuonPOG/Run2017/EfficienciesAndSF_RunBtoF_Nov17Nov2017.root","IsoMu27_PtEtaBins/abseta_pt_ratio",'mu_trig',ptvseta=True)
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  printtable('trigger POG',sftool_trig.getSF)
  
  # ID (Muon POG)
  start1 = time.time()
  sftool_id  = ScaleFactor(path+"MuonPOG/Run2018/RunABCD_SF_ID.root","NUM_MediumID_DEN_genTracks_pt_abseta",'mu_id',ptvseta=False)
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  printtable('id POG',sftool_id.getSF)
  
  # ISO (Muon POG)
  start1 = time.time()
  sftool_iso = ScaleFactor(path+"MuonPOG/Run2018/RunABCD_SF_ISO.root","NUM_TightRelIso_DEN_MediumID_pt_abseta",'mu_iso',ptvseta=False)
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  printtable('iso POG',sftool_iso.getSF)
  
  # ID/ISO (Muon POG)
  start1 = time.time()
  sftool_idiso    = sftool_id*sftool_iso
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  printtable('idiso POG',sftool_idiso.getSF)  
  print ">>> "
  

def muonHTT():
  LOG.header("muonHTT")
  
  # TRIGGER (HTT)
  start1 = time.time()
  print ">>> initializing trigger SFs from HTT..."
  sftool_mu_trig_HTT = ScaleFactorHTT(pathHTT_mu+"Muon_IsoMu24orIsoMu27.root","ZMass",'mu_idiso')
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  printtable('trigger HTT',sftool_mu_trig_HTT.getSF)
  
  ## ID ISO (HTT)
  #start1 = time.time()
  #print ">>> initializing idiso SFs from HTT..."
  #sftool_mu_idiso_HTT = ScaleFactorHTT(pathHTT_mu+"Muon_IdIso_IsoLt0p15_eff_RerecoFall17.root","ZMass",'mu_idiso')
  #print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  #printtable('idiso HTT',sftool_mu_idiso_HTT.getSF)
  #print ">>> "
  

def electronHTT():
  LOG.header("electronHTT")
  
  # RECO (EGAMMA POG)
  sftool_ele_reco_HTT = ScaleFactor(pathHTT_el+"egammaEffi.txt_EGM2D_runBCDEF_passingRECO.root","EGamma_SF2D",'ele_reco',ptvseta=True)
  printtable('reco POG',sftool_ele_reco_HTT.getSF)
  
  # ID/ISO (HTT)
  sftool_ele_idiso_HTT = ScaleFactorHTT(pathHTT_el+"Electron_IdIso_IsoLt0.15_IsoID_eff.root","ZMass",'ele_idiso')
  printtable('idiso HTT',sftool_ele_idiso_HTT.getSF)
  

def muonSFs():
  LOG.header("muonSFs")
  
  # MUON SFs
  start1 = time.time()
  print ">>> initializing MuonSF object..."
  muSFs = MuonSFs()
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  
  # GET SFs
  printtable('trigger',muSFs.getTriggerSF)
  printtable('idiso',muSFs.getIdIsoSF)
  print ">>> "
  
  # MUON 2018 SFs
  start1 = time.time()
  print ">>> initializing MuonSF(2018) object..."
  muSFs = MuonSFs(year=2018)
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  
  # GET SFs
  printtable('trigger',muSFs.getTriggerSF)
  printtable('idiso',muSFs.getIdIsoSF)
  print ">>> "
  

def electronSFs():
  LOG.header("electronSFs")
  
  # ELECTRON SFs
  print ">>> "
  start1 = time.time()
  print ">>> initializing ElectronSFs object..."
  eleSFs = ElectronSFs()
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  
  # GET SFs
  printtable('trigger',eleSFs.getTriggerSF)
  printtable('idiso',eleSFs.getIdIsoSF)
  

def tauTriggerSFs():
  LOG.header("tauTriggerSFs")
  
  # TAU TRIGGER
  tauSFs = TauTriggerSFs('tautau',wp='Medium', id='DeepTau2017v2p1',year=2018)
  
  # GET SFs
  ptvals  = [ 10., 20., 21., 22., 24., 26., 27., 34., 35., 36., 40., 60., 156., 223., 410., 560. ]
  dmvals  = [ 0, 1, 10, 11 ]
  #etavals = [ 0.0, 0.2, 0.5, 1.1, 1.5, 1.9, 2.0 ]
  printtable('trigger real',lambda p,d: tauSFs.getSF(p,d),ptvals=ptvals,etavals=dmvals)
  printtable('trigger fake',lambda p,d: tauSFs.getSF(p,d),ptvals=ptvals,etavals=dmvals)
  

def btagSFs(tagger='CSVv2'):
  LOG.header("btagSFs")
  
  # BTAG SFs
  print ">>> "
  start1 = time.time()
  print ">>> initializing BTagWeightTool(%r) object..."%tagger
  btagSFs = BTagWeightTool(tagger)
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  
  # GET SFs
  printtable('%s g'%tagger,lambda p,e: btagSFs.getSF(p,e,0,True))
  #printtable('%s u'%tagger,lambda p,e: btagSFs.getSF(p,e,1,True))
  #printtable('%s d'%tagger,lambda p,e: btagSFs.getSF(p,e,2,True))
  #printtable('%s s'%tagger,lambda p,e: btagSFs.getSF(p,e,3,True))
  printtable('%s c'%tagger,lambda p,e: btagSFs.getSF(p,e,4,True))
  printtable('%s b'%tagger,lambda p,e: btagSFs.getSF(p,e,5,True))
  

def pileupSFs(era='UL2017'):
  LOG.header("pileupSFs")
  
  # PILE UP TOOL
  print ">>> "
  start1 = time.time()
  print ">>> initializing PileupTool(%r) object..."%era
  puTool = PileupWeightTool(era)
  print ">>>   initialized in %.1f seconds"%(time.time()-start1)
  
  ## GET SFs
  start2 = time.time()
  TAB = LOG.table("%9.1f %15.3f")
  TAB.printheader("npu","pileup weight")
  npus = [0,1,2,5,10,15,18,20,24,25,26,28,30,35,40,50,60,70,80,100]
  for npu in npus:
    TAB.printrow(npu,puTool.getWeight(npu))
  print ">>>   got %d SFs in %.3f seconds"%(len(npus),time.time()-start2)
  

if __name__ == "__main__":
  
  muonPOG()
  #muonHTT()
  #electronHTT()
  #muonSFs()
  electronSFs()
  tauTriggerSFs()
  #btagSFs('CSVv2')
  btagSFs('DeepCSV')
  pileupSFs('2017')
  pileupSFs('UL2017')
  print ">>> "
  print ">>> done after %.1f seconds"%(time.time()-start0)
  print
