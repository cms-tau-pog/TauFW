# MuTau 2024 Analysis — TauFW Custom Branch

This branch (`MuTau_2024`) of the [TauFW](https://github.com/atharphy/TauFW) repository contains the customized framework and scripts required for performing a MuTau trigger efficiency study using 2024 data. The analysis compares the performance of the DeepTau and ParticleNet triggers using CMS nanoAOD samples.

---

## Installation and Setup

Follow these steps to set up the environment and dependencies.

### 1. Create and initialize CMSSW environment

```bash
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv
```

### 2. Clone this repository and checkout the MuTau analysis branch

```bash
git clone https://github.com/atharphy/TauFW.git
cd TauFW
git checkout MuTau_2024
```

### 3. Clone JSON POG payloads

```bash
cd PicoProducer
git clone ssh://git@gitlab.cern.ch:7999/cms-nanoAOD/jsonpog-integration.git data/jsonpog
```

### 4. Build the base framework

```bash
cd ../../
scram b -j 8
```

### 5. Clone and build nanoAOD-tools

```bash
cd $CMSSW_BASE/src/
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b -j 4
```

### 6. Clone and build TauPOG Tau ID Scale Factors

```bash
cd $CMSSW_BASE/src/
git clone https://github.com/cms-tau-pog/TauIDSFs TauPOG/TauIDSFs
cmsenv
scram b -j 4
```

### 7. Clone HTT Lepton Efficiencies

```bash
cd $CMSSW_BASE/src/TauFW/PicoProducer/data/lepton/
rm -rf HTT
git clone https://github.com/CMS-HTT/LeptonEfficiencies HTT
```

---

## Environment Setup for New Sessions

In every new session, make sure to reinitialize your environment:

```bash
cd $CMSSW_BASE/src
cmsenv
export X509_USER_PROXY=~/.x509up_u`id -u`
voms-proxy-init --voms cms -valid 192:00
cd TauFW/PicoProducer
```

---

## Running the MuTau Analysis

### 1. Set the era and module

```bash
pico.py set era 2024 samples_2024.py
pico.py set channel mutau 'ModuleMuTau_trig jec=False'
```

### 2. Perform a local test run

```bash
pico.py run -y 2024 -c mutau -m 10000
```

This should generate test ROOT files at:

```
TauFW/PicoProducer/output/pico_mutau_2024_*.root
```

### 3. Submit full job batch to the grid

```bash
pico.py submit -y 2024 -c mutau
```

### 4. Monitor job status

```bash
pico.py status -y 2024 -c mutau
```

### 5. Resubmit any failed jobs

```bash
pico.py resubmit -y 2024 -c mutau
```

---

## Output Location and Merging

Job outputs will be stored under:

```
/eos/user/<username>/output/2024/mutau/
```

Merge ROOT files using:

```bash
pico.py hadd -y 2024 -c mutau
```

The final output will be located in:

```
/eos/user/<username>/analysis/2024/Data/
```

---

## Plotting Trigger Efficiencies

### 1. Merge all per-era files into one combined ROOT file

```bash
python3 hadd_files.py -year 2024 -era CDEFGHI
```

This will create:

```
Muon_Run2024_mutau.root
```

under:

```
/eos/user/<username>/analysis/2024/Data/
```

### 2. Generate trigger efficiency plots

```bash
python3 trigger_efficiency_mutau_2024.py
```

This will generate:

- `efficiencies_2024.root`: contains 3 histograms (`eff_deep_2024`, `eff_pnet_2024`, `ratio_2024`)
- `eff_ratio_2024.png`: efficiency comparison plot

Both files will be saved to:

```
/eos/user/<username>/analysis/2024/Data/eff_plots/
```

### Contents of `efficiencies_2024.root`:

- `eff_deep_2024`: DeepTau MuTau trigger efficiency
- `eff_pnet_2024`: ParticleNet MuTau trigger efficiency
- `ratio_2024`: Ratio of ParticleNet / DeepTau efficiencies

---

## Notes

- Make sure to replace `<username>` with your CERN username in all EOS paths.
- Ensure that your `x509` proxy is valid and you have EOS access.
- The batch configuration scripts are located in:
  ```
  TauFW/PicoProducer/python/batch/
  ```

---

## Contact

For questions, please email: athar.ahmad@cern.ch
