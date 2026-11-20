#! /usr/bin/env python3
# Description: Plot Phase-II HLT trigger efficiencies from unified skim output.
#   Reads the flat tree produced by ModulePhase2TrigEff and applies
#   channel-specific selections at plot time.
#
# Usage:
#   python3 plot_phase2_trigeff.py --input pico.root --channel mutau  --outdir plots/
#   python3 plot_phase2_trigeff.py --input pico.root --channel ditau  --outdir plots/
#   python3 plot_phase2_trigeff.py --input pico.root --channel etau   --outdir plots/
#   python3 plot_phase2_trigeff.py --input pico.root --channel singletau --outdir plots/
#
import os, sys, argparse
import numpy as np
import ROOT

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from TauFW.PicoProducer.analysis.PhaseII.Phase2TriggerConfig import (
    CHANNELS, L1_SEEDS, HLT_PATHS, PT_BINS, ETA_BINS, PHI_BINS
)


# ── Helpers ──────────────────────────────────────────────────────────────

def eff_err(num, den):
  """Binomial efficiency and uncertainty."""
  if den == 0: return 0., 0.
  e = num / den
  return e, np.sqrt(e * (1 - e) / den)


def plot_eff(var_den, var_num, bins, xlabel, title, outdir, fname, ylabel="Efficiency", pdf=None):
  """Two-panel plot: distributions (top) + efficiency (bottom).
  If a PdfPages object `pdf` is provided, the figure is also added to it as a page."""
  h_den, edges = np.histogram(var_den, bins=bins)
  h_num, _     = np.histogram(var_num, bins=bins)
  centers = 0.5 * (edges[:-1] + edges[1:])
  xerr    = np.diff(edges) / 2

  eff = np.divide(h_num, h_den, out=np.zeros_like(h_num, dtype=float), where=h_den > 0)
  err = np.zeros_like(eff)
  m   = h_den > 0
  err[m] = np.sqrt(eff[m] * (1 - eff[m]) / h_den[m])

  fig, (ax_dist, ax_eff) = plt.subplots(2, 1, figsize=(8, 7),
                                          gridspec_kw={"height_ratios": [1, 1.5]},
                                          sharex=True)
  # Top: distributions
  ax_dist.errorbar(centers, h_den, xerr=xerr, yerr=np.sqrt(np.maximum(h_den, 0)),
                   fmt='s', color='#e74c3c', capsize=3, markersize=4, linewidth=1.2,
                   label='Denominator')
  ax_dist.errorbar(centers, h_num, xerr=xerr, yerr=np.sqrt(np.maximum(h_num, 0)),
                   fmt='o', color='#2980b9', capsize=3, markersize=4, linewidth=1.2,
                   label='Numerator')
  ax_dist.set_ylabel("Events", fontsize=13)
  ax_dist.legend(fontsize=10, loc='upper right')
  ax_dist.grid(True, alpha=0.3)
  ax_dist.set_title(title, fontsize=13, pad=8)

  # Bottom: efficiency
  ax_eff.errorbar(centers, eff, xerr=xerr, yerr=err, fmt='o', color='black',
                  capsize=3, markersize=5, linewidth=1.5)
  ax_eff.set_ylim(-0.05, 1.15)
  ax_eff.set_xlabel(xlabel, fontsize=13)
  ax_eff.set_ylabel(ylabel, fontsize=13)
  ax_eff.axhline(y=1.0, color='gray', ls='--', alpha=0.4)
  ax_eff.grid(True, alpha=0.3)

  plt.tight_layout()
  outpath = os.path.join(outdir, fname)
  fig.savefig(outpath, dpi=150, bbox_inches="tight")
  print(f"  Saved {outpath}")

  if pdf is not None:
    pdf.savefig(fig, bbox_inches="tight")
  plt.close(fig)


# ── Tree → numpy helper ─────────────────────────────────────────────────

def tree_to_arrays(tree, branches):
  """Read flat branches from ROOT tree into numpy arrays."""
  n = tree.GetEntries()
  arrays = {b: np.zeros(n) for b in branches}
  for i in range(n):
    tree.GetEntry(i)
    for b in branches:
      arrays[b][i] = getattr(tree, b)
  return arrays, n


# ── Unified Channel Logic ───────────────────────────────────────────────

def get_channel_info(channel):
  if channel == 'mutau':
    return {
      'l1': 'tau1', 'l2': 'mu1', 'l1_cfg': 'tau', 'l2_cfg': 'mu',
      'l1_name': r"$\tau_h$", 'l2_name': "Muon",
      'l1_file': 'tau', 'l2_file': 'mu',
      'title': "MuTau",
      'pair_label': r"$\mu + \tau_h$",
      'l1_gen_coll': "GenVisTau", 'l2_gen_coll': "GenPart",
      'l1_reco_coll': "hltHpsPFTau", 'l2_reco_coll': "hltMuon",
    }
  elif channel == 'etau':
    return {
      'l1': 'tau1', 'l2': 'ele1', 'l1_cfg': 'tau', 'l2_cfg': 'ele',
      'l1_name': r"$\tau_h$", 'l2_name': "Electron",
      'l1_file': 'tau', 'l2_file': 'ele',
      'title': "ETau",
      'pair_label': r"$e + \tau_h$",
      'l1_gen_coll': "GenVisTau", 'l2_gen_coll': "GenPart",
      'l1_reco_coll': "hltHpsPFTau", 'l2_reco_coll': "hltElectron",
    }
  elif channel == 'ditau':
    return {
      'l1': 'tau1', 'l2': 'tau2', 'l1_cfg': 'tau', 'l2_cfg': 'tau',
      'l1_name': r"Lead $\tau_h$", 'l2_name': r"Sub $\tau_h$",
      'l1_file': 'lead', 'l2_file': 'sub',
      'title': "DiTau",
      'pair_label': r"$\tau_h + \tau_h$",
      'l1_gen_coll': "GenVisTau", 'l2_gen_coll': "GenVisTau",
      'l1_reco_coll': "hltHpsPFTau", 'l2_reco_coll': "hltHpsPFTau",
    }
  else:
    raise ValueError(f"Unknown channel info: {channel}")


def apply_selection(a, cfg, info, has_reco_l2=True):
  """Apply channel gen+reco selection, return masks."""
  eta_cut = cfg.get('gen_tau_eta', 2.1)  # Read from config (currently 2.1 for all)
  dR_sep  = cfg['dr_separation']
  dR_match = cfg['dr_match']

  l1 = info['l1']
  l2 = info['l2']
  c1 = info['l1_cfg']
  c2 = info['l2_cfg']

  pt1_cut = cfg[f'gen_{c1}_pt']
  pt2_cut = cfg[f'gen_{c2}_pt']

  # Gen: 2 objects, eta, dR
  dr_gen_var = f"dr_gen_{l1}_{l2}"
  gen_base = (a[f'gen_{l1}_pt'] > 0) & (np.abs(a[f'gen_{l1}_eta']) < eta_cut) & \
             (a[f'gen_{l2}_pt'] > 0) & (np.abs(a[f'gen_{l2}_eta']) < eta_cut) & \
             (a[dr_gen_var] > dR_sep)

  gen_sel = gen_base & (a[f'gen_{l1}_pt'] > pt1_cut) & (a[f'gen_{l2}_pt'] > pt2_cut)

  # For turn-on curves, drop one pT cut
  gen_sel_no_l1pt = gen_base & (a[f'gen_{l2}_pt'] > pt2_cut)
  gen_sel_no_l2pt = gen_base & (a[f'gen_{l1}_pt'] > pt1_cut)

  # Reco: tau (and second leg if available)
  reco_pt1_cut = cfg[f'reco_{c1}_pt']
  reco_sel = (a[f'reco_{l1}_pt'] > reco_pt1_cut) & (np.abs(a[f'reco_{l1}_eta']) < eta_cut)
  
  match1 = (a[f'dr_gen{l1}_reco{l1}'] < dR_match) & (a[f'dr_gen{l1}_reco{l1}'] >= 0)

  if has_reco_l2:
    reco_pt2_cut = cfg[f'reco_{c2}_pt']
    reco_sel = reco_sel & (a[f'reco_{l2}_pt'] > reco_pt2_cut) & \
               (np.abs(a[f'reco_{l2}_eta']) < eta_cut) & \
               (a[f'dr_reco_{l1}_{l2}'] > dR_sep)
    match2 = (a[f'dr_gen{l2}_reco{l2}'] < dR_match) & (a[f'dr_gen{l2}_reco{l2}'] >= 0)
    matched = match1 & match2
    # DiTau: also try swapped gen-reco permutation (pT ordering can swap)
    cross_key1 = f'dr_gen{l1}_reco{l2}'
    cross_key2 = f'dr_gen{l2}_reco{l1}'
    if cross_key1 in a and cross_key2 in a:
      match_cross1 = (a[cross_key1] < dR_match) & (a[cross_key1] >= 0)
      match_cross2 = (a[cross_key2] < dR_match) & (a[cross_key2] >= 0)
      matched = matched | (match_cross1 & match_cross2)
  else:
    matched = match1

  return {
    'gen_sel': gen_sel, 'reco_sel': reco_sel, 'matched': matched,
    'gen_sel_no_l1pt': gen_sel_no_l1pt, 'gen_sel_no_l2pt': gen_sel_no_l2pt,
  }


def plot_channel(tree, outdir, sample_label, channel, pdf=None):
  """Unified channel efficiency plotter.
  If a PdfPages object `pdf` is provided, each plot is also added to it as a page."""
  cfg = CHANNELS[channel]
  info = get_channel_info(channel)
  
  l1 = info['l1']
  l2 = info['l2']
  
  branchlist = [b.GetName() for b in tree.GetListOfBranches()]
  has_reco_l2 = f'reco_{l2}_pt' in branchlist

  branches = [
    f'gen_{l1}_pt', f'gen_{l1}_eta', f'gen_{l1}_phi',
    f'gen_{l2}_pt', f'gen_{l2}_eta', f'gen_{l2}_phi',
    f'reco_{l1}_pt', f'reco_{l1}_eta', f'reco_{l1}_phi',
    f'dr_gen_{l1}_{l2}', f'dr_gen{l1}_reco{l1}',
    f'hlt_{channel}', f'l1_{channel}',
  ]
  if has_reco_l2:
    branches.extend([
      f'reco_{l2}_pt', f'reco_{l2}_eta', f'reco_{l2}_phi',
      f'dr_reco_{l1}_{l2}', f'dr_gen{l2}_reco{l2}'
    ])
  # DiTau: load cross-match dR branches for permutation matching
  cross_key1 = f'dr_gen{l1}_reco{l2}'
  cross_key2 = f'dr_gen{l2}_reco{l1}'
  if cross_key1 in branchlist and cross_key2 in branchlist:
    branches.extend([cross_key1, cross_key2])

  a, n = tree_to_arrays(tree, branches)
  sel = apply_selection(a, cfg, info, has_reco_l2=has_reco_l2)

  hlt_var = f'hlt_{channel}'
  l1_var = f'l1_{channel}'

  eff_den = sel['gen_sel'] & sel['reco_sel']
  eff_num = eff_den & a[hlt_var].astype(bool) & sel['matched']

  n_den, n_num = np.sum(eff_den), np.sum(eff_num)
  e, e_err = eff_err(n_num, n_den)

  print(f"\n{'='*60}")
  print(f"{info['title']} Trigger Efficiency — {sample_label}")
  print(f"{'='*60}")
  print(f"  Total events:     {n}")
  print(f"  Gen selection:    {np.sum(sel['gen_sel'])}")
  print(f"  Eff denominator:  {n_den}")
  l1_pass = np.sum(eff_den & a[l1_var].astype(bool))
  hlt_pass = np.sum(eff_den & a[hlt_var].astype(bool))
  print(f"  L1 {info['title']}:        {l1_pass} ({eff_err(l1_pass, n_den)[0]:.4f})")
  print(f"  HLT {info['title']}:       {hlt_pass} ({eff_err(hlt_pass, n_den)[0]:.4f})")
  print(f"  HLT + Match:      {n_num} ({e:.4f} ± {e_err:.4f})")

  pair_lbl = info['pair_label']

  # ══ HLT Efficiency: pT turn-on curves ═══════════════════════════════════
  # l1 pT (no gen l1 pT cut)
  den_l1pt = sel['gen_sel_no_l1pt'] & sel['reco_sel']
  num_l1pt = den_l1pt & a[hlt_var].astype(bool) & sel['matched']
  l2_pt_cut = int(cfg[f'gen_{info["l2_cfg"]}_pt'])
  plot_eff(a[f'gen_{l1}_pt'][den_l1pt], a[f'gen_{l1}_pt'][num_l1pt], PT_BINS,
           f"{info['l1_name']} $p_T$ [GeV] ({info['l1_gen_coll']})",
           f"{info['title']} HLT Eff. vs {info['l1_name']} $p_T$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair | {info['l2_name']} $p_T>{l2_pt_cut}$ applied, NO {info['l1_name']} $p_T$ cut",
           outdir, f"eff_{channel}_vs_{info['l1_file']}_pt.png", pdf=pdf)

  # l2 pT (no l2 pT cut)
  den_l2pt = sel['gen_sel_no_l2pt'] & sel['reco_sel']
  num_l2pt = den_l2pt & a[hlt_var].astype(bool) & sel['matched']
  l1_pt_cut = int(cfg[f'gen_{info["l1_cfg"]}_pt'])
  plot_eff(a[f'gen_{l2}_pt'][den_l2pt], a[f'gen_{l2}_pt'][num_l2pt], PT_BINS,
           f"{info['l2_name']} $p_T$ [GeV] ({info['l2_gen_coll']})",
           f"{info['title']} HLT Eff. vs {info['l2_name']} $p_T$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair | {info['l1_name']} $p_T>{l1_pt_cut}$ applied, NO {info['l2_name']} $p_T$ cut",
           outdir, f"eff_{channel}_vs_{info['l2_file']}_pt.png", pdf=pdf)

  # HLT η distributions
  plot_eff(a[f'gen_{l1}_eta'][eff_den], a[f'gen_{l1}_eta'][eff_num], ETA_BINS,
           f"{info['l1_name']} $\\eta$ ({info['l1_gen_coll']})",
           f"{info['title']} HLT Eff. vs {info['l1_name']} $\\eta$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair",
           outdir, f"eff_{channel}_vs_{info['l1_file']}_eta.png", pdf=pdf)
  plot_eff(a[f'gen_{l2}_eta'][eff_den], a[f'gen_{l2}_eta'][eff_num], ETA_BINS,
           f"{info['l2_name']} $\\eta$ ({info['l2_gen_coll']})",
           f"{info['title']} HLT Eff. vs {info['l2_name']} $\\eta$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair",
           outdir, f"eff_{channel}_vs_{info['l2_file']}_eta.png", pdf=pdf)

  # HLT φ distributions
  plot_eff(a[f'gen_{l1}_phi'][eff_den], a[f'gen_{l1}_phi'][eff_num], PHI_BINS,
           f"{info['l1_name']} $\\phi$ ({info['l1_gen_coll']})",
           f"{info['title']} HLT Eff. vs {info['l1_name']} $\\phi$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair",
           outdir, f"eff_{channel}_vs_{info['l1_file']}_phi.png", pdf=pdf)
  plot_eff(a[f'gen_{l2}_phi'][eff_den], a[f'gen_{l2}_phi'][eff_num], PHI_BINS,
           f"{info['l2_name']} $\\phi$ ({info['l2_gen_coll']})",
           f"{info['title']} HLT Eff. vs {info['l2_name']} $\\phi$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair",
           outdir, f"eff_{channel}_vs_{info['l2_file']}_phi.png", pdf=pdf)

  # ══ L1 Efficiency Plots ═════════════════════════════════════════════
  l1_eff_num = eff_den & a[l1_var].astype(bool) & sel['matched']

  # L1 turn-on: l1 pT
  l1_den_l1pt = sel['gen_sel_no_l1pt'] & sel['reco_sel']
  l1_num_l1pt = l1_den_l1pt & a[l1_var].astype(bool) & sel['matched']
  plot_eff(a[f'gen_{l1}_pt'][l1_den_l1pt], a[f'gen_{l1}_pt'][l1_num_l1pt], PT_BINS,
           f"{info['l1_name']} $p_T$ [GeV] ({info['l1_gen_coll']})",
           f"{info['title']} L1 Eff. vs {info['l1_name']} $p_T$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair | NO {info['l1_name']} $p_T$ cut",
           outdir, f"eff_l1{channel}_vs_{info['l1_file']}_pt.png", pdf=pdf)

  # L1 turn-on: l2 pT
  l1_den_l2pt = sel['gen_sel_no_l2pt'] & sel['reco_sel']
  l1_num_l2pt = l1_den_l2pt & a[l1_var].astype(bool) & sel['matched']
  plot_eff(a[f'gen_{l2}_pt'][l1_den_l2pt], a[f'gen_{l2}_pt'][l1_num_l2pt], PT_BINS,
           f"{info['l2_name']} $p_T$ [GeV] ({info['l2_gen_coll']})",
           f"{info['title']} L1 Eff. vs {info['l2_name']} $p_T$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair | NO {info['l2_name']} $p_T$ cut",
           outdir, f"eff_l1{channel}_vs_{info['l2_file']}_pt.png", pdf=pdf)

  # L1 η
  plot_eff(a[f'gen_{l1}_eta'][eff_den], a[f'gen_{l1}_eta'][l1_eff_num], ETA_BINS,
           f"{info['l1_name']} $\\eta$ ({info['l1_gen_coll']})",
           f"{info['title']} L1 Eff. vs {info['l1_name']} $\\eta$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair",
           outdir, f"eff_l1{channel}_vs_{info['l1_file']}_eta.png", pdf=pdf)
  plot_eff(a[f'gen_{l2}_eta'][eff_den], a[f'gen_{l2}_eta'][l1_eff_num], ETA_BINS,
           f"{info['l2_name']} $\\eta$ ({info['l2_gen_coll']})",
           f"{info['title']} L1 Eff. vs {info['l2_name']} $\\eta$ [{sample_label}]\n"
           f"Requiring {pair_lbl} pair",
           outdir, f"eff_l1{channel}_vs_{info['l2_file']}_eta.png", pdf=pdf)

  # ══ HLT Fake Rate Plots ═════════════════════════════════════════════
  # Fake Rate = (Reco Sel. + Trigger + Fail Gen-Reco Match) / Reco Sel.
  # Denominator: reco selection only (no gen requirement).
  # If either leg fails gen-reco matching (dR >= 0.1), event is counted as fake.
  fake_den = sel['reco_sel']
  fake_num_hlt = fake_den & a[hlt_var].astype(bool) & ~sel['matched']

  n_fake_den = np.sum(fake_den)
  n_fake_num_hlt = np.sum(fake_num_hlt)
  f_rate_hlt, f_err_hlt = eff_err(n_fake_num_hlt, n_fake_den)
  print(f"\n  HLT Fake rate:    {n_fake_num_hlt}/{n_fake_den} = {f_rate_hlt:.4f} ± {f_err_hlt:.4f}")

  # HLT Fake rate vs reco pT
  plot_eff(a[f'reco_{l1}_pt'][fake_den], a[f'reco_{l1}_pt'][fake_num_hlt], PT_BINS,
           f"Reco {info['l1_name']} $p_T$ [GeV] ({info['l1_reco_coll']})",
           f"{info['title']} HLT Fake Rate vs {info['l1_name']} $p_T$ [{sample_label}]\n"
           f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
           outdir, f"fake_{channel}_vs_{info['l1_file']}_pt.png", ylabel="Fake Rate", pdf=pdf)
  if has_reco_l2:
    plot_eff(a[f'reco_{l2}_pt'][fake_den], a[f'reco_{l2}_pt'][fake_num_hlt], PT_BINS,
             f"Reco {info['l2_name']} $p_T$ [GeV] ({info['l2_reco_coll']})",
             f"{info['title']} HLT Fake Rate vs {info['l2_name']} $p_T$ [{sample_label}]\n"
             f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
             outdir, f"fake_{channel}_vs_{info['l2_file']}_pt.png", ylabel="Fake Rate", pdf=pdf)

  # HLT Fake rate vs reco η
  plot_eff(a[f'reco_{l1}_eta'][fake_den], a[f'reco_{l1}_eta'][fake_num_hlt], ETA_BINS,
           f"Reco {info['l1_name']} $\\eta$ ({info['l1_reco_coll']})",
           f"{info['title']} HLT Fake Rate vs {info['l1_name']} $\\eta$ [{sample_label}]\n"
           f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
           outdir, f"fake_{channel}_vs_{info['l1_file']}_eta.png", ylabel="Fake Rate", pdf=pdf)
  if has_reco_l2:
    plot_eff(a[f'reco_{l2}_eta'][fake_den], a[f'reco_{l2}_eta'][fake_num_hlt], ETA_BINS,
             f"Reco {info['l2_name']} $\\eta$ ({info['l2_reco_coll']})",
             f"{info['title']} HLT Fake Rate vs {info['l2_name']} $\\eta$ [{sample_label}]\n"
             f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
             outdir, f"fake_{channel}_vs_{info['l2_file']}_eta.png", ylabel="Fake Rate", pdf=pdf)

  # HLT Fake rate vs reco φ
  plot_eff(a[f'reco_{l1}_phi'][fake_den], a[f'reco_{l1}_phi'][fake_num_hlt], PHI_BINS,
           f"Reco {info['l1_name']} $\\phi$ ({info['l1_reco_coll']})",
           f"{info['title']} HLT Fake Rate vs {info['l1_name']} $\\phi$ [{sample_label}]\n"
           f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
           outdir, f"fake_{channel}_vs_{info['l1_file']}_phi.png", ylabel="Fake Rate", pdf=pdf)
  if has_reco_l2:
    plot_eff(a[f'reco_{l2}_phi'][fake_den], a[f'reco_{l2}_phi'][fake_num_hlt], PHI_BINS,
             f"Reco {info['l2_name']} $\\phi$ ({info['l2_reco_coll']})",
             f"{info['title']} HLT Fake Rate vs {info['l2_name']} $\\phi$ [{sample_label}]\n"
             f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
             outdir, f"fake_{channel}_vs_{info['l2_file']}_phi.png", ylabel="Fake Rate", pdf=pdf)

  # ══ L1 Fake Rate Plots ══════════════════════════════════════════════
  fake_num_l1 = fake_den & a[l1_var].astype(bool) & ~sel['matched']

  n_fake_num_l1 = np.sum(fake_num_l1)
  f_rate_l1, f_err_l1 = eff_err(n_fake_num_l1, n_fake_den)
  print(f"  L1  Fake rate:    {n_fake_num_l1}/{n_fake_den} = {f_rate_l1:.4f} ± {f_err_l1:.4f}")

  # L1 Fake rate vs reco pT
  plot_eff(a[f'reco_{l1}_pt'][fake_den], a[f'reco_{l1}_pt'][fake_num_l1], PT_BINS,
           f"Reco {info['l1_name']} $p_T$ [GeV] ({info['l1_reco_coll']})",
           f"{info['title']} L1 Fake Rate vs {info['l1_name']} $p_T$ [{sample_label}]\n"
           f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
           outdir, f"fake_l1{channel}_vs_{info['l1_file']}_pt.png", ylabel="Fake Rate", pdf=pdf)
  if has_reco_l2:
    plot_eff(a[f'reco_{l2}_pt'][fake_den], a[f'reco_{l2}_pt'][fake_num_l1], PT_BINS,
             f"Reco {info['l2_name']} $p_T$ [GeV] ({info['l2_reco_coll']})",
             f"{info['title']} L1 Fake Rate vs {info['l2_name']} $p_T$ [{sample_label}]\n"
             f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
             outdir, f"fake_l1{channel}_vs_{info['l2_file']}_pt.png", ylabel="Fake Rate", pdf=pdf)

  # L1 Fake rate vs reco η
  plot_eff(a[f'reco_{l1}_eta'][fake_den], a[f'reco_{l1}_eta'][fake_num_l1], ETA_BINS,
           f"Reco {info['l1_name']} $\\eta$ ({info['l1_reco_coll']})",
           f"{info['title']} L1 Fake Rate vs {info['l1_name']} $\\eta$ [{sample_label}]\n"
           f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
           outdir, f"fake_l1{channel}_vs_{info['l1_file']}_eta.png", ylabel="Fake Rate", pdf=pdf)
  if has_reco_l2:
    plot_eff(a[f'reco_{l2}_eta'][fake_den], a[f'reco_{l2}_eta'][fake_num_l1], ETA_BINS,
             f"Reco {info['l2_name']} $\\eta$ ({info['l2_reco_coll']})",
             f"{info['title']} L1 Fake Rate vs {info['l2_name']} $\\eta$ [{sample_label}]\n"
             f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
             outdir, f"fake_l1{channel}_vs_{info['l2_file']}_eta.png", ylabel="Fake Rate", pdf=pdf)

  # L1 Fake rate vs reco φ
  plot_eff(a[f'reco_{l1}_phi'][fake_den], a[f'reco_{l1}_phi'][fake_num_l1], PHI_BINS,
           f"Reco {info['l1_name']} $\\phi$ ({info['l1_reco_coll']})",
           f"{info['title']} L1 Fake Rate vs {info['l1_name']} $\\phi$ [{sample_label}]\n"
           f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
           outdir, f"fake_l1{channel}_vs_{info['l1_file']}_phi.png", ylabel="Fake Rate", pdf=pdf)
  if has_reco_l2:
    plot_eff(a[f'reco_{l2}_phi'][fake_den], a[f'reco_{l2}_phi'][fake_num_l1], PHI_BINS,
             f"Reco {info['l2_name']} $\\phi$ ({info['l2_reco_coll']})",
             f"{info['title']} L1 Fake Rate vs {info['l2_name']} $\\phi$ [{sample_label}]\n"
             f"Requiring {pair_lbl} reco pair | Fail gen-reco match on $\\geq$1 leg",
             outdir, f"fake_l1{channel}_vs_{info['l2_file']}_phi.png", ylabel="Fake Rate", pdf=pdf)


# ── Main ─────────────────────────────────────────────────────────────────

def main():
  parser = argparse.ArgumentParser(description="Phase-II HLT trigger efficiency plotter")
  parser.add_argument("--input", required=True, help="Input ROOT file from ModulePhase2TrigEff")
  parser.add_argument("--channel", required=True, choices=['mutau', 'ditau', 'etau', 'singletau'],
                      help="Channel to plot")
  parser.add_argument("--outdir", default="plots_phase2")
  parser.add_argument("--sample-label", default="ZprimeToTauTau M500 (Phase-II)")
  parser.add_argument("--no-pdf", action="store_true",
                      help="Skip generating the combined PDF")
  args = parser.parse_args()

  os.makedirs(args.outdir, exist_ok=True)

  f = ROOT.TFile.Open(args.input)
  tree = f.Get("tree")
  if not tree:
    print(f"ERROR: Could not find 'tree' in {args.input}")
    print(f"  Available keys: {[k.GetName() for k in f.GetListOfKeys()]}")
    return

  print(f"Channel: {args.channel}")
  print(f"Input:   {args.input}  ({tree.GetEntries()} events)")

  if args.channel in ['mutau', 'ditau', 'etau']:
    if args.no_pdf:
      plot_channel(tree, args.outdir, args.sample_label, args.channel)
    else: # also write all plots for this channel into one combined PDF
      pdf_path = os.path.join(args.outdir, f"trigeff_{args.channel}.pdf")
      with PdfPages(pdf_path) as pdf:
        plot_channel(tree, args.outdir, args.sample_label, args.channel, pdf=pdf)
        npages = pdf.get_pagecount()
      print(f"\n  Combined PDF saved: {pdf_path}  ({npages} pages)")
  else:
    print(f"Plotter for channel '{args.channel}' not yet implemented.")
    print(f"  (SingleTau needs HLT path in menu)")

  f.Close()
  print(f"\nDone! Plots saved to {args.outdir}/")


if __name__ == "__main__":
  main()

