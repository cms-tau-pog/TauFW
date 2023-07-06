#! /usr/bin/env python
# Author: Alexei Raspereza (November 2022)
# Description: computes fake factors 
#              for high pT jet->tau fakes
from ROOT import TFile, TH1, TH1D, TCanvas, TLegend, TH2, gROOT, TF1, TVirtualFitter, kCyan, gStyle
import TauFW.Fitter.HighPT.utilsHighPT as utils
from array import array
import TauFW.Fitter.HighPT.stylesHighPT as styles
import os

#################################
#     definition of cuts        #
#################################
basecutEWK = 'mt_1>50&&iso_1<0.3&&pt_1>30&&fabs(eta_1)<2.4&&metfilter>0.5&&njets==0&&extraelec_veto<0.5&&extramuon_veto<0.5&&extratau_veto<0.5&&dphi>2.4&&pt_2>100&&fabs(eta_2)<2.3&&idDeepTau2017v2p1VSjet_2>0&&idDeepTau2017v2p1VSe_2>=4&&idDeepTau2017v2p1VSmu_2>=1'

basecutQCD = 'jpt>100&&njets==1&&dphi>2.4&&extraelec_veto<0.5&&extramuon_veto<0.5&&extratau_veto<0.5&&pt_2>100&&fabs(eta_2)<2.3&&idDeepTau2017v2p1VSjet_2>0&&idDeepTau2017v2p1VSe_2>=4&&idDeepTau2017v2p1VSmu_2>=1'

basecut = {
    "dijets": basecutQCD,
    "wjets" : basecutEWK
}

genFakeCut    = 'genmatch_2==0'
genNotFakeCut = 'genmatch_2!=0'

#########################
# Definition of samples #
#########################

mcSampleNames = ['DYJetsToLL_M-50','TTTo2L2Nu','TTToSemiLeptonic','TTToHadronic','WJetsToLNu','WJetsToLNu_HT-100To200','WJetsToLNu_HT-200To400','WJetsToLNu_HT-400To600','WJetsToLNu_HT-600To800','WJetsToLNu_HT-800To1200','WJetsToLNu_HT-1200To2500','ST_t-channel_antitop_4f_InclusiveDecays','ST_t-channel_top_4f_InclusiveDecays','ST_tW_antitop_5f_NoFullyHadronicDecays','ST_tW_top_5f_NoFullyHadronicDecays','WW','WZ','ZZ']

sigSampleNames = ['WJetsToLNu','WJetsToLNu_HT-100To200','WJetsToLNu_HT-200To400','WJetsToLNu_HT-400To600','WJetsToLNu_HT-600To800','WJetsToLNu_HT-800To1200','WJetsToLNu_HT-1200To2500']


# Fitting function (tau pt, ptratio bins)
def FitPt(x,par):
    a = 0.01*(x[0]-100.)
    ff = par[0]+par[1]*a
    if x[0]>200:
        ff = par[2]
    return ff

# Fitting function (mass, DM bins)
def FitMass(x,par):
    ff = par[0]+par[1]*x[0]+par[2]*x[0]*x[0]
    return ff

###########################
# Plotting and fitting FF #
###########################
def DrawFF(hist,era,channel,label,WP,**kwargs):

    print()
    print('fitting FF histo >>>',era,channel,label)

    isdata = kwargs.get('isdata',True)
    mode   = kwargs.get('mode',0)

    labelSample = "mc"
    color = 2
    if isdata: 
        color = 1
        labelSample = "data"

    styles.InitData(hist)


    nbins = hist.GetNbinsX()
    xmin = hist.GetXaxis().GetBinLowEdge(1)
    xmax = hist.GetXaxis().GetBinLowEdge(nbins+1)
    ymax = hist.GetMaximum()
    ymin = hist.GetMinimum()
    average = 0.5*(ymin+ymax)
    histToPlot = hist.Clone('temp')

    if mode==0 or mode==2:
        f1 = TF1("f1",FitPt,xmin,xmax,3)
        f1.SetParameter(0,average)
        f1.SetParameter(1,0)
        f1.SetParameter(2,ymax)
    elif mode==1:
        f1 = TF1("f1",FitMass,xmin,xmax,3)
        f1.SetParameter(0,average)
        f1.SetParameter(1,0)
        f1.SetParameter(2,0)    


    canv = styles.MakeCanvas("canv","",700,600)
    hist.Fit('f1',"R")
    if mode==1: canv.SetLogx(False)
    else: canv.SetLogx(True)

    hfit = TH1D("ff_"+labelSample+"_"+channel+"_"+label,"",5000,xmin,xmax)
    TVirtualFitter.GetFitter().GetConfidenceIntervals(hfit,0.68)

    hfitline = hfit.Clone('histline')
    hfitline.SetLineWidth(2)
    hfitline.SetLineColor(4)
    hfitline.SetMarkerSize(0)
    hfitline.SetMarkerStyle(0)
    for i in range(1,hfitline.GetNbinsX()+1): hfitline.SetBinError(i,0)

    styles.InitModel(hfit,4)
    hfit.SetFillColor(kCyan)
    hfit.SetFillStyle(1001)
    hfit.SetLineWidth(2)
    hfit.SetLineColor(4)
    hfit.SetMarkerSize(0)
    hfit.SetMarkerStyle(0)
    maxFit = 1.5*hfit.GetMaximum()
    hfit.GetYaxis().SetRangeUser(0.,maxFit)
    hfit.SetTitle(era+" : "+channel+" : "+label)
    if mode==1: hfit.GetXaxis().SetTitle("#tau mass [GeV]")
    else: hfit.GetXaxis().SetTitle("#tau p_{T} [GeV]")
    hfit.GetYaxis().SetTitle("Fake factor")

    hfit.Draw("e2")
    hfitline.Draw("hsame")
    histToPlot.Draw("e1same")

    if mode==0 or mode==2: leg = TLegend(0.5,0.2,0.7,0.4)
    else: leg = TLegend(0.23,0.2,0.43,0.4)
    styles.SetLegendStyle(leg)
    leg.SetTextSize(0.04)
    if isdata: leg.AddEntry(hist,"Data",'lp')
    else: leg.AddEntry(hist,"MC",'lp')
    leg.AddEntry(hfit,'Fit','l')
    leg.Draw()
    canv.RedrawAxis()
    canv.Update()
    canv.Print(utils.figuresFolderFF+'/FF_'+labelSample+"_"+channel+'_'+label+"_"+WP+'_'+era+'.png')
    
    return hfit

def main(outputfile,dataSamples,mcSamples,sigSamples,**kwargs):

    era = kwargs.get("era","UL2018")
    wp = kwargs.get("wp","Medium")
    channel = kwargs.get("channel","wjets")
    mode = kwargs.get("mode",0)

    print()
    print("+++++++++++++++++++++++++++++++++++++++++++")
    print()
    if mode==0: 
        print('Computing FF as a function of tau pT in bins of pt_tau/pt_jet',era,wp,channel)
    elif mode==1: 
        print('Computing FF as a function of tau mass in bins of DM',era,wp,channel)
    else: 
        print('Computing FF as a function of tau pT in bins of (pt_tau/pt_jet,DM)',era,wp,channel)
    print()
        
    cutTauDen = "idDeepTau2017v2p1VSjet_2<4"
    cutTauNum = "idDeepTau2017v2p1VSjet_2>=" + utils.tauWPs[wp]

    ##############
    ## labels ####
    ##############
    binCuts = {}
    if mode==0: binCuts = utils.ptratioCuts
    elif mode==1: binCuts = utils.decaymodeCuts
    else:
        for ptrat in utils.ptratio2DCuts:
            for dm in utils.decaymode2DCuts:
                binCuts[ptrat+"_"+dm] = utils.ptratio2DCuts[ptrat] + "&&" + utils.decaymode2DCuts[dm]
    
    ##############
    ## Variable ##
    ##############
    var = 'pt_2'
    if mode==1: var = 'm_2'

    ############################
    ###### Common cut ##########
    ############################
    commonCut = basecut[channel]

    histsdata = {}
    histssig = {}
    for label in binCuts:
        xbins = []
        print()
        print('***************************')
        print('Running over',label)
        print()
 
        if mode==0: xbins=utils.xbinsPt
        elif mode==1: xbins=utils.xbinsMass[label]
        else: xbins=utils.xbinsPt2D

        addCut = binCuts[label]
        cut = commonCut + "&&" + addCut
        cutNum = cut + "&&" + cutTauNum
        cutDen = cut + "&&" + cutTauDen

        datahistNum = utils.RunSamples(dataSamples,var,"1.0",cutNum,xbins,'data_num_'+label)
        datahistDen = utils.RunSamples(dataSamples,var,"1.0",cutDen,xbins,'data_den_'+label)

        if channel=="wjets":
            cutNumMC = cutNum + "&&" + genNotFakeCut
            cutDenMC = cutDen + "&&" + genNotFakeCut
            mchistNum = utils.RunSamples(mcSamples,var,"weight",cutNumMC,xbins,'mc_num_'+label)
            mchistDen = utils.RunSamples(mcSamples,var,"weight",cutDenMC,xbins,'mc_den_'+label)
            datahistNum.Add(datahistNum,mchistNum,1.,-1.)
            datahistDen.Add(datahistDen,mchistDen,1.,-1.)

            
        histffdata = utils.divideHistos(datahistNum,datahistDen,'d_'+channel+"_"+label)
        histsdata["data_"+channel+"_"+label] = DrawFF(histffdata,era,channel,
                                                      label,args.wp,mode=mode,isdata=True)
        
        if channel=="wjets":
            cutNumSig = cutNum + "&&" + genFakeCut
            cutDenSig = cutDen + "&&" + genFakeCut
            sighistNum = utils.RunSamples(sigSamples,var,"weight",cutNumSig,xbins,"sig_num_"+label)
            sighistDen = utils.RunSamples(sigSamples,var,"weight",cutDenSig,xbins,"sig_den_"+label)
            histffsig  = utils.divideHistos(sighistNum,sighistDen,"s_"+channel+"_"+label)
            histssig["mc_"+channel+"_"+label] = DrawFF(histffsig,era,channel,
                                                       label,args.wp,mode=mode,isdata=False)
                      
    outputfile.cd('')
    for hist in histsdata:
        histsdata[hist].Write(hist)
    
    if channel=="wjets":
        for hist in histssig:
            histssig[hist].Write(hist)
        
############
#   MAIN   #
############
if __name__ == "__main__":

    styles.InitROOT()
    styles.SetStyle()

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-e','--era', dest='era', default='UL2018', help="""Era : UL2017, UL2018""")
    parser.add_argument('-wp','--WP', dest='wp',  default='Medium', help="""WP : Loose, Medium, Tight, VTight, VVTight """)
    args = parser.parse_args() 

    if args.wp not in ['Loose','Medium','Tight','VTight','VVTight']:
        print('unknown WP',args.wp)
        exit()
    if args.era not in ['UL2017','UL2018']:
        print('unknown WP',args.era)
        exit()

    basefolder = utils.picoFolder

    print('initializing SingleMuon samples >>>')
    singlemuSamples = {} # data samples disctionary
    singlemuNames = utils.singlemu[args.era]
    for singlemuName in singlemuNames:
        singlemuSamples[singlemuName] = utils.sampleHighPt(basefolder,args.era,
                                                           "wjets",singlemuName,True)

    print()
    print('initializing JetHT samples >>>')
    jethtSamples = {} # data samples disctionary
    jethtNames = utils.jetht[args.era]
    for jethtName in jethtNames:
        jethtSamples[jethtName] = utils.sampleHighPt(basefolder,args.era,
                                                     "dijets",jethtName,True)

    print()
    print('initializing MC samples >>>')
    mcSamples = {} # mc samples dictionary
    for mcSampleName in mcSampleNames:
        if mcSampleName=="WJetsToLNu":
            mcSamples[mcSampleName] = utils.sampleHighPt(basefolder,args.era,"wjets",mcSampleName,
                                                         False,additionalCut='HT<100')
        else:
            mcSamples[mcSampleName] = utils.sampleHighPt(basefolder,args.era,"wjets",mcSampleName,
                                                         False)
    print()
    print('initializing W+Jets samples >>>') 
    sigSamples = {} # wjets samples dictionary
    for sigSampleName in sigSampleNames:
        if sigSampleName=="WJetsToLNu":
            sigSamples[sigSampleName] = utils.sampleHighPt(basefolder,args.era,"wjets",sigSampleName,
                                                           False,additionalCut='HT<100')
        else:
            sigSamples[sigSampleName] = utils.sampleHighPt(basefolder,args.era,"wjets",sigSampleName,
                                                           False)

    fullpathout = os.getenv('CMSSW_BASE') + '/src/TauFW/Plotter/data/ff_HighPT/ff_'+args.wp+"_"+args.era+".root"
    outputfile = TFile(fullpathout,'recreate')

    #   mode of measurement ->
    #   mode = 0 : FF as a function of pT(tau) in bins of pT(tau)/pT(jet), 
    #   mode = 1 : FF as a function of tau mass in bins of tau DM (1prPi0, 3pr, 3prPi0)
    #   mode = 2 : FF as a function of pT(tau) in bins of pT(tau)/pT(jet) and tau DM
    
    main(outputfile,singlemuSamples,mcSamples,sigSamples,
         wp=args.wp,era=args.era,channel="wjets",mode=0)
        
    main(outputfile,jethtSamples,mcSamples,sigSamples,
         wp=args.wp,era=args.era,channel="dijets",mode=0)

    outputfile.Close()


