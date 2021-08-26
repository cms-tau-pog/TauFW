#! /usr/bin/env python3
# Author: Izaak Neutelings (March 2021)
# Description: Create TauPOG JSON files from hardcoded energy scales 
# Adapted from https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
# Instructions:
#   ./tau_createJSONsTauES.py -E DeepTau2017v2p1 -y 2016Legacy -v1 -t _new
import os, sys
from math import sqrt
from tau_tes import makecorr_tes, makecorr_tes_id
from utils import *
_prec = 7 # precision


# SF CONTAINER
class SF:
  """Simple container class, that allows for multiplication of SFs
  with correct error propagation."""
  def __init__(self,nom,uncup,uncdn=None,prec=None):
    if prec==None:
      prec = _prec
    if prec<0:
      prec = 10
    if uncdn==None:
      uncdn = uncup
    self.nom   = round(nom,prec)
    self.unc   = round(max(uncup,uncdn),prec)
    self.uncup = round(uncup,prec)
    self.uncdn = round(uncdn,prec)
    self.up    = round(nom+uncup,prec)
    self.dn    = round(nom-uncdn,prec)
  def __mul__(self,osf):
    """Multiply SFs and propagate errors."""
    if isinstance(osf,SF):
      nom   = self.nom*osf.nom
      uncup = nom*sqrt((self.uncup/float(self.nom))**2 + (osf.uncup/float(osf.nom))**2)
      uncdn = nom*sqrt((self.uncdn/float(self.nom))**2 + (osf.uncdn/float(osf.nom))**2)
      return SF(nom,uncup,uncdn)
    return SF(osf*nom,osf*uncup,osf*uncdn) # assume scalar multiplication
  def __len__(self):
    return 3
  def __getitem__(self,index):
    """To act as a list/tuple: nom = sf[0]; uncup = sf[1]; uncdn = sf[2]"""
    if isinstance(index,slice):
      if index.stop!=None and index.stop>3:
        raise IndexError(f"SF only has 3 elements (nom,up,dn), got slice {index}!")
      return (self.nom,self.up,self.dn)[index]
    else:
      if index==0: return self.nom
      elif index==1: return self.up
      elif index==2: return self.dn
      raise IndexError(f"SF only has 3 elements (nom,up,dn), got {index}!")
  #def toJson(self):
  #  return "[%s, %s, %s]"%(self.nom,self.uncup,self.uncdn) #json.dumps((self.nom,self.uncup,self.uncdn))
  def __repr__(self):
    return "SF(%s+%s-%s)"%(self.nom,self.uncup,self.uncdn)
SF0 = SF(0,0) # default 0 +- 0
SF1 = SF(1,0) # default 1 +- 0


def main(args):
  
  global _prec
  outdir    = ensuredir(args.outdir) #"../data"
  tag       = args.tag # output tag for JSON file
  verbosity = args.verbosity
  tesfilter = args.tesfilter or ([ # only run these tau ESs
    #'MVAoldDM2017v2',
    'DeepTau2017v2p1',
  ] )
  erafilter = args.erafilter or [ # only run these eras
    '2016Legacy',
    '2017ReReco',
    '2018ReReco',
    'UL2016_preVFP',
    'UL2016_postVFP',
    'UL2017',
    'UL2018',
  ]
  if verbosity>=1:
    print(">>> tesfilter = {tesfilter}")
    print(">>> erafilter = {erafilter}")
  
  ########################
  #   TAU ENERGY SCALE   #
  ########################
  
  # TAU ENERGY SCALES low pT (Z -> tautau)
  tesvals = { }
  _prec   = 7
  
  # TAU ENERGY SCALES low pT (Z -> tautau)
  tesvals['low'] = { # units of percentage (centered around 0.0)
    #'MVAoldDM2017v2': {
    #  '2016Legacy': { 0: (-0.6,1.0), 1: (-0.5,0.9), 10: ( 0.0,1.1), 11: ( 0.0,1.1), },
    #  '2017ReReco': { 0: ( 0.7,0.8), 1: (-0.2,0.8), 10: ( 0.1,0.9), 11: (-0.1,1.0), },
    #  '2018ReReco': { 0: (-1.3,1.1), 1: (-0.5,0.9), 10: (-1.2,0.8), 11: (-1.2,0.8), },
    #},
    # https://indico.cern.ch/event/887196/contributions/3743090/attachments/1984772/3306737/TauPOG_TES_20200210.pdf
    'DeepTau2017v2p1': {
      '2016Legacy':     { 0: (-0.9,0.8), 1: (-0.1,0.6), 10: ( 0.3,0.8), 11: (-0.2,1.1), },
      '2017ReReco':     { 0: ( 0.4,1.0), 1: ( 0.2,0.6), 10: ( 0.1,0.7), 11: (-1.3,1.4), },
      '2018ReReco':     { 0: (-1.6,0.9), 1: (-0.4,0.6), 10: (-1.2,0.7), 11: (-0.4,1.2), },
      'UL2016_preVFP':  { 0: (-1.3,1.0), 1: (-0.2,0.6), 10: (-1.6,0.8), 11: (-0.1,1.1), },
      'UL2016_postVFP': { 0: (-0.7,0.9), 1: (-0.9,0.7), 10: ( 0.1,0.7), 11: (-0.3,1.6), },
      'UL2017':         { 0: (-1.4,0.9), 1: (-0.1,0.6), 10: (-0.1,0.7), 11: (-0.4,1.0), },
      'UL2018':         { 0: (-0.9,0.8), 1: ( 0.4,0.6), 10: (-0.2,0.7), 11: ( 0.4,0.9), },
    },
  }
  for id in tesvals['low']:
    if id not in tesfilter: continue
    for era in tesvals['low'][id]:
      if era not in erafilter: continue
      for dm, (tes,unc) in tesvals['low'][id][era].items():
        tesvals['low'][id][era][dm] = SF(1.+tes/100.,unc/100.) # convert percentage back to scale factor
  
  # TAU ENERGY SCALES at high pT (W* + jets)
  tesvals['high'] = { # scale factor centered around 1.
    #'MVAoldDM2017v2': { # central values from Z -> tautau measurement
    #  '2016Legacy': { 0: SF(0.991,0.030), 1: SF(0.995,0.030), 10: SF(1.000,0.030), 10: SF(1.000,0.030), }, # reuse DM10 for DM11
    #  '2017ReReco': { 0: SF(1.004,0.030), 1: SF(0.998,0.030), 10: SF(1.001,0.030), 10: SF(1.001,0.030), },
    #  '2018ReReco': { 0: SF(0.984,0.030), 1: SF(0.995,0.030), 10: SF(0.988,0.030), 10: SF(0.988,0.030), },
    #},
    # https://indico.cern.ch/event/871696/contributions/3687829/attachments/1968053/3276394/TauES_WStar_Run2.pdf
    'DeepTau2017v2p1': {
      '2016Legacy':     { 0: SF(0.991,0.030), 1: SF(1.042,0.020), 10: SF(1.004,0.012), 11: SF(0.970,0.027), },
      '2017ReReco':     { 0: SF(1.004,0.030), 1: SF(1.014,0.027), 10: SF(0.978,0.017), 11: SF(0.944,0.040), },
      '2018ReReco':     { 0: SF(0.984,0.030), 1: SF(1.004,0.020), 10: SF(1.006,0.011), 11: SF(0.955,0.039), },
      'UL2016_preVFP':  { 0: SF(0.991,0.030), 1: SF(1.042,0.020), 10: SF(1.004,0.012), 11: SF(0.970,0.027), },
      'UL2016_postVFP': { 0: SF(0.991,0.030), 1: SF(1.042,0.020), 10: SF(1.004,0.012), 11: SF(0.970,0.027), },
      'UL2017':         { 0: SF(1.004,0.030), 1: SF(1.014,0.027), 10: SF(0.978,0.017), 11: SF(0.944,0.040), },
      'UL2018':         { 0: SF(0.984,0.030), 1: SF(1.004,0.020), 10: SF(1.006,0.011), 11: SF(0.955,0.039), },
    },
  }
  
  # TAU ENERGY SCALES for e -> tau_h fakes (Olena)
  tesvals['ele'] = { # scale factor centered around 1.
    'DeepTau2017v2p1': {
      '2016Legacy': { # barrel / endcap
        0: [SF(1.00679,0.806/100.,0.982/100.), SF(0.965,  1.808/100.,1.102/100.)],
        1: [SF(1.03389,1.168/100.,2.475/100.), SF(1.05,   6.570/100.,5.694/100.)],
      },
      'UL2016_preVFP': { # barrel / endcap
        0: [SF(1.00679,0.806/100.,0.982/100.), SF(0.965,  1.808/100.,1.102/100.)],
        1: [SF(1.03389,1.168/100.,2.475/100.), SF(1.05,   6.570/100.,5.694/100.)],
      },
      'UL2016_postVFP': { # barrel / endcap
        0: [SF(1.00679,0.806/100.,0.982/100.), SF(0.965,  1.808/100.,1.102/100.)],
        1: [SF(1.03389,1.168/100.,2.475/100.), SF(1.05,   6.570/100.,5.694/100.)],
      },
      '2017ReReco': {
        0: [SF(1.00911,1.343/100.,0.882/100.), SF(0.97396,2.249/100.,1.430/100.)],
        1: [SF(1.01154,2.162/100.,0.973/100.), SF(1.015,  6.461/100.,4.969/100.)],
      },
      'UL2017': {
        0: [SF(1.00911,1.343/100.,0.882/100.), SF(0.97396,2.249/100.,1.430/100.)],
        1: [SF(1.01154,2.162/100.,0.973/100.), SF(1.015,  6.461/100.,4.969/100.)],
      },
      '2018ReReco': {
        0: [SF(1.01362,0.904/100.,0.474/100.), SF(0.96903,3.404/100.,1.250/100.)],
        1: [SF(1.01945,1.226/100.,1.598/100.), SF(0.985,  5.499/100.,4.309/100.)],
      },
      'UL2018': {
        0: [SF(1.01362,0.904/100.,0.474/100.), SF(0.96903,3.404/100.,1.250/100.)],
        1: [SF(1.01945,1.226/100.,1.598/100.), SF(0.985,  5.499/100.,4.309/100.)],
      },
    }
  }
  tesvals['ele']['MVAoldDM2017v2'] = tesvals['ele']['DeepTau2017v2p1'] # reuse DeepTau2017v2p1 ESs for MVAoldDM2017v2
  
  # CREATE JSON
  ptbins  = (0.,34.,170.)
  etabins = (0.,1.5,2.5)
  tesids  = [id for id in tesvals['low'].keys()]
  teseras = [e for e in tesvals['low'][tesids[0]].keys()]
  for era in teseras:
    if era not in erafilter: continue
    tesvals_ = { } # swap order: era -> id -> type -> dm (-> eta bin)
    for id in tesids:
      if id not in tesfilter: continue
      assert era in tesvals['high'][id], f"Did not find {era} for {id} high-pT tau energy scale!"
      assert era in tesvals['ele'][id],  f"Did not find {era} for {id} electron fake tau energy scale!"
      tesvals_[id] = {
        'low':  tesvals['low'][id][era],
        'high': tesvals['high'][id][era],
        'ele':  tesvals['ele'][id][era],
      }
      for key in tesvals_[id]:
        reusesf(tesvals_[id][key], 1, 2) # reuse DM1 for DM2
        reusesf(tesvals_[id][key],10,11) # reuse DM10 for DM11 (if DM10 exists)
    if verbosity>=1:
      print(">>> tesvals={")
      for id in tesvals_:
        print(f">>>   '{id}': {{")
        for key in tesvals_[id]:
          print(f">>>     '{key}': {tesvals_[id][key]}")
        print(">>>   }")
      print(">>> }")
    corr = makecorr_tes(tesvals_,era=era,ptbins=ptbins,etabins=etabins,
                        outdir=outdir,tag=tag,verb=verbosity)
  ###tesids  = tesvals['low'].keys()
  ###for id in tesids:
  ###  if id not in tesfilter: continue
  ###  assert id in tesvals['high'], f"Did not find {id} for high-pT tau energy scale!"
  ###  assert id in tesvals['ele'],  f"Did not find {id} for electron fake tau energy scale!"
  ###  teseras = tesvals['low'][id].keys()
  ###  for era in teseras:
  ###    assert era in tesvals['high'][id], f"Did not find {era} for {id} high-pT tau energy scale!"
  ###    assert era in tesvals['ele'][id],  f"Did not find {era} for {id} electron fake tau energy scale!"
  ###    if era not in erafilter: continue
  ###    tesvals_ = { # swap order: id -> era -> type -> dm (-> eta bin)
  ###      'low':  tesvals['low'][id][era],
  ###      'high': tesvals['high'][id][era],
  ###      'ele':  tesvals['ele'][id][era],
  ###    }
  ###    for key in tesvals_:
  ###      reusesf(tesvals_[key], 1, 2) # reuse DM1 for DM2
  ###      reusesf(tesvals_[key],10,11) # reuse DM10 for DM11 (if DM10 exists)
  ###    if verbosity>0:
  ###      print(f">>> tesvals={tesvals_}")
  ###    corr = makecorr_tes_id(tesvals_,id=id,era=era,ptbins=ptbins,etabins=etabins,
  ###                           outdir=outdir,tag=tag,verb=verbosity)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script creates JSON files for hardcoded TauPOG scale factors.'''
  parser = ArgumentParser(prog="tau_createJSONs.py",description=description,epilog="Good luck!")
  parser.add_argument('-o', '--outdir',   default="data/tau/new", help="output direcory for JSON file" )
  parser.add_argument('-t', '--tag',      default="", help="extra tag for JSON output file" )
  parser.add_argument('-E', '--tes',      dest='tesfilter', nargs='+', help="filter by tau ES" )
  parser.add_argument('-y', '--era',      dest='erafilter', nargs='+', help="filter by era" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done!")
  
