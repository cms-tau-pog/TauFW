# Author: Izaak Neutelings (November 2018)
import os, re
from TauFW.PicoProducer import datadir
from TauFW.common.tools.root import ensureTFile
from TauFW.common.tools.log import Logger
datadir = os.path.join(datadir,"jetveto")
LOG     = Logger('JetVetoMapTool',showname=True)


class JetVetoMapTool:
  
  def __init__(self, era, verb=0):
    """Load data and MC jetveto map profiles."""
    
    self.file = None
    self.era = era
    if re.search('2022[C-D]', era):
      filename = os.path.join(datadir,"Summer22_23Sep2023_RunCD_v1.root")
    elif re.search('2022[E-G]', era):
      filename = os.path.join(datadir,"Summer22EE_23Sep2023_RunEFG_v1.root")
    elif '2023C' in era:
      filename = os.path.join(datadir,"Summer23Prompt23_RunC_v1.root")
    elif '2023D' in era:
      filename = os.path.join(datadir,"Summer23BPixPrompt23_RunD_v1.root")
    else:
      LOG.throw(OSError,"Did not recognize era=%r..."%(era))
    self.file = ensureTFile(filename, 'READ')
    self.hist = self.file.Get('jetvetomap')
    
  def applyJetVetoMap(self,eta,phi):
    """Get eta phi region where jetveto needs to be applied"""
    if self.file == None:
       LOG.warning(f"JetVetoMapTools.applyJetVetoMap: either Jet veto is not applicable for {era} or jet veto file is not defined")
       return False
    else:
       apply_jetveto = self.hist.GetBinContent(self.hist.GetXaxis().FindBin(eta), self.hist.GetYaxis().FindBin(phi))
       return apply_jetveto
