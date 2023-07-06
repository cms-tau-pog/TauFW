#! /usr/bin/env python
# Author: Alexei Raspereza (December 2022)
# High pT tau ID efficiency measurement
# Datacard producer (W*->mu+v control region)
import ROOT
import math
import TauFW.Fitter.HighPT.utilsHighPT as utils
from array import array
import TauFW.Fitter.HighPT.stylesHighPT as styles
import os

#################################
#     definition of cuts        #
#################################
basecut = 'pt_1>120&&fabs(eta_1)<2.1&&metfilter>0.5&&njets==0&&extraelec_veto<0.5&&extramuon_veto<0.5&&extratau_veto<0.5&&idMedium_1>0.5&&njets==0&&iso_1<0.15'

jmetcut = 'met>130&&metdphi_1>2.8&&mt_1>200' # additional cuts (MET related variables)

#################################
#     definition of samples     #
#################################
bkgSampleNames = ['DYJetsToLL_M-50','TTTo2L2Nu','TTToSemiLeptonic','TTToHadronic','ST_t-channel_antitop_4f_InclusiveDecays','ST_t-channel_top_4f_InclusiveDecays','ST_tW_antitop_5f_NoFullyHadronicDecays','ST_tW_top_5f_NoFullyHadronicDecays','WW','WZ','ZZ']

sigSampleNames = ['WToMuNu_M-200']

def PlotWToMuNu(h_data_input,h_bkg_input,h_sig_input,era,var):

    h_data = h_data_input.Clone("data")
    h_sig = h_sig_input.Clone("signal")
    h_bkg = h_bkg_input.Clone("background")
    styles.InitData(h_data)
    styles.InitHist(h_bkg,"","",ROOT.TColor.GetColor("#6F2D35"),1001)
    styles.InitHist(h_sig,"","",ROOT.TColor.GetColor("#FFCC66"),1001)

    nbins = h_data.GetNbinsX()
    # log-normal systematic uncertainties (5% signal, 10% background)
    e_sig_sys = 0.05
    e_bkg_sys = 0.10
    for i in range(1,nbins+1):
        x_sig = h_sig.GetBinContent(i)
        x_bkg = h_bkg.GetBinContent(i)
        e_sig_stat = h_sig.GetBinError(i)
        e_sig = math.sqrt(e_sig_stat*e_sig_stat+e_sig_sys*e_sig_sys*x_sig*x_sig)
        h_sig.SetBinError(i,e_sig)
        e_bkg_stat = h_bkg.GetBinError(i)
        e_bkg = math.sqrt(e_bkg_stat*e_bkg_stat+e_bkg_sys*e_bkg_sys*x_bkg*x_bkg)
        h_bkg.SetBinError(i,e_bkg)

    h_sig.Add(h_sig,h_bkg,1.,1.)
    h_tot = h_sig.Clone("total")
    styles.InitTotalHist(h_tot)

    h_ratio = utils.histoRatio(h_data,h_tot,'ratio')
    h_tot_ratio = utils.createUnitHisto(h_tot,'tot_ratio')

    styles.InitRatioHist(h_ratio)
    h_ratio.GetYaxis().SetRangeUser(0.801,1.199)
    
    utils.zeroBinErrors(h_sig)
    utils.zeroBinErrors(h_bkg)

    ymax = h_data.GetMaximum()
    if h_tot.GetMaximum()>ymax: ymax = h_tot.GetMaximum()

    h_data.GetYaxis().SetRangeUser(0.,1.2*ymax)
    h_data.GetXaxis().SetLabelSize(0)
    h_data.GetYaxis().SetTitle("events / bin")
    h_ratio.GetYaxis().SetTitle("obs/exp")
    h_ratio.GetXaxis().SetTitle(utils.XTitle[var])

    # canvas and pads
    canvas = styles.MakeCanvas("canv","",600,700)
    # upper pad
    upper = ROOT.TPad("upper", "pad",0,0.31,1,1)
    upper.Draw()
    upper.cd()
    styles.InitUpperPad(upper)    
    
    h_data.Draw('e1')
    h_sig.Draw('hsame')
    h_bkg.Draw('hsame')
    h_data.Draw('e1same')
    h_tot.Draw('e2same')

    leg = ROOT.TLegend(0.5,0.4,0.8,0.7)
    styles.SetLegendStyle(leg)
    leg.SetTextSize(0.047)
    leg.AddEntry(h_data,'data','lp')
    leg.AddEntry(h_sig,'W#rightarrow #mu#nu','f')
    leg.AddEntry(h_bkg,'bkg','f')
    leg.Draw()

    styles.CMS_label(upper,era=era)

    upper.Draw("SAME")
    upper.RedrawAxis()
    upper.Modified()
    upper.Update()
    canvas.cd()

    # lower pad
    lower = ROOT.TPad("lower", "pad",0,0,1,0.30)
    lower.Draw()
    lower.cd()
    styles.InitLowerPad(lower)

    h_ratio.Draw('e1')
    h_tot_ratio.Draw('e2same')
    h_ratio.Draw('e1same')
    nbins = h_ratio.GetNbinsX()
    xmin = h_ratio.GetXaxis().GetBinLowEdge(1)    
    xmax = h_ratio.GetXaxis().GetBinLowEdge(nbins+1)
    line = ROOT.TLine(xmin,1.,xmax,1.)
    line.SetLineStyle(1)
    line.SetLineWidth(2)
    line.SetLineColor(4)
    line.Draw()
    lower.Modified()
    lower.RedrawAxis()

    canvas.cd()
    canvas.Modified()
    canvas.cd()
    canvas.SetSelected(canvas)
    canvas.Update()
    print()
    print('Creating control plot')
    canvas.Print(utils.figuresFolderWMuNu+"/wmunu_"+era+".png")

def CreateCardsWToMuNu(fileName,h_data,h_bkg,h_sig,uncs):

    x_data = h_data.GetSumOfWeights()
    x_bkg  = h_bkg.GetSumOfWeights()
    x_sig  = h_sig.GetSumOfWeights() 

    cardsFileName = fileName + ".txt"
    rootFileName = fileName + ".root"
    f = open(cardsFileName,"w")
    f.write("imax 1    number of channels\n")
    f.write("jmax *    number of backgrounds\n")
    f.write("kmax *    number of nuisance parameters\n")
    f.write("---------------------------\n")
    f.write("observation   %3.1f\n"%(x_data))
    f.write("---------------------------\n")
    f.write("shapes * *  "+rootFileName+"  munu/$PROCESS munu/$PROCESS_$SYSTEMATIC \n")
    f.write("---------------------------\n")
    f.write("bin                 WtoMuNu     WtoMuNu\n")
    f.write("process             wmunu       bkg_munu\n")
    f.write("process             1           2\n")
    f.write("rate                %4.3f   %4.3f\n"%(x_sig,x_bkg))
    f.write("---------------------------\n")
    f.write("muEff         lnN   1.02        -\n")
    f.write("bkgNorm_munu  lnN   -           1.2\n")
    for unc in uncs:
        f.write(unc+"    shape  1.0          -\n")
    f.write("normW  rateParam  WtoMuNu wmunu  1.0  [0.5,1.5]\n")
    f.write("* autoMCStats 0\n")
    f.close()


if __name__ == "__main__":

    styles.InitROOT()
    styles.SetStyle()

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-e','--era', dest='era', default='UL2018', help="""Era : UL2017, UL2018""")
    parser.add_argument('-nb','--nbins', dest='nbins',default=8,help=""" Number of bins""")
    parser.add_argument('-xmin','--xmin',dest='xmin' ,default=200,help=""" xmin """)
    parser.add_argument('-xmax','--xmax',dest='xmax' ,default=1000, help=""" xmax """)
    parser.add_argument('-var','--variable',dest='variable',default='mt_1',help=""" Variable to plot""")
    args = parser.parse_args() 
    xbins = [200,300,400,500,600,700,800,1000]
    #    xbins = utils.createBins(args.nbins,args.xmin,args.xmax)
    basefolder = utils.picoFolder
    var = args.variable    
    
    print()
    print('initializing SingleMuon samples >>>')
    singlemuSamples = {} # data samples dictionary
    singlemuNames = utils.singlemu[args.era]
    for singlemuName in singlemuNames:
        singlemuSamples[singlemuName] = utils.sampleHighPt(basefolder,args.era,
                                                           "munu",singlemuName,True)

    print()
    print('initializing background samples >>>')
    bkgSamples = {} # MC bkg samples dictionary 
    for bkgSampleName in bkgSampleNames:
        bkgSamples[bkgSampleName] = utils.sampleHighPt(basefolder,args.era,
                                                       "munu",bkgSampleName,False)

    print()
    print('initializing signal samples >>>')
    sigSamples = {} # MC signal samples dictionary 
    for sigSampleName in sigSampleNames:
        sigSamples[sigSampleName] = utils.sampleHighPt(basefolder,args.era,
                                                       "munu",sigSampleName,False)

    cut_data = basecut + "&&" + jmetcut + "&&mt_1<920."
    cut = basecut + "&&" + jmetcut
    hist_data = utils.RunSamples(singlemuSamples,var,"1.",cut_data,xbins,"data_obs")
    hist_bkg  = utils.RunSamples(bkgSamples,var,"weight",cut,xbins,"bkgd")
    hist_sig  = utils.RunSamples(sigSamples,var,"weight",cut,xbins,"wmunu")


    hists_unc = {} # uncertainty histograms  
    for unc in utils.unc_jme:
        for variation in ["Up"]:
            name_unc = unc + variation
            var_unc = var + "_" + name_unc            
            met_cut = "met_" + name_unc + ">130" 
            mt_1_cut = "mt_1_" + name_unc + ">200"
            metdphi_1_cut = "metdphi_1_" + name_unc + ">2.8"
            jmetcut_unc = met_cut + "&&" + mt_1_cut + "&&" + metdphi_1_cut
            cut_unc = basecut + "&&" + jmetcut_unc
            name = "wmunu_" + name_unc
            hist_sys = utils.RunSamples(sigSamples,var_unc,"weight",cut_unc,xbins,name)
            name_hist = "wmunu_" + unc
            hist_up,hist_down = utils.ComputeSystematics(hist_sig,hist_sys,name_hist)
            hists_unc[name_hist+"Up"] = hist_up
            hists_unc[name_hist+"Down"] = hist_down

    # making control plot
    PlotWToMuNu(hist_data,hist_bkg,hist_sig,args.era,var)

    # saving histograms to file
    outputFileName = utils.datacardsFolder + "/munu_" + args.era
    fileOutput = ROOT.TFile(outputFileName+".root","recreate")
    fileOutput.mkdir("munu")
    fileOutput.cd("munu")
    hist_data.Write("data_obs")
    hist_sig.Write("wmunu")
    hist_bkg.Write("bkg_munu")
    for uncName in hists_unc:
        hists_unc[uncName].Write(uncName)
        
    fileOutput.Close()
    
    uncs = ["JES","Unclustered"]
    CreateCardsWToMuNu(outputFileName,hist_data,hist_bkg,hist_sig,uncs)
