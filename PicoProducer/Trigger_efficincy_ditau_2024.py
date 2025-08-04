import ROOT
import uproot
import os
from array import array
from math import sqrt
from tqdm import tqdm
import getpass

ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
user = getpass.getuser()

file_path = f"/eos/user/{user[0]}/{user}/analysis/2024/Data/Muon_Run2024_mutau.root"
output_dir = f"/eos/user/{user[0]}/{user}/analysis/2024/Data/eff_plots"
os.makedirs(output_dir, exist_ok=True)

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

def plot_efficiency(hist, label, save_path):
    canvas = ROOT.TCanvas("canvas", "Canvas", 800, 600)
    hist.SetMinimum(0)
    hist.SetMaximum(1.1)
    hist.SetLineColor(ROOT.kBlue+1)
    hist.SetLineWidth(2)
    hist.SetMarkerStyle(20)
    hist.SetMarkerColor(ROOT.kBlue+1)
    hist.SetMarkerSize(1.0)
    hist.GetXaxis().SetTitle("Offline p_{T}^{#tau} [GeV]")
    hist.GetYaxis().SetTitle("Efficiency")
    hist.GetYaxis().SetTitleOffset(1.2)
    hist.SetTitle(f"PNet DiTau Trigger Efficiency ({label})")
    hist.Draw("EP")
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.04)
    latex.DrawLatex(0.15, 0.92, f"Run {label}")
    canvas.SaveAs(save_path)
    canvas.Close()

def compute_ditau_efficiency():
    with uproot.open(file_path) as f:
        tree = f["tree"]
        pt_2 = tree["pt_2"].array()
        eta_2 = tree["eta_2"].array()
        q1 = tree["q_1"].array()
        q2 = tree["q_2"].array()
        pass_probe = tree["pass_probe"].array()
        hlt_ditau = tree["HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1"].array()
        match_ditau = tree["trig_match_PNet_DiTau_Loose"].array()
        trig_match_single_muon = tree["trig_match_single_muon"].array()
        met_filter = tree["Flag_METFilters"].array()

    h_total = ROOT.TH1F("htotal_ditau", "", len(pt_bins)-1, pt_bin_array)
    h_num = ROOT.TH1F("hnum_ditau", "", len(pt_bins)-1, pt_bin_array)

    for i in tqdm(range(len(pt_2)), desc="Processing DiTau", unit="evt"):
        if pass_probe[i] and hlt_ditau[i] and met_filter[i] and abs(eta_2[i]) < 2.3 and trig_match_single_muon[i]:
            w = ss_weight(q1[i], q2[i])
            h_total.Fill(pt_2[i], w)
            if match_ditau[i]:
                h_num.Fill(pt_2[i], w)

    eff_hist = make_efficiency_hist(h_num, h_total, "eff_ditau_2024")
    return eff_hist

if __name__ == "__main__":
    eff_ditau = compute_ditau_efficiency()
    plot_efficiency(
        eff_ditau,
        label="2024",
        save_path=os.path.join(output_dir, "eff_ditau_2024.png")
    )
    output_file = ROOT.TFile(os.path.join(output_dir, "eff_ditau_2024.root"), "RECREATE")
    eff_ditau.SetName("eff_ditau_2024")
    eff_ditau.Write()
    output_file.Close()
