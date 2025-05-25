import ROOT
import uproot
import argparse
import os
from array import array
from math import sqrt

ROOT.gROOT.SetBatch()

parser = argparse.ArgumentParser(description="Combined Tau Trigger Efficiency Plotter with SS Subtraction")
parser.add_argument("input_root_file", type=str, help="Path to the input ROOT file")
args = parser.parse_args()

root_file = args.input_root_file
root_dir = os.path.dirname(root_file) if os.path.dirname(root_file) else "."
root_filename = os.path.splitext(os.path.basename(root_file))[0]

with uproot.open(root_file) as file:
    tree = file["tree"]
    pt_2 = tree["pt_2"].array()
    hlt_24 = tree["HLT_IsoMu24"].array()
    hlt_mutau = tree["HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1"].array()
    trig_match_loose = tree["trig_match_PNet_MuTau_Loose"].array()
    trig_match_deep = tree["trig_match_DeepTau_MuTau"].array()
    pass_probe = tree["pass_probe"].array()
    q_1 = tree["q_1"].array()
    q_2 = tree["q_2"].array()

def ss_weight(q1, q2):
    return 1 if q1 != q2 else -1

bins_pt = [20, 24, 28, 32, 36, 40, 50, 70, 150]
bins_pt_array = array('d', bins_pt)

hist_total_pt = ROOT.TH1F("hist_total_pt", "", len(bins_pt) - 1, bins_pt_array)
hist_num_pt_loose = ROOT.TH1F("hist_num_pt_loose", "", len(bins_pt) - 1, bins_pt_array)
hist_num_pt_deep = ROOT.TH1F("hist_num_pt_deep", "", len(bins_pt) - 1, bins_pt_array)

for i in range(len(pt_2)):
    if pass_probe[i] and hlt_24[i]:
        weight = ss_weight(q_1[i], q_2[i])  
        hist_total_pt.Fill(pt_2[i], weight)
        if hlt_mutau[i] and trig_match_loose[i]:
            hist_num_pt_loose.Fill(pt_2[i], weight)
        if hlt_mutau[i] and trig_match_deep[i]:
            hist_num_pt_deep.Fill(pt_2[i], weight)

def make_efficiency_hist(numerator, denominator, name):
    hist = numerator.Clone(name)
    for i in range(1, hist.GetNbinsX() + 1):
        num = numerator.GetBinContent(i)
        den = denominator.GetBinContent(i)
        eff = num / den if den != 0 else 0
        err = sqrt(eff * (1 - eff) / den) if den > 0 and 0 <= eff <= 1 else 0
        hist.SetBinContent(i, eff)
        hist.SetBinError(i, err)
    return hist

eff_loose = make_efficiency_hist(hist_num_pt_loose, hist_total_pt, "eff_loose")
eff_deep = make_efficiency_hist(hist_num_pt_deep, hist_total_pt, "eff_deep")

def make_ratio_hist(num, den, name):
    hist = num.Clone(name)
    for i in range(1, hist.GetNbinsX() + 1):
        n = num.GetBinContent(i)
        d = den.GetBinContent(i)
        e_n = num.GetBinError(i)
        e_d = den.GetBinError(i)
        r = n / d if d > 0 else 0
        err = sqrt((e_n / d)**2 + (n * e_d / d**2)**2) if n > 0 and d > 0 else 0
        hist.SetBinContent(i, r)
        hist.SetBinError(i, err)
    return hist

ratio_hist = make_ratio_hist(eff_loose, eff_deep, "ratio")

def plot_combined_efficiency(eff1, eff2, ratio, save_path):
    canvas = ROOT.TCanvas("canvas", "Canvas", 850, 850)
    pad1 = ROOT.TPad("pad1", "pad1", 0.0, 0.30, 1.0, 1.0)
    pad2 = ROOT.TPad("pad2", "pad2", 0.0, 0.0, 1.0, 0.27)
    pad1.SetBottomMargin(0.013)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.35)
    pad1.SetLeftMargin(0.15)
    pad2.SetLeftMargin(0.15)
    pad1.SetRightMargin(0.25)
    pad2.SetRightMargin(0.25)
    pad1.SetGrid()
    pad2.SetGrid()
    pad1.Draw()
    pad2.Draw()

    pad1.cd()
    frame1 = ROOT.TH1F("frame1", "", 100, 10, 150)
    frame1.SetStats(0)
    frame1.SetMinimum(0)
    frame1.SetMaximum(1.1)
    frame1.GetYaxis().SetTitle("L1+HLT Efficiency")
    frame1.GetYaxis().SetTitleSize(0.05)
    frame1.GetYaxis().SetLabelSize(0.04)
    frame1.GetXaxis().SetLabelSize(0)
    frame1.Draw()

    eff1.SetLineColor(ROOT.kRed)
    eff1.SetMarkerColor(ROOT.kRed)
    eff1.SetMarkerStyle(20)
    eff1.SetMarkerSize(0.9)
    eff1.SetLineWidth(2)
    eff1.Draw("EP SAME")

    eff2.SetLineColor(ROOT.kBlack)
    eff2.SetMarkerColor(ROOT.kBlack)
    eff2.SetMarkerStyle(20)
    eff2.SetMarkerSize(0.9)
    eff2.SetLineWidth(2)
    eff2.Draw("EP SAME")

    legend = ROOT.TLegend(0.77, 0.5, 0.97, 0.65)
    legend.AddEntry(eff1, "ParticleNet", "lp")
    legend.AddEntry(eff2, "DeepTau", "lp")
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.16, 0.91, "Era 2024I")

    pad2.cd()
    frame2 = ROOT.TH1F("frame2", "", 100, 10, 150)
    frame2.SetStats(0)
    frame2.SetMinimum(0.9)
    frame2.SetMaximum(1.4)
    frame2.GetYaxis().SetTitle("Ratio")
    frame2.GetYaxis().SetTitleOffset(0.6)
    frame2.GetYaxis().SetTitleSize(0.12)
    frame2.GetYaxis().SetLabelSize(0.10)
    frame2.GetXaxis().SetTitle("Offline p_{T}^{#tau} GeV")
    frame2.GetXaxis().SetTitleSize(0.12)
    frame2.GetXaxis().SetLabelSize(0.10)
    frame2.GetYaxis().SetNdivisions(505)
    frame2.Draw()

    ratio.SetMarkerColor(ROOT.kBlack)
    ratio.SetLineColor(ROOT.kBlack)
    ratio.SetMarkerStyle(20)
    ratio.SetMarkerSize(0.9)
    ratio.SetLineWidth(2)
    ratio.Draw("EP SAME")

    canvas.SaveAs(save_path)
    canvas.Close()

output_path = os.path.join(root_dir, f"combined_efficiency_pt_{root_filename}_SSsub.png")
plot_combined_efficiency(eff_loose, eff_deep, ratio_hist, output_path)
