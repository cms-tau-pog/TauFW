#! /usr/bin/env python3
# Author: Izaak Neutelings (October, 2020)
# Description: Simple standalone coffea analysis from official tutorial
# Sources:
#   source /cvmfs/sft.cern.ch/lcg/views/LCG_96python3/x86_64-centos7-gcc8-opt/setup.sh
#   https://coffeateam.github.io/coffea/notebooks/nanoevents.html#Using-NanoEvents-with-a-processor
import os, sys
import time; time0 = time.time()
from coffea import processor, hist


##############
#   MODULE   #
##############

class MyZPeak(processor.ProcessorABC):
  def __init__(self):
    self._histo = hist.Hist(
        "Events",
        hist.Cat("dataset", "Dataset"),
        hist.Bin("mass", "Z mass", 60, 60, 120),
    )
  
  @property
  def accumulator(self):
    return self._histo
  
  # we will receive a NanoEvents instead of a coffea DataFrame
  def process(self, events):
    out = self.accumulator.identity()
    mmevents = events[events.Muon.counts==2]
    zmm = mmevents.Muon[:,0] + mmevents.Muon[:,1]
    out.fill(
        dataset=events.metadata["dataset"],
        mass=zmm.mass.flatten(),
    )
    return out
  
  def postprocess(self, accumulator):
    return accumulator
  
print(MyZPeak,type(MyZPeak),processor.ProcessorABC,isinstance(MyZPeak,processor.ProcessorABC),MyZPeak.__class__.__name__)


###############
#   PROCESS   #
###############

samples = {
  "DrellYan": ["https://github.com/CoffeaTeam/coffea/raw/master/tests/samples/nano_dy.root",]
}
result = processor.run_uproot_job(
  samples,"Events",MyZPeak(),processor.iterative_executor,{"nano": True},
)
print(">>> Done after %.1f seconds"%(time.time()-time0))
