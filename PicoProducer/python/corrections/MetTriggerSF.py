import ROOT as r 
import os
import math

class METTriggerSF:

  def __init__(self,filename):
    fullpath = os.getenv('CMSSW_BASE') + '/src/TauFW/PicoProducer/data/trigger/' + filename
    self.mhtLabels = ('mht100to130','mht130to160','mht160to200','mhtGt200')
    self.sampleLabels = ('data','mc')
    self.labels = [ u+"_"+v for u in self.sampleLabels for v in self.mhtLabels]
    self.rootfile = r.TFile(fullpath)    
    self.histo = { } 
    for label in self.labels: 
      self.histo[label] = self.rootfile.Get(label)
      print((label,self.histo[label]))

  def getWeight(self,metnomu,mhtnomu):

    weight = 1.0
    eff_data = 0.0
    eff_mc = 0.0
    if metnomu<100 or mhtnomu<100:
      weight = 0.0
    else:
      binname = 'mht100to130'
      if mhtnomu>=130 and mhtnomu<160: 
        binname = 'mht130to160' 
      elif mhtnomu>=160 and mhtnomu<200: 
        binname = 'mht160to200'
      elif mhtnomu>=200:
        binname = 'mhtGt200'
      label_data = 'data_' + binname
      label_mc = 'mc_' + binname
      x = metnomu
      if metnomu>999.0: x = 999.
      bin_data = self.histo[label_data].GetXaxis().FindBin(x)
      bin_mc = self.histo[label_mc].GetXaxis().FindBin(x)
      eff_data = self.histo[label_data].GetBinContent(bin_data)
      eff_mc = self.histo[label_mc].GetBinContent(bin_mc)
      weight = 1.0
      if eff_data>1e-3 and eff_mc>1e-3:
        weight = eff_data/eff_mc
      
#    print(metnomu,mhtnomu,weight,eff_data,eff_mc)
    return weight 
