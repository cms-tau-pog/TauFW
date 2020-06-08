# PicoProducer

This setup run the [post-processors](https://github.com/cms-nanoAOD/nanoAOD-tools) on nanoAOD.
There are two modes:
1. **Skimming**: Skim nanoAOD by removing [unneeded branches](https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/processors/keep_and_drop_skim.txt),
                 bad data events (using [data certification JSONs](data/json)),
                 add things like JetMET corrections. Output is still of the nanoAOD format.
2. **Analysis**: Main analysis code in [`python/analysis/`](python/analysis),
                 pre-selecting events and objects and constructing variables.
                 The output is a custom tree format we will refer to as _pico_.

#### Table of Contents  
* [Installation](#Installation)<br>
* [Configuration](#Configuration)<br>
  * [Skimming](#Skimming)
  * [Analysis](#Analysis)
  * [Sample list](#Sample-list)
* [Samples](#Samples)<br>
* [Local run](#Local-run)<br>
* [Batch submission](#Batch-submission)<br>
  * [Submission](#Submission)
  * [Resubmission](#Resubmission)
  * [Finalize](#Finalize)
* [Plug-ins](#Plug-ins)<br>


## Installation

See [the README in the parent directory](../../../#taufw). Test the installation with
```
pico.py --help
```
To use DAS, make sure you have a GRID certificate installed, and a VOMS proxy setup
```
voms-proxy-init -voms cms -valid 200:0
```
or use the script
```
source utils/setupVOMS.sh
```


## Configuration

The user configuration is saved in [`config/config.json`](config/config.json).
You can manually edit the file, or set some variable with
<pre>
pico.py set <i>&lt;variables&gt; &lt;value&gt;</i>
</pre>
The configurable variables include
* `batch`: Batch system to use (e.g. `HTCondor`)
* `jobdir`: Directory to output job configuration and log files (e.g. `output/$ERA/$CHANNEL/$SAMPLE`)
* `nanodir`: Directory to store the output nanoAOD files from skimming jobs.
* `outdir`: Directory to copy the output pico files from analysis jobs.
* `picodir`: Directory to store the `hadd`'ed pico file from analysis job output.
* `nfilesperjob`: Default number of files per job.

Defaults are given in [`config/config.json`](config/config.json).
Note the directories can contain variables with `$` like
`$ERA`, `$CHANNEL`, `$CHANNEL`, `$TAG`, `$SAMPLE`, `$GROUP` and `$PATH`
to create a custom hierarchy and format.

### Skimming
Channels with `skim` in the name are reserved for skimming.
Link your skimming channel with a post-processor in [`python/processors/`](python/processors) with
```
pico.py channel skim skimjob.py
```
An example is given in [`skimjob.py`](python/processors/skimjob.py).

### Analysis
To link a channel short name (e.g. `mutau`) to an analysis module
in [`python/analysis/`](python/analysis), do
```
pico.py channel mutau ModuleMuTau.py
```
An simple example of an analysis is given in [`ModuleMuTauSimple.py`](python/analysis/ModuleMuTauSimple.py).
All analysis modules are run by `pico.py` with the post-processor [`picojob.py`](python/processors/skimjob.py).

### Sample list
To link an era to your favorite sample list in [`samples/`](samples/), do
```
pico.py era 2016 sample_2016.py
```


## Samples

Specify the samples with a python file in [`samples/`](samples).
The file must include a python list called `samples`, containing `Sample` objects
(or those from the derived `MC` and `Data` classes). For example,
```
samples = [
  Sample('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext1-v1/NANOAODSIM",
    dtype='mc',store=None,url="root://cms-xrd-global.cern.ch/",
  )
]
```
The `Samples` class takes at least three arguments:
1. The first string is a user-chosen name to group samples together (e.g. `DY`, `TT`, `VV`, `Data`, ...).
2. The second is a custom short name for the sample  (e.g. `DYJetsToLL_M-50`, `SingleMuon_Run2016C`). 
3. The third (and optionally additional) argument are the full DAS paths of the sample.
Multiple DAS paths for the same sample can be used for extensions.

Other optional keyword arguments are
* `dtype`: Data type like `mc`, `data` or `embed`. As a short cut you can use the subclasses `MC` and `Data`.
* `store`: Path where all nanoAOD files are stored (instead of being given by DAS). This is useful if you skimmed your samples.
  The path may contain variables like `$PATH` for the full DAS path, `$GROUP` for the group, `$SAMPLE` for the sample short name.
* `url`: Redirector URL for XRootD protocol, e.g. `root://cms-xrd-global.cern.ch` for DAS.
* `files`: Either a list of files, OR a string to a text file with a list of files.
  This can speed things up if DAS is slow or unreliable.
* `nfilesperjob`: Number filed per job. If the samples is split in many small files,
  you can choose a larger `nfilesperjob` to reduce the number of short jobs.
* `blacklist`: A list of files that you do not want to run on. This is useful if some files are corrupted.

To get a file list for a sample in the sample list, you can use the `get files` subcommand,
and with `--write`, you can write it to a text file:
```
pico.py get files -y 2016 -s DYJets --write
```

## Local run
A local run can be done as
```
pico.py run -y 2016 -c mutau
```
You can specify a sample that is available in [`samples/`](samples), by passing the `-s` flag a pattern as
```
pico.py run -y 2016 -c mutau -s 'DYJets*M-50'
pico.py run -y 2016 -c mutau -s SingleMuon
```


## Batch submission

### Submission
Once configured, submit with
```
pico.py submit -y 2016 -c mutau
```
This will create the the necessary output directories for job out put.
A JSON file is created to keep track of the job input and output.

You can specify a sample by a patterns to `-s`, or exclude patterns with `-x`. Glob patterns like `*` wildcards are allowed.
To give the output files a specific tag, use `-t`.

For all options with submission, do
```
pico.py submit --help
```


### Status
Check the job status with
```
pico.py status -y 2016 -c mutau
```

### Resubmission
If jobs failed, you can resubmit with
```
pico.py resubmit -y 2016 -c mutau
```

### Finalize
ROOT files from analysis output can be `hadd`'ed into one pico file:
```
pico.py hadd -y 2016 -c mutau
```
This will not work for channels with `skim` in the name,
as it is preferred to keep skimmed nanoAOD files split for batch submission.



## Plug-ins

To plug in your own batch system, make a subclass [`BatchSystem`](python/batch/BatchSystem.py)
overriding the abstract methods (e.g. `submit`).
Your subclass has to be saved in separate python module in [`python/batch`](python/batch),
and the module's filename should be the same as the class. See for example [`HTCondor.py`](python/batch/HTCondor.py).

Similarly for a storage element, subclass [`StorageSystem`](python/storage/StorageSystem.py).
