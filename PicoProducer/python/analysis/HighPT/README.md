##ModuleHighPT
This README is intended to give instructions on how create ntuples for the tau ID efficiency and ES SFs measurement at high pt. The ModuleHighPT is the main module for this kind of analysis.
The script is here:`python/analysis/ModuleHighPT.py`

##Before start
The ModuleHighPT analysis module inherits from other modules defined in `PicoProducer`.
All information provided here assume that one has already looked at [the README.md in the parent directory](https://github.com/cms-tau-pog/TauFW/#taufw).

##ModuleTauNu 
This module inherits from ModuleHighPT and it's meant to select events for the W*->tau nu process.
Event selection is performed by the script `python/analysis/HighPT/ModuleTauNu.py`.

##ModuleMuNu 
This module inherits from ModuleHighPT and it's meant to select events for the W*->mu nu process.
Event selection is performed by the script `python/analysis/HighPT/ModuleMuNu.py`.

##ModuleWJ
This module inherits from ModuleHighPT and intended to select events to select W(->mu+v)+1jet events for the measurement of the jet->tau fake factors.

##ModuleDiJet
This module inherits from ModuleHighPT and intended to select events to	select dijet events for the measurement of the jet->tau fake factors.

##TreeProducerHighPT
The TreeProducerHighPT module inherits from other modules defined in `PicoProducer`.
It's purpose is to be the basis for the TreeProducers.
The script is here:`python/analysis/TreeProducerHighPT.py`

##TreeProducerTauNu
This module inherits from TreeProducerHighPT and it's meant to create ntuples (ROOT files) for the W*->tau nu process.
The script is here:`python/analysis/TreeProducerTauNu.py`

##TreeProducerMuNu
This module inherits from TreeProducerHighPT and it's meant to create ntuples (ROOT files) for the W*->mu nu process.
The script is here:`python/analysis/TreeProducerMuNu.py`

##TreeProducerWJ
This module inherits from TreeProducerHighPT and it's meant to create ntuples (ROOT files) for the W(->mu+v)+1jet process.
The script is here:`python/analysis/TreeProducerWJ.py`

##TreeProducerDiJet
This module inherits from TreeProducerHighPT and it's meant to create ntuples (ROOT files) for the dijet events.
The script is here:`python/analysis/TreeProducerDijet.py`

## Check your configuration
`PicoProducer` relies on an user configuration file. 
Please, have a look at the [Configuration section](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Configuration) to set up your configuration.
To check your setup use:
```
pico.py list
```
We recommend choosing output directories (`nanodir` and `picodir`) in larger storage areas like EOS/d-cache, afs might not have sufficient space.
Setup your [channel](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Skimming) and your [analysis](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#analysis) for the tau ID efficiency and ES SFs measurement at high pt:
```
pico.py channel munu HighPT.ModuleMuNu
```
pico.py channel taunu HighPT.ModuleTauNu
```
To link an era to your preferred sample list in `samples/HighPT`, do:
```
pico.py era 2018 HighPT/samples_UL2018.py
```

## Selection of MC and Data samples
Samples for the analysis of the tau ID efficiency and ES SFs measurement at high pt should be stored inside `samples/HighPT/`. They can be copied from the folder `samples` and modified in order to run only on needed MC and datasets. The samples I ran the code on are here: `/eos/user/a/acardini/samples/HighPT/nano/2018`.

## Creating ntuples 
Ntuples can be created by running locally or submitting jobs to a batch system.
Before running we recommend testing the setup by performing a local run as mentioned in the `README` of `PicoProducer`: [Local run](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Local-run).
After the outputs have been investigated, the full analysis can be run using the [Batch submission](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Batch-submission).
A script named `Submitter.sh` has been created to launch job submission of different eras and for different systematic variations simultaneously.
Execute with `./Submitter.sh ERA` for UL datasets the convention is to use the following names: UL2018, UL2017, UL2016_preVFP, UL2016_postVFP
Use the commands `pico.py status -y ERA -c munu` and `pico.py resubmit -y ERA -c munu` jobs (see [Batch submission](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Batch-submission)).

## Hadd analysis output 
After all jobs have successfully finished ROOT files from analysis output can be `hadd`-ed into one large pico file (see [Finalize](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Finalize))
The script named `Hadder.sh` has been created to `hadd` different ROOT files for one era.
Execute with `./Hadder.sh ERA` for UL datasets the convention is to use the following names: UL2018, UL2017, UL2016_preVFP, UL2016_postVFP
