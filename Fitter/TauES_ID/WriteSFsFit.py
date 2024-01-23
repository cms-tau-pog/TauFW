"""
Date: December 2023
Author: @oponcet
Description: Calculate and Save Postfit Scale Factors to a Text File. For LnN systematic uncertainties, the values obtained 
from `combine` represent the sigma variation of the parameters. This script reads the configuration file to determine the 
corresponding 1-sigma variation and calculates the parameter values after the fit. For rate parameters, the values are preserved 
as it is. The results are saved in a text file with associated processes affected by the systematics. These results can be 
utilized in the `./Plotter/plot_postfit.py` script to generate postfit plots.
"""

Function:
calculate_SFpostfit(config, year, output_file)
- Loads a configuration file, calculates postfit scale factors for various parameters,
  and saves the results to a text file.

Parameters:
- config (str): Path to the configuration YAML file.
- year (str): The year for which the postfit scale factors are calculated.
- output_file (str): Path to the output text file where the results will be saved.
"""

import re
import yaml

def calculate_SFpostfit(config, year, output_file):

    # Load config file
    with open(config, 'r') as config_file:
        setup = yaml.safe_load(config_file)

    tag = setup["tag"]
    param_SF_postfit_dict = {}  # Store param_SF_postfit values for different parameters

    # Mapping for region replacement
    region_mapping = {'DM0': 'dm_2==0', 'DM1': 'dm_2==1', 'DM10': 'dm_2==10', 'DM11': 'dm_2==11'}

    # Process parameters without comparing to the yaml file
    additional_params = {
        "tid_SF": {"values": {}, "processes": ['ZTT'] },
        "xsec_dy": {"values": {}, "processes": ['ZTT', 'ZL', 'ZJ']},
        "sf_W": {"values": {}, "processes": ['W']},
    }
    # additional_params = {
    #     "tid_SF": {"values": {}, "processes": ['ZTT']},
    #     "sf_W": {"values": {}, "processes": ['W']},
    # }
    # Extract parameter name and value from txt data
    
    for key in additional_params:
        param_SF_postfit_dict[key] = {}
        for region in setup["plottingOrder"]:
            param_values = {}
            # Read values from txt file
            with open('./postfit_%s/FitparameterValues_%s_DeepTau_%s-13TeV_%s.txt' % (year,tag, year,region), 'r') as txt_file:
                txt_data = txt_file.readlines()
            for line in txt_data:
                match = re.match(r'(\w+)\s*:\s*([\d.-]+)', line)
                if match:
                    param_name_txt = match.group(1).replace("trackedParam_", "")
                    if key in param_name_txt:
                        print(param_name_txt)  
                        param_value = float(match.group(2))
                        # Replace regions according to mapping
                        print(region)
                        actual_region = region_mapping.get(region, region)
                        param_SF_postfit_dict[key][actual_region] = param_value

    for sys in setup["systematics"]:
        if setup["systematics"][sys]['effect'] == 'lnN' :
            param_name = sys
            if "name" in setup["systematics"][sys]:
                param_name = setup["systematics"][sys]["name"]

            param_SF_postfit_dict[param_name] = {}  # Initialize dictionary for each parameter
            for region in setup["plottingOrder"]:
                param_values = {}

                # Read values from txt file
                with open('./postfit_%s/FitparameterValues_%s_DeepTau_%s-13TeV_%s.txt' % (year,tag, year,region), 'r') as txt_file:
                    txt_data = txt_file.readlines()

                # Extract parameter name and value from txt data
                for line in txt_data:
                    match = re.match(r'(\w+)\s*:\s*([\d.-]+)', line)
                    if match:
                        param_name_txt = match.group(1)
                        param_value = float(match.group(2))
                        param_values[param_name_txt] = param_value

                param_name_modified = param_name.replace("$BIN", region)
                param_SF = setup["systematics"][sys]["scaleFactor"]
                if param_name_modified in param_values:
                    param_SF_postfit_val = param_values[param_name_modified] * (param_SF - 1) + 1
                    # Replace regions according to mapping
                    actual_region = region_mapping.get(region, region)
                    # Store param_SF_postfit values for each parameter and region
                    param_SF_postfit_dict[param_name][actual_region] = param_SF_postfit_val

    # Write param_SF_postfit_dict to a file
    with open(output_file, 'w') as outfile:
        outfile.write("scaleFactors:\n")
        for param, regions in param_SF_postfit_dict.items():
            outfile.write("  %s:\n" % param)
            if param in additional_params:
                processes =  additional_params[param]["processes"]
            # elif param in shape_params:
            #     processes =  shape_params[param]["processes"]
            else:     
                processes = setup["systematics"].get(param, {}).get("processes", [])

            print("for parameter %s process : %s " %(param, processes))
            outfile.write("    processes: %s\n" % (processes))            
            outfile.write("    values:\n")
            outfile.write("      {\n")
            for region, value in regions.items():
                outfile.write("      \'%s\': %s,\n" % (region, value))
            outfile.write("      }\n")




year = "2022_postEE" #2022_preEE

config = "./TauES_ID/config/Default_FitSetupTES_mutau_DM_mt40_mvisrange.yml"
# Load config file
with open(config, 'r') as config_file:
    setup = yaml.safe_load(config_file)

tag = setup["tag"]

output_filename = "SFpostfit%s_%s.txt" %(year,tag)
print(output_filename)
calculate_SFpostfit(config, year, output_filename)