# Tau long exercise for the 2020 CMSDAS

After having performed the [short exercises](https://github.com/CMSDAS/tau-short-exercise), you have learned how hadronic &tau;
lepton decays are reconstructed and discriminated against jets, electrons and muons at CMS.

The main target of this Tau long exercise is to make you familiar with the general procedure and aspects of an analysis from front to end,
using the measurement of the Z to &tau;&tau; cross-section as an example.

This exercise is based on the [TauFW](https://github.com/cms-tau-pog/TauFW) analysis framework and builds upon 2018 NanoAOD datasets.
The statistical inference is performed with [CombinedLimit](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit),
[CombineHarvester](https://github.com/cms-analysis/CombineHarvester), and analysis-specific package [CMSDAS2020TauLong](https://github.com/ArturAkh/CMSDAS2020TauLong).

After this exercise you will learn, how to:

 + apply selection to preselected NanoAOD samples to produce flat n-tuples, maybe also create preselected NanoAOD yourself,
 + estimate QCD multi-jet background to the Z to &tau;&tau; selection in a data-driven way,
 + normalize your expected backgrounds and signals to match the events collected in data,
 + create control plots of various quantities calculated in the flat n-tuples,
 + apply corrections to the expected contributions to improve agreement between data and expectation,
 + refine selection requirements to enrich Z to &tau;&tau;,
 + make a simple estimate of energy scale corrections and uncertainties for hadronic &tau; leptons,
 + create histograms in one inclusive category for statistical inference,
 + extend categorization by splitting the inclusive phase space with appropriate variables,
 + introduce normalization and shape uncertainties to the uncertainty model for the Z to &tau;&tau; cross-section measurement,
 + and calculate and plot the best-estimate for the cross-section.

To start with the exercise, please navigate through the linked sections found in the list below:

 + [Setting up the analysis software](sw_setup.md)
 + [Initial analysis configuration](configuration.md)
 + [Preselecting NanoAOD](preselection.md)
 + [Creating flat n-tuples](flat_n-tuples.md)
