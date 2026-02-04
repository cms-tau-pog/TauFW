# Tau Trigger Studies (Trigger Efficiencies using TauFW)

This branch (`Trig_EFf_with_SF`) of the [TauFW](https://github.com/cms-tau-pog/TauFW) repository contains the customized framework and scripts required for performing Tau trigger efficiency studies. The analysis compares the performance of the Tau triggers using CMS NANOAOD samples.

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
git checkout Trig_EFf_with_SF
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
Replace {year} with the year that you want to run on (2024, 2025, 2026)
- For MC samples:

```bash
pico.py set era {year} Tau_trig_SF_samples/{year}/samples_year_DY.py
```
- For Data samples:
```bash
pico.py set era {year} Tau_trig_SF_samples/{year}/samples_year_data.py
```
Do not set the MC and Data as samples together. Run it first on either Data and then on the other.
```bash
pico.py set channel mutau 'Tau_trig_SF_studies/ModuleMuTau_trig jec=False'
```
### 2. Perform a local test run

```bash
pico.py run -y {year} -c mutau -m 10000
```

This should generate test ROOT files at:

```
TauFW/PicoProducer/output/pico_mutau_{year}_*.root
```

### 3. Submit full job batch to the grid

```bash
pico.py submit -y {year} -c mutau
```

### 4. Monitor job status

```bash
pico.py status -y {year} -c mutau
```

### 5. Resubmit any failed jobs

```bash
pico.py resubmit -y {year} -c mutau
```

---

## Output Location and Merging

Job outputs will be stored under:

```
/eos/user/<username>/output/{year}/mutau/
```

Merge ROOT files using:

```bash
pico.py hadd -y {year} -c mutau
```

The final output will be located in:

```
/eos/user/<username>/analysis/{year}/{Data/DY}/
```

---
Now lets move to the plotting part. Lets move to the working directory of the Plotting tools.
```bash
cd ../Tau_Trigger_SF
```

## Plotting Trigger Efficiencies

### 1. Merge all per-era files into one combined ROOT file

```bash
python3 helper_scripts/hadd_files.py -year {year} -era CDEFGHI
```

This will create:

```
Muon_Run{year}_mutau.root
```

under:

```
/eos/user/<username>/analysis/{year}/Data/
```

### 2. Generate trigger efficiency plots
There are three scripts which can be used to make plots,
- Trigger_Efficiency_datavsmc.py : This is used to make Data vs MC plots for the desired year.
- Trigger_Efficiency_data_generic.py : This is used to compare the different Data eras for a certain year.
- Trigger_Efficiency_dtauvspnet.py : This is made for 2024 only for now and is used to compare the Particle Net trigger Efficiencies with DeepTau trigger efficiencies.

To run these,
- For Data vs MC plots,
```bash
python3 Efficiency_plotters/Trigger_Efficiency_datavsmc.py --year 2024
```
- For Data era comparison plots,
The attributes are {-- year} {year} for the year to plot, {--era} {BCDEFGHI} for the eras to plot and {--ratio} {era} for the era to use as reference it Total file is given as None in the script. 
```bash
python3 Efficiency_plotters/Trigger_Efficiency_data_generic.py --year 2024 --era CDEFGHI --ratio G
```
- For 2024 ParticleNet vs DeepTau plots,
```bash
python3 Efficiency_plotters/Trigger_Efficiency_dtauvspnet.py
```
All the plots will be saved to,
```
/eos/user/<username>/analysis/{year}/plots/
```
---
## Computing Trigger SF

Once you have the skimmed root files for Data and MC, you can move on to calculate the Trigger SF using this [readme](https://github.com/atharphy/TauFW/blob/Trig_EFf_with_SF/Tau_Trigger_SF/TriggerSF_tools/Readme.md).

---

## Notes

- Make sure to replace `<username>` with your CERN username in all EOS paths.
- Make sure to replace {year} with the desired year that you want to run on in each line where specified.
- Ensure that your `x509` proxy is valid and you have EOS access.
- The batch configuration scripts are located in:
  ```
  TauFW/PicoProducer/python/batch/
  ```
---

## Contact

For questions, please email: athar.ahmad@cern.ch
