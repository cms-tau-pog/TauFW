# jsonPOG-integration

 [![pipeline status](https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/badges/master/pipeline.svg)](https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/commits/master) 

## Instructions for users

The `correctionlib` library needed to read the files from python or C++ lives on [github](https://github.com/cms-nanoAOD/correctionlib), see
its [documentation](https://cms-nanoaod.github.io/correctionlib/) for installation and usage instructions.

Some examples on how to the read the files are provided here in the [examples](./examples/) folder.
Also see [these examples](https://gist.github.com/pieterdavid/a560e65658386d70a1720cb5afe4d3e9) for how to use the library from a ROOT::RDataFrame application.

The latest files from the `master` branch from the [main project](https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration)
are synced once a day to CVMFS at: `/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration`  (through [CMSSDT Jenkins](https://cmssdt.cern.ch/jenkins/job/cvmfs-cms-rsync-gitlab-repo/) )

The content of all the available files is summarized on [this webpage](https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/).

Inspecting the files manually can also be done using the command `correction summary file.json`.

## Instructions for POGs to add corrections

### [POG](./POG/) folder in the repository

In this folder we store all the corrections.
Each physics object has a separate json file, and each POG has a folder for storage.

| directory  | year_campaign | name.json |
| ---------- | --------------| ----------|
| POG/EGM  | "X_Y"  | photon.json |
|          |  "" | electron.json |
| POG/TAU  |  "" | tau.json |
| POG/MUON |  "" | muon.json |
| POG/JME  |  "" | fatJetPuppi.json |
|          |  "" | jetCHS.json |
| POG/BTV  |  "" | btagging.json |
|          |  "" | ctagging.json |
|          |  "" | subjet_tagging.json |
| POG/LUM  |  "" | puWeights.json | 

To be taken care of:
1. different campaings are organized in folders with label "X_Y" i.e. (2016preVFP_UL, 2016postVFP_UL, 2017_UL, 2018_UL, 2018_EOY...)
2. each physics object in nanoAOD gets a separate json
3. the "inputs" labels should be unique and standardized, please have a look at the existing files
4. store the json in .gz format for compression
5. when changing the content of an existing correction (same name), make sure you increase its version number
6. for systematic variations, until they are [better supported in correctionlib](https://github.com/cms-nanoAOD/correctionlib/issues/4),
please provide both the nominal and *up/down variations* of the corrections, not the uncertainties themselves.

### Before making a merge request

* Configure the forked project from which you will be making a merge request, to properly run the test scripts:
  * Create a project access token in the forked repository *Settings > Access Tokens*: create a token with `Reporter` rights and `api` scope
  * Copy the token to a CI variable named `GITLAB_API_TOKEN` under the repository *Settings > CI/CD > Variables*
* Make sure you have rebased your branch on top of the latest `master` branch from the [main project](https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration)
* Validate the files you have added or modified using `correction validate file.json`

### Automatic tests

Once a merge request is made, if the above has been done, the automatic tests will run.
The tests will happen with the script defined [here](./script/testMR.sh).
Goal of the test:
* verify that the files are compliant to the JSON schema ([currently v2](https://cms-nanoaod.github.io/correctionlib/schemav2.html)).
* produce a summary to inspect the content of new files
* for modified files, produce a summary of the changes, and verify that corrections whose content changes have their version number increased.
