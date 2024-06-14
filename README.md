# TauFW


## What is the TauFW ?
The TauFW is a framework developed for analysis of nanoAOD at CMS.
The original purpose was to have a common framework for the TauPOG measurements in CMS that can run on common nanoAOD samples, and keep track of the scripts in this repository.

## How do I install the TauFW ?
Please see [the Installation page](Installation).

## Where do I start?
Please have a look at our tutorial on lxplus: [Quick start with TauFW](Quick-start-with-TauFW)

## What does the TauFW offer ?
Three main packages are
1. [`PicoProducer`](../tree/master/PicoProducer):
   * Tools to run analysis code on nanoAOD for given lists of nanoAOD files.
   * Examples of ditau analysis code.
   * Tools to read & apply corrections in analyses (in particular for tau analysis at CMS).
   * Tools to keep track of nanoAOD samples stored on the GRID or other storage elements.
   * Tools to submit jobs to various batch systems. You can add your custom batch system as a module. 
   * Tools to access various storage elements. You can add your custom storage system as a module.
2. [`Plotter`](../tree/master/Plotter):
   * Tools to plot histograms and data/MC comparisons in CMS style.
   * Tools to handle sets of samples and produces histograms (`TH1`) from analysis ntuples (`TTree`).
   * Tools for further analysis, auxiliary measurements, validation...
3. [`Fitter`](../tree/master/Fitter):
   * Tools for measurements and fits in combine.
   * [Under development.]

## More information
Please find the latest information in [these wiki pages](https://github.com/cms-tau-pog/TauFW/wiki)!
