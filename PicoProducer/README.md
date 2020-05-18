# PicoProducer


## Installation

See [the README.md in the parent directory](../../../#taufw). Test the installation with
```
pico.py --help
```


## Configuration

The user configuration is saved in `config/config.json`.
You can manually edit the file, or set some variable as
```
pico.py set batch HTCondor
```
To link a channel short name (e.g. `mutau`) to an analysis module (e.g. `ModuleMuTau.py`)
in [`python/modules`](python/modules), do
```
pico.py channel mutau ModuleMuTau.py
```
To link an era to your favorite sample list in [`samples/`](samples/), do
```
pico.py era 2018 sample_2018.py
```


## Plug-ins

To plug in your own batch system, make a subclass [`BatchSystem`](python/batch/BatchSystem.py),
overriding the abstract methods (e.g. `submit`).
Your subclass has to be saved in separate python module in [`python/batch`](python/batch),
and the filename should be the same as the class. See for example [`HTCondor`](python/batch/HTCondor.py).

Similarly for a storage element, subclass [`StorageSystem`](python/batch/StorageSystem.py).


## Samples

Specify the samples with a python file in [`samples`](samples).
The file must include a python list `samples`, containing `Sample` objects
(or those from the derived `MC` and `Data` classes).


## Batch submission

### Submission
Once configured, submit with
```
pico.py submit -y 2018 -c mutau
```
This will create the the necessary output directories for job out put.
A JSON file is created to keep track of the job input and output.


### Status
Check the status with
```
pico.py status -y 2018 -c mutau
```


### Resubmission
If jobs failed, you can resubmit with
```
pico.py resubmit -y 2018 -c mutau
```


### Finalize
ROOT files from analysis output can be hadd'ed into one file:
```
pico.py hadd -y 2018 -c mutau
```

