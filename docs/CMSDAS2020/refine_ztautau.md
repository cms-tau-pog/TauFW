# 6. Refining Z&rarr;&tau;&tau; selection

All previously discussed steps allow to create **control plots** with the script
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py) of various quantities, which you have included into the analysis module
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py).

The main topic of this section will be to have a closer look at these control plots, to choose quantities, which allow to disentangle one or more backgrounds from
our Z&rarr;&tau;&tau; signal, and to define selection criteria, which reject most of the backgrounds while keeping most of the signal.

## Backgrounds contributing to the analysis

On of the first tasks to be done in the context of defining a good Z&rarr;&tau;&tau; selection, is to understand which backgrounds contribute to it, and which specific
features do they have in the kinematic phase space of the total collision event.
