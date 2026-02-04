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

parser = argparse.ArgumentParser(description="Era efficiency plotting with optional ratio reference")
parser.add_argument("--year", type=int, default=2024, help="Year of the dataset")
parser.add_argument("--era", type=str, required=True, help="Eras to compare, e.g. BCDE")
parser.add_argument(
    "--ratio",
    type=str,
    default="total",
    help="Ratio reference: 'total' or an era label (e.g. B). Default: total"
)
args = parser.parse_args()

year = args.year
eras = list(args.era.upper())
# ---------------------------------------------------------
# ratio_ref controls the denominator of ratio plots
#
# --ratio total   -> Era / Total (default)
# --ratio B       -> Era / Era B
#
# If the reference is missing, ratio plots are skipped.
# ---------------------------------------------------------
ratio_ref = args.ratio

BASE_DATA_DIR = f"/eos/user/{user[0]}/{user}/analysis/{year}/Data"
BASE_OUT_DIR  = f"/eos/user/{user[0]}/{user}/analysis/{year}/plots"

output_dir = os.path.join(BASE_OUT_DIR, f"Data_{year}_{''.join(eras)}")
os.makedirs(output_dir, exist_ok=True)

# TOTAL_FILE = os.path.join(BASE_DATA_DIR, f"Muon_Run{year}_mutau.root")
TOTAL_FILE = None


ERA_FILE_PATTERN = os.path.join(
    BASE_DATA_DIR, "era_wise", f"Muon_Run{year}" + "{era}_mutau.root"
)

# =========================================================
# OPTIONAL: Override individual era ROOT files here
# =========================================================
# Use this if an era file is NOT located under:
#   BASE_DATA_DIR/era_wise/Muon_Run<year><era>_mutau.root
#
# Example:
# ERA_FILE_OVERRIDES = {
#     "B": "/eos/user/.../Muon_Run2024B_custom.root",
#     "C": "/eos/user/.../Muon_Run2024C_reReco.root",
# }
# =========================================================
ERA_FILE_OVERRIDES = {
    "D": f"/eos/user/{user[0]}/{user}/analysis/2024/Data/era_wise/Muon_Run2024D_mutau.root",
    "I": f"/eos/user/{user[0]}/{user}/analysis/2024/Data/era_wise/Muon_Run2024I_mutau.root"
}

def resolve_era_file(era):
    if era in ERA_FILE_OVERRIDES:
        path = ERA_FILE_OVERRIDES[era]
        return path if os.path.exists(path) else None
    path = ERA_FILE_PATTERN.format(era=era)
    return path if os.path.exists(path) else None

# Trigger paths to be processed
# Add/remove triggers here
TRIGGERS = ["mutau","etau","ditau","ditaujet","vbfsingletau","vbfditau"]

# Tau decay mode selections
# None = inclusive
DM_FILTERS = [[0],[1],[10],[11],[10,11],None]
MODES = ["L1","L1HLT","HLT"]

# Pnet, DeepTau or both
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
TRIG_DISPLAY = {"mutau":"MuTau","etau":"ETau","ditau":"DiTau","ditaujet":"DiTauJet","vbfsingletau":"VBF SingleTau","vbfditau":"VBF DiTau"}
ALGO_DISPLAY = {"pnet":"ParticleNet","deeptau":"DeepTau","l1":"L1"}

eta_bins = np.linspace(-2.3, 2.3, 12)
phi_bins = np.linspace(-pi, pi, 12)
npv_bins = np.array([0,10,20,30,40,50,60,80],dtype=float)
pt_bins  = np.array([20,24,28,32,36,40,50,70,150],dtype=float)

VAR_CFG = {
    "pt_2": ("pt_2", pt_bins, r"Offline #tau_{h} p_{T} [GeV]", (float(pt_bins[0]), float(pt_bins[-1]))),
    "eta_2": ("eta_2", eta_bins, r"Offline #tau_{h} #eta", (-2.3, 2.3)),
    "phi_2": ("phi_2", phi_bins, r"Offline #tau_{h} #phi", (-pi, pi)),
    "PV_npvsGood": ("PV_npvsGood", npv_bins, "Number of Offline Reconstructed Primary Vertices", (0, 80)),
}

colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen+2, ROOT.kMagenta, ROOT.kOrange+7, ROOT.kCyan+2]

def make_ratio_hist(num, den, name):
    h = num.Clone(name)
    h.Reset()
    for i in range(1, h.GetNbinsX()+1):
        n, d = num.GetBinContent(i), den.GetBinContent(i)
        en, ed = num.GetBinError(i), den.GetBinError(i)
        if d > 0:
            r = n / d
            err = sqrt((en/d)**2 + (n*ed/d**2)**2) if n > 0 else 0
        else:
            r, err = 0.0, 0.0
        h.SetBinContent(i, r)
        h.SetBinError(i, err)
    return h

def plot_total_vs_eras(
    eff_ref, eff_eras, ratios,
    x_range, x_title, ytitle,
    trig_display, algo_display, dm_tag,
    save_base, year, ref_label,
    pt_cut=None, show_pt_cut=False
):
    c = ROOT.TCanvas("c","c",850,850)

    pad1 = ROOT.TPad("pad1","pad1",0,0.30,1,1)
    pad1.SetBottomMargin(0.013)
    pad1.SetGridx(True)
    pad1.SetGridy(True)
    pad1.Draw()

    pad2 = None
    if eff_ref and ratios:
        pad2 = ROOT.TPad("pad2","pad2",0,0,1,0.27)
        pad2.SetTopMargin(0.05)
        pad2.SetBottomMargin(0.35)
        pad2.SetGridx(True)
        pad2.SetGridy(True)
        pad2.Draw()

    pad1.cd()
    xmin, xmax = x_range
    frame1 = ROOT.TH1F("frame1","",100,xmin,xmax)
    frame1.SetMinimum(0)
    frame1.SetMaximum(1.1)
    frame1.GetYaxis().SetTitle(ytitle)
    frame1.GetXaxis().SetLabelSize(0)
    frame1.Draw()

    leg = ROOT.TLegend(0.62, 0.18, 0.88, 0.32)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.030)
    leg.SetEntrySeparation(0.12)
    leg.SetTextAlign(12) 

    if eff_ref:
        eff_ref.SetMarkerStyle(20)
        eff_ref.SetLineColor(ROOT.kBlack)
        eff_ref.Draw("EP SAME")
        leg.AddEntry(eff_ref, f"Year {year} {ref_label}", "lp")

    for i,(era,h) in enumerate(eff_eras.items()):
        if ref_label == f"era {era}":
            continue
        h.SetMarkerStyle(24+i)
        h.SetLineColor(colors[i%len(colors)])
        h.Draw("EP SAME")
        leg.AddEntry(h, f"Year {year} era {era}", "lp")

    if show_pt_cut and pt_cut:
        leg.AddEntry(0, f"Offline #tau p_{{T}} < {pt_cut} GeV", "")

    leg.SetBorderSize(0)
    leg.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.DrawLatex(0.16,0.92,"CMS #it{Preliminary}")
    latex.DrawLatex(0.16,0.86,f"{trig_display} {algo_display} (DM {dm_tag})")

    if pad2:
        pad2.cd()
        frame2 = ROOT.TH1F("frame2","",100,xmin,xmax)
        frame2.SetMinimum(0.8)
        frame2.SetMaximum(1.2)
        if ref_label:
            frame2.GetYaxis().SetTitle(f"Era / {ref_label}")
        frame2.GetXaxis().SetTitle(x_title)
        frame2.Draw()

        for i,r in enumerate(ratios.values()):
            r.SetMarkerStyle(24+i)
            r.SetLineColor(colors[i%len(colors)])
            r.Draw("EP SAME")

    c.SaveAs(save_base + ".png")
    c.SaveAs(save_base + ".pdf")
    root_out = save_base + ".root"
    fout = ROOT.TFile(root_out, "RECREATE")

    if eff_ref:
        eff_ref.Write(f"eff_{ref_label.replace(' ','_')}")

    for era, h in eff_eras.items():
        h.Write(f"eff_{era}")

    for era, r in ratios.items():
        r.Write(f"ratio_{era}_over_{ref_label.replace(' ','_')}")

    fout.Close()
    c.Close()

def read_arrays(path):
    with uproot.open(path) as f:
        return f["tree"].arrays(ALL_BRANCHES, library="np")

ALL_BRANCHES = ["pt_2","eta_2","phi_2","PV_npvsGood","q_1","q_2","dm_2","pass_probe",
                "HLT_IsoMu24","trig_match_single_muon","Flag_METFilters"]

for cfg in TRIG_MAP.values():
    ALL_BRANCHES += list(cfg.values())

ALL_BRANCHES = sorted(set(ALL_BRANCHES))

print("Reading total file if it exists...")
if TOTAL_FILE and os.path.exists(TOTAL_FILE):
    arrs_total = read_arrays(TOTAL_FILE)
else:
    arrs_total = None
    if ratio_ref == "total":
        print("[INFO] Total file not provided – total-based ratios will be skipped.")

print("Reading era files:", eras, flush=True)

arrs_eras = {}
for era in eras:
    print(f"loading era {era}", flush=True)

    path = resolve_era_file(era)

    if not path:
        print(f"    [WARN] file for era {era} not found", flush=True)
        continue

    print(f"    -> using file: {path}", flush=True)

    arrs_eras[era] = read_arrays(path)
    print(f"    loaded era {era}", flush=True)

if not arrs_eras:
    raise RuntimeError("No valid era files found.")

def binned_sum(values, mask, weights, bins):
    sel = (np.ones_like(values,dtype=bool) if mask is True else mask)
    hist,_ = np.histogram(values[sel], bins=np.asarray(bins,dtype=float), weights=weights[sel])
    return hist

def make_eff_hist_from_counts(num_counts, den_counts, name, bins_edges):
    h = ROOT.TH1F(name,"",len(bins_edges)-1,array('d',np.asarray(bins_edges,dtype=float)))
    for ib in range(1,h.GetNbinsX()+1):
        num,den = float(num_counts[ib-1]), float(den_counts[ib-1])
        eff = num/den if den>0 else 0.0
        err = np.sqrt(eff*(1.0-eff)/den) if den>0 and 0<=eff<=1 else 0.0
        h.SetBinContent(ib,eff); h.SetBinError(ib,err)
    return h

def eff_for_algo_var(arrs, base_mask, weights, trig_key, dm_filter, mode, algo, var_key, var_vals, bins_edges, pt_cut):
    cfg = TRIG_MAP[trig_key]
    l1_bits = arrs[cfg["l1"]].astype(bool)
    if algo=="pnet": hlt_bit,match = arrs[cfg["pnet_hlt"]].astype(bool), arrs[cfg["pnet_match"]].astype(bool)
    elif algo=="deeptau": hlt_bit,match = arrs[cfg["deep_hlt"]].astype(bool), arrs[cfg["deep_match"]].astype(bool)
    else: hlt_bit,match = np.zeros_like(l1_bits), np.zeros_like(l1_bits)
    dm_mask = True if dm_filter is None else np.isin(arrs["dm_2"],np.array(dm_filter,dtype=arrs["dm_2"].dtype))
    pt_mask = True if var_key=="pt_2" else (arrs["pt_2"]>=pt_cut)
    if mode in ("L1","L1HLT"):
        den_mask = base_mask & (pt_mask if isinstance(pt_mask,np.ndarray) else True) & (dm_mask if isinstance(dm_mask,np.ndarray) else True)
    else:
        den_mask = base_mask & l1_bits & (pt_mask if isinstance(pt_mask,np.ndarray) else True) & (dm_mask if isinstance(dm_mask,np.ndarray) else True)
    num_mask = den_mask & l1_bits if mode=="L1" else den_mask & l1_bits & hlt_bit & match
    den_counts = binned_sum(var_vals, den_mask, weights, bins_edges)
    num_counts = binned_sum(var_vals, num_mask, weights, bins_edges)
    return make_eff_hist_from_counts(num_counts, den_counts, f"eff_{algo}_{trig_key}_{mode}", bins_edges)

def build_mask_and_weights(arrs):
    q1,q2 = arrs["q_1"],arrs["q_2"]
    base = (
        arrs["pass_probe"].astype(bool) &
        arrs["HLT_IsoMu24"].astype(bool) &
        arrs["Flag_METFilters"].astype(bool) &
        (np.abs(arrs["eta_2"]) < 2.3) &
        arrs["trig_match_single_muon"].astype(bool)
    )
    weights = np.where(q1 != q2, 1.0, -1.0)
    return base, weights

base_mask_tot, weights_tot = (build_mask_and_weights(arrs_total) if arrs_total else (None,None))
base_masks_eras = {e: build_mask_and_weights(a) for e,a in arrs_eras.items()}

for trig in TRIGGERS:
    for mode in MODES:
        trig_dir = os.path.join(output_dir, trig, mode)
        os.makedirs(trig_dir, exist_ok=True)
        
        pt_cut = PT_CUTS[trig]
        trig_disp = TRIG_DISPLAY[trig]

        for dm_filter in DM_FILTERS:
            dm_tag = "inc" if dm_filter is None else "+".join(map(str,dm_filter))

            for var_key,(branch,bins,x_title,x_range) in VAR_CFG.items():
                eff_eras = {}

                for era,arrs in arrs_eras.items():
                    base_mask,weights = base_masks_eras[era]
                    eff_eras[era] = eff_for_algo_var(
                        arrs, base_mask, weights,
                        trig, dm_filter, "L1", "l1",
                        var_key, arrs[branch], bins, pt_cut
                    )

                eff_ref = None
                ref_label = None

                if ratio_ref == "total" and arrs_total:
                    eff_ref = eff_for_algo_var(
                        arrs_total, base_mask_tot, weights_tot,
                        trig, dm_filter, "L1", "l1",
                        var_key, arrs_total[branch], bins, pt_cut
                    )
                    ref_label = "total"
                elif ratio_ref in eff_eras:
                    eff_ref = eff_eras[ratio_ref]
                    ref_label = f"era {ratio_ref}"

                ratios = {}
                if eff_ref:
                    for era,h in eff_eras.items():
                        if era == ratio_ref:
                            continue
                        safe_ref = ref_label.replace(" ", "_")
                        ratios[era] = make_ratio_hist(
                            h, eff_ref, f"ratio_{era}_over_{safe_ref}"
                        )

                save_base = os.path.join(trig_dir, f"{trig}_{var_key}_dm_{dm_tag}")
                plot_total_vs_eras(
                    eff_ref, eff_eras, ratios,
                    x_range, x_title, "L1 Efficiency",
                    trig_disp, "L1", dm_tag,
                    save_base, year, ref_label,
                    pt_cut, var_key!="pt_2"
                )

print("Done. Outputs in:", output_dir)