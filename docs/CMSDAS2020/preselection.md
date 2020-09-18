# 3. Preselecting NanoAOD

After having configured the analysis setup for NanoAOD preselection explained in section [2](configuration.md#configuration-done-once-per-desired-change),
you will learn how to do this with the TauFW framework in this section.

The example covered here is discussing the steps needed to preselect the samples listed in [samples_mutau_2018.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018.py)
for the &mu;&tau;<sub>h</sub> final state, as already done and stored under the following path accessible from `lxplus`:

```sh
/eos/cms/store/group/phys_tau/CMSDAS2020/nano/2018/
```

Feel free to adapt this workflow to preselect NanoAOD samples for other final states, for example e&mu;.

## Processes contributing to a Z&rarr;&tau;&tau; final state

The first thing you need to figure out for the final state you are interested in, are the possible processes contributing to it.
In the context of the Z&rarr;&tau;&tau; cross-section measurement, the following processes are considered, independent of the actual final state:

+ Most important contribution containing also the Z&rarr;&tau;&tau; signal, is the Drell-Yan production of Z/&gamma;<sup>&ast;</sup>.
+ Especially in the &mu;&tau;<sub>h</sub> and e&tau;<sub>h</sub> final states, &tau;<sub>h</sub> is often a misidentified jet from the production of a W boson, accompanied by jets.
+ Furthermore, the production of a tt&#773; pair is considered, being dominant in particular in the e&mu; final state.
+ QCD multi-jet background is apparent in all final states, however it is usually estimated from data, such that you do not need to look for simulated samples for that process.
+ Minor contributions are expected fro the production of two bosons (WW, WZ, WZ), and from the single t production.
