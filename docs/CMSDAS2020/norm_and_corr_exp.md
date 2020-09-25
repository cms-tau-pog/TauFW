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
# `main(args)` method: main function used to execute the previous two after having specified the conditions for them appropriately.
# `if __name__ == "__main__":` section: This actually the part, which is executed, when you run the script. Usually, it is used to parse arguments and pass them to the `main` function.


To run the plot and histogram production script, please use the following commands, depending on the way you have produced your flat n-tuples:

```sh
# Move to Plotter directory
cd ${CMSSW_BASE/src}/TauFW/Plotter/

# In case you obtained your flat n-tuples from batch submission
./plots_and_histograms_CMSDAS2020.py -c mutau -y 2018

# In case you produced your flat n-tuples locally (via parallelized script, for example). Here, you need to specify a custom pattern for your output files
./plots_and_histograms_CMSDAS2020.py -c mutau -y 2018 --picopattern "${CMSSW_BASE}/src/TauFW/PicoProducer/output/pico_\$CHANNEL_\$ERA_\$SAMPLE.root"
```

If everything works out properly, you should obtain plots in the `${CMSSW_BASE/src}/TauFW/Plotter/plots/2018/` folder and a histogram in the `${CMSSW_BASE/src}/TauFW/Plotter/hists/2018/` folder.
