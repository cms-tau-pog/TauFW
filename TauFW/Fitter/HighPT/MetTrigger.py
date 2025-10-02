#! /usr/bin/env python
# Author: Alexei Raspereza (November 2022)
# Description: compute MET trigger efficiencies and SF 
from ROOT import TFile, TH1, TH1D, TCanvas, TLegend, TH2, gROOT
import TauFW.Fitter.HighPT.utilsHighPT as utils
from array import array
import TauFW.Fitter.HighPT.stylesHighPT as styles
import os

####################
# MET trigger cuts #
####################
mettrig   = 'mettrigger>0.5'
nomettrig = 'mettrigger<0.5'

def DrawEfficiency(histdata,histmc,era,legend):
    print('drawing efficiency histo >>>',era,legend)
    canv = styles.MakeCanvas("canv","",700,600)
    canv.SetLogx(True)

    histmc.SetLineColor(2)
    histmc.SetMarkerColor(2)
    histmc.SetMarkerSize(0.5)

    histdata.SetLineColor(1)
    histdata.SetMarkerColor(1)
    histdata.SetMarkerSize(0.5)
    histdata.GetYaxis().SetRangeUser(0.,1.2)
    histdata.GetXaxis().SetRangeUser(100.,1000.)
    histdata.GetXaxis().SetTitle("E_{T,no #mu}^{mis} [GeV]")
    histdata.GetYaxis().SetTitle("Efficiency")
    histdata.SetTitle(legend)
    histdata.Draw('h')
    histmc.Draw('hsame')
    leg = TLegend(0.6,0.3,0.9,0.5)
    styles.SetLegendStyle(leg)
    leg.SetTextSize(0.045)
    leg.AddEntry(histdata,'Data','l')
    leg.AddEntry(histmc,'MC','l')
    leg.Draw()

    styles.CMS_label(canv,era=era)

    canv.Update()
    canv.Print(utils.figuresFolderMetTrigger+'/mettrig_'+era+'_'+legend+'.png')

def main(args):

    era = args.era
    print()

    channel = "munu"
    basefolder = utils.picoFolder
    xbins = [100,120,130,140,150,160,170,180,190,200,225,250,275,300,1000]
    nbins = len(xbins)-1
    basecut = 'met>50&&mt_1>50&&pt_1>30&&fabs(eta_1)<2.1&&metfilter>0.5'
    weight = 'weight'
    var = 'metnomu'
    mhtLabels = {
        'mht100to130': 'mhtnomu>100&&mhtnomu<130',
        'mht130to160': 'mhtnomu>130&&mhtnomu<160',
        'mht160to200': 'mhtnomu>160&&mhtnomu<200',
        'mhtGt200'   : 'mhtnomu>200'}

    dataSampleNames = utils.singlemu[era]
    mcSampleNames = ['WJetsToLNu','WJetsToLNu_HT-100To200','WJetsToLNu_HT-200To400','WJetsToLNu_HT-400To600','WJetsToLNu_HT-600To800','WJetsToLNu_HT-800To1200','WJetsToLNu_HT-1200To2500']
    
    dataSamples = {} # data samples disctionary
    print('Initializing SingleMuon data samples>>>')
    for dataSampleName in dataSampleNames:
        dataSamples[dataSampleName] = utils.sampleHighPt(basefolder,era,channel,
                                                         dataSampleName,True)

    print()
    mcSamples = {} # mc samples dictionary
    print('Initializing W+Jets MC samples>>>')
    for mcSampleName in mcSampleNames:
        if mcSampleName=="WJetsToLNu":
            mcSamples[mcSampleName] = utils.sampleHighPt(basefolder,era,channel,
                                                         mcSampleName,False,additionalCut='HT<100')
        else:
            mcSamples[mcSampleName] = utils.sampleHighPt(basefolder,era,channel,
                                                         mcSampleName,False)
    print()
    histsdata = {} # data histo dictionary
    histsmc = {} # mc histo dictionary

    for mhtcut in mhtLabels:

        cutpass = basecut + '&&' + mettrig   + '&&' + mhtLabels[mhtcut]
        cutfail = basecut + '&&' + nomettrig + '&&' + mhtLabels[mhtcut]

        # Data ----->
        datahistpass = utils.RunSamples(dataSamples,var,"1",cutpass,xbins,'data_pass_'+mhtcut)
        datahistfail = utils.RunSamples(dataSamples,var,"1",cutfail,xbins,'data_fail_'+mhtcut)
        histeffdata = utils.dividePassProbe(datahistpass,datahistfail,'data_'+mhtcut)
        histsdata['data_'+mhtcut] = histeffdata
        
        # MC ----->
        mchistpass = utils.RunSamples(mcSamples,var,weight,cutpass,xbins,"mc_pass_"+mhtcut)
        mchistfail = utils.RunSamples(mcSamples,var,weight,cutfail,xbins,"mc_fail_"+mhtcut)
        histeffmc  = utils.dividePassProbe(mchistpass,mchistfail,"mc_"+mhtcut)
        histsmc['mc_'+mhtcut] = histeffmc        

        DrawEfficiency(histeffdata,histeffmc,era,mhtcut)

    fullpathout = os.getenv('CMSSW_BASE') + '/src/TauFW/PicoProducer/data/trigger/mettrigger_'+era+".root"
    outputfile = TFile(fullpathout,'recreate')
    outputfile.cd('')

    for hist in histsdata:
        histsdata[hist].Write(hist)
    
    for hist in histsmc:
        histsmc[hist].Write(hist)
        
    outputfile.Close()

############
#   MAIN   #
############
if __name__ == "__main__":

    styles.InitROOT()
    styles.SetStyle()

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-e','--era', dest='era', default='UL2018', help="""Era : UL2017, UL2018""")
    args = parser.parse_args() 

    main(args)



