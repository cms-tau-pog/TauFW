#!/usr/bin/env python3
import ROOT, uproot, os, numpy as np
from array import array
from math import sqrt, pi
import getpass
from tqdm import tqdm

ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
user = getpass.getuser()

file_data = f"/eos/user/{user[0]}/{user}/analysis/2024/Data/Muon_Run2024_mutau.root"
file_mc   = f"/eos/user/{user[0]}/{user}/analysis/2024/DY/DYto2Tau-4Jets_Bin-MLL-50_Fil-MuTauh_mutau.root"

base_outdir     = f"/eos/user/{user[0]}/{user}/analysis/2024/plots"
output_dir_data = os.path.join(base_outdir, "Data_pnet_deeptau_2024")
output_dir_mc   = os.path.join(base_outdir, "MC_pnet_deeptau_2024")
os.makedirs(output_dir_data, exist_ok=True)
os.makedirs(output_dir_mc,   exist_ok=True)

TRIGGERS   = ["mutau","etau","ditau","ditaujet","vbfsingletau","vbfditau"]
DM_FILTERS = [[0],[1],[10],[11],[10,11],None]
MODES      = ["L1","L1HLT","HLT"]

TRIG_MAP = {
    "mutau":       {"l1":"L1_mutau","pnet_hlt":"HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1","pnet_match":"trig_match_PNet_MuTau_Loose","deep_match":"trig_match_DeepTau_MuTau"},
    "etau":        {"l1":"L1_etau","pnet_hlt":"HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Tight_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_ETau_Tight","deep_match":"trig_match_DeepTau_ETau"},
    "ditau":       {"l1":"L1_ditau","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_DiTau_Medium","deep_match":"trig_match_DeepTau_DiTau"},
    "ditaujet":    {"l1":"L1_ditaujet","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_DiTauJet","deep_match":"trig_match_DeepTau_DiTauJet"},
    "vbfsingletau":{"l1":"L1_vbfsingletau","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1","pnet_match":"trig_match_PNet_VBFSingleTau","deep_match":"trig_match_DeepTau_VBFSingleTau"},
    "vbfditau":    {"l1":"L1_vbfditau","pnet_hlt":"HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1","deep_hlt":"HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1","pnet_match":"trig_match_PNet_VBFDiTau","deep_match":"trig_match_DeepTau_VBFDiTau"},
}

PT_CUTS = {"mutau":30,"ditau":50,"ditaujet":50,"vbfditau":30,"vbfsingletau":50,"etau":35}

TRIG_DISPLAY = {"mutau":"MuTau","etau":"ETau","ditau":"DiTau","ditaujet":"DiTauJet","vbfsingletau":"VBF SingleTau","vbfditau":"VBF DiTau"}

pt_bins  = [20,24,28,32,36,40,50,70,150]
eta_bins = np.linspace(-2.3, 2.3, 12)
phi_bins = np.linspace(-pi, pi, 12)
npv_bins = np.array([0,10,20,30,40,50,60,80], dtype=float)

VAR_CFG = {
    "pt_2":        ("pt_2", np.array(pt_bins, dtype=float), r"Offline #tau_{h} p_{T} [GeV]", (float(pt_bins[0]), float(pt_bins[-1]))),
    "eta_2":       ("eta_2", eta_bins, r"Offline #tau_{h} #eta", (-2.3, 2.3)),
    "phi_2":       ("phi_2", phi_bins, r"Offline #tau_{h} #phi", (-pi, pi)),
    "PV_npvsGood": ("PV_npvsGood", npv_bins, "Number of Offline Reconstructed Primary Vertices", (0, 80)),
}

ALL_BRANCHES = [
    "pt_2","eta_2","phi_2","PV_npvsGood","q_1","q_2","dm_2","pass_probe",
    "HLT_IsoMu24","trig_match_single_muon","Flag_METFilters",
]
for k,cfg in TRIG_MAP.items():
    ALL_BRANCHES += [cfg["l1"], cfg["pnet_hlt"], cfg["deep_hlt"], cfg["pnet_match"], cfg["deep_match"]]
ALL_BRANCHES = sorted(set(ALL_BRANCHES))

def make_ratio_hist(num, den, name):
    h = num.Clone(name); h.Reset(); h.SetStats(0)
    for i in range(1, h.GetNbinsX()+1):
        n, d = num.GetBinContent(i), den.GetBinContent(i)
        en, ed = num.GetBinError(i), den.GetBinError(i)
        r = n/d if d>0 else 0
        err = sqrt((en/d)**2 + (n*ed/d**2)**2) if n>0 and d>0 else 0
        h.SetBinContent(i, r); h.SetBinError(i, err)
    return h

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
        num = float(num_counts[ib-1]); den = float(den_counts[ib-1])
        eff = (num/den) if den>0 else 0.0
        err = (np.sqrt(eff*(1.0-eff)/den) if den>0 and 0.0<=eff<=1.0 else 0.0)
        h.SetBinContent(ib, eff); h.SetBinError(ib, err)
    return h

def process_combo(arrs, base_mask, weights, dm_filter, trig_key, mode, var_name, bins_edges, pt_cut):
    cfg = TRIG_MAP[trig_key]
    l1_bits = arrs[cfg["l1"]].astype(bool)
    hlt_pnet = arrs[cfg["pnet_hlt"]].astype(bool)
    hlt_deep = arrs[cfg["deep_hlt"]].astype(bool)
    match_pnet = arrs[cfg["pnet_match"]].astype(bool)
    match_deep = arrs[cfg["deep_match"]].astype(bool)
    var_vals = arrs[var_name]
    if dm_filter is None:
        dm_mask = True; dm_tag = "inc"
    else:
        dm_mask = np.isin(arrs["dm_2"], np.array(dm_filter, dtype=arrs["dm_2"].dtype))
        dm_tag = "+".join(map(str, dm_filter))
    pt_mask = True if var_name == "pt_2" else (arrs["pt_2"] >= pt_cut)
    if mode in ("L1","L1HLT"):
        den_mask = base_mask & (pt_mask if isinstance(pt_mask, np.ndarray) else True) & (dm_mask if isinstance(dm_mask, np.ndarray) else True)
    else:
        den_mask = base_mask & l1_bits & (pt_mask if isinstance(pt_mask, np.ndarray) else True) & (dm_mask if isinstance(dm_mask, np.ndarray) else True)
    if mode == "L1":
        num_L1_mask = den_mask & l1_bits
        den_counts = binned_sum(var_vals, den_mask, weights, bins_edges)
        num_L1 = binned_sum(var_vals, num_L1_mask, weights, bins_edges)
        return {"eff_L1": make_eff_hist_from_counts(num_L1, den_counts, "eff_L1", bins_edges), "dm_tag": dm_tag}
    num_pnet_mask = den_mask & l1_bits & hlt_pnet & match_pnet
    num_deep_mask = den_mask & l1_bits & hlt_deep & match_deep
    den_counts = binned_sum(var_vals, den_mask, weights, bins_edges)
    num_pnet = binned_sum(var_vals, num_pnet_mask, weights, bins_edges)
    num_deep = binned_sum(var_vals, num_deep_mask, weights, bins_edges)
    eff_p = make_eff_hist_from_counts(num_pnet, den_counts, "eff_pnet", bins_edges)
    eff_d = make_eff_hist_from_counts(num_deep, den_counts, "eff_deeptau", bins_edges)
    ratio  = make_ratio_hist(eff_p, eff_d, "ratio_pnet_over_deeptau")
    return {"eff_pnet": eff_p, "eff_deeptau": eff_d, "ratio": ratio, "dm_tag": dm_tag}

def draw_header(trig_display, dm_tag, mid_label):
    tx = ROOT.TLatex(); tx.SetNDC()
    tx.SetTextSize(0.05); tx.DrawLatex(0.16, 0.92, "CMS #it{Preliminary}")
    tx.SetTextSize(0.042); tx.DrawLatex(0.16, 0.86, f"{trig_display} {mid_label} (DM {dm_tag})")
    return tx

def plot_two_with_ratio(eff1, eff2, ratio, x_range, x_title, ytitle, trig_disp, dm_tag, save_base, pt_cut=None, show_pt_cut=False, lab1="ParticleNet", lab2="DeepTau"):
    c = ROOT.TCanvas("c", "c", 850, 850)
    p1 = ROOT.TPad("p1","p1",0,0.30,1,1); p2 = ROOT.TPad("p2","p2",0,0.0,1,0.27)
    for p in (p1,p2): p.SetLeftMargin(0.15); p.SetRightMargin(0.05); p.SetGrid(); p.SetTicks(1,1)
    p1.SetBottomMargin(0.013); p2.SetTopMargin(0.05); p2.SetBottomMargin(0.35)
    p1.Draw(); p2.Draw()

    p1.cd()
    xmin, xmax = x_range
    fr1 = ROOT.TH1F("fr1","",100,xmin,xmax)
    fr1.SetStats(0); fr1.SetMinimum(0.0); fr1.SetMaximum(1.1)
    fr1.GetYaxis().SetTitle(ytitle); fr1.GetXaxis().SetLabelSize(0); fr1.Draw()

    eff1.SetLineColor(ROOT.kRed+1);   eff1.SetMarkerColor(ROOT.kRed+1)
    eff1.SetMarkerStyle(20);          eff1.SetMarkerSize(0.9); eff1.SetLineWidth(2)
    eff2.SetLineColor(ROOT.kBlack);   eff2.SetMarkerColor(ROOT.kBlack)
    eff2.SetMarkerStyle(24);          eff2.SetMarkerSize(0.9); eff2.SetLineWidth(2)
    eff1.Draw("EP SAME"); eff2.Draw("EP SAME")

    draw_header(trig_disp, dm_tag, "DeepTau Monitoring Trigger")
    leg = ROOT.TLegend(0.62, 0.02, 0.97, 0.27)
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.035)
    leg.AddEntry(eff1, lab1, "lp"); leg.AddEntry(eff2, lab2, "lp")
    if show_pt_cut and pt_cut is not None: leg.AddEntry(0, f"Offline #tau p_{{T}} < {pt_cut} GeV", "")
    leg.Draw()

    p2.cd()
    fr2 = ROOT.TH1F("fr2","",100,xmin,xmax)
    fr2.SetStats(0); fr2.SetMinimum(0.8); fr2.SetMaximum(1.2)
    fr2.GetYaxis().SetTitle(f"{lab1} / {lab2}")
    fr2.GetYaxis().SetTitleOffset(0.6); fr2.GetYaxis().SetTitleSize(0.12); fr2.GetYaxis().SetLabelSize(0.10)
    fr2.GetXaxis().SetTitle(x_title);   fr2.GetXaxis().SetTitleSize(0.12); fr2.GetXaxis().SetLabelSize(0.10)
    fr2.GetYaxis().SetNdivisions(505); fr2.Draw()
    ratio.SetMarkerColor(ROOT.kBlack); ratio.SetLineColor(ROOT.kBlack)
    ratio.SetMarkerStyle(20); ratio.SetMarkerSize(0.9); ratio.SetLineWidth(2)
    ratio.Draw("EP SAME")

    c.SaveAs(save_base + ".png"); c.SaveAs(save_base + ".pdf")
    f = ROOT.TFile(save_base + ".root","RECREATE")
    eff1.SetName("eff_pnet"); eff2.SetName("eff_deeptau"); ratio.SetName("ratio_pnetOverdeeptau")
    eff1.Write(); eff2.Write(); ratio.Write(); f.Close()
    c.Close()

def plot_single_l1(eff, x_range, x_title, trig_disp, dm_tag, save_base, pt_cut=None, show_pt_cut=False):
    c = ROOT.TCanvas("c", "c", 850, 700)
    c.SetGrid()
    c.SetTicks(1,1)

    xmin, xmax = x_range
    fr = ROOT.TH1F("fr","",100,xmin,xmax)
    fr.SetStats(0)
    fr.SetMinimum(0.0)
    fr.SetMaximum(1.1)
    fr.GetYaxis().SetTitle("L1 Efficiency")
    fr.GetXaxis().SetTitle(x_title)
    fr.GetXaxis().SetTitleOffset(1.2) 
    fr.Draw()

    eff.SetMarkerStyle(20)
    eff.SetMarkerSize(0.9)
    eff.SetLineWidth(2)
    eff.SetMarkerColor(ROOT.kRed+1)
    eff.SetLineColor(ROOT.kRed+1)
    eff.Draw("EP SAME")

    draw_header(trig_disp, dm_tag, "L1 Monitoring Trigger")

    leg = ROOT.TLegend(0.62, 0.10, 0.97, 0.26)  # was (0.62, 0.04, 0.97, 0.20)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    leg.AddEntry(eff, "L1", "lp")
    if show_pt_cut and pt_cut is not None:
        leg.AddEntry(0, f"Offline #tau p_{{T}} < {pt_cut} GeV", "")
    leg.Draw()

    c.SaveAs(save_base + ".png")
    c.SaveAs(save_base + ".pdf")

    f = ROOT.TFile(save_base + ".root","RECREATE")
    eff.SetName("eff_L1")
    eff.Write()
    f.Close()
    c.Close()


for dataset_label, in_file, out_dir in [("2024 Data", file_data, output_dir_data), ("2024 MC", file_mc, output_dir_mc)]:
    os.makedirs(out_dir, exist_ok=True)
    with uproot.open(in_file) as f:
        arrs = f["tree"].arrays(ALL_BRANCHES, library="np")
    pt_2 = arrs["pt_2"]; eta_2 = arrs["eta_2"]
    q1 = arrs["q_1"]; q2 = arrs["q_2"]
    pass_probe = arrs["pass_probe"].astype(bool)
    hlt_single = arrs.get("HLT_IsoMu24", np.zeros_like(pt_2)).astype(bool)
    match_mu = arrs.get("trig_match_single_muon", np.zeros_like(pt_2)).astype(bool)
    met_filter = arrs.get("Flag_METFilters", np.zeros_like(pt_2)).astype(bool)
    base_mask = (pass_probe & hlt_single & met_filter & (np.abs(eta_2) < 2.3) & match_mu)
    weights = np.where(q1 != q2, 1.0, -1.0)

    for trig in tqdm(TRIGGERS, desc=f"Triggers ({dataset_label})", unit="trig"):
        trig_dir = os.path.join(out_dir, trig); os.makedirs(trig_dir, exist_ok=True)
        for m in MODES: os.makedirs(os.path.join(trig_dir, m), exist_ok=True)
        pt_cut = PT_CUTS[trig]; trig_disp = TRIG_DISPLAY.get(trig, trig)
        for dm_filter in DM_FILTERS:
            for mode in MODES:
                mode_dir = os.path.join(trig_dir, mode)
                for var_key, (branch, bins_edges, x_title, x_range) in VAR_CFG.items():
                    res = process_combo(arrs, base_mask, weights, dm_filter, trig, mode, branch, bins_edges, pt_cut)
                    dm_tag = "inc" if dm_filter is None else "+".join(map(str, dm_filter))
                    show_cut = (var_key != "pt_2")
                    if mode == "L1":
                        base = os.path.join(mode_dir, f"{trig}_{var_key}_l1_dm_{dm_tag}_L1")
                        plot_single_l1(res["eff_L1"], x_range, x_title, trig_disp, dm_tag, base, pt_cut=pt_cut, show_pt_cut=show_cut)
                    else:
                        base = os.path.join(mode_dir, f"{trig}_{var_key}_pnetVsdeeptau_dm_{dm_tag}_{mode}")
                        ytitle = "L1+HLT Efficiency" if mode=="L1HLT" else "HLT Efficiency (factorized)"
                        plot_two_with_ratio(res["eff_pnet"], res["eff_deeptau"], res["ratio"], x_range, x_title, ytitle, trig_disp, dm_tag, base, pt_cut=pt_cut, show_pt_cut=show_cut)

    print(f"All done for {dataset_label} -> {out_dir}")
