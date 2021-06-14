# Author: Izaak Neutelings (November 2018)
import os, re
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensureTFile
from TauFW.common.tools.log import Logger
datadir = os.path.join(datadir,"pileup")
LOG     = Logger('PileupTool',showname=True)


class PileupWeightTool:
  
  def __init__(self, era, sigma='central', sample=None, buggy=False, flat=False, minbias=None, verb=0):
    """Load data and MC pilup profiles."""
    
    assert( sigma in ['central','up','down'] ), "You must choose a s.d. variation from: 'central', 'up', or 'down'."
    if not minbias:
      minbias = '69p2'
      if sigma=='down':
        minbias = '66p0168' # -4.6%
      elif sigma=='up':
        minbias = '72p3832' # +4.6%
    
    datafilename, mcfilename = None, None
    if 'UL' in era:
      if '2016' in era and 'preVFP' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_UL2016_preVFP_%s.root"%(minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_UL2016_preVFP_Summer19.root")
      elif '2016' in era and 'postVFP' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_UL2016_postVFP_%s.root"%(minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_UL2016_postVFP_Summer19.root")
      elif '2016' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_UL2016_%s.root"%(minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_UL2016_Summer19.root")
      elif '2017' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_UL2017_%s.root"%(minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_UL2017_Summer19.root")
      elif '2018' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_UL2018_%s.root"%(minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_UL2018_Summer19.root")
    else:
      if '2016' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_%s_%s.root"%(era,minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_%s_Moriond17.root"%(era))
      elif '2017' in era:
        tag = ""
        if buggy or sample: # pre-UL 2017 had buggy samples
          buggy = buggy or hasBuggyPU(sample)
          tag = "_old_pmx" if buggy else "_new_pmx"
        datafilename = os.path.join(datadir,"Data_PileUp_%s_%s.root"%(era,minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_%s_Winter17_V2%s.root"%(era,tag))
      elif '2018' in era:
        datafilename = os.path.join(datadir,"Data_PileUp_%s_%s.root"%(era,minbias))
        mcfilename   = os.path.join(datadir,"MC_PileUp_%s_Autumn18.root"%(era))
    assert datafilename and mcfilename, "PileupWeightTool: Did not recognize era %r!"%(era)
    
    if flat or (sample and hasFlatPU(sample)):
      mcfilename  = os.path.join(datadir,"MC_PileUp_%d_FlatPU0to75.root"%year)
    
    print "Loading PileupWeightTool for %s and %s"%(datafilename,mcfilename)
    self.datafile = ensureTFile(datafilename, 'READ')
    self.mcfile   = ensureTFile(mcfilename, 'READ')
    self.datahist = self.datafile.Get('pileup')
    self.mchist   = self.mcfile.Get('pileup')
    self.datahist.SetDirectory(0)
    self.mchist.SetDirectory(0)
    self.datahist.Scale(1./self.datahist.Integral())
    self.mchist.Scale(1./self.mchist.Integral())
    self.datafile.Close()
    self.mcfile.Close()
    
  
  def getWeight(self,npu):
    """Get pileup weight for a given number of pileup interactions."""
    data = self.datahist.GetBinContent(self.datahist.GetXaxis().FindBin(npu))
    mc   = self.mchist.GetBinContent(self.mchist.GetXaxis().FindBin(npu))
    if mc>0.:
      ratio = data/mc
      if ratio>5.: return 5.
      return data/mc
    LOG.warning("PileupWeightTools.getWeight: Could not make pileup weight for npu=%s data=%s, mc=%s"%(npu,data,mc))
    return 1.
  
  

def hasBuggyPU(sample):
  """Manually check whether a given samplename has a buggy PU."""
  # BUGGY (large peak at zero nTrueInt, and bump between 2-10):
  # Use TauFW/PicoProducer/utils/check2017BuggedPU.sh to check:
  #  /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_v1-DeepTauv2_TauPOG-v1/USER
  #  /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_ext1_v1-DeepTauv2_TauPOG-v1/USER
  #  /W3JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017_12Apr2018_v1-DeepTauv2_TauPOG-v1/USER
  #  /WZ_TuneCP5_13TeV-pythia8/RunIIFall17NanoAODv5_PU2017_12Apr2018_v1-DeepTauv2_TauPOG-v1/USER
  #  /WZ_TuneCP5_13TeV-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7_ext1-v1/NANOAODSIM
  #  ??? /DYJetsToLL_M-10to50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7-v2/NANOAODSIM
  if "RunIIFall17" in sample:
    if all(p in sample for p in ["DYJetsToLL_M-50","madgraph","pythia8","PU2017RECOSIMstep"]):
      return True
    #if all(p in sample for p in ["W3JetsToLNu","madgraph","pythia8","PU2017"]):
    #  return True
    #if all(p in sample for p in ["WZ_","pythia8","PU2017"]):
    #  return True
  return False
  

def hasFlatPU(sample):
  """Check whether a given samplename has a flat PU."""
  #  /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8_Fall17/RunIIFall17NanoAODv5_FlatPU0to75TuneCP5_12Apr2018_v2-DeepTauv2_TauPOG-v1/USER
  if "FlatPU0to75" in sample:
    return True
  return False
  
