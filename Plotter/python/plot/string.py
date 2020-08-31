# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
import re
from TauFW.Plotter.plot.utils import LOG, unwraplistargs, ensurelist

var_dict = {
    'njets':     "Number of jets",          'njets20':  "Number of jets (pt>20 GeV)",
    'nfjets':    "Number of forward jets",  'nfjets20': "Number of forward jets (pt>20 GeV)",
    'ncjets':    "Number of central jets",  'ncjets20': "Number of central jets (pt>20 GeV)",
    'nbtag':     "Number of b tagged jets", 'nbtag20':  "Number of b tagged jets (pt>20 GeV)",
    'jpt_1':     "Leading jet pt",          'jpt_2':    "Subleading jet pt",
    'bpt_1':     "Leading b jet pt",        'bpt_2':    "Subleading b jet pt",
    'jeta_1':    "Leading jet eta",         'jeta_2':   "Subleading jet eta",
    'beta_1':    "Leading b jet eta",       'beta_2':   "Subleading b jet eta",
    'jphi_1':    "Leading jet phi",         'bphi_1':   "Subleading jet phi",
    'jphi_2':    "Leading b jet phi",       'bphi_2':   "Subleading b jet phi",
    'met':       "p_{T}^{miss}",
    'metphi':    "MET phi",
    'pt_1':      "Lepton pt",               'pt_2':     "tau_h pt",
    'eta_1':     "Lepton eta",              'eta_2':    "tau_h eta",
    'mt_1':      "m_t(l,MET)",              'mt_2':     "m_t(tau,MET)",
    'dzeta':     "D_{zeta}",                'pt_1+pt_2+jpt_1':     "S_{T}^{MET}",
    'pzetavis':  "p_{zeta}^{vis}",          'pt_1+pt_2+jpt_1+met': "S_{T}^{MET}",
    'pzetamiss': "p_{zeta}^{miss}",         'stmet':    "S_{T}^{MET}",
    'DM0':       "h^{#pm}",                 'STMET':    "S_{T}^{MET}",
    'DM1':       "h^{#pm}h^{0}",
    'DM10':      "h^{#pm}h^{#mp}h^{#pm}",
    'DM11':      "h^{#pm}h^{#mp}h^{#pm}h^{0}",
}
var_dict_sorted = sorted(var_dict,key=lambda x: len(x),reverse=True)


funcexpr = re.compile(r"(\w+)\(([^,]+),([^,]+)\)")
def makelatex(string,**kwargs):
  """Convert patterns in a string to LaTeX format."""
  global var_dict_sorted
  verbosity = LOG.getverbosity(kwargs)
  if not isinstance(string,str) or not string:
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
    func   = makelatex(match.group(1),**kwargs)
    arg1   = makelatex(match.group(2),**kwargs)
    arg2   = makelatex(match.group(3),**kwargs)
    old    = "%s(%s,%s)"%(match.group(1),match.group(2),match.group(3))
    new    = "%s(%s,%s)"%(func,arg1,arg2)
    string = string.replace(old,new)
    #print ">>> %r -> %r, %r -> %r, %r -> %r, %r"%(match.group(2),arg1,match.group(3),arg2,old,new,string)
  elif '+' in string:
    kwargs['units'] = False
    string = '+'.join(makelatex(s,**kwargs) for s in string.split('+'))
  else:
    strlow = string.lower().strip()
    if "p_" in strlow:
      string = re.sub(r"(?<!i)(p)_([^{}()|<>=\ ]+)",r"\1_{\2}",string,flags=re.IGNORECASE).replace('{t}','{T}')
      GeV    = True
    if re.search(r"(?<!le)(?<!byphoton)(?<!dee)pt(?!weight)",strlow):
      string = re.sub(r"(?<!k)(?<!Dee)(?<!OverTau)(p)[tT]_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",string,flags=re.IGNORECASE)
      string = re.sub(r"\b(?<!Dee)(p)[tT]\b",r"\1_{T}",string,flags=re.IGNORECASE)
      GeV    = True
    if strlow=="mt":
      string = re.sub(r"(m)(t)",r"\1_{T}",string,flags=re.IGNORECASE)
      GeV    = True
    elif "m_" in strlow:
      string = re.sub(r"(?<!u)(m)_([^{}()|<>=\ \^]+)",r"\1_{\2}",string,flags=re.IGNORECASE).replace('{t}','{T}')
      GeV    = True
    elif "mt_" in strlow:
      string = re.sub(r"(m)t_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",string,flags=re.IGNORECASE)
      GeV    = True
    if re.search(r"(?<!weig)(?<!daug)ht(?!au)",strlow): # HT
      string = re.sub(r"\b(h)t\b",r"\1_{T}",string,flags=re.IGNORECASE)
      GeV    = True
    if strlow[0]=='s' and 't' in strlow[1:3]: # scalar sum pT
      string = re.sub(r"s_?t(?!at)",r"S_{T}",string,flags=re.IGNORECASE)
      string = re.sub(r"met",r"^{MET}",string,flags=re.IGNORECASE)
      GeV    = True
    if " d_" in strlow:
      string = re.sub(r"(\ d)_([^{}()\|<>=\ ]+)",r"\1_{\2}",string,flags=re.IGNORECASE)
      cm     = True
    if "deltar_" in strlow:
      string = re.sub(r"(?<!\#)deltar_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",string,flags=re.IGNORECASE)
    elif "deltar" in strlow:
      string = re.sub(r"(?<!\#)deltar",r"#DeltaR",string,flags=re.IGNORECASE)
    elif "dr_" in strlow:
      string = re.sub(r"(?<!\w)dr_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",string,flags=re.IGNORECASE)
    elif "dr" in strlow:
      string = re.sub(r"(?<![a-z])dr(?![a-z])",r"#DeltaR",string,flags=re.IGNORECASE)
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
    if "tau" in strlow:
      #string = re.sub(r"(?<!^)tau(?!\ )",r"#tau",string,re.IGNORECASE)
      string = re.sub(r"(?<!Deep)(?<!Over)tau",r"#tau",string,flags=re.IGNORECASE)
      #string = re.sub(r" #tau ",r" tau ",string,flags=re.IGNORECASE)
      #string = re.sub(r"^#tau ",r"tau ",string,flags=re.IGNORECASE)
      string = re.sub(r"tau_([^{}()^|<>=\ ]+)",r"tau_{\1}",string,flags=re.IGNORECASE)
      string = re.sub(r"#tauh",r"#tau_{h}",string,flags=re.IGNORECASE)
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
      string = re.sub(r"npvs?","Number of primary vertices",string)
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
    if GeV or "mass" in string or "p_{T}" in string or "S_{T}" in string or (any(m in string.lower() for m in ["met","p_{t}^{miss}"]) and "phi" not in string):
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
  


def makehistname(*strings,**kwargs):
  """Use label and var to make an unique and valid histogram name."""
  hname = '_'.join(getfilename(s).strip('_') for s in strings)
  hname = hname.replace('+','-').replace(' - ','-').replace('.','p').replace(',','-').replace(' ','_').replace(
                        '(','-').replace(')','-').replace('[','-').replace(']','-').replace('||','OR').replace('&&','AND').replace(
                        '/','_').replace('<','lt').replace('>','gt').replace('=','e').replace('*','x')
  return hname
  


def makefilename(*strings,**kwargs):
  """Make string filename safe by replacing inconvenient characters."""
  fname = '_'.join(getfilename(s).strip('_') for s in strings)
  fname = re.sub(r"(\d+)\.(\d+)",r"\1p\2",fname)
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
  

symregx = re.compile(r"#[a-zA-Z]+")
def estimatelen(*strings):
  """Estimate maximum length of list of strings."""
  strings = unwraplistargs(*strings)
  maxlen  = 0
  replace = [
    ('{',''),('}',''),('_',''),('^',''),('#','')
  ]
  for string in strings:
    if not string: continue
    if '\n' in string:
      strlen = estimatelen(string.split('\n'))
    else:
      string = symregx.sub("x",string)
      for old, new in replace:
        string = string.replace(old,new)
      strlen = len(string)
    if strlen>maxlen:
      maxlen = strlen
  return maxlen
  

def match(terms, labels, **kwargs):
  """Match given search terms (strings) to some given list of labels."""
  verbosity = LOG.getverbosity(kwargs)
  terms     = ensurelist(terms, nonzero=True) # search terms
  labels    = ensurelist(labels,nonzero=True) # labels to match to
  found     = True
  regex     = kwargs.get('regex', False ) # use regexpr patterns (instead of glob)
  incl      = kwargs.get('incl',  True  ) # match at least one term; if incl=False ("exclusive"), match every term
  start     = kwargs.get('start', False ) # match only beginning of string
  LOG.verb("match: compare labels=%s -> searchterms=%s (incl=%s,regex=%s)"%(labels,terms,incl,regex),verbosity,3)
  if not terms:
    return False
  for i, searchterm in enumerate(terms):
    if not regex: # convert glob to regexp
      #fnmatch.translate( '*.foo' )
      #searchterm = re.sub(r"(?<!\\)\+",r"\+",searchterm)   # replace + with \+
      #searchterm = re.sub(r"([^\.])\*",r"\1.*",searchterm) # replace * with .*
      searchterm = re.escape(searchterm).replace(r'\?', '.').replace(r'\*', '.*?')
    if start:
      searchterm = '^'+searchterm
    terms[i] = searchterm
  if incl: # inclusive: match only one search term
    for searchterm in terms:
      for label in labels:
        matches = re.findall(searchterm,label)
        if matches:
          LOG.verb("  matched %r -> %r; return True"%(label,searchterm),verbosity,3)
          return True # one search terms is matched
        else:
          LOG.verb("  not matched %r -> %r"%(label,searchterm),verbosity,3)
    return False # no search term was matched
  else: # exclusive: match all search terms
    for searchterm in terms:
      for label in labels:
        matches = re.findall(searchterm,label)
        if matches:
          LOG.verb("  matched %r -> %r"%(label,searchterm),verbosity,3)
          break
        else:
          LOG.verb("  not matched %r -> %r"%(label,searchterm),verbosity,3)
      else:
        return False # this search terms was not matched
    return True # all search terms were matched
  

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
    LOG.warning("shiftjetvars: Already shifts in %r"%(var))
  if len(jshift)>0 and jshift[0]!='_': jshift = '_'+jshift
  for jvar in vars:
    oldvarpattern = r'('+jvar+r')'
    newvarpattern = r"\1%s"%(jshift)
    varshift = re.sub(oldvarpattern,newvarpattern,varshift)
  if verbosity>0:
    print "shiftjetvars with %r shift"%varshift
    print ">>>   %r"%var
    print ">>>    -> %r"%jshift
  return varshift
  

doubleboolrexp = re.compile(r"(?:&&|\|\|) *(?:&&|\|\|)")
def cleanbool(string):
  """Clean boolean operators."""
  return doubleboolrexp.sub(r"&&",string).strip(' ').strip('&').strip(' ')
  

def invertcharge(oldcuts,target='SS',**kwargs):
  """Help function to find, invert and replace charge selections."""
  verbosity = LOG.getverbosity(kwargs)
  oldcuts   = getselstr(oldcuts)
  newcuts   = oldcuts
  if oldcuts=="":
    newcuts = "q_1*q_2<0" if target=='OS' else "q_1*q_2>0" if target=='OS' else ""
  else:
    matchOS = re.findall(r"q_[12]\s*\*\s*q_[12]\s*<\s*0",oldcuts)
    matchSS = re.findall(r"q_[12]\s*\*\s*q_[12]\s*>\s*0",oldcuts)
    LOG.verbose("invertcharge: oldcuts=%r"%(oldcuts),verbosity,2)
    LOG.verbose("invertcharge: matchOS=%r, matchSS=%r"%(matchOS,matchSS),verbosity,2)
    if (len(matchOS)+len(matchSS))>1:
      LOG.warning('invertcharge: more than one charge match (%d OS, %d SS) in %r'%(len(matchOS),len(matchSS),oldcuts))
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
  

###isopattern1 = re.compile(r"(?:idMVA\w+|pfRelIso0._all)_1 *!?[<=>]=? *\d+ *[^|]&* *")
###isopattern2 = re.compile(r"idMVA\w+_2 *!?[<=>]=? *\d+ *[^|]&* *")
###def invertiso(cuts,**kwargs):
###  """Helpfunction to find, invert and replace isolation selections."""
###  
###  verbosity   = LOG.getverbosity(kwargs)
###  channel     = kwargs.get('channel', 'emu' )
###  iso_relaxed = kwargs.get('to',      ''    )
###  remove1     = kwargs.get('remove1', True  )
###  cuts0       = cuts
###  
###  # MATCH isolations
###  match_iso_1 = isopattern1.findall(cuts)
###  match_iso_2 = isopattern2.findall(cuts)
###  LOG.verbose('invertIsolationNanoAOD:\n>>>   match_iso_1 = %r\n>>>   match_iso_2 = %r'%(match_iso_1,match_iso_2),verbosity,level=2)
###  
###  # REPLACE
###  if match_iso_1 and match_iso_2:
###    if len(match_iso_1)>1: LOG.warning("invertIsolationNanoAOD: More than one iso_1 match! cuts=%s"%cuts)
###    if len(match_iso_2)>1: LOG.warning("invertIsolationNanoAOD: More than one iso_2 match! cuts=%s"%cuts)
###    if remove1:
###      cuts = cuts.replace(match_iso_1[0],'')
###    cuts = cuts.replace(match_iso_2[0],'')
###    if iso_relaxed:
###      cuts = combineCuts(cuts,iso_relaxed)
###  elif cuts and match_iso_1 or match_iso_2:
###      LOG.warning('invertIsolationNanoAOD: %d iso_1 and %d iso_2 matches! cuts=%r'%(len(match_iso_1),len(match_iso_2),cuts))
###  cuts = cleanBooleans(cuts)
###  
###  LOG.verbose('  %r\n>>>   -> %r\n>>>'%(cuts0,cuts),verbosity,level=2)
###  return cuts
  

###def relaxjetcuts(cuts,**kwargs):
###  """Helpfunction to find, relax and replace jet selections:
###       1) remove b tag requirements
###       2) relax central jet requirements.
###  """
###  ncjets_relaxed  = "ncjets>1" if "ncjets==2" in cuts.replace(' ','') else "ncjets>0"
###  verbosity       = LOG.getverbosity(kwargs)
###  channel         = kwargs.get('channel', 'mutau'        )
###  btags_relaxed   = kwargs.get('btags',   ""             )
###  cjets_relaxed   = kwargs.get('ncjets',  ncjets_relaxed )
###  cuts0           = cuts
###  
###  # MATCH PATTERNS
###  btags  = re.findall(r"&* *nc?btag(?:20)? *[<=>]=? *\d+ *",cuts)
###  cjets  = re.findall(r"&* *ncjets(?:20)? *[<=>]=? *\d+ *",cuts)
###  cjets += re.findall(r"&* *nc?btag(?:20)? *[<=>]=? *ncjets(?:20)? *",cuts)
###  LOG.verbose('relaxJetSelection:\n>>>   btags = %s\n>>>   cjets = %r' % (btags,cjets),verbosity,level=2)
###  if len(btags)>1: LOG.warning('relaxJetSelection: More than one btags match! Only using first instance in cuts %r'%cuts)
###  if len(cjets)>1: LOG.warning('relaxJetSelection: More than one cjets match! Only using first instance in cuts %r'%cuts)
###  
###  # REPLACE
###  #if len(btags):
###  #    cuts = cuts.replace(btags[0],'')
###  #    if btags_relaxed: cuts = "%s && %s"%(cuts,btags_relaxed)
###  #if len(cjets):
###  #    cuts = cuts.replace(cjets[0],'')
###  #    cuts = "%s && %s"%(cuts,cjets_relaxed)
###  if len(btags) and len(cjets):
###      cuts = cuts.replace(btags[0],'')
###      cuts = cuts.replace(cjets[0],'')
###      if btags_relaxed: cuts = "%s && %s && %s" % (cuts,btags_relaxed,cjets_relaxed)
###      else:             cuts = "%s && %s"       % (cuts,              cjets_relaxed)
###  #elif len(btags) or len(cjets):
###  #    LOG.warning("relaxJetSelection: %d btags and %d cjets matches! cuts=%s"%(len(btags),len(cjets),cuts))
###  cuts = cuts.lstrip(' ').lstrip('&').lstrip(' ')
###  
###  LOG.verbose('  %r\n>>>   -> %r\n>>>'%(cuts0,cuts),verbosity,level=2)
###  return cuts
  

####tgmpatternTT = re.compile(r"genmatch_1 *== *5 *&& *genmatch_2 *== *5")
###tgmpatternJJ = re.compile(r"\( *genmatch_1 *!= *5 *\|\| *genmatch_2 *!= *5 *\)")
###tgmpatternLL = re.compile(r"\(genmatch_2 *> *0 *&& *genmatch_2 *(<|!=) *5\)")
###tidpattern   = re.compile(r"(\* *\( *genmatch_[12] *==[^)]*\?[^)]*\))")
###tgmpattern2  = re.compile(r"(genmatch_2 *(!?[<=>]=? *\d))(?! *\?)")
###tgmpattern1  = re.compile(r"(genmatch_1 *(!?[<=>]=? *\d))(?! *\?)")
###def vetojtf(cuts,**kwargs):
###  """Helpfunction to ensure the jet to tau fakes (genmatch==0) are excluded in selection string.
###     Assume string contains gen_match_2 compared to any digits from 1 to 6.
###   """
###  verbosity  = LOG.getverbosity(kwargs)
###  removeTID  = kwargs.get('noTID',   False    )
###  channel    = kwargs.get('channel', "tautau" ) # TODO: generalize
###  cuts0      = cuts
###  
###  # TAU ID SF
###  if removeTID:
###    cuts     = tidpattern.sub("",cuts)
###  
###  # GENMATCH
###  if "tautau" in channel:
###    match1 = tgmpattern1.findall(cuts)
###    match2 = tgmpattern2.findall(cuts)
###    if len(match1)==0 and len(match2)==0:
###      subcuts0 = stripWeights(cuts)
###      subcuts1 = combineCuts(subcuts0,"genmatch_1>0 && genmatch_2>0")
###      cuts     = cuts.replace(subcuts0,subcuts1)
###      return cuts
###    matchJJ    = tgmpatternJJ.findall(cuts)
###    if matchJJ:
###       cuts = cuts.replace(matchJJ[0],"genmatch_1>0 && genmatch_2>0 && %s"%(matchJJ[0]))
###       return cuts
###    if len(match1)>0:
###      match, genmatch = match1[0]
###      if "!=" in genmatch:
###        if '5' in genmatch:
###          cuts = cuts.replace(match,"(genmatch_1!=5 && genmatch_1>0)")
###        elif '0' not in genmatch:
###          cuts = cuts.replace(match,"genmatch_1>0")
###    if len(match2)>0:
###      match, genmatch = match2[0]
###      if "!=" in genmatch:
###        if '5' in genmatch:
###          cuts = cuts.replace(match,"(genmatch_2!=5 && genmatch_2>0)")
###        elif '0' not in genmatch:
###          cuts = cuts.replace(match,"genmatch_2>0")
###  else:
###    match      = tgmpattern2.findall(cuts)
###    if len(match)==0:
###      subcuts0 = stripWeights(cuts)
###      subcuts1 = combineCuts(subcuts0,"genmatch_2>0")
###      cuts     = cuts.replace(subcuts0,subcuts1)
###      return cuts
###    elif len(match)>1:
###      for match, genmatch in match:
###        if '>0' in genmatch.replace(' ','') or '!=0' in genmatch.replace(' ',''):
###          LOG.warning('vetojtf: more than one "genmatch" match (%d) in %r, ignoring...'%(len(match),cuts))
###          return cuts
###      LOG.warning('vetojtf: more than one "genmatch" match (%d) in %r, only looking at first match...'%(len(match),cuts))
###    match, genmatch = match[0]
###    genmatch = genmatch.replace(' ','')
###    subcuts0 = stripWeights(cuts)
###    subcuts1 = subcuts0
###    
###    if '!=' in genmatch:
###      if '5' in genmatch: # "genmatch_2!=5"
###        subcuts1 = subcuts0.replace(match,"genmatch_2!=5 && genmatch_2>0")
###      elif not '0' in genmatch: # "genmatch_2!=*"
###        subcuts1 = combineCuts(subcuts0,"genmatch_2>0")
###    elif "=0" in genmatch: # "genmatch_2*=6"
###        LOG.warning('vetojtf: selection %r with %r set to "0"!'%(cuts,genmatch)) 
###        subcuts1 = "0"
###    elif '<' in genmatch: # "genmatch_2>*"
###        subcuts1 = combineCuts(subcuts0,"genmatch_2>0")
###    cuts = cuts.replace(subcuts0,subcuts1)
###  
###  #LOG.verbose('  %r\n>>>   -> %r\n>>>'%(cuts0,cuts),verbosity,level=2)
###  return cuts

  
def getfilename(string,**kwargs):
  """Make sure returned object is a string."""
  if hasattr(string,"filename"):
    return string.filename
  return string
  
def getselstr(string,**kwargs):
  """Make sure returned object is a string."""
  if hasattr(string,"selection"): #isinstance(selection,Selection):
    return string.selection
  return string
  

#from TauFW.Plotter.plot.Selection import Selection