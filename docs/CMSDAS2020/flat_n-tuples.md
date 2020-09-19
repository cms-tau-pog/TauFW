# 4. Creating flat n-tuples

After the NanoAOD samples are preselected as described in the [previous section](preselection.md), you can create flat n-tuples based on these samples
with faster turn-around cycles, than using original NanoAOD as input.

This section is meant as an introduction to the way analysis modules in TauFW can be setup to create flat n-tuples, based on the example for the &mu;&tau;<sub>h</sub>,
[ModuleMuTau](../../PicoProducer/python/analysis/CMSDAS2020/ModuleMuTau.py).

If your TauFW configuration still corresponds to the preselection setup (check with `pico.py list`), then please change it to be able to run on top preselected NanoAOD samples.
For &mu;&tau;<sub>h</sub>, you can follow the instructions from section [2](configuration.md#configuration-done-once-per-desired-change) to change the settings,
including an increase the number of processed files by default.

##Structure of an analysis module
