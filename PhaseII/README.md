# Phase-II Tau Trigger Efficiency Studies

This directory contains the plotting tools and documentation for Phase-II HLT tau
trigger efficiency studies. The skim module and its configuration live in
[`PicoProducer/python/analysis/PhaseII/`](../PicoProducer/python/analysis/PhaseII/),
and the sample list in [`PicoProducer/samples/PhaseII/`](../PicoProducer/samples/PhaseII/).

---

## Supported Channels

| Channel    | Gen Selection | HLT Path | L1 Seed | Status |
|------------|--------------|----------|---------|--------|
| **MuTau**     | 1 GenVisTau + 1 gen μ | `HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1` | `L1T_PuppiTauTkMuon_42_18` | ✅ Working |
| **DiTau**     | 2 GenVisTau | `HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1` | `L1T_DoublePuppiTau_52_52` | ✅ Working |
| **ETau**      | 1 GenVisTau + 1 gen e | `HLT_Ele30_WPTight_L1Seeded_LooseDeepTauPFTauHPS30_eta2p1_CrossL1` | `L1T_PuppiTauTkIsoEle_45_22` | ✅ Working |
| **SingleTau** | 1 GenVisTau (pT>130) | Not in menu | Not in menu | ⚠️ Trigger not defined |

---

## Input Data

The framework takes **Phase-II HLT NanoAOD** as input, produced via a
two-step `cmsDriver.py` pipeline:

1. **Step 1:** L1T rerun (GEN-SIM-DIGI-RAW → + L1T objects)
2. **Step 2:** L1P2GT + HLT + NanoAOD (→ NANOAODSIM with HLT + L1T trigger branches), e.g.
   ```bash
   cmsDriver.py step2 --processName=HLTX -s L1P2GT,HLT:@relvalRun4,NANO:@Phase2HLT \
     --conditions auto:phase2_realistic_T33 --geometry ExtendedRun4D110 --era Phase2C17I13M9 \
     --datatier NANOAODSIM --eventcontent NANOAODSIM \
     '--inputCommands=keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT' \
     --filein file:step1.root --fileout file:step2.root -n -1 --no_exec
   ```

The NanoAOD contains:
- `hltHpsPFTau_*` — HLT tau objects (pT, η, φ, deepTau scores, etc.)
- `hltMuon_*` — HLT muon objects
- `hltElectron_*` — HLT electron objects (pT, η, φ, isolation, etc.)
- `hltAK4PuppiJet_*` — HLT jet objects
- `L1T_*` — L1 trigger seed decisions (requires the CMSSW patch below)
- `HLT_*` — HLT path decisions
- `GenVisTau_*`, `GenPart_*` — Generator-level objects (`GenVisTau` requires the CMSSW patch below)

### CMSSW patch for step 2 (`L1T_*` seeds and `GenVisTau`)

Out of the box, the Phase-II HLT NanoAOD does not contain the L1GT seed decisions:
`NanoAODOutputModule` only saves `TriggerResults` paths starting with `HLT`, `Flag`, `L1`,
or containing `Scouting`, while the L1GT menu paths are named `p*` (e.g. `pPuppiTauTkMuon42_18`).
The patch in [`cmssw_patches/`](cmssw_patches/) modifies `HLTrigger/NGTScouting/python/HLTNanoProducer_cff.py` to

- add alias paths with an `L1T_` prefix that reuse the same L1GT condition modules, e.g.
  `pPuppiTauTkMuon42_18` → `L1T_PuppiTauTkMuon_42_18`, and
- add the `GenVisTau` table to the gen-level NanoAOD sequence.

It is only needed when **producing** the NanoAOD (step 2), not for running the skim on existing files.
It was made for `CMSSW_16_0_0_pre2`. Note that `git cms-addpkg` only works in an empty `src/`
directory, so check out the package **before** cloning TauFW (see [Installation](#installation-and-setup)):

```bash
cd $CMSSW_BASE/src
git cms-addpkg HLTrigger/NGTScouting   # before cloning TauFW!
git clone https://github.com/cms-tau-pog/TauFW TauFW
git apply TauFW/PhaseII/cmssw_patches/HLTNanoProducer_L1TSeeds_GenVisTau.patch
scram b -j4
```

---

## Installation and Setup

### 1. Create and initialize CMSSW environment

```bash
cmsrel CMSSW_16_0_0_pre2
cd CMSSW_16_0_0_pre2/src
cmsenv
```

### 2. Install TauFW

If you also want to produce the NanoAOD yourself, first run `git cms-addpkg HLTrigger/NGTScouting`
and apply the [CMSSW patch](#cmssw-patch-for-step-2-l1t_-seeds-and-genvistau) as described above.
Then follow the [main TauFW installation instructions](../README.md#TauFW-1):

```bash
cd $CMSSW_BASE/src/
git clone https://github.com/cms-tau-pog/TauFW TauFW
scram b -j4
```

### 3. Verify installation

```bash
python3 -c "from TauFW.PicoProducer.analysis.PhaseII.ModulePhase2TrigEff import ModulePhase2TrigEff; print('Import OK')"
```

---

## Environment Setup (New Sessions)

```bash
cd CMSSW_16_0_0_pre2/src
cmsenv
export X509_USER_PROXY=/afs/cern.ch/user/<u>/<username>/x509up_proxy
voms-proxy-init --voms cms --valid 192:00 --out $X509_USER_PROXY
cd TauFW/PicoProducer
```

> **Note:** The proxy must be on AFS (not `/tmp/`) so that HTCondor worker
> nodes can access it. Add the `export X509_USER_PROXY=...` line to your
> `~/.bashrc` for convenience.

---

## Workflow Overview

The analysis follows a two-step workflow:

```
Phase-II HLT NanoAOD ──→ [Skim Module] ──→ pico.root ──→ [Plotter --channel] ──→ plots/
     (full NanoAOD)     ModulePhase2TrigEff   (flat tree)     (channel cuts)
```

1. **Skim:** Run the unified `ModulePhase2TrigEff` module on the full HLT NanoAOD.
   This saves all gen-level and HLT reco objects + trigger decisions into a flat tree.
   **No channel-specific cuts** — the same output works for ALL channels.

2. **Plot:** Run the plotter with `--channel` to select MuTau, DiTau, ETau, or
   SingleTau. Channel-specific selections are applied at this stage.

---

## Running the Analysis

### 1. Configure the era and channel

The samples in [`samples_PhaseII.py`](../PicoProducer/samples/PhaseII/samples_PhaseII.py) are privately
produced (not on DAS). To use your own production, point `PHASE2_NANO_DIR` to the directory
containing the merged NanoAOD files (see the sample file for the expected file names):

```bash
export PHASE2_NANO_DIR=/eos/user/<u>/<username>/phase2_data
```

Then register the era and channel:

```bash
pico.py era PhaseII PhaseII/samples_PhaseII.py
pico.py channel phase2_trigeff PhaseII.ModulePhase2TrigEff
```

> **Tip:** By default, the commands below process **all** samples defined in `samples_PhaseII.py`.
> To process only a specific sample, add the `-s <sample_name>` flag (e.g. `-s ggHToTauTau`).

### 2. Local test run

```bash
pico.py run -y PhaseII -c phase2_trigeff -s <sample_name> -m 1000
```

### 3. Submit batch jobs

```bash
pico.py submit -y PhaseII -c phase2_trigeff -s <sample_name>
```

### 4. Monitor job status

```bash
pico.py status -y PhaseII -c phase2_trigeff -s <sample_name>
```

### 5. Resubmit failed jobs

```bash
pico.py resubmit -y PhaseII -c phase2_trigeff -s <sample_name>
```

### 6. Merge output files

```bash
pico.py hadd -y PhaseII -c phase2_trigeff -s <sample_name>
```

---

## Plotting Trigger Efficiencies

The plotter lives in this directory:

```bash
cd $CMSSW_BASE/src/TauFW/PhaseII
```

Generate efficiency plots from the merged output. The **same pico file works for
all channels** — just change `--channel`:

```bash
# MuTau
python3 plot_phase2_trigeff.py \
  --input /eos/user/<u>/<username>/analysis/Phase2/Zprime/ZprimeToTauTau_M500_phase2_trigeff.root \
  --channel mutau \
  --outdir plots_mutau_zprime/ \
  --sample-label "ZprimeToTauTau M500 (Phase-II)"

# DiTau (same input!)
python3 plot_phase2_trigeff.py \
  --input /eos/user/<u>/<username>/analysis/Phase2/Zprime/ZprimeToTauTau_M500_phase2_trigeff.root \
  --channel ditau \
  --outdir plots_ditau_zprime/ \
  --sample-label "ZprimeToTauTau M500 (Phase-II)"
```

### Output Plots

| Plot | Description |
|------|-------------|
| `eff_<ch>_vs_<leg>_pt.png` | HLT pT turn-on curve (no pT cut on plotted leg) |
| `eff_<ch>_vs_<leg>_eta.png` | HLT η efficiency |
| `eff_<ch>_vs_<leg>_phi.png` | HLT φ efficiency |
| `eff_l1<ch>_vs_<leg>_{pt,eta}.png` | L1 efficiency |
| `fake_<ch>_vs_<leg>_{pt,eta,phi}.png` | HLT fake rate (fails gen-reco matching on ≥1 leg) |
| `fake_l1<ch>_vs_<leg>_{pt,eta,phi}.png` | L1 fake rate |
| `trigeff_<ch>.pdf` | **Combined PDF** with all plots for the channel in order: HLT eff → L1 eff → HLT fakes → L1 fakes |

> **Note:** The combined PDF is generated automatically alongside the PNGs.
> Use `--no-pdf` to skip it.

---

## File Structure

```
TauFW/
├── PicoProducer/
│   ├── python/analysis/PhaseII/          # Analysis module + config
│   │   ├── __init__.py
│   │   ├── ModulePhase2TrigEff.py        # Unified skim module (all channels)
│   │   └── Phase2TriggerConfig.py        # Central config: channels, L1, HLT, binning
│   └── samples/PhaseII/
│       ├── __init__.py
│       └── samples_PhaseII.py            # Sample definitions (used by pico.py)
└── PhaseII/                              # Plotting tools + documentation
    ├── cmssw_patches/
    │   └── HLTNanoProducer_L1TSeeds_GenVisTau.patch  # CMSSW patch for NanoAOD production
    ├── plot_phase2_trigeff.py            # Efficiency plotter (--channel at plot time)
    └── README.md                         # This file
```

---

## Efficiency Definition

```
Efficiency = (Gen Sel. + Reco Sel. + Trigger + Gen-Reco Match)
           / (Gen Sel. + Reco Sel.)
```

- **Gen Sel.:** Channel-specific gen-level selection (GenVisTau, GenPart)
- **Reco Sel.:** Channel-specific HLT object selection (hltHpsPFTau, hltMuon, hltElectron)
- **Trigger:** HLT path (or L1 seed) fires
- **Matching:** dR(gen, reco) < 0.1 for all legs (for DiTau, both gen-reco permutations are tried)

### Turn-on Curve Convention

For pT turn-on plots: do NOT apply the pT cut on the leg being plotted,
DO apply it for the other leg(s).

---

## Notes

- The skim module runs on **full Phase-II HLT NanoAOD** — no pre-slimming needed.
- Missing HLT/L1 branches (e.g., SingleTau) are automatically
  detected and skipped with a warning.
- The unified module applies only a loose |η| < 2.5 preselection. All physics
  cuts (pT, η=2.1, dR, matching) are applied at the plotting stage.
- Ensure your grid proxy is valid and on AFS for batch job access.

---

## Contact

**Author:** Neeraj (neeraj.neeraj@cern.ch)
