# TauFW

Framework for tau analysis using NanoAOD at CMS. Three main packages are
1. [PicoProducer](tree/master/PicoProducer): Tools to process nanoAOD.
2. [Plotter](tree/master/Plotter): Tools for analysis and plotting.
2. [Fitter](tree/master/Fitter): Tools for measurements and fits in combine.

## Installation

First, install `NanoAODTools`:
```
export SCRAM_ARCH=slc6_amd64_gcc700
cmsrel CMSSW_10_3_3
cd CMSSW_10_3_3/src
cmsenv
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b
```

Then, install `TauFW`:
```
cd $CMSSW_BASE/src/
git clone https://github.com/IzaakWN/TauFW TauFW
scram b
```