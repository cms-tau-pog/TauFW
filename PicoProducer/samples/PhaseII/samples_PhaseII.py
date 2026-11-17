import os
from TauFW.PicoProducer.storage.Sample import MC as M

# ============================================================================
# Phase-II MC samples for HLT trigger efficiency studies
# ============================================================================
#
# Input: Full Phase-II HLT NanoAOD from the 2-step cmsDriver pipeline
#   Step 1: L1T rerun  (GEN-SIM-DIGI-RAW -> + L1T objects)
#   Step 2: HLT + Nano (+ L1T -> NANOAODSIM with trigger branches)
# See TauFW/PhaseII/README.md for how these files are produced.
#
# Usage:
#   pico.py era PhaseII PhaseII/samples_PhaseII.py
#   pico.py channel phase2_trigeff PhaseII.ModulePhase2TrigEff
#   pico.py run    -y PhaseII -c phase2_trigeff -s ZprimeToTauTau_M500 -m 1000
#   pico.py submit -y PhaseII -c phase2_trigeff
#
# The files are privately produced (not on DAS). To use your own production,
# point PHASE2_NANO_DIR to the directory containing the merged NanoAOD files:
#   export PHASE2_NANO_DIR=/eos/user/<u>/<username>/phase2_data
# ============================================================================

storage = os.environ.get('PHASE2_NANO_DIR', "/eos/user/n/nneeraj/phase2_data")
url     = "root://eosuser.cern.ch/"
opts    = "useT1=False"

samples = [

  # Z' -> tautau (M=500 GeV, PU200)
  M('Zprime','ZprimeToTauTau_M500',"zprime_full",
    store=storage, url=url, files=[storage+"/zprime_merged.root"], opts=opts, nfilesperjob=1),

  # gg -> H -> tautau
  M('ggH','ggHToTauTau',"ggHTT_full",
    store=storage, url=url, files=[storage+"/ggHTT_merged.root"], opts=opts, nfilesperjob=1),

  # VBF H -> tautau
  M('VBF','VBFHToTauTau',"vbfHTT_full",
    store=storage, url=url, files=[storage+"/vbfHTT_merged.root"], opts=opts, nfilesperjob=1),

]
