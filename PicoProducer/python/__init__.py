# Author: Izaak Neutelings (May 2020)
import os
if 'CMSSW_BASE' in os.environ: # look for $CMSSW_BASE/src/TauFW/PicoProducer
  basedir = os.path.join(os.environ['CMSSW_BASE'],"src/TauFW/PicoProducer")
else: # expand symlink
  basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
assert os.path.exists(basedir), f"Could not parse PicoProducer's basedir={basedir}"
datadir = os.path.join(basedir,'data')
