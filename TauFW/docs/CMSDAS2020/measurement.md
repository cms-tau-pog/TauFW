# 9. Performing the measurement

After having created the workspaces for the &mu;&tau;<sub>h</sub>, e&mu; final states, and their combination, as documented in section [8](prep_stat_inference.md),
you are ready to perform calculations with `combineTool.py` and obtain measurements in the context of the Z&rarr;&tau;&tau; analysis.

In the following, several `combineTool.py` commands will be given, with slightly different settings, such that it is important,
that you understand the differences among them.

With the first command, we run a maximum likelihood fit for the signal strength, assuming that &tau;<sub>h</sub> identification efficiency is fixed, and the corresponding scale factor is equal to 1.0.
For this command, all used options will be explained in detail.

```sh
combineTool.py -M MultiDimFit -d ztt_analysis/2018/mutau/workspace.root --there --algo singles --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --floatOtherPOIs 1 --setParameterRanges r=0.7,1.3 --freezeParameters tauh_id -n .r_with_tauID_fixed -v1  --setParameters r=1.0
```

Let us go through the different options of `combineTool.py` step by step.

+ `-M MultiDimFit`: This is specifying the method to be executed by `combine`. `MultiDimFit` is one of the common possibilities to perform maximum likelihood fits, for one or more parameters of interest.
+ `-d ztt_analysis/2018/mutau/workspace.root`: Path to the datacard or workspace to be used in the calculation.
+ `--there`: Produce outputs in the folder of the datacard/workspace. In this case, that is `ztt_analysis/2018/mutau/`.
+ `--algo singles`: An option specific to `MultiDimFit` method. Performs the a fit for each parameter of interest separately, *profiling* the other, that means, treating other parameters of interest
as nuisance parameters. The method also computes uncertainties for each parameter of interest under study, taking into account correlation with all other parameters.
+ `--robustFit 1`: specifying, that the uncertainty estimates for the parameters of interest, should be obtained from scans of these parameter, and not from estimates of the covariance matrix.
+ `--X-rtd MINIMIZER_analytic`: enabling a **r**un**t**ime **d**efined variable. In this case: flag to use analyting minimization procedure in the maximum likelihood fit.
Sidenode: maximizing the likelihood function L is mathematically equivalent with minimizing - 2 &middot; ln(L).
+ `--X-rtd FITTER_DYN_STEP`: enabling a **r**un**t**ime **d**efined variable. Here, it enable dynamic determination of steps between scan points for example for the scan enabled with `--robustFit 1`.
+ `--cminDefaultMinimizerStrategy 0 `: Choice of the default minimization strategy. For the value 0, the computation of the covariance matrix for all parameters is omitted, such that the computation
is faster. That is a valid choice, if only uncertainties are of interest, and these are derived in a different way, for example via `--robustFit 1`.
+ `--cminDefaultMinimizerTolerance 0.1`: Choice of the default tolerance in the minimization. Defines, how picke the criterium is to stop the minimization. The values 0.01 and 0.1 are the ones
chosen ofen, the latter being less stricter, but could lead to more stable results.
+ `--floatOtherPOIs 1` : An option specific to `MultiDimFit` method. If enabled, the other specified parameters of interest are *profiled*, and not fixed to a specified value.
+ `--setParameterRanges r=0.7,1.3`: Setting the ranges allowed in the fit for parameter `r` to specified values. This option can also be used for all other parameters. 
+ `--freezeParameters tauh_id `: Explicitly stating to keep parameter `tauh_id` fixed at a specified value. This option can also be used for all other parameters.
+ `--setParameters r=1.0`: Setting the parameter `r` to a nominal value, from which the fit will start.
+ `-n .r_with_tauID_fixed`: Add a suffix to the name of the output files.
+ `-v1`: increase the verbosity level to 1.

At this point: congragulations to your first fit of the signal strength for the Z&rarr;&tau;&tau; contribution, &mu;<sub>Z&rarr;&tau;&tau;</sub>! Does the numerical value of the parameter `r`
correspond to what you would expect from what you have seen in the control plots?

In the next step, let us drop the fixing of the &tau;<sub>h</sub> identification efficiency parameter, `tauh_id`, and let the maximum likelihood fit find best estimate of `tauh_id` on its own:

```sh
combineTool.py -M MultiDimFit -d ztt_analysis/2018/mutau/workspace.root --there --algo singles --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --floatOtherPOIs 1 --setParameterRanges r=0.7,1.3:tauh_id=0.7,1.3 -n .r_with_tauID_floating -v1  --setParameters r=1.0,tauh_id=1.0 --redefineSignalPOIs r,tauh_id
```

In the command above, we have made te following adaptions:

+ Parameter `tauh_id` is elevated to a parameter of interest by specifying `--redefineSignalPOIs r,tauh_id` (`r` is then still kept as parameter of interest).
+ Parameter `tauh_id` is not fixed anymore.
+ Range and the nominal value of `tauh_id` are specified.
+ Naming of the output files is changed.

Has the value for the signal strength parameter `r` changed? What about `tauh_id`? Do you think this is reasonable? Keep in mind, that both parameters modify the yield of the `ZTT` contribution
in a very similar way. Therefore think about what happens with one parameter, if the other is increased.

To quantify these thoughts into a numerical value, we can have a look at the correlation between `r` and `tauh_id`. To do this, we use the `-M FitDiagnostics` method, which saves the fit result, keeping
the estimated values of all parameters, as well as the correlations between them. The command reads as follows:

```sh
combineTool.py -M FitDiagnostics -d ztt_analysis/2018/mutau/workspace.root --there --robustFit 1 --robustHesse 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --setParameterRanges r=0.7,1.3:tauh_id=0.7,1.3 -n .r_vs_tauID_correlation -v1  --setParameters r=1.0,tauh_id=1.0
```

The following changes were included into the command:

+ `--algo singles`, `--floatOtherPOIs 1`, and `--redefineSignalPOIs r,tauh_id` were removed.
+ `--robustFit 1` extended with `--robustHesse 1` to enable a robust computation of the Hesse matrix used for the computation of the correlation matrix.

The resulting fit result is then stored in the `ztt_analysis/2018/mutau/fitDiagnostics.r_vs_tauID_correlation.root` output file. To print the correlation between `r` and `tauh_id`, you can use the
`print correlation.py` script:

```sh
print_correlation.py ztt_analysis/2018/mutau/fitDiagnostics.r_vs_tauID_correlation.root r tauh_id
```

Is the resulting correlation as you would have it expected? If you like to see, how the correlation was accessed, feel free to have a look at the script `print_correlation.py`.

A very interesting check would be to perform the commands above, including the e&mu; final state into the statistical inference,
running on the combined workspace in `ztt_analysis/2018/cmb/workspace.root`. How do the uncertainties, central values, and the correlations of `r` and `tau_id` change?

The last missing piece in terms of results is the derivation of the cross-section for Z&rarr;&tau;&tau;. This can be done by performing the fitting commands with a slightly modified setup.
To understand, what needs to be changed, let us recap, how actually the signal strength is defined:

&mu;<sub>Z&rarr;&tau;&tau;</sub> = ( &sigma;(Z) &middot; BR(Z&rarr;&tau;&tau;) ) / ( &sigma;<sub>SM</sub>(Z) &middot; BR<sub>SM</sub>(Z&rarr;&tau;&tau;) ).

So &mu;<sub>Z&rarr;&tau;&tau;</sub> is the ratio of two products: the measured cross-section times branching fraction, devided by the cross-section times branching fraction expected from the
Standard Model (SM).

This means: if measuring &mu;<sub>Z&rarr;&tau;&tau;</sub>, uncertainties on the SM expectation - &sigma;<sub>SM</sub>(Z) &middot; BR<sub>SM</sub>(Z&rarr;&tau;&tau;) - needs to be taken into account.
But if we multiply the signal strength by the SM expectation to perform the cross-section measurement, this product cancels out, such that the corresonding uncertainties can be neglected.

The procedure for the cross-section measurement is then the following:

+ Measure the signal strength with **fixed** nuisance parameter for &sigma;<sub>SM</sub>(Z) &middot; BR<sub>SM</sub>(Z&rarr;&tau;&tau;), called `xsec_ztt`.
+ Multiply the resulting signal strength value (and its uncertainties) by the SM expectation.

In case of the &sigma;<sub>SM</sub>(Z) &middot; BR<sub>SM</sub>(Z&rarr;&tau;&tau;) value, the one should be taken, for which the corresponding fiducial phase space matches the best the selection of
reconstructed quantities. But to keep it simple in our case, we take just the value of the Drell-Yan sample cross-section, devided by 3:

Our &sigma;<sub>SM</sub>(Z) &middot; BR<sub>SM</sub>(Z&rarr;&tau;&tau;) = 6077.22/3.0 [pb] = 2025.74 [pb]

The command for the signal strength computation reads as follows after extending the last command using `-M MultiDimFit` with `--freezeParameters xsec_ztt`:

```sh
combineTool.py -M MultiDimFit -d ztt_analysis/2018/mutau/workspace.root --there --algo singles --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --floatOtherPOIs 1 --setParameterRanges r=0.7,1.3:tauh_id=0.7,1.3 -n .r_with_tauID_floating_for_xsec -v1  --setParameters r=1.0,tauh_id=1.0 --redefineSignalPOIs r,tauh_id --freezeParameters xsec_ztt
```

With this CombineHarvester command, we have obtained all results of interest. Enjoy! :)

In the following, we will discuss a few alternatives to visualize the results better, and to make some additional diagnostics.

## Further commands for visualizing the results and diagnostics

In some cases, it might be useful to plot the likelihood scan performed for the fit of the signal strength parameter, or the &tau;<sub>h</sub> identification efficiency. To obtain this, we will
do the scan performed by `--robustFit 1` option by hand, specifying the points to scan. This can be done by using the already familier `-M MultiDimFit` method:

Performing the scan:

```sh
combineTool.py -M MultiDimFit -d ztt_analysis/2018/mutau/workspace.root --there --algo grid --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --floatOtherPOIs 1 --setParameterRanges r=0.65,1.1 -n .r_scan -v1  --setParameters r=1.0  --points 41 --split-points 8 --alignEdges 1 --parallel 5
```

Changes with respect to the `--robustFit 1` command to obtain the fit result:

+ `--algo grid`: Instead of performing the fit for the parameter of interest `r`, the likelihood is evaluated at fixed value of `r` in a predefined grid of values.
+ `--setParameterRanges r=0.65,1.1`, `--points 41` and `--alignEdges 1`: Settings, which define grid values are used for `r`. The option `--alignEdges 1` is used to make
sure, that the range edges are included in the scan. Please define the range with a bit higher values, than the uncertainty estimates around the best-estimate value you know
from the fit command.
+ `-n .r_scan`: Changed name suffix to distinguish from other files.
+ `--parallel 5`: The fits for each of the grid points are configured to run in parallel on 5 CPUs.

After the calculations for each grid value are finished, you can `hadd` the output files to one file:

```sh
hadd -f ztt_analysis/2018/mutau/higgsCombine.r_scan.MultiDimFit.mH120.root ztt_analysis/2018/mutau/higgsCombine.r_scan.POINTS.*.root
```

And plot the scan with:

```sh
plot1DScan.py ztt_analysis/2018/mutau/higgsCombine.r_scan.MultiDimFit.mH120.root -o r_scan --translate $CMSSW_BASE/src/CombineHarvester/CMSDAS2020TauLong/data/translate.json --POI r --logo-sub "CMSvDAS 2020 Tau"
```

To visualize the correlations, it is often very useful to perform such likelihood scans also in a 2-dimensional grid. Let us try it for the parameters `r` and `tauh_id`.

```sh
combineTool.py -M MultiDimFit -d ztt_analysis/2018/mutau/workspace.root --there --algo grid --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --floatOtherPOIs 1 --setParameterRanges r=0.5,1.6:tauh_id=0.5,1.6 -n .r_vs_tauh_id_scan -v1  --setParameters r=1.0,tauh_id=1.0  --points 1600 --split-points 320 --parallel 5 --redefineSignalPOIs r,tauh_id
```

After that, we put the outputs together:

```sh
hadd -f ztt_analysis/2018/mutau/higgsCombine.r_vs_tauh_id_scan.MultiDimFit.mH120.root ztt_analysis/2018/mutau/higgsCombine.r_vs_tauh_id_scan.POINTS.*.root
```

And then, plot the 68% and 95% confidence level regions:

```sh
plotMultiDimFit.py ztt_analysis/2018/mutau/higgsCombine.r_vs_tauh_id_scan.MultiDimFit.mH120.root --cms-sub "CMSvDAS 2020 Tau" --x-title "#mu_{Z#rightarrow#tau#tau}" --y-title "^{}#tau_{h} ID scale factor" --pois r tauh_id --title-left "^{}#mu^{}#tau_{h} final state"
```

The last useful tool from CombineHarvester for visualization and diagnostics presented here in the context of the Z&rarr;&tau;&tau; cross-section measurement is the investigation of impacts of different
nuisance parameters on the signal strength `r`. A corresponding method `-M Impacts` is used to perform this investigation.

At first, an initial fit is performed, very similar to the `-M FitDiagnostics` command:

```sh
combineTool.py -M Impacts --doInitialFit -d ztt_analysis/2018/mutau/workspace.root --there --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --setParameterRanges r=0.5,1.5:tauh_id=0.5,1.5 -v1  --setParameters r=1.0,tauh_id=1.0 -m 125
```

Then, each of the nuisance parameters is elevated to a parameter of interest, while `r` is left floating, like a nuisance parameter. The profiled likelihood is then evaluated at values of the considered
nuisance parameter corresponding to +1&sigma; and -1&sigma; variations, which are constrained from the initial fit. The resulting variation of the of `r` is considered as an impact. Corresponding
command reads as follows:

```sh
combineTool.py -M Impacts --doFits -d ztt_analysis/2018/mutau/workspace.root --robustFit 1 --X-rtd MINIMIZER_analytic --X-rtd FITTER_DYN_STEP --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --setParameterRanges r=0.5,1.5:tauh_id=0.5,1.5 -v1  --setParameters r=1.0,tauh_id=1.0 -m 125 --parallel 5
```

After these calculations are finished, the results are collected into a .json file:

```sh
combineTool.py -M Impacts -d ztt_analysis/2018/mutau/workspace.root -m 125 -o impacts.json
```

Finally, an impact plot is obtained by the following command:

```sh
plotImpacts.py -i impacts.json -o impacts
```

After having produced the plot, let us try to interpret it:

+ The leftmost column the names of
nuisance parameters, ordered by their impact on the parameter `r`.
+ The middle column summarizes the pulls and constraints on the nuisance parameters. The pulls are illustrated by black dots and represent the variation of the central value of the parameter relative
to the nominal value of the uncertainty, before the fit was performed. The constraints are visualized by error bars added to the dots and represent the change of the uncertainties after the fit with respect to their values before the fit.
+ The rightmost column shows the impacts of the nuisance parameters on the parameter of interest `r`: +1&sigma; and -1&sigma; variations using the uncertainty values after the fit was performed.
