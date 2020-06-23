# TauFW

Framework for tau analysis using NanoAOD at CMS. Three main packages are
1. [`PicoProducer`](PicoProducer): Tools to process nanoAOD and make custom analysis ntuples.
2. [`Plotter`](Plotter): Tools for analysis and plotting.
3. [`Fitter`](Fitter): Tools for measurements and fits in combine.

## Installation

First, setup a CMSSW release install and [`NanoAODTools`](https://github.com/cms-nanoAOD/nanoAOD-tools), for example
```
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_6_13
cd CMSSW_10_6_13/src
cmsenv
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b
```

Then, install `TauFW`:
```
cd $CMSSW_BASE/src/
git clone https://github.com/cms-tau-pog/TauFW TauFW
scram b
```