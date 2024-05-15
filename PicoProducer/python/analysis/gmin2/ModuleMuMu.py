# Author: Izaak Neutelings (May 2023)
# Description: Simple module to pre-select mumu events for g-2
# Sources:
#   https://github.com/cecilecaillol/NanoAODreprocessing/tree/master
#   https://github.com/cecilecaillol/MyNanoAnalyzer/blob/master/TauG2/python/objectSelector.py
import sys
from math import floor, ceil
from TauFW.PicoProducer.analysis.gmin2.TreeProducerMuMu import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonPair, idIso, matchtaujet, deltaPhi
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.BeamSpotTool import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
#from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool
from ROOT import gSystem
corrpath = "/afs/cern.ch/user/i/ineuteli/analysis/CMSSW_12_4_8_g-2/src/TauFW/Plotter/python/corrections/g-2"


def countTracksInWindow(z_track,z_dilep,branch):
  """Help function to count tracks in windows of 0.1 cm along z axis between -10 < z < 10 cm"""
  # Mapping of index, e.g.
  #     -1: -10.00
  #      0:  -9.99, -9.95, -9.91, -9.90
  #      1:  -9.89, -9.85, -9.81, -9.80
  #     99:  -0.09, -0.05, -0.01,  0.00
  #    100:   0.01,  0.05,  0.09,  0.10
  #    198:   9.81,  9.85,  9.89,  9.00
  #    199:   9.91,  9.95,  9.99, 10.00
  # Check mapping in python:
  #   from math import ceil, floor
  #   for i in range(-1,202):
  #     print(f"i={i}")
  #     for z0 in [-10.1,-10.09,-10.05,-10.01,-10.00]:
  #       z = z0+i*0.1 # beware binary representation errors
  #       #print(f"{z:23.18f} -> {floor(10*z)/10:23.18f} -> {int(ceil(10*(10+z)))-1:3d}")
  #       print(f"{z:6.2f} -> {floor(10*z)/10:6.2f} -> {int(ceil(10*(10+z)))-1:3d}")
  if -10<=z_track<10:
    zlow = floor(10*z_track)/10 # lower edge of track's 0.1 window
    zup  = zlow+0.1             # upper edge of track's 0.1 window
    if abs(zlow-z_dilep)>1.0 and abs(zup-z_dilep)>1.0: # window at least 1.0 cm from dilep vertex
      #if matchHS:
      #  print(">>> WARNING! countTracksInWindow: Found track with isMatchedToGenHS==True: z_dilep=%.4f, z_track=%.4f..."%(z_dilep,z_track))
      idx = int(ceil(10*(10+z_track)))-1 # map z -> window index [0-199]
      branch[idx] = min(60,branch[idx]+1)
      ###print(">>> count_tracks_in_window: z_track_corr=%7.4f -> zlow=%7.4 -> idx=%3d"%(z_track_corr,zlow,idx))
  

class ModuleMuMu(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mumu'
    kwargs['jec']     = False
    kwargs['useT1']   = False
    compress          = kwargs['compress'] or 'LZMA:9'
    super(ModuleMuMu,self).__init__(fname,**kwargs)
    self.out     = TreeProducerMuMu(fname,self,compress=compress)
    self.zwindow = kwargs.get('zwindow', False ) # stay between 70 and 110 GeV
    
    # TRIGGERS
    if self.year==2016:
      #self.trigger    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoTkMu24
      self.muon1CutPt = 26
      #self.muon1CutPt = lambda e: 26
      #self.muonCutEta = lambda e: 2.4 #if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
    elif self.year==2017:
      #self.trigger    = lambda e: e.HLT_IsoMu27
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt = 29
      #self.muon1CutPt = lambda e: 26 if e.HLT_IsoMu24 else 29
      #self.muonCutEta = lambda e: 2.4
    else:
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt = 26
      #self.muon1CutPt = lambda e: 26
      #self.muonCutEta = lambda e: 2.4
    self.muonCutEta = 2.4
    self.muon2CutPt = 10
    
    # CORRECTIONS
    self.beamspotTool = BeamSpotTool(era=self.era,loadcorrs=self.ismc,createhists=True,verb=10)
    if self.ismc:
      self.muSFs = MuonSFs(era=self.era,flags=['HLT_IsoMu27'])
      
      # PU TRACK CORRECTIONS
      print(">>> Loading PU & HS track corrections...")
      #gROOT.ProcessLine(".L python/corrections/g-2/corrs_ntracks.C+O")
      #gROOT.ProcessLine(".L python/corrections/g-2/aco.C+O")
      gSystem.Load(corrpath+"/corrs_ntracks_C.so") # faster than compiling
      print(">>> Loading acoplanarity corrections...")
      gSystem.Load(corrpath+"/aco_C.so") # faster than compiling
      from ROOT import loadPUTrackWeights, loadHSTrackWeights, loadAcoWeights, getEraIndex,\
                       getPUTrackWeight, getHSTrackWeight, getAcoWeight
      loadPUTrackWeights(self.era,1)
      loadHSTrackWeights(self.era,1)
      loadAcoWeights(self.era,1)
      self.getPUTrackWeight = getPUTrackWeight
      self.getHSTrackWeight = getHSTrackWeight
      self.getAcoWeight     = getAcoWeight
      self.iera = getEraIndex(self.era)
      print(">>> Done loading corrections! Got iera=%s"%(self.iera))
    
    # TRIGGERS
    jsonfile = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    trigger = 'SingleMuon_Mu24' if self.year==2016 else 'SingleMuon_Mu27' if self.year==2017 else 'SingleMuon'
    self.trigger = TrigObjMatcher(jsonfile,trigger=trigger,isdata=self.isdata)
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('pair',         "pair"                       )
    self.out.cutflow.addcut('leadTrig',     "leading muon triggered"     ) # ADDED FOR SF CROSS CHECKS!
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleMuMu,self).beginJob()
    print(">>> %-12s = %s"%('muon1CutPt', self.muon1CutPt))
    print(">>> %-12s = %s"%('muon2CutPt', self.muon2CutPt))
    print(">>> %-12s = %s"%('muonCutEta', self.muonCutEta))
    print(">>> %-12s = %s"%('zwindow',    self.zwindow))
    print(">>> %-12s = %s"%('trigger',    self.trigger))
    
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    super(ModuleMuMu,self).beginJob()
    self.beamspotTool.setDir(self.out.outfile)
    bs_z, bs_sig = self.beamspotTool.outhists['z'].GetMean(), self.beamspotTool.outhists['sig'].GetMean()
    if not self.isdata:
      self.out.setAlias('bs_z_raw',    "0+%s"%bs_z) # "0.02488"
      self.out.setAlias('bs_sigma_raw',"0+%s"%bs_sig) # "3.5"
    print(">>> Beam spot z=%.4g, z_sigma=%.4g"%(bs_z,bs_sig))
    self.out.endJob()
    
  
  def fillTrackBranches(self, event, lep1, lep2):
    # https://github.com/cecilecaillol/MyNanoAnalyzer/blob/master/TauG2/python/TauG2_analysis.py#L269
    # https://github.com/cecilecaillol/MyNanoAnalyzer/blob/master/NtupleAnalyzerCecile/FinalSelection_mumu.cc#L663-L837
    
    # BEAMSPOT
    self.out.pv_z[0] = event.PV_z # do not correct HS / PV
    if self.ismc:
      (corr_z, corr_zUp, corr_zDn),\
        (corr_zsig, corr_zsigUp, corr_zsigDn),\
        (bs_z, bs_sig, bs_sigErr) = self.beamspotTool.getZCorrSyst(event.beamspot_z0,event.beamspot_sigmaZ) # corr. factor
      self.out.bs_z[0]        = bs_z #corr_z+event.beamspot_z0
      self.out.bs_sigma[0]    = bs_sig #corr_zsig*event.beamspot_sigmaZ
      self.out.bs_sigmaErr[0] = bs_sigErr #(corr_zsigUp-corr_zsig)*event.beamspot_sigmaZ # reconstruct sampled uncertainty from up variation
    else:
      corr_z                  = 0. # z offset correction
      corr_zUp                = 0. # z offset correction, up
      corr_zDn                = 0. # z offset correction, down
      corr_zsig               = 1. # z width correction
      corr_zsigUp             = 1. # z width correction, up
      corr_zsigDn             = 1. # z width correction, down
      self.out.bs_z[0]        = event.beamspot_z0
      self.out.bs_sigma[0]    = event.beamspot_sigmaZ
      self.out.bs_sigmaErr[0] = event.beamspot_sigmaZ0Error
    m_dilep    = (lep1.p4()+lep2.p4()).M()
    dz_dilep   = (lep1.dz+lep2.dz)/2 # dilepton dz w.r.t. PV
    z_dilep    = event.PV_z+dz_dilep # dilepton z
    dz_sig_cut = 0.05 # 0.1 cm signal window around dilep: dz < 0.05 cm = 0.5 mm
    #dz_cut     = 0.5  # cut for storing tracks: 0.5 cm = 5 mm
    #dz_cut     = 2.5 if self.ismc else 0.5 # need wider window in dz in MC because of the BS correction
    i_low      = max(  0,int(ceil(10*( 9+z_dilep)))-1) # index of leftmost 0.1 window within 1 cm from z_dilep
    i_up       = min(199,int(ceil(10*(11+z_dilep)))-1) # index of rightmost 0.1 window within 1 cm from z_dilep
    isOS       = lep1.charge*lep2.charge<0 # boolean: is opposite sign
    isZmass    = abs(m_dilep-91.1876)<15 # boolean: falls inside mass window
    
    # SELECT & COUNT TRACKS
    #print('-'*80) # for debugging
    tracks           = [ ]
    chargedPF        = Collection(event,'ChargedPFCandidates')
    ntrack_1         = 0 # number of tracks matched to leading lepton
    ntrack_2         = 0 # number of tracks matched to subleading lepton
    ntrack_all       = 0 # number of tracks in signal window from hard scattering
    ntrack_hs        = 0 # number of tracks in signal window from hard scattering
    ntrack_pu_corr   = 0 # number of tracks in signal window from PU
    ntrack_pu_corrUp = 0 # number of tracks in signal window from PU, up
    ntrack_pu_corrDn = 0 # number of tracks in signal window from PU, down
    ntrack_pu_raw    = 0 # number of tracks in signal window from PU
    for i in range(len(self.out.ntrack_pu_0p1)):
      self.out.ntrack_pu_0p1[i] = 0 # reset count to 0
    if self.ismc:
      for i in range(len(self.out.ntrack_pu_0p1_raw)):
        self.out.ntrack_pu_0p1Up[i]   = 0 # reset count to 0, up
        self.out.ntrack_pu_0p1Down[i] = 0 # reset count to 0, down
        self.out.ntrack_pu_0p1_raw[i] = 0 # reset count to 0
    
    # LOOP over TRACKS
    for track in chargedPF:
      if abs(track.eta)>=2.5: continue # track abs(eta) < 2.5
      if track.pt<=0.5: continue       # track pt > 0.5 GeV
      
      # CORRECT BEAM SPOT
      z_track_raw         = event.PV_z+track.dz              # uncorrected track z
      z_track_corr        = corr_z  +corr_zsig*z_track_raw   #   corrected track z
      z_track_corrUp      = corr_zUp+corr_zsigUp*z_track_raw #   corrected track z, up
      z_track_corrDn      = corr_zDn+corr_zsigDn*z_track_raw #   corrected track z, down
      dz_track_corr       = z_track_corr-event.PV_z          #   corrected track dz
      dz_track_dilep_raw  = abs(track.dz-dz_dilep)           # uncorrected dz between track & dilepton vertex
      dz_track_dilep_corr = abs(dz_track_corr-dz_dilep)      #   corrected dz between track & dilepton vertex
      #print(f"dz_track_dilep_raw={dz_track_dilep_raw}, dz_track_dilep_corr={dz_track_dilep_corr}")
      
      # MATCH TRACK with selected leptons
      match_1 = False
      match_2 = False
      dR_1    = track.DeltaR(lep1)
      dR_2    = track.DeltaR(lep2)
      if abs(track.dz-lep1.dz)<0.1 and abs(track.pt-lep1.pt)/lep1.pt<0.2 and dR_1<0.05:
        match_1 = True
        ntrack_1 += 1
      if abs(track.dz-lep2.dz)<0.1 and abs(track.pt-lep2.pt)/lep2.pt<0.2 and dR_2<0.05:
        match_2 = True
        ntrack_2 += 1
      if match_1 and match_2:
        print("WARNING! Track matched to both leptons! "
              "track pt=%.3f, pt_1=%.3f, pt_2=%.3f, dR_1=%.3f, dR_2=%.3f"%(
              track.pt,lep1.pt,lep2.pt,dR_1,dR_2))
      
      # COUNT TRACKS in the 0.10 cm signal window; abs(dz_track-dz_dilep) < 0.05 cm = 0.5 mm
      if not (match_1 or match_2):
        if self.ismc: # MC simulation
          if track.isMatchedToGenHS and dz_track_dilep_raw<dz_sig_cut: # hard scattering / signal window
            ntrack_hs += 1
            if isZmass and isOS: # store track
              tracks.append(track)
          elif not track.isMatchedToGenHS: # from PU
            dz_track_corrUp       = z_track_corrUp-event.PV_z     # BS-corrected track dz, up
            dz_track_corrDn       = z_track_corrDn-event.PV_z     # BS-corrected track dz, down
            dz_track_dilep_corrUp = abs(dz_track_corrUp-dz_dilep) # BS-corrected dz between track & dilepton vertex, up
            dz_track_dilep_corrDn = abs(dz_track_corrDn-dz_dilep) # BS-corrected dz between track & dilepton vertex, down
            if dz_track_dilep_raw<dz_sig_cut: # uncorrected
              ntrack_pu_raw += 1
            if dz_track_dilep_corr<dz_sig_cut: # BS-corrected
              ntrack_pu_corr += 1
              if isZmass and isOS: # store track
                tracks.append(track)
            if dz_track_dilep_corrUp<dz_sig_cut: # BS-corrected, up
              ntrack_pu_corrUp += 1
            if dz_track_dilep_corrDn<dz_sig_cut: # BS-corrected, down
              ntrack_pu_corrDn += 1
        elif dz_track_dilep_raw<dz_sig_cut: # observed data
          ntrack_pu_raw  += 1 # assume PU
          ntrack_pu_corr += 1
          if isZmass and isOS: # store track
            tracks.append(track)
      
      # COUNT TRACKS in windows of 0.1 cm along z axis between -10 < z < 10 cm
      if isZmass and isOS: # only look inside Z mass window and OS events to save processing time
        ###if -10<z_track_corr<=10:
        ###  zlow = floor(10*z_track_corr)/10 # lower edge of track's 0.1 window
        ###  if abs(zlow-z_dilep)>1.0 and abs(zlow+0.1-z_dilep)>1.0: # window at least 1.0 cm from dilep vertex
        ###    idx = int(ceil(10*(10+z_track_corr)))-1 # map z -> window index [0-199]
        ###    self.out.ntrack_pu_0p1[idx] = min(250,self.out.ntrack_pu_0p1[idx]+1)
        ###    ###print(">>> fillTrackBranches: z_track_corr=%7.4f -> zlow=%7.4 -> idx=%3d"%(z_track_corr,zlow,idx))
        ###if self.ismc:
        ###  if -10<z_track_corrUp<=10: # UP VARIATION
        ###    zlow = floor(10*z_track_corrUp)/10 # lower edge of track's 0.1 window
        ###    if abs(zlow-z_dilep)>1.0 and abs(zlow+0.1-z_dilep)>1.0: # window at least 1.0 cm from dilep vertex
        ###      idx = int(ceil(10*(10+z_track_corrUp)))-1 # map z -> window index [0-199]
        ###      self.out.ntrack_pu_0p1Up[idx] = min(250,self.out.ntrack_pu_0p1Up[idx]+1)
        ###      ###print(">>> fillTrackBranches: z_track_corrUp=%7.4f -> zlow=%7.4 -> idx=%3d"%(z_track_corrUp,zlow,idx))
        ###  if -10<z_track_corrDn<=10: # DOWN VARIATION
        ###    zlow = floor(10*z_track_corrDn)/10 # lower edge of track's 0.1 window
        ###    if abs(zlow-z_dilep)>1.0 and abs(zlow+0.1-z_dilep)>1.0: # window at least 1.0 cm from dilep vertex
        ###      idx = int(ceil(10*(10+z_track_corrDn)))-1 # map z -> window index [0-199]
        ###      self.out.ntrack_pu_0p1Down[idx] = min(250,self.out.ntrack_pu_0p1Down[idx]+1)
        ###      ###print(">>> fillTrackBranches: z_track_corrDn=%7.4f -> zlow=%7.4 -> idx=%3d"%(z_track_corrDn,zlow,idx))
        ###  if -10<z_track_raw<=10: # RAW (NO CORRECTION)
        ###    zlow = floor(10*z_track_raw)/10 # lower edge of track's 0.1 window
        ###    if abs(zlow-z_dilep)>1.0 and abs(zlow+0.1-z_dilep)>1.0: # window at least 1.0 cm from dilep vertex
        ###      idx = int(ceil(10*(10+z_track_raw)))-1 # map z -> window index [0-199]
        ###      self.out.ntrack_pu_0p1_raw[idx] = min(250,self.out.ntrack_pu_0p1_raw[idx]+1)
        ###      ###print(">>> fillTrackBranches: z_track_raw =%7.4f -> zlow=%7.4 -> idx=%3d"%(z_track_raw,zlow,idx))
        countTracksInWindow(z_track_corr,z_dilep,self.out.ntrack_pu_0p1)
        if self.ismc:
          countTracksInWindow(z_track_corrUp,z_dilep,self.out.ntrack_pu_0p1Up) # UP VARIATION
          countTracksInWindow(z_track_corrDn,z_dilep,self.out.ntrack_pu_0p1Down) # DOWN VARIATION
          countTracksInWindow(z_track_raw,   z_dilep,self.out.ntrack_pu_0p1_raw) # RAW (NO CORRECTION)
      
      #### STORE
      ####if isZmass and isOS and not (match_1 or match_2) and dz_track_dilep_corr<dz_sig_cut: # to save disk space
      ###if isZmass and isOS and not (match_1 or match_2): #and dz_track_dilep_raw<dz_sig_cut: # to save disk space
      ###  if self.ismc:
      ###    if track.isMatchedToGenHS and dz_track_dilep_raw<dz_sig_cut:
      ###      tracks.append(track)
      ###    elif not track.isMatchedToGenHS and dz_track_dilep_corr<dz_sig_cut:
      ###      tracks.append(track)
      ###  elif dz_track_dilep_raw<dz_sig_cut: # observed data
      ###      tracks.append(track)
      ###if dz_track_dilep<dz_cut or dz_track_dilep_corr<dz_cut: # store for further analysis
      ###  track.dR_1 = dR_1
      ###  track.dR_2 = dR_2
      ###  tracks.append(track)
      ###elif match_1 or match_2:
      ###  print("WARNING! Track matched to selected leptons fails vertex dz cut: "
      ###        "track dz=%.2f, vertex dz=%.2f, dz_1=%.2f, dz_2=%.2f, dzcut=%.2f"%(
      ###         track.dz,dz_dilep,lep1.dz,lep2.dz,dz_cut))
    
    # SET DEFAULT NTRACK for 0.1 cm windows overlapping with 2 cm window around z_dilep
    #print("i_low=%s, i_up=%s, i_up-i_low=%s"%(i_low,i_up,i_up-i_low))
    #if -9<z_dilep<9 and i_up-i_low!=20: # sanity check: ignore 20 windows
    #  print(">>> WARNING! fillTrackBranches: excluded windows have indices i_up-i_low=%s != 20 windows for z_dilep=%.4g (i_low,i_up)=(%s,%s)..."%(i_up-i_low,z_dilepi_low,i_up))
    for i in range(i_low,i_up+1): # loop over excluded windows
      if self.out.ntrack_pu_0p1[i]>0: # sanity check for bugs / rounding errors
        print(">>> WARNING! fillTrackBranches: Excluded window has ntrack_pu_0p1[%s]=%s>0 tracks for z_dilep=%.4g..."%(i,self.out.ntrack_pu_0p1[i],z_dilep))
      self.out.ntrack_pu_0p1[i] = 250 # default int8 value (outside typical plotting range)
      if self.ismc:
        if self.out.ntrack_pu_0p1Up[i]>0: # sanity check
          print(">>> WARNING! fillTrackBranches: Excluded window has ntrack_pu_0p1Up[%s]=%s>0 tracks for z_dilep=%.4g..."%(i,self.out.ntrack_pu_0p1Up[i],z_dilep))
        if self.out.ntrack_pu_0p1Down[i]>0: # sanity check
          print(">>> WARNING! fillTrackBranches: Excluded window has ntrack_pu_0p1Down[%s]=%s>0 tracks for z_dilep=%.4g..."%(i,self.out.ntrack_pu_0p1Down[i],z_dilep))
        if self.out.ntrack_pu_0p1_raw[i]>0: # sanity check
          print(">>> WARNING! fillTrackBranches: Excluded window has ntrack_pu_0p1_raw[%s]=%s>0 tracks for z_dilep=%.4g..."%(i,self.out.ntrack_pu_0p1_raw[i],z_dilep))
        self.out.ntrack_pu_0p1Up[i]   = 250
        self.out.ntrack_pu_0p1Down[i] = 250
        self.out.ntrack_pu_0p1_raw[i] = 250
    
    # FILL BRANCHES
    self.out.ntrack_1[0]           = ntrack_1
    self.out.ntrack_2[0]           = ntrack_2
    self.out.ntrack_hs[0]          = ntrack_hs
    self.out.ntrack_pu[0]          = ntrack_pu_corr
    self.out.ntrack_pu_raw[0]      = ntrack_pu_raw
    if self.ismc:
      self.out.ntrack_puUp[0]      = ntrack_pu_corrUp
      self.out.ntrack_puDown[0]    = ntrack_pu_corrDn
    
    # FILL TRACK BRANCHES
    #print(">>> len(tracks) = %s"%(len(tracks)))
    nmax = len(self.out.track_pt)
    tracks.sort(key=lambda t: t.pt, reverse=True) # sort from high to low pT
    if len(tracks)>nmax:
      #print(">>> fillTrackBranches: #(selected tracks) = %d > %d"%(len(tracks),nmax))
      #tracks.sort(key=lambda t: abs(t.dz-dz_dilep)) # sort from small to large dz
      tracks = tracks[:nmax] # save only first nmax elements
    self.out.ntrack[0] = len(tracks)
    for i, track in enumerate(tracks): # takes way too much space!
      #print(">>> i=%3d, pt=%6.1f, eta=%6.1f"%(i,track.pt,track.eta))
      #if i>=nmax: continue
      self.out.track_pt[i]     = track.pt
      ###self.out.track_eta[i]    = track.eta
      ####self.out.track_phi[i]   = track.phi
      ###self.out.track_dR_1[i]   = track.dR_1
      ###self.out.track_dR_2[i]   = track.dR_2
      ###self.out.track_dz[i]     = track.dz
      ###self.out.track_dxy[i]    = track.dxy
      ###self.out.track_charge[i] = track.charge
      self.out.track_ishs[i]   = track.isMatchedToGenHS and abs(track.dz-dz_dilep)<dz_sig_cut
      ###self.out.track_lostInnerHits[i]   = track.lostInnerHits
      ###self.out.track_trackHighPurity[i] = track.trackHighPurity
    
    ###return tracks
    
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    
    ##### NO CUT #####################################
    if not self.fillhists(event):
      return False
    self.beamspotTool.fillHists(event)
    
    
    ##### TRIGGER ####################################
    #if not self.trigger(event):
    if not self.trigger.fired(event):
      return False
    self.out.cutflow.fill('trig')
    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<self.muon2CutPt: continue # lower pt cut
      if abs(muon.eta)>self.muonCutEta: continue
      ###if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      #if muon.pfRelIso04_all>0.50: continue # relaxed for background estimation
      if muon.pfRelIso04_all>0.15: continue
      muons.append(muon)
    if len(muons)==0:
      return False
    self.out.cutflow.fill('muon')
    
    
    ##### MUMU PAIR #################################
    dileps = [ ]
    #ptcut  = self.muon1CutPt(event) # trigger dependent
    for i, muon1 in enumerate(muons,1):
      for muon2 in muons[i:]:
        if muon2.DeltaR(muon1)<0.5: continue
        if muon1.pt<self.muon1CutPt and muon2.pt<self.muon1CutPt: continue # larger pt cut
        if abs(muon1.dz-muon2.dz)>0.2: continue
        if self.zwindow and not (70<(muon1.p4()+muon2.p4()).M()<110): continue # Z mass
        ltau = LeptonPair(muon1,muon1.pfRelIso04_all,muon2,muon2.pfRelIso04_all)
        dileps.append(ltau)
    if len(dileps)==0:
      return False
    muon1, muon2 = max(dileps).pair
    muon1.tlv    = muon1.p4()
    muon2.tlv    = muon2.p4()
    self.out.cutflow.fill('pair')
    
    #### Only keep events with leading muon triggered
    ###if not self.trigger.match(event,muon1): 
    ###  return False
    ###self.out.cutflow.fill('leadTrig')
    
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[ ],[muon1,muon2],[ ],self.channel, era=self.era)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = extramuon_veto, extraelec_veto, dilepton_veto
    self.out.lepton_vetoes[0]       = extramuon_veto or extraelec_veto or dilepton_veto
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    if self.ismc:
      self.out.pv_z_gen[0] = event.GenVtx_z
    
    # MUON 1
    self.out.pt_1[0]       = muon1.pt
    self.out.eta_1[0]      = muon1.eta
    self.out.phi_1[0]      = muon1.phi
    #self.out.m_1[0]        = muon1.mass
    #self.out.y_1[0]        = muon1.tlv.Rapidity()
    self.out.dxy_1[0]      = muon1.dxy
    self.out.dz_1[0]       = muon1.dz
    self.out.q_1[0]        = muon1.charge
    self.out.iso_1[0]      = muon1.pfRelIso04_all # relative isolation
    #self.out.tkRelIso_1[0] = muon1.tkRelIso
    #self.out.idMedium_1[0] = muon1.mediumId
    #self.out.idTight_1[0]  = muon1.tightId
    #self.out.idHighPt_1[0] = muon1.highPtId
    
    
    # MUON 2
    self.out.pt_2[0]       = muon2.pt
    self.out.eta_2[0]      = muon2.eta
    self.out.phi_2[0]      = muon2.phi
    #self.out.m_2[0]        = muon2.mass
    #self.out.y_2[0]        = muon2.tlv.Rapidity()
    self.out.dxy_2[0]      = muon2.dxy
    self.out.dz_2[0]       = muon2.dz
    self.out.q_2[0]        = muon2.charge
    self.out.iso_2[0]      = muon2.pfRelIso04_all # relative isolation
    #self.out.tkRelIso_2[0] = muon2.tkRelIso
    #self.out.idMedium_2[0] = muon2.mediumId
    #self.out.idTight_2[0]  = muon2.tightId
    #self.out.idHighPt_2[0] = muon2.highPtId
    
    
    # TRACKS & BEAM SPOT
    self.fillTrackBranches(event,muon1,muon2)
    
    
    ## GENERATOR
    #if self.ismc:
    #  self.out.genmatch_1[0] = muon1.genPartFlav
    #  self.out.genmatch_2[0] = muon2.genPartFlav
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,muon1,muon2)
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if muon1.pfRelIso04_all<0.50 and muon2.pfRelIso04_all<0.50:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # MUON WEIGHTS
      self.out.trigweight[0]    = self.muSFs.getTriggerSF(muon1.pt,muon1.eta) # assume leading muon was triggered on
      self.out.idisoweight_1[0] = self.muSFs.getIdIsoSF(muon1.pt,muon1.eta)
      self.out.idisoweight_2[0] = self.muSFs.getIdIsoSF(muon2.pt,muon2.eta)
      
      # CORRECTIONS g-2
      aco     = (1-abs(deltaPhi(muon1.phi,muon2.phi))/3.14159265)
      z_dilep = event.PV_z+0.5*muon1.dz+0.5*muon2.dz
      self.out.putrackweight[0] = self.getPUTrackWeight(int(self.out.ntrack_pu[0]),z_dilep,self.iera)
      self.out.hstrackweight[0] = self.getHSTrackWeight(int(self.out.ntrack_hs[0]),aco,self.iera)
      self.out.acoweight[0]     = self.getAcoWeight(aco,muon1.pt,muon2.pt,self.iera)
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,muon1,muon2,met,met_vars)
    
    
    self.out.fill()
    return True
    
