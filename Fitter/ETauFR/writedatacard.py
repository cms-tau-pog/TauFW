#! /usr/bin/env python
# Authors: Andrea Cardini, Lorenzo Vigilante and Yiwen Wen (Feb 2021) edited by Paola Mastrapasqua
# Description: Create datacards for combine
import sys
from CombineHarvester.CombineTools import ch
import os
import ROOT as R
import math
#eta = ['0to0.4','0.4to0.8','0.8to1.2','1.2to1.7','1.7to3.0']
eta = ['0to1.46','1.56to2.5']#'0.8to1.2','1.2to1.7','1.7to3.0']
#wp = ['VVVLoose','VVLoose','VLoose','Loose','Medium','Tight','VTight','VVTight']
wp = ['VVLoose', 'Tight']
#### IMPORTANT: change era HERE #####
era='UL2018'
tag=''
for ieta in eta :
    print '<<<<<<< eta range: ', ieta
    for iwp in wp :
        print '<<<<<<<<<<<<<< working point: ', iwp
        cb = ch.CombineHarvester()
        #cb.SetFlag('workspaces-use-clone', True)
        mc_backgrounds = ['ZTT','ZJ','W','VV','ST','TTT','TTL','TTJ']
        data_driven_backgrounds = ['QCD']
        backgrounds = mc_backgrounds + data_driven_backgrounds
        signals = ['ZL']

        categories = {

            'et' : [( 1, '%s_pass'%(iwp) ),( 2, '%s_fail'%(iwp) )],
        }

        cb.AddObservations(['*'], ['ETauFR'], ['%s'%(era)], ['et'],              categories['et']) # adding observed data
        cb.AddProcesses(   ['*'], ['ETauFR'], ['%s'%(era)], ['et'], backgrounds, categories['et'], False) # adding backgrounds
        cb.AddProcesses(   ['90'], ['ETauFR'], ['%s'%(era)], ['et'], signals,     categories['et'], True) # adding signals

        cb.cp().process(mc_backgrounds+signals).AddSyst(cb,'lumi_%s'%(era), 'lnN', ch.SystMap()(1.026)) 
        cb.cp().process(['TTT','TTL','TTJ','ST']).AddSyst(cb, 'xsec_top', 'lnN', ch.SystMap()(1.10))
        cb.cp().process(['VV']).AddSyst(cb, 'normalizationVV', 'lnN', ch.SystMap()(1.10))
        cb.cp().process(['ZL','ZTT','ZJ']).AddSyst(cb, 'normalizationDY', 'lnN', ch.SystMap()(1.10))
        cb.cp().process(['W']).AddSyst(cb, 'normalizationW', 'lnN', ch.SystMap()(1.20))
        cb.cp().process(['ZJ','TTJ']).AddSyst(cb, 'jet_to_tauFR', 'lnN', ch.SystMap()(1.20))
        cb.cp().process(['QCD']).AddSyst(cb, 'normalizationQCD', 'lnN', ch.SystMap()(1.2))
        #cb.cp().process(['ZL']).AddSyst(cb, 'normalizationZEE', 'rateParam', ch.SystMap()(1.0))
        cb.cp().process(['ZTT']).AddSyst(cb, 'shape_tes', 'shape', ch.SystMap()(1.0))
        cb.cp().process(['ZL']).AddSyst(cb, 'shape_fes', 'shapeU', ch.SystMap()(1.0))
        cb.cp().process(mc_backgrounds+signals).AddSyst(cb, 'shape_ees', 'shape', ch.SystMap()(1.0))
        #cb.cp().process(['ZL']).AddSyst(cb, 'shape_res', 'shape', ch.SystMap()(1.0))
        cb.cp().process(mc_backgrounds+signals).AddSyst(cb, 'CMS_eff_e', 'lnN', ch.SystMap()(1.05))
        #cb.cp().process(['ZTT','VV','ST','TTT','TTL','TTJ']).AddSyst(cb, 'CMS_eff_t', 'lnN', ch.SystMap()(1.05))

        filepath = os.path.join(os.environ['CMSSW_BASE'],'src/TauFW/Fitter/ETauFR/input', "zee_fr_m_vis_eta%s_et-%s%s.inputs.root")%(ieta,era,tag)
        processName = '$BIN/$PROCESS'
        systematicName = '$BIN/$PROCESS_$SYSTEMATIC'
        cb.cp().backgrounds().ExtractShapes(filepath, processName, systematicName)
        cb.cp().signals().ExtractShapes(filepath, processName, systematicName)
        ch.SetStandardBinNames(cb, '$BIN') # Define the name of the category names
        #cb.SetAutoMCStats(cb, 0.0) # Introducing statistical uncertainties on the total background for each histogram bin (Barlow-Beeston lite approach)
        
        bbb = ch.BinByBinFactory()
        bbb.SetAddThreshold(0.1).SetMergeThreshold(0.5).SetFixNorm(True)
        bbb.MergeBinErrors(cb.cp().backgrounds())
        bbb.AddBinByBin(cb.cp().backgrounds(), cb)
        
        datacardPath = 'input/%s/ETauFR/%s_eta%s.txt'%(era,iwp,ieta)
        shapePath = 'input/%s/ETauFR/common/%s_eta%s.root'%(era,iwp,ieta)
        writer = ch.CardWriter(datacardPath,shapePath)
        writer.SetWildcardMasses([])
        writer.WriteCards('cmb', cb) # writing all datacards into one folder for combination
        #cb.PrintAll()

        with open('input/%s/ETauFR/%s_eta%s.txt'%(era,iwp,ieta),'a') as f:
             #f.write("* autoMCStats 0  1  1\n") 
             f.write("normalizationZEE rateParam * ZL 1.000 [0.0,10.0]\n")
             f.write("vsjetsf rateParam * ZTT 1.000 [0.0,10.0]\n")
             f.write(" ")
             print '>> Done!'


        #writer.WriteCards(channel, cb.cp().channel([channel])) # writing datacards for each final state in a corresponding folder to be able to perform the measurement individually in each final state
        print 'pre-fit fake rate:'
        print cb.cp().bin(['%s_pass'%(iwp)]).process(['ZL']).GetRate() / ((cb.cp().bin(['%s_pass'%(iwp)]).process(['ZL']).GetRate()+cb.cp().bin(['%s_fail'%(iwp)]).process(['ZL']).GetRate()))

        sigRatePassPre = cb.cp().bin(['%s_pass'%(iwp)]).process(['ZL']).GetRate()
        sigRateFailPre = cb.cp().bin(['%s_fail'%(iwp)]).process(['ZL']).GetRate()
        sigErrPassPre = cb.cp().bin(['%s_pass'%(iwp)]).process(['ZL']).GetUncertainty()
        sigErrFailPre = cb.cp().bin(['%s_fail'%(iwp)]).process(['ZL']).GetUncertainty()
        
        dfdxPre = sigRateFailPre /((sigRatePassPre+sigRateFailPre)*(sigRatePassPre+sigRateFailPre))
        dfdyPre = -sigRatePassPre / ((sigRatePassPre+sigRateFailPre)*(sigRatePassPre+sigRateFailPre))
        errfakeratePrefit = math.sqrt((dfdxPre*sigErrPassPre)*(dfdxPre*sigErrPassPre)+(dfdyPre*sigErrFailPre)*(dfdyPre*sigErrFailPre))
        
        print 'pre-fit fake rate errors:'
        print errfakeratePrefit
