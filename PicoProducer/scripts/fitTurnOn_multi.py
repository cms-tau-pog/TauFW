import argparse
import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import scipy
import copy
from scipy import interpolate

import mplhep as hep

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()

path_prefix = '' if 'TAU-Trigger-NANO' in os.getcwd() else 'TAU-Trigger-NANO/'
sys.path.insert(0, path_prefix + 'Common/python')
from RootObjects import Histogram, Graph

parser = argparse.ArgumentParser(description='Fit turn-on curves.')
parser.add_argument('--input', required=True, type=str, help="ROOT file with turn-on curves")
parser.add_argument('--output', required=True, type=str, help="output file prefix")
parser.add_argument('--channels', required=False, type=str, default='etau,mutau,ditau,ditaujet', help="channels to process")
parser.add_argument('--decay-modes', required=False, type=str, default='all,0,1,10,11,1011', help="decay modes to process")
parser.add_argument('--working-points', required=False, type=str,
                    default='VVVLoose,VVLoose,VLoose,Loose,Medium,Tight,VTight,VVTight',
                    help="working points to process")
args = parser.parse_args()

path_dict = {
    "mutau": r"$\mathrm{\mu\tau_{h}}$",
    "PNet_MuTau_Loose": r"$\mathrm{\mu\tau_{h}}$",
    "DeepTau_ETau": r"$\mathrm{e\tau_{h}}$",
    "ditau": r"$\mathrm{Di-\tau_{h}}$",
    "PNet_DiTau_Medium": r"$\mathrm{Di-\tau_{h}}$",
    "ditaujet": r"$\mathrm{Di-\tau_{h} + jet}$",
    "PNet_DiTauJet": r"$\mathrm{Di-\tau_{h} + jet}$",
    "PNet_DiTauJet_L1Iso23": r"$\mathrm{Di-\tau_{h} + jet}$",
    "PNet_DiTauJet_L1Iso34": r"$\mathrm{Di-\tau_{h} + jet}$",
    "vbftau": r"$\mathrm{VBF + \tau_{h}}$",
    "vbfditau": r"$\mathrm{VBF + Di-\tau_{h}}$",
    "mutau_l1": r"$\mathrm{\mu\tau_{h}}$ (L1 only)",
    "etau_l1": r"$\mathrm{e\tau_{h}}$ (L1 only)",
    "ditau_l1": r"$\mathrm{Di-\tau_{h}}$ (L1 only)",
    "ditaujet_l1": r"$\mathrm{Di-\tau_{h} + jet}$ (L1 only)",
    "vbftau_l1": r"$\mathrm{VBF + \tau_{h}}$ (L1 only)",
    "vbfditau_l1": r"$\mathrm{VBF + Di-\tau_{h}}$ (L1 only)",
}

def MinTarget(dy, eff):
    y = np.cumsum(dy)
    return np.sum(((eff.y - y) / (eff.y_error_high + eff.y_error_low)) ** 2)

class FitResults:
    def __init__(self, eff, x_pred):
        kernel_high = ConstantKernel()
        kernel_low = ConstantKernel() * Matern(nu=1, length_scale_bounds=(10, 100), length_scale=20)
        N = eff.x.shape[0]
        res = scipy.optimize.minimize(MinTarget, np.zeros(N), args=(eff,), bounds = [ [0, 1] ] * N,
                                      options={"maxfun": int(1e6)})
        if not res.success:
            print(res)
            raise RuntimeError("Unable to prefit")

        eff = copy.deepcopy(eff)
        new_y = np.cumsum(res.x)
        delta = eff.y - new_y
        eff.y_error_low = np.sqrt(eff.y_error_low ** 2 + delta ** 2)
        eff.y_error_high = np.sqrt(eff.y_error_high ** 2 + delta ** 2)
        eff.y = new_y
        yerr = np.maximum(eff.y_error_low, eff.y_error_high)

        self.pt_start_flat = eff.x[-1]
        best_chi2_ndof = math.inf
        for n in range(1, N):
            flat_eff, residuals, _, _, _ = np.polyfit(eff.x[N-n-1:], eff.y[N-n-1:], 0, w=1/yerr[N-n-1:], full=True)
            chi2_ndof = residuals[0] / n
            #print(n, chi2_ndof)
            if (chi2_ndof > 0 and chi2_ndof < best_chi2_ndof) or eff.x[N-n-1] + eff.x_error_high[N-n-1] >= 100:
                self.pt_start_flat = eff.x[N-n-1]
                best_chi2_ndof = chi2_ndof
        if best_chi2_ndof > 20:
            print("Unable to determine the high pt region")
            self.pt_start_flat = eff.x[-1]

        low_pt = eff.x <= self.pt_start_flat
        high_pt = eff.x >= self.pt_start_flat

        self.gp_high = GaussianProcessRegressor(kernel=kernel_high, alpha=yerr[high_pt] ** 2, n_restarts_optimizer=10)
        self.gp_high.fit(np.atleast_2d(eff.x[high_pt]).T, eff.y[high_pt])
        self.gp_low = GaussianProcessRegressor(kernel=kernel_low, alpha=np.append([0], yerr[low_pt] ** 2),
                                               n_restarts_optimizer=10)
        self.gp_low.fit(np.atleast_2d(np.append([10], eff.x[low_pt])).T, np.append([0], eff.y[low_pt]))

        self.y_pred, sigma_pred = self.Predict(x_pred)

        sigma_orig = np.zeros(N)
        for n in range(N):
            idx = np.argmin(abs(x_pred - eff.x[n]))
            sigma_orig[n] = sigma_pred[idx]

        interp_kind = 'linear'
        sp = interpolate.interp1d(eff.x, sigma_orig, kind=interp_kind, fill_value="extrapolate")
        sigma_interp = sp(x_pred)
        max_unc = 0.05 / math.sqrt(2)
        sigma_pred, = self.ApplyStep(x_pred, [ [ sigma_pred, sigma_interp ] ], eff.x[0], eff.x[-1] )
        outer_trend = np.minimum(np.ones(x_pred.shape[0]), (x_pred - eff.x[-1]) / eff.x[-1])
        outer_sigma = np.maximum(sigma_pred, sigma_pred + (max_unc - sigma_pred) * outer_trend )
        self.sigma_pred = np.where(x_pred < eff.x[-1], sigma_pred, outer_sigma )

    def Predict(self, x_pred):
        y_pred_high, sigma_high = self.gp_high.predict(np.atleast_2d(x_pred).T, return_std=True)
        y_pred_low, sigma_low = self.gp_low.predict(np.atleast_2d(x_pred).T, return_std=True)
        return self.ApplyStep(x_pred, [ [y_pred_low, y_pred_high], [sigma_low, sigma_high] ], self.pt_start_flat)

    def ApplyStep(self, x_pred, functions, x0, x1 = None):
        step = (np.tanh(0.1*(x_pred - x0)) + 1) / 2
        if x1 is not None:
            step *= (np.tanh(0.1*(x1 - x_pred)) + 1) / 2
        step = np.where(step > 0.999, 1, step)
        step = np.where(step < 0.001, 0, step)
        results = []
        for fn in functions:
            results.append(fn[0] * (1-step) + fn[1] * step)
        return tuple(results)

channels = args.channels.split(',')
decay_modes = args.decay_modes.split(',')
working_points = args.working_points.split(',')
ch_validity_thrs = { 'etau': 35, 'PNet_ETau_Loose': 35, 'PNet_ETau_Medium': 35, 'PNet_ETau_Tight': 35, 'DeepTau_ETau': 35, 'mutau': 32, 'PNet_MuTau_Loose': 32, 'ditau': 40, 'PNet_DiTau_Medium': 35, 'PNet_DiTauJet_L1Iso23': 31, 'PNet_DiTauJet_L1Iso34': 31, 'PNet_DiTauJet': 31, 'PNet_VBFSingleTau': 50, 'PNet_VBFDiTau': 25, 'DeepTau_DiTau': 40, 'DeepTau_DiTauJet': 35, 'DeepTau_MuTau': 32, 'ditaujet': 40, }

file = ROOT.TFile(args.input, 'READ')
output_file = ROOT.TFile('{}.root'.format(args.output), 'RECREATE', '', ROOT.RCompressionSetting.EDefaults.kUseSmallest)

lumi_label = 109.8

if "Run3_combined" in args.input:
    lumi_label = 61.9
if "Run3_2022_combined" in args.input:
    lumi_label = 34.7
elif "22EE" in args.input:
    lumi_label = 26.7
elif "23_combined" in args.input:
    lumi_label = 27.8
elif "23BPix" in args.input:
    lumi_label = 9.7
elif "23" in args.input:
    lumi_label = 18.1
elif "22" in args.input:
    lumi_label = 8.0

for channel in channels:
    with PdfPages('{}_{}.pdf'.format(args.output, channel)) as pdf:
        for wp in working_points:
            for dm in decay_modes:
                print('Processing {} {} WP DM = {}'.format(channel, wp, dm))
                dm_label = '_dm{}'.format(dm) if dm != 'all' else ''
                name_pattern = '{{}}_{}_{}{}_fit_eff'.format(channel, wp, dm_label)
                dm_label = '_dm'+ dm if len(dm) > 0 else ''
                eff_data_root = file.Get(name_pattern.format('data'))
                eff_mc_root = file.Get(name_pattern.format('mc'))
                eff_data = Graph(root_graph=eff_data_root)
                eff_mc = Graph(root_graph=eff_mc_root)
                pred_step = 0.1
                #x_low = min(eff_data.x[0] - eff_data.x_error_low[0], eff_mc.x[0] - eff_mc.x_error_low[0])
                #x_high = max(eff_data.x[-1] + eff_data.x_error_high[-1], eff_mc.x[-1] + eff_mc.x_error_high[-1])
                x_low, x_high = 20, 1000
                x_pred = np.arange(x_low, x_high + pred_step / 2, pred_step)

                eff_data_fitted = FitResults(eff_data, x_pred)
                eff_mc_fitted = FitResults(eff_mc, x_pred)

                sf = eff_data_fitted.y_pred / eff_mc_fitted.y_pred
                sf_sigma = np.sqrt( (eff_data_fitted.sigma_pred / eff_mc_fitted.y_pred) ** 2 \
                         + (eff_data_fitted.y_pred / (eff_mc_fitted.y_pred ** 2) * eff_mc_fitted.sigma_pred ) ** 2 )

                fig, (ax, ax_ratio) = plt.subplots(2, 1, figsize=(7, 7), sharex=True,
                                                           gridspec_kw = {'height_ratios':[2, 1]})
                mc_color = 'firebrick'
                data_color = 'darkorange'
                trans = 0.3
                hep.style.use("CMS")
                hep.cms.label(label="Preliminary", ax=ax, loc=0, fontsize=20, data=True, com=13.6, lumi=lumi_label)

                # test by botao
                # print("mc low previous: {}".format(eff_mc.x_error_low))
                # print("data low previous: {}".format(eff_data.x_error_low))
                # count = 0
                # for _i,_obj in enumerate(eff_data.x_error_low) :
                #     if _obj < 0:
                #         _obj == abs(_obj)
                # for _i,_obj in enumerate(eff_data.x_error_high) :
                #     if _obj < 0:
                #         _obj == - _obj
                # count = 0
                # for _i,_obj in enumerate(eff_mc.x_error_low) :
                #     if _obj < 0:
                #         print("BUGBUGBUGBUG!")
                #         count = 1
                #         _obj == abs(_obj)
                # if count == 1:
                #     continue
                # for _i,_obj in enumerate(eff_mc.x_error_high) :
                #     if _obj < 0:
                #         _obj == - _obj
                # print("mc low: {}".format(eff_mc.x_error_low))
                # print("mc high: {}".format(eff_mc.x_error_high))
                # print("data low: {}".format(eff_data.x_error_low))
                # print("data high: {}".format(eff_data.x_error_high))
                # end test
                plt_data = ax.errorbar(eff_data.x, eff_data.y, xerr=(abs(eff_data.x_error_low), abs(eff_data.x_error_high)),
                                       yerr=(abs(eff_data.y_error_low), abs(eff_data.y_error_high)), color = data_color, fmt='.',
                                       markersize=5)
                print(abs(eff_data.y_error_low), abs(eff_data.y_error_high))
                plt_mc = ax.errorbar(eff_mc.x, eff_mc.y, xerr=(abs(eff_mc.x_error_low), abs(eff_mc.x_error_high)),
                                     yerr=(eff_mc.y_error_low, eff_mc.y_error_high), color = mc_color, fmt = '.', markersize=5)

                plt_data_fitted = ax.plot(x_pred, eff_data_fitted.y_pred, '--', color=data_color)
                ax.fill(np.concatenate([x_pred, x_pred[::-1]]),
                        np.concatenate([eff_data_fitted.y_pred - eff_data_fitted.sigma_pred,
                                       (eff_data_fitted.y_pred + eff_data_fitted.sigma_pred)[::-1]]),
                        alpha=trans, fc=data_color, ec='None')

                plt_mc_fitted = ax.plot(x_pred, eff_mc_fitted.y_pred, '--', color=mc_color)
                ax.fill(np.concatenate([x_pred, x_pred[::-1]]),
                        np.concatenate([eff_mc_fitted.y_pred - eff_mc_fitted.sigma_pred,
                                       (eff_mc_fitted.y_pred + eff_mc_fitted.sigma_pred)[::-1]]),
                        alpha=trans, fc=mc_color, ec='None')

                ax_ratio.plot(x_pred, sf, '--', color='olive')
                ax_ratio.fill(np.concatenate([x_pred, x_pred[::-1]]),
                              np.concatenate([sf - sf_sigma, (sf + sf_sigma)[::-1]]),
                              alpha=trans, fc='olive', ec='None')

                title = "Turn-ons for {} trigger with {} DeepTau VSjet".format(channel, wp)
                # if dm != 'all':
                #     title += " for DM={}".format(dm)
                # else:
                #     title += " for all DMs"
                #ax.set_title(title, fontsize=16)
                if dm != 'all':
                    # extra_text = "{0} trigger\n{1} WP TauID\n DM={2}".format(path_dict[channel], wp, dm)
                    extra_text = "{0} trigger\n{1} WP \nDeepTau ID\n DM={2}".format(path_dict[channel], wp, dm)
                else:
                    # extra_text = "{0} trigger\n{1} WP TauID".format(path_dict[channel], wp)
                    extra_text = "{0} trigger\n{1} WP \nDeepTau ID".format(path_dict[channel], wp)
                ax.text(
                    0.30, 0.20,
                    extra_text,
                    transform=ax.transAxes,  # Use axis-relative coordinates
                    fontsize=18,  # Font size for the text
                    verticalalignment='center',  # Align text vertically
                    horizontalalignment='center',  # Align text horizontally
                    # bbox=dict(boxstyle="round", facecolor="white", alpha=0.5),  # Optional: Add a box
                )
                # if dm != 'all':
                #     title += " for DM={}".format(dm)
                # else:
                #     title += " for all DMs"
                # ax.set_title(title, fontsize=16)
                ax.set_ylabel("L1+HLT Efficiency", fontsize=12)
                ax.set_ylim([ 0., 1.1 ])
                ax.set_xlim([ 20, min(200, plt.xlim()[1]) ])

                ax_ratio.set_xlabel("$p_T$ (GeV)", fontsize=12)
                ax_ratio.set_ylabel("Data/MC SF", fontsize=12)
                ax_ratio.set_ylim([0.5, 1.49])

                ax.get_xaxis().tick_bottom()
                ax.get_yaxis().set_ticks_position('left')
                ax_ratio.get_xaxis().set_ticks_position('bottom')
                ax_ratio.get_yaxis().set_ticks_position('left')
                
                ax.tick_params(axis='both', labelsize=20)  # Change font size for both x and y axes
                ax.grid(True, which="major", linestyle="--", linewidth=0.5, alpha=0.7, color="black")

                ax_ratio.xaxis.set_label_position('bottom')
                ax_ratio.set_ylabel("Data/MC SF", fontsize=20)
                ax_ratio.set_ylim([0.5, 1.49])
                # ax_ratio.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
                ax_ratio.tick_params(axis='both', labelsize=20)  # Change font size for both x and y axes
                ax_ratio.set_yticks([0.6, 0.8, 1.0, 1.2, 1.4])

                ax_ratio.set_xlabel(r"Offline $\mathrm{\tau_h}\,p_T$ [GeV]", fontsize=20, loc='right')

                validity_plt = ax.plot( [ ch_validity_thrs[channel] ] * 2, ax.get_ylim(), 'r--' )
                ax_ratio.plot( [ ch_validity_thrs[channel] ] * 2, ax_ratio.get_ylim(), 'r--' )
                
                ax.legend([ plt_data, plt_mc, plt_data_fitted[0], plt_mc_fitted[0], validity_plt[0] ],
                          [ "Data", "MC", "Data fitted", "MC fitted", "Validity range"], 
                          fontsize=20, loc='lower right', framealpha=0.0)


                plt.subplots_adjust(hspace=0.05)
                pdf.savefig(bbox_inches='tight')
                plt.close()

                out_name_pattern = '{{}}_{}_{}{}_{{}}'.format(channel, wp, dm_label)
                output_file.WriteTObject(eff_data_root, out_name_pattern.format('data', 'eff'), 'Overwrite')
                output_file.WriteTObject(eff_mc_root, out_name_pattern.format('mc', 'eff'), 'Overwrite')
                eff_data_fitted_hist = Histogram.CreateTH1(eff_data_fitted.y_pred, [x_low, x_high],
                                                           eff_data_fitted.sigma_pred, fixed_step=True)
                eff_mc_fitted_hist = Histogram.CreateTH1(eff_mc_fitted.y_pred, [x_low, x_high],
                                                         eff_mc_fitted.sigma_pred, fixed_step=True)
                sf_fitted_hist = eff_data_fitted_hist.Clone()
                sf_fitted_hist.Divide(eff_mc_fitted_hist)
                output_file.WriteTObject(eff_data_fitted_hist, out_name_pattern.format('data', 'fitted'), 'Overwrite')
                output_file.WriteTObject(eff_mc_fitted_hist, out_name_pattern.format('mc', 'fitted'), 'Overwrite')
                output_file.WriteTObject(sf_fitted_hist, out_name_pattern.format('sf', 'fitted'), 'Overwrite')

output_file.Close()
print('All done.')
