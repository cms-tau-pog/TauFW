# Jet To Tau FakeRate measurements
Last update : 26 July 2022
Author      : Konstantinos Christoforou


### Table of Contents  
* [General Idea](#General-Idea)<br>
* [Scripts and tools](#Scripts-and-Tools)<br>
  * [plot_forTauFR.py](#plot_forTauFR)<br>
  * [plotJetToTauFRvariables_writeJson.py](#plotJetToTauFRvariables_writeJson)<br>
  * [plotJetToTauFRvariables_writeJson_FRinPtBins.py](#plotJetToTauFRvariables_writeJson_FRinPtBins)<br>
  * [readAndPlotFR.py](#readAndPlotFR)<br>
  * [JetToTau_MisID.py](#JetToTau_MisID)<br>
  * [tools](#tools)
* [Workflow](#Workflow)

## General Idea
All scripts and tools needed for perfoming Jet to Tau Fake Rate measurements are included in this folder.
The goal of these measurements is to measure and compare the fake rate probability for a given jet
faking a tau in both Data and MC.  In order to proceed with the FR measurements and plotting, one should
first produce the dedicated pico tuple, using the analyzers in 
['JetTauFakeRate'](../../../../PicoProducer/python/analysis/JetTauFakeRate).

## Scripts and tools

### plot_forTauFR
A simple script for plotting basic distributions and comparing Data/MC.
This script was based on the original ['plot.py'](../../../plot.py).
An important addition was the Closure option (-C) but this works
only after the whole "Jet To Tau FakeRate measurement" has been performed
and the corresponding json file with the FRs exist.

Closure tests should performed for FRs in order to validate them.  Closure plots
are stored under "plots/<era>/<finalstate>/Closure".

### plotJetToTauFRvariables_writeJson
The measurement of the Jet to Tau FRs is performed in this script.  FRs
are calculated in pT-eta bins of the jet that serves as tau-candidate.
After the caclulation of the FRs, everything is stored in a json file named as
"TauFakeRate_<era>_<finalstate>.json" under "plots/<era>/<finalstate>/TauFakeRate_<era>_<finalstate>" directory that
is automatically produced.  

Bug-to-be-fixed : The final-state-barrel key written in the json file looks like :
'''
mumettau__mumettau:Barrel
'''
and for the moment should manually change to :
'''
mumettau_Barrel
'''
Same for endcap.  

### plotJetToTauFRvariables_writeJson_FRinPtBins
Same as plotJetToTauFRvariables_writeJson.py but the FR are calculated in pT-only-bins.

Bug-to-be-fixed : If you want to use FRs in pT-only-bins, you should manually
change the "eta" list in both ['readAndPlotFR'](readAndPlotFR.py) and 
['JetToTau_MisID.py'](../../methods/JetToTau_MisID.py) to "eta = [""] "

### readAndPlotFR
This script reads and plots the FRs of a given directory.  It uses scripts mainly from the
['tools'](tools) folder and it produces a Data-MC FR comparison plots under "plots/<era>/<finalstate>/FakeRates".

### JetToTau_MisID
This script is located [here](../../methods/JetToTau_MisID.py) and is where FR method is been applied.

### tools
This folder contains a few helping scripts mainly for calculating and plotting Fake Rates.
These scripts were used for another analysis and there is a lot of cleaning to be done at some point.
Though, there are a lot of dependencies between them and is a kind of a maze so it would be a very
dedicated and time-consuming task.

### Workflow
Example for W+jets enriched region
'''
./plot_forTauFR.py -c mumettau --era UL2018 (Optional, just to monitor and reference)
./plotJetToTauFRvariables_writeJson.py -c mumettau --era UL2018
-> Fix the label in the json file, as explained above
./readAndPlotFR.py --yMin 0.0 --yMax 0.5 --saveDir plots/UL2018/mumettau/FakeRates --ratio --bandValue 30 --dirs plots/UL2018/mumettau/TauFakeRate_UL2018_mumettau,plots/UL2018/mumettau/TauFakeRate_UL2018_mumettau --analysisType mumettau
./plot_forTauFR.py -c mumettau --era UL2018 -C

