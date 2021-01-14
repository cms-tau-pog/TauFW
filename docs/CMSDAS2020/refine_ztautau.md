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

### General aspects

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
[decay modes](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L124) should be selected,
and the working point of the [discriminator against jets](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L127), stored as `id_2`, should
be chosen stricter. To get a feeling about the right choice of the working point, have a look at the distribution of the
[discriminator score](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L190), stored as `iso_2`, in a control plot.

Electrons and muons, corresponding to exactly one reconstructed charged object, usually mimic the &tau;<sub>h</sub> decay modes with one charged hadron. Dedicated
[discriminators against leptons](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L127), stored as `anti_e_2` and `anti_mu_2`,
were designed to reduce the contamination by leptons
misidentified as &tau;<sub>h</sub> candidates. To check this effect, have a look at the distribution of the decay mode, stored as `decayMode_2`, of the selected
&tau;<sub>h</sub> candidate in a control plot.

After having understood, how a reconstructed &mu;&tau;<sub>h</sub> pair can be composed in general, let us now focus on individual contributions to this final state.

### tt&#773; pair

Let us first consider the decay chain of the [top quark pair](https://pdg.lbl.gov/2020/reviews/rpp2020-rev-top-quark.pdf).
At first, the tt&#773; pair decays with a probability of 1 to a pair of bottom quarks and a pair of W bosons:

tt&#773;&rarr;bW<sup>&plus;</sup>b&#773;W<sup>&minus;</sup>

The subsequent decay of the W bosons defines, how the tt&#773; pair production process would contribute to the &mu;&tau;<sub>h</sub> final state:

* A genuine &mu;&tau;<sub>h</sub> pair is created, if each of the W bosons decay into a &tau; lepton and a &tau; neutrino, and the two &tau; leptons according to the considered
final state.
* Since the two W bosons decay independently from each other, the muon could also come directly from the W boson decay, while the W boson is still decaying as in the case above.
* Furthermore, the &tau;<sub>h</sub> candidate may also result from misidentified signatures from muons, electrons and jets, the latter resulting from a hadronic W boson
decay.
* Additional jets can also contribute with a muon or a &tau;<sub>h</sub> candidate, coming from quark or gluon emissions from parton showers or contributions
from higher orders in QCD
* Other possibilities with smaller probability also exist, which we will not discuss in detail.

In summary, the tt&#773; process can contribute to all types of &mu;&tau;<sub>h</sub> pairs discussed in the paragraph with general aspects.

An obvious quantity derived from reconstructed objects, which can be used to distinguish tt&#773; background from Z&rarr;&tau;&tau; signal is the number of b-tagged
jets in the events. In case of tt&#773; the value is expected to be centered around 2, whereas it should be mostly at 0 for Z&rarr;&tau;&tau;.

Another more sophisticated quantity, in particular very suitable to reduce tt&#773; background in the e&mu; but also in the &mu;&tau;<sub>h</sub> final state,
is the D<sub>&zeta;</sub> variable,
which can be considered as a measure whether the invariant system of neutrinos is moving roughly into the same or opposite direction as the invariant system of visible
final state particles, which correspond to the &mu;&tau;<sub>h</sub> or the e&mu; pair.

Have a look at control plots of these variables, but also at others to define selection criteria to reduce tt&#773; background.

### W + jets with a charged lepton in final state

Another background, in particular important for the &mu;&tau;<sub>h</sub> final state, is the production of a W boson, accompanied by jets from emission of gluons or quarks.
For a leptonic decay of the W boson, the most probable constellation of a &mu;&tau;<sub>h</sub> pair is a muon coming directly from a W boson decay, and a jet with
a signature misidentified as a &tau;<sub>h</sub> candidate.

This means, that not the &mu;&tau;<sub>h</sub> pair corresponds to a resonance, but the invariant system of the muon and its neutrino. This can be exploited
to distinguish the W + jets background from Z&rarr;&tau;&tau;, if we get the best possible estimate for the mass of this invariant system. Since we only know
the MET as an estimate for the neutrino momentum, the best mass estimate is the **transverse** mass of the invariant system
of the muon and the MET vector.

If considering the transverse mass, you would expect a peak at about 80 GeV for the W + jets in its distribution, whereas for the Z&rarr;&tau;&tau;, the involved neutrinos
do not build a resonance with the muon alone, such that you would expect a peak at 0 GeV. For this variable, a good resolution is essential, such that it would be good
to compare the transverse mass computed with PF MET with the one computed with PUPPI MET.

A similar effect can also be achieved by making use of the D<sub>&zeta;</sub> variable, so have a look at it to separate W + jets from Z&rarr;&tau;&tau;.

Another obvious quantity to reduce the W + jets contribution is the &tau;<sub>h</sub> discriminator against jets.

Also here, you are advised to have a look at the control plots of these quantities to define appropriate selection criteria.

### Drell-Yan with charged leptons in final state

The Drell-Yan production of the Z boson, which decays into a pair of charged leptons, has the following possibilities to create a &mu;&tau;<sub>h</sub> pair:

* The Z boson can decay in two &tau; leptons, which decay independently from each other according to the considered final state, creating in such a way a genuine
 &mu;&tau;<sub>h</sub> pair. This would correspond to our Z&rarr;&tau;&tau; signal in the &mu;&tau;<sub>h</sub> final state.
* The Z boson decay into a pair of muons, such that one of them must be misidentified as a &tau;<sub>h</sub> candidate to enter the &mu;&tau;<sub>h</sub> final state.
* Additional jets from gluon or quark emissions, which may accompany the Z boson, can create signatures, which are misidentified as &tau; candidates.
* Other minor contributions due to misidentified objects, which we will not discuss in detail.

In summary, only the Z&rarr;&mu;&mu; background plays a more important role and needs to be distinguished from Z&rarr;&tau;&tau;.

One possibility is to have a look
at the visible mass of the &mu;&tau;<sub>h</sub> pair. In case of Z&rarr;&mu;&mu; process, the &tau;<sub>h</sub> candidate is a misidentified muon, and the contribution
should peak at 90 GeV. In contrast to that, the peak of Z&rarr;&tau;&tau; is shifted to lower values, since neutrinos are involved in the Z boson decay.

The usage of the &tau;<sub>h</sub> discriminator against muons should also help to reduce the amount of Z&rarr;&mu;&mu; background.

### Diboson and single top

These two minor contributions, with the production of two bosons (WW, WZ, or ZZ) or a production of a single top quark can contribute to each type of the
&mu;&tau;<sub>h</sub> pair, and are mostly relevant for the e&mu; final state.
Although minor, these backgrounds appear mostly over the full range of considered variables, such that
it might turn out to be not straight-forward to think of a proper selection to reduce this background effectively.

### QCD multijet background

The remaining background estimated in a data-driven way as explained in section [4](norm_and_corr_exp.md#data-driven-estimation-of-qcd-multijet-background), covers all
processes related to production of jets through QCD interactions. The muon from this contribution would be most probably not very isolated, whereas the &tau;<sub>h</sub>
candidate will be a misidentified jet signature. Therefore, have a look at control plots of isolation related variables to get a feeling about a proper selection to reduce
QCD multijet background.

