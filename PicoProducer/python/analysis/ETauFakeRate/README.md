#PicoProducer
This README is intended to give instructions on how create ntuples for the etau Fake Rate measurement.

##Before start
The etau Fake Rate analysis module inherits from other modules defined in `PicoProducer`.
All information provided here assume that one has already looked at [the README.md in the parent directory](https://github.com/cms-tau-pog/TauFW/#taufw).

## Check your configuration
`PicoProducer` relies on an user configuration file. 
Please, have a look at the [Configuration section](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Configuration) to set up your configuration.
To check your setup use:
```
pico.py list
```
We recommend choosing output directories (`nanodir` and `picodir`) in larger storage areas like EOS/d-cache, afs might not have sufficient space.
Setup your [channel](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Skimming) and your [analysis](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#analysis) for the etau Fake Rate measurement:
```
pico.py channel etau ETauFakeRate.ModuleETau
```
To link an era to your preferred sample list in `samples/ETauFakeRate`, do:
```
pico.py era UL2017 ETauFakeRate/samples_UL2017.py
```

## Selection of MC and Data samples
Samples for the analysis of the etau FR should be stored inside `samples/ETauFakeRate/`. They can be copied from the folder `samples` and modified in order to run only on needed MC and datasets.

## Event Selection
Event selection and skimming is performed by the script `python/analysis/ETauFakeRate/ModuleETau.py`.

## Creating ntuples 
Ntuples can be created by running locally or submitting jobs to a batch system.
Before running we recommend testing the setup by performing a local run as mentioned in the `README` of `PicoProducer`: [Local run](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Local-run).
After the outputs have been investigated, the full analysis can be run using the [Batch submission](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Batch-submission).
A script named `Submitter.sh` has been created to launch job submission of different eras and for different systematic variations simultaneously.
Execute with `./Submitter.sh ERA` for UL datasets the convention is to use the following names: UL2018, UL2017, UL2016_preVFP, UL2016_postVFP
Use the commands `pico.py status -y ERA -c etau` and `pico.py resubmit -y ERA -c etau` jobs (see [Batch submission](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Batch-submission)).

## Hadd analysis output 
After all jobs have successfully finished ROOT files from analysis output can be `hadd`-ed into one large pico file (see [Finalize](https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Finalize))
The script named `Hadder.sh` has been created to `hadd` different ROOT files for one era.
Execute with `./Hadder.sh ERA` for UL datasets the convention is to use the following names: UL2018, UL2017, UL2016_preVFP, UL2016_postVFP
