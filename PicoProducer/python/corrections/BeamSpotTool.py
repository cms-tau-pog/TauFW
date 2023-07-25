# Author: Izaak Neutelings (June 2023)
import os
#import numpy as np
from ROOT import TFile, TH1D, TH2D, gRandom
from TauFW.PicoProducer import datadir
pathBS = os.path.join(datadir,"beamspot/")


class BeamSpotTool:
  
  def __init__(self, era='UL2018', loadcorrs=False, createhists=False, verb=0):
    """Load histograms from files."""
    
    # DEFAULT ATTRIBUTES
    self.hists     = { } # for making corrections
    self.outhists  = { } # for filling on the fly and writing
    self.filename  = 'None'
    self.verbosity = verb
    gRandom.SetSeed(137137)
    
    # INPUT HISTOGRAMS for correcting MC
    if loadcorrs:
      # ./getBeamSpotProfiles.py /eos/user/i/ineuteli/analysis/g-2/UL2018/Data/SingleMuon_Run2018*root -o beamspot_UL2018 -v10
      self.filename = pathBS+"beamspot_%s_Data.root"%(era)
      file = TFile.Open(self.filename)
      hnames = [
        'bs_z', 'bs_sigma', 'bs_sigmaErr', #'bs_sigmaUp', 'bs_sigmaDown',
      ]
      for hname in hnames:
        hkey = hname.replace('bs_','').replace('sigma','sig')
        hist = file.Get(hname)
        assert hname, "Could not find %s:%s..."%(self.filename,hname)
        hist.SetDirectory(0)
        self.hists[hkey] = hist
      file.Close()
      print(">>> Loading BeamSpotTool for %s (era=%s)"%(self.filename,era))
    
    # OUTPUT HISTOGRAMS from data, saving for later
    if createhists:
      tit_z      = "Beamspot z [cm]"
      tit_sig    = "Beamspot width [cm]"
      tit_sigErr = "Beamspot width error [cm]"
      tit_sigUp  = "Beamspot width (up) [cm]"
      tit_sigDn  = "Beamspot width (down) [cm]"
      #zedges    = np.concatenate((np.arange(-6,-2,0.2),np.arange(-2,0,0.05),np.arange(0,2,0.05),np.arange(2,6.01,0.2)))
      zbins     = (300,-6,6) # equidistant binning
      #zbins     = (len(zedges)-1,zedges) # variable binning
      sigbins   = (200, 0,8)
      errbins   = (100, 0,0.5) # sigma error
      self.outhists   = {
        'z':          TH1D('bs_z',         '%s;%s;Events'%(tit_z,tit_z),          *zbins),
        'sig':        TH1D('bs_sigma',     '%s;%s;Events'%(tit_sig,tit_sig),      *sigbins),
        'sigErr':     TH1D('bs_sigmaErr',  '%s;%s;Events'%(tit_sigErr,tit_sigErr),*errbins),
        'sigUp':      TH1D('bs_sigmaUp',   '%s;%s;Events'%(tit_sigUp,tit_sigUp),  *sigbins),
        'sigDown':    TH1D('bs_sigmaDown', '%s;%s;Events'%(tit_sigDn,tit_sigDn),  *sigbins),
        'sig_vs_z':   TH2D('bs_sigma_vs_z',';%s;%s;Events'%(tit_z,tit_sig),       *(zbins+sigbins)),
        'err_vs_sig': TH2D('bs_err_vs_sig',';%s;%s;Events'%(tit_sig,tit_sigErr),  *(sigbins+errbins)),
      }
      for hkey in ['sig_vs_z','err_vs_sig']:
        self.outhists[hkey].SetOption('COLZ') # for display in TBrowser
      if self.verbosity>=1:
        print(">>> BeamSpotTool.__init__: Preparing histograms for %s"%(era))
  
  def getZCorr(self,bs_z,bs_zsig):
    """Get correction factors for z position and width of the simulated beamspot
    by sampling the beamspot profile in observed data."""
    # To correct a given z coordinate w.r.t. CMS center (z=0):
    #   z_corr = bs_z_obs + (bs_zsigma_obs / bs_zsigma_mc) * ( z - bs_z_mc )
    #          = bs_z_obs + corr_zsig * ( z - bs_z_mc )
    #          = corr_z + corr_zsig * z
    # with
    #   corr_zsig = (bs_zsigma_obs / bs_zsigma_mc)  # width correction factor
    #   corr_z    = bs_z_obs - corr_zsig * bs_z_mc  # shift correction
    corr_zsig = self.hists['sig'].GetRandom() / bs_zsig
    corr_z    = self.hists['z'].GetRandom() - bs_z * corr_zsig
    return corr_z, corr_zsig
  
  def getZSigmaCorr(self,bs_zsig):
    """Get correction factor for z width of the simulated beamspot
    by sampling the beamspot profile in observed data."""
    return self.hists['sig'].GetRandom() / bs_zsig
  
  def getZSigmaCorrSyst(self,bs_zsig):
    """Get correction factors for z width of the simulated beamspot
    by sampling the beamspot profile in observed data,
    and include systematic variations."""
    sig = self.hists['sig'].GetRandom() # sample from observed BS profile
    err = self.hists['sigErr'].GetRandom()
    return sig/bs_zsig, (sig+err)/bs_zsig, (sig-err)/bs_zsig
  
  def getZCorrSyst(self,bs_z,bs_zsig):
    """Get correction factors for z position and width of the simulated beamspot
    by sampling the beamspot profile in observed data,
    and include systematic variations."""
    z   = self.hists['z'].GetRandom() # sample from observed BS profile
    sig = self.hists['sig'].GetRandom() # sample from observed BS profile
    err = self.hists['sigErr'].GetRandom() # sample from observed BS profile
    corr_zsig   = sig/bs_zsig # BS width correction, nominal
    corr_zsigUp = (sig+err)/bs_zsig # BS width correction, up
    corr_zsigDn = (sig-err)/bs_zsig # BS width correction, down
    return ((z-bs_z*corr_zsig, z-bs_z*corr_zsigUp, z-bs_z*corr_zsigDn),
            (corr_zsig, corr_zsigUp, corr_zsigDn),
            (z, sig, err))
  
  def fillHists(self,event):
    """Fill histograms for later use."""
    self.outhists['z'].Fill(event.beamspot_z0)
    self.outhists['sig'].Fill(event.beamspot_sigmaZ)
    self.outhists['sigErr'].Fill(event.beamspot_sigmaZ0Error)
    self.outhists['sigUp'].Fill(event.beamspot_sigmaZ+event.beamspot_sigmaZ0Error)
    self.outhists['sigDown'].Fill(event.beamspot_sigmaZ-event.beamspot_sigmaZ0Error)
    self.outhists['sig_vs_z'].Fill(event.beamspot_z0,event.beamspot_sigmaZ)
    self.outhists['err_vs_sig'].Fill(event.beamspot_sigmaZ,event.beamspot_sigmaZ0Error)
  
  def setDir(self,directory,subdirname='beamspot'):
    """Set directory (TDirectory, e.g. TFile) of histograms before writing."""
    if self.verbosity>=2:
      print(">>> BeamSpotTool.setDir: Setting histograms directory to for %s/%s"%(
        directory.GetPath().rstrip('/'),subdirname))
    if self.outhists:
      if subdirname:
        subdir = directory.Get(subdirname)
        if not subdir:
          subdir = directory.mkdir(subdirname)
        directory = subdir
      for hkey, hist in self.outhists.items():
        hist.SetDirectory(directory)
    return directory
  
