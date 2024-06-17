#! /usr/bin/env python
# Example of how to read the tau JSON file
# For more information, see the README in
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/TAU
#import sys; sys.path.insert(0,"correctionlib") # add correctionlib to path
from correctionlib import _core

# Load CorrectionSet
fname = "../POG/TAU/2018_ReReco/tau.json.gz"
if fname.endswith(".json.gz"):
  import gzip
  with gzip.open(fname,'rt') as file:
    #data = json.load(file)
    data = file.read().strip()
  cset = _core.CorrectionSet.from_string(data)
else:
  cset = _core.CorrectionSet.from_file(fname)

# Load Correction objects that can be evaluated
corr1 = cset["DeepTau2017v2p1VSjet"]
corr2 = cset["DeepTau2017v2p1VSe"]
corr3 = cset["tau_trigger"]
corr4 = cset["tau_energy_scale"]
pt, eta, dm, genmatch = 25., 1.0, 0, 5
wp, syst = "Tight", "nom"
print('-'*50)
print("fname=%r"%fname)
print("pt=%.2f, eta=%.1f, dm=%d"%(pt,eta,dm))
print("wp=%r, syst=%r"%(wp,wp))
print('-'*50)

# DeepTau2017v2p1VSjet
sf1 = corr1.evaluate(pt,dm,1,wp,"nom","pt")
sf2 = corr1.evaluate(pt,dm,5,wp,"nom","pt")
print("DeepTau2017v2p1VSjet sf=%.2f (genmatch=1)"%sf1)
print("DeepTau2017v2p1VSjet sf=%.2f (genmatch=5)"%sf2)

# DeepTau2017v2p1VSe
sf3 = corr2.evaluate(eta,1,wp,syst)
sf4 = corr2.evaluate(eta,5,wp,syst)
print("DeepTau2017v2p1VSe sf=%.2f (genmatch=1)"%sf3)
print("DeepTau2017v2p1VSe sf=%.2f (genmatch=5)"%sf4)

# etau trigger
sf5 = corr3.evaluate(pt,dm,"etau",wp,"sf",syst)
print("etau trigger sf=%.2f"%sf5)

# tau energy scale
tes1 = corr4.evaluate(pt,eta,dm,1,"DeepTau2017v2p1",syst)
tes2 = corr4.evaluate(pt,eta,dm,5,"DeepTau2017v2p1",syst)
print("tes=%.2f (genmatch=1)"%tes1)
print("tes=%.2f (genmatch=5)"%tes2)
print('-'*50)
