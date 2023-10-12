# Tau exercise for the CMS PO&DAS 2023

<img src="../docs/PODAS23logo.png" alt="PO&DAS 2023" max-width="800"/>

Welcome to the next iteration of the TauPOG exercises for the Data Analysis Schools in CMS!

You will be spending with us the next 4 hours but in case you are interested in the topics covered and would like to know more, you can have a look at the Tau [short](https://github.com/CMSDAS/tau-short-exercise) and [long](../CMSDAS2020/main.md) exercises from the CMSDAS 2020. You can also check out the publication describing the Run 2 performance of the Tau identification for further information:
[doi:10.1088/1748-0221/17/07/P07023](https://doi.org/10.1088/1748-0221/17/07/P07023).

The main target of this Tau exercise is to give you an overview of the Tau reconstruction and identification in CMS, and of the procedures used to validate the identification algorithm and measure the scale factors used to fix the MC modelling to better represent the data collected at the detector. 

In the context of this exercise, you will do a simplified version of the Tau ID efficiency and energy scale measurement.

This exercise is based on the [TauFW](https://github.com/cms-tau-pog/TauFW) analysis framework and builds upon 2018 NanoAOD datasets.
The statistical inference is performed with [CombinedLimit](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit),
[CombineHarvester](https://github.com/cms-analysis/CombineHarvester).

Due to time constraints, and to avoid oversaturating the batch system with jobs we provide for you flat tuples with several preselections applied. If you desire you are free to try to run the FW yourself for the skimming of nanoAODs locally following the instructions in [TauFW/PicoProducer](https://github.com/cms-tau-pog/TauFW).


## Preparation work

The first part of the exercise requires you to set up a CMSSW release, you can start running the setup and preparing your work area while the description of tau leptons is done.


```bash
mkdir TauPOG_PODAS
cd TauPOG_PODAS
export CMSSW=CMSSW_11_3_4
export SCRAM_ARCH=slc7_amd64_gcc900
cmsrel $CMSSW
cd $CMSSW/src
cmsenv
cd $CMSSW_BASE/src/
git clone https://github.com/cardinia/TauFW.git TauFW -b PODAS
scram b -j4
cd $CMSSW_BASE/src/
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b -j4
cd $CMSSW_BASE/src/
git clone https://github.com/cms-tau-pog/TauIDSFs TauPOG/TauIDSFs
scram b -j4
cd $CMSSW_BASE/src/TauFW/PicoProducer/data/lepton/
rm -rf HTT
git clone https://github.com/CMS-HTT/LeptonEfficiencies HTT
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v9.1.0
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
scramv1 b clean; scramv1 b
git checkout v2.0.0

```

## Step 1

For this exercise first check that you can access the tuples stored in:
/nfs/dust/cms/user/cardinia/TauPOG/PODAS/skims/2018_v10

You can try as a simple check to open one of the files in the subdirectories and inspect it. After the ROOT tutorial you should already be able to open a root file and inspect its content.

For now navigate the tree stored and try to plot the visible mass of the muon+tau pair, try to apply some basic selections to the plot:
+ DeepTau vsJet
+ DeepTau vsE
+ DeepTau vsMu
+ Transverse mass

Change the selection to observe the effect of the different DeepTau working points on the distribution.