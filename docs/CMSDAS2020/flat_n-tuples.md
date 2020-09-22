# 4. Creating flat n-tuples

After the NanoAOD samples are preselected as described in the [previous section](preselection.md), you can create flat n-tuples based on these samples
with faster turn-around cycles, than using original NanoAOD as input.

This section is meant as an introduction to the way analysis modules in TauFW can be setup to create flat n-tuples, based on the example for &mu;&tau;<sub>h</sub>,
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py). You can use this example as a starting point for the further analysis in &mu;&tau;<sub>h</sub>, but also
for other final states with corresponding adaptions.

If your TauFW configuration still corresponds to the preselection setup (check with `pico.py list`), then please change it to be able to run on top preselected NanoAOD samples.
For &mu;&tau;<sub>h</sub>, you can follow the instructions from section [2](configuration.md#configuration-done-once-per-desired-change) to change the settings,
including an increase of the number of processed files by default.

## Purpose of flat n-tuples

In contrast to NanoAOD samples, flat n-tuples are not meant to be of general purpose, and should not contain vectors of quantities.
This means, the only quantities stored in the TTree of a flat n-tuple are usually
floats, integers, booleans, and characters, and they should comprise only those being of particular need for the analysis, for example to:

+ check and improve agreement between data and expectation,
+ refine signal selection to enrich the signal,
+ define sideband regions for data-driven background estimation,
+ define analysis categories,
+ and compute high-level quantities with high discriminating power.

Among these highly discriminating quantities, you could find for example mass related variables of the &tau;&tau; system,
or MVA based discriminators for (multi-)classification of signals and backgrounds.

After having clarified the purpose of flat n-tuples in the context of this exercise, let us have a closer look at the corresponding TauFW module.

## Structure of an analysis module

The analysis module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) is based on the [nanoAOD-tools](https://github.com/cms-nanoAOD/nanoAOD-tools) software.
The module is required to have the following methods:

+ `__init__(self,fname,**kwargs)`: Basic initialization of the module before starting the event loop. Here, the output file can be defined for example.
+ `beginJob(self)`: Instructions to be done at the beginning of the event loop, like the setup of a cutflow histogram and an output tree.
+ `endJob(self)`: Instructions after the configured event loop is finished, like storing everything in the output file and closing it.
+ `analyze(self, event)`: This is the main function of the analysis module, where the selection of physics objects and events is performed.

After this small overview over analysis module, let us now try to better understand the current selection implemented in the module, and what is
required from you to extend this selection in the context of the exercise.

## Initial analysis selection

The first step of the selection is to apply global event filters, like the requirement of a fired trigger.

After that, collections of different physics objects are created. In case of the &mu;&tau;<sub>h</sub> final state, the main collections are created for muons and &tau;<sub>h</sub> candidates.
These two collections are used to create a &tau;&tau; pair candidate.

However, additional physics objects could and should be considered to refine the selection of the analysis.

The collection of electrons can used together with the collection of muons to ensure, that the &mu;&tau;<sub>h</sub> final state does not overlap with other final states of the analysis, and to suppress
contributions from Z&rarr;&mu;&mu; or Z&rarr;ee events.

It is also good to have a look at jets and b-tagged jets to figure out, whether they can be used to enrich Z&rarr;&tau;&tau;, while suppressing backgrounds at the same time.

Finally, another important physics object is the missing transverse energy, called also missing E<sub>T</sub>, or simply MET. This physics object can be used to construct several
high-level quantities to distinguish Z&rarr;&tau;&tau; from W + jets and from tt&#773;.

The selection given in the [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) repository is essentially the one you have seen for [preselection](preselection.md)
of the &mu;&tau;<sub>h</sub> final state. The only more restrictive requirement is the separation in &Delta;R between the muon and the &tau;<sub>h</sub> candidate.

Therefore, several TODO&apos;s are defined for you to extend the inital selection to create flat n-tuples, partly also to be covered in section [6](refine_ztautau.md).

In the course of the exercise, you will come back often to this module to refine the selection further and further. That is also the reason, why it is good to have fast turn-arounds with this step.

But let us first define the tasks to be done for this section, which have the aim to make you familiar with nanoAOD content and to allow you to extend the content of the flat n-tuple outputs :).

## Tasks of this section

To avoid ambiguities, the tasks for this section are marked with `TODO section 3` in [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py).

To make these tasks easier for yourself, you should get familiar with quantities stored in the NanoAOD files, by looking at preselected or original samples on one hand:

```sh
# Hopefully already known commands for you from previous section ;)
root -l <original>.root -e "Events->GetListOfLeaves()->Print(); exit(0)" | sort -V > original_content.txt
root -l <preselected>.root -e "Events->GetListOfLeaves()->Print(); exit(0)" | sort -V > preselected_content.txt
```

and having a look at the [NanoAOD documentation](https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html) of these samples on the other hand to understand how
to interpret the quantities.

### Task 1: electrons and muons for event veto

Define collections of muons and electrons used to veto events with additional muons and electrons. The selection for the leptons should be equal or looser than the
the signal selection. Therefore, if other final states than &mu;&tau;<sub>h</sub> are anticipated to be done by some of you, discuss and agree on similar signal and veto selections across
all considered final states.

An example for possible veto selections:

+ muons: the same as signal muons, but with a looser p<sub>T</sub> threshold, p<sub>T</sub> > 15.0 GeV.
  + Align this selection with signal and veto selections for muons in other final states appropriately, if necessary.
  + Define the requirement to reject events with additional muons. How would it look like in the code explicitly?
+ electrons: p<sub>T</sub> > 15.0 GeV, loose WP of MVA-based ID (Fall17 training without using isolation), custom isolation cut on PF based isolation using all PF candidates.
  + Align also this selection with signal and veto selections for electrons in other final states appropriately, if necessary.
  + How is the requirement to reject events with additional electrons defined in the code?
