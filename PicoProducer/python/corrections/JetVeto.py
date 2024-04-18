import ROOT as r 
import os

class JetVeto:

  def __init__(self,era):
    filename = {
      '2022_preEE': 'Summer22_23Sep2023_RunCD_v1.root',
      '2022_postEE': 'Summer22EE_23Sep2023_RunEFG_v1.root',
      '2023C': 'Summer23Prompt23_RunC_v1.root',
      '2023D': 'Summer23BPixPrompt23_RunD_v1.root'
    }
    fullpath = os.getenv('CMSSW_BASE') + '/src/TauFW/PicoProducer/data/jetveto/' + filename[era]
    self.rootfile = r.TFile(fullpath)
    self.histo = self.rootfile.Get('')
    print('Full path = ',fullpath,' histo = ',self.histo)

  def isHot(self,jetCollection,muonCollection):

    hotSpot = False
    for jet in jetCollection:
      for muon in muonCollection:
        if abs(jet.pt) < 15: continue
        if jet.jetId<2: continue
        if (jet.chEmEF + jet.neEmEF) > 0.90: continue
        overlap = False
        for muon in muonCollection:
          if jet.DeltaR(muon) < 0.2:
            overlap = True
            break
        if overlap: continue
        value = self.histo.GetBinContent(self.histo.FindBin(jet.eta,jet.phi))
        if value>0.01: 
          hotSpot = True
          nx = self.histo.GetXaxis().FindBin(jet.eta)
          ny = self.histo.GetYaxis().FindBin(jet.phi)
          print('hotspot : [nx,ny]=[%2i,%2i] [eta,phi]=[%6.3f,%6.3f]'%(nx,ny,jet.eta,jet.phi))
        if hotSpot: break

    return hotSpot
