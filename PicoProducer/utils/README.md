# PicoProducer utility scripts

Some extra scripts for common tasks.


## [`setupVOMS.sh`](setupVOMS.sh)
Checks if VOMS proxy is still valid for at least 10 hours.
If not, it will create a new one for 200 hours. Otherwise, it will print the time left.
```
utils/setupVOMS.sh
utils/setupVOMS.sh -m 10 -t 200
```


## [`getDASParents.py`](getDASParents.py)
Trace back lineage of one or more DAS datasets to figure out if they have common ancestors, e.g.
```
utils/getDASParents.py /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17*/NANOAODSIM
utils/getDASParents.py /W1JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6*/NANOAODSIM
utils/getDASParents.py /Tau/Run2018D*/NANOAOD
```


## [`getNanoAODDatasets.sh`](getNanoAODDatasets.sh)
Get all the nanoAOD datasets for a certain campaign of our favorite list of samples.
You can edit the default sample list and campaign in the script itself, or run with flags:
```
utils/getNanoAODDatasets.sh
utils/getNanoAODDatasets.sh -y 17 -m DY*JetsToLL_M-50_TuneC*
utils/getNanoAODDatasets.sh -y 17 -d SingleMuon
```


## [`check2017BuggedPU.sh`](check2017BuggedPU.sh)
Check if a 2017 MC sample came from a sample with a buggy PU mixer based on `/afs/cern.ch/user/g/gurpreet/public/Fall17_oldPU.txt`:
```
utils/check2017BuggedPU.sh 
```
For more info, see 
* https://hypernews.cern.ch/HyperNews/CMS/get/generators/4060.html?inline=-1
* https://hypernews.cern.ch/HyperNews/CMS/get/physics-validation/3128.html


## [`compareNano.py`](compareNano.py)
Quickly compare two or more variables in the tree of one or more ROOT files (added in a `TChain`).
For example for nanoAOD files, simply use
```
 ./utils/compareNano.py nano*.root -V "Jet_pt_nom,Jet_pt_jerUp,Jet_pt_jerDown>>20,0,200" -v3
```

## [`comparePico.py`](comparePico.py)
Quickly compare two or more pico files by creating plots of some variables.
Edit the file to change or add more variables:
```
utils/comparePico.py pico1.root pico2.root
```

