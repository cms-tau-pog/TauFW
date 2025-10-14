#!/usr/bin/env python

import argparse
from array import array
import math
import numpy as np
import os
import re
import sys
import ROOT

# --------------
# Example Command:
# python3 createTurnOn_multi.py --input-data sk_data.root --input-dy-mc sk_mc.root --output TurnOn
# --------------

parser = argparse.ArgumentParser(description='Create turn on curves.')
parser.add_argument('--input-data', required=True, type=str, help="skimmed data input")
parser.add_argument('--input-dy-mc', required=True, type=str, help="skimmed DY MC input")
parser.add_argument('--output', required=True, type=str, help="output file prefix")
parser.add_argument('--channels', required=False, type=str, default='etau,mutau,ditau,ditaujet', help="channels to process")
# parser.add_argument('--channels', required=False, type=str, default='ditau,ditau_withptiso_nobitcut,ditau_withptiso_bit1,ditau_withptiso_bit1_bit17,ditau_withptiso_bit1_bit17_0bit18', help="channels to process")
parser.add_argument('--decay-modes', required=False, type=str, default='all,0,1,2,10,11', help="decay modes to process")
parser.add_argument('--working-points', required=False, type=str,
                    default='VVVLoose,VVLoose,VLoose,Loose,Medium,Tight,VTight,VVTight',
                    help="working points to process")
args = parser.parse_args()

sys.path.insert(0, 'Common/python')
from AnalysisTypes import *
from AnalysisTools import *
import RootPlotting
ROOT.ROOT.EnableImplicitMT(4)
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
RootPlotting.ApplyDefaultGlobalStyle()

bin_scans = {
    2:  [ 0.01 ],
    5:  [ 0.01, 0.05 ],
    10: [ 0.05, 0.1 ],
    20: [ 0.1, 0.2 ],
    #50: [ 0.2, 0.4 ],
    100: [ 0.2 ],
}
bin_scan_pairs = []
for max_bin_delta_pt, max_rel_err_vec in bin_scans.items():
    for max_rel_err in max_rel_err_vec:
        bin_scan_pairs.append([max_bin_delta_pt, max_rel_err])

def CreateBins(max_pt, for_fitting):
    if for_fitting:
        step=1
        return np.arange(20, 1000+step, step=step), False
        #high_pt_bins = np.arange(100, 501, step=5)
    else:
        #bins = np.arange(20, 100, step=10)
        bins = np.arange(20, 40, step=4)
        bins = np.append(bins, np.arange(40, 60, step=5))
        bins = np.append(bins, np.arange(60, 100, step=10))
        high_pt_bins = [ 100, 150, 200, 300, 400, 500, 650, 800, 1000 ]
        n = 0
        while n < len(high_pt_bins) and high_pt_bins[n] < max_pt:
            n += 1
        use_logx = max_pt > 200
        return np.append(bins, high_pt_bins[0:n+1]), use_logx

class TurnOnData:
    def __init__(self):
        self.hist_total = None
        self.hist_passed = None
        self.eff = None

def CreateHistograms(input_file, channels, decay_modes, discr_name, working_points, hist_models, label, var,
                     output_file):
    df = ROOT.RDataFrame('Events', input_file)
    turnOn_data = {}
    dm_labels = {}

#    for dm in decay_modes:
#        if dm == 'all':
#            dm_labels[dm] = ''
#            df_dm = df
#        elif dm == '0':
#            dm_labels[dm] = '_dm{}'.format(dm)
#            df_dm = df.Filter('tau_decayModePNet == 0 && tau_ipLengthSig >= 1.25')
#        elif dm == '1':
#            dm_labels[dm] = '_dm{}'.format(dm)
#            df_dm = df.Filter('tau_decayModePNet == 1 && tau_decayMode == 1')
#        elif dm == '2':
#            dm_labels[dm] = '_dm{}'.format(dm)
#            df_dm = df.Filter('tau_decayModePNet == 2 && tau_decayMode == 1')
#        elif dm == '10':
#            dm_labels[dm] = '_dm{}'.format(dm)
#            df_dm = df.Filter('tau_decayModePNet == 10')
#        elif dm == '11':
#            dm_labels[dm] = '_dm{}'.format(dm)
#            df_dm = df.Filter('tau_decayModePNet == 11')
    for dm in decay_modes:
        if dm == 'all':
            dm_labels[dm] = ''
            df_dm = df
        elif dm == '1011':
            dm_labels[dm] = '_dm{}'.format(dm)
            df_dm = df.Filter('tau_decayModePNet == 10 | tau_decayModePNet == 11')

        elif dm == '0':
            dm_labels[dm] = '_dm{}'.format(dm)
            df_dm = df.Filter('tau_decayModePNet == {} && abs(tau_ipLengthSig) >= 1.25'.format(dm))
        elif dm == '1':
            dm_labels[dm] = '_dm{}'.format(dm)
            df_dm = df.Filter('tau_decayModePNet == {} && tau_decayMode == 1'.format(dm))
        elif dm == '2':
            dm_labels[dm] = '_dm{}'.format(dm)
            df_dm = df.Filter('tau_decayModePNet == {} && tau_decayMode == 1'.format(dm))
        elif dm == '10' or dm == '11':
            dm_labels[dm] = '_dm{}'.format(dm)
            df_dm = df.Filter('tau_decayModePNet == {} && tau_hasRefitSV ==1'.format(dm))
        else:
            dm_labels[dm] = '_dm{}'.format(dm)
            df_dm = df.Filter('tau_decayModePNet == {}'.format(dm))
        turnOn_data[dm] = {}
        for wp in working_points:
            wp_bit = ParseEnum(DiscriminatorWP, wp)
            # df_wp = df_dm.Filter('({} & (1 << {})) != 0'.format(discr_name, wp_bit))
            df_wp = df_dm.Filter('{0} >= {1}'.format(discr_name, wp_bit))
            turnOn_data[dm][wp] = {}
            for channel in channels:
                turnOn_data[dm][wp][channel] = {}
                df_ch = df_wp.Filter('pass_{} > 0.5'.format(channel))
                for model_name, hist_model in hist_models.items():
                    turn_on = TurnOnData()
                    turn_on.hist_total = df_wp.Histo1D(hist_model, var, 'weight')
                    turn_on.hist_passed = df_ch.Histo1D(hist_model, var, 'weight')
                    turnOn_data[dm][wp][channel][model_name] = turn_on

    for dm in decay_modes:
        for wp in working_points:
            for channel in channels:
                for model_name, hist_model in hist_models.items():
                    turn_on = turnOn_data[dm][wp][channel][model_name]
                    name_pattern = '{}_{}_{}{}_{}_{{}}'.format(label, channel, wp, dm_labels[dm], model_name)
                    turn_on.name_pattern = name_pattern
                    if 'fit' in model_name:
                        passed, total, eff = AutoRebinAndEfficiency(turn_on.hist_passed.GetPtr(),
                                                                    turn_on.hist_total.GetPtr(), bin_scan_pairs)
                    else:
                        passed, total = turn_on.hist_passed.GetPtr(), turn_on.hist_total.GetPtr()
                        # # new add by botao
                        # if (passed.Integral() < 0) or (total.Integral() < 0):
                        #     continue
                        # # end add
                        try:
                            FixEfficiencyBins(passed, total)
                        except:
                            continue
                        turn_on.eff = ROOT.TEfficiency(passed, total)
                        eff = turn_on.eff
                    output_file.WriteTObject(total, name_pattern.format('total'), 'Overwrite')
                    output_file.WriteTObject(passed, name_pattern.format('passed'), 'Overwrite')
                    output_file.WriteTObject(eff, name_pattern.format('eff'), 'Overwrite')
                    # print(name_pattern)
                    # print('hist_total {}'.format(turn_on.hist_total.GetPtr().GetNbinsX()))
                    # for n in range(turn_on.hist_total.GetPtr().GetNbinsX() + 1):
                    #     print('\t{} {} +/- {} {} +/- {}'.format(turn_on.hist_total.GetPtr().GetBinLowEdge(n+1), turn_on.hist_total.GetPtr().GetBinContent(n+1), turn_on.hist_total.GetPtr().GetBinError(n+1), turn_on.hist_passed.GetPtr().GetBinContent(n+1), turn_on.hist_passed.GetPtr().GetBinError(n+1)))
                    # print('hist_passed {}'.format(turn_on.hist_passed.GetPtr().GetNbinsX()))
                    # for n in range(turn_on.hist_passed.GetPtr().GetNbinsX() + 1):
                    #     print('\t{} {}'.format(turn_on.hist_passed.GetPtr().GetBinLowEdge(n+1), ))
                    #if 'fit' not in model_name:
                    #    turn_on.eff = ROOT.TEfficiency(turn_on.hist_passed.GetPtr(), turn_on.hist_total.GetPtr())
                    #    output_file.WriteTObject(turn_on.eff, name_pattern.format('passed'), 'Overwrite')

    return turnOn_data

output_dir =  os.path.dirname(args.output)
os.makedirs(output_dir, exist_ok=True)

output_file = ROOT.TFile(args.output + '.root', 'RECREATE')
input_files = [ args.input_data, args.input_dy_mc ]
n_inputs = len(input_files)
labels = [ 'data', 'mc' ]
var = 'tau_pt'
title, x_title = '#tau p_{T}', '#tau p_{T} (GeV)'
decay_modes = args.decay_modes.split(',')
channels = args.channels.split(',')
working_points = args.working_points.split(',')
bins, use_logx = CreateBins(200, False)
bins_fit, _ = CreateBins(200, True)
hist_models = {
    'plot': ROOT.RDF.TH1DModel(var, var, len(bins) - 1, array('d', bins)),
    'fit': ROOT.RDF.TH1DModel(var, var, len(bins_fit) - 1, array('d', bins_fit))
}
turnOn_data = [None] * n_inputs
for input_id in range(n_inputs):
    print("Creating {} histograms...".format(labels[input_id]))
    turnOn_data[input_id] = CreateHistograms(input_files[input_id], channels, decay_modes, 'tau_idDeepTau2018v2p5VSjet', # tau_idDeepTau2017v2p1VSjet,
                                             working_points, hist_models, labels[input_id], var, output_file)

colors = [ ROOT.kRed, ROOT.kBlack ]
canvas = RootPlotting.CreateCanvas()

n_plots = len(decay_modes) * len(channels) * len(working_points)
plot_id = 0
for channel in channels:
    for wp in working_points:
        for dm in decay_modes:
            if dm == 'all':
                dm_label = ''
                dm_plain_label = ''
            else:
                dm_label = ' DM={}'.format(dm)
                dm_plain_label = '_dm{}'.format(dm)
            ratio_graph = None
            ref_hist = hist_models['plot'].GetHistogram()
            ratio_ref_hist = ref_hist.Clone()
            turnOns = [None] * n_inputs
            curves = [None] * n_inputs
            for input_id in range(n_inputs):
                turnOns[input_id] = turnOn_data[input_id][dm][wp][channel]['plot']
                curves[input_id] = turnOns[input_id].eff
            y_min, y_max = (0, 1)
            y_title = 'Efficiency'
            title = '{} {}{}'.format(channel, wp, dm_label)
            plain_title = '{}_{}{}'.format(channel, wp, dm_plain_label)
            main_pad, ratio_pad, title_controls = RootPlotting.CreateTwoPadLayout(canvas, ref_hist, ratio_ref_hist,
                                                                                  log_x=use_logx, title=title)
            RootPlotting.ApplyAxisSetup(ref_hist, ratio_ref_hist, x_title=x_title, y_title=y_title,
                                        ratio_y_title='Ratio', y_range=(y_min, y_max * 1.1), max_ratio=1.5)
            legend = RootPlotting.CreateLegend(pos=(0.78, 0.28), size=(0.2, 0.15))
            for input_id in range(n_inputs):
                curve = curves[input_id]
                try:
                    curve.Draw('SAME')
                except:
                    continue
                RootPlotting.ApplyDefaultLineStyle(curve, colors[input_id])
                legend.AddEntry(curve, labels[input_id], 'PLE')

                if input_id < n_inputs - 1:
                    ratio_graph = RootPlotting.CreateEfficiencyRatioGraph(turnOns[input_id].hist_passed,
                                                                          turnOns[input_id].hist_total,
                                                                          turnOns[-1].hist_passed,
                                                                          turnOns[-1].hist_total)
                    if ratio_graph:
                        output_file.WriteTObject(ratio_graph, 'ratio_{}'.format(plain_title), 'Overwrite')
                        ratio_pad.cd()
                        ratio_color = colors[input_id] if n_inputs > 2 else ROOT.kBlack
                        RootPlotting.ApplyDefaultLineStyle(ratio_graph, ratio_color)
                        ratio_graph.Draw("0PE SAME")
                        main_pad.cd()
            legend.Draw()

            canvas.Update()
            output_file.WriteTObject(canvas, 'canvas_{}'.format(plain_title), 'Overwrite')
            RootPlotting.PrintAndClear(canvas, args.output + '.pdf', plain_title, plot_id, n_plots,
                                       [ main_pad, ratio_pad ])
            plot_id += 1
output_file.Close()
print("Success")
os._exit(0)
