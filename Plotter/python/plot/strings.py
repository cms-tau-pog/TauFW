#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
import re
from TauFW.Plotter.plot.utils import LOG

varlist = {
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
varlist_sorted = sorted(varlist,key=lambda x: len(x),reverse=True)


def makelatex(string,**kwargs):
  """Convert patterns in a string to LaTeX format."""
  verbosity = LOG.getverbosity(kwargs)
  if not isinstance(string,str):
    return string
  if string and string[0]=='{' and string[-1]=='}':
    return string[1:-1]
  units = kwargs.get('units', True  )
  split = kwargs.get('split', False )
  GeV   = False
  cm    = False
  
  # PREDEFINED
  for var in varlist_sorted:
    if var in string:
      string = string.replace(var,varlist[var])
      #string = re.sub(r"\b%s\b"%var,varlist[var],string,re.IGNORECASE)
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
  
  # REPLACE PATTERNS
  strings = [ ]
  for substr in string.split(' / '):
    strlow = substr.lower()
    if "p_" in strlow:
      substr = re.sub(r"(?<!i)(p)_([^{}()|<>=\ ]+)",r"\1_{\2}",substr,flags=re.IGNORECASE).replace('{t}','{T}')
      GeV    = True
    if re.search(r"(?<!le)(?<!byphoton)(?<!dee)pt(?!weight)",strlow):
      substr = re.sub(r"(?<!k)(?<!Dee)(?<!OverTau)(p)[tT]_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",substr,flags=re.IGNORECASE)
      substr = re.sub(r"\b(?<!Dee)(p)[tT]\b",r"\1_{T}",substr,flags=re.IGNORECASE)
      GeV    = True
    if "m_" in strlow:
      substr = re.sub(r"(?<!u)(m)_([^{}()|<>=\ \^]+)",r"\1_{\2}",substr,flags=re.IGNORECASE).replace('{t}','{T}')
      GeV    = True
    if "mt_" in strlow:
      substr = re.sub(r"(m)t_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",substr,flags=re.IGNORECASE)
      GeV    = True
    if re.search(r"(?<!weig)(?<!daug)ht",strlow):
      substr = re.sub(r"\b(h)t\b",r"\1_{T}",substr,flags=re.IGNORECASE)
      GeV    = True
    if " d_" in strlow:
      substr = re.sub(r"(\ d)_([^{}()\|<>=\ ]+)",r"\1_{\2}",substr,flags=re.IGNORECASE)
      cm     = True
    if "deltar_" in strlow:
      substr = re.sub(r"(?<!\#)deltar_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",substr,flags=re.IGNORECASE)
    elif "deltar" in strlow:
      substr = re.sub(r"(?<!\#)deltar",r"#DeltaR",substr,flags=re.IGNORECASE)
    if "dR" in substr:
      substr = re.sub(r"(?<!\w)dR_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",substr)
    if "tau" in strlow:
      #substr = re.sub(r"(?<!^)tau(?!\ )",r"#tau",substr,re.IGNORECASE)
      substr = re.sub(r"(?<!Deep)(?<!Over)tau",r"#tau",substr,flags=re.IGNORECASE)
      #substr = re.sub(r" #tau ",r" tau ",substr,flags=re.IGNORECASE)
      #substr = re.sub(r"^#tau ",r"tau ",substr,flags=re.IGNORECASE)
      substr = re.sub(r"tau_([^{}()^|<>=\ ]+)",r"tau_{\1}",substr,flags=re.IGNORECASE)
    if "chi" in strlow:
      substr = re.sub(r"(?<!#)chi(?!ng)",r"#chi",substr,flags=re.IGNORECASE)
      substr = re.sub(r"chi_([^{}()^|<>=\ ]+)",r"chi_{\1}",substr,flags=re.IGNORECASE)
    if "phi" in strlow:
      if "dphi" in strlow:
        substr = substr.replace("dphi","#Delta#phi")
      else:
        substr = substr.replace("phi","#phi")
      substr = re.sub(r"phi_([^{}()|<>=\ ]+)",r"phi_{\1}",substr,flags=re.IGNORECASE)
    if "zeta" in strlow and "#zeta" not in strlow:
      if "Dzeta" in substr:
        substr = substr.replace("Dzeta","D_{zeta}")
        GeV    = True
      if "zeta_" in strlow:
        substr = re.sub(r"(?<!#)(zeta)_([^{}()|<>=\ ]+)",r"#\1_{\2}",substr,flags=re.IGNORECASE)
      else:
        substr = re.sub(r"(?<!#)(zeta)",r"#\1",substr,flags=re.IGNORECASE)
      GeV      = True
    if "eta" in strlow: #and "#eta" not in strlow and "#zeta" not in strlow and "deta" not in strlow:
      substr = substr.replace("deta","#Deltaeta")
      substr = re.sub(r"(?<!\#[Bbz])eta",r"#eta",substr)
      substr = re.sub(r"eta_([^{}()|<>=\ ]+)",r"eta_{\1}",substr)
    if "abs(" in substr and ")" in substr:
      substr = re.sub(r"abs\(([^)]+)\)",r"|\1|",substr)
      #substr = substr.replace("abs(","|").replace(")","") + "|" # TODO: split at next space
    if "mu" in strlow:
      substr = re.sub(r"(?<!VS)mu(?![lo])",r"#mu",substr)
      #substr = substr.replace("mu","#mu").replace("Mu","#mu")
      #substr = substr.replace("si#mulation","simulation")
    if "nu" in strlow:
      substr = re.sub(r"nu(?![pm])",r"#nu",substr)
    if "ttbar" in strlow:
      substr = re.sub(r"ttbar","t#bar{t}",substr,flags=re.IGNORECASE)
    if "npv" in strlow:
      substr = re.sub(r"npvs?","number of vertices",substr)
    if '->' in substr:
      substr = substr.replace('->','#rightarrow')
    if "=" in substr:
      substr = substr.replace(">=","#geq").replace("<=","#leq")
    strings.append(substr.replace('##','#'))
  newstr = ' / '.join(strings)
  
  # UNITS
  if isinstance(units,str):
    if re.search(r"[(\[].*[)\]]",units):
      newstr += " "+units.strip()
    else:
      newstr += " [%s]"%units.strip()
  elif units and not '/' in newstr:
    if GeV or "mass" in newstr or "S_{T}" in newstr or (any(m in newstr.lower() for m in ["met","p_{T}^{miss}"]) and "phi" not in newstr):
      if "GeV" not in newstr:
        newstr += " [GeV]"
      if cm:
        LOG.warning("makelatex: Flagged units are both GeV and cm!")
    elif cm: #or 'd_' in newstr
      newstr += " [cm]"
  
  return newstr
  


def maketitle(title,**kwargs):
  """Make header with LaTeX."""
  kwargs.update({'units':False, 'split':False})
  title = makelatex(title,**kwargs)
  return title
  


def makehistname(*labels,**kwargs):
  """Use label and var to make an unique and valid histogram name."""
  hname = '_'.join(labels)
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
  


def shift(*args,**kwargs):
  """Shift all jet variable in a given string (e.g. to propagate JEC/JER)."""
  return shiftjetvars(*args,**kwargs)
  


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
  


def undoshift(string):
  shiftless = re.sub(r"_[a-zA-Z]+(Up|Down|nom)","",string)
  return shiftless
  

