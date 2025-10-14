import math
import numpy as np
import scipy
import scipy.optimize
import ROOT

from RootObjects import Histogram, Graph, MultiGraph

def KatzLog(passed, total):
    """Returns 1-sigma confidence interval for a ratio of proportions using Katz-log method."""
    if np.count_nonzero(total) != len(total):
        raise RuntimeError("Total can't be zero")
    if np.count_nonzero(passed < 0) != 0 or np.count_nonzero(total < 0) != 0:
        raise RuntimeError("Yields can't be negative")
    if np.count_nonzero(passed > total) != 0:
        raise RuntimeError("Passed can't be bigger than total")
    if passed[0] == 0 and passed[1] == 0:
        return (0, math.inf)
    if passed[0] == total[0] and passed[1] == total[1]:
        y1 = total[0] - 0.5 if total[0] > 0.5 else total[0] * 0.99
        y2 = total[1] - 0.5 if total[1] > 0.5 else total[1] * 0.99
        # in some sources -1 instead of -0.5 is recommended for y2
    else:
        y1 = passed[0] if passed[0] != 0 else 0.5
        y2 = passed[1] if passed[1] != 0 else 0.5
    n1 = total[0]
    n2 = total[1]
    pi1 = y1 / n1
    pi2 = y2 / n2
    theta = pi1 / pi2
    sigma2 = (1 - pi1) / (pi1 * n1) + (1 - pi2) / (pi2 * n2)
    if sigma2 < 0:
        raise RuntimeError("Invalid inputs: passed={}, total={}".format(passed, total))
    sigma = math.sqrt(sigma2)
    return (theta * math.exp(-sigma), theta * math.exp(sigma))

def weighted_eff_confint_freqMC(n_passed, n_failed, n_passed_err, n_failed_err, alpha=1-0.68, n_gen=100000,
                                max_gen_iters=100, min_stat=80000, seed=42, symmetric=True):
    assert n_passed > 0
    assert n_failed > 0
    assert n_passed_err >= 0
    assert n_failed_err >= 0
    assert alpha > 0 and alpha < 1
    assert n_gen > 0
    assert max_gen_iters > 0
    assert min_stat > 0
    failed_mc = np.empty(0)
    passed_mc = np.empty(0)
    if seed is not None:
        np.random.seed(seed)
    for gen_iter in range(max_gen_iters):
        new_failed_mc = np.random.normal(n_failed, n_failed_err, n_gen)
        new_passed_mc = np.random.normal(n_passed, n_passed_err, n_gen)
        sel = (new_failed_mc >= 0) & (new_passed_mc >= 0)
        failed_mc = np.append(failed_mc, new_failed_mc[sel])
        passed_mc = np.append(passed_mc, new_passed_mc[sel])
        n_samples = len(passed_mc)
        if n_samples >= min_stat:
            eff = passed_mc / (passed_mc + failed_mc)
            break
    if n_samples < min_stat:
        raise RuntimeError("Unable to estimate confinterval please, increase MC statistics.")
    eff_exp = n_passed / float(n_passed + n_failed)

    if symmetric:
        def coverage(delta_eff):
            x = np.count_nonzero((eff > eff_exp - delta_eff) & (eff < eff_exp + delta_eff))
            return x / float(n_samples)
        opt = scipy.optimize.root_scalar(lambda x: coverage(x) - 1 + alpha, bracket=(0, 1), method='bisect')
        if not opt.converged:
            raise RuntimeError("weighted_eff_confint_freqMC: unable to find a symmetric conf interval.")
        q_down = max(0., eff_exp - opt.root)
        q_up = min(1., eff_exp + opt.root)
        return q_down, q_up
    else:
        eff_up = eff[eff > eff_exp]
        eff_down = eff[eff <= eff_exp]
        frac_up = len(eff_up) / float(n_samples)
        frac_down = len(eff_down) / float(n_samples)
        assert frac_up > 0
        assert frac_down > 0

        def L(alpha_up, return_interal=False):
            alpha_up = min(alpha, max(0, alpha_up))
            alpha_down = (alpha - alpha_up)
            alpha_up_scaled = alpha_up / frac_up
            alpha_down_scaled = min(1., alpha_down / frac_down)

            q_up = np.quantile(eff_up, 1 - alpha_up_scaled) if alpha_up != 0 else 1.
            q_down = np.quantile(eff_down, alpha_down_scaled) if alpha_down != 0 else 0.
            l = q_up - q_down
            if return_interal:
                return l, q_down, q_up
            return l

        opt = scipy.optimize.minimize_scalar(L, bounds=(0, min(alpha, frac_up)), method='Bounded')
        if not opt.success:
            raise RuntimeError("weighted_eff_confint_freqMC: unable to find a conf interval with the minimal size.")

        _, q_down, q_up = L(opt.x, True)
        return q_down, q_up

def ListToStdVector(l, elem_type='string'):
    v = ROOT.std.vector(elem_type)()
    for x in l:
        if elem_type in ['Int_t', 'UInt_t']:
            x = int(x)
        v.push_back(x)
    return v

def RemoveOverflowBins(hist):
    for bin in [ 0, hist.GetNbinsX() + 1 ]:
        hist.SetBinContent(bin, 0)
        hist.SetBinError(bin, 0)

def FixNegativeBins(hist, fix_integral=False, max_rel_shift=0.01):   # comment by botao for origin: max_rel_shift=0.01
    has_fixes = False
    integral = hist.Integral()
    if integral <= 0:
        raise RuntimeError("Unable to fix negative bins if integral <= 0.")
    for n in range(hist.GetNbinsX() + 2):
        x = hist.GetBinContent(n)
        if x < 0:
            x_err = hist.GetBinError(n)
            if x + x_err < 0:    # comment by botao to pass the RuntimeError
                raise RuntimeError("Yield in bin {} is {} +- {}. Negative bin for which the yield is not statistically"
                                   " compatible with 0 can't be fixed.".format(n, x, x_err))
            hist.SetBinError(n, math.sqrt(x_err ** 2 + x ** 2))
            hist.SetBinContent(n, 0)
            has_fixes = True
    if has_fixes:
        new_integral = hist.Integral()
        total_rel_shift = abs(new_integral - integral) / integral
        if total_rel_shift > max_rel_shift:
            raise RuntimeError("The overal shift to the integral due to negative bins = {} is above the allowed limit" \
                               " = {}.".format(total_rel_shift, max_rel_shift))
        if fix_integral:
            sf = integral / new_integral
            hist.Scale(sf)

def FixEfficiencyBins(hist_passed, hist_total, remove_overflow=True):
    if remove_overflow:
        RemoveOverflowBins(hist_passed)
        RemoveOverflowBins(hist_total)
    FixNegativeBins(hist_passed)
    FixNegativeBins(hist_total)
    for n in range(hist_total.GetNbinsX() + 2):
        if hist_passed.GetBinLowEdge(n) != hist_total.GetBinLowEdge(n):
            raise RuntimeError("Incompatible passed and total histograms")
        delta = hist_passed.GetBinContent(n) - hist_total.GetBinContent(n)
        if delta > 0:
            if delta > hist_passed.GetBinError(n) :  # comment by botao, plus 10 to skip the error 
                raise RuntimeError("The number of passed events = {} +/- {} is above the total number events" \
                                   " = {} +/- {} in bin {} [{}, {})" \
                                   .format(hist_passed.GetBinContent(n), hist_passed.GetBinError(n),
                                           hist_total.GetBinContent(n), hist_total.GetBinError(n), n,
                                           hist_total.GetBinLowEdge(n),
                                           hist_total.GetBinLowEdge(n) + hist_total.GetBinWidth(n)))
            hist_passed.SetBinError(n, math.sqrt(hist_passed.GetBinError(n) ** 2 + delta ** 2))
            hist_passed.SetBinContent(n, hist_total.GetBinContent(n))

def AutoRebinAndEfficiency(hist_passed, hist_total, bin_scan_pairs):
    passed, total = 0, 1
    hist = [ hist_passed, hist_total ]
    for n in range(len(hist)):
        if type(hist[n]) != Histogram:
            hist[n] = Histogram(hist[n])

    n_bins = hist_total.GetNbinsX()
    graphs = MultiGraph(len(hist) + 1, n_bins)

    n = 0
    n_output_points = 0
    abs_min_total_yield = bin_scan_pairs[-1][-1]
    while n < n_bins:
        if np.sum(hist[total].values[n:]) < abs_min_total_yield:
            break
        for max_bin_size, max_rel_error in bin_scan_pairs:
            bin_created=False
            v_counter = np.zeros(len(hist))
            w2_counter = np.zeros(len(hist))
            k = 0
            while k < max_bin_size and n + k < n_bins:
                for sel_id in range(len(hist)):
                    v_counter[sel_id] += hist[sel_id].values[n+k]
                    w2_counter[sel_id] += hist[sel_id].errors[n+k] ** 2
                if v_counter[total] > 0 and math.sqrt(w2_counter[total]) / v_counter[total] < max_rel_error \
                   and v_counter[passed] > 0 and v_counter[passed] < v_counter[total]:
                   #if v_counter[total] >= min_yield and v_counter[passed] > 0 and v_counter[passed] < v_counter[total]:
                    eff = v_counter[passed] / v_counter[total]
                    x_avg = np.average(hist[total].edges[n:n+k+1], weights=hist[total].values[n:n+k+1])
                    graphs.x[n_output_points] = x_avg
                    graphs.x_error_low[n_output_points] = x_avg - hist[total].edges[n]
                    graphs.x_error_high[n_output_points] = hist[total].edges[n+k+1] - x_avg
                    for sel_id in range(len(hist)):
                        graphs.y[sel_id, n_output_points] = v_counter[sel_id]
                        graphs.y_error_low[sel_id, n_output_points] = math.sqrt(w2_counter[sel_id])
                        graphs.y_error_high[sel_id, n_output_points] = math.sqrt(w2_counter[sel_id])
                    graphs.y[len(hist), n_output_points] = eff
                    eff_down, eff_up = weighted_eff_confint_freqMC(v_counter[passed],
                                                                   v_counter[total] - v_counter[passed],
                                                                   math.sqrt(w2_counter[passed]),
                                                                   math.sqrt(w2_counter[total] - w2_counter[passed]))
                    graphs.y_error_low[len(hist), n_output_points] = eff - eff_down
                    graphs.y_error_high[len(hist), n_output_points] = eff_up - eff
                    n_output_points += 1
                    bin_created = True
                    break
                k += 1
            if bin_created: break
        n += k + 1
    return tuple(graphs.ToRootGraphs(n_output_points))

def AutoRebinAndEfficiencyforDataMCboth(hist_passed, hist_total, bin_scan_pairs, hist_passed_mc, hist_total_mc):
    passed, total = 0, 1
    hist = [ hist_passed, hist_total ]
    for n in range(len(hist)):
        if type(hist[n]) != Histogram:
            hist[n] = Histogram(hist[n])
    # for mc
    hist_mc = [ hist_passed_mc, hist_total_mc ]
    for n in range(len(hist_mc)):
        if type(hist_mc[n]) != Histogram:
            hist_mc[n] = Histogram(hist_mc[n])
    # end mc

    n_bins = hist_total.GetNbinsX()
    graphs = MultiGraph(len(hist) + 1, n_bins)
    # for mc
    graphs_mc = MultiGraph(len(hist_mc) + 1, n_bins)
    # end mc

    n = 0
    n_output_points = 0
    abs_min_total_yield = bin_scan_pairs[-1][-1]
    while n < n_bins:
        if np.sum(hist[total].values[n:]) < abs_min_total_yield:
            break
        for max_bin_size, max_rel_error in bin_scan_pairs:
            bin_created=False
            v_counter = np.zeros(len(hist))
            w2_counter = np.zeros(len(hist))
            # for mc
            v_counter_mc = np.zeros(len(hist_mc))
            w2_counter_mc = np.zeros(len(hist_mc))
            # end mc
            k = 0
            while k < max_bin_size and n + k < n_bins:
                for sel_id in range(len(hist)):
                    v_counter[sel_id] += hist[sel_id].values[n+k]
                    w2_counter[sel_id] += hist[sel_id].errors[n+k] ** 2
                    # for mc
                    v_counter_mc[sel_id] += hist_mc[sel_id].values[n+k]
                    w2_counter_mc[sel_id] += hist_mc[sel_id].errors[n+k] ** 2
                    # end mc
                if v_counter[total] > 0 and math.sqrt(w2_counter[total]) / v_counter[total] < max_rel_error \
                   and v_counter[passed] > 0 and v_counter[passed] < v_counter[total]:
                   #if v_counter[total] >= min_yield and v_counter[passed] > 0 and v_counter[passed] < v_counter[total]:
                    
                    eff = v_counter[passed] / v_counter[total]
                    x_avg = np.average(hist[total].edges[n:n+k+1], weights=hist[total].values[n:n+k+1])
                    graphs.x[n_output_points] = x_avg
                    graphs.x_error_low[n_output_points] = x_avg - hist[total].edges[n]
                    graphs.x_error_high[n_output_points] = hist[total].edges[n+k+1] - x_avg
                    for sel_id in range(len(hist)):
                        graphs.y[sel_id, n_output_points] = v_counter[sel_id]
                        graphs.y_error_low[sel_id, n_output_points] = math.sqrt(w2_counter[sel_id])
                        graphs.y_error_high[sel_id, n_output_points] = math.sqrt(w2_counter[sel_id])
                    graphs.y[len(hist), n_output_points] = eff
                    eff_down, eff_up = weighted_eff_confint_freqMC(v_counter[passed],
                                                                   v_counter[total] - v_counter[passed],
                                                                   math.sqrt(w2_counter[passed]),
                                                                   math.sqrt(w2_counter[total] - w2_counter[passed]))
                    graphs.y_error_low[len(hist), n_output_points] = eff - eff_down
                    graphs.y_error_high[len(hist), n_output_points] = eff_up - eff
                    # for mc
                    eff_mc = v_counter_mc[passed] / v_counter_mc[total]
                    x_avg_mc = np.average(hist_mc[total].edges[n:n+k+1], weights=hist_mc[total].values[n:n+k+1])
                    graphs_mc.x[n_output_points] = x_avg_mc
                    graphs_mc.x_error_low[n_output_points] = x_avg_mc - hist_mc[total].edges[n]
                    graphs_mc.x_error_high[n_output_points] = hist_mc[total].edges[n+k+1] - x_avg_mc
                    for sel_id in range(len(hist)):
                        graphs_mc.y[sel_id, n_output_points] = v_counter_mc[sel_id]
                        graphs_mc.y_error_low[sel_id, n_output_points] = math.sqrt(w2_counter_mc[sel_id])
                        graphs_mc.y_error_high[sel_id, n_output_points] = math.sqrt(w2_counter_mc[sel_id])
                    graphs_mc.y[len(hist), n_output_points] = eff_mc
                    eff_down_mc, eff_up_mc = weighted_eff_confint_freqMC(v_counter_mc[passed],
                                                                   v_counter_mc[total] - v_counter_mc[passed],
                                                                   math.sqrt(w2_counter_mc[passed]),
                                                                   math.sqrt(w2_counter_mc[total] - w2_counter_mc[passed]))
                    graphs_mc.y_error_low[len(hist), n_output_points] = eff_mc - eff_down_mc
                    graphs_mc.y_error_high[len(hist), n_output_points] = eff_up_mc - eff_mc
                    # end mc
                    n_output_points += 1
                    bin_created = True
                    break
                k += 1
            if bin_created: break
        n += k + 1
    return tuple(graphs.ToRootGraphs(n_output_points)+graphs_mc.ToRootGraphs(n_output_points))
