# Tau exercise for the CMS PO&DAS 2023

<img src="../PODAS23logo.png" alt="PO&DAS 2023" max-width="800"/>
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
source /cvmfs/cms.cern.ch/cmsset_default.sh
mkdir TauPOG_PODAS
cd TauPOG_PODAS
export CMSSW=CMSSW_11_3_4
export SCRAM_ARCH=slc7_amd64_gcc900
cmsrel $CMSSW
cd $CMSSW/src
cmsenv
cd $CMSSW_BASE/src/
git clone https://github.com/cardinia/TauFW.git TauFW -b PODAS23
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
cd CombineHarvester
git checkout v2.0.0
scramv1 b clean; scramv1 b


```

## Step 1 : the basics when dealing with a new framework

For this exercise first check that you can access the tuples stored in:
/nfs/dust/cms/user/cardinia/TauPOG/PODAS/skims/2018_v10

You can try as a simple check to open one of the files in the subdirectories and inspect it. After the ROOT tutorial you should already be able to open a root file and inspect its content.

For now navigate the tree stored in one of the MC samples (DY= Drell-Yan, WJ= W+jets, TT= tt-bar, ST= single top, VV= diboson) and try to plot the visible mass of the muon+tau pair, try to apply some basic selections to the plot:
+ DeepTau vsJet
+ DeepTau vsE
+ DeepTau vsMu
+ Transverse mass

Change the selection to observe the effect of the different DeepTau working points on the distribution.


Objective: test your ability to "guess" what the content of a flat tree is. Often you'll have to dig through badly documented code (let's not kid ourselves, it's common), opening a file, inspecting it and making educated guesses is part of working in a large collaboration.
Try to understand what the variables are named in the code, draw them and see if the distribution is what you would expect based on the physical process you are inspecting

## Step 2 : Data-MC comparison

To have successful physics analyses, one need to accurately describe the collected data in the detector to the best of our theoretical understanding. As a common way to see how well our description is we plot Data/MC agreement plots.

You can have a look and use the plotting macro for the DAS [plot_CMSPODAS23](../../Plotter/plot_CMSPODAS23.py)

The plotter already includes several variables, but the ranges are rather odd considering the distrtibutions at hand. Try to fix the range to obtain something meaningful and play with the selection to see how the DeepTau scores and other distributions vary:
+ Change the DeepTau ID values
+ Remove or add the lepton veto
+ Remove the cut on the transverse mass

Selection cuts can be changed within the yml file stored in [setup_mutau_PODAS](../../Plotter/config/setup_mutau_PODAS.yml)


## Step 3: Combine

### Creating inputs

Inputs are root file used for the creation of the datacards is `Fitter/TauES/createinputsTES.py`.
These root files are saved in `Fitter/input` folder and named `ztt*.input*tag*.root`. They contain one TDirectory for each `"regions"` defined in the config file (.yml). For each region, there is a list of TH1D corresponding to each `"process"` defined in the config file (ex: ZTT). For each shape systematics, there is also two additionnal TH1D corresponding to the Up and Down variation of the process (ex: ZTT_shapedy_Up). For the TES there is a list of additional TH1D corresponding to the variations (defined by `"TESvariations"` in the config file) of the process by TES correction. 

You can create your own inputs by adding some cuts on several varaibles in the config files.

As an example, the config file in `Fitter/TauES_ID/config/Default_FitSetupTES_mutau_DM.yml` provided the inputs in `Fitter/inputs/ztt_mt_tes_m_vis.inputs-UL2018_v10-13TeV_mutau_mt65_DM_Dt2p5_DAS23_VSJetMedium.root`. You can use them directly to run combine.

:warning: Don't modify this file, create another one based on this example and change the tag to not overwrite the exisiting file.


:computer: Example of command :

 ```sh
  python TauES/createinputsTES.py -y UL2018_v10 -c TauES_ID/config/Default_FitSetupTES_mutau_DM.yml
  ```


### Config file 
This section provides an overview and explanation of the configuration file for the default tes and tid SF fit in the mutau channel. The config file contains various settings and parameters used in the analysis. For further details and explanations of each parameter, please refer to the specific sections within the config file itself.

The main information such as the channel, baseline cuts, and tag are provided at the beginning of the config file. Additional sub-options, like weight replacement for systematic uncertainties, are optional.
- `"channel"`: Specifies the channel for the analysis, which is "mutau" or "mumu" in this case.
- `"tag"`: Allows differentiation between different scenarios or versions.
- `"baselineCuts"`: Defines the baseline selection cuts for events. It includes various criteria for event selection such as charge correlation, isolation, identification, and additional requirements like lepton vetoes and met filters.
- `"regions"`: Defines different regions of interest in the analysis. Each region has a specific definition (using cuts or conditions) and a title for identification purposes. One datacard file is created for each region.
- `"plottingOrder"`: Determines the order in which the defined regions will be plotted. Used by plotParabola_POI.py to make the summary plot of the POI measurements.
- `"tesRegions"`: Specifies the TES (Tau Energy Scale) regions for the scans. Title are defined.
- `"tid_SFRegions"`: Specifies the TID (Tau ID) scale factor regions for the scans. Title are defined.
- `"observables"`: Defines the observables to be fitted and plotted in the analysis. Each observable has its own binning and title.
  - `"fitRegions"`: for each observable, fit regions are defined.
  - `"scanRegions"`: for each observable, the region to scan the poi. 
- `"TESvariations"`: Specifies the different TES variations considered in the analysis. It includes a list of TES values for which the analysis will be performed.
- `"fitSpecs"`: Defines specifications for bin-by-bin (BBB) systematics. It specifies whether to perform BBB systematics for both signal and background samples.
- `"samples"` : Specifies the samples to be used in the analysis and their association with different processes. It includes information about the file name format, sample joining, sample splitting, renaming, and removing or adding specific weights or scale factors.
- `"processes"` : Lists the processes taken into account in the fit.
- `"systematics"` : Each systematic uncertainty has an effect type (shape or lnN), associated processes, and a scaling factor if applicable.
- `"scaleFactors"`: Provides additional scale factors per year for specific processes. These scale factors can correct for cross-sections, reconstruction scale factors, and other factors.

### Running the fit :

#### Description of the main script `makePODAS23.py`: 

The script `makePODAS23.py` code provides functionality for generating datacards and performing fits in the mutau channels.

The fit is done using [Combine tool](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/). See the documentation to change the parameter of the fit. 

You can change the Parameter of Interest (POI) in the code to either scan the TES of the ID SF. 

#### Preparing the datacards

Datacards are directly generated in `makePODAS23.py`:

`generate_datacards_mutau(era, config, extratag)`: function that generates datacards for the mutau channel. This function call `harvestDatacards_TES_idSF_MCStat.py`.


The input to Combine tool is a datacards file (ztt root and txt files). The datacards are generated for each `"region"` defined in the config file.
It defines the following information :
- The tes is defined as a POI for each `"tesRegions"` defined in the config file. Horizontal morphing is used to interpolate between the templates generated for each `"TESvariations"` (defined in config file). 
- The tid SF is defined as rateParameter for each `"tid_SFRegions"` defined in the config file.
- If "norm_wj" is not specified in config file, a rateParameter "sf_W" is defined for the W+Jet normalisation. 
- The `autoMCstat` function is used to have bin-by-bin uncertainties for the sum of all backgrounds.

#### Plotting results

The results of the fit are saved in a root file (ex: `higgsCombine*root` in output folder) that can be used to produced several plots. Especially, NLL pararabola and summary plots can be produced via `plotScan(setup, era=era, config=config)` that called `plotParabola_POI_region.py`.

:computer: Example of command to run the TES scans by DM : 
```sh
python TauES_ID/makefit_PODAS23.py -y UL2018_v10 -c TauES_ID/config/Default_FitSetupTES_mutau_DM.yml
 ```
The TES NLL parabolae and summary plots are automatically generated. 
