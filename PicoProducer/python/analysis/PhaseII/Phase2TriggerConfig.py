# Author: Neeraj (June 2026)
# Description: Central configuration for Phase-II HLT trigger efficiency studies.
#              Defines channel selections, trigger paths, L1 seeds, and binning.
#
# Key convention (Phase-II vs Run-3):
#   Run-3:   L1_DoubleIsoTau32      — 32 is the L1-level pT cut
#   Phase-2: L1_DoublePuppiTau52    — 52 is the offline pT at 90% efficiency plateau
import numpy as np
from math import pi


# ─── Channel Configurations ────────────────────────────────────────────────
# Each channel defines the HLT path, L1 seed, gen/reco selection cuts,
# separation and matching dR requirements.

CHANNELS = {

  'mutau': {
    'hlt_path': 'HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1',
    'l1_seed':  'L1T_PuppiTauTkMuon_42_18',
    # Gen selection
    'gen_tau_pt':  27.0,  'gen_tau_eta': 2.1,   # GenVisTau: exactly 1
    'gen_mu_pt':   20.0,  'gen_mu_eta':  2.1,   # GenPart |pdgId|=13, status=1: exactly 1
    # Reco selection (HLT objects)
    'reco_tau_pt': 27.0,  'reco_tau_eta': 2.1,  # hltHpsPFTau: highest pT
    'reco_mu_pt':  20.0,  'reco_mu_eta':  2.1,  # hltMuon: highest pT
    # Matching
    'dr_separation': 0.5,  # dR(tau, muon) > 0.5
    'dr_match':      0.1,  # dR(gen, reco) < 0.1
    # Object collections
    'reco_tau_collection': 'hltHpsPFTau',
    'reco_lep_collection': 'hltMuon',
    'gen_lep_pdgid': 13,  # muon
  },

  'ditau': {
    'hlt_path': 'HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1',
    'l1_seed':  'L1T_DoublePuppiTau_52_52',
    # Gen selection
    'gen_tau_pt':  35.0,  'gen_tau_eta': 2.1,   # GenVisTau: exactly 2
    # Reco selection
    'reco_tau_pt': 35.0,  'reco_tau_eta': 2.1,  # hltHpsPFTau: 2 highest pT
    # Matching
    'dr_separation': 0.5,  # dR(tau1, tau2) > 0.5
    'dr_match':      0.1,
    # Object collections
    'reco_tau_collection': 'hltHpsPFTau',
  },

  'etau': {
    'hlt_path': 'HLT_Ele30_WPTight_L1Seeded_LooseDeepTauPFTauHPS30_eta2p1_CrossL1',
    'l1_seed':  'L1T_PuppiTauTkIsoEle_45_22',
    # Gen selection
    'gen_tau_pt':  30.0,  'gen_tau_eta': 2.1,   # GenVisTau: exactly 1
    'gen_ele_pt':  30.0,  'gen_ele_eta': 2.1,   # GenPart |pdgId|=11: exactly 1
    # Reco selection
    'reco_tau_pt': 30.0,  'reco_tau_eta': 2.1,
    'reco_ele_pt': 30.0,  'reco_ele_eta': 2.1,
    # Matching
    'dr_separation': 0.5,
    'dr_match':      0.1,
    # Object collections
    'reco_tau_collection': 'hltHpsPFTau',
    'reco_lep_collection': 'hltElectron',
    'gen_lep_pdgid': 11,  # electron
  },

  'singletau': {
    'hlt_path': None,  # not yet in menu
    'l1_seed':  None,  # not yet in menu
    # Gen selection
    'gen_tau_pt':  130.0,  'gen_tau_eta': 2.1,  # GenVisTau: exactly 1
    # Reco selection
    'reco_tau_pt': 130.0,  'reco_tau_eta': 2.1,
    # Matching
    'dr_match':      0.1,
    'dr_separation': 0.0,  # N/A for single tau (no second leg)
    # Object collections
    'reco_tau_collection': 'hltHpsPFTau',
  },

}


# ─── All L1 Seeds to Monitor ───────────────────────────────────────────────
# Derived from CHANNELS to avoid duplication; extra seeds added separately.
# These are stored for every event regardless of channel, to allow
# cross-channel L1 seed rate comparisons.

L1_SEEDS = {f'l1_{ch}': cfg['l1_seed']
            for ch, cfg in CHANNELS.items() if cfg.get('l1_seed')}
L1_SEEDS['l1_taumet']   = 'L1T_NNPuppiTauPuppiMet_55_190'
L1_SEEDS['l1_singlemu'] = 'L1T_SingleTkMuon_22'


# ─── All HLT Paths to Monitor ──────────────────────────────────────────────
# Derived from CHANNELS to avoid duplication.

HLT_PATHS = {f'hlt_{ch}': cfg['hlt_path']
             for ch, cfg in CHANNELS.items() if cfg.get('hlt_path')}


# ─── Binning for Efficiency Plots ──────────────────────────────────────────

PT_BINS  = np.array([0, 20, 25, 27, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 125, 200], dtype=float)
ETA_BINS = np.linspace(-2.5, 2.5, 11)
PHI_BINS = np.linspace(-pi, pi, 11)
