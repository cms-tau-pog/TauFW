"""
Date : May 2022 
Description :
 - fit of tes with others parameters free (option 1),
 - fit of tid_SF with other parameters free (option 2) 
 - combined fit of tes and tid_SF_DM with other parameters free (option 3)
 - Scan of tid_SF_pt for combined fit of tes_DM and tid_SF_pt (option 4)
 - Scan of tes_DM for combined fit of tes_DM and tid_SF_pt (option 5)
 - 2D Scan of tid_SF_pt et tes_DM for combined fit of tes_DM and tid_SF_pt (option 6)   
Add the option -t -1 to MultiDimFit to realize the fit with an asimov dataset
and add the option -saveToys to save the asimovdataset in higgsCombine*.root file. 
Note that the name of the generated file will be changed with this option 
(seed will be added at the end of the file name) -> use os.rename line 
Add the option --fastScan to do a fit without any systemetic
Add the option --freezeNuisanceGroups=group to do a fit a group of nuisance parameters
frozen, the groups are defined in harvestDatacards_TES_idSF_MCStat.py
"""
from distutils import filelist
from distutils.command.config import config
import sys
import os
import yaml
from argparse import ArgumentParser


### Fitting function using combine tool
def combinedfit(setup, option, **kwargs):
    tes_range    = kwargs.get('tes_range',    "%s,%s" %(min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))                         )
    tid_SF_range = kwargs.get('tid_SF_range', "0.4,1.6"                                                                                                       )
    extratag     = kwargs.get('extratag',     "_DeepTau"                                                                                                      )
    algo         = kwargs.get('algo',         "--algo=grid --alignEdges=1 --saveFitResult "                                                                   )# --saveWorkspace
    npts_fit     = kwargs.get('npts_fit',     "--points=61"                                                                                                  )
    fit_opts     = kwargs.get('fit_opts',     "--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=2 --setRobustFitTolerance=0.001 %s" %(npts_fit))
    xrtd_opts    = kwargs.get('xrtd_opts',    "--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND"                            )
    cmin_opts    = kwargs.get('cmin_opts',    "--cminFallbackAlgo Minuit2,Migrad,0:0.0001 --cminPreScan"                                                 )
    save_opts    = kwargs.get('save_opts',     "--saveNLL --saveSpecifiedNuis all "                                                                           )
    era          = kwargs.get('era',          ""                                                                                                              )
    config       = kwargs.get('config',       ""                                                                                                              )

    ### DM regions : tes and tid_SF
    if int(option) < '7':
    # Generating datacards
        print('Generating datacards')
        os.system("./TauES_ID/harvestDatacards_TES_idSF_MCStat.py -y %s -c %s -e %s "%(era,config,extratag)) # Generating the datacards with one statistics uncertianties for all processes
       
    else:
        print("This option does not exist... try --help")


    # Variable like m_vis 
    for v in setup["observables"]:
        variable = setup["observables"][v]
        print("Observable : "+v)

        ##Combining the datacards to do the fit simultaneously with all the parameters
        if  int(option) > 2: 
            LABEL = setup["tag"]+extratag+"-"+era+"-13TeV"
            filelist = "" # List of the datacard files to merge in one file combinecards.txt
            for region in variable["fitRegions"]:
                filelist += region + "=output_"+era+"/ztt_mt_m_vis-"+region+LABEL+".txt "
            #print("filelist : %s") %(filelist) 
            os.system("combineCards.py %s >output_%s/combinecards%s.txt" % (filelist, era,setup["tag"]))
            print(">>>>>>>>> merging datacards is done ")
            os.system("text2workspace.py output_%s/combinecards%s.txt " % (era,setup["tag"]))

        ## For each region defined in scanRegions in the config file 
        for r in variable["scanRegions"]:
            print("Region : "+r)

            # Global variables
            BINLABEL = "mt_"+v+"-"+r+setup["tag"]+extratag+"-"+era+"-13TeV"
            WORKSPACE = "output_"+era+"/ztt_"+BINLABEL+".root"

            # Fit of tes_DM by DM with tid_SF as a nuisance parameter 
            if option == '1':
                POI = "tes_%s" % (r)
                NP = "rgx{.*tid.*}"
                print(">>>>>>>"+POI+" fit")
                POI_OPTS = "-P %s --setParameterRanges %s=%s:tid_SF_%s=%s -m 90 --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r " % (POI, POI, tes_range, r,tid_SF_range)  # tes_DM
                os.system("text2workspace.py output_%s/ztt_%s.txt" %(era, BINLABEL))
                os.system("combine -M MultiDimFit  %s %s %s -n .%s %s %s %s %s --trackParameters %s" %(WORKSPACE, algo, POI_OPTS, BINLABEL, fit_opts, xrtd_opts, cmin_opts, save_opts,NP))
                # ##Impact plot
                # POI_OPTS_I = "-P %s --setParameterRanges %s=%s:tid_SF_%s=%s -m 90 --setParameters r=1 --freezeParameters r "%(POI, POI, tes_range, r,tid_SF_range)
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs %s %s %s %s %s  --doInitialFit"%(BINLABEL, WORKSPACE, POI,fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts))
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs %s %s %s %s %s --doFits --parallel 4"%(BINLABEL, WORKSPACE, POI,fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts))
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs %s %s %s %s %s -o postfit/impacts_%s.json"%(BINLABEL, WORKSPACE,POI, fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts, BINLABEL))
                # os.system("plotImpacts.py -i postfit/impacts_%s.json -o postfit/impacts_%s.json"%(BINLABEL,BINLABEL))
                # os.system("convert -density 160 -trim postfit/impacts_%s.json.pdf[0] -quality 100 postfit/impacts_%s.png"%(BINLABEL,BINLABEL))
                
            # Fit of tid_SF_DM by DM with tes as a nuisance parameter
            elif option == '2':
                POI = "tid_SF_%s" % (r)
                NP = "rgx{.*tid.*}" 
                print(">>>>>>> tid_"+r+" fit")
                POI_OPTS = "-P %s --setParameterRanges %s=%s:tes_%s=%s -m 90 --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r " % (POI, POI, tid_SF_range, r,tid_SF_range)  # tes_DM
                os.system("text2workspace.py output_%s/ztt_%s.txt" %(era, BINLABEL))
                os.system("combine -M MultiDimFit %s %s %s -n .%s %s %s %s %s --trackParameters %s" %(WORKSPACE, algo, POI_OPTS, BINLABEL, fit_opts, xrtd_opts, cmin_opts, save_opts, NP))
                 ##Impact plot
                # POI_OPTS_I = "-P %s --setParameterRanges %s=%s:tes_%s=%s -m 90 --setParameters r=1 --freezeParameters r %s"%(POI, POI,tid_SF_range, r,tes_range,r)
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs %s %s %s %s %s  --doInitialFit"%(BINLABEL, WORKSPACE, POI,fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts))
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs %s %s %s %s %s --doFits --parallel 4"%(BINLABEL, WORKSPACE, POI,fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts))
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs %s %s %s %s %s -o postfit/impacts_%s.json"%(BINLABEL, WORKSPACE,POI, fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts, BINLABEL))
                # os.system("plotImpacts.py -i postfit/impacts_%s.json -o postfit/impacts_%s.json"%(BINLABEL,BINLABEL))
                # os.system("convert -density 160 -trim postfit/impacts_%s.json.pdf[0] -quality 100 postfit/impacts_%s.png"%(BINLABEL,BINLABEL))
                


            # 2D Fit of tes_DM and tid_SF_DM by DM, both are pois
            elif option == '3':  
                print(">>>>>>> Fit of tid_SF_"+r+" and tes_"+r)
                POI1 = "tid_SF_%s" % (r)
                POI2 = "tes_%s" % (r)
                POI_OPTS = "-P %s -P %s --setParameterRanges %s=%s:%s=%s -m 90 --setParameters r=1,%s=1,%s=1 --freezeParameters r " % (POI2, POI1, POI2, tes_range, POI1,tid_SF_range, POI2, POI1)
                os.system("text2workspace.py output_%s/ztt_%s.txt" %(era, BINLABEL))
                os.system("combine -M MultiDimFit %s %s %s -n .%s %s %s %s %s " %(WORKSPACE, algo, POI_OPTS, BINLABEL, fit_opts, xrtd_opts, cmin_opts, save_opts))


            ### Fit with combined datacards 
            ## Fit of tid_SF in its regions with tes_region and other tid_SF_regions as nuisance parameters    tes_DM0,tes_DM1,tes_DM10,tes_DM11
            elif option == '4': 
                print(">>>>>>> Fit of tid_SF_"+r)
                POI_OPTS = "-P tid_SF_%s --redefineSignalPOIs tes_DM0,tes_DM1,tes_DM10,tes_DM11 --setParameterRanges rgx{.*tid.*}=%s:rgx{.*tes.*}=%s -m 90 --setParameters  r=1,rgx{.*tes.*}=1 --freezeParameters r,var{.*tes.*} --floatOtherPOIs=1" %(r, tid_SF_range,tes_range)
                WORKSPACE = "output_"+era+"/combinecards%s.root"%(setup["tag"])
                os.system("combine -M MultiDimFit %s %s %s -n .%s %s %s %s %s  --trackParameters rgx{.*tid.*} --saveInactivePOI=1" %(WORKSPACE, algo, POI_OPTS, BINLABEL, fit_opts, xrtd_opts, cmin_opts, save_opts))
                # POI_OPTS_I = "-P tid_SF_%s --setParameterRanges tid_SF_%s=%s -m 90 --setParameters r=1 --freezeParameters r" %(r,r, tid_SF_range)
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs tid_SF_%s %s %s %s %s  --doInitialFit"%(BINLABEL, WORKSPACE, r,fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts))
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs tid_SF_%s %s %s %s %s --doFits --parallel 4"%(BINLABEL, WORKSPACE, r,fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts))
                # os.system("combineTool.py -M Impacts -n %s -d %s --redefineSignalPOIs tid_SF_%s %s %s %s %s -o postfit/impacts_%s.json"%(BINLABEL, WORKSPACE,r, fit_opts, POI_OPTS_I, xrtd_opts, cmin_opts, BINLABEL))
                # os.system("plotImpacts.py -i postfit/impacts_%s.json -o postfit/impacts_%s.json"%(BINLABEL,BINLABEL))
                # os.system("convert -density 160 -trim postfit/impacts_%s.json.pdf[0] -quality 100 postfit/impacts_%s.png"%(BINLABEL,BINLABEL))


            ## Fit of tes in DM regions with tid_SF and other tes_DM as nuisance parameters  
            elif option == '5':
                print(">>>>>>> simultaneous fit of tid_SF in pt bins and tes_"+r + " in DM")
                POI_OPTS = "-P tes_%s --redefineSignalPOIs tes_DM0,tes_DM1,tes_DM10,tes_DM11 --setParameterRanges rgx{.*tid.*}=%s:rgx{.*tes.*}=%s -m 90 --setParameters r=1,rgx{.*tes.*}=1,rgx{.*tid.*}=1 --freezeParameters r,rgx{.*tid.*} --floatOtherPOIs=1" %(r, tid_SF_range, tes_range)
                WORKSPACE = "output_"+era+"/combinecards%s.root"%(setup["tag"])
                os.system("combine -M MultiDimFit %s %s %s -n .%s %s %s %s %s --trackParameters rgx{.*tid.*} --saveInactivePOI=1" %(WORKSPACE, algo, POI_OPTS, BINLABEL, fit_opts, xrtd_opts, cmin_opts, save_opts))
                # # Add this when addind -saveToys option to combine
                # print("higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.123456.root")
                # os.rename("higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.123456.root", "higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.root")
                # #os.rename("higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.GenerateOnly.mH90.123456.root", "higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.root")

            ### 2D Fit of tes_DM and tid_SF in DM and pt regions with others tid_SF and tes_DM as nuisance parameter
            elif option == '6':
                #for each decay mode
                for r in setup['tidRegions']: #["DM0","DM1","DM10","DM11"]
                    for dm in setup['tesRegions']:
                        BINLABEL = "mt_"+v+"-"+r+dm+setup["tag"]+extratag+"-"+era+"-13TeV"
                        print("Region : "+r)
                        print(">>>>>>> simultaneous fit of tes_" +r + " in pt bins and tes_"+r + "in DM")
                        POI_OPTS = "-P tid_SF_%s -P tes_%s --setParameterRanges rgx{.*tid.*}=%s:rgx{.*tes.*}=%s -m 90 --setParameters r=1 --freezeParameters r" %(r,dm, tid_SF_range, tes_range)
                        WORKSPACE = "output_"+era+"/combinecards%s.root"%(setup["tag"])
                        os.system("combine -M MultiDimFit %s %s %s -n .%s %s %s %s %s " %(WORKSPACE, algo, POI_OPTS, BINLABEL, fit_opts, xrtd_opts, cmin_opts, save_opts))

            else:
                continue

    os.system("mv higgsCombine*root output_%s"%era)

    ## Plot 

    if option == '2' or option == '4' :
      print(">>> Plot parabola")
      os.system("./TauES_ID/plotParabola_POI_region.py -p tid_SF -y %s -e %s -r %s,%s -s -a -c %s"% (era, extratag, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]), config))
      os.system("./TauES_ID/plotPostFitScan_POI.py --poi tid_SF -y %s -e %s -r %s,%s -c %s" %(era,extratag,min(tid_SF_range),max(tid_SF_range), config))

    elif option == '1' or option == '5' :
        print(">>> Plot parabola")
        os.system("./TauES_ID/plotParabola_POI_region.py -p tes -y %s -e %s -r %s,%s -s -a -c %s" % (era, extratag, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]), config))
        os.system("./TauES_ID/plotPostFitScan_POI.py --poi tes -y %s -e %s -r %s,%s -c %s" %(era,extratag,min(setup["TESvariations"]["values"]),max(setup["TESvariations"]["values"]), config))

    else:
        print(" No output plot...")
      

            # Add this when addind -saveToys option to combine
            # print("higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.123456.root")
            # os.rename("higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.123456.root", "higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.root")
            # os.rename("higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.GenerateOnly.mH90.123456.root", "higgsCombine.mt_"+v+"-"+r+setup["tag"]+"_DeepTau-UL2018-13TeV.MultiDimFit.mH90.root")

 


### main function
def main(args):

    print("Using configuration file: %s")%(args.config)
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    era    = args.era
    config = args.config
    option = args.option

    combinedfit(setup, era=era, config=config, option=option)

###
if __name__ == '__main__':
    print

    argv = sys.argv
    parser = ArgumentParser(prog="makeTESfit", description="execute all steps to run TES fit")
    parser.add_argument('-y', '--era', dest='era', choices=['2016', '2017', '2018', 'UL2016_preVFP','UL2016_postVFP', 'UL2017', 'UL2018','UL2018v10'], default=['UL2018'], action='store', help="set era")
    parser.add_argument('-c', '--config', dest='config', type=str, default='TauES_ID/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
    parser.add_argument('-o', '--option', dest='option', choices=['1', '2', '3', '4', '5','6'], default='1', action='store',
                        help="set option : fit of tes_DM(-o 1) ; fit of tid_SF_DM (-o 2) ; combined fit of tes_DM and tid_SF_DM (-o 3) \
                        ; combined fit of on region scan ID SF (-o 4); combine fit of on region scan TES (-o 5)\
                        ; combine fit of on region 2D scan TES and tid SF (-o 6) ")
   
    args = parser.parse_args()

    main(args)
    print ">>>\n>>> done\n"








