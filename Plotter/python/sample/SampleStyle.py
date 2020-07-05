# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (July 2020)
import os, re
from collections import OrderedDict
from TauFW.Plotter.sample.utils import LOG
from ROOT import TColor, kBlack, kWhite, kGray, kAzure, kBlue, kCyan,\
                 kGreen, kSpring, kTeal, kYellow,\
                 kOrange, kRed, kPink, kMagenta, kViolet

sample_title_dict = {
  'DY':       "Z + jets", #Drell-Yan
  'ZTT':      "Z -> tau_{mu}tau_{h}",
  'ZTT_DM0':  "Z -> tau_{mu}tau_{h}, h^{#pm}",
  'ZTT_DM1':  "Z -> tau_{mu}tau_{h}, h^{#pm}#pi^{0}",
  'ZTT_DM10': "Z -> tau_{mu}tau_{h}, h^{#pm}h^{#mp}h^{#pm}",
  'ZL':       "Drell-Yan with l -> tau_h",
  'ZJ':       "Drell-Yan with j -> tau_h",
  'TT':       "ttbar",
  'TTT':      "ttbar with real tau_h",
  'TTJ':      "ttbar other",
  'TTL':      "ttbar with l -> tau_h",
  'ST':       "Single t",
  'STT':      "Single t with real tau_h",
  'STL':      "Single t with l -> tau_h",
  'STJ':      "Single t other",
  'VV':       "Diboson",
  'W':        "W + jets",
  'JTF':      "j -> tau_h fakes",
  'QCD':      "QCD multijet",
  'Data':     "Observed",
  'data_obs': "Observed",
}

colors_sample_dict = {
  'DY':        kOrange-4,
  'ZL':        TColor.GetColor(100,182,232), #kAzure+5,
  'ZJ':        kGreen-6,
  'ZTT':       kOrange-4,
  'ZTT_DM0':   kOrange+5,
  'ZTT_DM1':   kOrange-4, #kOrange,
  'ZTT_DM10':  kYellow-9,
  'ZTT_DM11':  kOrange-6,
  'ZTT_other': kOrange-8,
  'DY10':      TColor.GetColor(240,175,60), #TColor.GetColor(222,90,106)
  'TT':        kBlue-8,
  'TTT':       kAzure-9,
  'TTJ':       kBlue-8,
  'TTL':       kGreen-6,
  'ST':        TColor.GetColor(140,180,220),
  'STJ':       kMagenta-8,
  'VV':        TColor.GetColor(222,140,106),
  'WJ':        50,
  'QCD':       kMagenta-10,
  'Data':      kBlack,
}


def set_sample_colors(coldict):
  global colors_sample_dict
  colors_sample_dict = OrderedDict([
    ('DY',               coldict['DY']),
    ('ZTT',              coldict['DY']),
    ('ZL',               coldict['ZL']),
    ('ZJ',               coldict['ZJ']),
    ('Drel*Yan',         coldict['DY']),
    ('Z*tau',            coldict['DY']),
    ('Z*ll',             coldict['ZL']),
    #('D*Y*j*tau',        coldict['ZJ']),
    #('D*Y*l*tau',        coldict['ZL']),
    #('D*Y*other',        coldict['ZJ']), #kSpring+3, kPink-2
    ('D*Y*10*50',        coldict['DY10']),
    ('D*Y*50',           coldict['DY']),
    ('ZTT_DM0',          coldict['ZTT_DM0']),
    ('ZTT_DM1',          coldict['ZTT_DM1']),
    ('ZTT_DM10',         coldict['ZTT_DM10']),
    ('ZTT_DM11',         coldict['ZTT_DM11']),
    ('ZTT_DMother',      coldict['ZTT_other']),
    #('Z*tau*h*pm',       coldict['ZTT_DM0']),
    #('Z*tau*h*pm*h*0',   coldict['ZTT_DM1']),
    #('Z*tau*h*h*h',      coldict['ZTT_DM10']),
    #('Z*tau*h*h*h*h*0',  coldict['ZTT_DM11']),
    #('Z*tau*other',      coldict['DY10']),
    ('Embedded',         coldict['DY']),
    ('W*jets',           coldict['WJ']),
    ('W*J',              coldict['WJ']),
    ('W',                coldict['WJ']),
    ('WW',               coldict['VV']),
    ('WZ',               coldict['VV']),
    ('ZZ',               coldict['VV']),
    ('VV',               coldict['VV']),
    ('Diboson',          coldict['VV']),
    ('Electroweak',      coldict['VV']),
    ('EWK',              coldict['VV']),
    ('TT',               coldict['TT']),
    ('TTT',              coldict['TTT']),
    ('TTL',              coldict['TTL']),
    ('TTJ',              coldict['TTJ']),
    ('ttbar',            coldict['TT']),
    #('ttbar*real*tau',   coldict['TTT']),
    #('ttbar*l',          coldict['TTL']),
    #('ttbar*j',          coldict['TTJ']),
    #('ttbar*other',      coldict['TTJ']),
    #('ttbar*single',     coldict['TT']),
    ('Top',              coldict['TT']),
    ('ST',               coldict['ST']),
    #('Single*top':       coldict['ST']),
    ('STT',              coldict['ST']),
    ('STJ',              coldict['STJ']),
    #('Single*top*real',  coldict['ST']),
    #('Single*top*other', coldict['STJ'],
    ('QCD',              coldict['QCD']),
    ('JTF',              coldict['QCD']),
    ('Fake*rate',        coldict['QCD']),
    ('j*tau*fake',       coldict['QCD']),
    ('Data',             coldict['Data']),
    ('Observed',         coldict['Data']),
  ])
set_sample_colors(colors_sample_dict)

def getcolor(sample,color=kWhite,**kwargs):
  """Get color for some sample name."""
  verbosity = LOG.getverbosity(kwargs)
  if hasattr(sample,'name'):
    sample = sample.name
  for key in colors_sample_dict: #sorted(colors_sample_dict,key=lambda x: len(x),reverse=True)
    if re.findall(key.replace('*',".*"),sample): # glob -> regex wildcard
      LOG.verb("getcolor: Found color %s for %r from searchterm %r!"%(colors_sample_dict[key],sample,key),verbosity,level=2)
      color = colors_sample_dict[key]
      break
  else:
    LOG.warning("getcolor: Could not find color for %r!"%sample)
  return color
  
