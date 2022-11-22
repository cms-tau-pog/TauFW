
import ROOT as r


def GetWmassWeight(wmass,filename="/afs/desy.de/user/r/rasp/public/WStar/kfactor_mu.root",histoname="kfactor_mu"):
 f = r.TFile(filename)
 histo = f.Get(histoname)
 if (wmass<100 or wmass >3000):
    weight = 1.0
 else:
    weight = histo.GetBinContent(histo.FindBin(wmass))
 return weight 