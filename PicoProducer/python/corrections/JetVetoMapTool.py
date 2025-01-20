# Author: Saswati Nandan & Izaak Neutelings (April 2024)
# https://cms-jerc.web.cern.ch/Recommendations/#jet-veto-maps
import os, re
from TauFW.PicoProducer import datadir
from TauFW.common.tools.root import ensureTFile
from TauFW.common.tools.log import Logger
datadir = os.path.join(datadir,"jetveto")
LOG     = Logger('JetVetoMapTool',showname=True)


class JetVetoMapTool:
  
  def __init__(self, era, verb=1):
    """Load data and MC jetveto map profiles."""
    filename = None
    if re.search(r"2022([C-D]|.*pre)",era):
      filename = os.path.join(datadir,"Summer22_23Sep2023_RunCD_v1.root")
    elif re.search(r"2022([E-G]|.*post)",era):
      filename = os.path.join(datadir,"Summer22EE_23Sep2023_RunEFG_v1.root")
    elif re.search(r"2023(C|.*pre)",era):
      filename = os.path.join(datadir,"Summer23Prompt23_RunC_v1.root")
    elif re.search(r"2023(D|.*post)",era) or re.search(r"2024", era):
      filename = os.path.join(datadir,"Summer23BPixPrompt23_RunD_v1.root")
    if not filename:
      LOG.throw(OSError,"Did not recognize era=%r... Note: Only mandatory in Run 3,"
                        " please see https://cms-jerc.web.cern.ch/Recommendations/#jet-veto-maps"%(era))
    if verb>=1:
      print("Loading jet veto maps for era %r from %s..."%(era,filename))
    self.era  = era
    self.file = ensureTFile(filename, 'READ')
    self.hist = self.file.Get('jetvetomap')
    self.hist.SetDirectory(0) # load into memory, so we can safely close the file
    self.file.Close()
    
  def applyJetVetoMap(self,eta,phi):
    """Get eta phi region where jetveto needs to be applied"""
    return self.hist.GetBinContent(self.hist.GetXaxis().FindBin(eta), self.hist.GetYaxis().FindBin(phi))
