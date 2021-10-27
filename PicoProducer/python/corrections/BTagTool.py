# Author: Izaak Neutelings (January 2019)
# Sources:
#   https://twiki.cern.ch/twiki/bin/view/CMS/BTagSFMethods
#   https://twiki.cern.ch/twiki/bin/view/CMSPublic/BTagCalibration
#   https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation#Recommendation_for_13_TeV_Data
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation94X
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
#   nanoAOD-tools/python/postprocessing/modules/btv/btagSFProducer.py
#   https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/modules/btv/btagSFProducer.py
import os
from array import array
import ROOT
#ROOT.gROOT.ProcessLine('.L ./BTagCalibrationStandalone.cpp+')
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensureTFile
from TauFW.common.tools.log import Logger
from ROOT import TH2F, BTagCalibration, BTagCalibrationReader
from ROOT.BTagEntry import OP_LOOSE, OP_MEDIUM, OP_TIGHT, OP_RESHAPING # enum 0, 1, 2, 3
from ROOT.BTagEntry import FLAV_B, FLAV_C, FLAV_UDSG # enum: 0, 1, 2
datadir = os.path.join(datadir,"btag")
LOG     = Logger('BTagTool',showname=True)


class BTagWPs:
  """Contain b tagging working points."""
  def __init__( self, tagger, year=2017 ):
    assert( year in [2016,2017,2018] ), "You must choose a year from: 2016, 2017, or 2018."
    if year==2016:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
      if 'deepjet' in tagger.lower():
        self.loose    = 0.0614
        self.medium   = 0.3093
        self.tight    = 0.7221
      elif 'deep' in tagger.lower():
        self.loose    = 0.2217 # 0.2219 for 2016ReReco vs. 2016Legacy
        self.medium   = 0.6321 # 0.6324
        self.tight    = 0.8953 # 0.8958
      else: # CSV
        self.loose    = 0.5426 # for 80X ReReco
        self.medium   = 0.8484
        self.tight    = 0.9535
    elif year==2017:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation94X
      # https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation106XUL17
      if 'deepjet' in tagger.lower():
        self.loose    = 0.0532
        self.medium   = 0.3040
        self.tight    = 0.7476
      elif 'deep' in tagger.lower():
        self.loose    = 0.1522 # for 94X
        self.medium   = 0.4941
        self.tight    = 0.8001
      else: # CSV
        self.loose    = 0.5803 # for 94X
        self.medium   = 0.8838
        self.tight    = 0.9693
    elif year==2018:
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
      # https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation106XUL18
      if 'deepjet' in tagger.lower():
        self.loose    = 0.0494
        self.medium   = 0.2770
        self.tight    = 0.7264
      elif 'deep' in tagger.lower():
        self.loose    = 0.1241 # for 102X
        self.medium   = 0.4184
        self.tight    = 0.7527
      else: # CSV
        self.loose    = 0.5803 # for 94X
        self.medium   = 0.8838
        self.tight    = 0.9693
    

class BTagWeightTool:
  
  def __init__(self, tagger, wp='medium', channel='mutau', year=2017, maxeta=None, loadsys=False, type_bc='comb', yearsplit=False, filltags=[""]):
    """Load b tag weights from CSV file."""
    
    assert(year in [2016,2017,2018]), "You must choose a year from: 2016, 2017, or 2018."
    assert(tagger in ['CSVv2','DeepCSV']), "BTagWeightTool: You must choose a tagger from: CSVv2, DeepCSV!"
    assert(wp in ['loose','medium','tight']), "BTagWeightTool: You must choose a WP from: loose, medium, tight!"
    #assert(sigma in ['central','up','down']), "BTagWeightTool: You must choose a WP from: central, up, down!"
    #assert(channel in ['mutau','eletau','tautau','mumu']), "BTagWeightTool: You must choose a channel from: mutau, eletau, tautau, mumu!"
    
    # FILE
    csvname_bc = None
    if year==2016:
      if 'deep' in tagger.lower():
        # https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
        csvname = os.path.join(datadir,"DeepCSV_2016LegacySF_V1.csv")
        effname = os.path.join(datadir,"DeepCSV_2016_Moriond17_eff.root")
      else:
        csvname = os.path.join(datadir,"CSVv2_Moriond17_B_H.csv")
        effname = os.path.join(datadir,"CSVv2_2016_Moriond17_eff.root")
    elif year==2017:
      if 'deep' in tagger.lower():
        # https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation94X
        # https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation106XUL17
        csvname = os.path.join(datadir,"DeepCSV_94XSF_V5_B_F.csv")
        effname = os.path.join(datadir,"DeepCSV_2017_12Apr2017_eff.root")
      else:
        csvname = os.path.join(datadir,"CSVv2_94XSF_V2_B_F.csv")
        effname = os.path.join(datadir,"CSVv2_2017_12Apr2017_eff.root")
    elif year==2018:
      if 'deep' in tagger.lower():
        # https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
        # https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation106XUL18
        csvname = os.path.join(datadir,"DeepCSV_102XSF_V2.csv")
        effname = os.path.join(datadir,"DeepCSV_2018_Autumn18_eff.root")
      else:
        csvname = os.path.join(datadir,"CSVv2_94XSF_V2_B_F.csv")
        effname = os.path.join(datadir,"CSVv2_2018_Autumn18_eff.root")
    if not csvname_bc:
      csvname_bc = csvname
    
    # MAX ETA
    if maxeta==None:
      maxeta = 2.4 if year==2016 else 2.5
    
    # TAGGING WP
    self.wpname = wp
    self.wp     = getattr(BTagWPs(tagger,year),wp)
    if 'deep' in tagger.lower():
      tagged = lambda j: j.btagDeepB>self.wp
    else:
      tagged = lambda j: j.btagCSVV2>self.wp
    
    # LOAD CALIBRATION TOOL
    print "Loading BTagWeightTool for %s (%s WP) %s..."%(tagger,wp,csvname) #,(", "+sigma) if sigma!='central' else ""
    calib = BTagCalibration(tagger, csvname)
    if csvname_bc and csvname_bc!=csvname:
      print "  and from %s..."%(csvname_bc)
      calib_bc = BTagCalibration(tagger,csvname_bc)
    else:
      calib_bc = calib # use same calibrator
    print "  with efficiencies from %s..."%(effname)
    
    # CSV READER
    readers   = { }
    opnum     = OP_LOOSE if wp=='loose' else OP_MEDIUM if wp=='medium' else OP_TIGHT if wp=='tight' else OP_RESHAPING
    type_udsg = 'incl'
    type_bc   = type_bc # 'mujets' for QCD; 'comb' for QCD+TT
    readers['Nom'] = BTagCalibrationReader(opnum,'central')
    if loadsys:
      readers['Up']   = BTagCalibrationReader(opnum,'up')
      readers['Down'] = BTagCalibrationReader(opnum,'down')
    if yearsplit: # split uncertainties by year
      readers['UpCorr']     = BTagCalibrationReader(op,'up_correlated')
      readers['DownCorr']   = BTagCalibrationReader(op,'down_correlated')
      readers['UpUncorr']   = BTagCalibrationReader(op,'up_uncorrelated')
      readers['DownUncorr'] = BTagCalibrationReader(op,'down_uncorrelated')
    for reader in readers.values():
      reader.load(calib_bc,FLAV_B,type_bc)
      reader.load(calib_bc,FLAV_C,type_bc)
      reader.load(calib,FLAV_UDSG,type_udsg)
    
    # EFFICIENCIES
    jetmaps = { t: { } for t in filltags } # histograms counting jets to compute the b tagging efficiencies in MC
    effmaps = { } # b tag efficiencies in MC to compute b tagging weight for an event
    efffile = ensureTFile(effname)
    default = False
    if not efffile:
      LOG.warning("File %s with efficiency histograms does not exist! Reverting to default efficiency histogram..."%(effname))
      default = True
    for flavor in [0,4,5]:
      flavor  = flavorToString(flavor)
      effname = "%s/eff_%s_%s_%s"%(channel,tagger,flavor,wp)
      for tag in filltags:
        hname = "%s_%s_%s%s"%(tagger,flavor,wp,'_'+tag if tag else "")
        jetmaps[tag][flavor] = getJetMap(hname,maxeta) # numerator = b tagged jets
        jetmaps[tag][flavor+'_all'] = getJetMap(hname+'_all',maxeta) # denominator = all jets
      if efffile:
        effmaps[flavor] = efffile.Get(effname)
        if not effmaps[flavor]:
          LOG.warning("Histogram '%s' does not exist in %s! Reverting to default efficiency histogram..."%(effname,efffile.GetName()))
          default = True
          effmaps[flavor] = getDefaultEffMap(effname,flavor,wp)
      else:
        effmaps[flavor] = getDefaultEffMap(effname,flavor,wp)
      effmaps[flavor].SetDirectory(0)
    efffile.Close()
    
    if default:
      LOG.warning("Created default efficiency histograms! The b tag weights from this module should be regarded as placeholders only,\n"+\
                  "and should NOT be used for analyses. B (mis)tag efficiencies in MC are analysis dependent. Please create your own\n"+\
                  "efficiency histogram with data/btag/getBTagEfficiencies.py after running all MC samples with BTagWeightTool.")
    
    self.tagged   = tagged
    self.calib    = calib
    self.calib_bc = calib_bc
    self.readers  = readers
    self.loadsys  = loadsys
    self.jetmaps  = jetmaps
    self.effmaps  = effmaps
    self.maxeta   = maxeta
  
  def getWeight(self,jets,unc='Nom'):
    """Get b tagging event weight for a given set of jets."""
    weight = 1.
    for jet in jets:
      if abs(jet.eta)<self.maxeta:
        weight *= self.getSF(jet.pt,jet.eta,jet.partonFlavour,self.tagged(jet),unc=unc)
    return weight
  
  def getHeavyFlavorWeight(self,jets,unc='Nom'):
    """Get b tagging event weight for a given set of jets for heavy flavors only."""
    weight_bc = 1. # heavy flavor
    for jet in jets:
      if abs(jet.eta)<self.maxeta:
        if abs(jet.partonFlavour) in [4,5]: # heavy flavor: b (5), c (4)
          weight_bc *= self.getSF(jet.pt,jet.eta,jet.partonFlavour,self.tagged(jet),unc=unc)
    return weight_bc
  
  def getFlavorWeight(self,jets,unc='Nom'):
    """Get b tagging event weight for a given set of jets per flavor."""
    weight_bc   = 1. # heavy flavor
    weight_udsg = 1. # light flavor
    for jet in jets:
      if abs(jet.eta)<self.maxeta:
        if abs(jet.partonFlavour) in [4,5]: # heavy flavor: b (5), c (4)
          weight_bc *= self.getSF(jet.pt,jet.eta,jet.partonFlavour,self.tagged(jet),unc=unc)
        else: # light flavor: udsg (0-3)
          weight_udsg *= self.getSF(jet.pt,jet.eta,jet.partonFlavour,self.tagged(jet),unc=unc)
    return weight_bc, weight_udsg
  
  def getSF(self,pt,eta,flavor,tagged,unc='Nom'):
    """Get b tag SF for a single jet."""
    FLAV = flavorToFLAV(flavor)
    if   self.maxeta>=+2.4: eta = self.maxeta-0.001 # BTagCalibrationReader returns zero if |eta| > 2.4
    elif self.maxeta<=-2.4: eta = 0.001-self.maxeta
    sf = self.readers[unc].eval(FLAV,abs(eta),pt) #eval_auto_bounds
    if not tagged:
      eff = self.getEff(pt,eta,flavor)
      if eff>=1. or eff<0.:
        LOG.warning("BTagWeightTool.getSF: MC efficiency is %.3f <0 or >=1 for untagged jet with pt=%s, eta=%s, flavor=%s, sf=%s"%(eff,pt,eta,flavor,sf))
        return 1.
      else:
        sf = (1.-sf*eff)/(1.-eff)
    return sf
  
  def getEff(self,pt,eta,flavor):
    """Get b tag efficiency for a single jet in MC."""
    flavor = flavorToString(flavor)
    hist   = self.effmaps[flavor]
    xbin   = hist.GetXaxis().FindBin(pt)
    ybin   = hist.GetYaxis().FindBin(eta)
    if xbin==0: xbin = 1
    elif xbin>hist.GetXaxis().GetNbins(): xbin -= 1
    if ybin==0: ybin = 1
    elif ybin>hist.GetYaxis().GetNbins(): ybin -= 1
    eff    = hist.GetBinContent(xbin,ybin)
    ###if eff==1:
    ###  print "Warning! BTagWeightTool.getEff: MC efficiency is 1 for pt=%s, eta=%s, flavor=%s, sf=%s"%(pt,eta,flavor,sf)
    return eff
  
  def fillEffMaps(self,jets,usejec=False,tag=""):
    """Fill histograms to make efficiency map for MC, split by true jet flavor,
    and jet pT and eta. Numerator = b tagged jets; denominator = all jets."""
    for jet in jets:
      jetpt  = jet.pt_nom if usejec else jet.pt
      flavor = flavorToString(jet.partonFlavour)
      if self.tagged(jet):
        self.jetmaps[tag][flavor].Fill(jetpt,jet.eta)
      self.jetmaps[tag][flavor+'_all'].Fill(jetpt,jet.eta)
  
  def setDir(self,directory,subdirname='btag'):
    """Set directory of histograms (efficiency map) before writing."""
    if subdirname:
      subdir = directory.Get(subdirname)
      if not subdir:
        subdir = directory.mkdir(subdirname)
      directory = subdir
    for tag, hists in self.jetmaps.items():
      for hname, hist in hists.items():
        hist.SetDirectory(directory)
  

def flavorToFLAV(flavor):
  """Help function to convert an integer flavor ID to a BTagEntry enum value."""
  return FLAV_B if abs(flavor)==5 else FLAV_C if abs(flavor) in [4,15] else FLAV_UDSG       
  

def flavorToString(flavor):
  """Help function to convert an integer flavor ID to a string value."""
  return 'b' if abs(flavor)==5 else 'c' if abs(flavor)==4 else 'udsg'
  

def getJetMap(hname,maxeta=2.5):
  """Help function to create efficiency maps (TH2D) with uniform binning and layout.
  One method to rule them all."""
  ptbins  = array('d',[10,20,30,50,70,100,140,200,300,500,1000,2000])
  etabins = array('d',[-maxeta,-1.5,0.0,1.5,maxeta])
  bins    = (len(ptbins)-1,ptbins,len(etabins)-1,etabins)
  hist    = TH2F(hname,hname,*bins)
  hist.GetXaxis().SetTitle("Jet p_{T} [GeV]")
  hist.GetYaxis().SetTitle("Jet #eta")
  hist.SetDirectory(0)
  return hist
  

def getDefaultEffMap(hname,flavor,wp='medium'):
  """Create default efficiency histograms. WARNING! Do not use this for analysis! Use it as a placeholder,
  until you have made an efficiency map from MC for you analysis."""
  if   wp=='loose':  eff = 0.75 if flavor=='b' else 0.11 if flavor=='c' else 0.01
  elif wp=='medium': eff = 0.85 if flavor=='b' else 0.42 if flavor=='c' else 0.10
  else:              eff = 0.60 if flavor=='b' else 0.05 if flavor=='c' else 0.001
  hname = hname.split('/')[-1] + "_default"
  hist     = getJetMap(hname)
  for xbin in xrange(0,hist.GetXaxis().GetNbins()+2):
    for ybin in xrange(0,hist.GetYaxis().GetNbins()+2):
      hist.SetBinContent(xbin,ybin,eff)
  return hist
  
