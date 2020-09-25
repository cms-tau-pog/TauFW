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
