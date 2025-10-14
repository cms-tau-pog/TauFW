# MuTau 2024 Analysis with Trigger SF — TauFW Integration Branch

This branch (`MuTau_2024_TriggerSF_integration`) of the [TauFW](https://github.com/atharphy/TauFW) repository integrates Ather's MuTau analysis framework with Irene's Tau Trigger Scale Factor calculation tools. It enables complete trigger efficiency studies and scale factor derivation for 2024 CMS data.

**Supported Channels**: etau, mutau, singletau, ditau, ditaujet, vbftau, vbfditau

---

## Installation and Setup

Follow these steps to set up the environment and dependencies.

### 1. Create and initialize CMSSW environment

```bash
cmsrel CMSSW_14_1_0_pre4
```

```bash
cd CMSSW_14_1_0_pre4/src
```

```bash
cmsenv
```

### 2. Clone this repository and checkout the integration branch

```bash
git clone https://github.com/atharphy/TauFW.git
```

```bash
cd TauFW
```

```bash
git checkout MuTau_2024_TriggerSF_integration
```

### 3. Clone JSON POG payloads

```bash
cd PicoProducer
```

```bash
git clone ssh://git@gitlab.cern.ch:7999/cms-nanoAOD/jsonpog-integration.git data/jsonpog
```

### 4. Build the base framework

```bash
cd ../../
```

```bash
scram b -j 8
```

### 5. Clone and build nanoAOD-tools

```bash
cd $CMSSW_BASE/src/
```

```bash
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
```

```bash
scram b -j 4
```

### 6. Clone and build TauPOG Tau ID Scale Factors

```bash
cd $CMSSW_BASE/src/
```

```bash
git clone https://github.com/cms-tau-pog/TauIDSFs TauPOG/TauIDSFs
```

```bash
cmsenv
```

```bash
scram b -j 4
```

### 7. Clone HTT Lepton Efficiencies

```bash
cd $CMSSW_BASE/src/TauFW/PicoProducer/data/lepton/
```

```bash
rm -rf HTT
```

```bash
git clone https://github.com/CMS-HTT/LeptonEfficiencies HTT
```

### 8. Install Python dependencies for Trigger SF

```bash
cd $CMSSW_BASE/src
```

```bash
cmsenv
```

```bash
pip3 install --user scipy matplotlib scikit-learn
```

Verify installation:
```bash
python3 -c "import scipy, matplotlib, sklearn; print('All packages OK')"
```

---

## Framework Structure

```
TauFW/
├── PicoProducer/              # Main TauFW analysis
├── TriggerSF/                 # Trigger SF tools (NEW)
│   ├── Common/                # Core modules
│   │   ├── AnalysisTypes.py
│   │   ├── AnalysisTools.py
│   │   ├── RootPlotting.py
│   │   └── RootObjects.py
│   ├── createTurnOn_multi.py  # Turn-on creation
│   ├── fitTurnOn_multi.py     # Fitting script
│   └── convert_to_json.py     # JSON output
```

---

## Usage

### Complete Workflow

#### Step 1: Set up environment (start of each session)

```bash
cd $CMSSW_BASE/src
```

```bash
cmsenv
```

#### Step 2: Create turn-on curves

```bash
cd $CMSSW_BASE/src/TauFW/TriggerSF
```

```bash
python3 createTurnOn_multi.py \
    --input-data /path/to/skimmed_data.root \
    --input-dy-mc /path/to/skimmed_mc.root \
    --output TurnOn_2024 \
    --channels mutau,etau,ditau,ditaujet \
    --decay-modes all,0,1,10,11 \
    --working-points VVVLoose,VVLoose,VLoose,Loose,Medium,Tight,VTight,VVTight
```

#### Step 3: Fit turn-on curves

```bash
python3 fitTurnOn_multi.py \
    --input TurnOn_2024_*.root \
    --output Fit_2024 \
    --channels mutau,etau,ditau,ditaujet \
    --decay-modes all,0,1,10,11 \
    --working-points VVVLoose,VVLoose,VLoose,Loose,Medium,Tight,VTight,VVTight
```

#### Step 4: Convert to JSON scale factors

```bash
python3 convert_to_json.py \
    --input Fit_2024 \
    --output trigger_sf_2024.json
```

---

## Configuration

### Trigger Channels and Validity Thresholds (2024)

| Channel | Validity pT (GeV) | Monitoring Trigger |
|---------|-------------------|-------------------|
| etau | 35 | `HLT_Ele24_eta2p1_WPTight_Gsf_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1` |
| mutau | 32 | `HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1` |
| singletau | 190 | `HLT_IsoMu24_eta2p1_LooseDeepTauPFTauHPS180_eta2p1` |
| ditau | 40 | `HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1` |
| ditaujet | 35 | `HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1` |
| vbftau | 50 | `HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1` |
| vbfditau | 25 | `HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1` |

### Decay Modes
- **all**: All decay modes combined
- **0**: 1-prong
- **1**: 1-prong + π⁰
- **10**: 3-prong
- **11**: 3-prong + π⁰

### Working Points
DeepTau ID: `VVVLoose`, `VVLoose`, `VLoose`, `Loose`, `Medium`, `Tight`, `VTight`, `VVTight`

---

## Quick Example: MuTau Channel

```bash
cd $CMSSW_BASE/src
cmsenv
cd TauFW/TriggerSF

# Create turn-ons
python3 createTurnOn_multi.py \
    --input-data data_mutau.root \
    --input-dy-mc mc_mutau.root \
    --output TurnOn_MuTau \
    --channels mutau

# Fit turn-ons
python3 fitTurnOn_multi.py \
    --input TurnOn_MuTau_mutau.root \
    --output Fit_MuTau \
    --channels mutau

# Generate JSON
python3 convert_to_json.py \
    --input Fit_MuTau \
    --output sf_mutau_2024.json
```

---

## Troubleshooting

### Import errors
**Problem**: `ModuleNotFoundError: No module named 'TauFW.TriggerSF'`

**Solution**:
```bash
cd $CMSSW_BASE/src
cmsenv
```

### Missing Python packages
**Problem**: `ModuleNotFoundError: No module named 'scipy'`

**Solution**:
```bash
pip3 install --user scipy matplotlib scikit-learn
```

### ROOT import issues
**Problem**: `ImportError: No module named 'ROOT'`

**Solution**:
```bash
cd $CMSSW_BASE/src
cmsenv
python3 -c "import ROOT; print('ROOT OK')"
```

---

## Output Files

- **Turn-on ROOT files**: `TurnOn_2024_<channel>.root` - Contains efficiency histograms
- **Fit results**: `Fit_2024_<channel>/` - Fit parameters and plots
- **JSON scale factors**: `trigger_sf_2024.json` - Ready for physics analysis

---

## References

- **TauFW Repository**: https://github.com/atharphy/TauFW
- **Trigger SF Repository**: https://github.com/Ksavva1021/Tau-Trigger-SF
- **CMS Tau POG**: https://twiki.cern.ch/twiki/bin/view/CMS/TauIDRecommendation

---

## Contact

- **TauFW**: Ather
- **Trigger SF**: Irene Andreou, Braden Allmond
- **Integration**: Neeraj
