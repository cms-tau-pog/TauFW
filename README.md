# TauFW

Framework for tau analysis using NanoAOD at CMS. Three main packages are
1. [`PicoProducer`](PicoProducer): Tools to process nanoAOD and make custom analysis ntuples.
2. [`Plotter`](Plotter): Tools for further analysis, auxiliary measurements, validation and plotting. [Under development.]
3. [`Fitter`](Fitter): Tools for measurements and fits in combine. [Under development.]

## Installation

First, setup a CMSSW release, for example,
```
export CMSSW=CMSSW_10_6_13
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel $CMSSW
cd $CMSSW/src
cmsenv
```
Which CMSSW version should matter for post-processing of nanoAOD,
but if you like to use Combine in the same repository,
it is better to use at least the [recommended version](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/#setting-up-the-environment-and-installation).
Then, install `TauFW`:
```
cd $CMSSW_BASE/src/
git clone https://github.com/cms-tau-pog/TauFW TauFW
scram b -j4
```
With each new session, do
```
export SCRAM_ARCH=slc7_amd64_gcc700
cd $CMSSW/src
cmsenv
```

### PicoProducer
If you want to process nanoAOD using `PicoProducer`, install [`NanoAODTools`](https://github.com/cms-nanoAOD/nanoAOD-tools):
```
cd $CMSSW_BASE/src/
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b -j4
```
If you want to use tau ID SF, please install [`TauIDSFs` tool](https://github.com/cms-tau-pog/TauIDSFs):
```
cd $CMSSW_BASE/src
git clone https://github.com/cms-tau-pog/TauIDSFs TauPOG/TauIDSFs
cmsenv
scram b -j4
```

### Fitter and Combine tools
If you want to use the `Combine` tools in `Fitter`, install
[`Combine`](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/#setting-up-the-environment-and-installation),
```
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.1.0
```
and then [`CombineHarvester`](https://github.com/cms-analysis/CombineHarvester),
```
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
scramv1 b clean; scramv1 b
```
