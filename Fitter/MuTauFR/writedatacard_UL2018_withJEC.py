#! /usr/bin/env python
# Author: Yiwen Wen (Feb 2021)
# Description: Create datacards for combine
import sys
from CombineHarvester.CombineTools import ch
import os
import ROOT as R
import math
eta = ['0to0.4','0.4to0.8','0.8to1.2','1.2to1.7','1.7to3.0']
#eta = ['1.7to3.0']
wp = ['VLoose','Loose','Medium','Tight']
#wp = ['VLoose']
for ieta in eta :
    print '<<<<<<< eta range: ', ieta
    for iwp in wp :
        print '<<<<<<<<<<<<<< working point: ', iwp
        cb = ch.CombineHarvester()
        #cb.SetFlag('workspaces-use-clone', True)
        mc_backgrounds = ['ZTL','ZTT','ZJ','W','VV','ST','TTT','TTL','TTJ']
        data_driven_backgrounds = ['QCD']
        backgrounds = mc_backgrounds + data_driven_backgrounds
        signals = ['ZMM']

        categories = {
            'mutau' : [( 1, 'Pass' ),( 2, 'Fail' )],
        }

        cb.AddObservations(['*'], ['MuTauFR'], ['2018'], ['mutau'],              categories['mutau']) # adding observed data
        cb.AddProcesses(   ['*'], ['MuTauFR'], ['2018'], ['mutau'], backgrounds, categories['mutau'], False) # adding backgrounds
        cb.AddProcesses(   ['*'], ['MuTauFR'], ['2018'], ['mutau'], signals,     categories['mutau'], True) # adding signals

        cb.cp().process(mc_backgrounds+signals).AddSyst(cb,'lumi_2018', 'lnN', ch.SystMap()(1.026))
        cb.cp().process(mc_backgrounds+signals).AddSyst(cb,'muon_eff', 'lnN', ch.SystMap()(1.02))

        cb.cp().process(['TTT','TTL','TTJ','ST']).AddSyst(cb, 'xsec_top', 'lnN', ch.SystMap()(1.10))
        cb.cp().process(['VV']).AddSyst(cb, 'xsec_vv', 'lnN', ch.SystMap()(1.15))
        cb.cp().process(['ZMM','ZTL','ZTT','ZJ']).AddSyst(cb, 'xsec_z', 'lnN', ch.SystMap()(1.03))
        cb.cp().process(['W']).AddSyst(cb, 'w_estimation', 'lnN', ch.SystMap()(1.20))
        cb.cp().process(['ZJ','TTJ']).AddSyst(cb, 'jet_to_tauFR', 'lnN', ch.SystMap()(1.30))
        cb.cp().process(['QCD']).AddSyst(cb, 'ss_to_os_extrap', 'lnN', ch.SystMap()(1.2))
        cb.cp().process(['ZMM']).AddSyst(cb, 'vsjetSF', 'rateParam', ch.SystMap()(1.0))
        cb.cp().process(['ZTT', 'TTT']).AddSyst(cb, 'TES', 'shape', ch.SystMap()(1.0))
        cb.cp().process(['ZMM','ZTL','TTL']).AddSyst(cb, 'FES', 'shape', ch.SystMap()(1.0))
        cb.cp().process(['ZMM']).AddSyst(cb, 'RES', 'shape', ch.SystMap()(1.0))

        filepath = os.path.join(os.environ['CMSSW_BASE'],'src/TauFW/Fitter/MuTauFR/input', "MuTauFR_m_vis_eta%s_mt-UL2018_withJEC.inputs.root")%(ieta)
        processName = '%s$BIN/$PROCESS'%(iwp)
        systematicName = '%s$BIN/$PROCESS_$SYSTEMATIC'%(iwp)
        cb.cp().backgrounds().ExtractShapes(filepath, processName, systematicName)
        cb.cp().signals().ExtractShapes(filepath, processName, systematicName)
        ch.SetStandardBinNames(cb, '$BIN') # Define the name of the category names
        #cb.SetAutoMCStats(cb, 0.0) # Introducing statistical uncertainties on the total background for each histogram bin (Barlow-Beeston lite approach)
        
        bbb = ch.BinByBinFactory()
        bbb.SetAddThreshold(0.1).SetMergeThreshold(0.5).SetFixNorm(True)
        bbb.MergeBinErrors(cb.cp().backgrounds())
        bbb.AddBinByBin(cb.cp().backgrounds(), cb)
        
        datacardPath = 'input/UL2018_withJEC/MuTauFR/%s_eta%s.txt'%(iwp,ieta)
        shapePath = 'input/UL2018_withJEC/MuTauFR/common/%s_eta%s.root'%(iwp,ieta)
        writer = ch.CardWriter(datacardPath,shapePath)
        writer.SetWildcardMasses([])
        writer.WriteCards('cmb', cb) # writing all datacards into one folder for combination
        #cb.PrintAll()
        #writer.WriteCards(channel, cb.cp().channel([channel])) # writing datacards for each final state in a corresponding folder to be able to perform the measurement individually in each final state
        print 'pre-fit fake rate:'
        print cb.cp().bin(['Pass']).process(['ZMM']).GetRate() / ((cb.cp().bin(['Pass']).process(['ZMM']).GetRate()+cb.cp().bin(['Fail']).process(['ZMM']).GetRate()))

        sigRatePassPre = cb.cp().bin(['Pass']).process(['ZMM']).GetRate()
        sigRateFailPre = cb.cp().bin(['Fail']).process(['ZMM']).GetRate()
        sigErrPassPre = cb.cp().bin(['Pass']).process(['ZMM']).GetUncertainty()
        sigErrFailPre = cb.cp().bin(['Fail']).process(['ZMM']).GetUncertainty()
        
        dfdxPre = sigRateFailPre /((sigRatePassPre+sigRateFailPre)*(sigRatePassPre+sigRateFailPre))
        dfdyPre = -sigRatePassPre / ((sigRatePassPre+sigRateFailPre)*(sigRatePassPre+sigRateFailPre))
        errfakeratePrefit = math.sqrt((dfdxPre*sigErrPassPre)*(dfdxPre*sigErrPassPre)+(dfdyPre*sigErrFailPre)*(dfdyPre*sigErrFailPre))
        
        print 'pre-fit fake rate errors:'
        print errfakeratePrefit
