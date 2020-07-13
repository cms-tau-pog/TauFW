# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
import re
from TauFW.Plotter.plot.utils import LOG

var_dict = {
    'njets':       "Number of jets",          'njets20':     "Number of jets (pt>20 GeV)",
    'nfjets':      "Number of forward jets",  'nfjets20':    "Number of forward jets (pt>20 GeV)",
    'ncjets':      "Number of central jets",  'ncjets20':    "Number of central jets (pt>20 GeV)",
    'nbtag':       "Number of b tagged jets", 'nbtag20':     "Number of b tagged jets (pt>20 GeV)",
    'jpt_1':       "Leading jet pt",          'jpt_2':       "Subleading jet pt",
    'bpt_1':       "Leading b jet pt",        'bpt_2':       "Subleading b jet pt",
    'jeta_1':      "Leading jet eta",         'jeta_2':      "Subleading jet eta",
    'beta_1':      "Leading b jet eta",       'beta_2':      "Subleading b jet eta",
    'jphi_1':      "Leading jet phi",         'bphi_1':      "Subleading jet phi",
    'jphi_2':      "Leading b jet phi",       'bphi_2':      "Subleading b jet phi",
    'met':         "p_{T}^{miss}",
    'metphi':      "MET phi",
    'mt_1':        "m_t(l,MET)",
    'dzeta':       "D_{zeta}",
    'pzetavis':    "p_{zeta}^{vis}",
    'pzetamiss':   "p_{zeta}^{miss}",
    'DM0':         "h^{#pm}",
    'DM1':         "h^{#pm}h^{0}",
    'DM10':        "h^{#pm}h^{#mp}h^{#pm}",
    'DM11':        "h^{#pm}h^{#mp}h^{#pm}h^{0}",
}
var_dict_sorted = sorted(var_dict,key=lambda x: len(x),reverse=True)


funcexpr = re.compile(r"(\w+)\(([^,]+),([^,]+)\)")
def makelatex(string,**kwargs):
  """Convert patterns in a string to LaTeX format."""
  global var_dict_sorted
  verbosity = LOG.getverbosity(kwargs)
  if not isinstance(string,str):
    return string
  if string and string[0]=='{' and string[-1]=='}':
    return string[1:-1]
  units  = kwargs.get('units', True  )
  split  = kwargs.get('split', False )
  GeV    = False
  cm     = False
  oldstr = string
  
  # PREDEFINED
  if len(var_dict_sorted)!=len(var_dict):
    var_dict_sorted = sorted(var_dict,key=lambda x: len(x),reverse=True)
  for var in var_dict_sorted:
    if var in string:
      string = string.replace(var,var_dict[var])
      #string = re.sub(r"\b%s\b"%var,var_dict[var],string,re.IGNORECASE)
      break
  
  # SPLIT LINE
  if split:
    while '\n' in string:
      string = "#splitline{%s}"%(string.replace('\n','}{',1))
    if 'splitline' not in string and len(string)>30:
      part1 = string[:len(string)/2]
      part2 = string[len(string)/2:]
      if ' ' in part2:
        string = "#splitline{"+part1+part2.replace(' ','}{',1)+"}"
      elif ' ' in part1:
        i = part1.rfind(' ')
        string = "#splitline{"+string[:i]+'}{'+string[i+1:]+"}"
  
  # REPLACE PATTERNS (RECURSIVELY)
  match = funcexpr.match(string) # for min(), max(), ...
  if ' / ' in string:
    kwargs['units'] = False
    string = ' / '.join(makelatex(s,**kwargs) for s in string.split(' / '))
  elif match:
    kwargs['units'] = False
    arg1   = makelatex(match.group(2),**kwargs)
    arg2   = makelatex(match.group(3),**kwargs)
    old    = "%s(%s,%s)"%(match.group(1),match.group(2),match.group(3))
    new    = "%s(%s,%s)"%(match.group(1),arg1,arg2)
    string = string.replace(old,new)
    #print ">>> %r -> %r, %r -> %r, %r -> %r, %r"%(match.group(2),arg1,match.group(3),arg2,old,new,string)
  elif '+' in string:
    kwargs['units'] = False
    string = '+'.join(makelatex(s,**kwargs) for s in string.split('+'))
  else:
    strlow = string.lower()
    if "p_" in strlow:
      string = re.sub(r"(?<!i)(p)_([^{}()|<>=\ ]+)",r"\1_{\2}",string,flags=re.IGNORECASE).replace('{t}','{T}')
      GeV    = True
    if re.search(r"(?<!le)(?<!byphoton)(?<!dee)pt(?!weight)",strlow):
      string = re.sub(r"(?<!k)(?<!Dee)(?<!OverTau)(p)[tT]_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",string,flags=re.IGNORECASE)
      string = re.sub(r"\b(?<!Dee)(p)[tT]\b",r"\1_{T}",string,flags=re.IGNORECASE)
      GeV    = True
    if "m_" in strlow:
      string = re.sub(r"(?<!u)(m)_([^{}()|<>=\ \^]+)",r"\1_{\2}",string,flags=re.IGNORECASE).replace('{t}','{T}')
      GeV    = True
    if "mt_" in strlow:
      string = re.sub(r"(m)t_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",string,flags=re.IGNORECASE)
      GeV    = True
    if re.search(r"(?<!weig)(?<!daug)ht",strlow):
      string = re.sub(r"\b(h)t\b",r"\1_{T}",string,flags=re.IGNORECASE)
      GeV    = True
    if " d_" in strlow:
      string = re.sub(r"(\ d)_([^{}()\|<>=\ ]+)",r"\1_{\2}",string,flags=re.IGNORECASE)
      cm     = True
    if "deltar_" in strlow:
      string = re.sub(r"(?<!\#)deltar_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",string,flags=re.IGNORECASE)
    elif "deltar" in strlow:
      string = re.sub(r"(?<!\#)deltar",r"#DeltaR",string,flags=re.IGNORECASE)
    if "dR" in string:
      string = re.sub(r"(?<!\w)dR_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",string)
    if "tau" in strlow:
      #string = re.sub(r"(?<!^)tau(?!\ )",r"#tau",string,re.IGNORECASE)
      string = re.sub(r"(?<!Deep)(?<!Over)tau",r"#tau",string,flags=re.IGNORECASE)
      #string = re.sub(r" #tau ",r" tau ",string,flags=re.IGNORECASE)
      #string = re.sub(r"^#tau ",r"tau ",string,flags=re.IGNORECASE)
      string = re.sub(r"tau_([^{}()^|<>=\ ]+)",r"tau_{\1}",string,flags=re.IGNORECASE)
    if "chi" in strlow:
      string = re.sub(r"(?<!#)chi(?!ng)",r"#chi",string,flags=re.IGNORECASE)
      string = re.sub(r"chi_([^{}()^|<>=\ ]+)",r"chi_{\1}",string,flags=re.IGNORECASE)
    if "phi" in strlow:
      if "dphi" in strlow:
        string = string.replace("dphi","#Delta#phi")
      else:
        string = string.replace("phi","#phi")
      string = re.sub(r"phi_([^{}()|<>=\ ]+)",r"phi_{\1}",string,flags=re.IGNORECASE)
    if "zeta" in strlow and "#zeta" not in strlow:
      if "Dzeta" in string:
        string = string.replace("Dzeta","D_{zeta}")
        GeV    = True
      if "zeta_" in strlow:
        string = re.sub(r"(?<!#)(zeta)_([^{}()|<>=\ ]+)",r"#\1_{\2}",string,flags=re.IGNORECASE)
      else:
        string = re.sub(r"(?<!#)(zeta)",r"#\1",string,flags=re.IGNORECASE)
      GeV      = True
    if "eta" in strlow: #and "#eta" not in strlow and "#zeta" not in strlow and "deta" not in strlow:
      string = string.replace("deta","#Deltaeta")
      string = re.sub(r"(?<!\#[Bbz])eta",r"#eta",string)
      string = re.sub(r"eta_([^{}()|<>=\ ]+)",r"eta_{\1}",string)
    if "abs(" in string and ")" in string:
      string = re.sub(r"abs\(([^)]+)\)",r"|\1|",string)
      #string = string.replace("abs(","|").replace(")","") + "|" # TODO: split at next space
    if "mu" in strlow:
      string = re.sub(r"(?<!VS)mu(?![lo])",r"#mu",string)
      #string = string.replace("mu","#mu").replace("Mu","#mu")
      #string = string.replace("si#mulation","simulation")
    if "nu" in strlow:
      string = re.sub(r"nu(?![pm])",r"#nu",string)
    if "ttbar" in strlow:
      string = re.sub(r"ttbar","t#bar{t}",string,flags=re.IGNORECASE)
    if "npv" in strlow:
      string = re.sub(r"npvs?","number of vertices",string)
    if '->' in string:
      string = string.replace('->','#rightarrow')
    if '=' in string:
      string = string.replace(">=","#geq").replace("<=","#leq")
    string = string.replace('##','#')
  
  # UNITS
  if isinstance(units,str):
    if re.search(r"[(\[].*[)\]]",units):
      string += " "+units.strip()
    else:
      string += " [%s]"%units.strip()
  elif units and not '/' in string:
    if GeV or "mass" in string or "S_{T}" in string or (any(m in string.lower() for m in ["met","p_{t}^{miss}"]) and "phi" not in string):
      if "GeV" not in string:
        string += " [GeV]"
      if cm:
        LOG.warning("makelatex: Flagged units are both GeV and cm!")
    elif cm: #or 'd_' in string
      string += " [cm]"
  if (verbosity>=2 and string!=oldstr) or verbosity>=3:
    print ">>> makelatex: %r -> %r"%(oldstr,string)
  return string
  


def maketitle(title,**kwargs):
  """Make header with LaTeX."""
  kwargs.update({'units':False, 'split':False})
  title = makelatex(title,**kwargs)
  return title
  


def makehistname(*labels,**kwargs):
  """Use label and var to make an unique and valid histogram name."""
  hname = '_'.join(s.strip('_') for s in labels)
  hname = hname.replace('+','-').replace(' - ','-').replace('.','p').replace(',','-').replace(' ','_').replace(
                        '(','-').replace(')','-').replace('[','-').replace(']','-').replace('||','OR').replace('&&','AND').replace(
                        '/','_').replace('<','lt').replace('>','gt').replace('=','e').replace('*','x')
  return hname
  


def makefilename(string,**kwargs):
  """Make string filename safe by replacing inconvenient characters."""
  fname = re.sub(r"(\d+)\.(\d+)",r"\1p\2",string)
  if 'abs(' in fname:
    fname = re.sub(r"abs\(([^\)]*)\)",r"\1",fname).replace('eta_2','eta')
  if 'm_t' in fname:
    fname = re.sub(r"(?<!zoo)m_t(?!au)",r"mt",fname)
  fname = fname.replace(" and ",'-').replace(',','-').replace(',','-').replace('+','-').replace(':','-').replace(
                        '(','').replace(')','').replace('{','').replace('}','').replace(
                        '|','').replace('&','').replace('#','').replace('!','not').replace(
                        'pt_mu','pt').replace('m_T','mt').replace(
                        '>=',"geq").replace('<=',"leq").replace('>',"gt").replace('<',"lt").replace("=","eq").replace(
                        ' ','').replace('GeV','').replace('anti-iso',"antiIso")
  #if 'm_t' in string.lower:
  #  string = re.sub(r"(?<!u)(m)_([^{}\(\)<>=\ ]+)",r"\1_{\2}",string,re.IGNORECASE).replace('{t}','{T}')
  #if "m_" in string.lower():
  #    string = re.sub(r"(?<!u)(m)_([^{}\(\)<>=\ ]+)",r"\1_{\2}",string,re.IGNORECASE).replace('{t}','{T}')
  #if not (".png" in name or ".pdf" in name or ".jpg" in name): name += kwargs.get('ext',".png")
  return fname
  

def joinweights(*weights,**kwargs):
  """Join weight strings multiplicatively."""
  verbosity = LOG.getverbosity(kwargs)
  weights   = [w for w in weights if w and isinstance(w,str)]
  if weights:
    weights = "*".join(weights)
    weights = weights.replace('*/','/')
  else:
    weights = ""
  return weights
  

def joincuts(*cuts,**kwargs):
  """Joins selection strings and apply weight if needed."""
  verbosity = LOG.getverbosity(kwargs)
  cuts      = [c for c in cuts if c and isinstance(c,str)]
  weight    = kwargs.get('weight', False)
  if any('||' in c and not ('(' in c and ')' in c) for c in cuts):
    LOG.warning('joincuts: Be careful with those "or" statements in %s! Not sure how to join...'%(cuts,))
    for i, cut in enumerate(cuts):
      if '||' in cut and not ('(' in cut and ')' in cut):
        cuts[i] = "(%s)"%(cut)
  if weight:
    string = re.sub("\(.+\)","",weight)
    if any(c in string for c in '=<>+-&|'):
      weight = "(%s)"%(weight)
  if cuts:
    cuts = " && ".join(cuts)
    if weight:
      string = re.sub("\(.+\)","",cuts)
      cuts   = "(%s)*%s"%(cuts,weight)
  elif weight:
    cuts = weight
  else:
    cuts = ""
  #print cuts
  return cuts
  

def shift(*args,**kwargs):
  """Shift all jet variable in a given string (e.g. to propagate JEC/JER)."""
  return shiftjetvars(*args,**kwargs)
  

def undoshift(string):
  shiftless = re.sub(r"_[a-zA-Z]+(Up|Down|nom)","",string)
  return shiftless
  

def shiftjetvars(var, jshift, **kwargs):
  """Shift all jet variable in a given string (e.g. to propagate JEC/JER)."""
  vars        = [r'mt_1',r'met(?!filter)'] if "unclusten" in jshift.lower() else\
                [r'jpt_[12]',r'jeta_[12]',r'jets\w*',r'nc?btag\w*',r'mt_1',r'met(?!filter)',r'dphi_ll_bj']
  verbosity   = LOG.getverbosity(kwargs)
  vars        = kwargs.get('vars',  vars )
  varshift    = var[:]
  if re.search(r"(Up|Down)",var):
    LOG.warning('shiftjetvars: Already shifts in "%s"'%(var))
  if len(jshift)>0 and jshift[0]!='_': jshift = '_'+jshift
  for jvar in vars:
    oldvarpattern = r'('+jvar+r')'
    newvarpattern = r"\1%s"%(jshift)
    varshift = re.sub(oldvarpattern,newvarpattern,varshift)
  if verbosity>0:
    print 'shiftjetvars with "%s" shift'%varshift
    print '>>>   "%s"'%var
    print '>>>    -> "%s"'%jshift
  return varshift
  

doubleboolrexp = re.compile(r"(?:&&|\|\|) *(?:&&|\|\|)")
def cleanbool(string):
  """Clean boolean operators."""
  return doubleboolrexp.sub(r"&&",string).strip(' ').strip('&').strip(' ')
  

def invertcharge(oldcuts,target='SS',**kwargs):
  """Help function to find, invert and replace charge selections."""
  verbosity = LOG.getverbosity(kwargs)
  newcuts   = oldcuts
  if oldcuts=="":
    newcuts = "q_1*q_2<0" if target=='OS' else "q_1*q_2>0" if target=='OS' else ""
  else:
    matchOS = re.findall(r"q_[12]\s*\*\s*q_[12]\s*<\s*0",oldcuts)
    matchSS = re.findall(r"q_[12]\s*\*\s*q_[12]\s*>\s*0",oldcuts)
    LOG.verbose("invertcharge: oldcuts=%r"%(oldcuts),verbosity,2)
    LOG.verbose("invertcharge: matchOS=%r, matchSS=%r"%(matchOS,matchSS),verbosity,2)
    if (len(matchOS)+len(matchSS))>1:
      LOG.warning('invertcharge: more than one charge match (%d OS, %d SS) in "%s"'%(len(matchOS),len(matchSS),oldcuts))
    if target=='OS':
      for match in matchSS: newcuts = oldcuts.replace(match,"q_1*q_2<0") # invert SS to OS
    elif target=='SS':
      for match in matchOS: newcuts = oldcuts.replace(match,"q_1*q_2>0") # invert OS to SS
    else:
      for match in matchOS: newcuts = oldcuts.replace(match,"") # REMOVE
      for match in matchSS: newcuts = oldcuts.replace(match,"") # REMOVE
    newcuts = cleanbool(newcuts)
  LOG.verbose('  %r\n>>>   -> %r %s\n>>>'%(oldcuts,newcuts,target),verbosity,2)
  return newcuts
  
