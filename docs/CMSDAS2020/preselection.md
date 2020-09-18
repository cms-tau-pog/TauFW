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

## Simulated samples of the expected contributions

After it is clear, which contributions are expected, you need to find corresponding simulated samples.

In this case, you need a valid VOMS proxy, so check its validiy with the commands from section [2](configuration.md#configuration-after-new-login-or-in-a-new-terminal).

The tool to check for available data samples and simulated samples is the `dasgoclient`, which can be used in command line. Alternatively, you can do the same sample searches
on the [Data Aggregation Service](https://cmsweb.cern.ch/das/) webpage, provided that your VOMS certificate is included in your browser.
But let us stay with nuch faster command line tool ;).

The query for the simulated Drell-Yan sample from [samples_mutau_2018.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018.py) looks as follows:

```sh
dasgoclient --query="dataset dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM"
```

If you like to see, whether there are other Drell-Yan samples available, you can use wildcard notation with &ast;:

```sh
dasgoclient --query="dataset dataset=/DY*JetsToLL_M-50_TuneCP5*/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20*/NANOAODSIM"
```

You can also search for the files of the first dataset, or on which sites it is located:

```sh
dasgoclient --query="file dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM"
dasgoclient --query="site dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM"
```

You can even get more information on the sample, like the number of events, if requiring to have detailed info in .json format:
```sh
dasgoclient --query="dataset dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM" -json
```
