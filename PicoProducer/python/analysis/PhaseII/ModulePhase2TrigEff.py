# Author: Neeraj (June 2026)
# Description: Unified Phase-II HLT trigger efficiency skimming module.
#   Saves all gen-level and HLT reco objects + trigger decisions in a flat
#   tree. Channel-specific selections (MuTau, DiTau, ETau, SingleTau) are
#   applied at the plotting stage, NOT here.
#
# Usage:
#   pico.py channel phase2_trigeff PhaseII.ModulePhase2TrigEff
#
import sys
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer
from TauFW.PicoProducer.analysis.utils import deltaR
from TauFW.PicoProducer.analysis.PhaseII.Phase2TriggerConfig import L1_SEEDS, HLT_PATHS


class ModulePhase2TrigEff(Module):
  """Unified Phase-II trigger efficiency skimmer.

  Saves all gen and HLT-reco objects with a loose |eta| < 2.5 preselection.
  NO channel-specific pT or dR cuts are applied — those are done in the plotter.
  """

  def __init__(self, fname, **kwargs):
    self.out  = TreeProducer(fname, self)
    self.verb = kwargs.get('verb', 0)

    # ─── Event info ─────────────────────────────────────────────────
    self.out.addBranch('evt',  'l')
    self.out.addBranch('run',  'i')
    self.out.addBranch('lumi', 'i')

    # ─── Trigger decisions ──────────────────────────────────────────
    for name in HLT_PATHS:
      self.out.addBranch(name, '?')
    for name in L1_SEEDS:
      self.out.addBranch(name, '?')

    # ─── Gen taus (from GenVisTau, sorted by pT) ───────────────────
    self.out.addBranch('n_gen_tau',      'i',  0 )
    self.out.addBranch('gen_tau1_pt',    'f', -1.)
    self.out.addBranch('gen_tau1_eta',   'f', -9.)
    self.out.addBranch('gen_tau1_phi',   'f', -9.)
    self.out.addBranch('gen_tau2_pt',    'f', -1.)
    self.out.addBranch('gen_tau2_eta',   'f', -9.)
    self.out.addBranch('gen_tau2_phi',   'f', -9.)

    # ─── Gen muons (from GenPart, |pdgId|=13, status=1) ───────────
    self.out.addBranch('n_gen_mu',      'i',  0 )
    self.out.addBranch('gen_mu1_pt',    'f', -1.)
    self.out.addBranch('gen_mu1_eta',   'f', -9.)
    self.out.addBranch('gen_mu1_phi',   'f', -9.)

    # ─── Gen electrons (from GenPart, |pdgId|=11, status=1) ───────
    self.out.addBranch('n_gen_ele',     'i',  0 )
    self.out.addBranch('gen_ele1_pt',   'f', -1.)
    self.out.addBranch('gen_ele1_eta',  'f', -9.)
    self.out.addBranch('gen_ele1_phi',  'f', -9.)

    # ─── Reco HLT taus (from hltHpsPFTau, sorted by pT) ───────────
    self.out.addBranch('n_reco_tau',     'i',  0 )
    self.out.addBranch('reco_tau1_pt',   'f', -1.)
    self.out.addBranch('reco_tau1_eta',  'f', -9.)
    self.out.addBranch('reco_tau1_phi',  'f', -9.)
    self.out.addBranch('reco_tau2_pt',   'f', -1.)
    self.out.addBranch('reco_tau2_eta',  'f', -9.)
    self.out.addBranch('reco_tau2_phi',  'f', -9.)

    # ─── Reco HLT muons (from hltMuon, sorted by pT) ──────────────
    self.out.addBranch('n_reco_mu',     'i',  0 )
    self.out.addBranch('reco_mu1_pt',   'f', -1.)
    self.out.addBranch('reco_mu1_eta',  'f', -9.)
    self.out.addBranch('reco_mu1_phi',  'f', -9.)

    # ─── Reco HLT electrons (from hltElectron, sorted by pT) ──────
    self.out.addBranch('n_reco_ele',     'i',  0 )
    self.out.addBranch('reco_ele1_pt',   'f', -1.)
    self.out.addBranch('reco_ele1_eta',  'f', -9.)
    self.out.addBranch('reco_ele1_phi',  'f', -9.)

    # ─── Precomputed dR values (convenience for plotter) ───────────
    self.out.addBranch('dr_gen_tau1_mu1',      'f', -1.)  # gen tau1 ↔ gen muon
    self.out.addBranch('dr_gen_tau1_ele1',     'f', -1.)  # gen tau1 ↔ gen electron
    self.out.addBranch('dr_gen_tau1_tau2',     'f', -1.)  # gen tau1 ↔ gen tau2
    self.out.addBranch('dr_reco_tau1_mu1',     'f', -1.)  # reco tau1 ↔ reco muon
    self.out.addBranch('dr_reco_tau1_tau2',    'f', -1.)  # reco tau1 ↔ reco tau2
    # Gen-Reco matching dR
    self.out.addBranch('dr_gentau1_recotau1',  'f', -1.)
    self.out.addBranch('dr_gentau2_recotau2',  'f', -1.)
    self.out.addBranch('dr_genmu1_recomu1',    'f', -1.)
    self.out.addBranch('dr_genele1_recoele1',  'f', -1.)
    self.out.addBranch('dr_reco_tau1_ele1',    'f', -1.)  # reco tau1 ↔ reco electron
    # DiTau cross-match dR (for permutation matching)
    self.out.addBranch('dr_gentau1_recotau2',  'f', -1.)
    self.out.addBranch('dr_gentau2_recotau1',  'f', -1.)

    # ─── Cutflow (basic, channel-independent) ──────────────────────
    self.out.cutflow.addcut('none',         "no cut"            )
    self.out.cutflow.addcut('has_gen_tau',  ">=1 GenVisTau"     )
    self.out.cutflow.addcut('has_reco_tau', "+ >=1 HLT tau"     )
    self.out.cutflow.addcut('has_gen_mu',   "+ >=1 gen muon"    )
    self.out.cutflow.addcut('has_reco_mu',  "+ >=1 HLT muon"   )
    self.out.cutflow.addcut('has_gen_ele',  "+ >=1 gen electron")
    self.out.cutflow.addcut('has_reco_ele', "+ >=1 HLT electron")


  def beginJob(self):
    print(">>> ModulePhase2TrigEff: Starting unified Phase-II trigger skim...")
    print(">>> All gen/reco objects saved with loose |eta|<2.5 preselection.")
    print(">>> Channel-specific cuts applied at plotting stage.")


  def endJob(self):
    self.out.endJob()


  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    sys.stdout.flush()
    branchlist = [b.GetName() for b in inputTree.GetListOfBranches()]
    self._hlt_avail = {name: path for name, path in HLT_PATHS.items() if path in branchlist}
    self._l1_avail  = {name: seed for name, seed in L1_SEEDS.items()  if seed in branchlist}
    missing_hlt = set(HLT_PATHS) - set(self._hlt_avail)
    missing_l1  = set(L1_SEEDS)  - set(self._l1_avail)
    if missing_hlt:
      print(">>> WARNING: HLT branches not found: %s" % ', '.join(HLT_PATHS[n] for n in missing_hlt))
    if missing_l1:
      print(">>> WARNING: L1 branches not found: %s" % ', '.join(L1_SEEDS[n] for n in missing_l1))
    # Determine HLT electron collection name
    if 'nhltElectron' in branchlist:
      self._hlt_ele_coll = 'hltElectron'
    elif 'nhltEle' in branchlist:
      self._hlt_ele_coll = 'hltEle'
    else:
      self._hlt_ele_coll = None
      print(">>> WARNING: No HLT electron collection found (nhltElectron / nhltEle)")


  def _fill_obj(self, prefix, obj):
    """Fill pt/eta/phi branches for a given prefix."""
    getattr(self.out, prefix + '_pt')[0]  = obj.pt
    getattr(self.out, prefix + '_eta')[0] = obj.eta
    getattr(self.out, prefix + '_phi')[0] = obj.phi

  def _clear_obj(self, prefix):
    """Set pt/eta/phi to default values."""
    getattr(self.out, prefix + '_pt')[0]  = -1.
    getattr(self.out, prefix + '_eta')[0] = -9.
    getattr(self.out, prefix + '_phi')[0] = -9.


  def analyze(self, event):
    ETA_PRE = 2.5  # loose preselection — plotter applies tighter cuts

    self.out.cutflow.fill('none')

    # ─── Trigger decisions ──────────────────────────────────────────
    for name in HLT_PATHS:
      if name in self._hlt_avail:
        getattr(self.out, name)[0] = bool(getattr(event, self._hlt_avail[name]))
      else:
        getattr(self.out, name)[0] = False
    for name in L1_SEEDS:
      if name in self._l1_avail:
        getattr(self.out, name)[0] = bool(getattr(event, self._l1_avail[name]))
      else:
        getattr(self.out, name)[0] = False

    # ─── Gen taus (GenVisTau) ───────────────────────────────────────
    gen_taus = []
    for tau in Collection(event, 'GenVisTau'):
      if abs(tau.eta) > ETA_PRE: continue
      gen_taus.append(tau)
    gen_taus.sort(key=lambda t: t.pt, reverse=True)

    self.out.n_gen_tau[0] = len(gen_taus)
    if len(gen_taus) >= 1:
      self._fill_obj('gen_tau1', gen_taus[0])
      self.out.cutflow.fill('has_gen_tau')
    else:
      self._clear_obj('gen_tau1')
    if len(gen_taus) >= 2:
      self._fill_obj('gen_tau2', gen_taus[1])
    else:
      self._clear_obj('gen_tau2')

    # ─── Gen muons (GenPart, |pdgId|=13, status=1) ─────────────────
    gen_muons = []
    for part in Collection(event, 'GenPart'):
      if abs(part.pdgId) != 13: continue
      if part.status != 1:      continue
      if abs(part.eta) > ETA_PRE: continue
      gen_muons.append(part)
    gen_muons.sort(key=lambda m: m.pt, reverse=True)

    self.out.n_gen_mu[0] = len(gen_muons)
    if len(gen_muons) >= 1:
      self._fill_obj('gen_mu1', gen_muons[0])
      if len(gen_taus) >= 1:
        self.out.cutflow.fill('has_gen_mu')
    else:
      self._clear_obj('gen_mu1')

    # ─── Gen electrons (GenPart, |pdgId|=11, status=1) ─────────────
    gen_eles = []
    for part in Collection(event, 'GenPart'):
      if abs(part.pdgId) != 11: continue
      if part.status != 1:      continue
      if abs(part.eta) > ETA_PRE: continue
      gen_eles.append(part)
    gen_eles.sort(key=lambda e: e.pt, reverse=True)

    self.out.n_gen_ele[0] = len(gen_eles)
    if len(gen_eles) >= 1:
      self._fill_obj('gen_ele1', gen_eles[0])
      if len(gen_taus) >= 1:
        self.out.cutflow.fill('has_gen_ele')
    else:
      self._clear_obj('gen_ele1')

    # ─── Reco HLT taus ─────────────────────────────────────────────
    reco_taus = []
    for tau in Collection(event, 'hltHpsPFTau'):
      if abs(tau.eta) > ETA_PRE: continue
      reco_taus.append(tau)
    reco_taus.sort(key=lambda t: t.pt, reverse=True)

    self.out.n_reco_tau[0] = len(reco_taus)
    if len(reco_taus) >= 1:
      self._fill_obj('reco_tau1', reco_taus[0])
      if len(gen_taus) >= 1:
        self.out.cutflow.fill('has_reco_tau')
    else:
      self._clear_obj('reco_tau1')
    if len(reco_taus) >= 2:
      self._fill_obj('reco_tau2', reco_taus[1])
    else:
      self._clear_obj('reco_tau2')

    # ─── Reco HLT muons ───────────────────────────────────────────
    reco_muons = []
    for muon in Collection(event, 'hltMuon'):
      if abs(muon.eta) > ETA_PRE: continue
      reco_muons.append(muon)
    reco_muons.sort(key=lambda m: m.pt, reverse=True)

    self.out.n_reco_mu[0] = len(reco_muons)
    if len(reco_muons) >= 1:
      self._fill_obj('reco_mu1', reco_muons[0])
      if len(gen_muons) >= 1 and len(gen_taus) >= 1:
        self.out.cutflow.fill('has_reco_mu')
    else:
      self._clear_obj('reco_mu1')

    # ─── Reco HLT electrons ──────────────────────────────────────────
    reco_eles = []
    if self._hlt_ele_coll:
      for ele in Collection(event, self._hlt_ele_coll):
        if abs(ele.eta) > ETA_PRE: continue
        reco_eles.append(ele)
      reco_eles.sort(key=lambda e: e.pt, reverse=True)

    self.out.n_reco_ele[0] = len(reco_eles)
    if len(reco_eles) >= 1:
      self._fill_obj('reco_ele1', reco_eles[0])
      if len(gen_eles) >= 1 and len(gen_taus) >= 1:
        self.out.cutflow.fill('has_reco_ele')
    else:
      self._clear_obj('reco_ele1')

    # ─── Precomputed dR values ─────────────────────────────────────
    # Gen separations
    if len(gen_taus) >= 1 and len(gen_muons) >= 1:
      self.out.dr_gen_tau1_mu1[0] = deltaR(gen_taus[0].eta, gen_taus[0].phi,
                                            gen_muons[0].eta, gen_muons[0].phi)
    else:
      self.out.dr_gen_tau1_mu1[0] = -1.

    if len(gen_taus) >= 1 and len(gen_eles) >= 1:
      self.out.dr_gen_tau1_ele1[0] = deltaR(gen_taus[0].eta, gen_taus[0].phi,
                                             gen_eles[0].eta, gen_eles[0].phi)
    else:
      self.out.dr_gen_tau1_ele1[0] = -1.

    if len(gen_taus) >= 2:
      self.out.dr_gen_tau1_tau2[0] = deltaR(gen_taus[0].eta, gen_taus[0].phi,
                                             gen_taus[1].eta, gen_taus[1].phi)
    else:
      self.out.dr_gen_tau1_tau2[0] = -1.

    # Reco separations
    if len(reco_taus) >= 1 and len(reco_muons) >= 1:
      self.out.dr_reco_tau1_mu1[0] = deltaR(reco_taus[0].eta, reco_taus[0].phi,
                                              reco_muons[0].eta, reco_muons[0].phi)
    else:
      self.out.dr_reco_tau1_mu1[0] = -1.

    if len(reco_taus) >= 1 and len(reco_eles) >= 1:
      self.out.dr_reco_tau1_ele1[0] = deltaR(reco_taus[0].eta, reco_taus[0].phi,
                                               reco_eles[0].eta, reco_eles[0].phi)
    else:
      self.out.dr_reco_tau1_ele1[0] = -1.

    if len(reco_taus) >= 2:
      self.out.dr_reco_tau1_tau2[0] = deltaR(reco_taus[0].eta, reco_taus[0].phi,
                                               reco_taus[1].eta, reco_taus[1].phi)
    else:
      self.out.dr_reco_tau1_tau2[0] = -1.

    # Gen-Reco matching dR
    if len(gen_taus) >= 1 and len(reco_taus) >= 1:
      self.out.dr_gentau1_recotau1[0] = deltaR(gen_taus[0].eta, gen_taus[0].phi,
                                                 reco_taus[0].eta, reco_taus[0].phi)
    else:
      self.out.dr_gentau1_recotau1[0] = -1.

    if len(gen_taus) >= 2 and len(reco_taus) >= 2:
      self.out.dr_gentau2_recotau2[0] = deltaR(gen_taus[1].eta, gen_taus[1].phi,
                                                 reco_taus[1].eta, reco_taus[1].phi)
    else:
      self.out.dr_gentau2_recotau2[0] = -1.

    if len(gen_muons) >= 1 and len(reco_muons) >= 1:
      self.out.dr_genmu1_recomu1[0] = deltaR(gen_muons[0].eta, gen_muons[0].phi,
                                               reco_muons[0].eta, reco_muons[0].phi)
    else:
      self.out.dr_genmu1_recomu1[0] = -1.

    if len(gen_eles) >= 1 and len(reco_eles) >= 1:
      self.out.dr_genele1_recoele1[0] = deltaR(gen_eles[0].eta, gen_eles[0].phi,
                                                 reco_eles[0].eta, reco_eles[0].phi)
    else:
      self.out.dr_genele1_recoele1[0] = -1.

    # DiTau cross-match dR (for permutation matching)
    if len(gen_taus) >= 1 and len(reco_taus) >= 2:
      self.out.dr_gentau1_recotau2[0] = deltaR(gen_taus[0].eta, gen_taus[0].phi,
                                                 reco_taus[1].eta, reco_taus[1].phi)
    else:
      self.out.dr_gentau1_recotau2[0] = -1.

    if len(gen_taus) >= 2 and len(reco_taus) >= 1:
      self.out.dr_gentau2_recotau1[0] = deltaR(gen_taus[1].eta, gen_taus[1].phi,
                                                 reco_taus[0].eta, reco_taus[0].phi)
    else:
      self.out.dr_gentau2_recotau1[0] = -1.

    # ─── Event info ─────────────────────────────────────────────────
    self.out.evt[0]  = event.event
    self.out.run[0]  = event.run
    self.out.lumi[0] = event.luminosityBlock

    self.out.fill()
    return True
