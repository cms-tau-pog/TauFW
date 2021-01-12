# 6. Refining Z&rarr;&tau;&tau; selection

All previously discussed steps allow to create **control plots** with the script
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py) of various quantities, which you have included into the analysis module
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py).

The main topic of this section will be to have a closer look at these control plots, to choose quantities, which allow to disentangle one or more backgrounds from
our Z&rarr;&tau;&tau; signal, and to define selection criteria, which reject most of the backgrounds while keeping most of the signal.

## Backgrounds contributing to the analysis

One of the first tasks to be done in the context of defining a good Z&rarr;&tau;&tau; selection, is to understand which backgrounds contribute to it, and which specific
features do they have in the kinematic phase space of the total collision event.

Let us repeat, what we have already discussed in section [3](preselection.md#processes-contributing-to-a-z%CF%84%CF%84-final-state) about expected contributions and discuss
in more detail, what makes the backgrounds unique and distinguishable from the Z&rarr;&tau;&tau; signal.

A &mu;&tau;<sub>h</sub> pair can result from different physical processes, either with a pair correctly reconstructed,
or from particles or signatures, which are misidentified as such a pair.

A muon signature is very unlikely to result from particles other than muons, being charged hadrons
in most cases, which punch through all detector layers up to the first muon chamber. Therefore, it is rather accurate to assume, that the muon in the selected
&mu;&tau;<sub>h</sub> pair is a true muon, which is rather isolated, or created within a jet. To get a feeling, how isolated the muon should be to restrict the
selection to the Z&rarr;&tau;&tau; signal, you can have a look at the control plot of distribution of the muon
[isolation sum](https://github.com/ArturAkh/TauFW/blob/master/PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L182), `iso_1`.

In contrast to that, &tau;<sub>h</sub> candidates are difficult objects reconstructed from jet constituents. Therefore, a reconstructed &tau;<sub>h</sub> candidate can
correspond to a real hadronic decay of a &tau; lepton, or to a jet, electron, or muon misidentified as a &tau;<sub>h</sub> candidate.

Jets can produce a &tau;<sub>h</sub> signature for all decay modes of the &tau;<sub>h</sub> candidate, in particular those with 2 charged hadrons, where a third
charged hadron was missed by the reconstruction. Such &tau;<sub>h</sub> decay modes are strongly contaminated by misidentified signatures. To reduce the contamination
by jets misidentified as &tau;<sub>h</sub> candidates, proper
[decay modes](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L124), stored as `decayMode_2`, should be selected,
and the working point of the [discriminator against jets](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L127), stored as `id_2`, should
be chosen stricter. To get a feeling about the right choice of the working point, have a look at the distribution of the
[discriminator score](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L190), stored as `iso_2`, in a control plot.

Electrons and muons, corresponding to exactly one reconstructed charged object, usually mimic the &tau;<sub>h</sub> decay modes with one charged hadron. Dedicated
[discriminators against leptons](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L127), stored as `anti_e_2` and `anti_mu_2`,
were designed to reduce the contamination by leptons
misidentified as &tau;<sub>h</sub> candidates. To check this effect, have a look at the distribution of the decay mode of the selected
&tau;<sub>h</sub> candidate in a control plot.
