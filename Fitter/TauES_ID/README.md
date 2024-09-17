# TauFW Fitter TauES_ID 

## Installation 

See [the README.md in the parent directory](../../../#taufw).

## Creating NTuples 
The first step is to produce the NTuples via PicoProducer tool. See [the README.md in the parent directory](../../../PicoProducer).
## Creating inputs
Input root files containing all the shape systematic variation for samples defined in the config file are created using the [createinputsTES.py](https://github.com/saswatinandan/TauFW/blob/master/Fitter/TauES/createinputsTES.py). These root files are saved in the directory defined [here](https://github.com/saswatinandan/TauFW/blob/master/Fitter/TauES/createinputsTES.py#L38). New directories are created for each wp of against electron and against jet and corresponding root files are stored within these directories. They contain one TDirectory for each `"pt regions"` defined in the config file (.yml). For each region, there is a list of TH1D corresponding to each `"process"` defined in the config file (ex: ZTT). For each shape systematics, there is also two additionnal TH1D corresponding to the Up and Down variation of the process (ex: ZTT_shapedy_Up). For the TES there is a list of additional TH1D corresponding to the variations (defined by `"TESvariations"` in the config file) of the process by TES correction. 

Exemple of command :

 ```sh
 python3 TauES/createinputsTES.py -y 2023C -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -d DM0 -j Medium -e VVLoose
  ```
The above command will create root file `ztt_mt_tes_m_visDM0.inputs-2023C-13TeV_mutau_mt65_DM_pt_Dt2p5_puppimet.root` inside the directory `Fitter/input_pt_less_region/againstjet_Medium/againstelectron_VVLoose`. Once root files are created for deacy `dm`, these rootfiles needs to be hadded to the final output root file `ztt_mt_tes_m_vis.inputs-2023C-13TeV_mutau_mt65_DM_pt_Dt2p5_puppimet.root` inside the directory `Fitter/input_pt_less_region/againstjet_Medium/againstelectron_VVLoose`, and this root file will be used to extract the SF for `Medium` against jet wp and `VVLoose` against electron wp for era 2023C and for all `dms` and all `pt` regions defined in the config file `TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml`.

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

### Description of the main script `makecombinedfitTES_SF.py`: 

The script `makecombinedfitTES_SF.py` code provides functionality for generating datacards and performing fits in the mutau and mumu channels. It supports various fit options and allows for scanning and profiling of different parameters.

The fit is done using [Combine tool](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/). See the documentation to change the parameter of the fit. 

### Preparing the datacards

Datacards are generated in `makecombinedfitTES_SF.py`:
1. `generate_datacards_mutau(era, config, extratag)`: function that generates datacards for the mutau channel. This function call `harvestDatacards_TES_idSF_MCStat.py`.
2. `generate_datacards_mumu(era, config_mumu, extratag)`: function that generates datacards for the mumu channel (Control Region). This function call `harvestDatacards_zmm.py`.

3. Exemple of command :

 ```sh
  python3 TauES_ID/makecombinedfitTES_SF.py -y 2023C -o 1 -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -cmm TauES/config/FitSetup_mumu.yml -i input_pt_less_region/againstjet_Medium/againstelectron_VVLoose
  ```
The above command will create the root files and datacard txt files to do the fit for `option 1` which profiles the `tau enrgy scale` and floats `tau_id SF` freely. All `output root files and txt files` will be created in the dirrectory `output_pt_less_region/againstjet_Medium/againstelectron_VVLoose/2023C/`. 

Same `config` file which is used to create the input root files containing the systematic variations, should be used in the above command and value of the argument, input directory `i` should be same as it is defined [here](https://github.com/saswatinandan/TauFW/blob/master/Fitter/TauES/createinputsTES.py#L38).

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

The results of the fit are saved in a root file (ex: `higgsCombine*root` in output folder) that can be used to produced several plots using [this](https://github.com/saswatinandan/TauFW/blob/master/Fitter/TauES_ID/makecombinedfitTES_SF.py#L282).

- NLL pararabola and summary plots can be produced via `plotScan(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option)` that called `plotParabola_POI_region.py`.
- Postfit plots showing the correlation between parameters can be produced via `plotScan(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option)` that called `plotPostFitScan_POI.py`. The parameter to be plot need to be change in `plotPostFitScan_POI.py` code.

### Saving SF in root files

- The above `python3 TauES_ID/makecombinedfitTES_SF.py ...` command will also create the txt files containg the SFs with the error in the directory `plots_pt_less_region/againstjet_Medium/againstelectron_VVLoose/2023C/` with the name `*_fit_asymm.txt`.
- Produced `txt` files are used to save the SFs in the root file format using [this code](https://github.com/saswatinandan/TauFW/blob/master/Fitter/createroot_TES.py)
- The example command to produce the root file as below:
    ```sh
      python3 createroot_TES.py -y 2023C -e VVLoose
  ``` 
Above command will produce the root files in the direcory `tau_sf/*_SF_dm_DeepTau2018v2p5_2023_VSjetMedium_VSeleVVLoose_Run3_May24.root` both for `tes and tid` variations.
   
## Example of recipe

### Fit of TES and ID SF by DM 

1. Create the NTuples : See [the README.md in the parent directory](../../../PicoProducer).

2. Use `/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml`

3. Check the NTuples via control plots. 
 ```sh
  python plot_v10.py -y UL2018_v10 -c ./../Fitter/TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion
  ```
Control plot of the differents variables are saved in `/plots` folder. See [the README.md in the parent directory](../../../Plotter) for more informations.

4. Create the inputs :
 ```sh
  python TauES/createinputsTES.py -y 2023C -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -d DM0 -j Medium -e VVLoose 
  ```
Inputs are saved in `Fitter/input_pt_less_region/againstjet_Medium/againstelectron_VVLoose`.

5. Run the TES scans with Zmm CR : 
```sh
python3 TauES_ID/makecombinedfitTES_SF.py -y 2023C -o 1 -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -cmm TauES/config/FitSetup_mumu.yml -i input_pt_less_region/againstjet_Medium/againstelectron_VVLoose
 ```
The TES NLL parabolae and summary plots are automatically generated. 

6. Run the id SF scans with Zmm CR : 
```sh
python3 TauES_ID/makecombinedfitTES_SF.py -y 2023C -o 2 -c TauES_ID/config/Default_FitSetupTES_mutau_DM_mt65pt_lessptregion.yml -cmm TauES/config/FitSetup_mumu.yml -i input_pt_less_region/againstjet_Medium/againstelectron_VVLoose
 ```
The id SF NLL parabolae and summary plots are automatically generated.

7. Save the SF in root file:
  ```sh
   python3 createroot_TES.py -y 2023C -e VVLoose
   ```

9. run `hadd` command to hadd the root files, obtained from the last command for different wp of against electron and share this `hadd root` file with the group. 

## Post-fit Plots :construction:

This section is dedicated to the recipe followed to create post-fit plots.

### Difficulty
Achieving the combined fit of TauES and Identification Scale Factor necessitates the use of the `-M MultidimFit --algo=grid` method. Unfortunately, the option provided by the combined fit does not allow for saving post-fit results. While post-fit plots can be saved with the `-M FitDiagnostic` method (refer to the commented code in `TauES_ID/makecombinedfitTES_SF.py`), the parameter results differ between the two fits. Consequently, a set of scripts has been developed to save the values of the parameters after the `-M MultidimFit --algo=grid` fit.

### Recipe
The values of the fit parameters specified in `fulllist` within `plotPostFitScan_POI.py` are saved in a text file by the `writeParametersFitVal()` function. These values correspond to the sigma variation of the parameter after the fit (for LnN and shape systematic).
- **For LnN systematics and rate parameters:** The script `WriteSFsFit.py` calculates and saves Post-fit Scale Factors to a text file. For LnN systematic uncertainties, the values obtained from `combine` represent the sigma variation of the parameters. This script reads the configuration file to determine the corresponding 1-sigma variation and calculates the parameter values after the fit. For rate parameters, the values are preserved as is. The results are saved in a text file with associated processes affected by the systematics. These results can be copied into the config file (like `Default_FitSetupTES_mutau_DM_pt.yml`) and utilized in the `./Plotter/plot_postfit.py` script to generate post-fit plots.
- **For Shape systematics:** The variation can be calculated in the same way with `shape_syt.py`. The values of the parameters need to be used to generate new templates with the picoproducer. The script `plot_postfit_shift.py` has been used to generate the post-fit plots by specifying the TES values, shape parameter values, and the values of the LnN and rateParameter in the config file.

### Warning :warning:
- These plots do not include `dy_shape` systematics.
- This procedure is not optimized and automated; more developments are welcomed!
