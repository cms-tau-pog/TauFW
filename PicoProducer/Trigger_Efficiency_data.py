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

parser = argparse.ArgumentParser(description="Total vs Era efficiency plotting")
parser.add_argument("--year", type=int, default=2024, help="Year of the dataset (default: 2024)")
parser.add_argument("--era", type=str, required=True, help="Eras to compare, e.g. BCDE")
args = parser.parse_args()
year = args.year
eras = list(args.era.upper())

file_total = f"/eos/user/{user[0]}/{user}/analysis/{year}/Data/Muon_Run{year}_mutau.root"

base_outdir = f"/eos/user/{user[0]}/{user}/analysis/{year}/plots"
output_dir  = os.path.join(base_outdir, f"Data_{year}_{''.join(eras)}")

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
TRIG_DISPLAY = {"mutau":"MuTau","etau":"ETau","ditau":"DiTau","ditaujet":"DiTauJet","vbfsingletau":"VBF SingleTau","vbfditau":"VBF DiTau"}
ALGO_DISPLAY = {"pnet":"ParticleNet","deeptau":"DeepTau","l1":"L1"}

eta_bins = np.linspace(-2.3, 2.3, 12)
phi_bins = np.linspace(-pi, pi, 12)
npv_bins = np.array([0,10,20,30,40,50,60,80],dtype=float)
pt_bins = np.array([20,24,28,32,36,40,50,70,150],dtype=float)

VAR_CFG = {
    "pt_2": ("pt_2", pt_bins, r"Offline #tau_{h} p_{T} [GeV]", (float(pt_bins[0]), float(pt_bins[-1]))),
    "eta_2": ("eta_2", eta_bins, r"Offline #tau_{h} #eta", (-2.3, 2.3)),
    "phi_2": ("phi_2", phi_bins, r"Offline #tau_{h} #phi", (-pi, pi)),
    "PV_npvsGood": ("PV_npvsGood", npv_bins, "Number of Offline Reconstructed Primary Vertices", (0, 80)),
}

colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen+2, ROOT.kMagenta, ROOT.kOrange+7, ROOT.kCyan+2]

def make_ratio_hist(num, den, name):
    hist = num.Clone(name)
    hist.Reset()
    for i in range(1,hist.GetNbinsX()+1):
        n,d = num.GetBinContent(i), den.GetBinContent(i)
        en,ed = num.GetBinError(i), den.GetBinError(i)
        r = n/d if d>0 else 0
        err = sqrt((en/d)**2+(n*ed/d**2)**2) if n>0 and d>0 else 0
        hist.SetBinContent(i,r)
        hist.SetBinError(i,err)
    return hist

def plot_total_vs_eras(eff_total, eff_eras, ratios,
                       x_range, x_title, ytitle,
                       trig_display, algo_display, dm_tag,
                       save_base, year, eras,
                       pt_cut=None, show_pt_cut=False):

    c = ROOT.TCanvas("c","c",850,850)
    pad1 = ROOT.TPad("pad1","pad1",0.0,0.30,1.0,1.0)
    pad2 = ROOT.TPad("pad2","pad2",0.0,0.0,1.0,0.27)
    pad1.SetBottomMargin(0.013)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.35)
    pad1.SetLeftMargin(0.15)
    pad2.SetLeftMargin(0.15)
    pad1.SetRightMargin(0.05)
    pad2.SetRightMargin(0.05)
    pad1.Draw()
    pad2.Draw()

    pad1.cd()
    xmin, xmax = x_range
    frame1 = ROOT.TH1F("frame1","",100,xmin,xmax)
    frame1.SetMinimum(0.0)
    frame1.SetMaximum(1.1)
    frame1.GetYaxis().SetTitle(ytitle)
    frame1.GetXaxis().SetLabelSize(0)
    frame1.Draw()

    eff_total.SetLineColor(ROOT.kBlack)
    eff_total.SetMarkerColor(ROOT.kBlack)
    eff_total.SetMarkerStyle(20)
    eff_total.Draw("EP SAME")

    leg = ROOT.TLegend(0.55,0.02,0.95,0.3)
    leg.AddEntry(eff_total,f"Year {year} total","lp")
    for i,(era,h) in enumerate(eff_eras.items()):
        h.SetLineColor(colors[i%len(colors)])
        h.SetMarkerColor(colors[i%len(colors)])
        h.SetMarkerStyle(24+i)
        h.Draw("EP SAME")
        leg.AddEntry(h,f"Year {year} era {era}","lp")
    if show_pt_cut and pt_cut is not None:
        leg.AddEntry(0,f"Offline #tau p_{{T}} < {pt_cut} GeV","")
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.Draw()

    latex = ROOT.TLatex(); latex.SetNDC()
    latex.SetTextSize(0.05)
    latex.DrawLatex(0.16,0.92,"CMS #it{Preliminary}")
    latex.SetTextSize(0.042)
    latex.DrawLatex(0.16,0.86,f"{trig_display} {algo_display} Trigger (DM {dm_tag})")

    pad2.cd()
    frame2 = ROOT.TH1F("frame2","",100,xmin,xmax)
    frame2.SetMinimum(0.8); frame2.SetMaximum(1.2)
    frame2.GetYaxis().SetTitle("Era / Total")
    frame2.GetYaxis().SetTitleSize(0.10)
    frame2.GetYaxis().SetLabelSize(0.08)
    frame2.GetYaxis().SetTitleOffset(0.5)  
    frame2.GetXaxis().SetTitle(x_title)
    frame2.GetXaxis().SetTitleSize(0.12)
    frame2.GetXaxis().SetLabelSize(0.10)
    frame2.GetYaxis().SetNdivisions(505)
    frame2.Draw()

    for i,(era,r) in enumerate(ratios.items()):
        r.SetLineColor(colors[i%len(colors)])
        r.SetMarkerColor(colors[i%len(colors)])
        r.SetMarkerStyle(24+i)
        r.Draw("EP SAME")

    c.SaveAs(save_base+".png")
    c.SaveAs(save_base+".pdf")

    root_out = save_base + ".root"
    fout = ROOT.TFile(root_out, "RECREATE")
    eff_total.Write("eff_total")
    for era,h in eff_eras.items():
        h.Write(f"eff_{era}")
    for era,r in ratios.items():
        r.Write(f"ratio_{era}_over_total")
    fout.Close()

    c.Close()


ALL_BRANCHES = ["pt_2","eta_2","phi_2","PV_npvsGood","q_1","q_2","dm_2","pass_probe","HLT_IsoMu24","trig_match_single_muon","Flag_METFilters"]
for k,cfg in TRIG_MAP.items():
    ALL_BRANCHES += [cfg["l1"],cfg["pnet_hlt"],cfg["deep_hlt"],cfg["pnet_match"],cfg["deep_match"]]
ALL_BRANCHES = sorted(set(ALL_BRANCHES))

def read_arrays(path):
    with uproot.open(path) as f:
        return f["tree"].arrays(ALL_BRANCHES, library="np")

print("Reading input files...")

for _ in tqdm([file_total], desc="Total", unit="file"):
    arrs_total = read_arrays(file_total)

arrs_eras = {}
for era in tqdm(eras, desc="Eras", unit="era"):
    era_file = f"/eos/user/{user[0]}/{user}/analysis/{year}/Data/era_wise/Muon_Run{year}{era}_mutau.root"
    arrs_eras[era] = read_arrays(era_file)

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
    pass_probe = arrs["pass_probe"].astype(bool)
    hlt_single = arrs.get("HLT_IsoMu24",np.zeros_like(q1)).astype(bool)
    match_mu   = arrs.get("trig_match_single_muon",np.zeros_like(q1)).astype(bool)
    met_filter = arrs.get("Flag_METFilters",np.zeros_like(q1)).astype(bool)
    base_mask  = (pass_probe & hlt_single & met_filter & (np.abs(arrs["eta_2"])<2.3) & match_mu)
    weights    = np.where(q1!=q2,1.0,-1.0)
    return base_mask,weights

base_mask_tot,weights_tot = build_mask_and_weights(arrs_total)
base_masks_eras = {era: build_mask_and_weights(arrs) for era,arrs in arrs_eras.items()}

for trig in tqdm(TRIGGERS, desc="Triggers", unit="trig"):
    trig_dir = os.path.join(output_dir,trig); os.makedirs(trig_dir,exist_ok=True)
    for m in MODES: os.makedirs(os.path.join(trig_dir,m),exist_ok=True)
    pt_cut = PT_CUTS[trig]; trig_disp = TRIG_DISPLAY.get(trig,trig)
    for dm_filter in DM_FILTERS:
        dm_tag = "inc" if dm_filter is None else "+".join(map(str,dm_filter))
        for var_key,(branch,bins_edges,x_title,x_range) in VAR_CFG.items():
            var_tot = arrs_total[branch]
            show_pt_cut = (var_key!="pt_2")
            algo_tag = "l1"
            eff_tot = eff_for_algo_var(arrs_total,base_mask_tot,weights_tot,trig,dm_filter,"L1",algo_tag,var_key,var_tot,bins_edges,pt_cut)
            eff_eras = {}
            ratios = {}
            for era,arrs in arrs_eras.items():
                base_mask,weights = base_masks_eras[era]
                var_era = arrs[branch]
                eff_era = eff_for_algo_var(arrs,base_mask,weights,trig,dm_filter,"L1",algo_tag,var_key,var_era,bins_edges,pt_cut)
                eff_eras[era] = eff_era
                ratios[era] = make_ratio_hist(eff_era,eff_tot,f"era_vs_total_ratio_{trig}_L1_{dm_tag}_{var_key}_{era}")
            save_base = os.path.join(trig_dir,"L1",f"{trig}_{var_key}_{algo_tag}_dm_{dm_tag}_L1")
            plot_total_vs_eras(eff_tot,eff_eras,ratios,x_range,x_title,"L1 Efficiency",trig_disp,ALGO_DISPLAY["l1"],dm_tag,save_base,year,eras,pt_cut=pt_cut,show_pt_cut=show_pt_cut)
            for mode in ("L1HLT","HLT"):
                for algo in ALGOS:
                    eff_tot = eff_for_algo_var(arrs_total,base_mask_tot,weights_tot,trig,dm_filter,mode,algo,var_key,var_tot,bins_edges,pt_cut)
                    eff_eras = {}
                    ratios = {}
                    for era,arrs in arrs_eras.items():
                        base_mask,weights = base_masks_eras[era]
                        var_era = arrs[branch]
                        eff_era = eff_for_algo_var(arrs,base_mask,weights,trig,dm_filter,mode,algo,var_key,var_era,bins_edges,pt_cut)
                        eff_eras[era] = eff_era
                        ratios[era] = make_ratio_hist(eff_era,eff_tot,f"era_vs_total_ratio_{trig}_{mode}_{dm_tag}_{var_key}_{era}")
                    ytitle = "L1+HLT Efficiency" if mode=="L1HLT" else "HLT Efficiency (factorized)"
                    save_base = os.path.join(trig_dir,mode,f"{trig}_{var_key}_{algo}_dm_{dm_tag}_{mode}")
                    plot_total_vs_eras(eff_tot,eff_eras,ratios,x_range,x_title,ytitle,trig_disp,ALGO_DISPLAY[algo],dm_tag,save_base,year,eras,pt_cut=pt_cut,show_pt_cut=show_pt_cut)

print("Done. Outputs in:", output_dir)
