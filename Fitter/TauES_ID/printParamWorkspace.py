"""
Date: November 2023
Author: @oponcet
Description: Save Fit Parameters to Text File. Parameters of the fit have been obtained using the `combine -M FitDiagnostics` 
method and the save option. This script has not been used for the results of the final postfit plots because the results of 
the fit with the method `-M FitDiagnostics` differ from those obtained with `-M Multidimfit`, which is the method used to obtain
the scale factors (SFs).
"""


import ROOT

def save_fit_parameters_to_txt(file_name, workspace_name, output_file):
    """
    Opens a ROOT file, accesses a workspace, and writes fit parameters to a text file.

    Parameters:
    - file_name (str): The name of the ROOT file.
    - workspace_name (str): The name of the workspace within the ROOT file.
    - output_file (str): The name of the output text file.

    Returns:
    - None: Returns early if there are issues opening the file or accessing the workspace.
    """

    # Open the ROOT file
    file = ROOT.TFile.Open(file_name)
    if not file or file.IsZombie():
        print("Error opening file")
        return

    # Access the workspace
    workspace = file.Get(workspace_name)
    if not workspace:
        print("Error accessing workspace")
        file.Close()
        return


    # Open a text file to write the parameters
    with open(output_file, 'w') as f:
        # Get the list of parameters from the fit result
        parameters = workspace.floatParsFinal()
        
        # Loop over parameters and write their names and values to the file
        for i in range(parameters.getSize()):
            param = parameters.at(i)
            line = "%s = %s \n" %(param.GetName(),param.getVal())
            f.write(line)

    # Close the ROOT file
    file.Close()


regions = ["DM0", "DM1", "DM10", "DM11"]

outdir = "postfit_2022_postEE"
input_workspace_name = "fit_s"

for r in regions : 
    # Example usage:
    
    input_file_name = "output_2022_postEE/fitDiagnostics.mt_m_vis-%s_mutau_mt65cut_DM_Dt2p5_VSJetMedium_DeepTau-2022_postEE-13TeV.root" %(r)
    output_txt_file = "%s/fit_parameters%s.txt" %(outdir,r)

    save_fit_parameters_to_txt(input_file_name, input_workspace_name, output_txt_file)

