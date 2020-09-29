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
+ `-n .r_with_tauID_fixed`: Add a postfix to the name of the output files.
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
