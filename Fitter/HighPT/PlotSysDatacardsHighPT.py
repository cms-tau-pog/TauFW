#! /usr/bin/env python
# Author: Alexei Raspereza (December 2022)
# Checking systematic variations in datacards
import ROOT
import TauFW.Fitter.HighPT.utilsHighPT as utils
from array import array
import TauFW.Fitter.HighPT.stylesHighPT as styles
import os

def PlotSystematics(h_central,h_up,h_down,era,sampleName,sysName,ratioLower,ratioUpper):

    styles.InitData(h_central)
    styles.InitData(h_up)
    styles.InitData(h_down)

    h_up.SetMarkerSize(0)
    h_up.SetLineColor(2)
    h_up.SetMarkerColor(2)
    h_up.SetLineStyle(1)

    h_down.SetMarkerSize(0)
    h_down.SetLineColor(4)
    h_down.SetMarkerColor(4)
    h_down.SetLineStyle(1)

    h_ratio_up = utils.divideHistos(h_up,h_central,'ratio_up')
    h_ratio_down = utils.divideHistos(h_down,h_central,'ratio_down')
    h_ratio = utils.createUnitHisto(h_central,'ratio')
    styles.InitRatioHist(h_ratio)
    h_ratio.GetYaxis().SetRangeUser(ratioLower,ratioUpper)

    utils.zeroBinErrors(h_up)
    utils.zeroBinErrors(h_down)
    utils.zeroBinErrors(h_ratio_up)
    utils.zeroBinErrors(h_ratio_down)

    ymax = h_central.GetMaximum()
    if h_up.GetMaximum()>ymax: ymax = h_up.GetMaximum()
    if h_down.GetMaximum()>ymax: ymax = h_down.GetMaximum()
    h_central.GetYaxis().SetRangeUser(0.,1.2*ymax)
    h_central.GetXaxis().SetLabelSize(0)

    # canvas and pads
    canvas = styles.MakeCanvas("canv","",600,700)
    # upper pad
    upper = ROOT.TPad("upper", "pad",0,0.31,1,1)
    upper.Draw()
    upper.cd()
    styles.InitUpperPad(upper)    
    
    h_central.Draw('e1')
    h_down.Draw('hsame')
    h_up.Draw('hsame')
    h_central.Draw('e1same')
    
    leg = ROOT.TLegend(0.6,0.6,0.9,0.9)
    styles.SetLegendStyle(leg)
    leg.SetTextSize(0.045)
    leg.SetHeader(era+"  "+sampleName+":"+sysName)
    leg.AddEntry(h_central,'central','lp')
    leg.AddEntry(h_up,'up','l')
    leg.AddEntry(h_down,'down','l')
    leg.Draw()

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
    h_ratio_up.Draw('hsame')
    h_ratio_down.Draw('hsame')
    h_ratio.Draw('e1same')
    nbins = h_ratio.GetNbinsX()
    xmin = h_ratio.GetXaxis().GetBinLowEdge(1)    
    xmax = h_ratio.GetXaxis().GetBinLowEdge(nbins+1)
    line = ROOT.TLine(xmin,1.,xmax,1.)
    line.Draw()
    lower.Modified()
    lower.RedrawAxis()

    canvas.cd()
    canvas.Modified()
    canvas.cd()
    canvas.SetSelected(canvas)
    canvas.Update()
    canvas.Print(utils.figuresFolderSys+"/sys_cards_"+era+"_"+sampleName+"_"+sysName+".png")


if __name__ == "__main__":

    styles.InitROOT()
    styles.SetStyle()

#####################################################################
#   Systematics :
#   jmet    = JES, Unclustered
#   taues   = taues, taues_1pr taues_1pr1pi0 taues_3pr taues_3pr1pi0    
#   fakes   = [ewk,qcd]_ptratio[Low,Medium,Hight]_unc[1,2]
#   ------
#   WP      = [Loose,Medium,Tight,VTight,VVTight]
#   ------
#   samples = [wmunu,wtaunu,fake]
#####################################################################
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-e','--era',      dest='era',     default='UL2018',help=""" era : UL2017, UL2018""")
    parser.add_argument('-c','--channel',  dest='channel', default='taunu', help=""" channel : munu, wtaunu""")
    parser.add_argument('-s','--sample',   dest='sample',  default='wtaunu', help=""" sample : wmunu, wtaunu, fake""")
    parser.add_argument('-wp','--WP',      dest='wp',      default='Medium', help=""" tauID WP (taunu channel) """)
    parser.add_argument('-sys','--sysname',dest='sysname', default='JES',help=""" Systematics name : JES, JER, Unclustered, taues, taues_1pr, taues_1pr1pi0, taues_3pr, taues_3pr1pi0, fake tau uncertainties """)
    args = parser.parse_args() 

    basefolder = utils.datacardsFolder
    filename = args.channel + "_" + args.era + ".root"
    if args.channel=='taunu':
        filename = args.channel + "_" + args.wp + "_" + args.era + ".root"
    print("filename",filename)
    cardsFile = ROOT.TFile(basefolder+"/"+filename)
    
    hist_central = cardsFile.Get(args.channel+"/"+args.sample)
    hist_up = cardsFile.Get(args.channel+"/"+args.sample+"_"+args.sysname+"Up")
    hist_down = cardsFile.Get(args.channel+"/"+args.sample+"_"+args.sysname+"Down")
    print("hist_central",hist_central)
    print("hist_up",hist_up)
    print("hist_down",hist_down)

    PlotSystematics(hist_central,hist_up,hist_down,args.era,args.sample,args.sysname,0.8,1.2)
