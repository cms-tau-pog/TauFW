#! /usr/bin/env python
"""
Date : October 2023 
Author : @oponcet 
Description :
 - Scan of tes or/and tid SF which is implemented as a rateParamer.
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


# Function to run the fit     
def run_combined_fit(setup, **kwargs):
    #tes_range    = kwargs.get('tes_range',    "0.970,1.030")
    tes_range    = kwargs.get('tes_range',    "%s,%s" %(min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))                         )
    tid_SF_range = kwargs.get('tid_SF_range', "0.7,1.3")
    extratag     = kwargs.get('extratag',     "_DeepTau")
    algo         = kwargs.get('algo',         "--algo=grid --alignEdges=1 --saveFitResult ")
    npts_fit     = kwargs.get('npts_fit',     "--points=7")
    fit_opts     = kwargs.get('fit_opts',     "--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=2 --setRobustFitTolerance=0.001 %s" %(npts_fit))
    xrtd_opts    = kwargs.get('xrtd_opts',    "--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NE")
    cmin_opts    = kwargs.get('cmin_opts',    "--cminFallbackAlgo Minuit2,Migrad,0:0.0001 --cminPreScan"                                                 )
    save_opts    = kwargs.get('save_opts',    "--saveNLL --saveSpecifiedNuis all "                                                                           )
    era          = kwargs.get('era',          "")
    workspace = ""



    # Variable of the fit (usually mvis)
    variable = "m_vis"
    ## For each region defined in scanRegions in the config file 
    for r in setup["observables"]["m_vis"]["scanRegions"]:
        print("Region : "+r)

        # Binelabel for output file of the fit
        BINLABELoutput = "mt_"+variable+"-"+r+setup["tag"]+extratag+"-"+era+"-13TeV"

        # For fit by region create the datacards and the workspace here
        datacardfile = "ztt_mt_m_vis-"+r+setup["tag"]+extratag+"-"+era+"-13TeV"
        print("datacard file for fit by region = %s" %(datacardfile)) 
        # Create workspace 
        os.system("text2workspace.py output_%s/%s.txt" %(era, datacardfile))
        workspace = "output_%s/%s.root" %(era, datacardfile)
        print("Datacard workspace has been created")

        ## FIT ##

        # Fit of the POI for each region defined in the config file 
        # POI = "tes_%s" % (r) # Change your POI here : tes_ or tid_SF_
        # NP = "rgx{.*tid.*}"
        POI = "tid_SF_%s" % (r) # Change your POI here : tes_ or tid_SF_
        NP = "rgx{.*tes.*}"
        print(">>>>>>> "+POI+" fit")
        # you can fit tes_ or tid_SF_ (which is not you POI) if you don't want to include it in the fit.
        # Else it will be combined fit of tes and tid_SF
        POI_OPTS = "-P %s --redefineSignalPOIs %s --setParameterRanges %s=%s -m 90 --setParameters r=1,tes_%s=1,tid_SF_%s=1 --freezeParameters r " % (POI, POI, POI, tes_range, r, r)  # tes_DM
        MultiDimFit_opts = " %s %s %s -n .%s %s %s %s %s --trackParameters %s,rgx{.**.},rgx{.*sf_W_*.}" %(workspace, algo, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts,NP)
        # Fit with combine
        os.system("combine -M MultiDimFit  %s" %(MultiDimFit_opts))
            

    os.system("mv higgsCombine*root output_%s"%era)

# Plot the scan using output file of combined 
def plotScan(setup, **kwargs):
    tid_SF_range = kwargs.get('tid_SF_range', "0.7,1.3")
    extratag     = kwargs.get('extratag',     "_DeepTau")
    era          = kwargs.get('era',          ""        )
    config       = kwargs.get('config',       ""        )

    # Plot 
    # do not forget to change the POI and the range
    os.system("./TauES_ID/plotParabola_POI_region.py -p tid_SF -y %s -e %s -r %s,%s -s -a -c %s" % (era, extratag, 0.7, 1.3, config))
    #os.system("./TauES_ID/plotPostFitScan_POI.py --poi tes -y %s -e %s -r %s,%s -c %s" %(era,extratag,min(setup["TESvariations"]["values"]),max(setup["TESvariations"]["values"]), config))



### main function
def main(args):

    era    = args.era
    config = args.config
    extratag     = "_DeepTau"


    print("Using configuration file: %s"%(args.config))
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    # Generating the datacards for mutau channel
    generate_datacards_mutau(era=era, config=config,extratag=extratag)

    # Run the fit using combine
    run_combined_fit(setup, era=era, config=config)

    # Plots 
    plotScan(setup, era=era, config=config)


###
if __name__ == '__main__':

    argv = sys.argv
    parser = ArgumentParser(prog="makeTESfit", description="execute all steps to run TES fit")
    parser.add_argument('-y', '--era', dest='era', choices=['2016', '2017', '2018', 'UL2016_preVFP','UL2016_postVFP', 'UL2017', 'UL2018','UL2018_v10'], default=['UL2018'], action='store', help="set era")
    parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
    args = parser.parse_args()

    main(args)
    print(">>>\n>>> done\n")
