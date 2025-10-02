# Measuring Z pT reweighting

This module includes some tools to derive the Z pT reweighting in dimuon events for LO Drell-Yan samples.

Two techniques to take into account the resolution are available:
* `measureZpt.py` using unfolding from reconstructed dimuon pT (and mass) to generator-level Z pT (and mass) using `RooUnfold`.
* `measureZpt_average.py` derives weights by first comparing reconstructed dimuon distribution in data and MC, and then simply averaging those weights as a function of Z pT.

This measurement was presented in [this Tau ID meeting](https://indico.cern.ch/event/1048446/#10-z-pt-reweighting-in-ul).

## Installation
Install the `TauFW` as usual.
Create analysis tuples for the dimuon analysis, e.g.
```
cd PicoProducer
pico.py era 2018 samples/samples_2018.py
pico.py channel mumu python/analysis/ModuleMuMu.py
pico.py run -c mumu -y 2018 -s DY
pico.py submit -c mumu -y 2018
pico.py status -c mumu -y 2018
pico.py hadd -c mumu -y 2018
```
Once you have a complete set of dimuon tuples for data and MC, edit `config/sample.py` to set the correct sample names and tuple paths.

If you want to use unfolding, install [`RooUnfold`](https://gitlab.cern.ch/RooUnfold/RooUnfold):
```
git clone https://gitlab.cern.ch/RooUnfold/RooUnfold.git
cd RooUnfold
make
```


## Unfolding 2D
The script `measureZpt.py` can do unfolding for the reconstructed dimuon pT and mass distribution to generator-level Z pT and mass.
It does so by "unrolling" the 2D histogram to a 1D one using the [`Unroll.cxx` macro](../../Plotter/python/macros/Unroll.cxx).


## Application
To apply the Z pT reweighting on the fly, please use the [`weights/zptweight.C` macro](weights/zptweight.C).
```
from ROOT import gROOT
gROOT.Macro('weights/zptweight.C+')
from ROOT import loadZptWeights
loadZptWeights("weights/zptmass_weight_2017.root",'zpt_weight') # load histogram from histogram
tree.Draw("pt_mumu >> h","(pt_1>20 && pt_2>30)*getZptWeight(Zpt)",'gOff')
```
Or to apply during the processing of nanoAOD Drell-Yan, please have a look at
[`PicoProducer/python/corrections/README.md`](../../PicoProducer/python/corrections/#Z-pT-reweighting) and
[`PicoProducer/python/corrections/RecoilCorrectionTool.py`](../../PicoProducer/python/corrections/RecoilCorrectionTool.py).
