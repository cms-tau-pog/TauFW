# PicoProducer analysis code

This modules are used to process nanoAOD for analysis. Analysis modules
1. **pre-select** events, e.g. events passing some trigger and containing a muon-tau pair;
2. **reconstruct** variables like invariant mass;
3. **apply corrections**, like energy scale, SFs, weights, etc;
3. **save variables** in branches of a custom tree.
The analysis modules are run on nanoAOD with the [post-processors](https://github.com/cms-nanoAOD/nanoAOD-tools),
for example with [`picojob.py`](../processors/skimjob.py).
The output is a custom analysis ntuple, we refer to as the _pico_ format.

#### Table of Contents  
* [Run](#Run)<br>
* [Subdirectories](#Subdirectories)<br>
* [Accessing nanoAOD](#Accessing-nanoAOD)<br>
* [Custom tree format](#Custom-tree-format)<br>
* [Cutflow](#Cutflow)<br>
* [Corrections](#Corrections)<br>


## Run
To run to an analysis module with `pico.py`, you can link the module to a channel shortname in several ways, e.g.
```
pico.py channel mutau ModuleMuTau
pico.py channel mutau python/analysis/ModuleMuTau.py
```
and then run it with e.g.
```
pico.py run -c mutau -y 2016
```
For more detailed instructions for `pico.py`, see the README in [the grandparent folder](../../README.md).


## Subdirectories
You can organize your modules in a subdirectory, e.g.
```
pico.py channel mutau TauID.ModuleMuTau
pico.py channel mutau python/analysis/TauID/ModuleMuTau_TauID.py
```


## Accessing nanoAOD
Please refer to the [nanoAOD documentation](https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html)
for a full list of available variables.
To know how they are defined from miniAOD, you can dig in the CMSSW source code in
[`cmssw/PhysicsTools/NanoAOD`](https://github.com/cms-sw/cmssw/tree/master/PhysicsTools/NanoAOD).

To access information of nanoAOD using python, you can subclass [`Module`](https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/eventloop.py)
from the [`nanoAOD-tools`](https://github.com/cms-nanoAOD/nanoAOD-tools):
```
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
class ModuleMuTauSimple(Module):
  def analyze(self,event):
    muon_idx = [ ]
    for imuon in event.nMuon:
      if event.Muon_pt[imuon]>20:
        muon_idx.append(imuon)
    return True
```
Without loss of performance, you can make the latter more readable using [`Collection`](https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/datamodel.py):
```
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
class ModuleMuTauSimple(Module):
  def analyze(self, event):
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt>20:
        muons.append(muon)
    return True
```
Triggers are saved as booleans, e.g.
```
    if not event.HLT_IsoMu24:
      return False
```
To save space, some identification working points (WPs) are saved in nanoAOD as `UChar_t`, which is 1 byte (8 bits),
instead of 4 bytes (64 bits) like `Int_t`. For example, to require the Medium WP of the `DeepTau2017v2p1VSjet` tau identification,
you see in the [documentation](https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#Tau)
that it corresponds to the fifth bit, i.e. `16`.
To access them in python, you may need the built-in functions `ord` or `int`, e.g.
```
    tau_idx = [ ]
    for itau in event.nTau:
    if event.Tau_pt[itau]>20 and ord(event.Tau_idDeepTau2017v2p1VSjet[itau])>=16:
      tau_idx.append(itau)
```
If you use `Collections`, you do not need `ord` anymore:
```
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if tau.pt>20 and tau.idDeepTau2017v2p1VSjet>=16:
        taus.append(tau)
```

## Custom tree format
A simple example to make your custom tree is given in [`ModuleMuTauSimple.py`](ModuleMuTauSimple.py). Reduced:
```
import numpy as np
class ModuleMuTauSimple(Module):
  def __init__(self,fname,**kwargs):
    self.outfile = TFile(fname,'RECREATE')
  def beginJob(self):
    self.tree = TTree('tree','tree')
    self.pt_1 = np.zeros(1,dtype=float) # float
    self.q_1  = np.zeros(1,dtype=int)   # integer
    self.id_1 = np.zeros(1,dtype=bool)  # boolean
    self.tree.Branch('pt_1',  self.pt_1,  'pt_1/F')
    self.tree.Branch('q_1',   self.q_1,   'q_1/I')
    self.tree.Branch('id_1',  self.id_1,  'id_1/O')
  def analyze(self, event):
    self.pt_1[0] = 20.0
    self.q_1[0]  = -1
    self.id_1[0] = True
    self.tree.Fill()
    return True
  def endJob(self):
    self.outfile.Write()
    self.outfile.Close()
```
To make your life easier, you can use separate "tree producer" classes.
For example, [`TreeProducerBase`](TreeProducerBase.py) can be subclassed as in [`TreeProducerMuTau.py`](TreeProducerMuTau.py).
You then define branches with something like
```
from TreeProducerTauPair import TreeProducerTauPair
class TreeProducerMuTau(TreeProducerBase):
  def __init__(self, filename, module, **kwargs):
    super(TreeProducerBase,self).__init__(filename,module,**kwargs)
    self.addBranch('pt_1',  'f') # float
    self.addBranch('q_1',   'i') # integer
    self.addBranch('medium','?') # boolean
```
In the main analysis module [`ModuleMuTau.py`](ModuleMuTau.py), you basically do
```
from TauFW.PicoProducer.analysis.TreeProducerMuTau import TreeProducerMuTau
class ModuleMuTau(Module):
  def __init__(self, fname, **kwargs):
    self.out = TreeProducerMuTau(fname,self)
  def analyze(self, event):
    self.out.pt_1[0]   = 20.0
    self.out.q_1[0]    = -1
    self.out.medium[0] = True
    self.out.fill()
    return True
```


## Cutflow
To keep track of efficiencies of each pre-selection, one should use a cuflow.
This is a simple histogram, binned per integer, that is filled each time a pre-selection is passed.
Again [`ModuleMuTauSimple.py`](ModuleMuTauSimple.py) provides a straightforward solution.

The [`TreeProducerBase`](TreeProducerBase.py) class already uses a special `Cutflow` class,
that can be used as
```
class ModuleMuTau(ModuleTauPair):
  def __init__(self, fname, **kwargs):
    self.out.cutflow.addcut('none',"no cut" )
    self.out.cutflow.addcut('trig',"trigger")
    self.out.cutflow.addcut('muon',"muon"   )
    self.out.cutflow.addcut('tau', "tau"    )
  def analyze(self, event):
    self.out.cutflow.fill('none')
    # require trigger...
    self.out.cutflow.fill('trig')
    # require muon...
    self.out.cutflow.fill('muon')
    # require tau...
    self.out.cutflow.fill('tau')
    # ...
```


## Corrections
Correction tools are found in [`python/corrections`](`../corrections`) and weights, scale factors and more in [`data`](../../data).

