#! /usr/bin/env python
# Author: Izaak Neutelings (December 2018)
# Instructions:
#   python3 test/testSFs.py -t mu -m 2 -y UL2016_post UL2016_pre UL2017 UL2018 2022_pre 2022_post 2023C 2023D
import time
start0 = time.time()
print(">>> Importing modules...")
from TauFW.common.tools.log import Logger, color, underline
LOG = Logger("testSF")

# PATHS
path       = 'data/lepton/'
pathHTT_mu = 'data/lepton/HTT/Muon/Run2017/'
pathHTT_el = 'data/lepton/HTT/Electron/Run2017/'
maxerr     = 10 # maximum number of errors
neta       = True # include negative eta
ptvals_    = [ 10., 20., 21., 22., 24., 25., 26., 27., 34., 35., 36., 40., 60., 156., 223., 410., 560. ]
etavals_   = [ 0.0, 0.5, 1.1, 1.9, 2.3, 2.4, 2.8, 3.4 ]

# MATRIX
def printtable(name,method,ptvals=None,etavals=None,etamax=3.0,phi=None):
  start2 = time.time()
  if ptvals==None:
    ptvals  = ptvals_
  if etavals==None:
    etavals = etavals_
    if neta:
      etavals = [-eta for eta in reversed(etavals) if eta>0]+etavals # add negative values
  if etamax!=None:
    etavals = [eta for eta in etavals if abs(eta)<etamax]
  print(">>>   %s:"%name)
  #TAB = LOG.table("%9.2f"+" %9.2f"*len(etavals)+"  ")
  #TAB.printheader("pt\eta",*[str(eta) for eta in etavals])
  print(">>>   "+underline("%10s "%('pt\eta')+' '.join('%9.2f'%eta for eta in etavals)))
  errors = [ ]
  for pt in ptvals:
    #print(">>>    %10.2f"%(pt)+' '.join('%10.3f'%method(pt,eta) for eta in etavals))
    #TAB.printrow(pt,*[method(pt,eta) for eta in etavals])
    row = ">>>   %10.2f"%(pt)
    for eta in etavals:
      try:
          if phi!=None:
            row += " %9.2f"%(method(pt,eta,phi))
          else:
            row += " %9.2f"%(method(pt,eta))
      except Exception as error:
        row += color("     ERROR",'red')
        errors.append(error)
    print(row)
  print(">>>   Got %d SFs in %.3f seconds"%(len(ptvals)*len(etavals),time.time()-start2))
  if len(errors)>=1:
    print(">>>   Caught %s error(s):"%(len(errors)))
    if maxerr>=1:
      errors = errors[:maxerr]
    for error in errors:
      print(">>>     "+color("%s: %r"%(error.__class__.__name__,str(error)),'red'))
  print(">>> ")
  

def muonPOG():
  LOG.header("muonPOG (ROOT)")
  
  # TRIGGER (Muon POG)
  start1 = time.time()
  print(">>> Initializing trigger SFs from Muon POG (ROOT)...")
  sftool_trig = ScaleFactor(path+"MuonPOG/Run2017/EfficienciesAndSF_RunBtoF_Nov17Nov2017.root","IsoMu27_PtEtaBins/abseta_pt_ratio",'mu_trig',ptvseta=True)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  printtable('trigger POG',sftool_trig.getSF)
  
  # ID (Muon POG)
  start1 = time.time()
  sftool_id  = ScaleFactor(path+"MuonPOG/Run2018/RunABCD_SF_ID.root","NUM_MediumID_DEN_genTracks_pt_abseta",'mu_id',ptvseta=False)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  printtable('id POG',sftool_id.getSF)
  
  # ISO (Muon POG)
  start1 = time.time()
  sftool_iso = ScaleFactor(path+"MuonPOG/Run2018/RunABCD_SF_ISO.root","NUM_TightRelIso_DEN_MediumID_pt_abseta",'mu_iso',ptvseta=False)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  printtable('iso POG',sftool_iso.getSF)
  
  # ID/ISO (Muon POG)
  start1 = time.time()
  sftool_idiso    = sftool_id*sftool_iso
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  printtable('idiso POG',sftool_idiso.getSF)  
  print(">>> ")
  

def muonHTT():
  LOG.header("muonHTT (ROOT)")
  
  # TRIGGER (HTT)
  start1 = time.time()
  print(">>> Initializing trigger SFs from HTT...")
  sftool_mu_trig_HTT = ScaleFactorHTT(pathHTT_mu+"Muon_IsoMu24orIsoMu27.root","ZMass",'mu_idiso')
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  printtable('trigger HTT',sftool_mu_trig_HTT.getSF)
  
  ## ID ISO (HTT)
  #start1 = time.time()
  #print(">>> Initializing idiso SFs from HTT...")
  #sftool_mu_idiso_HTT = ScaleFactorHTT(pathHTT_mu+"Muon_IdIso_IsoLt0p15_eff_RerecoFall17.root","ZMass",'mu_idiso')
  #print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  #printtable('idiso HTT',sftool_mu_idiso_HTT.getSF)
  #print(">>> ")
  

def electronHTT():
  LOG.header("electronHTT (ROOT)")
  
  # RECO (EGAMMA POG)
  sftool_ele_reco_HTT = ScaleFactor(pathHTT_el+"egammaEffi.txt_EGM2D_runBCDEF_passingRECO.root","EGamma_SF2D",'ele_reco',ptvseta=True)
  printtable('reco POG',sftool_ele_reco_HTT.getSF)
  
  # ID/ISO (HTT)
  sftool_ele_idiso_HTT = ScaleFactorHTT(pathHTT_el+"Electron_IdIso_IsoLt0.15_IsoID_eff.root","ZMass",'ele_idiso')
  printtable('idiso HTT',sftool_ele_idiso_HTT.getSF)
  

def muonSFs_JSON(era='UL2018'):
  LOG.header("muonSFs (JSON)")
  
  # MUON SFs
  start1 = time.time()
  print(">>> Initializing MuonSF object for era=%r..."%(era))
  muSFs = MuonSFs(era)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  
  # GET SFs
  printtable('trigger',muSFs.getTriggerSF)
  printtable('idiso',muSFs.getIdIsoSF)
  print(">>> ")
  

def muonSFs_ROOT(era='UL2018'):
  LOG.header("muonSFs (ROOT)")
  
  # MUON SFs
  start1 = time.time()
  print(">>> Initializing MuonSF object for era=%r..."%(era))
  muSFs = MuonSFs_ROOT(era)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  
  # GET SFs
  printtable('trigger',muSFs.getTriggerSF)
  printtable('idiso',muSFs.getIdIsoSF)
  print(">>> ")
  

def electronSFs(era='UL2018'):
  LOG.header("electronSFs")
  
  # ELECTRON SFs
  print(">>> ")
  start1 = time.time()
  print(">>> Initializing ElectronSFs object for era=%s..."%(era))
  eleSFs = ElectronSFs(era)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  
  # GET SFs
  printtable('trigger',eleSFs.getTriggerSF)
  printtable('idiso',eleSFs.getIdIsoSF,phi=1.)
  
def electronSFs_ROOT(era='UL2018'):
  LOG.header("electronSFs ROOT")
  
  # ELECTRON SFs
  print(">>> ")
  start1 = time.time()
  print(">>> Initializing ElectronSFs object for era=%s..."%(era))
  eleSFs = ElectronSFs_ROOT(era)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  
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
  

def btagSFs(era='UL2018',tagger='DeepJet'):
  LOG.header("btagSFs")
  
  # BTAG SFs
  print(">>> ")
  start1 = time.time()
  print(">>> Initializing BTagWeightTool(%r,%r) object..."%(tagger,era))
  btagSFs = BTagWeightTool(tagger,wp='medium',era=era,channel='mutau')
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  
  # GET SFs
  printtable('%s g'%tagger,lambda p,e: btagSFs.getSF(p,e,0,True),etamax=5)
  #printtable('%s u'%tagger,lambda p,e: btagSFs.getSF(p,e,1,True),etamax=5)
  #printtable('%s d'%tagger,lambda p,e: btagSFs.getSF(p,e,2,True),etamax=5)
  #printtable('%s s'%tagger,lambda p,e: btagSFs.getSF(p,e,3,True),etamax=5)
  printtable('%s c'%tagger,lambda p,e: btagSFs.getSF(p,e,4,True),etamax=5)
  printtable('%s b'%tagger,lambda p,e: btagSFs.getSF(p,e,5,True),etamax=5)
  

def pileupSFs(era='UL2018'):
  LOG.header("pileupSFs")
  
  # PILE UP TOOL
  print(">>> ")
  start1 = time.time()
  print(">>> Initializing PileupTool(%r) object..."%era)
  puTool = PileupWeightTool(era)
  print(">>>   Initialized in %.1f seconds"%(time.time()-start1))
  
  ## GET SFs
  start2 = time.time()
  TAB = LOG.table("%9.1f %15.3f")
  TAB.printheader("npu","pileup weight")
  npus = [0,1,2,5,10,15,18,20,24,25,26,28,30,35,40,50,60,70,80,100]
  for npu in npus:
    TAB.printrow(npu,puTool.getWeight(npu))
  print(">>>   Got %d SFs in %.3f seconds"%(len(npus),time.time()-start2))
  

def main(args):
  tools = args.tools
  eras  = args.eras
  
  # LEPTON SF
  if not tools or 'musf' in tools:
    muonPOG()
    muonHTT()
  if not tools or 'elesf' in tools:
    electronHTT()
  if not tools or 'mu' in tools:
    for era in eras:
      muonSFs_JSON(era)
  if not tools or 'muroot' in tools:
    for era in eras:
      muonSFs_ROOT(era)
  if not tools or 'ele' in tools:
    for era in eras:
        electronSFs(era)
  if not tools or 'eleroot' in tools:
    for era in eras:
      electronSFs_ROOT(era)

  # TAU
  if not tools or 'tau' in tools:
    tauTriggerSFs()
  
  # BTV
  if not tools or 'btag' in tools:
    for era in eras:
      btagSFs(era=era,tagger='DeepJet')
  
  # PU
  if not tools or 'pu' in tools:
    for era in eras:
      pileupSFs(era)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test corrections tools"""
  parser = ArgumentParser(description=description,epilog="Good luck!")
  parser.add_argument('-t','--tool',    dest='tools', nargs='+',
                                        help="corrections tools to test" )
  parser.add_argument('-y','--era',     dest='eras', nargs='+', default=['UL2018'],
                                        help="eras to run" )
  parser.add_argument('-m','--maxerr',  dest='maxerr', type=int, default=10,
                                        help="maximum nubmer of errors to print" )
  parser.add_argument('-e','--eta',     dest='etavals', type=float, nargs='+',
                                        help="etas to check" )
  parser.add_argument('-p','--pt',      dest='ptvals', type=float, nargs='+',
                                        help="pt vals to check" )
  parser.add_argument('-n','--neta',    dest='neta', action='store_false',
                                        help="no negative eta" )
  parser.add_argument('-v','--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                        help="set verbosity level" )
  args     = parser.parse_args()
  tools    = args.tools
  maxerr   = args.maxerr
  neta     = args.neta
  if args.ptvals:
    ptvals_  = args.ptvals
  if args.etavals:
    etavals_ = args.etavals
  
  # IMPORTS
  start1 = time.time()
  from ROOT import TFile # typically slows down other modules
  print(">>>   Imported ROOT classes after %.1f seconds"%(time.time()-start1))
  
  if any(s in tools for s in ['musf','elesf']):
    start1 = time.time()
    from TauFW.PicoProducer.corrections.ScaleFactorTool import *
    print(">>>   Imported ScaleFactorTool classes after %.1f seconds"%(time.time()-start1))
  
  if 'mu' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.MuonSFs import *
    print(">>>   Imported MuonSFs classes after %.1f seconds"%(time.time()-start1))
  
  if 'muroot' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.MuonSFs_ROOT import MuonSFs as MuonSFs_ROOT
    print(">>>   Imported MuonSFs_ROOT classes after %.1f seconds"%(time.time()-start1))
  
  if 'ele' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.ElectronSFs import *
    print(">>>   Imported ElectronSFs classes after %.1f seconds"%(time.time()-start1))
 
  if 'eleroot' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.ElectronSFs_ROOT import ElectronSFs as ElectronSFs_ROOT
    print(">>>   Imported ElectronSFs_ROOT classes after %.1f seconds"%(time.time()-start1))

  if 'tau' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.TauTriggerSFs import *
    print(">>>   Imported TauTriggerSFs classes after %.1f seconds"%(time.time()-start1))
  
  if 'btag' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.BTagTool import *
    print(">>>   Imported BTagTool classes after %.1f seconds"%(time.time()-start1))
  
  if 'pu' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.PileupTool import *
    print(">>>   Imported PileupTool classes after %.1f seconds"%(time.time()-start1))
  
  if 'jetveto' in tools:
    start1 = time.time()
    from TauFW.PicoProducer.corrections.JetVetoMapTool import *
    print(">>>   Imported JetVetoMapTool classes after %.1f seconds"%(time.time()-start1))
    
  print(">>>   Imported everything after %.1f seconds"%(time.time()-start0))
  print(">>> ")
  
  # MAIN FUNCTIONALITY
  main(args)
  print(">>> ")
  print(">>> Done after %.1f seconds"%(time.time()-start0))
  print('')
