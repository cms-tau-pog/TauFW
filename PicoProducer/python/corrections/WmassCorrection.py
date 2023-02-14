import ROOT as r 
import os

class WStarWeight:

  def __init__(self,filename,histoname):
    fullpath = os.getenv('CMSSW_BASE') + '/src/TauFW/PicoProducer/data/Wstar/' + filename
    self.rootfile = r.TFile(fullpath)
    self.histo = self.rootfile.Get(histoname)
    print('Full path = ',fullpath,' histo = ',self.histo)

  def getWeight(self,wmass):

    if (wmass<100 or wmass >3000):
      weight = 1.0
    else:
#      print('bin',self.histo.FindBin(wmass))
      weight = self.histo.GetBinContent(self.histo.FindBin(wmass))

#    print('wmass',wmass,'weight',weight)
    return weight 
