import ROOT
import uproot
import numpy as np
import argparse
import os
from array import array

ROOT.gROOT.SetBatch()

parser = argparse.ArgumentParser(description="Trigger Efficiency Plotter with SS Subtraction")
parser.add_argument("input_root_file", type=str, help="Path to the input ROOT file")
args = parser.parse_args()

root_file = args.input_root_file
root_dir = os.path.dirname(root_file) if os.path.dirname(root_file) else "."
root_filename = os.path.splitext(os.path.basename(root_file))[0]

with uproot.open(root_file) as file:
    tree = file["tree"]
    eta_2 = tree["eta_2"].array()
    pt_2 = tree["pt_2"].array()
    hlt_24 = tree["HLT_IsoMu24"].array()
    hlt_mu24 = tree["HLT_IsoMu24_eta2p1"].array()
    hlt_mutau = tree["HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1"].array()
    trig_match_deep = tree["trig_match_DeepTau_MuTau"].array()
    trig_match_loose = tree["trig_match_PNet_MuTau_Loose"].array()
    trig_match_medium = tree["trig_match_PNet_MuTau_Medium"].array()
    trig_match_tight = tree["trig_match_PNet_MuTau_Tight"].array()
    trig_match_single_muon = tree["trig_match_single_muon"].array()
    pass_tag = tree["pass_tag"].array()
    pass_probe = tree["pass_probe"].array()
    q_1 = tree["q_1"].array()
    q_2 = tree["q_2"].array()

def create_bins():
    return np.arange(0, 200, 20)

def ss_weight(q1, q2):
    return 1 if q1 != q2 else -1  # +1 for OS, -1 for SS

bins_eta = np.linspace(-2.5, 2.5, 11)
bins_eta_array = array('d', bins_eta)
bins_pt = create_bins()
bins_pt_array = array('d', bins_pt)

hist_total_eta_1 = ROOT.TH1F("hist_total_eta_1", "", len(bins_eta)-1, bins_eta_array)
hist_num_eta_1 = ROOT.TH1F("hist_num_eta_1", "", len(bins_eta)-1, bins_eta_array)
hist_total_pt_1 = ROOT.TH1F("hist_total_pt_1", "", len(bins_pt)-1, bins_pt_array)
hist_num_pt_1 = ROOT.TH1F("hist_num_pt_1", "", len(bins_pt)-1, bins_pt_array)

hist_total_eta_2 = ROOT.TH1F("hist_total_eta_2", "", len(bins_eta)-1, bins_eta_array)
hist_num_eta_2 = ROOT.TH1F("hist_num_eta_2", "", len(bins_eta)-1, bins_eta_array)
hist_total_pt_2 = ROOT.TH1F("hist_total_pt_2", "", len(bins_pt)-1, bins_pt_array)
hist_num_pt_2 = ROOT.TH1F("hist_num_pt_2", "", len(bins_pt)-1, bins_pt_array)

for i in range(len(eta_2)):
    weight = ss_weight(q_1[i], q_2[i])

    if pass_tag[i]:
        hist_total_eta_1.Fill(eta_2[i], weight)
        hist_total_pt_1.Fill(pt_2[i], weight)
        if hlt_mu24[i] and trig_match_single_muon[i]:
            hist_num_eta_1.Fill(eta_2[i], weight)
            hist_num_pt_1.Fill(pt_2[i], weight)

    if pass_probe[i] and hlt_24[i]:
        hist_total_eta_2.Fill(eta_2[i], weight)
        hist_total_pt_2.Fill(pt_2[i], weight)
        if hlt_mutau[i] and (trig_match_deep[i] or trig_match_loose[i] or trig_match_medium[i] or trig_match_tight[i]):
            hist_num_eta_2.Fill(eta_2[i], weight)
            hist_num_pt_2.Fill(pt_2[i], weight)

eff_1_eta = ROOT.TEfficiency(hist_num_eta_1, hist_total_eta_1)
eff_1_pt = ROOT.TEfficiency(hist_num_pt_1, hist_total_pt_1)
eff_2_eta = ROOT.TEfficiency(hist_num_eta_2, hist_total_eta_2)
eff_2_pt = ROOT.TEfficiency(hist_num_pt_2, hist_total_pt_2)

def create_root_plot(eff_graph, title, xlabel, trigger_label, save_path):
    canvas = ROOT.TCanvas("canvas", "Canvas", 600, 700)
    canvas.SetGrid()
    canvas.SetLeftMargin(0.12)
    canvas.SetRightMargin(0.05)
    canvas.SetBottomMargin(0.12)
    canvas.SetTopMargin(0.08)

    dummy_hist = ROOT.TH1F("dummy_hist", "", 1, -2.5, 2.5) if "eta" in xlabel else ROOT.TH1F("dummy_hist", "", 1, 0, 200)
    dummy_hist.SetStats(0)
    dummy_hist.GetXaxis().SetTitle(xlabel)
    dummy_hist.GetYaxis().SetTitle("HLT Efficiency")
    dummy_hist.GetYaxis().SetRangeUser(0, 1.1)
    dummy_hist.Draw()

    eff_graph.SetMarkerSize(0)
    eff_graph.SetLineColor(ROOT.kBlack)
    eff_graph.SetLineWidth(2)
    eff_graph.Draw("E1 SAME")

    latex = ROOT.TLatex()
    latex.SetTextSize(0.05)
    latex.SetTextAlign(22)
    latex.DrawLatexNDC(0.5, 0.94, trigger_label)

    canvas.SaveAs(save_path)
    canvas.Close()

eff_1_eta_plot_path = os.path.join(root_dir, f"efficiency_1_eta_{root_filename}_SSsub.png")
eff_1_pt_plot_path = os.path.join(root_dir, f"efficiency_1_pt_{root_filename}_SSsub.png")
eff_2_eta_plot_path = os.path.join(root_dir, f"efficiency_2_eta_{root_filename}_SSsub.png")
eff_2_pt_plot_path = os.path.join(root_dir, f"efficiency_2_pt_{root_filename}_SSsub.png")

create_root_plot(eff_1_eta, "Efficiency 1: Single Muon Trigger", "#tau #eta", "HLT_IsoMu24_eta2p1 (SS-subtracted)", eff_1_eta_plot_path)
create_root_plot(eff_1_pt, "Efficiency 1: Single Muon Trigger", "#tau p_{T} (GeV)", "HLT_IsoMu24_eta2p1 (SS-subtracted)", eff_1_pt_plot_path)
create_root_plot(eff_2_eta, "Efficiency 2: Mu+Tau Trigger", "#tau #eta", "HLT_MuTau (SS-subtracted)", eff_2_eta_plot_path)
create_root_plot(eff_2_pt, "Efficiency 2: Mu+Tau Trigger", "#tau p_{T} (GeV)", "HLT_MuTau (SS-subtracted)", eff_2_pt_plot_path)
