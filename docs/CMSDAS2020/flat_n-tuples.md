# 4. Creating flat n-tuples

After the NanoAOD samples are preselected as described in the [previous section](preselection.md), you can create flat n-tuples based on these samples
with faster turn-around cycles, than using original NanoAOD as input.

This section is meant as an introduction to the way analysis modules in TauFW can be setup to create flat n-tuples, based on the example for &mu;&tau;<sub>h</sub>,
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py). You can use this example as a starting point for the further analysis in &mu;&tau;<sub>h</sub>, but also
for other final states with corresponding adaptions.

If your TauFW configuration still corresponds to the preselection setup (check with `pico.py list`), then please change it to be able to run on top of preselected NanoAOD samples.
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
of the &mu;&tau;<sub>h</sub> final state. The only more restrictive requirement is the separation
in &Delta;R = (&Delta;&phi;<sup>2</sup> + &Delta;&eta;<sup>2</sup>)<sup>0.5</sup> between the muon and the &tau;<sub>h</sub> candidate.

Therefore, several TODO&apos;s are defined for you to extend the inital selection to create flat n-tuples, partly also to be covered in section [6](refine_ztautau.md).

In the course of the exercise, you will come back often to this module to refine the selection further and further. That is also the reason, why it is good to have fast turn-arounds with this step.

But let us first define the tasks to be done for this section, which have the aim to make you familiar with NanoAOD content and to allow you to extend the content of the flat n-tuple outputs :).

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

To define new variables, let you inspire by already existing output variables, such as `m_vis`, `decayMode_2` or `id_2`.

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

### Task 2 (optional): improve the selection of the &mu;&tau;<sub>h</sub> pair

This is an optional task, not necessarily needed to achieve proper results. However, those of you interested in the details of the more sophisticated
[&tau;&tau; pair selection algorithm](https://twiki.cern.ch/twiki/bin/view/CMS/HiggsToTauTauWorking2017#Pair_Selection_Algorithm) may tackle this task and share
the result with others, once concluded.

The main idea of this &tau;&tau; pair selection algorithm is to select the most *isolated* pair, not the one composed from physics objects with highest p<sub>T</sub>.

Some tips to understand the algorithm better:

+ The isolation values are considered to be the same, if they match up to a certain digit after comma, therefore you would need round the numbers appropriately before comparing them.
+ Isolation of muons and electrons is given relative to p<sub>T</sub> as energy sums. Therefore, the *smaller* the value, the more isolated is the physics object.
+ In contrast to that, the measure for isolation of a &tau;<sub>h</sub> candidate is its DNN based discriminator against jets. Here, the *higher* the value, the more isolated is the
&tau;<sub>h</sub> candidate.
+ In [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py), the isolation measures for the muon and the &tau;<sub>h</sub> candidate are already chosen in the right
way and written out as `iso_1` and `iso_2`, respectively.

### Task 3: jet selection and variables

Jets are not directly used as signal objects, however, they can be quite useful to enrich Z&rarr;&tau;&tau; or to define signal categories and control regions regions for backgrounds.

For this reason, you are asked to selected good jets and store quantities related to them. The selection can be performed in three main steps:

+ Basic selection of jets with:
  + p<sub>T</sub> > 20.0 GeV, |&eta;| < 4.7,
  + passing loose WP of the pileup jet ID, tight WP of standard jet ID,
  + not overlapping with the muon or &tau;<sub>h</sub> candidate of the signal pair, having &Delta;R(&mu; or &tau;<sub>h</sub>, jet) &ge; 0.5 
+ p<sub>T</sub> > 30.0 GeV jets:
  + Starting from basic jets, keep only those with p<sub>T</sub> > 30.0 GeV to suppress pileup jets further.
  + Store as output quantities the number of the resulting jets, as well as p<sub>T</sub> and &eta; of the jets leading and subleading in p<sub>T</sub>
+ b-tagged jets:
  + Starting from basic jets, keep only those with |&eta;| < 2.5 and require [medium WP](https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X#Supported_Algorithms_and_Operati)
of the DeepFlavour b+bb+lepb discriminator. Since the b-tagged jets are within the tracker acceptance, they may have lower p<sub>T</sub> because the existence of charged tracks allows for
a better discrimination of jets from pileup.
  + Store as output quantities the number of b-tagged jets, as well as p<sub>T</sub> and &eta; of the b-tagged jets leading and subleading in p<sub>T</sub>

### Task 4: MET choice and variables

Also the MET is a useful variable to construct high-level variables to enrich Z&rarr;&tau;&tau; or to define signal categories and control regions.

In the current NanoAOD format, there are various definitions of MET available. The most used ones - as you can see discussed in the corresponding
[MET paper](https://doi.org/10.1088/1748-0221/14/07/P07004) - are the PF-based MET (stored simply as `MET` in NanoAOD) and the PUPPI MET (stored as `PuppiMET` in NanoAOD). Both
are corrected for pileup contributions, the latter with the [**P**ile**u**p **p**er **P**article **I**dentification](https://doi.org/10.1007/JHEP10(2014)059) method.

To be able to compare these two definitions in terms of mean, resolution and data/expectation agreement, please store p<sub>T</sub>, &phi;, and &Sigma;E<sub>T</sub> for both
versions of the MET in different variables. As soon as you start to implement variables using MET in their computation, please also keep in mind to create two versions of the
computed variable.

### Task 5: Additional (high-level) variables

After all physics objects of interest are selected, variables can be computed and stored, which are computed from multiple input quantities, or are global properties of an event.
Please implement at least the following list of variables:

+ visible p<sub>T</sub> of the Z boson candidate. Tip: have a look at the `m_vis` computation.
+ best-estimate for the full p<sub>T</sub> of the Z boson candidate, including neutrinos. What should added to the p<sub>T</sub> vector of the &mu;&tau;<sub>h</sub> pair?
+ transverse mass for the system of the muon and MET, m<T>(&mu; MET). A definition is given for example in [doi:10.1140/epjc/s10052-018-6146-9](https://doi.org/10.1140/epjc/s10052-018-6146-9),
equation (3). Please check, whether the value for &Delta;&phi; is in the [-&pi;,+&pi;] interval. If not, does this have an influence on the result from applying Sine or Cosine functions on it?
+ D<sub>&zeta;</sub> variable, also defined in [doi:10.1140/epjc/s10052-018-6146-9](https://doi.org/10.1140/epjc/s10052-018-6146-9), formula (4) and Figure 1. The difference is that it
is considered for the e&mu; final state there, but could be used also for other &tau;&tau; final states.
+ Separation in &Delta;R between the muon and the &tau;<sub>h</sub> candidate. Here you can use the functions defined for the
[`Object`](https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/datamodel.py#L49-L89) class defined in NanoAOD,
as already used in [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py). Please note, that in this case, the interval of &Delta;&phi; is required to be [-&pi;,+&pi;].
+ Pileup density &rho;, computed from all PF Candidates.
+ Number of reconstructed primary vertices.
+ for MC only: number of **true** pileup interactions. Please use the `if self.ismc:` case to fill this variable to distinguish from data, where this quantity is not available in NanoAOD.

## Producing local n-tuple output and testing the code

In the process of your adaptions to the analysis module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py), you are adviced to test your implementation frequently
after each small step you have done. This, you do best locally, using a limited number of events. Furthermore, it is always a good idea to do it for one simulated sample and one data sample separately,
in case you are working on simulation-specific implementations, for example.

A possible local test command using preselected NanoAOD samples could look like:

```sh
pico.py run -c mutau -y 2018 -s DY
```

Since the already preselected samples for &mu;&tau;<sub>h</sub> are quite small, you do not need to specify the number of events to be processed with `-m`. Furthermore,
for local tests with `pico.py run`, only one input file is user per default. The input file is chosen from the list of files for the Drell-Yan sample, which is chosen via `-s DY`.

A test for a data sample would then look similar:

```sh
pico.py run -c mutau -y 2018 -s SingleMuon
```

Having these commands at hand, test always extensions of the module, and have a look at the local outputs produced as `${CMSSW_BASE}/src/TauFW/PicoProducer/output/pico_*.root` by checking
the quantities stored in these files, and their values. Are these as you have expected?

There are several possibilities to check your local outputs, discussed in the following.

First step could be to check, whether the desired quantity is booked at all as a TLeaf in the TTree `tree`. By now, you should know the appropriate command, since it appeared already twice
in the course of this exercise :) Just scroll up a bit ;).

Next you can check in a very convenient way the values for some of the processed events in the ROOT shell:

```sh
root -l <path-to-pico-output>.root
# in the ROOT shell
root [0]
...
root [1] tree->Scan("m_vis:pt_1:decayMode_2")

```

Furthermore, you can test different cuts:

root -l <path-to-pico-output>.root
# in the ROOT shell
root [0]
...
root [1] tree->GetEntries("m_vis > 90.0")
...
root [2] tree->GetEntries("pt_1 < 20.0")

```

The best way to check your outputs is of course having a look at the various distributions of the stored quantities. Provided, that you have ROOT installed on the work system at your home institution,
you can copy the output file(s) there and have a look at the file using a graphical interface of ROOT.

First, get the absolute path of the output:

```sh
readlink -f <path-to-pico-output>.root
```

Then, on the work system at your home institution, copy the file from CERN `lxplus` to you. The following command should work on unix-based operating systems:

```sh
scp <cern-username>@lxplus.cern.ch:<absolute-path-to-pico-output>.root .
```

Then you can open the file at your home institution and start the TBrowser with a graphical interface:

```sh
root -l  <path-to-pico-output>.root
# in the ROOT shell
root [0]
...
root [1] TBrowser b
```

Then, you can relatively fast click through the structure of the opened file to get familiar with it.

You can for example plot the `cutflow` histogram to check, whether the tracked cuts are affecting the event selection. Besides that, you can get the distributions of the quantities stored in `tree`
by (double-)clicking on the corresponding leaves.

Furthermore, if you like to see the values of a quantity in a specified range, then, with the TBrowser still open, use the ROOT shell:

```sh
# in the ROOT shell, with TBrowser open
root [2] tree->Draw("m_vis","m_vis >=70 && m_vis < 110")
```

Then the plot in canvas of TBrowser will be updated accordingly.
