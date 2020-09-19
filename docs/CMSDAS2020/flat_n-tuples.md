# 4. Creating flat n-tuples

After the NanoAOD samples are preselected as described in the [previous section](preselection.md), you can create flat n-tuples based on these samples
with faster turn-around cycles, than using original NanoAOD as input.

This section is meant as an introduction to the way analysis modules in TauFW can be setup to create flat n-tuples, based on the example for the &mu;&tau;<sub>h</sub>,
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
+ `analyze(self, event)`: This is the main function of the analysis module.
