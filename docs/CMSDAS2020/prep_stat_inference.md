# 8. Preparations for statistical inference

After having performed the different group tasks of the analysis, it is time to put everything together.
Please create a final set of flat n-tuples with modified module [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py)
containing the following improvements from each group:

+ Variables implemented, which are needed for a refined selection of Z&rarr;&tau;&tau; applied in the plotting script
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py)
+ Additional weights included, needed for corrections
+ Energy scale corrections applied to the &tau;<sub>h</sub> candidate

The nominal set of n-tuples for &mu;&tau;<sub>h</sub> should be supplemented with the e&mu; n-tuples,
and the variations of &tau;<sub>h</sub> energy scale corresponding to the uncertainty estimate.

Based on these n-tuples, you can produce plots and - more important for the statistical inference - histograms
of our main discriminator, the visible mass of the &mu;&tau;<sub>h</sub> (or e&mu;) pair. Please use for that
the selection defined as `signal_region` enriching Z&rarr;&tau;&tau;, and include the weights needed to apply corrections. Also do
not forget to modify the QCD extrapolation factor [`scale`](https://github.com/ArturAkh/TauFW/blob/master/Plotter/plots_and_histograms_CMSDAS2020.py#L126) according
to your measurement of that factor.

For the systematic variations of the &tau;<sub>h</sub> energy scale in the &mu;&tau;<sub>h</sub> final state, you can also create histograms for the processes affected
by it, for example `TopT`, `EWKT`, `ZTT`, but with the [`tag`](../../Plotter/plots_and_histograms_CMSDAS2020.py#L149) 
modified to the way you have saved the downvard and upward variations of the energy scale n-tuples using the tag.
Then, modify the naming of the histograms as follows in the corresponding lines:

```python
    # ...
    variation_name = "tauh_esDown" # change to tauh_esUp for the other variation
    for stack, variable in stacks.iteritems():
      outhists.cd(selection.filename)
      for h in stack.hists:
        h.Write(h.GetName().replace("QCD_","QCD") + variation_name,R.TH1.kOverwrite) # adding to the name for es variations in addition
    # ...
```

In that way, your output file should contain histograms like `signal_region/m_vis_ZTT_tauh_esDown`, which are then accessed by
CombineHarvester to create systematic variations.

Assuming, that you have different channel names for the nominal n-tuples, and the corresponding scale variations, the histogram output
files should also have different names. You can put them together with `hadd` to have everything in one file:

```sh
cd $CMSSW_BASE/src/TauFW/Plotter/
hadd mutau.root hists/2018/mutau*.root
```

Feel free also to use your own setup of [ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py) and
[plots_and_histograms_CMSDAS2020.py](../../Plotter/plots_and_histograms_CMSDAS2020.py), with a possible additional selection

```python
signal_region = "q_1*q_2<0 && pt_1 > 29 && pt_2 > 20 && iso_1 < 0.15 && (decayMode_2 < 5 || decayMode_2 > 7) && id_2 >= 31 && anti_mu_2 == 15"
```
In that way, you can get familiar with the statistical inference procedure, using your own histograms, without having to wait for the final set of n-tuples.

After having prepared the input histograms, the software set for statistical inference consisting of [CombinedLimit](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit),
[CombineHarvester](https://github.com/cms-analysis/CombineHarvester), and [CMSDAS2020TauLong](https://github.com/ArturAkh/CMSDAS2020TauLong) can be used
to obtain the results. The usual procedure within this framework consists of three main steps:

+ Creation of datacards and associated histogram inputs, handled by the script [construct_datacards.py](https://github.com/ArturAkh/CMSDAS2020TauLong/blob/master/scripts/construct_datacards.py).
+ Translation of the datacards into a RooWorkspace, using the `combineTool.py -M T2W` method.
+ Performing calculations to obtain results with a suite of different CombineHarvester commands.

The first two steps will be discussed in detail within this section, while the last step will be covered by section [9](measurement.md).

## Constructing datacards and RooWorkspace

Before proceeding with the first step of preparations for statistical inference, please make sure, that your software setup is switched to the statistical inference environment,
as explained in section [2](configuration.md#configuration-after-new-login-or-in-a-new-terminal).

Furthermore, please put the histogram files merged with `hadd` to contain the systematics variations - they should have their channel names, `mutau.root` and `emu.root` -
into the appropriate folder [shapes](https://github.com/ArturAkh/CMSDAS2020TauLong/blob/master/shapes).

Now, let us have a closer look at the script [construct_datacards.py](https://github.com/ArturAkh/CMSDAS2020TauLong/blob/master/scripts/construct_datacards.py).

After having setup the required imports and the main CombineHarvester instance, expected contributions are defined with their names:

```python
# Definition of process names to be used in the analysis
mc_backgrounds = ['TopT', 'TopJ', 'EWKT', 'EWKJ', 'ZL']
data_driven_backgrounds = ['QCD']
backgrounds = mc_backgrounds + data_driven_backgrounds

signals = ['ZTT']

mc = mc_backgrounds + signals
```

The processes are grouped according to their type, being either background or signal, and data-driven or simulated.

In the next step, categories are defined with a proper syntax for CombineHarvester:

```python
# Introduction of categories to be analysed
categories = {
    # this defines the CHANNEL name used in the context of CombineHarvester
    'mutau' : [( 1, 'signal_region' )], # way to assign a category, called BIN in CombineHarvester with a string name and a BIN index
    #TODO section 8: extend with emu channel here in the same manner
}
```

The categories are summarized as a python dictionary with the considered final states as key. Currently, only &mu;&tau;<sub>h</sub> is implemented, but you can easily extend
to e&mu;.

To each final state - in CombineHarvester syntax considered as `CHANNEL` - a list of category tuples is assigned, which contain the `BINID` number of the category
as the first element, and the category name as the second. In CombineHarvester syntax, categories are considered as `BIN`.

After that, the data - called `Observation` in CombineHarvester - and  and the expected processes are added formally to the CombineHarvester instance:

```python
for channel in categories:
    cb.AddObservations(['*'], ['ztt'], ['2018'], [channel],              categories[channel]) # adding observed data
    cb.AddProcesses(   ['*'], ['ztt'], ['2018'], [channel], backgrounds, categories[channel], False) # adding backgrounds
    cb.AddProcesses(   ['*'], ['ztt'], ['2018'], [channel], signals,     categories[channel], True) # adding signals
    
cb.ForEachObs(lambda x : x.set_process('SingleMuon_Run2018')) # some hack to change the naming to the one in the input files; usual name: data_obs
```

The next part of the code introduces and defines the uncertainties of the statistical model, which are introduced with nuisance parameters drawn from
appropriate distributions. In the context of this exercise, we consider three types of uncertainties and parameters:

```python
# Normalization uncertainty
cb.cp().process(mc).AddSyst(cb,'lumi_2018', 'lnN', ch.SystMap()(1.025)) # 2.5 % uncertainty on luminosity for 2018 from the measurement

# Shape uncertainty
cb.cp().channel(['mutau']).process(['ZTT', 'TopT', 'EWKT']).AddSyst(cb, 'tauh_es', 'shape', ch.SystMap()(1.0))

# Unconstrained nuisance parameter
cb.cp().channel(['mutau']).process(['ZTT', 'TopT', 'EWKT']).AddSyst(cb, 'tauh_id', 'rateParam', ch.SystMap()(1.0))
```

The first type is a normalization uncertainty, which is modelled with a log-normally distributed (`lnN`) nuisance parameter. The value put into `ch.SystMap()(<value>)` corresponds
to the uncertainty estimate, so the one &sigma; standard deviation measured for this particular systematic uncertainty source.

The second type is a (binned) shape uncertainty. In this case `ch.SystMap()(1.0)` means, that the shapes corresponding to the downward and upward variations are assigned to 
a variation of one &sigma; standard deviation of the corresponding nuisance parameter. This Gaussian distributed nuisance paramter is used to inter- and extrapolate bin-wise between the 
variations and the nominal histogram in a correlated way accross all histogram bins.

The last type we consider is an unconstrained rate parameter. Such parameters can be used to define additional quantities, which are not known a priori, such as the &tau;<sub>h</sub>
identification efficiency, which we have not measured beforehand. This rate parameter is not drawn from a certain distribution, but has a flat prior, such that each of its values has an equal
probability - therefore the name "unconstrained". In this case `ch.SystMap()(1.0)` is used to set the nominal value of the nuisance parameter.

Rate parameters can be used - as also done in our case - to measure quantities simultaneously with the parameter of interest, the signal strength &mu;<sub>Z&rarr;&tau;&tau;</sub>.

Next, the shapes are extracted for the processes and their systematic shape variations:

```python
# Define access of the input histograms; please note how systematics shape variations should be stored:
#       $BIN/m_vis_$PROCESS_$SYSTEMATIC with $SYSTEMATIC containing the name like 'tau_es' and a postfix 'Up' or 'Down'
for channel in categories:
    filepath = os.path.join(os.environ['CMSSW_BASE'],'src/CombineHarvester/CMSDAS2020TauLong/shapes', channel+'.root')
    cb.cp().channel([channel]).backgrounds().ExtractShapes(filepath, '$BIN/m_vis_$PROCESS', '$BIN/m_vis_$PROCESS_$SYSTEMATIC')
    cb.cp().channel([channel]).signals().ExtractShapes(filepath, '$BIN/m_vis_$PROCESS', '$BIN/m_vis_$PROCESS_$SYSTEMATIC')
```

Here, the patterns for the processes and systematic variations should be chosen carefully to match the syntax in the input histograms exactly.

Finally, before writing everything out into appropriate datacard folders, the statistical uncertainties on the total background are introduced, based on the Barlow-Beeston (lite) approach:

```python
cb.SetAutoMCStats(cb, 0.0) # Introducing statistical uncertainties on the total background for each histogram bin (Barlow-Beeston lite approach)
```

The created datacards are put all into one `cmb` folder for the combined measurement, and into `mutau` and `emu` folders for measurements in individual final states.
The target directory, where these folders are placed, is `ztt_analysis/2018/`, created in the directory, where the script `construct_datacards.py` is executed, for
example:

```sh
cd $CMSSW_BASE/src/CombineHarvester/CMSDAS2020TauLong/
construct_datacards.py
```

After creating the datacard folder infracstructure, these need to be translated into workspaces, using the following command:

```sh
combineTool.py -M T2W -i ztt_analysis/2018/*/ --parallel 3 -o workspace.root
```

This will create in each of the datacard folders `mutau`, `emu`, and `cmb` a workspace, which can be used for the measurements to be covered in the next section.
With the `-M T2W` method, it is possible to introduce more complicated signal models via `-P` and `--PO` options. However for our purposes, the standard signal model
with all signals assigned to a single signal strength parameter `r` in CombineHarvester is sufficient.

If looking at the datacards themselves, for example at `/ztt_analysis/2018/cmb/ztt_mutau_signal_region_2018.txt`, one can see the different contributions, and
uncertainties introduced in [construct_datacards.py](https://github.com/ArturAkh/CMSDAS2020TauLong/blob/master/scripts/construct_datacards.py), as well as how the
histogram inputs are assigned to the processes. Furthermore, you can see, that signals have a process ID smaller or equal to 0, whereas the backgrounds obtain a
process ID greater than 0.

After these preparations you should be ready to perform the various commands for calculations involved into the measurement. Let us move on to section [9](measurement.md)!
