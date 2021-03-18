#! /usr/bin/env python

import os, re
import multiprocessing
import copy
import math
from array import array
from ROOT import ROOT, gROOT, gStyle, gRandom, TSystemDirectory
from ROOT import TFile, TChain, TTree, TCut, TH1F, TH2F, THStack, TGraph, TGraphAsymmErrors
from ROOT import TStyle, TCanvas, TPad, TBox
from ROOT import TLegend, TLatex, TText, TLine, TPaveText, kBlack, kRed, kOrange, kGreen
#from utils import *

import optparse
usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)
parser.add_option("-b", "--bash",     action="store_true", dest="bash", default=False )
parser.add_option("-f", "--fileName", action="store", type="string", dest="fileName", default="pulls.txt")
parser.add_option("-o", "--outName",  action="store", type="string", dest="outName",  default="pulls"    )
parser.add_option("-t", "--text",     action="store", type="string", dest="text",     default=""         )
parser.add_option("-l", "--header",   action="store", type="string", dest="header",   default=""         )
(options, args) = parser.parse_args()
if options.bash: gROOT.SetBatch(True)

fileName = options.fileName
outName  = options.outName
text     = options.text
header   = options.header

# Format:
#0 : sys name
#1 : b-only DX
#2 : b-only dDX
#3 : s+b DX
#4 : s+b dDX
#5 : rho

gStyle.SetOptStat(0)
gStyle.SetErrorX(0)
var_dict = { 'pfmt_1': "m_{T}", 'm_vis': "m_{vis}", 'm_2': "m_{#tau}", }
cat_dict = { 'DM0': "h^{#pm}", 'DM1': "h^{#pm}#pi^{0}", 'DM10': "h^{#pm}h^{#mp}h^{#pm}", }


def pulls(fileName):
    
    content = filterPullFile(fileName)
    nbins, off = len(content), 0.10
    
    b_pulls = TH1F("b_pulls", ";;Pulls", nbins, 0.-off, nbins-off)
    s_pulls = TH1F("s_pulls", ";;Pulls", nbins, 0.+off, nbins+off) #

    for i, s in enumerate(content):
        l = s.split()
        b_pulls.GetXaxis().SetBinLabel(i+1, l[0])
        s_pulls.GetXaxis().SetBinLabel(i+1, l[0])
        b_pulls.SetBinContent(i+1, float(l[1]))
        b_pulls.SetBinError(i+1, float(l[2]))
        s_pulls.SetBinContent(i+1, float(l[3]))
        s_pulls.SetBinError(i+1, float(l[4]))

    b_pulls.SetFillStyle(3005)
    b_pulls.SetFillColor(923)
    b_pulls.SetLineColor(923)
    b_pulls.SetLineWidth(2)
    b_pulls.SetMarkerStyle(20)
    b_pulls.SetMarkerSize(1.25)
    
    s_pulls.SetLineColor(602)
    s_pulls.SetMarkerColor(602)
    s_pulls.SetMarkerStyle(24) #24
    s_pulls.SetLineWidth(2)
    
    b_pulls.GetYaxis().SetRangeUser(-2.5, 2.5)
    
    
    canvas = TCanvas("canvas", "Pulls", 1600, 800)
    canvas.cd()
    canvas.GetPad(0).SetTopMargin(0.06)
    canvas.GetPad(0).SetRightMargin(0.05)
    canvas.GetPad(0).SetBottomMargin(0.15)
    canvas.GetPad(0).SetTicks(1, 1)

    #    box = TBox(950., 105., 2000., 200.)
    #    box.SetFillStyle(3354)
    #    #box.SetFillStyle(0)
    #    box.SetFillColor(1)
    #    box.SetLineWidth(2)
    #    box.SetLineStyle(2)
    #    box.SetLineColor(1)
    #    box.Draw()

    # Draw
    b_pulls.Draw("PE1")
    #b_pulls.Draw("B")
    s_pulls.Draw("SAME, PE1")

    leg = TLegend(0.25, 0.95, 0.75, 0.995)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetFillColor(0)
    leg.SetNColumns(2)
    leg.AddEntry(b_pulls,  "background-only fit", "flp")
    leg.AddEntry(s_pulls,  "signal+background fit", "lp")
    if text: leg.AddEntry(0, text, "")
    
    line = TLine()
    line.DrawLine(0., 0., nbins, 0.)
    line.SetLineStyle(7)
    line.SetLineWidth(2)
    line.SetLineColor(417)
    line.DrawLine(0., 1., nbins, 1.)
    line.DrawLine(0., -1., nbins, -1.)
    line.SetLineColor(800)
    line.DrawLine(0., 2., nbins, 2.)
    line.DrawLine(0., -2., nbins, -2.)
    
    leg.Draw()
    #    drawCMS(LUMI, "Simulation")
    #    drawAnalysis("DM")
    #    drawRegion(channel)

    #    canvas.Print(outName+".jpg")
    canvas.Print(outName+".png")
    canvas.Print(outName+".pdf")

    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")



def pullsVertical(fileName):
    
    content = filterPullFile(fileName)
    nbins, off = len(content), 0.10
    
    b_pulls = TH1F("b_pulls", ";;Pulls", nbins, 0.-off, nbins-off)
    s_pulls = TH1F("s_pulls", ";;Pulls", nbins, 0.+off, nbins+off) #

    for i, s in enumerate(content):
        l = s.split()
        b_pulls.GetXaxis().SetBinLabel(i+1, l[0])
        s_pulls.GetXaxis().SetBinLabel(i+1, l[0])
        b_pulls.SetBinContent(i+1, float(l[1]))
        b_pulls.SetBinError(i+1, float(l[2]))
        s_pulls.SetBinContent(i+1, float(l[3]))
        s_pulls.SetBinError(i+1, float(l[4]))
    
    b_pulls.SetFillStyle(3005)
    b_pulls.SetFillColor(923)
    b_pulls.SetLineColor(923)
    b_pulls.SetLineWidth(1)
    b_pulls.SetMarkerStyle(20)
    b_pulls.SetMarkerSize(1.25)
    
    s_pulls.SetLineColor(602)
    s_pulls.SetMarkerColor(602)
    s_pulls.SetMarkerStyle(24) #24
    s_pulls.SetLineWidth(1)
    
    b_pulls.GetYaxis().SetRangeUser(-2.5, 2.5)
    
    # Graphs
    h_pulls = TH2F("pulls", "", 6, -3., 3., nbins, 0, nbins)
    B_pulls = TGraphAsymmErrors(nbins)
    S_pulls = TGraphAsymmErrors(nbins)
    
    boxes = []
    
    canvas = TCanvas("canvas", "Pulls", 600, 150+nbins*10)#nbins*20)
    canvas.cd()
    canvas.SetGrid(0, 1)
    canvas.GetPad(0).SetTopMargin(0.01)
    canvas.GetPad(0).SetRightMargin(0.01)
    canvas.GetPad(0).SetBottomMargin(0.05)
    canvas.GetPad(0).SetLeftMargin(0.25)#(0.25)#(0.065)
    canvas.GetPad(0).SetTicks(1, 1)
    
    for i, s in enumerate(content):
        l = s.split()
        if "1034h" in l[0]: l[0]="CMS_PDF_13TeV"
        h_pulls.GetYaxis().SetBinLabel(i+1, l[0].replace('CMS2016_', ''))#C
        #y1 = gStyle.GetPadBottomMargin()
        #y2 = 1. - gStyle.GetPadTopMargin()
        #h = (y2 - y1) / float(nbins)
        #y1 = y1 + float(i) * h
        #y2 = y1 + h
        #box = TPaveText(0, y1, 1, y2, 'NDC')
        #box.SetFillColor(0)
        #box.SetTextSize(0.02)
        #box.SetBorderSize(0)
        #box.SetTextAlign(12)
        #box.SetMargin(0.005)
        #if i % 2 == 0:
        #    box.SetFillColor(18)
        #box.Draw()
        #boxes.append(box)
        B_pulls.SetPoint(i+1,float(l[1]),float(i+1)-0.3)#C
        B_pulls.SetPointError(i+1,float(l[2]),float(l[2]),0.,0.)#C
    
    for i, s in enumerate(content):
        l = s.split()
        S_pulls.SetPoint(i+1,float(l[3]),float(i+1)-0.7)#C
        S_pulls.SetPointError(i+1,float(l[4]),float(l[4]),0.,0.)#C
    
    h_pulls.GetXaxis().SetTitle("(#hat{#theta} - #theta_{0}) / #Delta#theta")
    h_pulls.GetXaxis().SetLabelOffset(-0.01)
    h_pulls.GetXaxis().SetTitleOffset(.6)
    h_pulls.GetYaxis().SetNdivisions(nbins, 0, 0)
    
    B_pulls.SetFillColor(1)
    B_pulls.SetLineColor(1)
    B_pulls.SetLineStyle(1)
    B_pulls.SetLineWidth(2)
    B_pulls.SetMarkerColor(1)
    B_pulls.SetMarkerStyle(20)
    B_pulls.SetMarkerSize(1)#(0.75)
    
    S_pulls.SetFillColor(629)
    S_pulls.SetLineColor(629)
    S_pulls.SetMarkerColor(629)
    S_pulls.SetLineWidth(2)
    S_pulls.SetMarkerStyle(20)
    S_pulls.SetMarkerSize(1)
    
    box1 = TBox(-1., 0., 1., nbins)
    box1.SetFillStyle(3001)
    #box1.SetFillStyle(0)
    box1.SetFillColor(417)
    box1.SetLineWidth(2)
    box1.SetLineStyle(2)
    box1.SetLineColor(417)
    
    box2 = TBox(-2., 0., 2., nbins)
    box2.SetFillStyle(3001)
    #box2.SetFillStyle(0)
    box2.SetFillColor(800)
    box2.SetLineWidth(2)
    box2.SetLineStyle(2)
    box2.SetLineColor(800)
    
    leg = TLegend(0.1, -0.05, 0.7, 0.08)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetFillColor(0)
    leg.SetNColumns(2)
    leg.AddEntry(B_pulls,  "B-only fit", "lp")
    leg.AddEntry(S_pulls,  "S+B fit", "lp")
    if text: leg.AddEntry(0, text, "")
    
    h_pulls.Draw("")
    box2.Draw()
    box1.Draw()
    B_pulls.Draw("P6SAME")
    S_pulls.Draw("P6SAME")
    leg.Draw()
    
#    drawCMS(35867, "Preliminary")
#    drawAnalysis("VH")
#    drawRegion(outName)
    
    canvas.Print(outName+".png")
    canvas.Print(outName+".pdf")

    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")



def pullsVertical_noBonly(fileName):
    
    content = filterPullFile(fileName)
    nbins, off = len(content), 0.10
    
    # Graphs
    h_pulls = TH2F("pulls", "", 6, -3., 3., nbins, 0, nbins)
    S_pulls = TGraphAsymmErrors(nbins)
    
    boxes = []
    
    canvas = TCanvas("canvas", "Pulls", 720, 300+nbins*18)#nbins*20)
    canvas.cd()
    canvas.SetGrid(0, 1)
    canvas.SetTopMargin(0.01)
    canvas.SetRightMargin(0.01)
    canvas.SetBottomMargin(0.10)
    canvas.SetLeftMargin(0.40)
    canvas.SetTicks(1, 1)
    
    for i, s in enumerate(content):
        l = s.split()
        h_pulls.GetYaxis().SetBinLabel(i+1, l[0])
        S_pulls.SetPoint(i,float(l[3]),float(i+1)-0.5)
        S_pulls.SetPointError(i,float(l[4]),float(l[4]),0.,0.)
    
    h_pulls.GetXaxis().SetTitle("(#hat{#theta} - #theta_{0}) / #Delta#theta")
    h_pulls.GetXaxis().SetLabelOffset(0.0)
    h_pulls.GetXaxis().SetTitleOffset(0.8)
    h_pulls.GetXaxis().SetLabelSize(0.045)
    h_pulls.GetXaxis().SetTitleSize(0.050)
    h_pulls.GetYaxis().SetLabelSize(0.046)
    h_pulls.GetYaxis().SetNdivisions(nbins, 0, 0)
    
    S_pulls.SetFillColor(kBlack)
    S_pulls.SetLineColor(kBlack)
    S_pulls.SetMarkerColor(kBlack)
    S_pulls.SetLineWidth(2)
    S_pulls.SetMarkerStyle(20)
    S_pulls.SetMarkerSize(1)
    
    box1 = TBox(-1., 0., 1., nbins)
    #box1.SetFillStyle(3001) # 3001 checkered
    #box1.SetFillStyle(0)
    box1.SetFillColor(kGreen+1) # 417
    box1.SetLineWidth(2)
    box1.SetLineStyle(2)
    box1.SetLineColor(kGreen+1) # 417
    
    box2 = TBox(-2., 0., 2., nbins)
    #box2.SetFillStyle(3001) # 3001 checkered
    #box2.SetFillStyle(0)
    box2.SetFillColor(kOrange) # 800
    box2.SetLineWidth(2)
    box2.SetLineStyle(2)
    box2.SetLineColor(kOrange) # 800
    
    leg = TLegend(0.01, 0.01, 0.3, 0.15)
    leg.SetTextSize(0.05)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetFillColor(0)
    #leg.SetNColumns(2)
    leg.AddEntry(S_pulls, "S+B fit", "lp")
    if text: leg.AddEntry(0, text, "")
    
    h_pulls.Draw("")
    box2.Draw()
    box1.Draw()
    S_pulls.Draw("P6SAME")
    leg.Draw()
    canvas.RedrawAxis()
    
    canvas.Print(outName+".png")
    canvas.Print(outName+".pdf")
    
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")
    


def filterPullFile(fileName):
    with open(fileName) as file:
      content = file.readlines()
    #if "m_2" in fileName:
    #  return [x for x in content if (not 'bin_' in x or 'QCD' in x or 'W' in x) and any(c.isdigit() for c in x)]
    return [x for x in content if (not 'bin_' in x) and any(c.isdigit() for c in x)]

def formatParameter(param):
    """Helpfunction to format nuisance parameter."""
    string = param.replace("CMS_","").replace("ttbar_","").replace("ztt_","").replace("_13TeV","")
    if "DM" in string:
      string = re.sub(r"mt_DM\d+_","",string)
    return string

def makeLatex(string):
    for var in var_dict:
      string = string.replace(var,var_dict[var])
    for wp,Wp in [("vvlo","VVLo"),("vlo","VLo"),("lo","Lo"),("me","Me"),
                  ("vvti","VVTi"),("vti","VTi"),("ti","Ti")]:
      if wp in string:
        string = string.replace(wp,Wp)
    #if '_' in string:
    #  string = re.sub(r"\b([^_]*)_([^_]*)\b",r"\1_{\2}",string,flags=re.IGNORECASE)
    return string



text = makeLatex(text)
header = makeLatex(header)
pullsVertical_noBonly(fileName)
