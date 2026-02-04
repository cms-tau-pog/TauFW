#! /usr/bin/env python3

import os, sys
assert sys.version_info>=(3,8),"Python version must be newer than 3.8, currently %s.%s"%(sys.version_info[:2])
import correctionlib._core as core
import correctionlib.schemav2 as schema
import correctionlib.JSONEncoder as JSONEncoder
#from correctionlib.schemav2 import Correction, CorrectionSet
import json, jsonschema
import gzip
from ROOT import TFile


def getsystinfo(systkeys=['nom','up','down']):
  """Help function to create description of systematic inputs."""
  #systkeys.sort(key=syst_sortkey)
  systinfo = "Systematic variations: "
  systinfo += "'"+ "', '".join(systkeys)+"'" # e.g. "'nom', 'up', 'down'"
  return systinfo
  

def getgminfo():
  """Help function to create description of genmatch inputs."""
  return "genmatch: 0 or 6 = unmatched or jet, 1 or 3 = electron, 2 or 4 = muon, 5 = real tau"
  

def getdminfo(dms):
  """Help function to create description of DM inputs."""
  dminfo = ', '.join(str(d) for d in dms)
  return f"Reconstructed tau decay mode: {dminfo}"
  

def getwpinfo(id,wps):
  """Help function to create description of WP inputs."""
  try:
    wpmin = max([w for w in wps if 'loose' in w.lower()],key=lambda x: len(x)) # get loose WP with most 'V's
    wpmax = max([w for w in wps if 'tight' in w.lower()],key=lambda x: len(x)) # get tight WP with most 'V's
    info  = f"{id} working point: {wpmin}-{wpmax}"
  except:
    info  = f"{id} working point: {', '.join(wps)}"
  return info
  

def reusesf(sfs,dm1,dm2):
  """Help function to copy SFs for other DM in dictionary, if it does not exist already."""
  if dm1 in sfs and dm2 not in sfs: # reuse dm1 for dm2
    print(warn(f"Reusing DM{dm1} SF {sfs[dm1]} for DM{dm2} SF..."))
    if isinstance(sfs[dm1],(list,tuple)):
      sfs[dm2] = sfs[dm1][:]
    else:
      sfs[dm2] = sfs[dm1]
  return sfs.get(dm1,None)
  

def wp_sortkey(string):
  """Help function to sort WPs. Use as
      wps = ['Medium','Tight','Loose','VTight','VLoose','VVTight']
      sorted(wps,key=wp_sortkey)
      wps.sort(key=wp_sortkey)
  """
  lowstr = string.lower()
  if lowstr.startswith('medium'):
    return 0
  elif lowstr.lstrip('v').startswith('loose'):
    return -1*(lowstr.count('v')+1)
  elif lowstr.startswith('tight'):
    return 1*(lowstr.count('v')+1)
  return 100+len(string) # anything else at the end
  

def syst_sortkey(string):
  """Help function to sort systematic keys. Use as
      systs = ['nom','up','down']
      sorted(systs,key=syst_sortkey)
      systs.sort(key=syst_sortkey)
  """
  lowstr = string.lower()
  if lowstr=='nom':
    return 0
  else:
    return 2*len(lowstr.replace('up','').replace('down',''))+int('down' in lowstr)
  

def header(string):
  print("\n>>> \033[1m\033[4m%s\033[0m"%(string))
  

def green(string,**kwargs):
  return "\033[32m%s\033[0m"%string
  

def warn(string):
  return ">>> "+f"\033[33m{string}\033[0m"
  

def eval(corr,*args):
  try:
    sf = "%.1f"%(corr.evaluate(*args))
  except Exception as err:
    sf = f" \033[1m\033[91m{err.__class__.__name__}\033[0m\033[91m: {err}\033[0m"
  return sf
  

def sf2str(nom,up,dn):
  if nom==None:
    str = " %6s %6s %6s"%('ERR','ERR','ERR')
  else:
    str  = " %6.3f"%(nom)
    str += " %6s"%('ERR') if up==None else " %+6.3f"%(up-nom)
    str += " %6s"%('ERR') if dn==None else " %+6.3f"%(dn-nom)
  return str
  

def marksf(sfs1,sfs2):
  str1, str2 = "", ""
  nom1, nom2 = sfs1[0], sfs2[0]
  cap = False
  for i, (sf1, sf2) in enumerate(zip(sfs1,sfs2)):
    if i==0:
      frmt = lambda s,n: (" %6s"%'ERR') if s==None else (" %6.3f"%s)
    else:
      frmt = lambda s,n: (" %6s"%'ERR') if s==None else (" %+6.3f"%(s-n))
    str1_ = frmt(sf1,nom1)
    str2_ = frmt(sf2,nom2)
    if sf1!=sf2:
      if sf1==None or sf2==None or abs(sf1-sf2)>0.01:
        if not cap or "\033[93m" in str1:
          str1_ = "\033[1m\033[91m"+str1_
          str2_ = "\033[1m\033[91m"+str2_
          cap = True
      elif abs(sf1-sf2)>0.0001:
        if not cap or "\033[91m" in str1:
          str1_ = "\033[1m\033[93m"+str1_
          str2_ = "\033[1m\033[93m"+str2_
          cap = True
      elif cap: # no difference; cap off color highlight
        str1_ = "\033[0m"+str1_
        str2_ = "\033[0m"+str2_
        cap = False
    str1 += str1_
    str2 += str2_
  if cap:
    str1 += "\033[0m"
    str2 += "\033[0m"
  return str1, str2
  

def evaltool(tool,args,largs=tuple()):
  """Help function to execute old ROOT tool or new JSON tool in common format."""
  sfs = [ ] # nom, up, down
  if callable(tool): #hasattr(tool,'evaluate') # assume old ROOT tool for Run-2
    sfs = tool(args) # down, nom, up
    sfs = (sfs[1],sfs[2],sfs[0]) # nom, up, down
  else: # assume new JSON tool
    for syst in ['nom','up','down']:
      try:
        sf = tool.evaluate(*args,syst,*largs)
      except Exception as err:
        sf = None
      sfs.append(sf)
  return sfs
  

def comparetools(oldtool,newtool,args1,args2,largs1=tuple(),largs2=tuple()):
  """Help function to compare the SFs of two tools."""
  sfnew = [ ]
  sfold = [ ]
  sfold = evaltool(oldtool,args1,largs1) # nom, up, down
  sfnew = evaltool(newtool,args2,largs2) # nom, up, down
  #str1  = sf2str(*sfold)
  #str2  = sf2str(*sfnew)
  str1, str2 = marksf(sfold,sfnew)
  #mark  = any(s==None for s in sfold+sfnew) or any(abs(x-y)>0.01 for x, y in zip(sfold,sfnew))
  #if mark:
  #  str1 = "\033[1m\033[91m"+str1+"\033[0m"
  #  str2 = "\033[1m\033[91m"+str2+"\033[0m"
  #elif any(abs(x-y)>0.0001 for x, y in zip(sfold,sfnew)):
  #  str1 = "\033[93m"+str1+"\033[0m"
  #  str2 = "\033[93m"+str2+"\033[0m"
  return str1, str2
  

def isjson(fname,verb=0):
  return fname.endswith(".json") or fname.endswith(".json.gz")
  

def readjson(fname,rename=None,validate=True,verb=0):
  """Read & validate JSON."""
  if verb>=1:
    print(f">>> Opening {fname}...")
  if not os.path.isfile(fname):
    print(warn(f'Could not find JSON file {fname}...'))
  #corr = schema.Correction.parse_file(fname)
  if fname.endswith(".json.gz"):
    with gzip.open(fname,'rt') as file:
      data = json.load(file)
  else:
    with open(fname) as file:
      data = json.load(file)
  clss = schema.Correction if 'data' in data else schema.CorrectionSet
  if validate:
    if verb>=1:
      print(f">>> Validating {fname}...")
    out = jsonschema.validate(data,clss.schema())
  if rename!=None and 'name' in data:
    if verb>=2:
      print(f">>> Renaming {data['name']} -> {rename}...")
    data['name'] = rename # rename
  corr = clss.parse_obj(data)
  if verb>=2:
    print(JSONEncoder.dumps(corr))
  elif verb>=3:
    print(corr)
  return corr
  

def wrap(corrs,verb=0):
  """Return purely python CorrectionSet object, and wrapped C++ CorrectionSet object."""
  if isinstance(corrs,schema.Correction):
    corrs = [corrs]
  if isinstance(corrs,schema.CorrectionSet):
    cset_py = corrs
  else: # create CorrectionSet from list of Correction objects
    cset_py = schema.CorrectionSet( # simple python CorrectionSet object
      schema_version=schema.VERSION,
      corrections=list(corrs),
    )
  cset_cpp = core.CorrectionSet.from_string(cset_py.json()) # wrap to create C++ object that can be evaluated
  if verb>=2:
    print(f">>> Wrap: {type(cset_py)} -> {type(cset_cpp)}")
  return cset_cpp
  

def loadeval(fname,rename=None,validate=True,verb=0):
  """Load C++ evaluator from JSON."""
  if isinstance(fname,str):
    corrs = readjson(fname,rename=rename,validate=validate,verb=verb)
    cset  = wrap(corrs,verb=verb) # create C++ CorrectionSet
  else:
    cset  = fname
  return cset
  

def ensuredir(dirname,**kwargs):
  """Make directory if it does not exist."""
  verbosity = kwargs.get('verb', 0 )
  if dirname and not os.path.exists(dirname):
    os.makedirs(dirname)
    if verbosity>=1:
      print(f'>>> Made directory "{dirname}"')
    if not os.path.exists(dirname):
      print(f'>>> Failed to make directory "{dirname}"')
  return dirname
  

def ensureTFile(fname,**kwargs):
  """Open TFile."""
  verbosity = kwargs.get('verb', 0 )
  file = None
  if os.path.isfile(fname):
    file = TFile.Open(fname)
    if not file or file.IsZombie():
      print(warn(f'Could not open file {fname}...'))
    elif verbosity>=1:
      print(">>> Opening {fname}...")
  else:
    print(warn(f'Did not find file {fname}...'))
    return None
  return file
