#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)

import os, re
from array import array
from copy import copy, deepcopy
from math import sqrt, pow, log
from SettingTools import *
from PrintTools   import *
#from SelectionTools import Selection


varlist = {
    'fjpt_1':          "leading forward jet pt (|eta|>2.4)",
    'fjpt_2':          "subleading forward jet pt (|eta|>2.4)",
    'fjeta_1':         "leading forward jet eta (|eta|>2.4)",
    'fjeta_2':         "subleading forward jet eta (|eta|>2.4)",
    'njets':           "multiplicity of jets",
    'ncjets':          "multiplicity of central jets",                  'nfjets':      "multiplicity of forward jets",
    'nbtag':           "multiplicity of b tagged jets",                 'ncbtag':      "multiplicity of b tagged jets",
    'njets20':         "multiplicity of jets with pt>20 GeV",
    'ncjets20':        "multiplicity of central jets with pt>20 GeV",   'nfjets20': "multiplicity of forward jets with pt>20 GeV",
    'nbtag20':         "multiplicity of b tagged jets with pt>20 GeV",  'ncbtag20': "multiplicity of b tagged jets with pt>20 GeV",
    'njets40':         "multiplicity of jets with pt>40 GeV",
    'ncjets40':        "multiplicity of central jets with pt>40 GeV",   'nfjets40': "multiplicity of forward jets with pt>40 GeV",
    'nbtag40':         "multiplicity of b tagged jets with pt>40 GeV",  'ncbtag40': "multiplicity of b tagged jets with pt>40 GeV",
    'pt_3':            "tau pt",
    'eta_3':           "tau eta",
    'jpt_1':           "leading jet pt",                 'jpt_2':        "subleading jet pt",
    'bpt_1':           "leading b jet pt",               'bpt_2':        "subleading b jet pt",
    'abs(jeta_1)':     "leading jet abs(eta)",           'abs(jeta_2)':  "subleading jet abs(eta)",
    'abs(beta_1)':     "leading b jet abs(eta)",         'abs(beta_2)':  "subleading b jet abs(eta)",
    'jeta_1':          "leading jet eta",                'jeta_2':       "subleading jet eta",
    'beta_1':          "leading b jet eta",              'beta_2':       "subleading b jet eta",
    'beta_1':          "leading b jet eta",              'beta_2':      "subleading b jet eta",
    'pt_tt':           "pt_ltau",                        'R_pt_m_vis':  "R = pt_ltau / m_vis",
    'pt_tt_sv':        "SVFit pt_ltau,sv",               'R_pt_m_sv':   "SVFit R_{sv} = pt_ltau / m_sv",
    'm_sv':            "SVFit mass m_{tautau}",          'dzeta':       "D_{zeta}",
    'dR_ll':           "DeltaR_{ltau}",                  'pzeta_disc':  "D_{zeta}",
    'pfmt_1':          "m_t(l,MET)",                     'pzetavis':    "p_{zeta}^{vis}",
    'dphi_ll_bj':      "Deltaphi_ll',bj",                'pzetamiss':   "p_{zeta}^{miss}",
    'puweight':        "pileup weight",                  'met':         "MET",
    'chargedPionPt_2': "charged pion pt",                'metphi':      "MET phi",
    'neutralPionPt_2': "neutral pion pt",                'pt_genboson': "Z boson pt",
    'DM0':            "h^{#pm}",                         'm_genboson':  "Z boson mass",               
    'DM1':            "h^{#pm}h^{0}",                  
    'DM10':           "h^{#pm}h^{#mp}h^{#pm}",           
    'DM11':           "h^{#pm}h^{#mp}h^{#pm}h^{0}",           
}
varlist_sorted = sorted(varlist,key=lambda x: len(x),reverse=True)

def makeLatex(title,**kwargs):
    """Convert patterns in a string to LaTeX format."""
    
    if not isinstance(title,str): return title
    if title and title[0]=='{' and title[-1]=='}': return title[1:-1]
    units = kwargs.get('units', True  )
    split = kwargs.get('split', False )
    GeV   = False
    cm    = False
    
    #if "jpt" in title:
    #    if   "jpt_1" in title and title.count(">3.0") is 2:
    #        title = "leading forward jet p_{T} (|#eta|>3.0)"
    #    elif "jpt_1" in title and title.count(">2.4") is 2:
    #        title = "leading forward jet p_{T} (|#eta|>2.4)"
    #    elif "jpt_1" in title and title.count("<3.0") is 2:
    #        title = "leading central jet p_{T} (|#eta|<3.0)"
    #    elif "jpt_1" in title and title.count("<2.4") is 2:
    #        title = "leading central jet p_{T} (|#eta|<2.4)"
    #    elif "jpt_1" in title and title.count("<2.4") is 1:
    #        title = "central jpt_1 (|#eta|<2.4)"
    #    elif "jpt_1" in title and title.count(">2.4") is 1:
    #        title = "forward jpt_1 (|#eta|>2.4)"
    #    elif "jpt_1" in title and title.count(">3.0") is 1:
    #        title = "forward jpt_1 (|#eta|>3.0)"
    #    elif "jpt_2" in title and title.count(">3.0") is 1:
    #        title = "forward jpt_2 (|#eta|>3.0)"
    #    elif "jpt_2" in title and title.count(">2.4") is 1:
    #        title = "forward jpt_2 (|#eta|>2.4)"
    #    elif ">" in title or "<" in title or "=" in title:
    #        LOG.warning("makeLatex: Boolean expression detected! How to replace \"%s\"?"%(title))
    #if "_jer" in title:
    #    title = title.replace("_jer","")
    
    
    for var in varlist_sorted:
      if var in title:
          title = title.replace(var,varlist[var])
          #title = re.sub(r"\b%s\b"%var,varlist[var],title,re.IGNORECASE)
          break
    
    if split:
      while '\n' in title:
          title = "#splitline{%s}"%(title.replace('\n','}{',1))
       
      if 'splitline' not in title and len(title)>30:
          part1 = title[:len(title)/2]
          part2 = title[len(title)/2:]
          if ' ' in part2:
            title = "#splitline{"+part1+part2.replace(' ','}{',1)+"}"
          elif ' ' in part1:
            i = part1.rfind(' ')
            title = "#splitline{"+title[:i]+'}{'+title[i+1:]+"}"
    
    strings = [ ]
    for string in title.split(' / '):
        stringlow = string.lower()
        
        if "p_" in stringlow:
            string = re.sub(r"(?<!i)(p)_([^{}()|<>=\ ]+)",r"\1_{\2}",string,flags=re.IGNORECASE).replace('{t}','{T}')
            GeV = True
        
        if "pt" in stringlow and "ptweighted" not in stringlow and "byPhotonPt" not in stringlow:
            string = re.sub(r"(?<!k)(p)[tT]_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",string,flags=re.IGNORECASE)
            string = re.sub(r"\b(p)[tT]\b",r"\1_{T}",string,flags=re.IGNORECASE)
            GeV = True
        
        if "m_" in stringlow:
            string = re.sub(r"(?<!u)(m)_([^{}()|<>=\ \^]+)",r"\1_{\2}",string,flags=re.IGNORECASE).replace('{t}','{T}')
            GeV = True
        
        if "mt_" in stringlow:
            string = re.sub(r"(m)t_([^{}()|<>=\ ]+)",r"\1_{T}^{\2}",string,flags=re.IGNORECASE)
            GeV = True
        
        if "ht" in stringlow and "weight" not in stringlow:
            string = re.sub(r"\b(h)t\b",r"\1_{T}",string,flags=re.IGNORECASE)
            GeV = True
        
        if " d_" in stringlow:
            string = re.sub(r"(\ d)_([^{}()\|<>=\ ]+)",r"\1_{\2}",string,flags=re.IGNORECASE)
            cm = True
        
        if "deltar_" in stringlow:
            string = re.sub(r"(?<!\#)deltar_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",string,flags=re.IGNORECASE)
        elif "deltar" in stringlow:
            string = re.sub(r"(?<!\#)deltar",r"#DeltaR",string,flags=re.IGNORECASE)
        
        if "dR" in string:
            string = re.sub(r"(?<!\w)dR_([^{}()|<>=\ ]+)",r"#DeltaR_{\1}",string)
        
        if "tau" in stringlow:
            #string = re.sub(r"(?<!^)tau(?!\ )",r"#tau",string,re.IGNORECASE)
            string = re.sub(r"tau",r"#tau",string,flags=re.IGNORECASE)
            string = re.sub(r" #tau ",r" tau ",string,flags=re.IGNORECASE)
            string = re.sub(r"^#tau ",r"tau ",string,flags=re.IGNORECASE)
            string = re.sub(r"tau_([^{}()|<>=\ ]+)",r"tau_{\1}",string,flags=re.IGNORECASE)
        
        if "phi" in stringlow:
            if "dphi" in stringlow:
              string = string.replace("dphi","#Delta#phi")
            else:
              string = string.replace("phi","#phi")
            string = re.sub(r"phi_([^{}()|<>=\ ]+)",r"phi_{\1}",string,flags=re.IGNORECASE)
        
        if "zeta" in stringlow and "#zeta" not in stringlow:
            if "Dzeta" in string:
                string = string.replace("Dzeta","D_{zeta}")
                GeV = True
            if "zeta_" in stringlow:
                string = re.sub(r"(?<!#)(zeta)_([^{}()|<>=\ ]+)",r"#\1_{\2}",string,flags=re.IGNORECASE)
            else:
                string = re.sub(r"(?<!#)(zeta)",r"#\1",string,flags=re.IGNORECASE)
            GeV = True
        
        if "eta" in stringlow: #and "#eta" not in stringlow and "#zeta" not in stringlow and "deta" not in stringlow:
            string = string.replace("deta","#Deltaeta")
            string = re.sub(r"(?<!\#[Bbz])eta",r"#eta",string)
            string = re.sub(r"eta_([^{}()|<>=\ ]+)",r"eta_{\1}",string)
        
        if "abs(" in string and ")" in string:
            string = re.sub(r"abs\(([^)]+)\)",r"|\1|",string)
            #string = string.replace("abs(","|").replace(")","") + "|" # TODO: split at next space
        
        if  "mu" in stringlow:
            string = re.sub(r"mu(?![lo])",r"#mu",string)
            #string = string.replace("mu","#mu").replace("Mu","#mu")
            #string = string.replace("si#mulation","simulation")
        
        if "ttbar" in stringlow:
            string = re.sub(r"ttbar","t#bar{t}",string,flags=re.IGNORECASE)
        
        if "npv" in stringlow:
            string = string.replace("npv","number of vertices")
        
        if '->' in string:
            string = string.replace('->','#rightarrow')
        
        if "=" in string:
            string = string.replace(">=","#geq").replace("<=","#leq")
        
        strings.append(string.replace('##','#'))
    
    newtitle = ' / '.join(strings)
    
    if units and not '/' in newtitle:
      if isinstance(units,str):
        if re.search(r"[(\[].*[)\]]",newtitle):
          newtitle += " "+units
        else:
          newtitle += " [%s]"%units
      elif GeV or "mass" in newtitle or ("met" in newtitle.lower() and "phi" not in newtitle ):
        if "GeV" not in newtitle:
          newtitle += " [GeV]"
        if cm:
          LOG.warning("makeLatex: Flagged units are both GeV and cm!")
      elif cm:
        newtitle += " [cm]"
    
    return newtitle
    


def makeTitle(title,**kwargs):
    """Make header with LaTeX."""
    kwargs.update({'units':False, 'split':False})
    title = makeLatex(title,**kwargs)
    return title
    
def makeHistName(*labels,**kwargs):
    """Use label and var to make an unique and valid histogram name."""
    hist_name = '_'.join(labels)
    hist_name = hist_name.replace('+','-').replace(' - ','-').replace('.','p').replace(',','-').replace(' ','_').replace(
                                  '(','-').replace(')','-').replace('[','-').replace(']','-').replace(
                                  '/','').replace('<','lt').replace('>','gt').replace('=','e').replace('*','x')
    return hist_name
    
def makeFileName(string,**kwargs):
    """Make filename without inconvenient character."""
    string = re.sub(r"(\d+)\.(\d+)",r"\1p\2",string)
    if 'abs(' in string:
      string = re.sub(r"abs\(([^\)]*)\)",r"\1",string).replace('eta_2','eta')
    if 'm_t' in string:
      string = re.sub(r"m_t(?!au)",r"mt",string)
    string = string.replace(" and ",'-').replace(',','-').replace('(','').replace(')','').replace('{','').replace('}','').replace(':','-').replace(
                            '|','').replace('&','').replace('#','').replace('!','not').replace(
                            'pt_mu','pt').replace('m_T','mt').replace(
                            '>=',"geq").replace('<=',"leq").replace('>',"gt").replace('<',"lt").replace("=","eq").replace(
                            ' ','').replace('GeV','').replace('anti-iso',"antiIso")
    #if 'm_t' in string.lower:
    #  string = re.sub(r"(?<!u)(m)_([^{}\(\)<>=\ ]+)",r"\1_{\2}",string,re.IGNORECASE).replace('{t}','{T}')
    #if "m_" in string.lower():
    #    string = re.sub(r"(?<!u)(m)_([^{}\(\)<>=\ ]+)",r"\1_{\2}",string,re.IGNORECASE).replace('{t}','{T}')
    #if not (".png" in name or ".pdf" in name or ".jpg" in name): name += kwargs.get('ext',".png")
    return string
    


def shift(string, jshift, **kwargs):
    """Shift all jet variable in a given string (e.g. to propagate JEC/JER)."""
    return shiftJetVariable( string, jshift, **kwargs)
    
def shiftJetVariable(var, jshift, **kwargs):
    """Shift all jet variable in a given string (e.g. to propagate JEC/JER)."""
    
    vars        = [r'pfmt_1',r'met'] if "uncen" in jshift.lower() else\
                  [r'jpt_[12]',r'jeta_[12]',r'jets(?:20)?',r'nc?btag(?:20)?(?:_noTau)?',r'pfmt_1',r'met',r'dphi_ll_bj']
    verbosity   = getVerbosity(kwargs,verbosityVariableTools)
    vars        = kwargs.get('vars',  vars )
    varShift    = var[:]
    if re.search(r"(Up|Down)",var):
      LOG.warning('shiftJetVariable: Already shifts in "%s"'%(var))
    if len(jshift)>0 and jshift[0]!='_': jshift = '_'+jshift
    if "jets20" in var: LOG.warning('shiftJetVariable: "jets20" in var')
    for jvar in vars:
        oldvarpattern = r'('+jvar+r')'
        newvarpattern = r"\1%s"%(jshift)
        varShift = re.sub(oldvarpattern,newvarpattern,varShift)
    LOG.verbose('shiftJetVariable with "%s" shift\n>>>   "%s"\n>>>     -> "%s"'%(jshift,var,varShift), verbosity)
    return varShift
    
def undoShift(string):
    shiftless = re.sub(r"_[a-zA-Z]+(Up|Down|nom)","",string)
    return shiftless


class Variable(object):
    """
    Variable class to:
       - hold all relevant information of a variable that will be plotted;
           var name, filename friendly name, LaTeX friendly title, binning, ...
       - allow for variable binning into TH1
       - allow for contextual binning, i.e. depending on channel/selection/...
       - easy string conversions: filename, LaTeX, ...
       - analysis-specific operations: applying variations, ...
    """
    
    def __init__(self, name, *args, **kwargs):
        strings              = [a for a in args if isinstance(a,str) ]
        self.name            = name
        self.title           = strings[0] if strings else self.name
        self.title           = kwargs.get('title',          self.title                  ) # for plot axes
        self.filename        = kwargs.get('filename',       makeFileName(self.name)     ) # for file
        self.filename        = self.filename.replace('$NAME',self.name).replace('$VAR',self.name)
        self.units           = kwargs.get('units',          True                        ) # for plot axes
        self.latex           = kwargs.get('latex',          True                        ) # for plot axes
        self.nbins           = None
        self.min             = None
        self.max             = None
        self.xbins           = None
        self.setBinning(*args)
        self.data            = kwargs.get('data',           True                        ) # also draw data
        self.binlabels       = kwargs.get('binlabels',      [ ]                         )
        self.ymin            = kwargs.get('ymin',           None                        )
        self.ymax            = kwargs.get('ymax',           None                        )
        self.logx            = kwargs.get('logx',           False                       )
        self.logy            = kwargs.get('logy',           False                       )
        self.ymargin         = kwargs.get('ymargin',        1.80 if self.logy else 1.16 )
        self.position        = kwargs.get('position',       ""                          ) # legend position
        self.ncolumns        = kwargs.get('ncolumns',       1                           ) # legend position
        #self.plot            = kwargs.get('plots',          True                        )
        self.only            = kwargs.get('only',           [ ]                         )
        self.veto            = kwargs.get('veto',           [ ]                         )
        self.blind           = kwargs.get('blind',          ""                          )
        self.contexttitle    = getContextFromDict(kwargs, None, key='ctitle'                ) # context-dependent title
        self.contextbinning  = getContextFromDict(kwargs, args, key='cbinning',  regex=True ) # context-dependent binning
        self.contextposition = getContextFromDict(kwargs, self.position, key='cposition', regex=True ) # context-dependent position
        self.contextblind    = getContextFromDict(kwargs, self.blind, key='cblind', regex=True ) # context-dependent blind limits
        if self.latex:
          self.title = makeLatex(self.title,units=self.units)
        if self.only:
          if not isList(self.only): self.only = [ self.only ]
        if self.veto:
          if not isList(self.veto): self.veto = [ self.veto ]
        if self.binlabels and len(self.binlabels)<self.nbins:
          LOG.warning("Variable::init: len(binlabels)=%d < %d=nbins"%(len(self.binlabels),self.nbins))
        
    
    @property
    def var(self): return self.name
    @var.setter
    def var(self,value): self.name = value
    
    @property
    def N(self): return self.nbins
    @N.setter
    def N(self,value): self.nbins = value
    
    @property
    def a(self): return self.min
    @a.setter
    def a(self,value): self.a = value
    
    @property
    def b(self): return self.max
    @b.setter
    def b(self,value): self.b = value
    
    @property
    def xmin(self): return self.min
    @xmin.setter
    def xmin(self,value): self.xmin = value
    
    @property
    def xmax(self): return self.max
    @xmax.setter
    def xmax(self,value): self.xmax = value
    
    def __str__(self):
      """Returns string representation of Variable object."""
      return self.name
    
    def __repr__(self):
      """Returns string representation of Variable object."""
      #return '<%s.%s("%s","%s",%s,%s,%s)>'%(self.__class__.__module__,self.__class__.__name__,self.name,self.title,self.nbins,self.xmin,self.xmax)
      return '<%s("%s","%s",%s,%s,%s) at %s>'%(self.__class__.__name__,self.name,self.title,self.nbins,self.xmin,self.xmax,hex(id(self)))
    
    def __iter__(self):
      """Start iteration over variable information."""
      for i in [self.name,self.nbins,self.min,self.max]:
        yield i
    
    def printWithBinning(self):
        return '%s(%s,%s,%s)'%(self.name,self.nbins,self.xmin,self.xmax)
    
    def setBinning(self,*args):
        """Set binning: (N,min,max), or xbins if it is set"""
        numbers         = [a for a in args if isNumber(a) ]
        xbins           = [a for a in args if isList(a)   ]
        if len(numbers)==3:
          self.nbins    = numbers[0]
          self.min      = numbers[1]
          self.max      = numbers[2]
          self.xbins    = None
        elif len(xbins)>0:
          xbins         = xbins[0]
          self.nbins    = len(xbins)-1
          self.min      = xbins[0]
          self.max      = xbins[-1]
          self.xbins    = xbins #array('d',list(xbins))
        else:
          print error('Variable: bad arguments "%s" for binning!'%(args,))
          exit(1)
    
    def getBinning(self):
        """Get binning: (N,xmin,xmax), or xbins if it is set"""
        if self.hasVariableBinning():
          return self.xbins
        else:
          return (self.nbins,self.min,self.max)
    
    def hasVariableBinning(self):
        """True is xbins is set."""
        return self.xbins != None
    
    def isPartOf(self, *searchterms, **kwargs):
        """Check if all labels are in the variable's name, title."""
        searchterms = [l for l in searchterms if l!='']
        if not searchterms: return False
        found       = True
        regex       = kwargs.get('regex',       False   )
        exlcusive   = kwargs.get('exclusive',   True    )
        for searchterm in searchterms:
          if not regex:
            searchterm = re.sub(r"([^\.])\*",r"\1.*",searchterm) # replace * with .*
          if exlcusive:
            for varlabel in [self.name,self.title]:
                matches    = re.findall(searchterm,varlabel)
                if matches: break # try next searchterm, or return True
            else: return False # none of the labels contain the searchterm
          else: # inclusive
            for varlabel in [self.name,self.title]:
                matches    = re.findall(searchterm,varlabel)
                if matches: return True # one of the searchterm has been found
        return exlcusive
    
    def changeContext(self,*args):
        """Change the contextual title, binning or position for a set of arguments, if it is available"""
        if self.contexttitle:
          title = self.contexttitle.getContext(*args)
          if title!=None: self.title = title
        if self.contextbinning:
          binning = self.contextbinning.getContext(*args)
          if isinstance(binning,list): binning = (binning,)
          if binning!=None: self.setBinning(*binning)
        if self.contextposition:
          position = self.contextposition.getContext(*args)
          if position!=None: self.position = position
        #if self.contextplot:
        #  plot = self.contextplot.getContext(*args)
        #  if binning!=None: self.plot = plot
    
    def plotForSelection(self,selection,**kwargs):
        """Check is selection is vetoed for this variable."""
        verbosity = getVerbosity(kwargs,verbosityVariableTools)
        if not isinstance(selection,str):
          selection = selection.selection
        for searchterm in self.veto:
          if re.search(searchterm,selection):
            LOG.verbose('Variable::plotForSelection: Regex match of selection "%s" to "%s"'%(selection,searchterm),verbosity,level=2)
            return False
        for searchterm in self.only:
          if re.search(searchterm,selection):
            LOG.verbose('Variable::plotForSelection: Regex match of selection "%s" to "%s"'%(selection,searchterm),verbosity,level=2)
            return True
        return len(self.only)==0
    
    def unwrap(self):
        return (self.name,self.nbins,self.min,self.max)
    
    #def latex(self):
    #    return makeLatex(self.name)
    
    def shift(self,jshift,**kwargs):
        if len(jshift)>0 and jshift[0]!='_':
          jshift = '_'+jshift
        newname               = shift(self.name,jshift,**kwargs)
        newvariable           = deepcopy(self)
        newvariable.name      = newname
        if self.name != newname:
          newvariable.filename += jshift
        return newvariable
    
    def shiftName(self,jshift,**kwargs):
        return shift(self.name,jshift,**kwargs)
    
def var(*args,**kwargs):
    """Shorthand for Variable class."""
    return Variable(*args,**kwargs)

def wrapVariable(*args,**kwargs):
    """Help function to wrap variable arguments into a Variable object."""
    if   len(args) == 4 or len(args) == 5:
      return Variable(args) # (varname,N,a,b)
    elif len(args) == 1 and isinstance(args[0],Variable):
      return args[0]
    LOG.warning('wrapVariable: Could not unwrap arguments "%s" to a Variable object. Returning None.'%args)
    return None

def unwrapVariableBinning(*args,**kwargs):
    """Help function to unwrap variable arguments to return variable name, number of bins,
    minumum and maximum x axis value."""
    if   len(args) == 4:
      return (varname,N,a,b)
    elif len(args) == 1 and isintance(args[0],Variable):
      return args[0].unwrap()
    LOG.warning('unwrapVariableBinning: Could not unwrap arguments "%s" to a Variable object. Returning None.'%args)
    return None



class Context(object):
    """
    Context class to save different objects that depend on a certain context 
    TODO: point to specific attribute ?
    TODO: allow to set context for pattern (e.g. selection string)
    """
    
    def __init__(self, context_dict, *args, **kwargs):
        if not isinstance(context_dict,dict):
          LOG.warning("Context::Context: No dictionary given!")
        self.context = context_dict
        self.default = args[0] if len(args)>0 else context_dict.get('default',None)
        self.regex   = kwargs.get('regex',False)
        
    def __iter__(self):
        """Start iteration over selection information."""
        for i in self.context:
          yield i
        
    def getContext(self,*args,**kwargs):
        """Get the contextual object for a set of ordered arguments. If it is not available, return Default."""
        
        regex = kwargs.get('regex', self.regex)
        
        # CHECK
        if len(args)==0:
          LOG.warning("Context::getContext: No arguments given!")
          return self.default
        if not self.context:
          LOG.warning("Context::getContext: No context dictionary!")
          return None
        
        # MATCH
        ckey = args[0]
        if regex:
          for key in sorted(self.context,key=lambda x: len(x),reverse=True):
            #LOG.verbose('Context::getContext: Matching "%s" to "%s"'%(key,ckey),True)
            if re.search(key,ckey):
              #LOG.verbose('Context::getContext: Regex match of key "%s" to "%s"'%(key,ckey),True)
              ckey = key
              break
          else:
              return self.default
        elif ckey not in self.context:
          return self.default
        result = self.context[ckey]
        
        # RESULT
        if isinstance(result,Context):
          return result.getContext(*args[1:],**kwargs) # recursive
        else:
          return result
        

def getContextFromDict(contextdict,*default,**kwargs):
    """Check for context in contextdict. If a dictionary is given, make a Context object. Else return None."""
    ckey    = kwargs.get('key',         'context'   )
    regex   = kwargs.get('regex',       False       )
    context = contextdict.get(ckey,     None        ) # context-dependent
    if isinstance(context,Context):
        return context
    if isinstance(context,dict):
        if len(default)==0: default = context.get('default', None)
        else: default = default[0]
        context = Context(context,default,regex=regex)
        return context
    elif not context:
        return None
    LOG.error('getContext - No valid arguments "%s"'%(args))
    return None


