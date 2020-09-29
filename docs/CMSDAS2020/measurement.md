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
