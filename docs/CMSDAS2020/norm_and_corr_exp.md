# 5. Normalizing and correcting expected contributions

After having produced all flat n-tuples you need, as discussed in section [4](flat_n-tuples.md), you are ready to create your first histograms and plots
of the variables stored in the flat n-tuples.

The topics discussed in this section are crucial for understanding the data you are analysing, and to understand
the impact of improvements and corrections to be applied to step by step for a better data/expectation agreement.

Expect to play around most of your time with the tools introduced in this section, as well as with the analysis module
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py), which you will need to adapt step by step and start reproducing the outputs :).

The main script for the tasks considered and discussed within this section is [plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py)

It is constructed to produce nice plots of distributions of various quantities, like the visible mass of the &tau;&tau; system, m<sub>vis</sub>, and to create histograms
for further processing with CombineHarvester.

Let us first have a look at its general structure:

+ `getsampleset(...)` method: In this function, the diffent contributions are declared, normalized to the collected data and corrected.
+ `plot(...)` method: Here, the plots and histogram output files are created. During this process, also the various selection conditions and variables are
specified for the plots and histograms. Furthemore, the QCD estimation runs in that method.
+ `main(args)` method: main function used to execute the previous two after having specified the conditions for them appropriately.
+ `if __name__ == "__main__":` section: This actually the part, which is executed, when you run the script. Usually, it is used to parse arguments and pass them to the `main` function.


To run the plot and histogram production script, please use the following commands, depending on the way you have produced your flat n-tuples:

```sh
# Move to Plotter directory
cd ${CMSSW_BASE/src}/TauFW/Plotter/

# In case you obtained your flat n-tuples from batch submission
./plots_and_histograms_CMSDAS2020.py -c mutau -y 2018

# In case you produced your flat n-tuples locally (via parallelized script, for example). Here, you need to specify a custom pattern for your output files
./plots_and_histograms_CMSDAS2020.py -c mutau -y 2018 --picopattern "${CMSSW_BASE}/src/TauFW/PicoProducer/output/pico_\$CHANNEL_\$ERA_\$SAMPLE.root"
```

If everything works out properly, you should obtain plots in the `${CMSSW_BASE}/src/TauFW/Plotter/plots/2018/` folder and a histogram in the `${CMSSW_BASE}/src/TauFW/Plotter/hists/2018/` folder.

To have a look a one specific plot in `.pdf` format, you can use `evince` (via X11 forwarding, directly on CERN `lxplus`):

```sh
evince ${CMSSW_BASE}/src/TauFW/Plotter/plots/2018/m_vis_mutau-inclusive-2018.pdf
```

Alternatively, you can also use `eog` to have a look at multiple plots in `.png` format:

```sh
eog ${CMSSW_BASE}/src/TauFW/Plotter/plots/2018/*.png
```

## Definition of contributions from simulation and data

Now let us have a closer look at what is done in the `getsampleset(...)` method.

The first thing that needs to be done is a proper scaling of simulated contributions to the amount of data collected.

The formula for the expected number of events in a dataset for a specific process *P* is N<sub>data</sub> = L<sub>int</sub> &middot; &sigma;<sub>*P*</sub>  &middot; &epsilon; with

+ integrated luminosity L<sub>int</sub> = 59.7 fb<sup>-1</sup> for 2018 data,
+ the cross-section of the process *P* &sigma;<sub>*P*</sub>,
+ and the acceptance and selection efficiency &epsilon;.

In case of consistent selection in data and simulation, the efficiency &epsilon; should be similar up to residual differences mitigated by corresponding event-by-event scale-factors.

Omitting these corrections for the moment, to arrive at the right number of events, the multiplicative factor L<sub>int</sub> &middot; &sigma;<sub>*P*</sub> is needed, provided that you
know the probability distribution of a sample to obtain a single event.

Now, how to arrive at this probability distribution (e.g. in the visible mass of the &mu;&tau;<sub>h</sub> pair)? Simply by dividing by the number of events in a simulated dataset.
There is one important peculiarity: what is meant, is the *effective* number of events N<sub>eff</sub>, and it different from the actually simulated number of events, N<sub>sim</sub>,
if negative generator weights are present in the dataset.

In samples simulated with such generators, usually simulations at least at NLO QCD precision, negative events are used to account for interference effects. This is done by assigning to each event
a weight with the same absolute value - often just 1.0 or the generator cross-section - but a different sign. That means:

N<sub>eff</sub> = N(+) - N(-) = N<sub>sim</sub> - 2 &middot; N(-) = N<sub>sim</sub> &middot; ( 1 - 2 &middot; f ), with f being the fraction of negative events.

This explains the setup of different samples in [plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py), e.g. for the Drell-Yan production:

```python
    # GROUP NAME                     TITLE                 XSEC [pb]      effective NEVENTS = simulated NEVENTS * ( 1  - 2 * negative fraction)
    # ...
    ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",       6077.22,       {"nevts" : 100194597 * (1.0 - 2 * negative_fractions["DYJetsToLL_M-50"])}),

```

If you execute the plotting script with an increased verbosity:

```sh
./plots_and_histograms_CMSDAS2020.py -c mutau -y 2018 --verbose 2
```

you will see the total normalization factor:

```sh
>>> Sample.normalize: Normalize 'DYJetsToLL_M-50' sample to lumi*xsec*1000/sumw = 59.7*6077.2*1000/1.0011e+08 = 3.624!
```

Since the cross-sections are given in [pb] and the integrated luminosity in [fb<sup>-1</sup>], an additional factor of 1000 is needed.

Now what about the generator weights? Since we anyhow normalize to an inclusive cross-section with a higher precision than the one computed with the generator used for simulation,
the cross-section contained in the generator weight should be devided out:

```python
weight = "genWeight/abs(genWeight)"
```

To arrive at the proper probability distribution for one event, it is important to apply this normalized generator weight on an event-by-ebent basis.

The remaining question for simulated samples is, where to get the information on the cross-sections, the number of simulated events, and the fraction of negative events.

In case of cross-sections, several Twiki pages can be consulted:

+ SM processes like Drell-Yan, Diboson, W + Jets, etc.: [StandardModelCrossSectionsat13TeV](https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV)
+ TTbar production: [TtbarNNLO](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO#Top_quark_pair_cross_sections_at)
+ Single top production: [SingleTopSigma](https://twiki.cern.ch/twiki/bin/viewauth/CMS/SingleTopSigma)
+ Higgs boson production: [LHCHXSWG](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHXSWG#Higgs_cross_sections_and_decay_b)

In some cases, the cross-section is not known for a particular phase-space simulated by the generator. The most precise possibility is to use the
[GenXSecAnalyzer](https://twiki.cern.ch/twiki/bin/viewauth/CMS/HowToGenXSecAnalyzer) in this case. Sometimes, the cross-sections are also given in [XSDB](https://cms-gen-dev.cern.ch/xsdb/),
however, you need to be sure to select the right `DAS` name for the sample you search for. Sometimes, the info is not available because the datbase is not updated accordingly.

To find out which numbers of simulated events are needed, you can use the `dasgoclient` as discussed in section [3](preselection.md). Alternatively you can find
this information also at [McM](https://cms-pdmv.cern.ch/mcm/). Go to that page, click on the "Request" button and put the DAS name of the dataset into the "Output Dataset" field.
In the "Select View", you can activate the information, which you would like to see. For the number of simulated events, please activate "Total events".

The best way to determine the negative fraction of events is to compute it yourself from the original, **not preselected** NanoAOD samples. To do this, you would need to loop through the files
and access the TTree `Events` for each file. For each `Events` tree, have a look at the number of events with negative generator weights, and the total number of simulated events.

At first, find out with dasgoclient, which files a sample has, e.g.:

```sh
dasgoclient -query="file dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM" > DYJetsToLL_M-50_files.txt
```

Then, you can use the following python code snippet to compute the fraction of negative events for this dataset:

```python
#! /usr/bin/env python
import ROOT as r
r.gROOT.SetBatch()
xrdserver = "root://cms-xrd-global.cern.ch/"
    
filepaths = [xrdserver + p.strip() for p in open("DYJetsToLL_M-50_files.txt","r").readlines()]
n_events = 0.0
n_negative_events = 0.0

for p in filepaths:
    f = r.TFile.Open(p)
    print "Processing:",p
    tree = f.Get("Events")
    n_events += float(tree.GetEntries())
    n_negative_events += float(tree.GetEntries("genWeight < 0"))
    f.Close()


print "Number of simulated events:",n_events
print "Fraction of negative events:",n_negative_events/n_events
```

Feel free to make it more automatic to cover all datasets considered in the filelists of the analysis.
But be warned, that this will be rather a slow method, so perhaps use multiprocessing per dataset
and leave it running over night.

Alternatively, you can have at the values stored on [XSDB](https://cms-gen-dev.cern.ch/xsdb/) by searching for the appropriate "process_name" and activating "process_name", "DAS", and "fraction_negative_weight" to check, that it is the right sample and its fraction of negativ events. Since this database is not updated regurarly, it might well be, that this information is outdated and not available for the recent "DAS" names.

Side remark: all the needed numbers for cross-sections, numbers of simulated events, and the fractions of negative events are already integrated into the
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py). The instructions above are for your information and later reference.

In case of data, there are no adaptions to be made. The only thing to be done is the selection of the appropriate sample for the considered final state.
For &mu;&tau;<sub></sub>, the setup look as follows:

```python
# OBSERVED DATA SAMPLES
if 'mutau'  in channel: dataset = "SingleMuon_Run%d?"%year
else:
  LOG.throw(IOError,"Did not recognize channel %r!"%(channel))
datasample = ('Data',dataset) # Data for chosen channel
```

## Joining and splitting distributions

After having defined each contribution, it is often good to summarize multiple contributions into one. For example, since we are not interested in the individual
contributions involving two of the bosons W or Z, but in an inclusive contribution of these processes in the first place.
In the script [plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py), this is achieved with the following line:

```python
sampleset.join('WW', 'WZ', 'ZZ', name='VV'  ) # Diboson
```

On the other hand, we need to distinguish between contributions to the &mu;&tau;<sub>h</sub> final state with a real &tau;<sub>h</sub> candidate from contributions, where the &tau;<sub>h</sub>
is a misidentified muon, electron, or jet. To accomplish this, a splitting of a process can be performed:

```python
GMR = "genmatch_2==5"
GMO = "genmatch_2!=5"
sampleset.split('DY', [('ZTT',GMR),('ZL',GMO)])
```

This splitting is based on generator information, whether the reconstructed &tau;<sub>h</sub> candidate is matched to a real &tau;<sub>h</sub> or not. However, after fixing
your refined signal selection, please have a look, whether all of the splitted contributions are well populated.

As a small, optional task, please have a look at the distribution of quantities `genmatch_1` and `genmatch_2` for the various sameples you have processed to flat n-tuples.
Please have a look at the definition of these variables in the [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) and the
[NanoAOD documentation](https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html).

For the Drell-Yan process, `ZL` is defined as every contribution, where the reconstructed &tau;<sub>h</sub> candidate does not correspond to a real &tau;<sub>h</sub>. The naming `ZL`
indicates, that the Z&rarr;&mu;&mu; process is meant in case of the &mu;&tau;<sub>h</sub> final state, assuming that this is the major contribution to `ZL`. Is this justified?
What is the major contribution to other processes with `genmatch_2!=5`?

## Data-driven estimation of QCD multijet background

Until now, we have discussed, how to define contributions for simulated samples and collected data. However, often also data-driven techniques are used to estimate background contributions
from side-band regions.

In the context of this exercise, you will get familiar with a simple way to estimate the QCD multijet background from data.

The main idea, also in general for other methods, is to go into a side-band region - also called as control region -  where the considered background should be a major contribution, and more
important, where you are sure not to see any signal you would like to measure.

For QCD multijet background, it is possible to construct this by requiring the &mu;&tau;<sub>h</sub> pair have constituents of the same charge. In contrast to that, our signal - in the context
of our measurement this would be Z&rarr;&tau;&tau; - should consist of pair of a muon and a &tau;<sub>h</sub> candidate with opposite charges.

Therefore the most inclusive signal region is defined by an opposite charge requirement:

```python
inclusive = "(q_1*q_2<0)"
inclusive = inclusive.replace(" ","")
```

The corresponding control region is constructed by inverting this requirement:

```python
inclusive_cr_qcd = inclusive.replace("q_1*q_2<0","q_1*q_2>0") # inverting the opposite-sign requirement of the mutau pair into a same-sign requirment
```

This is also done in the corresponding implementation of the background estimation method [QCD_OSSS.py](../../Plotter/python/methods/QCD_OSSS.py),
which is used in the plotting script [plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py)
after the definition of considered data samples and simulated samples, the selection, and the variables:

```python
stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',scale=1.1,parallel=parallel) # the 'scale' keyword argument - chosen as 1.1 for mutau - 
                                                                                               # is an extrapolation factor for the QCD shape from the same-sign
                                                                                               # to the opposite-sign region
```
In the same-sign control region, all expected simulated contributions are subtracted from data, and the remaining shape is assumed to be QCD.
For the example of the m<sub>vis</sub> distribution, this would look like:

QCD<sup>ss</sup>[m<sub>vis</sub>] = data<sup>ss</sup>[m<sub>vis</sub>] - expected non-QCD<sup>ss</sup>[m<sub>vis</sub>]

Having the QCD distribution in the same-sign region, a rather simple extrapolation to the signal region is done by scaling the shape from the same-sign region
by a certain scale factor:

QCD<sup>os</sup>[m<sub>vis</sub>] = extrapolation factor &middot;  QCD<sup>ss</sup>[m<sub>vis</sub>]

In this way, it is assumed, that the shapes among the two regions - same-sign control region vs. opposite-sign signal region -
are the same, which might turn out to be not true in general. Luckily, for our application in &mu;&tau;<sub>h</sub>, this is a good approximation :)

As you might have noticed, the extrapolation factor is chosen to be `scale=1.1`. Where does this number come from? Again: this needs to be done
in a corresponding control region, having both same-sign and opposite sign events.

A usual choice for that region is created by a relaxed muon isolation requirement. This is also the reason, why we have kept the muon isolation loose
in the analysis module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py):

```python
    #...
    for muon in Collection(event,'Muon'):
      good_muon = muon.mediumId and muon.pfRelIso04_all < 0.5 and abs(muon.eta) < 2.5
    #...
```

Given that the analysis selection in the n-tuple is kept loose, a stricter selection can be applied at the level of the plotting script
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py),
adding additional cut strings to the `selections` list, which contain the muon isolation `iso_1`.

A stricter signal region requirement could be for example `iso_1 < 0.15`, while side-band region with a relaxed muon isolation condition could constructed accordingly
via `iso_1 >= 0.15 && iso_1 < 0.5`. You need to ensure, that the signal region and the side-band region are orthogonal to each other.

The side-band region with relaxed muon isolation requirement can then be separated into an opposite-sign and a same-sign region, and since it is assumed
that both of the regions are signal-depleted, the number of QCD events in both regions can be estimated in the same manner: subtracting all non-QCD contributions
from data and defining the remaining events to come from QCD.

Since we are interested in the first place in a global scale factor, on can (ab)use variables like `q_1` to count events passing the selection of the two regions:

```python
variables = [
   Var('m_vis',  40,  0, 200),
   Var('q_1', 1, -2.0, 2.0), # using the q_1 variable to count events passing a selection
]
```

The measured extrapolation would then be the ratio between the number of QCD events in the opposite-sign side-band region with relaxed muon isolation and the number
of QCD events in the same-sign side-band region with relaxed muon isolation.

Side note: the estimation method [QCD_OSSS.py](../../Plotter/python/methods/QCD_OSSS.py) can also be used to plot contributions in the same-sign region. The method
recognizes, if the same-sign region is passed as the formal opposite-sign signal region, and the QCD shape is estimated automatically without an extrapolation factor,
setting `scale = 1.0`. By construction, the data/expectation ratio for the same-sign region is exactly at 1.

### Group task - data-driven QCD estimation

For those of you, who would like to have a look closer at the data-driven QCD estimation, the task would be to understand the procedure of estimating QCD with the method
above and documenting the procedure with plots and graphics:

+ Describe the method, using a sketch of the different regions needed for the estimation
+ Show the constructed shape estimate of QCD in the same-sign region (with a control plot)
+ Describe the estimation of the extrapolation factor in the side-band region with relaxed muon isolation
+ Quote your estimated number for it and assign an uncertainty, based on the statistical uncertainty of this ratio

## Selection and variables

As indicated already in the discussion about the QCD estimation, selection requirements can also be introduced in the plotting script
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py).

In the process of trying out different cuts, it is more convenient to produce a set of loosely selected n-tuples containing all variables
to be used in the selection, and then trying out different cuts by adding corresponding selection requirement to the list of `selections`:

```python
  # SELECTIONS
  inclusive = "(q_1*q_2<0)"
  inclusive = inclusive.replace(" ","")
  inclusive_cr_qcd = inclusive.replace("q_1*q_2<0","q_1*q_2>0") # inverting the opposite-sign requirement of the mutau pair into a same-sign requirment
  selections = [
    Sel('inclusive',inclusive),
    Sel('inclusive_cr_qcd',inclusive_cr_qcd),
  ]
```

And after having converged on a selection suitable for the Z&rarr;&tau;&tau; cross-section measurement, you may introduce it to the analysis module
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py),
keeping in mind not to reject events needed for example for QCD estimation - so **do not** use the charge requirement `(q_1*q_2<0)` in the analysis module.

Introducing the refined selection to the analysis module would reduce the number of events stored in the flat n-tuples, reducing in turn the run-time of the histogram production.

Besides the extension of the selections to be tested, the list of variables can be filled with quantities avaibale in the n-tuples to be able to
make corresponding histograms and control plots:

```python
  # VARIABLES
  variables = [
     Var('m_vis',  40,  0, 200),
  ]
```

Try to choose for each variable an appropriate binning. To make the plots nicer,
extend the dictionary containing the labels of each stored variable, if necessary. The dictionary is implemented in [string.py](../../Plotter/python/plot/string.py).

## Event-by-event corrections to simulated contributions

Usually, the out-of-the-box agreement between selected data and expected contributions is not good. In the following, we will discuss some of the required
corrections to be applied to simulated events in the context of the Z&rarr;&tau;&tau; to improve the agreement.

The corrections considered in this subsection belong to the type, that can be introduced with event weights. A different type of corrections will
be discussed in section [7](es_tau.md), covering the &tau;<sub>h</sub> energy scale correction as an example.

### Pileup reweighting

One of the general corrections used for simulated samples is the pileup reweighting. The reason to introduce this correction is the fact, that the distribution of the
number of additional interactions taking place in collision events is different between data and simulation. The measured mean number of interactions per bunch crossing
for the 2018 data-taking period is shown on public results pages of the luminosity group of CMS:

![](https://cmslumi.web.cern.ch/publicplots/pileup_pp_2018_69200.png)

This histogram corresponds to the true number of interactions per bunch crossing in simulation, averaged over a luminosity section. This value is used as an input parameter to
obtain the Poisson distributed number of interactions on an event-by-event basis.
Details on the measurement of the number of interactions and its determination for simulated events is given on the
[Pileup Twiki page](https://twiki.cern.ch/twiki/bin/view/CMS/PileupJSONFileforData).

The corresponding histograms are already included in the software framework:

* Data from 2018 data-taking period: [Data_PileUp_2018_69p2.root](../../PicoProducer/data/pileup/Data_PileUp_2018_69p2.root)
* Simulation from the Autumn18 Monte-Carlo campaign: [MC_PileUp_2018_Autumn18.root](../../PicoProducer/data/pileup/MC_PileUp_2018_Autumn18.root)

This means, that you would need to introduce a new weight quantity `pileupWeight` to the analysis module
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) by dividing the two histograms after having normalized them to unity, and extracting
the appropriate weight using the `Pileup_nTrueInt` quantity from the simulated NanoAOD input sample. In the next step, extend the weight applied to all simulated
samples in [plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py) accordingly.

You can demonstrate the effect of the reweighting by having a look at the control plots of the two quantities affected by this correction:

* Number of reconstructed primary vertices (`PV_npvs`)
* Pileup density &rho;, computed from all PF Candidates (`fixedGridRhoFastjetAll`)

Furthermore, make a plot of the two pileup distributions in data and simulation, and the resulting correction weights histogram.

### Muon efficiency corrections

In contrast to pileup reweighting, which is a pure modelling systematic effect related to Monte-Carlo simulation, muon efficiency corrections belong to systematic effects of
experimental type. In the context of the exercise, we will examine the muon identification and muon isolation efficiencies.

Under muon identification (ID) we understand a selection of muons with quality requirements (see
[Muon ID Twiki](https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonIdRun2#Muon_Identification)), which are compiled in working points, the most common being
[Loose](https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonIdRun2#Loose_Muon), [Medium](https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonIdRun2#Medium_Muon), and
[Tight](https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonIdRun2#Tight_Muon). These working points are defined according to the efficiency to identify true muons and
the misidentification rate of objects reconstructed falsely as muons.

The **tighter** the selection the purer is the selected set of muons, having a smaller efficiency,
but also a much smaller misidentification rate. For some applications, a higher efficiency is more important than a pure set of muons, such that a **looser** working point
is chosen.

For muons, muon isolation (Iso) is handled separately from identification to allow for flexibility of an analysis to choose the Iso working points independently of ID working
points. The isolation is computed by summing up the energy around the muon in a predefined (&eta;, &phi;) cone. At CMS, we usually use the
[PF-based isolation](https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonIdRun2#Particle_Flow_isolation), summing up transverse energy and momenta of particle flow
candidates around the muon.

To correct the isolation sum for contamination from pileup (PU), an estimate of the corresponding energy contribution is subtracted from the full energy sum. For muons, the
&Delta;&beta; correction is used, leading to the following formula for the muon isolation sum:

Iso(&mu;) = &Sigma;p<sub>T</sub>(P<sup>&plusmn;</sup> from PV) + max(0, &Sigma;p<sub>T</sub>(h<sup>0</sup>) + &Sigma;p<sub>T</sub>(&gamma;) - &Delta;&beta; &middot;
&Sigma;p<sub>T</sub>(P<sup>&plusmn;</sup> from PU))

The following assumptions and syntax is used for the formula above:

* Cone around the muon is chosen to be &Delta;R = 0.4.
* Multiplicative factor &Delta;&beta; = 0.5.
* P<sup>&plusmn;</sup> from PV: charged particles from the primary vertex (other than the considered muon)
* P<sup>&plusmn;</sup> from PU: charged particles from pileup
* h<sup>0</sup>: neutral hadrons
* &gamma;: photons

The main idea of the &Delta;&beta; correction is to estimate the energy contribution of neutral particles from
pileup by exploiting the ratio between charged and neutral particles from pileup, which is estimated to be the factor &Delta;&beta;.

To define a working point for a selection of isolated muons, usually the **relative** isolation sum of a muon is considered:

rel. Iso(&mu;) = Iso(&mu;)/p<sub>T</sub>(&mu;)

Also for the selection of isolated muons, several working points are defined according to the efficiency to select true muons.

Both the muon identification and muon isolation efficiencies are measured with the
[Tag and Probe (TnP) method](https://twiki.cern.ch/twiki/bin/view/CMS/MuonReferenceEffsRun2Legacy), selecting Z&rarr;&mu;&mu; with a strict selection of one
of the muons (tag muon) and checking, whether the second muon (probe muon) passes the considered selection requirements. The efficiencies are measured
recursively, such that the isolation efficiency depends on a chosen identification working point. Usually, these efficiencies are measured as functions
of the p<sub>T</sub> and &eta; of the muon. 

Scale factors used for correction are then derived as the ratio of the efficiencies in data and simulation. Such a scale factor is expected to be close to one,
but may differ from unity due to differences of detector response between data events and simulated events or modelling used in simulation,
leading to different distributions of quantities used for reconstruction, identification of muons and the particles around it.

The corresponding histograms are already provided in the software framework:

* Identification scale factors: [RunABCD_SF_ID.root](../../PicoProducer/data/lepton/MuonPOG/Run2018/RunABCD_SF_ID.root)
* Isolation scale factors: [RunABCD_SF_Iso.root](../../PicoProducer/data/lepton/MuonPOG/Run2018/RunABCD_SF_Iso.root)

Please note, that only a limited set of combinations is provided for the working points of ID and Iso in these files, such that you would have to stick to these
selection choices to apply the corrections consistently.

Please introduce two weights `idWeight` and `isoWeight` to the analysis module
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) by extracting the weights from the histograms using the p<sub>T</sub> and &eta; of the muon
from the &mu;&tau;<sub>h</sub> pair. As for the pileup weight before, please extend the total weight applied to all simulated
samples in [plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py) accordingly after having added the two weights to your n-tuples.

As you might already have guessed, the change of the correction can be demonstrated best with control plots of p<sub>T</sub> and &eta; of the muon.

### Z boson p<sub>T</sub> correction

The last type of correction which we will examine is a modelling correction, which is in contrast to the pileup reweighting process specific, such that it has
to be applied only to Drell-Yan events - the Z boson p<sub>T</sub> correction. The reason for this correction is the fact, that the used simulated samples correspond
to leading order (LO) precision in QCD for Drell-Yan events, for which the Z boson p<sub>T</sub> is not well described if compared to the corresponding data distribution.

The correction scale factors are measured for a pure Z&rarr;&mu;&mu selection, were the true Z boson p<sub>T</sub> is expected to corrrespond to the p<sub>T</sub>
of the &mu;&mu; pair. These weights are computed such that they change the distribution of reconstructed p<sub>T</sub>(Z) in simulation to the one in data, preserving
the overal normalization of the considered simulated events.

The weights, which are already provided in [Zpt_weights_2018.root](../../PicoProducer/data/zpt/Zpt_weights_2018.root) are then applied to generator truth information
on the Z boson p<sub>T</sub>. In that way, the correction can be applied to Z&rarr;&tau;&tau; events, where the Z boson p<sub>T</sub> can not be reconstructed precisely
due to neutrinos involved in &tau; decays.

To obtain the information on particles at the level of the Monte-Carlo generator, you would need to loop through the list of generator particles
[`GenPart`](https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html#GenPart) and select the Z boson according to its
[`pdgId`](https://pdg.lbl.gov/2020/reviews/rpp2020-rev-monte-carlo-numbering.pdf). There will be several instantiations of the Z boson with a different status,
which is a detail of the [Pythia 8.2](http://home.thep.lu.se/~torbjorn/pythia82html/Welcome.html) event generator.
You should choose `GenPart_status == 62` which corresponds to the generator truth Z boson after proper treatment of beam remnant particles,
contributing to the underlying event of a collision.

The weight from the histogram in [Zpt_weights_2018.root](../../PicoProducer/data/zpt/Zpt_weights_2018.root), extracted by using generator Z boson p<sub>T</sub>, should
only be computed for and applied to the simulated events of the Drell-Yan process, which can be managed by an option keyword argument `zpt` introduced in
[samples_mutau_2018_preselected.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018_preselected.py#L8-L12). You can access this keyword argument
in a similar way as the sample type `dtype` in [ModuleMuTau.py](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py#L25).

After having introduced a sample specific weight `zptWeight` to your Drell-Yan n-tuple, you can add it with the `extraweight` key into the dictionary of the Drell-Yan
process in [plots_and_histograms_CMSDAS2020.py](https://github.com/ArturAkh/TauFW/blob/master/Plotter/plots_and_histograms_CMSDAS2020.py#L37-L38), as already done for `nevts`.
An example, how this can be done, is given in [samples.py](https://github.com/ArturAkh/TauFW/blob/master/Plotter/config/samples.py#L19-L24).

To demonstrate the change introduced by this correction, you can have a look at the control plots of the visible Z boson p<sub>T</sub>, computed from the p<sub>T</sub>
of the &mu;&tau;<sub>h</sub> pair, and the best reconstructed estimate for the Z boson p<sub>T</sub>, corresponding to the vector sum of &mu;&tau;<sub>h</sub>
pair p<sub>T</sub> and the MET vector.

### Group task - implement the event-by-event corrections

Those of you, who would like to take care of the corrections discussed in the previous subsections, please implement the required procedures, and document the
impact of each correction step by step in form of control plots. For the presentation, please explain the purpose of each correction, if needed, by making use of
sketches and plots of provided correction factors.
