#! /usr/bin/env python
"""
Date : Sept 2024
Author : @oponcet 
Description :
This script is used to run a FITDiagnotic for TES and tid_S. It take as input the values of the parameter of the fit obtained wit h MultiDimFit in makecombinedfit_TES_SFt.py. The parameters are read from a text file and used in the fit. The fit is done for each region defined in the config file. The fit is done using the combine tool. The output of the fit is saved in a root file. The script also run the PostFitShapeFromWorkspace to get the postfit shape of the fit. 
"""

from distutils import filelist
from distutils.command.config import config
import sys
import os
import yaml
from argparse import ArgumentParser

# Generating the datacards for mutau channel
def generate_datacards_mutau(era, config, extratag):
    print(' >>>>>> Generating datacards for mutau channel')
    os.system("./TauES_ID/harvestDatacards_TES_idSF_MCStat.py -y %s -c %s -e %s "%(era,config,extratag)) 

# Generating the datacards for mumu channel
def generate_datacards_mumu(era, config_mumu, extratag):
    print(' >>>>>> Generating datacards for mumu channel')
    os.system("TauES_ID/harvestDatacards_zmm.py -y %s -c %s -e %s "%(era,config_mumu,extratag)) # Generating the datacards with one statistics uncertianties for all processes

# Merge the datacards between regions for combine fit and return the name of the combined datacard file
def merge_datacards_regions(setup, setup_mumu, config_mumu, era, extratag):
    # Variable of the fit (usually mvis)
    variable = "m_vis"
    print("Observable : "+variable)
    # LABEL used for datacard file
    LABEL = setup["tag"]+extratag+"-"+era+"-13TeV"
    filelist = "" # List of the datacard files to merge in one file combinecards.txt
    # Name of the combined datacard file
    outcombinedfile = "combinecards%s" %(setup["tag"])
    for region in setup["observables"]["m_vis"]["fitRegions"]:
        filelist += region + "=output_"+era+"/ztt_mt_m_vis-"+region+LABEL+".txt "
        os.system("combineCards.py %s >output_%s/%s.txt" % (filelist, era,outcombinedfile))
    #print("filelist : %s") %(filelist) 
    # Add the CR datacard file to the lsit of file to merge if there is CR option
    if str(config_mumu) != 'None':
        LABEL_mumu = setup_mumu["tag"]+extratag+"-"+era+"-13TeV"
        filelist +=  "zmm=output_"+era+"/ztt_mm_m_vis-baseline"+LABEL_mumu+".txt "
        outcombinedfile += "CR"
        os.system("combineCards.py %s >output_%s/%s.txt" % (filelist, era,outcombinedfile))
        print(">>>>>>>>> merging datacards is done ")
    return outcombinedfile



# Merge the datacards between mt regions and Zmm when using Zmm CR and return the name of the CR + region datacard file
def merge_datacards_ZmmCR(setup, setup_mumu, era,extratag,region):
    # datacard of the region to be merged
    datacardfile_region = "ztt_mt_m_vis-"+region+setup["tag"]+extratag+"-"+era+"-13TeV.txt"
    filelist = "%s=output_%s/%s" %(region,era, datacardfile_region)
    LABEL_mumu = setup_mumu["tag"]+extratag+"-"+era+"-13TeV"
    filelist += " Zmm=output_"+era+"/ztt_mm_m_vis-baseline"+LABEL_mumu+".txt "
    print(filelist)
    # Name of the CR + region datacard file
    outCRfile = "ztt_mt_m_vis-%s_zmmCR" %(region)
    # os.system("combineCards.py %s >output_%s/%s.txt" % (filelist, era,outCRfile))
    return outCRfile
    
def run_combined_fit(setup, setup_mumu, option, **kwargs):
    # tes_range    = kwargs.get('tes_range',    "0.930,1.300")
    tes_range    = kwargs.get('tes_range',    "%s,%s" %(min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))                         )
    tid_SF_range = kwargs.get('tid_SF_range', "0.7,1.3") #"0.7,1.1"
    extratag     = kwargs.get('extratag',     "_DeepTau")
    algo         = kwargs.get('algo',         "--algo=grid --alignEdges=1  ")
    npts_fit     = kwargs.get('npts_fit',     "--points=61") ## 66 and 96
    fit_opts     = kwargs.get('fit_opts',     "--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=2 --setRobustFitTolerance=0.00001 %s" %(npts_fit))
    xrtd_opts    = kwargs.get('xrtd_opts',    "--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NE")
    cmin_opts    = kwargs.get('cmin_opts',    "--cminFallbackAlgo Minuit2,Migrad,0:0.0001 --cminPreScan"                                            ) #--cminPreScan
    save_opts    = kwargs.get('save_opts',    "--saveNLL --saveSpecifiedNuis all --saveFitResult"                                                                           )
    era          = kwargs.get('era',          "")
    config_mumu  = kwargs.get('config_mumu',  "")
    workspace = ""

    # Create the workspace for combined fit
    if int(option) > 3:
        # merge datacards regions
        datacardfile = merge_datacards_regions(setup,setup_mumu, config_mumu, era, extratag)
        print("datacard file for combined fit = %s" %(datacardfile)) 
        # Create workspace 
        os.system("text2workspace.py output_%s/%s.txt" %(era, datacardfile))
        workspace = "output_%s/%s.root" %(era, datacardfile)
   
    # Variable of the fit (usually mvis)
    variable = "m_vis"
    ## For each region defined in scanRegions in the config file 
    for r in setup["observables"]["m_vis"]["scanRegions"]:
        print("Region : "+r)

        # Binelabel for output file of the fit
        BINLABELoutput = "mt_"+variable+"-"+r+setup["tag"]+extratag+"-"+era+"-13TeV"

        # For fit by region create the datacards and the workspace here
        if int(option) <= 3 :
            # For CR Zmumu 
            print("config_mumu = %s"  %(config_mumu))
            if str(config_mumu) != 'None':
                # merge datacards regions and CR
                datacardfile = merge_datacards_ZmmCR(setup, setup_mumu, era, extratag, r)
                print("datacard file for fit by region with additionnal CR = %s" %(datacardfile)) 

            else:
                datacardfile = "ztt_mt_m_vis-"+r+setup["tag"]+extratag+"-"+era+"-13TeV"
                print("datacard file for fit by region = %s" %(datacardfile)) 
            # Create workspace 
            # os.system("text2workspace.py output_%s/%s.txt" %(era, datacardfile))
            workspace = "output_%s/%s.root" %(era, datacardfile)
            print("Datacard workspace has been created")

        ## FIT ##

        # Fit of tes_DM by DM with tid_SF as a nuisance parameter 
        if option == '1':
            POI = "tes_%s" % (r)
            NP = "rgx{.*tid.*}"
            # Here you can adjsut the range of the TES to constrain it in the FITDAIGNOSTICS 
            if r == "DM0_pt1" :
                tes_range = "0.840,0.880"
            elif r == "DM0_pt2" :
                tes_range = "0.890,0.920"
            elif r == "DM0_pt3" :
                tes_range = "0.942,0.960"
            elif r == "DM0_pt4" :
                tes_range = "0.942,0.962"
            elif r == "DM1_pt1" :
                tes_range = "0.960,0.980"
            elif r == "DM1_pt2" :
                tes_range = "0.970,0.990"
            elif r == "DM1_pt3" :
                tes_range = "0.982,1.012"
            elif r == "DM1_pt4" :
                tes_range = "0.990,1.010"
            elif r == "DM10_pt1" :
                tes_range = "0.994,1.010"
            elif r == "DM10_pt2" :
                tes_range = "0.970,1.000"
            elif r == "DM10_pt3" :
                tes_range = "0.984,1.010"
            elif r == "DM10_pt4" :
                tes_range = "0.984,1.010"
            elif r == "DM11_pt1":
                tes_range = "0.960,0.980"
            elif r == "DM11_pt2":
                tes_range = "0.930,0.990"
            elif r == "DM11_pt3":
                tes_range = "0.990,1.010"
            elif r == "DM11_pt4":
                tes_range = "1.020,1.030"
            else:
                tes_range = "0.900,1.300"

            # Load the parameters from the text file
            param_file = kwargs.get('param_file', './postfit_%s/FitparameterValues_%s_DeepTau_%s-13TeV_%s.txt' % (era, setup["tag"],era, r))
            params = {}

            with open(param_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:  # Ensure the line is not empty and contains ':'
                        key, value = line.split(':', 1)  # Split into key and value based on ':'
                        key = key.strip()
                        value = float(value.strip())  # Convert value to float

                        if key.startswith('trackedParam_'):
                            key = key[len('trackedParam_'):]

                        params[key] = value
                    else:
                        print(f"Skipping invalid line: {line}")  # Optionally, print a message for invalid lines


            # POSTFIT 
            # Incorporate the parameters from the file into the fit command
            param_opts = ",".join([f"{key}={value}" for key, value in params.items()])
            print("param_opts : %s" %(param_opts))
            POI_OPTS_F = "--saveNLL --setParameters r=1,%s --setParameterRanges tes_%s=%s:tid_SF_%s=%s:sf_W_%s=0.0,10.0 --freezeParameters r" % (param_opts,r,tes_range,r,tid_SF_range,r)  # tes_DM
            MutliFitout = "output_%s/higgsCombine.%s.MultiDimFit.mH90.root" %(era, BINLABELoutput)
            FitDiagnostics_opts = " -m 90  %s %s -n .%s %s %s " %(MutliFitout, POI_OPTS_F, BINLABELoutput, xrtd_opts, cmin_opts)
            os.system("combine -M FitDiagnostics %s --redefineSignalPOIs tes_%s,tid_SF_%s  --plots  " %(FitDiagnostics_opts,r,r))
            print("FitDiagnostics %s : " %(r))

            # Postifit shape:
            outf_postfit = "PostFitShape_%s_%s_%s.root" %(era,setup["tag"],r)
            outf_fit = "fitDiagnostics.mt_m_vis-%s%s_DeepTau-%s-13TeV.root" %(r,setup["tag"],era)
            os.system("PostFitShapesFromWorkspace --output %s --workspace %s -f %s:fit_s --postfit "% (outf_postfit, workspace, outf_fit))
            # outf_postfit = "PostFitShape_%s_%s_%s.root" %(era,setup["tag"],r)
            # outf_fit = "output_UL2018_v10/higgsCombine.mt_m_vis-%s%s_DeepTau-%s-13TeV.MultiDimFit.mH90.root" %(r,setup["tag"],era)
            # os.system("PostFitShapesFromWorkspace --output %s --workspace %s -f %s:w --postfit "% (outf_postfit, workspace, outf_fit))
        # Fit of tid_SF_DM by DM with tes as a nuisance parameter

        else:
            continue

    os.system("mv higgsCombine*root output_%s"%era)
    os.system("mv *.root output_%s"%era)
    os.system("mv *.png output_%s"%era)

    

# Plot the scan using output file of combined 
def plotScan(setup, setup_mumu, option, **kwargs):
    tid_SF_range = kwargs.get('tid_SF_range', "0.4,1.6")
    extratag     = kwargs.get('extratag',     "_DeepTau")
    era          = kwargs.get('era',          ""        )
    config       = kwargs.get('config',       ""        )
    # Plot 

    if option == '2' or option == '4'  :
        print(">>> Plot parabola")
        os.system("./TauES_ID/plotParabola_POI_region.py -p tid_SF -y %s -e %s  -s -a -c %s"% (era, extratag, config))
        os.system("./TauES_ID/plotPostFitScan_POI.py --poi tid_SF -y %s -e %s -r %s,%s -c %s" %(era,extratag,min(tid_SF_range),max(tid_SF_range), config))

    elif option == '1' or option == '5' :
        print(">>> Plot parabola")
        os.system("./TauES_ID/plotParabola_POI_region.py -p tes -y %s -e %s -r %s,%s -s -a -c %s " % (era, extratag, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]), config)) # -b
        os.system("./TauES_ID/plotPostFitScan_POI.py --poi tes -y %s -e %s -r %s,%s -c %s" %(era,extratag,min(setup["TESvariations"]["values"]),max(setup["TESvariations"]["values"]), config))

    else:
        print(" No output plot...")






### main function
def main(args):

    era    = args.era
    config = args.config
    config_mumu = args.config_mumu 
    option = args.option
    extratag     = "_DeepTau"


    print("Using configuration file: %s"%(args.config))
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    if config_mumu != 'None':
        print("Using configuration file for mumu: %s"%(args.config_mumu))
        with open(args.config_mumu, 'r') as file_mumu:
            setup_mumu = yaml.safe_load(file_mumu)
    else: 
        setup_mumu = 0

    # # Generating the datacards for mutau channel
    # generate_datacards_mutau(era=era, config=config,extratag=extratag)

    # Generating the datacards for mumu channel
    # if str(config_mumu) != 'None':
        # generate_datacards_mumu(era=era, config_mumu=config_mumu,extratag=extratag)

    # Run the fit using combine with the different options 
    run_combined_fit(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option)

    # # Plots 
    # plotScan(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option)


###
if __name__ == '__main__':

    argv = sys.argv
    parser = ArgumentParser(prog="makeTESfit", description="execute all steps to run TES fit")
    parser.add_argument('-y', '--era', dest='era', choices=['2016', '2017', '2018', 'UL2016_preVFP','UL2016_postVFP', 'UL2017', 'UL2018','UL2018_v10','2022_postEE','2022_preEE'], default=['UL2018'], action='store', help="set era")
    parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
    parser.add_argument('-o', '--option', dest='option', choices=['1', '2', '3', '4', '5','6'], default='1', action='store',
                        help="set option : Scan of tes and tid SF is profiled (-o 1) ;  Scan of tid SF and tes is profiled (-o 2) ; 2D scan of tes and tid SF (-o 3) \
                        ; Scan of tid SF, tid SF and tes of other regions are profiled POIs (-o 4); Scan of tes, tid SF and tes of other regions are profiled POIs(-o 5)\
                        ; 2D scan of tes and tid SF and tes of other regions are profiled POIs (-o 6) ")
    parser.add_argument('-cmm', '--config_mumu', dest='config_mumu', type=str, default='None', action='store', help="set config file containing sample & fit setup")

    args = parser.parse_args()

    main(args)
    print(">>>\n>>> done\n")