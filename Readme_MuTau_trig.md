# MuTau 2024 Analysis — TauFW Custom Branch

This branch (`MuTau_2024`) of the [TauFW](https://github.com/cms-tau-pog/TauFW) repository contains the customized framework and scripts required for performing a MuTau trigger efficiency study using 2024 data. The analysis compares the performance of the DeepTau and ParticleNet triggers using CMS nanoAOD samples.

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


### 2. Clone this repository and checkout the MuTau analysis branch

```bash
git clone https://github.com/atharphy/TauFW.git
```
```bash
cd TauFW
```
```bash
git checkout MuTau_2024
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

---

## Environment Setup for New Sessions

In every new session, make sure to reinitialize your environment:

```bash
cd $CMSSW_BASE/src
```
```bash
cmsenv
```
```bash
export X509_USER_PROXY=~/.x509up_u`id -u`
```
```bash
voms-proxy-init --voms cms -valid 192:00
```
```bash
cd TauFW/PicoProducer
```

---

## Running the MuTau Analysis

### 1. Set the era and module

- For Data,
```bash
pico.py set era {year} samples_{year}_data.py
```
for example for 2024 this will be,
```bash
pico.py set era 2024 samples_2024_data.py
```
I have added 2024 everywhere but you can replace it with the desired year.

- For DY MC,
```bash
pico.py set era {year} samples_{year}_DY.py
```
- Then set the module to,
```bash
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
So I have made three plotting scripts,
- Trigger_Efficiency_datavsmc.py : This is used to make Data vs MC plots for the desired year.
- Trigger_Efficiency_data.py: This is used to compare the different Data eras for a certain year.
- Trigger_Efficiency_dtauvspnet.py: This is made for 2024 only for now and is used to compare the Particle Net trigger Efficiencies with DeepTau trigger efficiencies.

To run these,
- For Data vs MC plots,
```bash
python3 Trigger_Efficiency_datavsmc.py --year 2024
```
- For Data era comparison plots,
```bash
python3 Trigger_Efficiency_data.py --year 2024 --era CDEFGHI
```
- For 2024 ParticleNet vs DeepTau plots,
```bash
python3 Trigger_Efficiency_dtauvspnet.py
```
All the plots will be saved to,
```
/eos/user/<username>/analysis/2024/plots/
```
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
