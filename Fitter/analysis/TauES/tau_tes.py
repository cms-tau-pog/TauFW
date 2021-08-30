#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with format of TauPOG SFs.
# Instructions:
#  ./scripts/tau_tes.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html#Tau
import sys; sys.path.append('scripts')
from utils import *
from collections import namedtuple
#TES = namedtuple('TES',['nom','up','dn_lowpt','nom_highpt','up_highpt','dn_highpt']) # helper class


def interpolate_tes(teslow,teshigh,prec=8):
  """Interpolate tau energy scale for real tau (genmatch==5)."""
  # f = TFormula('f',sf)
  # for x in [10,34,35,(170+34)/2,100,169.9,170,171,200,2000]: x, f.Eval(x)
  #return f"x<34?{low}: x<170?{low}+({high}-{low})/(170.-34.)*(x-34): {high}"
  tesnom = teslow[0] # use low-pT as central value for whole pT range
  uncup_low,  uncdn_low  = teslow[1]-teslow[0],   teslow[0]-teslow[2]
  uncup_high, uncdn_high = teshigh[1]-teshigh[0], teshigh[0]-teshigh[2]
  gradup = (uncup_high-uncup_low)/(170.-34.)
  graddn = (uncdn_high-uncdn_low)/(170.-34.)
  offsup = teslow[1]-34.*gradup
  offsdn = teslow[2]+34.*graddn
  if uncup_low>uncup_high:
    print(warn("Low-pT TES up %.3f > high-pT TES up %.3f !!!"%(uncup_low,uncup_high)))
  if uncdn_low>uncdn_high:
    print(warn("Low-pT TES down %.3f > high-pT TES down %.3f !!!"%(uncdn_low,uncdn_high)))
  tesdata = [ # key:syst
    { 'key': 'nom',  'value': tesnom }, # central value
    { 'key': 'up', 'value': { # down
        'nodetype': 'binning',
        'input': "pt",
        'edges': [0.,34.,170.,1000.],
        'flow': "clamp",
        'content': [
          teslow[1],
          { 'nodetype': 'formula', # down (pt-dependent)
            #'expression': "%.6g+%.6g*(x-34.)"%(offsup,gradup),
            'expression': "%.6g+%.6g*x"%(offsup,gradup),
            'parser': "TFormula",
            'variables': ["pt"],
          },
          round(tesnom+uncup_high,prec),
        ],
      },
    }, # key:syst=up
    { 'key': 'down', 'value': { # down
        'nodetype': 'binning',
        'input': "pt",
        'edges': [0.,34.,170.,1000.],
        'flow': "clamp",
        'content': [
          teslow[2],
          { 'nodetype': 'formula', # down (pt-dependent)
            #'expression': "%.6g-%.6g*(x-34.)"%(offsdn,graddn),
            'expression': "%.6g-%.6g*x"%(offsdn,graddn),
            'parser': "TFormula",
            'variables': ["pt"],
          },
          round(tesnom-uncdn_high,prec),
        ],
      },
    }, # key:syst=down
  ] # key:syst
  return tesdata
  

def maketesdata(tesvals,etabins,gms):
  """Construct tau energy scale data block."""
  dms     = sorted(tesvals['low'].keys())
  fesdms  = sorted(tesvals['ele'].keys())
  fesvals = tesvals['ele'] # dm -> [(nom,up,down),(nom,up,down)] per eta bin
  tesvals = { # dm -> TES(nom,uplow,downlow,uphigh,downhigh)
    dm: (tesvals['low'][dm],tesvals['high'].get(dm,tesvals['low'][dm])) for dm in dms
  }
  
  # REAL TAU (genmatch==5)
  tesdata = schema.Category.parse_obj({ # category:dm -> category:syst
    'nodetype': 'category', # category:dm
    'input': "dm",
    #'default': 1.0, # no default: throw error if unsupported DM
    'content': [ # key:dm
      { 'key': dm,
        'value': {
          'nodetype': 'category', # category:syst
          'input': "syst",
          'content': interpolate_tes(*tesvals[dm])
        } # category:syst
      } for dm in dms
    ] # key:dm
  }) # category:dm
  
  # E -> TAU FAKE (genmatch==1,3)
  fesdata = schema.Category.parse_obj({ # category:dm -> transform:eta -> binning:eta -> category:syst
    'nodetype': 'category', # category:dm
    'input': "dm",
    #'default': 1.0, # no default: throw error if unsupported DM
    'content': [ # key:dm
      { 'key': dm,
        'value': {
          'nodetype': 'transform', # transform:eta
          'input': "eta",
          'rule': {
            'nodetype': 'formula',
            'expression': "abs(x)",
            'parser': "TFormula",
            'variables': ["eta"],
          },
          'content': {
            'nodetype': 'binning', # binning:eta
            'input': "eta",
            'edges': etabins,
            'flow': "clamp",
            'content': [
              { 'nodetype': 'category', # category:syst
                'input': "syst",
                'content': [
                  { 'key': 'nom',  'value': fes[0] },
                  { 'key': 'up',   'value': fes[1] },
                  { 'key': 'down', 'value': fes[2] },
                ]
              } for fes in fesvals[dm] # category:syst
            ]
          } # binning:eta
        } # transform:eta
      } for dm in fesdms
    ]+[
      { 'key': dm, 'value': 1.0 } # default for supported DMs
      for dm in dms if dm not in fesdms
    ] # key:dm
  }) # category:dm
  
  # MU -> TAU FAKE (genmatch==2,4)
  mesdata = schema.Category.parse_obj({
    'nodetype': 'category', # category:syst
    'input': "syst",
    'content': [
      { 'key': 'nom',  'value': 1.00 },
      { 'key': 'up',   'value': 1.01 },
      { 'key': 'down', 'value': 0.99 },
    ]
  }) # category:syst
  
  # DATA
  tesdata = schema.Transform.parse_obj({ # transform:genmatch -> category:genmatch -> key:genmatch
    'nodetype': 'transform', # transform:genmatch
    'input': "genmatch",
    'rule': {
      'nodetype': 'category', # category:genmatch
      'input': "genmatch",
      #'default': 0, # no default: throw error if unrecognized genmatch
      'content': [ # key:genmatch
        { 'key': gm,
          'value': 1 if gm in [1,3] else 2 if gm in [2,4] else 6 if gm in [0,6] else gm # group 1,3 and 2,4, 0,6
        } for gm in gms
      ] # key:genmatch
    }, # category:genmatch
    'content': {
      'nodetype': 'category', # category:genmatch
      'input': "genmatch",
      #'default': 1.0, # no default: throw error if unrecognized genmatch
      'content': [
        { 'key': 1, 'value': fesdata },  # e  -> tau_h fake
        { 'key': 2, 'value': mesdata },  # mu -> tau_h fake
        { 'key': 5, 'value': tesdata },  # real tau_h
        { 'key': 6, 'value': 1.0 },      # j  -> tau_h fake
      ]
    } # category:genmatch
  }) # transform:genmatch
  
  return tesdata


def makecorr_tes(tesvals=None,**kwargs):
  """Make Correction object JSON for tau energy scale from dictionary:
  tesvals = {
    id:                                    # e.g. 'DeepTau2017v2p1'
      'low':  { dm: (nom,uncup,uncdn) },   # low pT measurement in Z -> tautau -> mutau_h
      'high': { dm: (nom,uncup,uncdn) },   # high pT measurement in W* + jets
      'ele':  { dm: [(nom,uncup,uncdn),(nom,uncup,uncdn)] }, # per eta bin
  }
  """
  verb    = kwargs.get('verb',0)
  tag     = kwargs.get('tag',"") # output tag for JSON file
  outdir  = kwargs.get('outdir',"data/tau") # output directory for JSON file
  info    = ", to be applied to reconstructed tau_h Lorentz vector (pT, mass and energy) in simulated data"
  dms     = (0,1,2,10,11)
  fesdms  = (0,1)
  gms     = (0,1,2,3,4,5,6)
  ptbins  = (0.,34.,170.)
  etabins = (0.,1.5,2.5)
  if tesvals:
    era     = kwargs.get('era',  "unkown")
    name    = kwargs.get('name', f"tau_es_dm_{era}")
    fname   = kwargs.get('fname',f"{outdir}/{name}{tag}.json")
    info    = kwargs.get('info', f"DM-dependent tau energy scale in {era}"+info)
    ptbins  = kwargs.get('ptbins',ptbins)
    etabins = kwargs.get('etabins',etabins)
    ids     = list(tesvals.keys())
    dms     = sorted(list({dm for id in tesvals for dm in tesvals[id]['low']})) # get largest possible DM list
  else: # test format with dummy values
    header(f"Tau energy scale")
    name    = kwargs.get('name', f"test_dm")
    fname   = kwargs.get('fname',f"{outdir}/test_tau_tes{tag}.json")
    info    = kwargs.get('info', f"DM-dependent tau energy scale"+info)
    ids     = ['DeepTau2017v2p1']
    tesvals = {
      id: {
        'low':  {dm: (1.0,1.1,0.9) for dm in dms}, # (nom,up,down) per dm
        'high': {dm: (1.0,1.2,0.8) for dm in dms}, # (nom,up,down) per dm
        'ele':  {dm: [(1.0,1.2,0.8)]*(len(etabins)-1) for dm in fesdms} # (nom,up,down) per eta bin
      } for id in ids
    }
  
  # CORRECTION OBJECT
  corr = schema.Correction.parse_obj({
    'version': 0,
    'name': name,
    'description': info,
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "Reconstructed tau pT"},
      {'name': "eta",      'type': "real",   'description': "Reconstructed tau eta"},
      {'name': "dm",       'type': "int",    'description': getdminfo(dms)},
      {'name': "genmatch", 'type': "int",    'description': getgminfo()},
      {'name': "id",       'type': "string", 'description': f"Tau ID: {', '.join(ids)}"},
      {'name': "syst",     'type': "string", 'description': getsystinfo()},
    ],
    'output': {'name': "tes", 'type': "real", 'description': "tau energy scale"},
    'data': { # category:id -> key:id -> transform:genmatch -> category:genmatch -> key:genmatch
      'nodetype': 'category', # category:genmatch
      'input': "id",
      'content': [ # key:id
        { 'key': id,
          'value': maketesdata(tesvals[id],etabins,gms)
        } for id in ids
      ]  # key:id
    } # category:id
  })
  
  if verb>=2:
    print(JSONEncoder.dumps(corr))
  elif verb>=1:
    print(corr)
  if fname:
    print(f">>> Writing {fname}...")
    JSONEncoder.write(corr,fname)
  return corr
  

def makecorr_tes_id(tesvals=None,**kwargs):
  """Make Correction object JSON for tau energy scale for a single tau ID from dictionary:
  tesvals = {
    'low':  { dm: (nom,uncup,uncdn) }, # low pT measurement in Z -> tautau -> mutau_h
    'high': { dm: (nom,uncup,uncdn) }, # high pT measurement in W* + jets
    'ele':  { dm: [(nom,uncup,uncdn),(nom,uncup,uncdn)] }, # per eta bin
  }
  """
  verb    = kwargs.get('verb',0)
  tag     = kwargs.get('tag',"") # output tag for JSON file
  outdir  = kwargs.get('outdir',"data/tau") # output directory for JSON file
  info    = ", to be applied to reconstructed tau_h Lorentz vector (pT, mass and energy) in simulated data"
  #dms     = (0,1,2,5,6,10,11)
  gms     = (0,1,2,3,4,5,6)
  ptbins  = (0.,34.,170.)
  etabins = (0.,1.5,2.5)
  if tesvals:
    id      = kwargs.get('id',   "unkown")
    era     = kwargs.get('era',  "unkown")
    name    = kwargs.get('name', f"tau_es_dm_{id}_{era}")
    fname   = kwargs.get('fname',f"{outdir}/{name}{tag}.json")
    info    = kwargs.get('info', f"DM-dependent tau energy scale for {id} in {era}"+info)
    ptbins  = kwargs.get('ptbins',ptbins)
    etabins = kwargs.get('etabins',etabins)
    dms     = sorted(list(tesvals['low'].keys()))
  else: # test format with dummy values
    id      = kwargs.get('id',  "DeepTau2017v2p1VSjet")
    header(f"Tau energy scale for {id}")
    name    = kwargs.get('name', f"test_{id}_dm")
    fname   = kwargs.get('fname',f"{outdir}/test_tau_tes{tag}.json")
    info    = kwargs.get('info', f"DM-dependent tau energy scale for {id}"+info)
    dms     = (0,1,2,10,11)
    fesdms  = (0,1,2) # for FES only DM0 and 1
    tesvals = {
      'low':  {dm: (1.0,1.1,0.9) for dm in dms}, # (nom,up,down) per dm
      'high': {dm: (1.0,1.2,0.8) for dm in dms}, # (nom,up,down) per dm
      'ele':  {dm: [(1.0,1.2,0.8)]*(len(etabins)-1) for dm in fesdms} # (nom,up,down) per eta bin
    }
  
  # CORRECTION OBJECT
  corr = schema.Correction.parse_obj({
    'version': 0,
    'name': name,
    'description': info,
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "Reconstructed tau pT"},
      {'name': "eta",      'type': "real",   'description': "Reconstructed tau eta"},
      {'name': "dm",       'type': "int",    'description': getdminfo(dms)},
      {'name': "genmatch", 'type': "int",    'description': getgminfo()},
      {'name': "syst",     'type': "string", 'description': getsystinfo()},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': maketesdata(tesvals,etabins,gms)
  })
  
  if verb>=2:
    print(JSONEncoder.dumps(corr))
  elif verb>=1:
    print(corr)
  if fname:
    print(f">>> Writing {fname}...")
    JSONEncoder.write(corr,fname)
  return corr
  

def evaluate(corrs):
  header("Evaluate")
  cset    = wrap(corrs) # wrap to create C++ object that can be evaluated
  ptbins  = [10.,20.,30.,100.,170.,500.,2000.]
  etabins = [-2.0,-1.0,0.0,1.1,2.0,2.5,3.0]
  gms     = [0,1,2,3,4,5,6,7]
  dms     = [0,1,2,5,10,11]
  id      = "DeepTau2017v2p1"
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    #print(corr.inputs)
    for gm in gms:
      xbins = ptbins if gm==5 else etabins
      ttype = "real tau_h" if gm==5 else "e -> tau_h" if gm in [1,3] else\
              "mu -> tau_h" if gm in [2,4] else "j -> tau_h" if gm in [0,6] else "non-existent"
      print(f">>>\n>>> genmatch={gm}: {ttype}")
      print(">>> %5s"%("dm")+" ".join("  %-15.1f"%(x) for x in xbins))
      for dm in dms:
        row   = ">>> %5d"%(dm)
        for x in xbins:
          pt, eta = (x,1.5) if gm==5 else (20.,x)
          sfnom = 0.0
          for syst in ['nom','up','down']:
            #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
            try:
              sf = corr.evaluate(pt,eta,dm,gm,id,syst)
              if 'nom' in syst:
                row += "%6.2f"%(sf)
                sfnom = sf
              elif 'up' in syst:
                row += "%+6.2f"%(sf-sfnom)
              else:
                row += "%+6.2f"%(sf-sfnom)
            except Exception as err:
              row += "\033[1m\033[91m"+"  ERR".ljust(6)+"\033[0m"
        print(row)
  print(">>>")
  

def main():
  corr1 = makecorr_tes()
  corrs = [corr1] # list of corrections
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
