import ROOT
import uproot
import os
import numpy as np
from array import array
from math import sqrt, pi
import getpass
from tqdm import tqdm
import argparse

ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
user = getpass.getuser()

parser = argparse.ArgumentParser(description="Data vs MC efficiency plotting with year flag")
parser.add_argument("--year", type=int, default=2024, help="Year of the dataset (default: 2024)")
args = parser.parse_args()
year = args.year

file_data = f"/eos/user/{user[0]}/{user}/analysis/{year}/Data/Muon_Run{year}_mutau.root"
file_mc   = f"/eos/user/{user[0]}/{user}/analysis/{year}/DY/DYto2Tau-4Jets_Bin-MLL-50_Fil-MuTauh_mutau.root"

base_outdir = f"/eos/user/{user[0]}/{user}/analysis/{year}/plots"
output_dir  = os.path.join(base_outdir, f"Data_MC_plots_{year}")
os.makedirs(output_dir, exist_ok=True)

TRIGGERS = ["mutau","etau","ditau","ditaujet","vbfsingletau","vbfditau"]

DM_FILTERS = [[0],[1],[10],[11],[10,11],None]

MODES = ["L1","L1HLT","HLT"]

ALGOS = ["pnet","deeptau"]

TRIG_MAP = {
    "mutau":       {"l1":"L1_mutau","pnet_hlt":"HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1","pnet_match":"trig_match_PNet_MuTau_Loose","deep_match":"trig_match_DeepTau_MuTau"},
    "etau":        {"l1":"L1_etau","pnet_hlt":"HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Tight_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_ETau_Tight","deep_match":"trig_match_DeepTau_ETau"},
    "ditau":       {"l1":"L1_ditau","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_DiTau_Medium","deep_match":"trig_match_DeepTau_DiTau"},
    "ditaujet":    {"l1":"L1_ditaujet","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_DiTauJet","deep_match":"trig_match_DeepTau_DiTauJet"},
    "vbfsingletau":{"l1":"L1_vbfsingletau","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_VBFSingleTau","deep_match":"trig_match_DeepTau_VBFSingleTau"},
    "vbfditau":    {"l1":"L1_vbfditau","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1","pnet_match":"trig_match_PNet_VBFDiTau","deep_match":"trig_match_DeepTau_VBFDiTau"},
}

PT_CUTS = {"mutau":30,"ditau":50,"ditaujet":50,"vbfditau":30,"vbfsingletau":50,"etau":35}

TRIG_DISPLAY = {
    "mutau":"MuTau","etau":"ETau","ditau":"DiTau","ditaujet":"DiTauJet","vbfsingletau":"VBF SingleTau","vbfditau":"VBF DiTau"
}

ALGO_DISPLAY = {"pnet":"ParticleNet","deeptau":"DeepTau","l1":"L1"}

eta_bins = np.linspace(-2.3, 2.3, 12)

phi_bins = np.linspace(-pi, pi, 12)

npv_bins = np.array([0, 10, 20, 30, 40, 50, 60, 80], dtype=float)

pt_bins_list = [20, 24, 28, 32, 36, 40, 50, 70, 150]

pt_bins = np.array(pt_bins_list, dtype=float)

VAR_CFG = {
    "pt_2": ("pt_2", pt_bins, r"Offline #tau_{h} p_{T} [GeV]", (float(pt_bins[0]), float(pt_bins[-1]))),
    "eta_2": ("eta_2", eta_bins, r"Offline #tau_{h} #eta", (-2.3, 2.3)),
    "phi_2": ("phi_2", phi_bins, r"Offline #tau_{h} #phi", (-pi, pi)),
    "PV_npvsGood": ("PV_npvsGood", npv_bins, "Number of Offline Reconstructed Primary Vertices", (0, 80)),
}

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

def plot_data_mc_ratio(eff_data, eff_mc, ratio, x_range, x_title, ytitle, trig_display, algo_display, dm_tag, save_base, pt_cut=None, show_pt_cut=False):
    canvas = ROOT.TCanvas("canvas", "Canvas", 850, 850)
    pad1 = ROOT.TPad("pad1", "pad1", 0.0, 0.30, 1.0, 1.0)
    pad2 = ROOT.TPad("pad2", "pad2", 0.0, 0.0, 1.0, 0.27)
    pad1.SetBottomMargin(0.013)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.35)
    pad1.SetLeftMargin(0.15)
    pad2.SetLeftMargin(0.15)
    pad1.SetRightMargin(0.05)
    pad2.SetRightMargin(0.05)
    pad1.SetGrid()
    pad2.SetGrid()
    pad1.SetTicks(1,1)
    pad2.SetTicks(1,1)
    pad1.Draw()
    pad2.Draw()
    pad1.cd()
    xmin, xmax = x_range
    frame1 = ROOT.TH1F("frame1_dm", "", 100, xmin, xmax)
    frame1.SetStats(0)
    frame1.SetMinimum(0.0)
    frame1.SetMaximum(1.1)
    frame1.GetYaxis().SetTitle(ytitle)
    frame1.GetXaxis().SetLabelSize(0)
    frame1.Draw()
    eff_data.SetLineColor(ROOT.kRed)
    eff_data.SetMarkerColor(ROOT.kRed)
    eff_data.SetMarkerStyle(20)
    eff_data.SetMarkerSize(0.9)
    eff_data.SetLineWidth(2)
    eff_data.Draw("EP SAME")
    eff_mc.SetLineColor(ROOT.kBlack)
    eff_mc.SetMarkerColor(ROOT.kBlack)
    eff_mc.SetMarkerStyle(24)
    eff_mc.SetMarkerSize(0.9)
    eff_mc.SetLineWidth(2)
    eff_mc.Draw("EP SAME")
    legend = ROOT.TLegend(0.62, 0.02, 0.97, 0.27)
    legend.AddEntry(eff_data, "Data", "lp")
    legend.AddEntry(eff_mc,   "MC",   "lp")
    if show_pt_cut and pt_cut is not None:
        legend.AddEntry(0, f"Offline #tau p_{{T}} < {pt_cut} GeV", "")
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetTextSize(0.035)
    legend.Draw()
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.05)
    latex.DrawLatex(0.16, 0.92, "CMS #it{Preliminary}")
    latex.SetTextSize(0.042)
    latex.DrawLatex(0.16, 0.86, f"{trig_display} {algo_display} Monitoring Trigger (DM {dm_tag})")
    pad2.cd()
    frame2 = ROOT.TH1F("frame2_dm", "", 100, xmin, xmax)
    frame2.SetStats(0)
    frame2.SetMinimum(0.8)
    frame2.SetMaximum(1.2)
    frame2.GetYaxis().SetTitle("Data / MC")
    frame2.GetYaxis().SetTitleOffset(0.6)
    frame2.GetYaxis().SetTitleSize(0.12)
    frame2.GetYaxis().SetLabelSize(0.10)
    frame2.GetXaxis().SetTitle(x_title)
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
    canvas.SaveAs(save_base + ".png")
    canvas.SaveAs(save_base + ".pdf")
    out_root = ROOT.TFile(save_base + ".root", "RECREATE")
    eff_data.Write()
    eff_mc.Write()
    ratio.Write()
    out_root.Close()
    canvas.Close()

ALL_BRANCHES = [
    "pt_2","eta_2","phi_2","PV_npvsGood",
    "q_1","q_2","dm_2","pass_probe",
    "HLT_IsoMu24","trig_match_single_muon","Flag_METFilters",
]

for k,cfg in TRIG_MAP.items():
    ALL_BRANCHES += [cfg["l1"], cfg["pnet_hlt"], cfg["deep_hlt"], cfg["pnet_match"], cfg["deep_match"]]

ALL_BRANCHES = sorted(set(ALL_BRANCHES))

def read_arrays(path):
    with uproot.open(path) as f:
        tree = f["tree"]
        return tree.arrays(ALL_BRANCHES, library="np")

arrs_data = read_arrays(file_data)

arrs_mc   = read_arrays(file_mc)

pt_2_d = arrs_data["pt_2"]

eta_2_d = arrs_data["eta_2"]

phi_2_d = arrs_data["phi_2"]

npv_d = arrs_data["PV_npvsGood"]

q1_d = arrs_data["q_1"]

q2_d = arrs_data["q_2"]

pass_probe_d = arrs_data["pass_probe"].astype(bool)

hlt_single_d = arrs_data.get("HLT_IsoMu24", np.zeros_like(pt_2_d)).astype(bool)

match_mu_d = arrs_data.get("trig_match_single_muon", np.zeros_like(pt_2_d)).astype(bool)

met_filter_d = arrs_data.get("Flag_METFilters", np.zeros_like(pt_2_d)).astype(bool)

base_mask_d = (pass_probe_d & hlt_single_d & met_filter_d & (np.abs(eta_2_d) < 2.3) & match_mu_d)

weights_d = np.where(q1_d != q2_d, 1.0, -1.0)

pt_2_m = arrs_mc["pt_2"]

eta_2_m = arrs_mc["eta_2"]

phi_2_m = arrs_mc["phi_2"]

npv_m = arrs_mc["PV_npvsGood"]

q1_m = arrs_mc["q_1"]

q2_m = arrs_mc["q_2"]

pass_probe_m = arrs_mc["pass_probe"].astype(bool)

hlt_single_m = arrs_mc.get("HLT_IsoMu24", np.zeros_like(pt_2_m)).astype(bool)

match_mu_m = arrs_mc.get("trig_match_single_muon", np.zeros_like(pt_2_m)).astype(bool)

met_filter_m = arrs_mc.get("Flag_METFilters", np.zeros_like(pt_2_m)).astype(bool)

base_mask_m = (pass_probe_m & hlt_single_m & met_filter_m & (np.abs(eta_2_m) < 2.3) & match_mu_m)

weights_m = np.where(q1_m != q2_m, 1.0, -1.0)

def binned_sum(values, mask, weights, bins):
    sel = (np.ones_like(values, dtype=bool) if mask is True else mask)
    bins_arr = np.asarray(bins, dtype=float)
    hist, _ = np.histogram(values[sel], bins=bins_arr, weights=weights[sel])
    return hist

def make_eff_hist_from_counts(num_counts, den_counts, name, bins_edges):
    bins_arr = np.asarray(bins_edges, dtype=float)
    h = ROOT.TH1F(name, "", len(bins_arr)-1, array('d', bins_arr))
    h.SetStats(0)
    for ib in range(1, h.GetNbinsX()+1):
        num = float(num_counts[ib-1])
        den = float(den_counts[ib-1])
        eff = (num/den) if den > 0 else 0.0
        err = (np.sqrt(eff*(1.0-eff)/den) if den > 0 and 0.0 <= eff <= 1.0 else 0.0)
        h.SetBinContent(ib, eff)
        h.SetBinError(ib, err)
    return h

def eff_for_algo_var(arrs, base_mask, weights, trig_key, dm_filter, mode, algo, var_key, var_vals, bins_edges, pt_cut):
    cfg = TRIG_MAP[trig_key]
    l1_bits = arrs[cfg["l1"]].astype(bool)
    if algo == "pnet":
        hlt_bit = arrs[cfg["pnet_hlt"]].astype(bool)
        match   = arrs[cfg["pnet_match"]].astype(bool)
    elif algo == "deeptau":
        hlt_bit = arrs[cfg["deep_hlt"]].astype(bool)
        match   = arrs[cfg["deep_match"]].astype(bool)
    else:
        hlt_bit = np.zeros_like(l1_bits, dtype=bool)
        match   = np.zeros_like(l1_bits, dtype=bool)
    if dm_filter is None:
        dm_mask = True
    else:
        dm_mask = np.isin(arrs["dm_2"], np.array(dm_filter, dtype=arrs["dm_2"].dtype))
    pt_mask = True if var_key == "pt_2" else (arrs["pt_2"] >= pt_cut)
    if mode in ("L1", "L1HLT"):
        den_mask = base_mask & (pt_mask if isinstance(pt_mask, np.ndarray) else True) & (dm_mask if isinstance(dm_mask, np.ndarray) else True)
    else:
        den_mask = base_mask & l1_bits & (pt_mask if isinstance(pt_mask, np.ndarray) else True) & (dm_mask if isinstance(dm_mask, np.ndarray) else True)
    if mode == "L1":
        num_mask = den_mask & l1_bits
    else:
        num_mask = den_mask & l1_bits & hlt_bit & match
    den_counts = binned_sum(var_vals, den_mask, weights, bins_edges)
    num_counts = binned_sum(var_vals, num_mask, weights, bins_edges)
    return make_eff_hist_from_counts(num_counts, den_counts, f"eff_{algo}_{trig_key}_{mode}", bins_edges)

for trig in tqdm(TRIGGERS, desc="Triggers", unit="trig"):
    trig_dir = os.path.join(output_dir, trig)
    os.makedirs(trig_dir, exist_ok=True)
    for m in MODES:
        os.makedirs(os.path.join(trig_dir, m), exist_ok=True)
    pt_cut = PT_CUTS[trig]
    trig_disp = TRIG_DISPLAY.get(trig, trig)
    for dm_filter in DM_FILTERS:
        dm_tag = ("inc" if dm_filter is None else "+".join(map(str, dm_filter)))
        for var_key, (branch, bins_edges, x_title, x_range) in VAR_CFG.items():
            var_d = arrs_data[branch]
            var_m = arrs_mc[branch]
            show_pt_cut = (var_key != "pt_2")
            algo_tag = "l1"
            eff_d = eff_for_algo_var(arrs_data, base_mask_d, weights_d, trig, dm_filter, "L1", algo_tag, var_key, var_d, bins_edges, pt_cut)
            eff_m = eff_for_algo_var(arrs_mc,   base_mask_m, weights_m, trig, dm_filter, "L1", algo_tag, var_key, var_m, bins_edges, pt_cut)
            ratio = make_ratio_hist(eff_d, eff_m, f"{algo_tag}_ratio_data_mc_{trig}_L1_{dm_tag}_{var_key}")
            ytitle = "L1 Efficiency"
            label_algo = ALGO_DISPLAY["l1"]
            save_base = os.path.join(trig_dir, "L1", f"{trig}_{var_key}_{algo_tag}_dm_{dm_tag}_L1")
            plot_data_mc_ratio(eff_d, eff_m, ratio, x_range, x_title, ytitle, trig_disp, label_algo, dm_tag, save_base, pt_cut=pt_cut, show_pt_cut=show_pt_cut)
            for mode in ("L1HLT", "HLT"):
                for algo in ALGOS:
                    eff_d = eff_for_algo_var(arrs_data, base_mask_d, weights_d, trig, dm_filter, mode, algo, var_key, var_d, bins_edges, pt_cut)
                    eff_m = eff_for_algo_var(arrs_mc,   base_mask_m, weights_m, trig, dm_filter, mode, algo, var_key, var_m, bins_edges, pt_cut)
                    ratio = make_ratio_hist(eff_d, eff_m, f"{algo}_ratio_data_mc_{trig}_{mode}_{dm_tag}_{var_key}")
                    ytitle = ("L1+HLT Efficiency" if mode == "L1HLT" else "HLT Efficiency (factorized)")
                    label_algo = ALGO_DISPLAY[algo]
                    save_base = os.path.join(trig_dir, mode, f"{trig}_{var_key}_{algo}_dm_{dm_tag}_{mode}")
                    plot_data_mc_ratio(eff_d, eff_m, ratio, x_range, x_title, ytitle, trig_disp, label_algo, dm_tag, save_base, pt_cut=pt_cut, show_pt_cut=show_pt_cut)

print("Done. Outputs in:", output_dir)
