import ROOT
import uproot
import os
from array import array
from math import sqrt
from tqdm import tqdm
import getpass
import argparse

ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
user = getpass.getuser()

parser = argparse.ArgumentParser(description="L1+HLT eff vs pT with optional DM loop")
parser.add_argument("-dm", nargs="*", default=None)
args = parser.parse_args()

file_2024 = f"/eos/user/{user[0]}/{user}/analysis/2024/Data/Muon_Run2024_mutau.root"
output_dir = f"/eos/user/{user[0]}/{user}/analysis/2024/Data/eff_plots"
os.makedirs(output_dir, exist_ok=True)

if args.dm is None:
    dm_filter_list = [None]
elif len(args.dm) == 0:
    dm_filter_list = [[0], [1], [10], [11]]
elif len(args.dm) == 1 and args.dm[0].lower() == "inclusive":
    dm_filter_list = [None]
else:
    try:
        vals = [int(x) for x in args.dm]
        dm_filter_list = [[v] for v in vals]
    except ValueError:
        raise SystemExit(f"Invalid -dm values: {args.dm}")

pt_bins = [20, 24, 28, 32, 36, 40, 50, 70, 150]
pt_bin_array = array('d', pt_bins)

def ss_weight(q1, q2):
    return 1 if q1 != q2 else -1

def make_efficiency_hist(numerator, denominator, name):
    hist = numerator.Clone(name)
    hist.Reset()
    hist.SetStats(0)
    for i in range(1, hist.GetNbinsX() + 1):
        num = numerator.GetBinContent(i)
        den = denominator.GetBinContent(i)
        eff = num / den if den > 0 else 0
        err = sqrt(eff * (1 - eff) / den) if den > 0 and 0 <= eff <= 1 else 0
        hist.SetBinContent(i, eff)
        hist.SetBinError(i, err)
    return hist

def make_ratio_hist(num, den, name):
    hist = num.Clone(name)
    hist.Reset()
    hist.SetStats(0)
    for i in range(1, hist.GetNbinsX() + 1):
        n, d = num.GetBinContent(i), den.GetBinContent(i)
        en, ed = num.GetBinError(i), den.GetBinError(i)
        r = n / d if d > 0 else 0
        err = sqrt((en / d)**2 + (n * ed / d**2)**2) if n > 0 and d > 0 else 0
        hist.SetBinContent(i, r)
        hist.SetBinError(i, err)
    return hist

def process_file(path, era_label, dm_filter, tag):
    print(f"\nProcessing file for {era_label}: {path}")
    if dm_filter is None:
        print("DM selection: inclusive")
    else:
        print(f"DM selection: {dm_filter}")
    with uproot.open(path) as f:
        tree = f["tree"]
        pt_2  = tree["pt_2"].array()
        eta_2 = tree["eta_2"].array()
        q1    = tree["q_1"].array()
        q2    = tree["q_2"].array()
        dm_2  = tree["dm_2"].array()
        pass_probe = tree["pass_probe"].array()
        hlt = tree["HLT_IsoMu24"].array()
        hlt_pnet_mutau = tree["HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1"].array()
        hlt_dtau_mutau = tree["HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1"].array()
        match_pnet = tree["trig_match_PNet_MuTau_Loose"].array()
        match_deep = tree["trig_match_DeepTau_MuTau"].array()
        trig_match_single_muon = tree["trig_match_single_muon"].array()
        met_filter = tree["Flag_METFilters"].array()
    h_total    = ROOT.TH1F(f"htotal_{era_label}_{tag}", "", len(pt_bins)-1, pt_bin_array)
    h_num_pnet = ROOT.TH1F(f"hnum_pnet_{era_label}_{tag}", "", len(pt_bins)-1, pt_bin_array)
    h_num_deep = ROOT.TH1F(f"hnum_deep_{era_label}_{tag}", "", len(pt_bins)-1, pt_bin_array)
    for i in tqdm(range(len(pt_2)), desc=f"{era_label}", unit="evt"):
        base_sel = pass_probe[i] and hlt[i] and met_filter[i] and abs(eta_2[i]) < 2.3 and trig_match_single_muon[i]
        if not base_sel:
            continue
        if dm_filter is not None and int(dm_2[i]) not in dm_filter:
            continue
        w = ss_weight(q1[i], q2[i])
        h_total.Fill(pt_2[i], w)
        if hlt_pnet_mutau[i] and match_pnet[i]:
            h_num_pnet.Fill(pt_2[i], w)
        if hlt_dtau_mutau[i] and match_deep[i]:
            h_num_deep.Fill(pt_2[i], w)
    eff_pnet = make_efficiency_hist(h_num_pnet, h_total, f"eff_pnet_{era_label}_{tag}")
    eff_deep = make_efficiency_hist(h_num_deep, h_total, f"eff_deep_{era_label}_{tag}")
    ratio    = make_ratio_hist(eff_pnet, eff_deep, f"ratio_{era_label}_{tag}")
    return eff_pnet, eff_deep, ratio

def plot_eff_ratio(eff1, eff2, ratio, label, save_path):
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
    latex.DrawLatex(0.16, 0.91, f"{label}")
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
    print(f"Saved: {save_path}")

out_root = ROOT.TFile(os.path.join(output_dir, "efficiencies_2024.root"), "RECREATE")

for dm_filter in dm_filter_list:
    tag = "inclusive" if dm_filter is None else "dm_" + "_".join(str(x) for x in dm_filter)
    eff_pnet, eff_deep, ratio = process_file(file_2024, "2024", dm_filter, tag)
    png_path = os.path.join(output_dir, f"eff_ratio_2024_{tag}.png")
    plot_eff_ratio(eff_pnet, eff_deep, ratio, f"2024 ({tag})", png_path)
    eff_pnet.SetName(f"eff_pnet_2024_{tag}")
    eff_pnet.SetTitle(f"ParticleNet MuTau Trigger Efficiency (2024, {tag})")
    eff_pnet.GetXaxis().SetTitle("Offline p_{T}^{#tau} [GeV]")
    eff_pnet.GetYaxis().SetTitle("Efficiency")
    eff_deep.SetName(f"eff_deep_2024_{tag}")
    eff_deep.SetTitle(f"DeepTau MuTau Trigger Efficiency (2024, {tag})")
    eff_deep.GetXaxis().SetTitle("Offline p_{T}^{#tau} [GeV]")
    eff_deep.GetYaxis().SetTitle("Efficiency")
    ratio.SetName(f"ratio_2024_{tag}")
    ratio.SetTitle(f"ParticleNet / DeepTau Efficiency Ratio (2024, {tag})")
    ratio.GetXaxis().SetTitle("Offline p_{T}^{#tau} [GeV]")
    ratio.GetYaxis().SetTitle("Efficiency Ratio")
    out_root.cd()
    eff_pnet.Write()
    eff_deep.Write()
    ratio.Write()

out_root.Close()
print(f"Saved: {out_root.GetName()}")
