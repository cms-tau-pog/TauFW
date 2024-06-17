#! /usr/bin/env python
# Example of how to read the tau JSON file
# For more information, see the README in
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/JME
from correctionlib import _core

# Load CorrectionSet
fname = "../POG/JME/2017_EOY/2017_jmar.json.gz"
if fname.endswith(".json.gz"):
    import gzip
    with gzip.open(fname,'rt') as file:
        data = file.read().strip()
        evaluator = _core.CorrectionSet.from_string(data)
else:
    evaluator = _core.CorrectionSet.from_file(fname)


##### DeepAK8/ParticleNet tagging
eta, pt, syst, wp = 2.0,450.,"nom","0p1"
map_name = "ParticleNet_Top_Nominal"
valsf= evaluator[map_name].evaluate(eta, pt, syst, wp)
print("Example for "+map_name)
print("The "+syst+" SF for a Jet with pt="+str(pt) + " GeV and eta="+str(eta) + " for a misidentification rate of "+wp+" is "+str(valsf))

##### cut-based top tagging
eta, pt, syst, wp = 2.0,450.,"nom","wp1"
map_name = "Top_tagging_PUPPI_mergedTop"
valsf= evaluator[map_name].evaluate(eta, pt, syst, wp)
print("Example for "+map_name)
print("The "+syst+" SF for a Jet with pt="+str(pt) + " GeV and eta="+str(eta) + " for the "+wp+" working point is "+str(valsf))

##### cut-based W tagging
eta, pt, syst, wp = 2.0,450.,"nom","2017HP43DDT"
map_name = "Wtagging_2017HP43DDT"
valsf= evaluator[map_name].evaluate(eta, pt, syst, wp)
print("Example for "+map_name)
print("The "+syst+" SF for a Jet with pt="+str(pt) + " GeV and eta="+str(eta) + " for the "+wp+" working point is "+str(valsf))


##### soft drop mass correction
eta, pt, syst = 1.0,200.,"nom"
map_name = "JMS"
valsf= evaluator[map_name].evaluate(eta, pt, syst)
print("Example for "+map_name)
print("The "+syst+" SF for a Jet with pt="+str(pt) + " GeV and eta="+str(eta) + " is "+str(valsf))

##### PU JetID
eta, pt, syst, wp = 2.0,20.,"nom","L"
map_name = "PUJetID_eff"
valsf= evaluator[map_name].evaluate(eta, pt, syst, wp)
print("Example for "+map_name)
print("The "+syst+" SF for a Jet with pt="+str(pt) + " GeV and eta="+str(eta) + " for the "+wp+" working point is "+str(valsf))

##### Quark-Gluon tagging
eta, pt, syst, discriminator_value = 1.0,20.,"nom",0.5
map_name = "Gluon_Pythia"
valsf= evaluator[map_name].evaluate(eta, pt, syst, discriminator_value)
print("Example for "+map_name)
print("The "+syst+" SF for a Jet with pt="+str(pt) + " GeV and eta="+str(eta) + " for a discriminator value of "+str(discriminator_value)+" is "+str(valsf))
