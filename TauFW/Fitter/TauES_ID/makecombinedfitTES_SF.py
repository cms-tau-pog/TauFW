#! /usr/bin/env python
"""
Date : July 2023 
Author : @oponcet 
Description :
 - Scan of tes and tid SF is implemented as a rateParamer wich is profiled. Ex usage : Scan by DM (option 1)
 - Scan of tid SF and tes need to be set as POI with redefineSignalPOIs to include it in the fit. Ex usage : Scan by DM (option 2) 
 - 2D scan of tes and tid SF. Ex usage : Scan by DM (option 3)
 - Scan of tid SF, tid SF and tes of other regions are profiled POIs. Ex usage : Fit tes by DM and tid SF by pt (option 4)
 - Scan of tes, tid SF and tes of other regions are profiled POIs. Ex usage : Fit tes by DM and tid SF by pt (option 5)
 - 2D scan of tes and tid SF and tes of other regions are profiled POIs. Ex usage : Fit tes by DM and tid SF by pt (option 6) 
"""

from distutils import filelist
from distutils.command.config import config
import sys
import os
import yaml
from argparse import ArgumentParser

# Generating the datacards for mutau channel
def generate_datacards_mutau(era, config, extratag,input_dir):
    print(' >>>>>> Generating datacards for mutau channel')
    os.system("./TauES_ID/harvestDatacards_TES_idSF_MCStat.py -y %s -c %s -e %s -i %s"%(era,config,extratag,input_dir)) 

# Generating the datacards for mumu channel
def generate_datacards_mumu(era, config_mumu, extratag, output_dir):
    print(' >>>>>> Generating datacards for mumu channel')
    os.system("TauES_ID/harvestDatacards_zmm.py -y %s -c %s -e %s -o %s"%(era,config_mumu,extratag,output_dir)) # Generating the datacards with one statistics uncertianties for all processes

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
def merge_datacards_ZmmCR(setup, setup_mumu, era,extratag,region, output_dir):
    # datacard of the region to be merged
    datacardfile_region = "ztt_mt_m_vis-"+region+setup["tag"]+extratag+"-"+era+"-13TeV.txt"
    filelist = f"%s={output_dir}/%s" %(region, datacardfile_region)
    LABEL_mumu = setup_mumu["tag"]+extratag+"-"+era+"-13TeV"
    filelist += " Zmm="+output_dir+"/ztt_mm_m_vis-baseline"+LABEL_mumu+".txt "
    print(filelist)
    # Name of the CR + region datacard file
    outCRfile = "ztt_mt_m_vis-%s_zmmCR" %(region)
    os.system(f"combineCards.py %s >{output_dir}/%s.txt" % (filelist, outCRfile))
    return outCRfile
    
def run_combined_fit(setup, setup_mumu, option, **kwargs):
    #tes_range    = kwargs.get('tes_range',    "1.000,1.000")
    tes_range    = kwargs.get('tes_range',    "%s,%s" %(min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))                         )
    tid_SF_range = kwargs.get('tid_SF_range', "0.5,1.6")
    extratag     = kwargs.get('extratag',     "_DeepTau")
    algo         = kwargs.get('algo',         "--algo=grid --alignEdges=1  ")
    npts_fit     = kwargs.get('npts_fit',     "--points=96") ## 66
    fit_opts     = kwargs.get('fit_opts',     "--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=2 --setRobustFitTolerance=0.001 %s" %(npts_fit))
    xrtd_opts    = kwargs.get('xrtd_opts',    "--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NE")
    cmin_opts    = kwargs.get('cmin_opts',    "--cminFallbackAlgo Minuit2,Migrad,0:0.0001 --cminPreScan"                                                 )
    save_opts    = kwargs.get('save_opts',    "--saveNLL --saveSpecifiedNuis all --saveFitResult"                                                                           )
    era          = kwargs.get('era',          "")
    config_mumu  = kwargs.get('config_mumu',  "")
    output_dir   = kwargs.get('input_dir')
    output_dir = output_dir.replace('input', 'output')
    output_dir = os.path.join(output_dir, era)
    workspace = ""

    # Create the workspace for combined fit
    if int(option) > 3:
        # merge datacards regions
        datacardfile = merge_datacards_regions(setup,setup_mumu, config_mumu, era, extratag)
        print("datacard file for combined fit = %s" %(datacardfile)) 
        # Create workspace 
        os.system(f"text2workspace.py {output_dir}/{datacardfile}.txt")
        workspace = f"{output_dir}/{datacardfile}.root"
   
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
                datacardfile = merge_datacards_ZmmCR(setup, setup_mumu, era, extratag, r, output_dir)
                print("datacard file for fit by region with additionnal CR = %s" %(datacardfile)) 

            else:
                datacardfile = "ztt_mt_m_vis-"+r+setup["tag"]+extratag+"-"+era+"-13TeV"
                print("datacard file for fit by region = %s" %(datacardfile)) 
            # Create workspace 
            os.system(f"text2workspace.py {output_dir}/{datacardfile}.txt")
            workspace = f"{output_dir}/{datacardfile}.root"
            print("Datacard workspace has been created")

        ## FIT ##

        # Fit of tes_DM by DM with tid_SF as a nuisance parameter 
        if option == '1':
            POI = "tes_%s" % (r)
            NP = "rgx{.*tid.*}"
            print(">>>>>>> "+POI+" fit")
            #POI_OPTS = "-P %s --setParameterRanges %s=%s:tid_SF_%s=%s --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r,tid_SF_%s  --redefineSignalPOIs tid_SF_%s" % (POI, POI, tes_range, r,tid_SF_range,r,r)  # tes_DM
            if POI == "tes_DM10":
                tes_range = "0.950,1.030"
            #tes_range = "0.850,1.030"
            POI_OPTS = "--saveWorkspace -P %s --setParameterRanges %s=%s:tid_SF_%s=%s:sf_W_%s=0.0,10.0 --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r  --redefineSignalPOIs tid_SF_%s --floatOtherPOIs=1" % (POI, POI, tes_range, r,tid_SF_range,r,r)  # tes_DM
            MultiDimFit_opts = " -m 90  %s %s %s -n .%s %s %s %s %s --trackParameters %s,rgx{.**.},rgx{.*sf_W_*.} --saveInactivePOI=1" %(workspace, algo, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts,NP)
            #MutliFitout = "higgsCombine.%s.MultiDimFit.mH90.root" %(BINLABELoutput)
            
            # POI_OPTS_F = " --snapshotName %s --saveNLL --setParameterRanges %s=%s:tid_SF_%s=%s --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r  --redefineSignalPOIs tes_%s " % ( "MultiDimFit",POI, tes_range, r,tid_SF_range,r)  # tes_DM
            # FitDiagnostics_opts = " -m 90  %s %s -n .%s %s %s " %(MutliFitout, POI_OPTS_F, BINLABELoutput, xrtd_opts, cmin_opts)
            # Fit with combine
            print("MultidimFit %s : " %(r), '\t', MultiDimFit_opts)
            os.system("combine -M MultiDimFit  %s" %(MultiDimFit_opts))
           
            # print("MultidimFit %s : " %(r))
            # MultiDimFit_opts = " -m 90  %s %s -n .%s %s %s %s %s --trackParameters %s,rgx{.**.},rgx{.*sf_W_*.} --saveInactivePOI=1" %(workspace, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts,NP)
            # os.system("combine -M MultiDimFit %s " %(FitDiagnostics_opts))


            # print("FitDiagnostics %s : " %(r))
            # os.system("combine -M FitDiagnostics  %s --plots  " %(FitDiagnostics_opts))

            # ##Impact plot
            # POI_OPTS_I = "--redefineSignalPOIs %s --setParameterRanges %s=%s:tid_SF_%s=%s -m 90 --setParameters r=1,tes_%s=1,tid_SF_%s=1 --freezeParameters r " % (POI, POI, tes_range, r,tid_SF_range,r,r)
            # os.system("combineTool.py -M Impacts -n %s -d %s %s  --doInitialFit"%(BINLABELoutput, workspace, POI_OPTS_I))
            # os.system("combineTool.py -M Impacts -n %s -d %s %s  --doFits --parallel 4"%(BINLABELoutput, workspace, POI_OPTS_I))
            # os.system("combineTool.py -M Impacts  -n %s -d %s  %s -o postfit/impacts_%s.json"%(BINLABELoutput, workspace, POI_OPTS_I, BINLABELoutput))
            # os.system("plotImpacts.py -i postfit/impacts_%s.json -o postfit/impacts_%s.json"%(BINLABELoutput,BINLABELoutput))
            # os.system("convert -density 160 -trim postfit/impacts_%s.json.pdf[0] -quality 100 postfit/impacts_%s.png"%(BINLABELoutput,BINLABELoutput))
            # Postifit shape:
            # outf_postfit = "PostFitShape_%s_%s_%s.root" %(era,setup["tag"],r)
            # outf_fit = "fitDiagnostics.mt_m_vis-%s%s_DeepTau-%s-13TeV.root" %(r,setup["tag"],era)
            # os.system("PostFitShapesFromWorkspace --output %s --workspace %s -f %s:fit_s --postfit "% (outf_postfit, workspace, outf_fit))
            # outf_postfit = "PostFitShape_%s_%s_%s.root" %(era,setup["tag"],r)
            # outf_fit = "higgsCombine.mt_m_vis-%s%s_DeepTau-%s-13TeV.MultiDimFit.mH90.root" %(r,setup["tag"],era)
            # os.system("PostFitShapesFromWorkspace --output %s --workspace %s -f %s:w --postfit "% (outf_postfit, workspace, outf_fit))
        # Fit of tid_SF_DM by DM with tes as a nuisance parameter
        elif option == '2':
            POI = "tid_SF_%s" % (r)
            NP = "rgx{.*tid.*}" 
            print(">>>>>>> Scan of "+POI)
            #POI_OPTS = "-P %s  --setParameterRanges %s=%s:tes_%s=%s -m 90 --setParameters r=1,rgx{.*tid.*}=1,rgx{.*tes.*}=1 --freezeParameters r,tes_%s --redefineSignalPOIs tes_%s --floatOtherPOIs 1" % (POI, POI, tid_SF_range,r,tes_range,r,r)  # tes_DM
            POI_OPTS = "-P %s --redefineSignalPOIs tes_%s --setParameterRanges %s=%s:tes_%s=%s -m 90 --setParameters r=1,rgx{.*tid.*}=1,rgx{.*tes.*}=1 --freezeParameters r --floatOtherPOIs=1" % (POI,r, POI, tid_SF_range, r,tes_range)  # tes_DM
            MultiDimFit_opts = " %s %s %s -n .%s %s %s %s %s --trackParameters rgx{.*tid.*},rgx{.*W.*},rgx{.*dy.*} --saveInactivePOI=1 " %(workspace, algo, POI_OPTS, BINLABELoutput,fit_opts, xrtd_opts, cmin_opts, save_opts)
            print("MultidimFit %s : " %(r), '\t', MultiDimFit_opts)
            os.system("combine -M MultiDimFit %s " %(MultiDimFit_opts))

        # 2D Fit of tes_DM and tid_SF_DM by DM, both are pois
        elif option == '3':  
            print(">>>>>>> Fit of tid_SF_"+r+" and tes_"+r)
            POI1 = "tid_SF_%s" % (r)
            POI2 = "tes_%s" % (r)
            POI_OPTS = "-P %s -P %s --setParameterRanges %s=%s:%s=%s  --setParameters r=1,%s=1,%s=1 --freezeParameters r " % (POI2, POI1, POI2, tes_range, POI1,tid_SF_range, POI2, POI1)
            MultiDimFit_opts = " -m 90 %s %s %s -n .%s %s %s %s %s --trackParameters rgx{.*tid.*},rgx{.*W.*},rgx{.*dy.*}" %(workspace, algo, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts)
            os.system("combine -M MultiDimFit  %s " %(MultiDimFit_opts))

        ### Fit with combined datacards  tes_DM0,tes_DM1,tes_DM10,tes_DM11 
        ## Fit of tid_SF in its regions with tes_region and other tid_SF_regions as nuisance parameters    tes_DM0,tes_DM1,tes_DM10,tes_DM11
        elif option == '4': 
            print(">>>>>>> Fit of tid_SF_"+r)
            POI_OPTS = "-P tid_SF_%s --redefineSignalPOIs tes_DM0_pt1,tes_DM0_pt2,tes_DM1_pt1,tes_DM1_pt2,tes_DM10_pt1,tes_DM10_pt2,tes_DM11_pt1,tes_DM11_pt2  --setParameterRanges rgx{.*tid.*}=%s:rgx{.*tes.*}=%s -m 90 --setParameters r=1,rgx{.*tes.*}=1 --freezeParameters r --floatOtherPOIs=1 " %(r, tid_SF_range,tes_range)
            MultiDimFit_opts = "%s %s %s -n .%s %s %s %s %s  --trackParameters rgx{.*tid.*},rgx{.*W.*},rgx{.*dy.*} --saveInactivePOI=1" %(workspace, algo, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts)
            os.system("combine -M MultiDimFit %s" %(MultiDimFit_opts))

        ## Fit of tes in DM regions with tid_SF and other tes_DM as nuisance parameters  
        elif option == '5':
            print(">>>>>>> simultaneous fit of tid_SF in pt bins and tes_"+r + " in DM")
            POI_OPTS = "-P tes_%s --redefineSignalPOIs tes_DM0,tes_DM1,tes_DM10,tes_DM11,tid_SF_DM0,tid_SF_DM1,tid_SF_DM10,tid_SF_DM11 --setParameterRanges rgx{.*tid.*}=%s:rgx{.*tes.*}=%s -m 90 --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r --floatOtherPOIs=1" %(r, tid_SF_range, tes_range)
            MultiDimFit_opts = "%s %s %s -n .%s %s %s %s %s --trackParameters rgx{.**.} --saveInactivePOI=1"  %(workspace, algo, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts)
            os.system("combine -M MultiDimFit %s " %(MultiDimFit_opts))

        ### 2D Fit of tes_DM and tid_SF in DM and pt regions with others tid_SF and tes_DM as nuisance parameter
        elif option == '6':
            #for each decay mode
            for r in setup['tidRegions']: #["DM0","DM1","DM10","DM11"]
                for dm in setup['tesRegions']:
                    print("Region : "+r)
                    print(">>>>>>> simultaneous fit of tes_" +r + " in pt bins and tes_"+r + "in DM")
                    POI_OPTS = "-P tid_SF_%s -P tes_%s --setParameterRanges rgx{.*tid.*}=%s:rgx{.*tes.*}=%s -m 90 --setParameters r=1 --freezeParameters r" %(r,dm, tid_SF_range, tes_range)
                    MultiDimFit_opts = "-m 90 %s %s %s -n .%s %s %s %s %s  " %(workspace, algo, POI_OPTS, BINLABELoutput, fit_opts, xrtd_opts, cmin_opts, save_opts)
                    os.system("combine -M MultiDimFit %s" %(MultiDimFit_opts))

        else:
            continue

    os.system("mv higgsCombine*root %s" %output_dir)
    os.system("mv *.root %s" %output_dir)
    os.system("mv *.png %s"%output_dir)

    

# Plot the scan using output file of combined 
def plotScan(setup, setup_mumu, option, **kwargs):
    tid_SF_range = kwargs.get('tid_SF_range', "0.4,1.6")
    extratag     = kwargs.get('extratag',     "_DeepTau")
    era          = kwargs.get('era',          ""        )
    config       = kwargs.get('config',       ""        )
    indir        = kwargs.get('indir', "")
    # Plot 

    if option == '2' or option == '4'  :
        print(">>> Plot parabola")
        os.system("./TauES_ID/plotParabola_POI_region.py -p tid_SF -y %s -e %s  -s -a -c %s -i %s"% (era, extratag, config, indir))
        os.system("./TauES_ID/plotPostFitScan_POI.py --poi tid_SF -y %s -e %s -r %s,%s -c %s -i %s" %(era,extratag,min(tid_SF_range),max(tid_SF_range), config, indir))

    elif option == '1' or option == '5' :
        print('indir: ', indir)
        print(">>> Plot parabola")
        os.system("./TauES_ID/plotParabola_POI_region.py -p tes -y %s -e %s -r %s,%s -s -a -c %s -i %s" % (era, extratag, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]), config, indir))
        os.system("./TauES_ID/plotPostFitScan_POI.py --poi tes -y %s -e %s -r %s,%s -c %s -i %s" %(era,extratag,min(setup["TESvariations"]["values"]),max(setup["TESvariations"]["values"]), config, indir))

    else:
        print(" No output plot...")






### main function
def main(args):

    era    = args.era
    config = args.config
    config_mumu = args.config_mumu 
    option = args.option
    extratag     = "_DeepTau"
    input_dir = args.input_dir

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
    generate_datacards_mutau(era=era, config=config,extratag=extratag, input_dir=input_dir)

    # Generating the datacards for mumu channel
    if str(config_mumu) != 'None':
        output_dir=input_dir.replace('input', 'output')
        output_dir = os.path.join(output_dir, era)
        generate_datacards_mumu(era=era, config_mumu=config_mumu,extratag=extratag, output_dir=output_dir)

    # Run the fit using combine with the different options 
    run_combined_fit(setup,setup_mumu, era=era, input_dir=input_dir, config=config, config_mumu=config_mumu, option=option)

    # Plots
    plotScan(setup,setup_mumu, era=era, config=config, config_mumu=config_mumu, option=option, indir=output_dir)


###
if __name__ == '__main__':

    argv = sys.argv
    parser = ArgumentParser(prog="makeTESfit", description="execute all steps to run TES fit")
    parser.add_argument('-y', '--era', dest='era', default=['UL2018'], action='store', help="set era")
    parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
    parser.add_argument('-o', '--option', dest='option', choices=['1', '2', '3', '4', '5','6'], default='1', action='store',
                        help="set option : Scan of tes and tid SF is profiled (-o 1) ;  Scan of tid SF and tes is profiled (-o 2) ; 2D scan of tes and tid SF (-o 3) \
                        ; Scan of tid SF, tid SF and tes of other regions are profiled POIs (-o 4); Scan of tes, tid SF and tes of other regions are profiled POIs(-o 5)\
                        ; 2D scan of tes and tid SF and tes of other regions are profiled POIs (-o 6) ")
    parser.add_argument('-cmm', '--config_mumu', dest='config_mumu', type=str, default='None', action='store', help="set config file containing sample & fit setup")
    parser.add_argument('-i', '--input_dir', dest='input_dir', type=str, help="inputdir containing root files for datacard")
    args = parser.parse_args()

    main(args)
    print(">>>\n>>> done\n")
