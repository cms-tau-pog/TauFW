#! /usr/bin/env python3
# Author: Izaak Neutelings (March 2021)
# Description: Create TauPOG JSON files from hardcoded energy scales & anti-lepton discriminators SFs
# Adapted from https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
# Instructions:
#   scripts/tau_createJSONs.py -I DeepTau2017v2p1VSe -y 2016Legacy -v1 -t _new
#   scripts/tau_createJSONs.py -I DeepTau2017v2p1VSmu -y 2016Legacy -v1 -t _new
#   scripts/tau_createJSONs.py -T DeepTau2017v2p1 -y 2016Legacy -v1 -t _new
import os, sys
from math import sqrt
from tau_tid import makecorr_tid_dm, makecorr_tid_pt
from tau_ltf import makecorr_ltf
from utils import *
#from correctionlib.utils import *
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
  tidfilter = args.tidfilter or ([ # only run these tau IDs
    'DeepTau2017v2p1VSe',
  ])
  erafilter = args.erafilter or [ # only run these eras
    'UL2016_preVFP',
    'UL2016_postVFP',
    'UL2017',
    'UL2018',
  ]
  if verbosity>=1:
    print(">>> tidfilter = {tidfilter}")
    print(">>> erafilter = {erafilter}")
  
  #######################
  #   ANTI-LEPTON SFs   #
  #######################
  
  _prec = 5
  antiLepSFs     = { }
  antiLepSFs['DeepTau2017v2p1VSe'] = {
      'UL2016_preVFP': {
      'VVLoose': ( SF(1.12,0.04), SF1, SF(1.07,0.07) ),
      'VLoose':  ( SF(0.94,0.05), SF1, SF(0.99,0.07) ),
      'Loose':   ( SF(1.00,0.04), SF1, SF(1.04,0.08) ),
      'Medium':  ( SF(1.24,0.05), SF1, SF(1.06,0.10) ),
      'Tight':   ( SF(1.66,0.06), SF1, SF(1.15,0.17) ),
      'VTight':  ( SF(2.15,0.24), SF1, SF(1.71,0.44) ),
      'VVTight': ( SF(2.68,0.45), SF1, SF(3.61,1.20) ),
    },
    'UL2016_postVFP': {
      'VVLoose': ( SF(1.06,0.05), SF1, SF(0.95,0.06) ),
      'VLoose':  ( SF(1.08,0.05), SF1, SF(0.88,0.09) ),
      'Loose':   ( SF(1.13,0.05), SF1, SF(0.83,0.16) ),
      'Medium':  ( SF(1.19,0.07), SF1, SF(0.90,0.21) ),
      'Tight':   ( SF(1.39,0.15), SF1, SF(0.83,0.32) ),
      'VTight':  ( SF(1.39,0.37), SF1, SF(1.00,1.00) ),
      'VVTight': ( SF(2.39,0.84), SF1, SF(0.35,0.70) ),
    },
    'UL2017': {
      'VVLoose': ( SF(0.89,0.05), SF1, SF(0.93,0.06) ),
      'VLoose':  ( SF(0.85,0.04), SF1, SF(0.89,0.07) ),
      'Loose':   ( SF(0.97,0.04), SF1, SF(0.85,0.08) ),
      'Medium':  ( SF(1.21,0.05), SF1, SF(0.82,0.09) ),
      'Tight':   ( SF(1.63,0.10), SF1, SF(0.93,0.21) ),
      'VTight':  ( SF(2.37,0.23), SF1, SF(1.04,0.41) ),
      'VVTight': ( SF(3.37,0.20), SF1, SF(1.55,0.93) ),
    },
    'UL2018': {
      'VVLoose': ( SF(0.90,0.04), SF1, SF(1.07,0.07) ),
      'VLoose':  ( SF(0.89,0.04), SF1, SF(1.01,0.07) ),
      'Loose':   ( SF(0.92,0.05), SF1, SF(0.94,0.08) ),
      'Medium':  ( SF(0.99,0.06), SF1, SF(0.96,0.11) ),
      'Tight':   ( SF(1.39,0.16), SF1, SF(1.02,0.23) ),
      'VTight':  ( SF(1.92,0.39), SF1, SF(1.01,0.53) ),
      'VVTight': ( SF(2.63,0.71), SF1, SF(2.65,0.07) ),
    },
  }
  
  # CREATE JSON
  antiEleEtaBins = ( 0.0, 1.460, 1.558, 2.3 )
  for id in antiLepSFs:
    if id not in tidfilter: continue
    ltype = 'e'
    for era in antiLepSFs[id]:
      if era not in erafilter: continue
      sfs   = antiLepSFs[id][era] # WP -> (nom,uncup,uncdn)
      ebins = antiEleEtaBins 
      if verbosity>0:
        print(f">>> etabins={ebins}")
        print(f">>> sfs={sfs}")
      corr = makecorr_ltf(sfs,id=id,era=era,ltype=ltype,bins=ebins,
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
  parser.add_argument('-o', '--outdir',   default="data/tau/new", help="output direcory for JSON file" ) #
  parser.add_argument('-t', '--tag',      default="", help="extra tag for JSON output file" )
  parser.add_argument('-I', '--tid',      dest='tidfilter', nargs='+', help="filter by tau ID" )
  parser.add_argument('-y', '--era',      dest='erafilter', nargs='+', help="filter by era" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done!")
  
