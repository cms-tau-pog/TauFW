# TauFW Fitter TauES_ID 

## Installation 

See [the README.md in the parent directory](../../../#taufw).

## Creating NTuples 
The first step is to produce the NTuples via PicoProducer tool. See [the README.md in the parent directory](../../../PicoProducer).
## Creating inputs
Inputs are root file used for the creation of the datacards. The script to create the inputs is [createinputsTESPlots.py](Fitter/TauES/createinputsTESPlots.py). These root files are saved in `Fitter/input` folder and named `ztt*.input*tag*.root`. They contain one TDirectory for each `"regions"` defined in the config file (.yml). For each region, there is a list of TH1D corresponding to each `"process"` defined in the config file (ex: ZTT). For each shape systematics, there is also two additionnal TH1D corresponding to the Up and Down variation of the process (ex: ZTT_shapedy_Up). For the TES there is a list of additional TH1D corresponding to the variations (defined by `"TESvariations"` in the config file) of the process by TES correction. 

Exemple of command :

 ```sh
  python TauES/createinputsTES.py -y UL2018 -c TauES_ID/config/FitSetupTES_mutau_DMt.yml 
  ```

See [the README.md in the TauES directory ](../TauES)

## Config file 
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


## Running the fit :

### Description of the main script [makecombinedfitTES_SF.py](makecombinedfitTES_SF.py): 

The script [makecombinedfitTES_SF.py](makecombinedfitTES_SF.py) code provides functionality for generating datacards and performing fits in the mutau and mumu channels. It supports various fit options and allows for scanning and profiling of different parameters.

The fit is done using [Combine tool](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/). See the documentation to change the parameter of the fit. 

### Preparing the datacards

Datacards are generated directly in [makecombinedfitTES_SF.py](makecombinedfitTES_SF.py):
1. `generate_datacards_mutau(era, config, extratag)`: function that generates datacards for the mutau channel. This function call [harvestDatacards_TES_idSF_MCStat.py](harvestDatacards_TES_idSF_MCStat.py).
2. `generate_datacards_mumu(era, config_mumu, extratag)`: function that generates datacards for the mumu channel (Control Region). This function call [harvestDatacards_zmm.py](harvestDatacards_zmm.py).

The input to Combine tool is a datacards file (ztt root and txt files). The datacards are generated for each `"region"` defined in the config file.
It defines the following information :
- The tes is defined as a POI for each `"tesRegions"` defined in the config file. Horizontal morphing is used to interpolate between the templates generated for each `"TESvariations"` (defined in config file). 
- The tid SF is defined as rateParameter for each `"tid_SFRegions"` defined in the config file.
- If `-cmm Zmmconfigfile.yml` command is used, so if CR is used, dy_xsec is also implemented as rateParameter.
- If "norm_wj" is not specified in config file, a rateParameter "sf_W" is defined for the W+Jet normalisation. 
- The `autoMCstat` function is used to have bin-by-bin uncertainties for the sum of all backgrounds.

Merging of datacards is required for two case:
1. When using Zmm CR to merge the datacards between each mutau region and Zmm CR. In this case, `merge_datacards_ZmmCR(setup, setup_mumu, era, extratag, region)` is called and it returns the the name of the CR + region datacard file (without .txt).
2. When using option for a combined fit of all the regions (option 4, 5 and 6), wich require to merge the datacard of all the regions (and optionnaly the Zmm CR) in one datacard file. The systematic with the same name (ex tid_pt1 of DM0 and tid_pt1 of DM10) will be assumed 100% correlated. In this case, `merge_datacards_regions(setup, setup_mumu, config_mumu, era, extratag)` is called and return the name of the datacard file (without .txt).

### Fit options
The option 4,5,6 use combined datacards and are useful to fit on several regions. (ex: tes_DM and tid_SF_pt ...)

1.  Option 1 : This is the default option. For each `"scanRegions"` defined in the config file, a scan of tes is performed. The scan is done in the range specify in the config file (`"TESvariations"`). The tid SF is implemented as a rateParamer wich is profiled. Ex usage : Scan by DM.
2.  Option 2 :  For each `"scanRegions"` defined in the config file, a scan of tid SF is performed. The tes needs to be set as POI with `redefineSignalPOIs` to include it in the fit.
3.  Option 3 : For each 'scanRegions' of each 'observable' a 2D scan of the tes and tid SF is performed. Note that they need to be in the same region (ex: tes_DM0 and tid_SF_DM0).
4.  Option 4 : For each `"scanRegions"` defined in the config file, a scan of the parameter of interest (POI) tif_SF is done. The tes and the tid_SF of other regions are profiled POIs. Ex usage : Fit tes by DM and tid SF by pt.
5.  Option 5 : For each `"scanRegions"` defined in the config file, a scan of the parameter of interest (POI) tes is done. The tid_SF and the tes of other regions are profiled POIs. Ex usage : Fit tes by DM and tid SF by pt.
6.  Option 5 : For each "`tesRegions`" and `"tidRegions"` defined in the config file, a 2D scan of the parameters of interest (POI) tes and tid_SF is done. The tid_SF and the tes of other regions are profiled POIs. Ex usage : Fit tes by DM and tid SF by pt.

### Plotting results

The results of the fit are saved in a root file (ex: `higgsCombine*root` in output folder) that can be used to produced several plots.

- NLL pararabola and summary plots can be produced via `plotScan(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option)` that called [Fitter/TauES_ID/plotParabola_POI_region.py](Fitter/TauES_ID/plotParabola_POI_region.py).
- Postfit plots showing the correlation between parameters can be produced via `plotScan(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option)` that called `plotPostFitScan_POI.py`. The parameter to be plot need to be change in `plotPostFitScan_POI.py` code.
- Summary plot of the results of the POI (tes or tid_SF) in function of pt (DM inclusive or not with `--dm-bins` option) via [plotpt_poi.py](plotpt_poi.py). This script uses the txt output file of [plotParabola_POI_region.py](plotParabola_POI_region.py) to produce the plots. The values of the mean of the pt bin and its std dev need to be change in the fit. These values can be obtained using [Plotter/get_ptmean.py](./../Plotter/get_ptmean.py) (need pt plots of the distribution).


## Example of recipe

### Fit of TES and ID SF by DM 

1. Create the NTuples : See [the README.md in the parent directory](../../../PicoProducer).

2. Use `/config/Default_FitSetupTES_mutau_DM.yml`

3. Check the NTuples via control plots. 
 ```sh
  python plot_v10.py -y UL2018_v10 -c ./../Fitter/TauES_ID/config/Default_FitSetupTES_mutau_DM.yml 
  ```
Control plot of the differents variables are saved in `/plots` folder. See [the README.md in the parent directory](../../../Plotter) for more informations.

4. Create the inputs :
 ```sh
  python TauES/createinputsTES.py -y UL2018_v10 -c TauES_ID/config/Default_FitSetupTES_mutau_DM.yml 
  ```
Inputs are saved in `input/ztt_mt_tes_m_vis.inputs-UL2018_v10-13TeV_mutau_mt65_DM_Dt2p5_default`.

5. Run the TES scans with Zmm CR : 
```sh
python TauES_ID/makecombinedfitTES_SF.py -y UL2018_v10 -o 1 -c TauES_ID/config/Default_FitSetupTES_mutau_DM.yml -cmm TauES/config/FitSetup_mumu.yml
 ```
The TES NLL parabolae and summary plots are automatically generated. 

6. Run the id SF scans with Zmm CR : 
```sh
python TauES_ID/makecombinedfitTES_SF.py -y UL2018_v10 -o 2 -c TauES_ID/config/Default_FitSetupTES_mutau_DM.yml -cmm TauES/config/FitSetup_mumu.yml
 ```
The id SF NLL parabolae and summary plots are automatically generated. 

