
"""
Date : December 2023
Author : @oponcet
Description: Calculate Postfit Values for Shape Systematics.

Function:
calculate_shape_syst()
- Calculates postfit values for shape systematics parameters based on a specified variation.
- Reads parameter values from a text file and calculates the postfit values.
- Prints the postfit values for each relevant parameter.

Parameters:
- None (parameters are predefined within the function).
"""
import re
import yaml

def calculate_shape_syst():

    year = "2022_postEE"
    tag= "_mutau_mt65cut_DM_Dt2p5_VSJetMedium_mvisrange_puppimet"
    
    for region in ["DM0", "DM1", "DM10", "DM11"]:

        with open('./postfit_%s/FitparameterValues_%s_DeepTau_%s-13TeV_%s.txt' % (year,tag, year,region), 'r') as txt_file:
            txt_data = txt_file.readlines()
        for line in txt_data:
            match = re.match(r'(\w+)\s*:\s*([\d.-]+)', line)
            param_name_txt = match.group(1)
            if "shape" in param_name_txt:
                param_value = float(match.group(2))
                #print("Parameter : %s with value : %s"  %(param_name_txt,param_value))  
                # Replace regions according to mapping
                if "shape_mTauFake" in param_name_txt:
                    var = 0.05
                elif "shape_jTauFake":
                    var = 0.1
                else :
                    var = 1
                param_postfit = 1 + (var * param_value)

                print("Parameter : %s with posfit value : %s"  %(param_name_txt,param_postfit))  


calculate_shape_syst()