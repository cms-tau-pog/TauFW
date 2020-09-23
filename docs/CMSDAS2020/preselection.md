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
+ Minor contributions are expected from the production of two bosons (WW, WZ, WZ), and from the single t production.

## Simulated samples of the expected contributions

After it is clear, which contributions are expected, you need to find corresponding simulated samples.

In this case and for the remaining part of this section, you need a valid VOMS proxy, so check its validiy with the commands from section
[2](configuration.md#configuration-after-new-login-or-in-a-new-terminal).

The tool to check for available data samples and simulated samples is the `dasgoclient`, which can be used in command line. Alternatively, you can do the same sample searches
on the [Data Aggregation Service](https://cmsweb.cern.ch/das/) webpage, provided that your VOMS certificate is included in your browser.
But let us stay with much faster command line tool ;).

The query for the simulated Drell-Yan sample from [samples_mutau_2018.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018.py) looks as follows:

```sh
dasgoclient -query="dataset dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM"
```

If you like to see, whether there are other Drell-Yan samples available, you can use wildcard notation with &ast;:

```sh
dasgoclient -query="dataset dataset=/DY*JetsToLL_M-50_TuneCP5*/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20*/NANOAODSIM"
```

You can also search for the files of the first dataset, or on which sites it is located:

```sh
dasgoclient -query="file dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM"
dasgoclient -query="site dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM"
```

You can even get more information on the sample, like the number of events, if requiring to have detailed info in .json format:

```sh
dasgoclient -query="dataset dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM" -json
```

Feel free to play around with the tool to get familiar with it.

## Collected data appropriate for a Z&rarr;&tau;&tau; final state

In case of data samples, you would need to search for the one appropriate to the specific final state you would like to consider, since the data is collected by a trigger system.

For the &mu;&tau;<sub>h</sub> final state, the `SingleMuon` datasets were chosen (compare with [samples_mutau_2018.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018.py)):

```sh
dasgoclient -query="dataset dataset=/SingleMuon/Run2018*Nano25Oct2019*/NANOAOD"
```

As you will see after executing the command above, there are four different run periods available for 2018 data: A, B, C and D. To check all possible datasets collected in 2018 - let us stick to run period D for convenience, but feel free to check also the other three periods - you can execute the following:

```sh
dasgoclient -query="dataset dataset=/*/Run2018D*Nano25Oct2019*/NANOAOD"
```

Which datasets would you choose for the other Z&rarr;&tau;&tau; final states of interest: e&tau;<sub>h</sub>, &tau;<sub>h</sub>&tau;<sub>h</sub>, and e&mu;?

## Choice of preselection and quantities of interest

The samples to be processed are now chosen. The main purpose of the preselection you learn in this section is twofold:

+ Select only those events, that might be interesting.
+ Choose only those quantities from NanoAOD, which are relevant.

The preselection, also called *skimming*, is handled in the TauFW framework by the [skimjob.py](../../PicoProducer/python/processors/skimjob.py) processor, which can be used
with the main script [pico.py](../../PicoProducer/scripts/pico.py):

```sh
pico.py run -c skim -y 2018 -m 10000 -p
```

By default, `pico.py` runs on the first file of the first sample from its list. The options specified in the command above mean the following:

+ `-c skim` or `--channel skim`: selects the processor for skimming, [skimjob.py](../../PicoProducer/python/processors/skimjob.py).
+ `-y 2018` or `--era 2018`: selects the era to be processed, and with it the sample list configured for that era.
+ `-m 10000` or `--maxevts 10000`: limits the execution of the command to process at most 1000 events.
+ `-p` or `--prefetch`: enables copying of the (remote) input file to a local temporary directory. If the input file is large enough, it is often much faster and safer just to copy it to the local worker node and run on the copied file. The alternative would be to stream the remote file (e.g. via XRootD), which can break up in the middle of a job, or be very slow. In case of NanoAOD files, which are actually small compared to other formats, that is a pretty convenient solution.

So far, no preselection is specified. This can be done via the option `--preselect`.
For the preselected samples configured in [samples_mutau_2018_preselected.py](../../PicoProducer/samples/CMSDAS2020/samples_mutau_2018_preselected.py) the command reads as follows (local test version of it):

```sh
pico.py run -c skim -y 2018 -m 10000 -p --preselect 'HLT_IsoMu27 == 1 && Muon_pt > 28 && Tau_pt > 18 && Muon_mediumId == 1 && Muon_pfRelIso04_all < 0.5 && Tau_idDeepTau2017v2p1VSmu >= 1 && Tau_idDeepTau2017v2p1VSe >= 1 && Tau_idDeepTau2017v2p1VSjet >= 1'
```
Let us have a closer look at the various parts of the selection:

+ `HLT_IsoMu27 == 1`: Since data is collected with the help of a trigger system, an appropriate trigger decision needs to be specified to be consistent in the selection of data and simulation. For the
&mu;&tau;<sub>h</sub> final state, it is good to select a high level trigger (HLT) path targeting one muon, since this HLT path is simple and not too restrictive.
+ `Muon_pt > 28`: Due to the selection of the HLT, we are interested in muons with offline transverse momentum (p<sub>T</sub>) slightly above the HLT p<sub>T</sub> threshold.
In that way, the turn-on region of the HLT path is avoided, which is usually difficult to model.
+ `Tau_pt > 18`: An HLT path is not required for &tau;<sub>h</sub> candidates, therefore, you can choose the loosest threshold possible for these physics objects. If you have a look at the NanoAOD definition, you will figure out, that it exactly matches this definition. In the context of this exercise, you will be advised to test different possibilities for a higher threshold
on p<sub>T</sub>(&tau;<sub>h</sub>) in further steps of the analysis discussed later.
+ `Muon_mediumId == 1 && Muon_pfRelIso04_all < 0.5`: In an analysis, you are interested in well reconstructed muons. A good compromise between high purity and high efficiency is the medium working point (WP) of muon identification. Although it is usually best to select also well isolated muons, the threshold on the relative muon isolation using all particle flow (PF) candidates is kept high to be able to define sideband regions with looser isolation requirement.
+ `Tau_idDeepTau2017v2p1VSmu >= 1 && Tau_idDeepTau2017v2p1VSe >= 1 && Tau_idDeepTau2017v2p1VSjet >= 1`: To allow you playing around with &tau;<sub>h</sub> candidates, the loosest possible WPs are chosen for the DeepTau discriminators against muons, electrons, and jets.

After executing the command above for the Drell-Yan dataset (taken by default), you will notice, that only 0.1% of events pass the preselection defined for &mu;&tau;<sub>h</sub>.
If none of the physics objects have satisfied the criteria from above in an event, this event is discarded.

Therefore, if you plan to preselect for a different final state, think first about a preselection which is loose enough to allow for definitions of sideband regions and for optimization studies,
but restrictive enough to reject enough events to reduce the size of the dataset.

Now let us check, which quantities are chosen from original NanoAOD into the preselected NanaAOD. For this purpose, the [skimjob.py](../../PicoProducer/python/processors/skimjob.py) processor
loads the [keep_and_drop_skim.txt](../../PicoProducer/python/processors/keep_and_drop_skim.txt) file, in which the keys `keep` and `drop` are used, as well as wildcards to select
required quantities. For more details, have a look at [branchselection.py](https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/branchselection.py) of
[nanoAOD-tools](https://github.com/cms-nanoAOD/nanoAOD-tools).

To have an example for the original NanoAOD, you can copy one of the files from Drell-Yan dataset (use `dasgoclient` to get a file path) from remote to your local work directory with `xrdcopy`:

`xrdcopy root://cms-xrd-global.cern.ch/<file-path-from-dasgoclient> .`

For an example of a preselected file, just run the preselection command above, if you wish, with an additional requirement of `-s DY` or `--sample DY` to be sure to run on Drell-Yan dataset.

Now you can have a look at the content of the `Events` TTree, which stores event information of the NanoAOD file. Most convenient way to do this is just by executing two `ROOT` commands and `vimdiff`:

```sh
root -l <original>.root -e "Events->GetListOfLeaves()->Print(); exit(0)" | sort -V > original_content.txt
root -l <preselected>.root -e "Events->GetListOfLeaves()->Print(); exit(0)" | sort -V > preselected_content.txt
vimdiff original_content.txt preselected_content.txt
```
Note, that you have to replace `<original>.root` and `<preselected>.root` with appropriate local file paths. And again, `vimdiff` is just so much cooler than `diff` ;).

## Batch submission of preselection

After having tested your preselection locally - **test always your commands and code locally at first** - you can prepare and then start the submission to a batch system, since
such a system offers you plenty of resources for your calculations.

*Batch systems are a physicist&apos;s best friend*, someone told once :).

The batch system at CERN that can be accessed from `lxplus` and which has also access to your local work directory on `lxplus` by itself,
is based on [HTCondor](https://research.cs.wisc.edu/htcondor/manual/). Details, on how jobs at CERN `lxplus` batch system can be submitted, can be found at CERN&apos;s
[Batch Docs](https://batchdocs.web.cern.ch/local/submit.html).

To submit the skim command with preselection from above to the batch system, replace `run` with `submit` and modify the remaining options as you need, for example by using the `espresso` queue:

```sh
pico.py submit -c skim -y 2018 -p --preselect 'HLT_IsoMu27 == 1 && Muon_pt > 28 && Tau_pt > 18 && Muon_mediumId == 1 && Muon_pfRelIso04_all < 0.5 && Tau_idDeepTau2017v2p1VSmu >= 1 && Tau_idDeepTau2017v2p1VSe >= 1 && Tau_idDeepTau2017v2p1VSjet >= 1' --queue espresso
```

You are advised to test the command above at first with `--dry` to ensure, that all job directories are created properly. Then you can remove these directories and try to perform a test submit without
`--dry` but for one sample, e.g. `-s DY`. With this test submit you can check, whether the `espresso` queue with 20 minutes is sufficient to run the preselection on the amount of files configured by
default (check it with `pico.py list` before submission).

To check the status of the jobs, perform the `status` command adapted from the `submit` command above:

```sh
pico.py status -c skim -y 2018
```

In case jobs are failed, you can resubmit these with changed options by replacing `submit` with `resubmit`.
It is important to keep the other options you do not want to change, such as `--preselect` also for the `resubmit` command.
To get more familiar with job submission, check the corresponding `--help` of `pico.py`.

For successfully finished jobs, have a look, how the corresponding logging files look like. There you can also check, where the output files from the preselection are copied.
The directories with logging files and the final output directory should match your configuration, which you can check with `pico.py list`.

After all jobs for the test submit are finished you can submit the remaining samples by specifying the other sample names as a list passed to the `-s` option.

Then, after occasional baby-sitting and resubmission of jobs, you should have all of them processed at some point. Congragulations! :)

Let us use these preselected NanoAOD samples for further processing to create flat n-tuples, as will be explained in the [next section](flat_n-tuples.md).
