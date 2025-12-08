# Script to plot mvis distributions for mu-tau and e-tau channels
# Author: Irene Andreou
# Date: September 2025

import uproot
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import matplotlib.ticker as ticker

# Apply CMS style
plt.style.use(hep.style.CMS)
output_folders = ['PASPlots', 'PaperPlots']
for d in ['PASPlots', 'PaperPlots']:
    os.makedirs(d, exist_ok=True)
for i in range(2):

    # Open the ROOT file
    for file_path in ["combined22_mt_uncorrected.root",
                      "combined22_mt_corrected.root",
                      "combined22_et_uncorrected.root",
                      "combined22_et_corrected.root"]:
        file = uproot.open(file_path)

        # Define TTree keys for the stack and the ratio plot (if needed -- this based on HiggsDNA ntuples)
        # prefix = "mt_inclusive_mTLt65/" if "mt" in file_path else "et_inclusive_mTLt65/"
        stack_keys = [
             "mvis_QCD_",
             "mvis_Top",
             "mvis_VV",
             "mvis_WJ",
             "mvis_ZJ",
             "mvis_ZL",
             "mvis_ZTT",
        ]
        if "et" in file_path:
            data_key = "mvis_EGamma_Run2022"
        elif "mt" in file_path:
            data_key = "mvis_Muon_Run2022"

        # Define labels for the stacked histograms
        stack_labels = [
            r"$\mathrm{QCD~multijet}$",
            r"$t\bar{t}~\mathrm{and~single}~t$",
            r"$\mathrm{Diboson}$",
            r"$W~+~\mathrm{jets}$",
            r"$Z \rightarrow \ell\ell$, $j\rightarrow \tau_h$",
            r"$Z~\rightarrow \ell\ell$, $\ell \rightarrow \tau_h$",
            r"$Z~\rightarrow \tau_\mu\tau_h$" if "mt" in file_path else r"$Z~\rightarrow \tau_e\tau_h$",
        ]

        # Define the new color palette with the specified colours
        colours = [
            '#832db6',  # QCD
            '#94a4a2',  # TTbar
            "#a96b59",  # Diboson
            "#bd1f01",  # WJ
            "#b9ac70",  # DY
            "#3f90da",  # Zll
            '#ffa90e',  # ZTT
        ]

        # Function to extract data from TTree - uproot TH1 objects from HiggsDNA
        def extract_hist_data(hist):
            bin_contents = hist.values()
            bin_errors = np.sqrt(hist.variances())
            bin_edges = hist.axes[0].edges()
            bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
            return bin_centers, bin_contents, bin_errors

        # Extract stack histograms and data histogram
        stack_histograms = []
        for key in stack_keys:
            if isinstance(key, list):
                # Sum histograms for grouped keys
                hists = [file[k] for k in key]
                # Sum bin contents and variances
                summed_values = np.sum([h.values() for h in hists], axis=0)
                summed_variances = np.sum([h.variances() for h in hists], axis=0)
                bin_edges = hists[0].axes[0].edges()
                bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
                bin_errors = np.sqrt(summed_variances)
                stack_histograms.append((bin_centers, summed_values, bin_errors))
            else:
                stack_histograms.append(extract_hist_data(file[key]))
        data_histogram = extract_hist_data(file[data_key])

        # Prepare stack histograms
        bin_centers = stack_histograms[0][0]  # Bin centers are the same for all
        stack_values = np.array([h[1] for h in stack_histograms])  # Bin contents
        stack_errors = np.array([h[2] for h in stack_histograms])  # Bin errors

        # Calculate bin edges from bin centers (assuming uniform bin widths)
        bin_width = bin_centers[1] - bin_centers[0]
        bin_edges = np.append(bin_centers - bin_width / 2, bin_centers[-1] + bin_width / 2)

        # Sum stack values for the ratio plot
        stack_sum_values = np.sum(stack_values, axis=0)
        stack_sum_errors = np.sqrt(np.sum(stack_errors**2, axis=0))  # Combine errors in quadrature

        # Data values and errors
        data_values = data_histogram[1]
        data_errors = data_histogram[2]

        # Avoid division by zero in ratio values
        ratio_values = np.ones_like(data_values)  # Default ratio value is 1
        ratio_errors = np.zeros_like(data_errors)  # Default ratio error is 0
        nonzero_mask = stack_sum_values > 0  # Mask for nonzero stack sum

        # Only compute ratio and errors where stack_sum_values > 0
        ratio_values[nonzero_mask] = data_values[nonzero_mask] / stack_sum_values[nonzero_mask]
        ratio_errors[nonzero_mask] = ratio_values[nonzero_mask] * np.sqrt(
            (data_errors[nonzero_mask] / data_values[nonzero_mask]) ** 2 +
            (stack_sum_errors[nonzero_mask] / stack_sum_values[nonzero_mask]) ** 2
        )

        # Create the plot
        fig, axs = plt.subplots(2, 1, gridspec_kw={'height_ratios': [5, 1]}, sharex=True, figsize=(9, 9))
        fig.subplots_adjust(hspace=0.08)

        # Top plot: Stacked histograms with step outlines
        cumulative = np.zeros_like(stack_values[0], dtype=np.float64)  # Initialize cumulative array
        for values, label, colour in zip(stack_values, stack_labels, colours):
            # Fill the stacked histogram
            axs[0].fill_between(
                bin_edges,
                np.append(cumulative, cumulative[-1]),
                np.append(cumulative + values, (cumulative + values)[-1]),
                step="post",
                label=label,
                color=colour
            )
            # Add step outline
            axs[0].step(
                bin_edges,
                np.append(cumulative + values, (cumulative + values)[-1]),
                where="post",
                color="black",
                linewidth=0.5
            )
            cumulative += values  # Update cumulative

        # Add statistical uncertainty band
        axs[0].fill_between(
            bin_centers,
            stack_sum_values - stack_sum_errors,
            stack_sum_values + stack_sum_errors,
            step="mid",
            facecolor='none',
            hatch='////',
            edgecolor='gray',
            linewidth=0,
            alpha=0.5,
            label=r"$\mathrm{Stat.~unc.}$"
        )

        # Add observed data points
        axs[0].errorbar(
            bin_centers, data_values, yerr=data_errors, fmt="o", color="black", label=r"$\mathrm{Data}$", markersize=8
        )
        axs[0].set_ylabel("Events / 5 GeV",  fontsize=24)
        axs[0].tick_params(axis='both', which='major', labelsize=24)

        # Determine calibration status based on the filename
        calibration_status = "Pre-calibration" if "uncorrected" in file_path else "Post-calibration"

        # Add calibration status text beneath the legend
        axs[0].text(
            0.2, 0.9,  # Position relative to the legend
            calibration_status,   
            transform=axs[0].transAxes,
            fontweight='bold',
            fontsize=22,
            verticalalignment='top',
            horizontalalignment='left',
        )

        # Add legends
        handles, labels = axs[0].get_legend_handles_labels()
        # Choose ZTT label based on channel
        if "mt" in file_path:
            ztt_label = r"$Z~\rightarrow \tau_\mu\tau_h$"
        else:
            ztt_label = r"$Z~\rightarrow \tau_e\tau_h$"
        # Move ZTT to the top of the legend
        order = [labels.index(r"$\mathrm{Data}$"), labels.index(ztt_label)] + [
            i for i in range(len(labels)) if i not in (labels.index(ztt_label), labels.index(r"$\mathrm{Data}$"))
        ]
        axs[0].legend([handles[idx] for idx in order], [labels[idx] for idx in order], fontsize=22, loc="upper right", frameon=False, ncol=1)
        axs[0].set_ylim(0, max(data_values) * 1.5)
        axs[0].set_xlim(bin_edges[0], bin_edges[-1])
        # Use ScalarFormatter for scientific notation with math text (gives ×10⁶ style)
        formatter = ticker.ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((0, 0))
        axs[0].yaxis.set_major_formatter(formatter)

        # Move the offset text (×10^n) to the left
        offset = axs[0].yaxis.get_offset_text()
        offset.set_x(-0.1)  # Adjust this value as needed

        # Bottom plot: Ratio plot with stat uncertainty
        axs[1].errorbar(
            bin_centers, ratio_values, yerr=ratio_errors, fmt="o", color="black", label=r"$\mathrm{Ratio}$", markersize=8
        )
        axs[1].fill_between(
            bin_centers,
            1 - stack_sum_errors / np.maximum(stack_sum_values, 1e-10),  # Avoid division by zero
            1 + stack_sum_errors / np.maximum(stack_sum_values, 1e-10),
            step="mid",
            facecolor='none',
            hatch='////',
            edgecolor='gray',
            linewidth=0,
            alpha=0.5,
            label=r"$\mathrm{Stat.~unc.}$"
        )
        axs[1].axhline(1, color="red", linestyle="--")
        axs[1].set_xlabel(r"$m_\mathrm{vis}$ (GeV)", fontsize=24)
        axs[1].set_ylabel("Obs. / Exp.", fontsize=24)
        axs[1].tick_params(axis='both', which='major', labelsize=24)
        axs[1].set_ylim(0.4, 1.65)
        axs[1].set_xlim(bin_edges[0], bin_edges[-1])

        # Figure name based on input file dictionary
        fig_names = {
            "combined22_mt_uncorrected.root": "mvis_mt_wCorrTight-signalRegion-2022_woSF.pdf",
            "combined22_mt_corrected.root": "mvis_mt_wCorrTight-signalRegion-2022_wSF.pdf",
            "combined22_et_uncorrected.root": "mvis_et_wCorrTight2-tightVsele-2022_woSF.pdf",
            "combined22_et_corrected.root": "mvis_et_wCorrTight2-tightVsele-2022_wSF.pdf",

        }


        # Apply CMS label
        cms_label = hep.cms.label("Preliminary" if i == 0 else "", ax=axs[0], loc=0, data=True, lumi=35.1, com=13.6, fontsize=24)

        plt.savefig(f'{output_folders[i]}/{fig_names[file_path]}', bbox_inches='tight')

        print(f"Plot saved as '{output_folders[i]}/{fig_names[file_path]}'")
        for artist in cms_label:
                artist.remove()