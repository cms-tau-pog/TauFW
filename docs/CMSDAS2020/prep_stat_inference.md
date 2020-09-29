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
the selection defined as `signal_region` enriching Z&rarr;&tau;&tau;.

For the systematic variations of the &tau;<sub>h</sub> energy scale, you can also create histograms for the processes affected
by it, for example `TopT`, `EWKT`, `ZTT`, but with the [`tag`](../../Plotter/plots_and_histograms_CMSDAS2020.py#L149) 
modified to `_tauh_esDown` for the downvard variation of the energy scale, and `_tauh_esUp` for the upward variation.

In that way, your output file should contain histograms like `signal_region/m_vis_ZTT_tauh_esDown`, which are then accessed by
to create systematic variations.
