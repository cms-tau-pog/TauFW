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
+ Higgs Boson production: [LHCHXSWG](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHXSWG#Higgs_cross_sections_and_decay_b)

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

This splitting is based on generator information, whether the reconstructed &tau;<sub>h</sub> candidate is matched to a real &tau;<sub>h</sub> or not.

As a small, optional task, please have a look at the distribution of quantities `genmatch_1` and `genmatch_2` for the various sameples you have processed to flat n-tuples.
Please have a look at the definition of these variables in the [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) and the
[NanoAOD documentation](https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html).

For the Drell-Yan process, `ZL` is defined as every contribution, where the reconstructed &tau;<sub>h</sub> candidate does not correspond to a real &tau;<sub>h</sub>. The naming `ZL`
indicates, that the Z&rarr;&mu;&mu; process is meant in case of the &mu;&tau;<sub>h</sub> final state, assuming that this is the major contribution to `ZL`. Is this justified?
What is the major contribution to other processes with `genmatch_2!=5`?
