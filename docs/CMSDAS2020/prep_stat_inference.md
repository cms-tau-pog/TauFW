# 8. Preparations for statistical inference

After having performed the different group tasks of the analysis, it is time to put everything together.
Please create a final flat n-tuples with modified module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py)
containing the following improvements from each group:

+ Variables implemented, which are needed for a refined selection of Z&rarr;&tau;&tau; applied in the plotting script
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py)
+ Additional weights included, needed for corrections
+ Energy scale corrections applied to the &tau;<sub>h</sub> candidate

The nominal set of n-tuples for &mu;&tau;<sub>h</sub> should be supplemented with the e&mu; n-tuples,
and the variations of &tau;<sub>h</sub> energy scale corresponding to the uncertainty estimate.

Based on these n-tuples, you can produce plots and - more important for the statistical inference - histograms
of our main discriminator, the visible mass of the &mu;&tau;<sub>h</sub> (or e&mu;) pair. Please use for that
the selection defined as `signal_region` enriching Z&rarr;&tau;&tau;, and include the weights needed to apply corrections. Also do
not forget to modify the QCD extrapolation factor [`scale`](https://github.com/ArturAkh/TauFW/blob/master/Plotter/plots_and_histograms_CMSDAS2020.py#L126) according
to your measurement of that factor.

For the systematic variations of the &tau;<sub>h</sub> energy scale in the &mu;&tau;<sub>h</sub> final state, you can also create histograms for the processes affected
by it, for example `TopT`, `EWKT`, `ZTT`, but with the [`tag`](../../Plotter/plots_and_histograms_CMSDAS2020.py#L149) 
modified to `_tauh_esDown` for the downvard variation of the energy scale, and `_tauh_esUp` for the upward variation.
Then, modify the naming of the histograms as follows in the corresponding lines:

```python
    # ...
    for stack, variable in stacks.iteritems():
      outhists.cd(selection.filename)
      for h in stack.hists:
        h.Write(h.GetName().replace("QCD_","QCD") + tag,R.TH1.kOverwrite) # adding tag to the name for es variations in addition
    # ...
```

In that way, your output file should contain histograms like `signal_region/m_vis_ZTT_tauh_esDown`, which are then accessed by
CombineHarvester to create systematic variations.

Assuming, that you have different channel names for the nominal n-tuples, and the corresponding scale variations, the histogram output
files should also have different names. You can put them together with `hadd` to have everything in one file:

```sh
cd $CMSSW_BASE/src/TauFW/Plotter/
hadd mutau.root hists/2018/mutau*.root
```

Feel free also to use your own setup of [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) and
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py), with a possible additional selection

```python
signal_region = "q_1*q_2<0 && pt_1 > 29 && pt_2 > 20 && iso_1 < 0.15 && (decayMode_2 < 5 || decayMode_2 > 7) && id_2 >= 31 && anti_mu_2 == 15"
```
In that way, you can get familiar with the statistical inference procedure, using your own histograms, without having to wait for the final set of n-tuples.

After having prepared the input histograms, the software set for statistical inference consisting of [CombinedLimit](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit),
[CombineHarvester](https://github.com/cms-analysis/CombineHarvester), and [CMSDAS2020TauLong](https://github.com/ArturAkh/CMSDAS2020TauLong) can be used
to obtain the results. The usual procedure within this framework consists of three main steps:

+ Creation of datacards and associated histogram inputs, handled by the script [construct_datacards.py](https://github.com/ArturAkh/CMSDAS2020TauLong/blob/master/scripts/construct_datacards.py).
+ Translation of the datacards into a RooWorkspace, using the `combineTool.py -M T2W` method.
+ Performing calculations to obtain results with a suite of different CombineHarvester commands.

The first two steps will be discussed in detail within this section, while the last step will be covered by section [9](measurement.md).
