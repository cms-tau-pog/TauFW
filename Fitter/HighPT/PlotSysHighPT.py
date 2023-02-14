#! /usr/bin/env python
# Author: Alexei Raspereza (December 2022)
# Checking systematic variations in W*->mu+v and W*->tau+v samples
import ROOT
import TauFW.Fitter.HighPT.utilsHighPT as utils
from array import array
import TauFW.Fitter.HighPT.stylesHighPT as styles
import os

def PlotSystematics(h_central,h_up,h_down,sampleName,sysName,ratioMin,ratioMax):

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
    h_ratio.GetYaxis().SetRangeUser(ratioMin,ratioMax)

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
    leg.SetHeader(sampleName+":"+sysName)
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
    canvas.Print(utils.figuresFolderSys+"/syst_"+sampleName+"_"+sysName+".png")


if __name__ == "__main__":

    styles.InitROOT()
    styles.SetStyle()

#   Systematics :
#   jet,met = JES, JER, Unclustered
#   taues   = taues_1pr taues_1pr1pi0 taues_3pr taues_3pr1pi0    

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-e','--era', dest='era', default='UL2018', help="""Era : UL2017, UL2018""")
    parser.add_argument('-c','--channel', dest='channel',  default='taunu', help="""Channel : munu, taunu """)
    parser.add_argument('-nb','--nbins', dest='nbins',default=8,help=""" Number of bins""")
    parser.add_argument('-xmin','--xmin',dest='xmin' ,default=200,help=""" xmin """)
    parser.add_argument('-xmax','--xmax',dest='xmax' ,default=1000, help=""" xmax """)
    parser.add_argument('-var','--variable',dest='variable',default='mt_1',help=""" Variable to plot""")
    parser.add_argument('-sys','--sysname',dest='sysname',default='JES',help=""" Systematics name : JES, JER, Unclustered, taues, taues_1pr, taues_1pr1pi0, taues_3pr, taues_3pr1pi0 """)
    args = parser.parse_args() 

    sampleName = 'WToMuNu_M-200'
    if args.channel=='taunu': sampleName = 'WToTauNu_M-200'

    xbins = utils.createBins(args.nbins,args.xmin,args.xmax)
    basefolder = utils.picoFolder

    variableCentral = args.variable
    variableUp = args.variable + "_" + args.sysname + "Up"
    variableDown = args.variable + "_" + args.sysname + "Down"
    sample = utils.sampleHighPt(basefolder,args.era,args.channel,sampleName,False)
    hist_central = sample.CreateHisto(variableCentral,"weight","weight>0.0",xbins,"hist_central")
    hist_up      = sample.CreateHisto(variableUp,"weight","weight>0.0",xbins,"hist_up")
    hist_down    = sample.CreateHisto(variableDown,"weight","weight>0.0",xbins,"hist_down")
    
    fileOutput = ROOT.TFile("test.root","recreate")
    fileOutput.cd("")
    hist_central.Write("h_central")
    hist_up.Write("h_up")
    hist_down.Write("h_down")
    fileOutput.Close()

    PlotSystematics(hist_central,hist_up,hist_down,sampleName,args.sysname,0.9,1.1)
