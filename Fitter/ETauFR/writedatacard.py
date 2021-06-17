#! /usr/bin/env python
# Author: Yiwen Wen (Feb 2021)
# Description: Create datacards for combine
import sys
from CombineHarvester.CombineTools import ch
import os
import ROOT as R
import math
#eta = ['0to0.4','0.4to0.8','0.8to1.2','1.2to1.7','1.7to3.0']
eta = ['0to1.46','1.56to2.3']#'0.8to1.2','1.2to1.7','1.7to3.0']
wp = ['VVVLoose','VVLoose','VLoose','Loose','Medium','Tight','VTight','VVTight']

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

        cb.AddObservations(['*'], ['ETauFR'], ['2016'], ['et'],              categories['et']) # adding observed data
        cb.AddProcesses(   ['*'], ['ETauFR'], ['2016'], ['et'], backgrounds, categories['et'], False) # adding backgrounds
        cb.AddProcesses(   ['90'], ['ETauFR'], ['2016'], ['et'], signals,     categories['et'], True) # adding signals

        cb.cp().process(mc_backgrounds).AddSyst(cb,'lumi_2016', 'lnN', ch.SystMap()(1.026))
        cb.cp().process(mc_backgrounds).AddSyst(cb,'muon_eff', 'lnN', ch.SystMap()(1.02))

        cb.cp().process(['TTT','TTL','TTJ','ST']).AddSyst(cb, 'xsec_top', 'lnN', ch.SystMap()(1.10))
        cb.cp().process(['VV']).AddSyst(cb, 'normalizationVV', 'lnN', ch.SystMap()(1.15))
        cb.cp().process(['ZL','ZTT','ZJ']).AddSyst(cb, 'normalizationDY', 'lnN', ch.SystMap()(1.03))
        cb.cp().process(['W']).AddSyst(cb, 'normalizationW', 'lnN', ch.SystMap()(1.20))
        cb.cp().process(['ZJ','TTJ']).AddSyst(cb, 'jet_to_tauFR', 'lnN', ch.SystMap()(1.30))
        cb.cp().process(['QCD']).AddSyst(cb, 'normalizationQCD', 'lnN', ch.SystMap()(1.2))
        cb.cp().process(['ZL']).AddSyst(cb, 'normalizationZEE', 'rateParam', ch.SystMap()(1.0))
        cb.cp().process(['ZTT']).AddSyst(cb, 'shape_tes', 'shape', ch.SystMap()(1.0))
        cb.cp().process(['ZL']).AddSyst(cb, 'shape_fes', 'shapeU', ch.SystMap()(1.0))
        cb.cp().process(['ZL']).AddSyst(cb, 'shape_ees', 'shape', ch.SystMap()(1.0))
        cb.cp().process(['ZL']).AddSyst(cb, 'shape_res', 'shape', ch.SystMap()(1.0))
        cb.cp().process(['ZTT','ZL','ZJ','VV','ST','TTT','TTL','TTJ']).AddSyst(cb, 'CMS_eff_e', 'lnN', ch.SystMap()(1.05))
        cb.cp().process(['ZTT','ZL','VV','ST','TTT','TTL','TTJ']).AddSyst(cb, 'CMS_eff_t', 'lnN', ch.SystMap()(1.05))

        filepath = os.path.join(os.environ['CMSSW_BASE'],'src/TauFW/Fitter/ETauFR/input', "zee_fr_m_vis_eta%s_et-2016.inputs.root")%(ieta)
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
        
        datacardPath = 'input/2016/ETauFR/%s_eta%s.txt'%(iwp,ieta)
        shapePath = 'input/2016/ETauFR/common/%s_eta%s.root'%(iwp,ieta)
        writer = ch.CardWriter(datacardPath,shapePath)
        writer.SetWildcardMasses([])
        writer.WriteCards('cmb', cb) # writing all datacards into one folder for combination
        #cb.PrintAll()
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
