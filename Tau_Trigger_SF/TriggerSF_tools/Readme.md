
# Trigger Scale Factor Tool — Usage Guide

This document describes how to **derive Tau trigger scale factors (SFs)** using the
**TriggerSF_tools** framework integrated within TauFW.

**Supported Channels**: etau, mutau, singletau, ditau, ditaujet, vbftau, vbfditau

This tool has been written for 2024 but can be easily adapted for other data years.

> This README assumes that:
> - CMSSW is already built
> - TauFW and all dependencies are already installed
> - Skimmed ROOT files from the PicoProducer step already exist


---

## Directory Structure

The Trigger SF tools live under:

```
TauFW/Tau_Trigger_SF/TriggerSF_tools
```

Key scripts:
```
TriggerSF_tools/
├── Common/
│   ├── AnalysisTypes.py
│   ├── AnalysisTools.py
│   ├── RootPlotting.py
│   └── RootObjects.py
├── createTurnOn_multi.py
├── fitTurnOn_multi.py
└── convert_to_json.py
```


---

## Environment Setup (Each New Session)

```bash
cd $CMSSW_BASE/src
cmsenv
```

Make sure Python can find TauFW and Trigger SF tools:

```bash
export PYTHONPATH=$CMSSW_BASE/src:$CMSSW_BASE/src/TauFW:$PYTHONPATH
```

Move to the Trigger SF working directory:

```bash
cd TauFW/Tau_Trigger_SF/TriggerSF_tools
```

---

## Required Inputs

You need **merged skimmed ROOT files** produced by the PicoProducer step.

Typical inputs (you can rename them as you like):
- **Data**
  ```
  data_mutau.root
  ```
- **MC (DY)**
  ```
  mc_mutau.root
  ```

These are usually located under:
```
/eos/user/<username>/analysis/{year}/{Data/MC}/
```

---

## Step 1: Create Turn-On Curves

```bash
python3 createTurnOn_multi.py   --input-data /path/to/data_mutau.root   --input-dy-mc /path/to/mc_mutau.root   --output TurnOn_2024   --channels mutau   --decay-modes all,0,1,10,11   --working-points VVVLoose,VVLoose,VLoose,Loose,Medium,Tight,VTight,VVTight
```

Output:
```
TurnOn_2024_mutau.root
```

---

## Step 2: Fit Turn-On Curves

```bash
python3 fitTurnOn_multi.py   --input TurnOn_2024_mutau.root   --output Fit_2024   --channels mutau   --decay-modes all,0,1,10,11   --working-points VVVLoose,VVLoose,VLoose,Loose,Medium,Tight,VTight,VVTight
```

Output directory:
```
Fit_2024_mutau/
```

---

## Step 3: Convert Fits to JSON Scale Factors

```bash
python3 convert_to_json.py   --input Fit_2024   --output trigger_sf_2024.json
```

Output:
```
trigger_sf_2024.json
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
cd TauFW/Tau_Trigger_SF/TriggerSF_tools

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

## Contacts

- **TauFW Framework**: Athar Ahmad
- **Trigger SF**: Irene Andreou
- **Integration**: Neeraj
