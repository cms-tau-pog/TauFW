#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)

import re
from ctypes import c_double
from math import sqrt, pow
from copy import copy, deepcopy
from collections import namedtuple as ntuple
from ROOT import gROOT, TFile, TTree, TH1F, TH1D, TH2F, TH2D, gDirectory, TColor, \
                 kAzure, kBlack, kBlue, kCyan, kGray, kGreen, kMagenta, kOrange, kPink, kRed, kSpring, kTeal, kWhite, kViolet, kYellow
from SettingTools import *
if loadMacros:
  ###gROOT.Macro('PlotTools/weightJEta1.C+')
  if doFakeRate:
    gROOT.Macro('PlotTools/fakeRate/fakeRate.C+')
    #gROOT.ProcessLine('TString MVArerunv2 = "MVArerunv2"; TString MVArerunv1new = "MVArerunv1new";')
  elif doQCD:
    gROOT.Macro('PlotTools/QCD/QCD.C+') 
  gROOT.Macro('PlotTools/leptonTauFake/leptonTauFake.C+')
  gROOT.Macro('PlotTools/Zpt/zptweight.C+')
  gROOT.Macro('PlotTools/pileup/pileup.C+')
  ###gROOT.Macro("prefire/prefireAnalysis.C+") # TODO: COMMENT OUT !!!
  

colors_HTT_dict = {
  'TT':   kBlue-8,                         'DY':          kOrange-4,
  'TTT':  kAzure-9,                        'ZL':          TColor.GetColor(100,182,232), #kAzure+5,
  'TTJ':  kBlue-8,                         'ZJ':          kGreen-6,
  'TTL':  kGreen-6,                        'ZTT':         kOrange-4,
  'ST':   TColor.GetColor(140,180,220),    'ZTT_DM0':     kOrange+5,
  'STJ':  kMagenta-8,                      'ZTT_DM1':     kOrange-4, #kOrange,
  'QCD':  kMagenta-10,                     'ZTT_DM10':    kYellow-9,
  'data': kBlack,                          'ZTT_DM11':    kOrange-6,
  'WJ':   50,                              'ZTT_DMother': kOrange-8,
  'VV':   TColor.GetColor(222,140,106),    'DY10':        TColor.GetColor(240,175,60), #TColor.GetColor(222,90,106)
  'sig':  kBlue
}
colors_IWN_dict = {
  'TT':   kRed-2,        'DY':          kGreen-2,
  'TTT':  kRed-2,        'ZL':          kAzure+5,
  'TTJ':  kOrange+9,     'ZJ':          kSpring-7, #kGreen-7,
  'TTL':  kRed+1,        'DY10':        kAzure+5,
  'ST':   kMagenta-3,    'ZTT_DM0':     kOrange,
  'STJ':  kMagenta+3,    'ZTT_DM1':     kOrange+5,
  'QCD':  kRed-7,        'ZTT_DM10':    kYellow-9,
  'data': kBlack,        'ZTT_DM11':    kYellow-3, #kOrange+6
  'WJ':   kOrange-5,     'ZTT_DMother': kOrange-6, #kOrange+6
  'VV':   kYellow-7, #+771,
  'sig':  kAzure+4,
}
colors_sample_dict = { }


def setSampleColorDict(col_dict):
    global colors_sample_dict
    colors_sample_dict = {  
      "TT":               col_dict['TT'],         'DY':          col_dict['DY'],
      'TTT':              col_dict['TTT'],        'ZTT':         col_dict['DY'],
      'TTL':              col_dict['TTL'],        'ZL':          col_dict['ZL'],
      'TTJ':              col_dict['TTJ'],        'ZJ':          col_dict['ZJ'],
      'ttbar':            col_dict['TT'],         'Drel*Yan':    col_dict['DY'],
      'ttbar*real*tau':   col_dict['TTT'],        'Z*tau':       col_dict['DY'],
      'ttbar*l':          col_dict['TTL'],        'Z*ll':        col_dict['ZL'],
      'ttbar*j':          col_dict['TTJ'],        'Z*j*tau':     col_dict['ZJ'],
      'ttbar*other':      col_dict['TTJ'],        'D*Y*l*tau':   col_dict['ZL'],
      'ST':               col_dict['ST'],         'D*Y*other':   col_dict['ZJ'], #kSpring+3, kPink-2
      'single top':       col_dict['ST'],         'D*Y*10*50':   col_dict['DY10'],
      'STT':              col_dict['ST'],         'D*Y*50':      col_dict['DY'],
      'STJ':              col_dict['STJ'],        'ZTT_DM0':     col_dict['ZTT_DM0'],     'Z*tau*DM0':   col_dict['ZTT_DM0'],
      'single top*real':  col_dict['ST'],         'ZTT_DM1':     col_dict['ZTT_DM1'],     'Z*tau*DM1':   col_dict['ZTT_DM1'],
      'single top*other': col_dict['STJ'],        'ZTT_DM10':    col_dict['ZTT_DM10'],    'Z*tau*DM10':  col_dict['ZTT_DM10'],
      'QCD':              col_dict['QCD'],        'ZTT_DM11':    col_dict['ZTT_DM11'],    'Z*tau*DM11':  col_dict['ZTT_DM11'],
      'JTF':              col_dict['QCD'],        'ZTT_DMother': col_dict['ZTT_DMother'], 'Z*tau*other': col_dict['DY10'],
      'fake*rate':        col_dict['QCD'],        'W*jets':      col_dict['WJ'],
      'j*tau*fake':       col_dict['QCD'],        'W*J':         col_dict['WJ'],
      'signal':           col_dict['sig'],        'W':           col_dict['WJ'],
      'VLQ':              col_dict['sig'],        'WW':          col_dict['VV'],
      'bbA':              col_dict['sig'],        'WZ':          col_dict['VV'],
      'data':             col_dict['data'],       'ZZ':          col_dict['VV'],
      'single muon':      col_dict['data'],       'VV':          col_dict['VV'],
      'single electron':  col_dict['data'],       'diboson':     col_dict['VV'],
      'observed':         col_dict['data'],       'electroweak': col_dict['VV'],
    }
setSampleColorDict(colors_IWN_dict if 'IWN' in colorset else colors_HTT_dict)

sample_dict = {
  'TT':        "ttbar",                         'DY':       "Drell-Yan",
  'TTT':       "ttbar with real tau_h",         'ZTT':      "Z -> tau_{mu}tau_{h}",
  'TTJ':       "ttbar other",                   'ZTT_DM0':  "Z -> tau_{mu}tau_{h}, h^{#pm}",
  'TTL':       "ttbar with l -> tau_h",         'ZTT_DM1':  "Z -> tau_{mu}tau_{h}, h^{#pm}#pi^{0}",
  'ST':        "single top",                    'ZTT_DM10': "Z -> tau_{mu}tau_{h}, h^{#pm}h^{#mp}h^{#pm}",
  'STT':       "single top with real tau_h",    'ZL':       "Drell-Yan with l -> tau_h",
  'STJ':       "single top other",              'ZJ':       "Drell-Yan with j -> tau_h",
  'data_obs':  "observed",                      'W':        "W + jets",
  'XTT':       "VLQ",                           'VV':       "diboson",
  'XTT-MB170': "VLQ m_{B}=170",                 'QCD':      "QCD multijet",
  'XTT-MB300': "VLQ m_{B}=300",                 'JTF':      "j -> tau fakes",
  'XTT-MB450': "VLQ m_{B}=450",                 'ATT':      "bbA",
}


def makeSFrameSamples(samplesD,samplesB,samplesS,**kwargs):
    """
    Make Sample objects from a list of SFrame samples given
      subdir, name, title and cross section for simulations,
      subdir, name and title for data.
    The data should be a dictionary with channel as keys.
    """
    outdir  = kwargs.get('dir',      SAMPLE_DIR  )
    weight  = kwargs.get('weight',   ""          )
    kwargs.update({'SFrame': True, 'nanoAOD': False,    'dir': outdir,
                   'data': False,  'background': False, 'signal': False})
    
    # DATA
    for channel, sample in samplesD.items():
        subdir, name, title = sample[:3]
        sdict = dict(kwargs,**sample[3]) if len(sample)>3 else kwargs.copy()
        sdict['weight'] = ""
        sdict['data']   = True
        samplesD[channel] = Sample(name,title,SFrameOutputPath(sdict['dir'],subdir,name,**sdict),**sdict)
    
    # BACKGROUND
    for i, sample in enumerate(samplesB):
        subdir, name, title, sigma = sample[:4]
        sdict = dict(kwargs,**sample[4]) if len(sample)>4 else kwargs.copy()
        sdict['background'] = True
        samplesB[i] = Sample(name,title,sigma,SFrameOutputPath(sdict['dir'],subdir,name,**sdict),**sdict)
    
    # SIGNAL
    for i, sample in enumerate(samplesS):
        subdir, name, title, sigma = sample[:4]
        sdict = dict(kwargs,**sample[4]) if len(sample)>4 else kwargs.copy()
        sdict['signal'] = True
        samplesS[i] = Sample(name,title,sigma,SFrameOutputPath(sdict['dir'],subdir,name,**sdict),**sdict)
    
def makeNanoAODSamples(channel,samplesD,samplesB,samplesS,**kwargs):
    """
    Make Sample objects from a list of nanoAOD samples given
      channel, name, title and cross section for simulations,
      channel, name and title for data.
    The data should be a dictionary with channel as keys.
    """
    outdir  = kwargs.get('dir',      SAMPLE_DIR  )
    weight  = kwargs.get('weight',   ""          )
    kwargs.update({'SFrame': False, 'nanoAOD': True,     'dir': outdir,
                   'treeName': 'tree',
                   'data': False,   'background': False, 'signal': False})
    
    # DATA
    for channel, sample in samplesD.items():
        subdir, name, title = sample[:3]
        sdict = dict(kwargs,**sample[3]) if len(sample)>3 else kwargs.copy()
        sdict['weight'] = ""
        sdict['data']   = True
        samplesD[channel] = Sample(name,title,nanoAODOutputPath(sdict['dir'],subdir,name,channel,**sdict),**sdict)
    
    # BACKGROUND
    for i, sample in enumerate(samplesB):
        subdir, name, title, sigma = sample[:4]
        sdict = dict(kwargs,**sample[4]) if len(sample)>4 else kwargs.copy()
        sdict['background'] = True
        samplesB[i] = Sample(name,title,sigma,nanoAODOutputPath(sdict['dir'],subdir,name,channel,**sdict),**sdict)
    
    # SIGNAL
    for i, sample in enumerate(samplesS):
        subdir, name, title, sigma = sample[:4]
        sdict = dict(kwargs,**sample[4]) if len(sample)>4 else kwargs.copy()
        sdict['signal'] = True
        samplesS[i] = Sample(name,title,sigma,nanoAODOutputPath(sdict['dir'],subdir,name,channel,**sdict),**sdict)
    

def SFrameOutputPath(outdir,subdir,samplename,*args,**kwargs):
    """Return a path to a root file from SFrame."""
    verbosity   = getVerbosity(kwargs,verbosityPlotTools,verbositySampleTools)
    cycle       = kwargs.get('cycle',   'TauTauAnalysis' )
    tag         = kwargs.get('tag',      globalTag       )
    tag        += kwargs.get('extratag', ""              )
    if args and isinstance(args,str): tag = args[0]
    file        = "%s/%s/%s.%s%s.root" % (outdir,subdir,cycle,samplename,tag)
    LOG.verbose('file = "%s"'%(file), verbosity,level=3)
    return file
    

def nanoAODOutputPath(outdir,subdir,samplename,channel,*args,**kwargs):
    """Return a path to a root file from the nanoAOD analysis."""
    verbosity   = getVerbosity(kwargs,verbosityPlotTools,verbositySampleTools)
    tag         = kwargs.get('tag',      globalTag       )
    tag        += kwargs.get('extratag', ""              )
    if args and isinstance(args,str): tag = args[0]
    file        = "%s/%s/%s_%s%s.root" % (outdir,subdir,samplename,channel,tag)
    LOG.verbose('file = "%s"'%(file), verbosity,level=3)
    return file
    

def shiftSample(samples0,searchterms,file_app,title_app,**kwargs):
    """Shift sample filename and title. Find the sample via a simple search term."""
    weight      = kwargs.get('weight',      ""          )
    filter      = kwargs.get('filter',      False       )
    #samples     = getSample(samples0,searchterm)
    if not isList(searchterms): searchterms = [ searchterms ]
    
    samples     = [ ]
    for searchterm in searchterms:
      for sampleinfo in samples0:
        subdir, filename, title, sigma = sampleinfo[:4]
        sdict = sampleinfo[4] if len(sampleinfo)>4 else { }
        if searchterm in subdir or searchterm in filename or searchterm in title:
          samples.append((subdir, filename+file_app, title+title_app, sigma, sdict))
        elif not filter:
          samples.append(sampleinfo)
    print samples
    
    return samples
    


    ############
    # Cutflows #
    ############

def getEfficienciesFromHistogram(hist,cuts,**kwargs):
    """Get efficiencies for some histogram, as defined by a list of selections."""
    
    weight = kwargs.get('weight',   ""      )
    offset = kwargs.get('offset',   0       )
    iN     = kwargs.get('iN',       1       )
    efficiencies = EffTable([ ],[ ],[ ],[ ],[ ],[ ])
    
    N_tot0 = hist.GetBinContent(iN)
    N_tot  = N_tot0
    N      = N_tot0
    for i, cutname in enumerate(cuts,1):
        if i>1:      N = hist.GetBinContent(i)
        if N_tot0<1: N_tot0 = N
        if N and N_tot:
            efficiencies.append(( cutname, N, N/N_tot*100, N/N_tot0*100 ))
        else:
            efficiencies.append(( cutname, N, 0, 0 ))
            print ">>> Warning: GetBinContent(%i) = %s, GetBinContent(%i) = %s " % (i,N,i-1,N_tot)
        N_tot = N
        #efficiencies.add(cutname,cutname,N,N,)
    
    #for cutname, efficiency in efficiencies:
    #    print ">>> %s: %5.2f%%" % (cut,efficiency*100)
    
    return efficiencies
    
def getEfficienciesFromTree(tree,cuts,**kwargs):
    """Get efficiencies for some tree, as defined by a list of selections [(name,cut)]."""
    
    weight = kwargs.get('weight',"")
    
    efficiencies = [ ]
    if not cuts: return [ ]
    
    N_tot0 = kwargs.get('N',getSumWeights(tree,cuts[0][1],weight))
    N_tot  = N_tot0
    N      = N_tot0
    
    for i, (cutname,cut) in enumerate(cuts):
        print cut
        N = getSumWeights(tree,cut,weight)
        if N_tot0<1:  N_tot0 = N
        if N and N_tot:
            efficiencies.append(( cutname, N, N/N_tot*100, N/N_tot0*100 ))
        else: 
            efficiencies.append(( cutname, N, 0, 0 ))
            print ">>> Warning: GetEntries(cut) = %.1f, GetEntries(cut-1) = %.1f, cut=%s" % (N,N_tot,cut)
        N_tot = N
    
    return efficiencies
    
def getSumWeights(tree,cut0,weight):
    """Get sum of weights. In case a weight is given, the weighted number of events."""
    if not weight:
      return float(tree.GetEntries(cut))
    else:
      hist     = TH1F("Sumw","Sumw",2,0,2)
      cut      = "(%s)*%s"%(cut0,weight)
      out      = tree.Draw("%s >> %s"%(1,"Sumw"),cut,"gOff")
      integral = hist.GetBinContent(2)
      gDirectory.Delete(hist.GetName())
      return integral
    
def printComparingCutflow(efficiencies1,efficiencies2):
    print ">>> %13s:   %21s %8s   %15s   %16s   " % ("name","events".center(21,' '),"ratio".center(5,' '),"rel. eff.".center(15,' '),"abs. eff.".center(17,' '))
    for (name1,N1,releff1,abseff1), (name2,N2,releff2,abseff2) in zip(efficiencies1,efficiencies2):
       ratio = "-"
       if N1: ratio = N2/N1
       print (">>> %13s:   %9d - %9d %8.2f   %6.2f - %6.2f   %7.3f - %7.3f  " % (name1,N1,N2,ratio,releff1,releff2,abseff1,abseff2))
    
def getColor(name):
    """Get color for some sample name."""
    if isinstance(name,Sample):
      name = "signal "+name.title if name.isSignal else name.title
    for searchterm in sorted(colors_sample_dict,key=lambda x: len(x),reverse=True):
      if re.findall(searchterm.replace('*',".*"),name): # glob -> regex wildcard # re.IGNORECASE
        LOG.verbose('getColor - "%s" gets color %s from searchterm "%s"!'%(name,colors_sample_dict[searchterm],searchterm),verbositySampleTools,level=3)
        return colors_sample_dict[searchterm]
    LOG.warning('getColor - could not find color for "%s"!'%name)
    return 0
    
def checkMemory():
    print "gDirectory %s"%(gDirectory.GetName())
    print gDirectory.ls()
    


CutInfo = ntuple("CutInfo",['name','cut','N','N_unweighted','abseff','releff','kwargs'])
class Cutflow(object):
    """Sample to store relative and absolute efficiencies."""
    
    def __init__(self, name, **kwargs):
        self.name = name
        self.cuts = [ ]
        
    def add(self, *args, **kwargs):
        strings = [a for a in arg if isinstance(a,str)]
        numbers = [a for a in arg if isNumber(a)]
        if len(strings)==0:
          LOG.warning("Cutflow::add: Did not find name!")
          strings = [ "no name" ]
        if len(numbers)<3:
          LOG.warning("Cutflow::add: Not enough numbers!")
          while len(numbers)<=4: numbers.append(0)
        if len(numbers)==3:
          numbers.insert(1,numbers[0])
        name   = strings[0]
        cut    = strings[1] if len(strings)>1 else name
        N      = numbers[0]
        N_unw  = numbers[1]
        abseff = numbers[2]
        releff = numbers[3]
        self.cuts.append(CutInfo(name,cut,N,N_unweighted,abseff,releff))



    ##########
    # Sample #
    ##########

class Sample(object):
    """
    TODO:
    Sample class to
      - hold all relevant sample information: file, name, cross section, number of events,
        type, extra weight, extra scale, color, ...
      - calculate and set normalization (norm) based on integrated luminosity, cross section
        and number of events
      - make histogram with the Plot class
      - split histograms into subsamples (based on some (generator-level) selections
    """
    
    def __init__(self, name, title, *args, **kwargs):
        
        # UNWRAP optional arguments
        sigma    = -1.0
        filename = ""
        for arg in args:
          if sigma < 0 and not kwargs.get('sigma',False) and isNumber(arg):
            sigma = arg
          if not filename and not kwargs.get('filename',False) and isinstance(arg,str):
            filename = arg
        
        # INITIALIZE attributes
        self.name           = name
        self.title          = title
        self.tags           = [ ]
        self.filename       = kwargs.get('filename',        filename            )
        self.filenameshort  = '/'.join(self.filename.split('/')[-2:])
        self.file           = TFile(self.filename) if self.filename else None
        self._tree          = kwargs.get('tree',            None                )
        self._treename      = kwargs.get('treeName',        "tree_mutau"        )
        self.sigma          = kwargs.get('sigma',           sigma               )
        self.N              = kwargs.get('N',               -1                  ) # sum weights
        self.N_unweighted   = kwargs.get('N_unweighted',    -1                  ) # "raw" number of MC events
        self.N_exp          = kwargs.get('N_exp',           -1                  ) # events you expect to have to check fail rate
        self.binN_weighted  = kwargs.get('binN_weighted',   8                   ) # index of bin with total sum of weight
        self.norm           = kwargs.get('norm',            1.0                 ) # normalization L*sigma/N
        self.scale          = kwargs.get('scale',           1.0                 ) # renormalization scales
        self.upscale        = kwargs.get('upscale',         1.0                 ) # drawing up/down scaling
        self._scaleBU       = self.scale # back up scale to overwrite previous renormalizations
        self.weight         = kwargs.get('weight',          ""                  ) # weights
        self.extraweight    = kwargs.get('extraweight',     ""                  ) # extra weights
        self.cuts           = kwargs.get('cuts',            ""                  ) # extra cuts
        self.isData         = kwargs.get('data',            False               )
        self.isBackground   = kwargs.get('background',      False               )
        self.isSignal       = kwargs.get('signal',          False               )
        self.blind_dict     = kwargs.get('blind',           blind_dict          ) # var vs. (xmin,xmax)
        self.splitsamples   = [ ]
        self.color          = kwargs.get('color',           None                )
        self.linecolor      = kwargs.get('linecolor',       kBlack              )
        self.lumi           = kwargs.get('lumi',            luminosity          )
        self.isSFrame       = kwargs.get('SFrame',          True                )
        self.isNanoAOD      = kwargs.get('nanoAOD',         not self.isSFrame   )
        
        if self.color==None:
          self.color = getColor(self)
        
        # CHECK FILE
        if not isinstance(self,MergedSample) and (not self.file or not isinstance(self.file,TFile)): # self.filename
            LOG.fatal('SampleSet::SampleSet: Could not open or find file for "%s" sample: "%s"'%(self.name,self.filename))
        
        # SFRAME
        if self.isData:
          self.getNumberOfEvents('mutau',1,self.binN_weighted)
        elif self.sigma>=0 and not isinstance(self,MergedSample):
          self.getNumberOfEvents('mutau',1,self.binN_weighted)
          self.normalizeToLumiCrossSection(self.lumi)
        
        # CHECK NUMBER OF EVENTS
        if 0 < self.N < self.N_exp*0.97:
            LOG.warning('SampleSet::SampleSet: Sample "%s" has significantly less events (%d) than expected (%d).'%(self.name,self.N,self.N_exp))
        
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        """Returns string representation of Variable object."""
        #return '<%s.%s("%s","%s") at %s>'%(self.__class__.__module__,self.__class__.__name__,self.name,self.title,hex(id(self)))
        return '<%s("%s","%s") at %s>'%(self.__class__.__name__,self.name,self.title,hex(id(self)))
        
    def __add__(self, sample):
        """Add samples into MergedSamples."""
        if isinstance(sample,Sample):
          mergedsample = MergedSample(self,sample)
          return self
        return None
        
    def __mul__(self, scale):
        """Multiply selection with some weight (that can be string or Selection object)."""
        if isNumber(scale):
          self.setScale(scale)
          return self
        return None
        
    def row(self,**kwargs):
        """Returns string that can be used as a row in a samples summary table"""
        pre    = kwargs.get('pre', "")
        return ">>>  %s%-24s  %-40s  %12.2f  %10i  %11i  %10.3f  %s" %\
          (pre,self.title,self.name,self.sigma,self.N_unweighted,self.N,self.norm,self.extraweight) #+ ("  isData" if self.isData else "")
        
    def printRow(self):
        print self.row()
    
    def printSampleObjects(self,title=""):
        """Print all sample objects recursively"""
        print ">>> %s%r"%(title,self)
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.printSampleObjects(title+"  ")
        for sample in self.splitsamples:
          sample.printSampleObjects(title+"  ")
    
    #@property
    #def filename(self):
    #  return self._filename
    #
    #@filename.setter
    #def filename(self, value):
    #  self._filename = value
    #  if self.file:
    #    self.file.Close()
    #    self.file = TFile(self._filename)
    #  if isinstance(self,MergedSample):
    #    for sample in self.samples:
    #      sample.filename = value
    #  for sample in self.splitsamples:
    #      sample.filename = value
    
    @property
    def treename(self):
      return self._treename
    
    @treename.setter
    def treename(self, value):
      self._treename = value
      if isinstance(self,MergedSample):
        for sample in self.samples:
          sample.treename = value
      for sample in self.splitsamples:
          sample.treename = value
    
    @property
    def tree(self):
      if not self.file:
        LOG.warning('Sample::tree - file "%s" not opened! Reopening...'%(self.filename))
        self.file = TFile(self.filename)
      if self._tree:
        if isinstance(self._tree,TTree):
          if self._tree.GetName()==self._treename:
            return self._tree
          else:
            return self.file.Get(self._treename)
        else:
          LOG.warning("Sample::tree - no valid TTree instance!")
      else:
        #self._tree = self.file.Get(self._treename)
        return self.file.Get(self._treename)
    
    @tree.setter
    def tree(self, value):
      self._tree = value
    
    def getTree(self,treename):
        """Get tree with treename."""
        if treename!=self.treename:
          LOG.warning('Sample::getTree: treename = "%s" != "%s" = self.treename'%(treename,self.treename))
          tree = self.file.Get(treename)
        else:
          tree = self.tree
        if not tree or not isinstance(tree,TTree):
          if not self.file:
            LOG.error('Sample::getTree: Could not find tree "%s" for "%s"! File is closed: %s'%(treename,self.name,self.filename))
          else:
            LOG.error('Sample::getTree: Could not find tree "%s" for "%s"! Check %s'%(treename,self.name,self.filename))
          exit(1)
        return tree
    
    @property
    def labels(self):
      return [ self.name, self.title, self.filenameshort ]
    
    @labels.setter
    def labels(self, value):
      LOG.warning('Sample::labels - No setter for "labels" attribute!')
    
    @property
    def scaleBU(self):
      return self._scaleBU
    
    @scaleBU.setter
    def scaleBU(self, value):
      LOG.warning("Sample - Not allowed to set scaleBU (%.4g)!"%self._scaleBU)
      
    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for key, val in self.__dict__.items():
            setattr(result, key, deepcopy(val, memo))
        return result
    
    def clone(self,*args,**kwargs):
        """Shallow copy."""
        samename                = kwargs.get('samename', False )
        deep                    = kwargs.get('deep',     False )
        close                   = kwargs.get('close',    False )
        name                    = args[0] if len(args)>0 else self.name  + ("" if samename else  "_clone" )
        title                   = args[1] if len(args)>1 else self.title + ("" if samename else " (clone)")
        filename                = args[2] if len(args)>2 else self.filename
        splitsamples            = [s.clone(samename=samename,deep=deep) for s in self.splitsamples] if deep else self.splitsamples[:]
        kwargs['signal']        = self.isSignal
        newsample               = type(self)(name,title,filename,**kwargs)
        newdict                 = self.__dict__.copy()
        newdict['name']         = name
        newdict['title']        = title
        newdict['splitsamples'] = splitsamples
        if deep and self.file:
          file = TFile(self.file.GetName())
          newdict['file'] = file
        newsample.__dict__.update(newdict)
        #LOG.verbose('Sample::clone: "%s", weight = "%s"'%(newsample.name,newsample.weight),1)
        if close: newsample.close()
        return newsample
        
    def setColor(self,*args):
        """Set color"""
        self.color = args[0] if args else getColor(self)
        
    #def setFileName(self,filename):
    #    """Set filename."""
    #    self.filename = filename
        
    def appendFileName(self,file_app,**kwargs):
        """Append filename (in front of globalTag)."""
        title_app     = kwargs.get('title_app',  "" )
        title_tag     = kwargs.get('title_tag',  "" )
        title_veto    = kwargs.get('title_veto', "" )
        oldfilename   = self.filename
        newfilename   = oldfilename if file_app in oldfilename else oldfilename.replace(globalTag,file_app+globalTag)
        LOG.verbose('replacing "%s" with "%s"'%(oldfilename,self.filename),verbositySampleTools,level=3)
        self.filename = newfilename
        if file_app  not in self.name:
          self.name  += file_app
        if title_app not in self.title and not (title_veto and re.search(title_veto,self.title)):
          self.title += title_app
        if self.file:
          #reopenTree = True if self._tree else False
          self.file.Close()
          self.file = TFile(self.filename)
          #if reopenTree: self.tree = self.file.Get(self.treename)
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.appendFileName(file_app,**kwargs)
        for sample in self.splitsamples:
            sample.appendFileName(file_app,**kwargs)
        
    def setTreeName(self,treename):
        """Set treename."""
        self.treename = treename
        
    def setScale(self,scale):
        """Set treename, for split samples as well."""
        self.scale = scale
        for sample in self.splitsamples:
            sample.scale = scale
        
    def resetScale(self,scale=1.0,**kwargs):
        """Reset scale to BU scale."""
        LOG.verbose("resetScale: before scale = %s"%(self.scale),verbositySampleTools,2)
        self.scale = self.scaleBU*scale # only scale first layer
        LOG.verbose("            after  scale = %s"%(self.scale),verbositySampleTools,2)
        for sample in self.splitsamples:
            sample.resetScale(**kwargs)
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.resetScale(**kwargs)
        
    def reload(self,**kwargs):
        """Close and reopen file. Use it to free up some memory."""
        verbosity = kwargs.get('verbosity', 0)
        if self.file:
          if verbosity>3:
            LOG.verbose('Sample::reload: closing and deleting %s with content:'%(self.file.GetName()),verbosity,2)
            self.file.ls()
          self.file.Close()
          del self.file
          self.file = None
        if not isinstance(self,MergedSample):
          if self.filename:
            self.file = TFile(self.filename)
        else:
          for sample in self.samples:
            sample.reload(**kwargs)
        for sample in self.splitsamples:
            sample.reload(**kwargs)
    
    def open(self,**kwargs):
        """Open file. Use it to free up some memory."""
        verbosity = kwargs.get('verbosity', 0)
        self.reload(**kwargs)
        
    def close(self,**kwargs):
        """Close file. Use it to free up some memory."""
        verbosity = kwargs.get('verbosity', 0 )
        if self.file:
            if verbosity>1:
              LOG.verbose('Sample::close: closing and deleting %s with content:'%(self.file.GetName()),verbosity,3)
              self.file.ls()
            self.file.Close()
            del self.file
            self.file = None
        for sample in self.splitsamples:
            sample.close(**kwargs)
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.close(**kwargs)
        
    def addCuts(self, cuts):
        """Combine cuts."""
        #LOG.verbose('Sample::addCuts: combine cuts "%s" with "%s"'%(self.cuts,cuts),1)
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.addCuts(cuts)
        else:
          self.cuts = combineCuts(self.cuts, cuts)
        for sample in self.splitsamples:
            sample.addCuts(cuts)
        
    def addWeight(self, weight):
        """Add weight."""
        #LOG.verbose('Sample::addWeight: combine weights "%s" with "%s"'%(self.weight,weight),1)
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.addWeight(weight)
        else:
          LOG.verbose('addWeight: before: %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
          self.weight = combineWeights(self.weight, weight)
          LOG.verbose('           after:  %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
        for sample in self.splitsamples:
            sample.addWeight(weight)
        
    def addExtraWeight(self, weight):
        """Add extra weight."""
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.addExtraWeight(weight)
        else:
          LOG.verbose('addExtraWeight: before: %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
          self.extraweight = combineWeights(self.extraweight, weight)
          LOG.verbose('                after:  %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
        for sample in self.splitsamples:
            sample.addExtraWeight(weight)
        
    def setWeight(self, weight, extraweight=False):
        """Set weight, overwriting all previous ones."""
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.setWeight(weight)
        else:
          LOG.verbose('setWeight: before: %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
          self.weight = weight
          LOG.verbose('           after:  %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
        for sample in self.splitsamples:
            sample.setWeight(weight)
        
    def setExtraWeight(self, weight):
        """Set extra weight, overwriting all previous ones."""
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.setExtraWeight(weight)
        else:
          LOG.verbose('setExtraWeight: before: %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
          self.extraweight = weight
          LOG.verbose('                after:  %s, self.weight = "%s", self.extraweight = "%s"'%(self,self.weight,self.extraweight),verbositySampleTools,2)
        for sample in self.splitsamples:
            sample.setExtraWeight(weight)
        
    def replaceWeight(self, oldweight, newweight):
        """Replace weight."""
        if isinstance(self,MergedSample):
          for sample in self.samples:
            sample.replaceWeight(oldweight,newweight)
        else:
          if oldweight in self.weight:
            LOG.verbose('>>> replaceWeight: before "%s"'%(self.weight),verbositySampleTools)
            self.weight = self.weight.replace(oldweight,newweight)
            LOG.verbose('>>>                after  "%s"'%(self.weight),verbositySampleTools)
          if oldweight in self.extraweight:
            LOG.verbose('>>> replaceWeight: before "%s"'%(self.extraweight),verbositySampleTools)
            self.extraweight = self.extraweight.replace(oldweight,newweight)
            LOG.verbose('>>>                after  "%s"'%(self.extraweight),verbositySampleTools)
        
    def normalizeToLumiCrossSection(self,lumi,**kwargs):
        """Calculate and set the normalization for simulation as L*sigma/N"""
        norm     = 1.
        sigma    = kwargs.get('sigma',  self.sigma  )
        N_events = kwargs.get('N',      self.N      )
        if self.sigma<0:
          LOG.warning('Sample::normalizeToLumiCrossSection: Cannot normalize "%s": sigma = %s < 0'%(self.name,sigma))
          return -1
        if self.isData:
          LOG.warning('Sample::normalizeToLumiCrossSection: Ignoring data sample "%s"'%(self.name))
          return norm
        if N_events:
          norm = lumi*sigma*1000/N_events
        else:
          LOG.warning('Sample::normalizeToLumiCrossSection: Cannot normalize "%s" sample: N_events = %s!'%(self.name,N_events))
        if norm <= 0:
          LOG.warning('Sample::normalizeToLumiCrossSection: Calculated normalization for "%s" sample is %.5g <= 0 (L=%.5g,sigma=%.5g,N=%.5g)!'%(self.name,norm,lumi,sigma,N_events))
        
        self.norm = norm
        return norm
        
    def getNumberOfEvents(self,channel,binN,binN_weighted):
        """Get number of events for a SFrame sample from the cutflow histogram."""
        if self.isSFrame:
          cutflowHist         = self.file.Get("histogram_%s/cutflow_%s"%(channel,channel))
          if not cutflowHist:
              cutflowHist     = self.file.Get("histogram_emu/cutflow_emu")
          if not cutflowHist:
              cutflowHist     = self.file.Get("histogram_mumu/cutflow_mumu")
          if not cutflowHist:
              cutflowHist     = self.file.Get("histogram_ditau/cutflow_ditau")
          if not cutflowHist:
              LOG.error("Could not find cutflow histogram!")
          self.N              = cutflowHist.GetBinContent(binN_weighted)
          self.N_unweighted   = cutflowHist.GetBinContent(binN)
        elif self.isNanoAOD:
          cutflowHist         = self.file.Get("h_cutflow")
          self.N              = cutflowHist.GetBinContent(binN_weighted)
          self.N_unweighted   = cutflowHist.GetBinContent(binN)
        else:
          LOG.warning("getNumberOfEvents: Cannot set number of event, because it is not clear what histogram to use (SFrame or nanoAOD?)")
        
    
    def split(self,splitlist,**kwargs):
        """Split sample for some dictionairy of cuts."""
        
        verbosity      = getVerbosity(kwargs,verbositySampleTools)
        splitsamples   = [ ]
        
        for i, info in enumerate(reversed(splitlist)): #split_dict.items()
            name         = info[0] if len(info)>2 else "%s_split%d"%(self.name,i)
            title        = info[1] if len(info)>2 else info[0] if len(info)>1 else name
            cut          = info[2] if len(info)>2 else info[1] if len(info)>1 else ""
            sample       = self.clone(name,title)
            sample.cuts  = combineCuts(self.cuts,cut)
            sample.color = getColor(sample.title)
            splitsamples.append(sample)
        
        self.splitsamples = splitsamples # save list of split samples
        #return splitsamples
        
    
    def hist(self, *args, **kwargs):
        """Make a histogram from a tree."""
        
        verbosity      = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts = unwrapVariableSelection(*args)
        scale          = kwargs.get('scale',             1.0                         ) * self.scale * self.norm
        treename       = kwargs.get('treename',          self.treename               )
        name           = kwargs.get('name',              makeHistName(self.name,var) )
        name          += kwargs.get('append',            ""                          )
        title          = kwargs.get('title',             self.title                  )
        shift          = kwargs.get('shift',             0                           )
        smear          = kwargs.get('smear',             0                           )
        scaleup        = kwargs.get('scaleup',           0.0                         )
        includeUncs    = kwargs.get('includeUnc',        ""                          )
        blind          = kwargs.get('blind',             False                       )
        noJTF          = kwargs.get('noJTF',             False                       )
        color0         = kwargs.get('color',             self.color                  )
        linecolor      = kwargs.get('linecolor',         self.linecolor              )
        divideBinSize  = kwargs.get('divideByBinSize',   False                       )
        extracuts      = kwargs.get('cuts',              ""                          )
        weight         = kwargs.get('weight',            ""                          )
        replaceweight  = kwargs.get('replaceweight',     None                        )
        
        drawoption    = "E0" if self.isData else "HIST"
        drawoption    = "gOff"+kwargs.get('option',   drawoption                     )
        
        # SIGNAL
        if scaleup and self.upscale!=1.:
            #title += " (#times%d)" % (self.upscale)
            upscale_round = self.upscale
            if isNumber(scaleup):
              upscale_round *= scaleup
            upscale_round = roundToSignificantDigit(upscale_round,multiplier=5)
            title += ", %g pb"%(upscale_round)
            scale *= upscale_round 
        
        # BLIND
        blindcuts = ""
        if blind:
          if isinstance(blind,tuple):
            a, b    = blind
          elif var in self.blind_dict:
            a, b    = self.blind_dict[var]
          blindcuts = makeBlindCuts(var,a,b,nbins,xmin,xmax)
        
        # WEIGHTS
        weight   = combineWeights(self.weight, self.extraweight, weight)
        if replaceweight:
          for pair in replaceweight:
            if pair[0] in weight:
              print '>>> replacing weight: before "%s"'%weight
              weight = weight.replace(pair[0],pair[1])
              print '>>>                   after  "%s"'%weight
        
        # CUTS
        cuts     = combineCuts(cuts, extracuts, kwargs.get('extracuts',""), self.cuts, blindcuts, weight=weight)
        if noJTF:
          cuts   = vetoJetTauFakes(cuts)
        if self.isData and ('Up' in var or 'Down' in var or 'Up' in cuts or 'Down' in cuts):
          var    = undoShift(var)
          cuts   = undoShift(cuts)
          weight = undoShift(weight)
        
        # TREE
        tree = self.getTree(treename)
        
        # ARGS
        hargs  = (nbins, array('d',xbins)) if xbins else (nbins, xmin, xmax)
        
        # HIST
        hist = TH1D(name, title, *hargs)
        if self.isData: hist.SetBinErrorOption(TH1D.kPoisson)
        else:           hist.Sumw2()
        
        # DRAW
        out = tree.Draw("%s >> %s" % (var,name), cuts, drawoption)
        if out<0: LOG.error('Sample::hist - Drawing histogram for "%s" sample failed!'%(title))
        hist.SetDirectory(0)
        
        # SCALE
        if scale!=1.0:  hist.Scale(scale)
        if scale==0.0:  LOG.warning("Scale of %s is 0!"%self.name)
        if verbosity>2: printBinError(hist)
        
        # STYLE
        hist.SetLineColor(linecolor)
        hist.SetFillColor(kWhite if self.isData or self.isSignal else color0)
        hist.SetMarkerColor(color0)
        
        # DIVIDE BY BIN SIZE
        if divideBinSize: divideByBinSize(hist)
        
        # INCLUDE SYSTEMATIC (JER, JEC, ...)
        if includeUncs and not self.isSignal:
          ensureList(includeUncs)
          for shift in includeUncs:
            varShift  = shift(var,  includeUnc)
            cutsShift = shift(cuts, includeUnc)
            histShift = self.hist(varShift, nbins, xmin, xmax, cutsShift, **kwargs)
            addUncToHist(hist,histShift)
        
        # PRINT
        if verbosity>1:
            # TODO: make simple table ?
            print ">>>\n>>> Sample - %s" % (color(name,color="grey"))
            #print ">>>\n>>> Sample - %s, %s: %s (%s)" % (color(name,color="grey"),var,self.filenameshort,self.treename)
            #print ">>>    norm=%.4f, scale=%.4f, total %.4f" % (self.norm,self.scale,scale)
            #print ">>>    weight:  %s" % (("\n>>>%s*("%(' '*18)).join(weight.rsplit('*(',max(0,weight.count("*(")-1))))
            print ">>>    entries: %d (%.2f integral)" % (hist.GetEntries(),hist.Integral())
            print ">>>    %s" % (cuts.replace("*(","\n>>>%s*("%(' '*18)))
        return hist
        
    
    def hist2D(self, *args, **kwargs):
        """Make a 2D histogram from a tree."""
        
        xvar, nxbins, xmin, xmax, xbins,\
        yvar, nybins, ymin, ymax, ybins, cuts = unwrapVariableSelection2D(*args)
        verbosity     = getVerbosity(kwargs,verbositySampleTools)
        name          = makeHistName(self.name,"%s_vs_%s"%(xvar,yvar))
        scale         = kwargs.get('scale',           1.0                         ) * self.scale * self.norm
        treename      = kwargs.get('treename',        self.treename               )
        name          = kwargs.get('name',            name                        )
        name         += kwargs.get('append',          ""                          )
        title         = kwargs.get('title',           self.title                  )
        extracuts     = kwargs.get('cuts',            ""                          )
        noJTF         = kwargs.get('noJTF',           False                       )
        color0        = kwargs.get('color',           self.color                  )
        linecolor     = kwargs.get('linecolor',       self.linecolor              )
        drawoption    = "COLZ"
        drawoption    = "gOff"+kwargs.get('option',   drawoption                  )
        
        # CUTS & WEIGHTS
        weight   = combineWeights(self.weight, self.extraweight, kwargs.get('weight', ""))
        cuts     = combineCuts(cuts, extracuts, kwargs.get('extracuts', ""), self.cuts, weight=weight)
        if noJTF:
          cuts   = vetoJetTauFakes(cuts)
        
        # TREE
        tree = self.getTree(treename)
        
        # ARGS
        hargs  = (nxbins, array('d',xbins)) if xbins else (nxbins, xmin, xmax)
        hargs += (nybins, array('d',ybins)) if ybins else (nybins, ymin, ymax)
        
        # HIST
        hist = TH2F(name, title, *hargs)
        if self.isData: hist.SetBinErrorOption(TH2F.kPoisson)
        else:           hist.Sumw2()
        hist.SetOption("COLZ")
        
        # DRAW
        out = tree.Draw("%s:%s >> %s"%(yvar,xvar,name), cuts, drawoption)
        if out<0: LOG.error('Sample::hist - Drawing histogram for "%s" sample failed!'%(title))
        hist.SetDirectory(0)
        
        # SCALE
        if scale!=1.0:  hist.Scale(scale)
        if scale==0.0:  LOG.warning("Scale of %s is 0!"%self.name)
        if verbosity>2: printBinError(hist)
        
        # STYLE
        hist.SetLineColor(linecolor)
        hist.SetFillColor(kWhite if self.isData or self.isSignal else color0)
        hist.SetMarkerColor(color0)
        
        # PRINT
        if verbosity>1:
            print ">>>\n>>> Sample - %s" % (color(name,color="grey"))
            print ">>>    entries: %d (%.2f integral)" % (hist.GetEntries(),hist.Integral())
            print ">>>    %s" % (cuts.replace("*(","\n>>>%s*("%(' '*18)))
        return hist
    
    
    def getEfficiency(self):
        """Calculate efficiency for some selections."""
        # TODO:
        #  - from cutflow hist
        #  - from selections in tree 
    
    def isPartOf(self, *searchterms, **kwargs):
        """Check if all labels are in the sample's name, title or tags."""
        searchterms = [l for l in searchterms if l!='']
        if not searchterms: return False
        found       = True
        regex       = kwargs.get('regex',       False   )
        exlcusive   = kwargs.get('exclusive',   True    )
        start       = kwargs.get('start',       False   )
        labels      = [self.name,self.title]+self.tags
        for searchterm in searchterms:
          if not regex:
              searchterm = re.sub(r"(?<!\\)\+",r"\+",searchterm) # replace + with \+
              searchterm = re.sub(r"([^\.])\*",r"\1.*",searchterm) # replace * with .*
          if start:
            searchterm = '^'+searchterm
          if exlcusive:
              for samplelabel in labels:
                  matches = re.findall(searchterm,samplelabel)
                  if matches: break
              else: return False # none of the labels contain the searchterm
          else: # inclusive
              for samplelabel in labels:
                  matches = re.findall(searchterm,samplelabel)
                  if matches: return True # one of the searchterm has been found
        return exlcusive
    


class SampleData(object):
    def __init__(self, name, title, *args, **kwargs):
        kwargs['isData'] = True
        Sample.__init__(self,name,title,*args,**kwargs)
    




    ################
    # MergedSample #
    ################

class MergedSample(Sample):
    """Class to combine a list of Sample objects to make one histogram with the Plot class."""

    def __init__(self, *args, **kwargs):
        name, title, samples = unwrapMergedSamplesArgs(*args,**kwargs)
        self.samples = list(samples)
        Sample.__init__(self,name,title,**kwargs)
        if self.samples: self.initFromSample(samples[0])
        
    def initFromSample(self, sample, **kwargs):
        """Set some relevant attributes (inherited from the Sample class) with a given sample."""
        self.filename     = sample.filename
        self._treename    = sample.treename
        self.isSignal     = sample.isSignal
        self.isBackground = sample.isBackground
        self.isData       = sample.isData
        self.linecolor    = sample.linecolor
    
    def __iter__(self):
      """Start iteration over samples."""
      for sample in self.samples:
        yield sample
    
    def __add__(self,sample):
      """Start iteration over samples."""
      self.add(sample)
    
    def add(self, sample, **kwargs):
        """Add Sample object to list of samples."""
        if not self.samples: self.initFromSample(sample)
        self.samples.append(sample)
    
    def row(self,**kwargs):
        """Returns string that can be used as a row in a samples summary table."""
        pre    = kwargs.get('pre', "")
        string = ">>>  %s%-24s  %-40s  %12.2f  %10i  %11i  %10.3f  %s" %\
          (pre,self.title,self.name,self.sigma,self.N_unweighted,self.N,self.norm,self.extraweight)
        for sample in self.samples:
          string += "\n" + sample.row(pre=pre+"  ")
        return string
    
    def clone(self,*args,**kwargs):
        """Shallow copy."""
        samename           = kwargs.get('samename', False )
        deep               = kwargs.get('deep',     False )
        close              = kwargs.get('close',    False )
        #samples            = kwargs.get('samples',  False )
        strings            = [ a for a in args if isinstance(a,str) ]
        name               = args[0] if len(args)>0 else self.name + ("" if samename else  "_clone" )
        title              = args[1] if len(args)>1 else self.title+ ("" if samename else " (clone)")
        samples            = [s.clone(samename=samename,deep=deep) for s in self.samples] if deep else self.samples[:]
        splitsamples       = [ ]
        for oldsplitsample in self.splitsamples:
          if deep:
            newsplitsample = oldsplitsample.clone(samename=samename,deep=deep)
            if isinstance(newsplitsample,MergedSample):
              # splitsamples.samples should have same objects as self.samples !!!
              for subsample in oldsplitsample.samples:
                if subsample in self.samples:
                  newsplitsample.samples[oldsplitsample.samples.index(subsample)] = samples[self.samples.index(subsample)]
            splitsamples.append(newsplitsample)
          else:
            splitsamples.append(oldsplitsample)
        newdict            = self.__dict__.copy()
        newdict['name']    = name
        newdict['title']   = title
        newdict['samples'] = samples
        newdict['splitsamples'] = splitsamples
        newsample          = type(self)(name,title,*samples,**kwargs)
        newsample.__dict__.update(newdict)
        if close: newsample.close()
        return newsample
    
    def hist(self, *args, **kwargs):
        """Create histgram for multiple samples. (Overrides Sample::hist2D.)"""
        
        verbosity        = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts = unwrapVariableSelection(*args)
        name             = kwargs.get('name',               makeHistName(self.name+"_merged", var))
        name            += kwargs.get('append',             ""                      )
        title            = kwargs.get('title',              self.title              )
        divideBinSize    = kwargs.get('divideByBinSize',    False                   )
        kwargs['cuts']   = combineCuts(kwargs.get('cuts'),  self.cuts               )
        kwargs['weight'] = combineWeights(kwargs.get('weight', ""), self.weight     ) # pass weight down
        kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
        kwargs['divideByBinSize'] = False
        
        if verbosity>1:
          print ">>>\n>>> Samples - %s, %s: %s"%(color(name,color="grey"), var, self.filenameshort)
          #print ">>>    norm=%.4f, scale=%.4f, total %.4f" % (self.norm,kwargs['scale'],self.scale)
        
        hargs = (nbins, array('d',xbins)) if xbins else (nbins, xmin, xmax)
        hist  = TH1D(name, title, *hargs)
        hist.SetDirectory(0)
        
        if self.isData: hist.SetBinErrorOption(TH1D.kPoisson)
        else:           hist.Sumw2()
        for sample in self.samples:
            if 'name' in kwargs: # prevent memory leaks
              kwargs['name']  = makeHistName(sample.name,name.replace(self.name+'_',''))    
            hist_new = sample.hist(*args, **kwargs)
            hist.Add( hist_new )
            #LOG.verbose("    sample %s added with %.1f events (%d entries)" % (sample.name,hist_new.Integral(),hist_new.GetEntries()),verbosity,level=2)
        
        # COLOR
        hist.SetLineColor(self.linecolor)
        hist.SetFillColor(self.color)
        hist.SetMarkerColor(self.color)
        
        # DIVIDE BY BIN SIZE
        if divideBinSize: divideByBinSize(hist)
        
        if verbosity>2: printBinError(hist)
        return hist
    
    def hist2D(self, *args, **kwargs):
        """Create 2D histgram for multiple samples. (Overrides Sample::hist2D.)"""
        
        verbosity        = getVerbosity(kwargs,verbositySampleTools)
        xvar, nxbins, xmin, xmax, xbins, yvar, nybins, ymin, ymax, ybins, cuts = unwrapVariableSelection2D(*args)
        name             = makeHistName(self.name+"_merged","%s_vs_%s"%(xvar,yvar))
        name             = kwargs.get('name',               name                    )
        name            += kwargs.get('append',             ""                      )
        title            = kwargs.get('title',              self.title              )
        kwargs['cuts']   = combineCuts(kwargs.get('cuts'),  self.cuts               )
        kwargs['weight'] = combineWeights(kwargs.get('weight', ""), self.weight     )# pass scale down
        kwargs['scale']  = kwargs.get('scale', 1.0) * self.scale * self.norm # pass scale down
        
        if verbosity>1:
          print ">>>\n>>> Samples - %s, %s vs. %s: %s" % (color(name,color="grey"), yvar, xvar, self.filenameshort)
          #print ">>>    norm=%.4f, scale=%.4f, total %.4f" % (self.norm,kwargs['scale'],self.scale)
        
        hargs  = (nxbins, array('d',xbins)) if xbins else (nxbins, xmin, xmax)
        hargs += (nybins, array('d',ybins)) if ybins else (nybins, ymin, ymax)
        
        hist = TH2F(name, title, *hargs)
        hist.SetDirectory(0)
        hist.Sumw2()
        hist.SetOption("COLZ")
        for sample in self.samples:
            if 'name' in kwargs: # prevent memory leaks
              kwargs['name']  = makeHistName(sample.name,name.replace(self.name+'_',''))    
            hist_new = sample.hist2D(*args, **kwargs)
            hist.Add( hist_new )
            #LOG.verbose("    sample %s added with %.1f events (%d entries)" % (sample.name,hist_new.Integral(),hist_new.GetEntries()),verbosity,level=2)
        
        # COLOR
        hist.SetLineColor(self.linecolor)
        hist.SetFillColor(self.color)
        hist.SetMarkerColor(self.color)
        
        return hist
        
                
def unwrapMergedSamplesArgs(*args,**kwargs):
    """Help function to unwrap arguments for MergedSamples."""
    
    strings = [ ]
    samples = [ ]
    args    = list(args)
    for arg in args[:]:
      if isinstance(arg,str):
        strings.append(arg)
        args.remove(arg)
      elif isinstance(arg,Sample):
        samples.append(arg)
        args.remove(arg)
      elif isList(arg):
        if arg and isinstance(arg[0],Sample):
          samples.append(arg[0])
          args.remove(arg[0])
    
    if len(strings)==1:
      name, title = strings[0], strings[0]
    elif len(strings)>1:
      name, title = strings[:3]
    elif len(samples)==0:
      name, title = "noname", "no title"
    else:
      name, title = '-'.join([s.name for n in samples]), ', '.join([s.title for n in samples])
    return name, title, samples




    #############
    # SampleSet #
    #############

class SampleSet(object):
    """
    TODO:
    Sample set class to hold set of samples and give easy functionality to:
       - find sample by name/pattern (wildcard or regex?)
       - find samples by type: signal, background, simlation, data samples, ...
       - merge, stitch and split sample by name/pattern,
       - draw all histograms for a given variable and set of selections,
       - allow switching on/off the splitting of samples (e.g. into final state) when draw,
       - allow fixed order,
       - renormalize in control regions: WJ, TT, ... (instead of in Plot)
       - measure OS/SS ratio, ... (instead of in Plot)
    """
    
    def __init__(self, samplesD, samplesB, samplesS, **kwargs):
        
        self.samplesB           = list(samplesB)
        self.samplesS           = list(samplesS)
        self._samplesD          = samplesD # may be a dictionary with channel as keys
        self.name               = kwargs.get('name',          ""          )
        self.label              = kwargs.get('label',         ""          )
        self.channel            = kwargs.get('channel',       "mutau"     )
        self.verbosity          = kwargs.get('verbosity',     0           )
        self.loadingbar         = kwargs.get('loadingbar',    True        ) and self.verbosity<2
        self.ignore             = kwargs.get('ignore',        [ ]         )
        self.sharedsamples      = kwargs.get('shared',        [ ]         )
        self.shiftQCD           = kwargs.get('shiftQCD',      0           )
        self.isNanoAOD          = kwargs.get('nanoAOD',       False       )
        #self.weight             = kwargs.get('weight',        ""          )
        self.closed             = False
        
        self.TTscale            = { }
        self.nPlotsMade         = 0
        self.color_dict         = { }
        self.linecolor_dict     = { }
        
    def __str__(self):
      """Returns string representation of Sample object."""
      return str([s.name for s in self.samplesB+self.samplesS]+[s.name for s in self.samplesD])
    
    def printSampleObjects(self,title=""):
      for sample in self.samples:
        sample.printSampleObjects(title="")
    
    def printTable(self,title=""):
      """Print table of all samples."""
      print ">>>\n>>> %s samples with integrated luminosity L = %s / fb at sqrt(s) = 13 TeV"%(title,luminosity)
      print ">>>  %-24s  %-40s  %12s  %10s  %11s  %10s  %s" %\
            ("sample title","name","sigma [pb]","events","sum weights","norm.","extra weight")
      for sample in self.samples:
        sample.printRow()
      print ">>> "
    
    @property
    def samples(self):
      """Getter for "samples" attribute of SampleSet."""
      return self.samplesB+self.samplesS+self.samplesD
    @samples.setter
    def samples(self, value):
      """Setter for "samples" attribute."""
      # samplesB, samplesS, samplesD = [ ], [ ], [ ]
      # for sample in value:
      #   if   sample.isData:       samplesD.append(sample)
      #   elif sample.isBackground: samplesB.append(sample)
      #   elif sample.isSignal:     samplesS.append(sample)
      #   else: LOG.warning("Sample.samples - Sample \"%s\" has no background or signal flag!"%sample.title)
      # self.samplesB, self.samplesS, self.samplesD = samplesB, samplesS, samplesD
      LOG.warning("Sample.samplesD - No setter for \"samples\" attribute available!")
    
    @property
    def samplesD(self):
      """Getter for "samplesD". If dataset depends on channel, return the data sample
      corresponding to the current channel."""
      if not self._samplesD:
        return [ ]
      if isinstance(self._samplesD,dict):
        if self.channel in self._samplesD:
          return [self._samplesD[self.channel]]
        else:
          LOG.warning("Sample::samplesD - Channel \"%s\" not in _samplesD: %s"%(self.channel,self._samplesD))
      return self._samplesD
    
    @samplesD.setter
    def samplesD(self, value):
      """Setter for "samplesD". If dataset depends on channel, set the given data sample
      to the current channel."""
      if isinstance(value,dict):
        self._samplesD = value
      elif   isinstance(self._samplesD,dict): #and len(value)==1:
        self._samplesD[self.channel] = value #[0]
      elif isList(self._samplesD) and isList(value):
        self._samplesD = value
      LOG.warning("Sample.samplesD - Check setter for \"samplesD\" attribute!")
    
    @property
    def samplesMC(self):
      return self.samplesB + self.samplesS
    @samplesMC.setter
    def samplesMC(self, value):
      samplesB, samplesS = [ ], [ ]
      for sample in value:
        if sample.isBackground: samplesB.append(sample)
        elif sample.isSignal:   samplesS.append(sample)
        else: LOG.warning("Sample::samplesMC - Sample \"%s\" has no background or signal flag!"%sample.title)
      self.samplesB, self.samplesS = samplesB, samplesS
    
    def __iter__(self):
      """Start iteration over samples."""
      for sample in self.samples:
        yield sample
    
    def setTreeName(self,treename):
        """Set tree name for each sample to draw histograms with."""
        for sample in self.samples:
          sample.setTreeName(treename)
          
    def setChannel(self,channel,treename=""):
        """Set channel."""
        self.channel = channel
        if treename:
          self.setTreeName(treename)
        if not self.closed:
          self.refreshMemory(now=True)
    
    def setColors(self):
        """TODO: Check and compare all sample's colors and set to another one if needed."""
        
        verbosity   = getVerbosity(kwargs,verbositySampleTools)
        usedColors  = [ ]
        
        # CHECK SPLIT
        for sample in self.samples:
          if sample.color is kBlack:
              LOG.warning("SamplesSet::setColors - %s"%sample.name)
          if sample.color in usedColor:
              # TODO: check other color
              sample.setColor()
              LOG.warning("SamplesSet::setColors - Color used twice!")
          else:
              usedColors.append(sample.color)
    
    def open(self,**kwargs):
        """Help function to close all files in samples list."""
        for sample in self.samples:
          sample.open(**kwargs)
        self.closed = False
    
    def close(self,**kwargs):
        """Help function to close all files in samples list."""
        shared = kwargs.get('shared', False)
        for sample in self.samples:
          if shared and sample in self.sharedsamples: continue
          sample.close(**kwargs)
        self.closed = True
          
    def clone(self,name="",**kwargs):
        """Shift samples in samples set by creating new samples with new filename/titlename."""
        filter          = kwargs.get('filter',      False       )
        share           = kwargs.get('share',       False       ) # share other samples (as opposed to cloning them)
        app             = kwargs.get('app',         "clone"     )
        close           = kwargs.get('close',       False       )
        deep            = kwargs.get('deep',        True        )
        
        filterterms     = filter if isList(filter) else ensureList(filter) if isinstance(filter,str) else [ ]
        shareterms      = share  if isList(share)  else ensureList(share)  if isinstance(share,str)  else [ ]
        samplesD        = { }
        samplesB        = [ ]
        samplesS        = [ ]
        sharedsamples   = [ ]
        for sample in self.samplesB:
          if filter and sample.isPartOf(*filterterms,exclusive=False):
            if share:
              newsample = sample
              sharedsamples.append(newsample)
            else:
              newsample = sample.clone(samename=True,deep=deep)
            samplesB.append(newsample)
          elif not filter:
            if share or (shareterms and sample.isPartOf(*shareterms,exclusive=False)):
              newsample = sample
              sharedsamples.append(newsample)
            else:
              newsample = sample.clone(samename=True,deep=deep)
            samplesB.append(newsample)
        for sample in self.samplesS:
          if filter and sample.isPartOf(*filterterms,exclusive=False):
            if share:
              newsample = sample
              sharedsamples.append(newsample)
            else:
              newsample = sample.clone(samename=True,deep=deep)
            samplesB.append(newsample)
          elif not filter:
            if share or (shareterms and sample.isPartOf(*shareterms,exclusive=False)):
              newsample = sample
              sharedsamples.append(newsample)
            else:
              newsample = sample.clone(samename=True,deep=deep)
            samplesS.append(newsample)
        if not filter:
          samplesD = self._samplesD
          sharedsamples.append(samplesD)
        
        kwargs['shared'] = sharedsamples
        kwargs['name']   = name
        newset = SampleSet(samplesD,samplesB,samplesS,**kwargs)
        newset.closed = close
        return newset
    
    def reloadFiles(self,**kwargs):
        """Help function to reload all files in samples list."""
        for sample in self.samples:
          sample.reload(**kwargs)
        self.closed = False
    
    def refreshMemory(self,**kwargs):
        """Open/reopen files to reset file memories."""
        verbosity = getVerbosity(kwargs,verbositySampleTools)
        now       = kwargs.get('now',  False )
        step      = kwargs.get('step', 10    )
        kwargs['verbosity'] = verbosity
        gROOT.cd()
        if verbosity>1:
          LOG.warning('SampleSet::refreshMemory refreshing memory (gDirectory "%s")'%(gDirectory.GetName()))
          gDirectory.ls()
        if now or (self.nPlotsMade%step==0 and self.nPlotsMade>0):
          self.reloadFiles(**kwargs)
          self.nPlotsMade = 0
        self.nPlotsMade +=1
    
    def changeContext(self,*args):
        """Help function to change context of variable object."""
        for arg in args:
          if isinstance(arg,Variable):
            arg.changeContext(self.channel)
            selections = [a for a in args if isinstance(a,Selection) or isSelectionString(a)]
            if len(selections)>0:
              arg.changeContext(selections[0] if isinstance(selections[0],str) else selections[0].selection)
            return arg
        return None
    
    def plotStack(self, *args, **kwargs):
        """Create histograms and make a Plot object to plot a stack."""
        self.refreshMemory()
        kwargs['stack'] = True
        if isinstance(args[0],Variable):
          var             = self.changeContext(*args)
          plotargs        = [ var ] if var else [ ]
        elif isinstance(args[0],str):
          plotargs        = [ args[0] ]
        else:
          LOG.error("Samples::plotStack: First argument %s is not a Variable object or string!")
        plotargs       += self.createHistograms(*args,**kwargs)
        return Plot(*plotargs,**kwargs)
    
    def getStack(self, *args, **kwargs):
        """Get data histogram."""
        name                   = kwargs.get('name',"stack")
        kwargs.update({'data':False, 'signal':False, 'background':True})
        var                    = self.changeContext(*args)
        histsD, histsB, histsS = self.createHistograms(*args,**kwargs)
        stack                  = THStack(name,name)
        for hist in histsB:
          stack.Add(hist)
        return stack
        
    
    def getData(self, *args, **kwargs):
        """Create histograms of background simulations and make a stack."""
        name                   = kwargs.get('name',"data")
        kwargs.update({'data':True, 'signal':False, 'background':False})
        var                    = self.changeContext(*args)
        histsD, histsB, histsS = self.createHistograms(*args,**kwargs)
        return histsD[0]

    
    def createHistograms(self, *args, **kwargs):
        """Create histograms for all samples and return lists of histograms."""
        
        var, nbins, xmin, xmax, xbins, cuts = unwrapVariableSelection(*args)
        verbosity       = getVerbosity(kwargs,verbositySampleTools)
        data            = kwargs.get('data',            True                )
        signal          = kwargs.get('signal',          True                )
        background      = kwargs.get('background',      True                )
        divideBinSize   = kwargs.get('divideByBinSize', False               )
        weight          = kwargs.get('weight',          ""                  )
        weight_data     = kwargs.get('weight_data',     ""                  )
        replaceweight   = kwargs.get('replaceweight',   None                )
        split           = kwargs.get('split',           True                )
        blind           = kwargs.get('blind',           True                )
        scaleup         = kwargs.get('scaleup',         0.0                 )
        reset           = kwargs.get('reset',           False               )
        append          = kwargs.get('append',          ""                  )
        makeJTF         = kwargs.get('JFR',             False               )
        #makeJTF         = kwargs.get('FF',              False               )
        noJTF           = kwargs.get('noJTF',           makeJTF             )
        makeQCD         = kwargs.get('QCD',             False               ) and not makeJTF
        ratio_WJ_QCD    = kwargs.get('ratio_WJ_QCD_SS', False               )
        QCDshift        = kwargs.get('QCDshift',        0.0                 )
        QCDrelax        = kwargs.get('QCDrelax',        False               )
        task            = kwargs.get('task',            "making histograms" )
        saveToFile      = kwargs.get('saveToFile',      ""                  )
        file            = createFile(saveToFile,text=cuts) if saveToFile else None
        gROOT.cd()
        
        histsS          = [ ]
        histsB          = [ ]
        histsD          = [ ]
        #samples_dict    = { }
        
        samples = [ ]
        if split:
          for sample in self.samples:
            if not signal and sample.isSignal: continue
            if not data   and sample.isData:   continue
            if noJTF and (sample.isPartOf("WJ","W*J","W*j") or "gen_match_2==6" in sample.cuts):
              continue
            if sample.splitsamples:
              samples += sample.splitsamples
            else:
              samples.append(sample)
        else:
          for sample in self.samples:
            if not signal and sample.isSignal: continue
            if not data   and sample.isData:   continue
            if noJTF and (sample.isPartOf("WJ","W*J","W*j") or "gen_match_2==6" in sample.cuts):
              continue
            samples.append(sample)
            
        
        bar = None
        if verbosity>1:
            if not ("QCD" in task or "JFR" in task):
              print header("creating histograms for variable %s"%(var))
            print ">>> split=%s, makeQCD=%s, makeJTF=%s, noJTF=%s"%(split,makeQCD,makeJTF,noJTF)
            print '>>>   with extra weights "%s" for MC and "%s" for data'%(weight,weight_data)
        elif self.loadingbar and verbosity<2:
            bar = LoadingBar(len(samples),width=16,pre=">>> %s: %s: "%(var,task),counter=True,remove=True)
        for sample in samples:
            if bar:   bar.message(sample.title)
            if reset: sample.resetScale()
            if sample.name in self.ignore:
              if bar: bar.count("%s skipped"%sample.title)
              continue
            
            # ADD background
            if sample.isBackground and background:
              hist = sample.hist(*args,append=append,weight=weight,noJTF=noJTF,divideByBinSize=divideBinSize,replaceweight=replaceweight,verbosity=verbosity)
              histsB.append(hist)
            
            # ADD signal
            elif sample.isSignal and signal:
              hist = sample.hist(*args,append=append,weight=weight,noJTF=noJTF,divideByBinSize=divideBinSize,verbosity=verbosity,scaleup=scaleup)
              histsS.append(hist)
            
            # ADD data
            elif sample.isData and data:
              hist = sample.hist(*args,append=append,weight=weight_data,blind=blind,divideByBinSize=divideBinSize,verbosity=verbosity)
              histsD.append(hist)
            
            if bar: bar.count("%s done"%sample.name)
        
        # ADD QCD
        if makeJTF:
            hist = self.jetFakeRate(*args,xbins=xbins,append=append,weight=weight,divideByBinSize=divideBinSize,verbosity=verbosity,saveToFile=file)
            if hist:
              histsB.insert(0,hist)
        elif makeQCD:
            hist = self.QCD(*args,xbins=xbins,shift=QCDshift,ratio_WJ_QCD_SS=ratio_WJ_QCD,append=append,weight=weight,divideByBinSize=divideBinSize,verbosity=verbosity,saveToFile=file)
            if hist:
              histsB.insert(0,hist)
        
        if len(histsD)>1:
          LOG.warning("SampleSet::createHistograms: More than one data histogram!")
        
        # SAVE histograms
        if file:
          file.cd()
          for hist in histsD + histsB + histsS:
            hist.GetXaxis().SetTitle(var)
            hist.Write(hist.GetName())
            #file.Write(hist.GetName())
          file.Close()
          gROOT.cd()
        
        return [ histsD, histsB, histsS ] #, samples_dict
        
    
    
    def createHistograms2D(self, *args, **kwargs):
        """Create histograms for all samples and return lists of histograms."""
        
        xvar, nxbins, xmin, xmax, xbins,\
        yvar, nybins, ymin, ymax, ybins, cuts = unwrapVariableSelection2D(*args)
        
        verbosity       = getVerbosity(kwargs,verbositySampleTools)
        data            = kwargs.get('data',            True                   )
        background      = kwargs.get('background',      True                   )
        weight          = kwargs.get('weight',          ""                     )
        weight_data     = kwargs.get('weight_data',     ""                     )
        append          = kwargs.get('append',          ""                     )
        makeJTF         = kwargs.get('JFR',             False                  )
        noJTF           = kwargs.get('noJTF',           makeJTF                )
        task            = kwargs.get('task',            "making histograms"    )
        gROOT.cd()
        
        histsS          = [ ]
        histsB          = [ ]
        histsD          = [ ]
        
        samples = [ ]
        for sample in self.samples:
          if not data   and sample.isData:   continue
          if noJTF and (sample.isPartOf("WJ","W*J","W*j") or "gen_match_2==6" in sample.cuts):
            continue
          samples.append(sample)
        
        bar = None
        if self.loadingbar and verbosity<2:
            bar = LoadingBar(len(samples),width=16,pre=">>> %s vs. %s: %s: "%(yvar,xvar,task),counter=True,remove=True)
        for sample in samples:
            if bar:   bar.message(sample.title)
            if sample.name in self.ignore:
              if bar: bar.count("%s skipped"%sample.title)
              continue
            
            # ADD background
            if sample.isBackground and background:
              hist = sample.hist2D(*args,append=append,weight=weight,noJTF=noJTF,verbosity=verbosity)
              histsB.append(hist)
            
            # ADD data
            elif sample.isData and data:
              hist = sample.hist2D(*args,append=append,weight=weight_data,verbosity=verbosity)
              histsD.append(hist)
            
            if bar: bar.count("%s done"%sample.name)
        
        # ADD JTF
        if makeJTF:
            hist = self.jetFakeRate2D(*args,append=append,weight=weight,verbosity=verbosity)
            if hist: histsB.insert(0,hist)
        
        if len(histsD)>1:
          LOG.warning("SampleSet::createHistograms: More than one data histogram!")
        
        return [ histsD, histsB, histsS ]
    
    
    
    def jetFakeRate(self, *args, **kwargs):
        """Estimate tau fake rate background.
           - selection:
               all events passing VLoose tau ID, but failing Tight
               MC events passing gen_match<6
           - fake rate:
               weight*( data - MC )
           - NOTE: discard all MC events with gen_match==6
        """
        
        gROOT.cd()
        verbosity       = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts0 = unwrapVariableSelection(*args)
        if verbosity > 1:
            print header("estimating fakeRate for variable %s" % (var))
        name            = kwargs.get('name',            makeHistName("JTF",var) )
        append          = kwargs.get('append',          ""                      )+"_JFR"
        title           = kwargs.get('title',           "j -> tau fakes"        )
        weight          = kwargs.get('weight',          ""                      )
        weight_data     = kwargs.get('weight',          ""                      )
        file            = kwargs.get('saveToFile',      None                    )
        shift           = kwargs.get('shift',           None                    )
        anisolated      = False
        name           += append
        
        # WEIGHT
        gROOT.ProcessLine('setID("MVArerun")')
        weightFR        = 'getFakeRate(pt_2,m_2,eta_2,decayMode_2)' # pt-, eta-/mass-dependent
        #weightFR        = 'getFakeRate(pt_2,m_2,decayMode_2)' # pt-, mass-dependent
        ###weightFR        = "getFakeRate(pt_2,decayMode_2)" # pt-dependent only
        if shift:
          if 'down' in shift.lower(): weightFR = weightFR.replace('getFakeRate','getFakeRateDown')
          elif 'up' in shift.lower(): weightFR = weightFR.replace('getFakeRate','getFakeRateUp')
          else: LOG.warning('SampleSet::jetFakeRate: Did not recognize shift "%s"!'%(shift))
        
        # CUTS
        cuts          = vetoJetTauFakes(cuts0)
        cuts_aniso    = "iso_2_vloose==1 && iso_2!=1"
        isomatch      = re.findall(r"iso_2\ *==\ *1",cuts)
        anisomatch    = re.findall(r"iso_2_vloose\ *==\ *1 && iso_2\ *!=\ *1",cuts)
        if len(isomatch)==0 and len(anisomatch)==0:
          cuts_aniso  = "byVLooseIsolationMVArun2v1DBnewDMwLT_2==1 && byTightIsolationMVArun2v1DBnewDMwLT_2!=1"
          isomatch    = re.findall(r"byTightIsolationMVArun2v1DBnewDMwLT_2\ *==\ *1",cuts)
          anisomatch  = re.findall(r"byVLooseIsolationMVArun2v1DBnewDMwLT_2\ *==\ *1 && byTightIsolationMVArun2v1DBnewDMwLT_2\ *!=\ *1",cuts)
          if len(isomatch)>0: gROOT.ProcessLine('setID("MVArerunv1new")')
        if len(isomatch)==0 and len(anisomatch)==0:
          cuts_aniso  = "byVLooseIsolationMVArun2v2DBoldDMwLT_2==1 && byTightIsolationMVArun2v2DBoldDMwLT_2!=1"
          isomatch    = re.findall(r"byTightIsolationMVArun2v2DBoldDMwLT_2\ *==\ *1",cuts)
          anisomatch  = re.findall(r"byVLooseIsolationMVArun2v2DBoldDMwLT_2\ *==\ *1 && byTightIsolationMVArun2v2DBoldDMwLT_2\ *!=\ *1",cuts)
          if len(isomatch)>0: gROOT.ProcessLine('setID("MVArerunv2")')
        if len(isomatch)==0 and len(anisomatch)==1:
          LOG.warning('SampleSet::jetFakeRate: Using anti-isolated selection "%s" for fake rate!'%(cuts))
          isomatch    = anisomatch
          anisolated  = True
        elif len(isomatch)==0:
          LOG.error('SampleSet::jetFakeRate: Cannot apply fake rate method to selections "%s" without tau isolation!'%(cuts))
        elif len(isomatch)>1:
          LOG.warning('SampleSet::jetFakeRate: Selection string "%s" has two tau isolations!'%(cuts))
        isomatch      = isomatch[0]
        if not anisolated:
          cuts        = cuts.replace(isomatch,cuts_aniso)
          weight      = combineWeights(weightFR,weight)
          weight_data = weightFR
        if verbosity>1:
          print '>>> SampleSet::jetFakeRate:\n>>>   cuts0="%s"\n>>>   cuts="%s"\n>>>   cuts_aniso="%s"\n>>>   weightFR="%s"'%(cuts0,cuts,cuts_aniso,weightFR)
        
        ## HISTOGRAMS
        #histsD_JFR, histsB_JFR, _ = self.createHistograms(var,N,a,b,cuts,weight=weight,weight_data=weight_data,append=append,
        #                                                  signal=False,background=False,QCD=False,task="calculating JFR",split=False,blind=False,noJTF=True)
        #histJTF = histsD_JFR[0].Clone(name)
        #histJTF.SetTitle(title)
        #histJTF.SetFillColor(getColor('JTF'))
        #histMC_JFR = histsD_JFR[0].Clone("MC_JFR")
        #histMC_JFR.Reset()
        
        # HISTOGRAMS
        histsD_JFR, histsB_JFR, _ = self.createHistograms(var,nbins,xmin,xmax,cuts,weight=weight,weight_data=weight_data,append=append,
                                                          signal=False,QCD=False,task="calculating JFR",split=False,blind=False,noJTF=True)
        
        # CHECK histograms
        if not histsD_JFR:
            LOG.warning("SampleSet::jetFakeRate: No data to make DATA driven JFR!")
            return None
        histD_JFR = histsD_JFR[0]
        if not histsB_JFR:
            LOG.warning("SampleSet::jetFakeRate: No MC to make JFR!")
            return None
        
        # JTF HIST
        histMC_JFR = histsB_JFR[0].Clone("MC_JFR")
        histMC_JFR.SetTitle("sum of all MC in JFR CR")
        for hist in histsB_JFR[1:]: histMC_JFR.Add(hist)
        histJTF = substractHistsFromData(histD_JFR,histMC_JFR,name=name,title=title)
        if not histJTF: LOG.warning("SampleSet::jetFakeRate: Could not make JTF! JTF histogram is none!", pre="  ")
        histJTF.SetFillColor(getColor('JTF'))
        histJTF.SetOption('HIST')
        
        # SAVE histograms
        if file:
          dir = file.mkdir('jetTauFake')
          dir.cd()
          canvas, pave = canvasWithText(cuts)
          pave.AddText("weight: "+weight)
          canvas.Write("selections")
          for hist in histsB_JFR+histsD_JFR+[histMC_JFR]:
            hist.GetXaxis().SetTitle(var)
            hist.Write(hist.GetName())
            #dir.Write(hist.GetName())
          gROOT.cd()
        
        # PRINT
        if verbosity>1:
          MC_JFR   = histMC_JFR.Integral()
          data_JFR = histD_JFR.Integral()
          JFR      = histJTF.Integral()
          print ">>> SampleSet::jetFakeRate: - data = %.1f, MC = %.1f, JFR = %.1f"%(data_JFR,MC_JFR,JFR)
        
        close(histsB_JFR+histsD_JFR+[histMC_JFR])
        return histJTF
        
    
    def jetFakeRate2D(self, *args, **kwargs):
        """Estimate tau fake rate background in 2D."""
        
        gROOT.cd()
        verbosity            = getVerbosity(kwargs,verbositySampleTools)
        xvar, nxbins, xmin, xmax, xbins,\
        yvar, nybins, ymin, ymax, ybins, cuts0 = unwrapVariableSelection2D(*args,**kwargs)
        
        if verbosity > 1:
            print header("estimating fakeRate for variable %s" % (var))
        name            = kwargs.get('name',            makeHistName("JTF",yvar,xvar) )
        append          = kwargs.get('append',          ""                            )+"_JFR"
        title           = kwargs.get('title',           "j -> tau fakes"              )
        weight          = kwargs.get('weight',          ""                            )
        weight_data     = kwargs.get('weight',          ""                            )
        xbins           = kwargs.get('xbins',           [ ]                           )
        ybins           = kwargs.get('ybins',           [ ]                           )
        name           += append
        
        # WEIGHT & CUTS
        weightFR        = "getFakeRate(pt_2,m_2,decayMode_2)" # pt-, mass- dependent 
        cuts        = vetoJetTauFakes(cuts0)
        isomatch    = re.findall(r"iso_2\ *==\ *1",cuts)
        anisomatch  = re.findall(r"iso_2_vloose\ *==\ *1 && iso_2\ *!=\ *1",cuts)
        if len(isomatch)==0 and len(anisomatch)==1:
          LOG.warning('SampleSet::jetFakeRate: Using anti-isolated selection "%s" for fake rate!'%(cuts))
          isomatch   = anisomatch
        elif len(isomatch)==0:
          LOG.error('SampleSet::jetFakeRate: Cannot apply fake rate method to selections "%s" without tau isolation!'%(cuts))
        elif len(isomatch)>1:
          LOG.error('SampleSet::jetFakeRate: Selection string "%s" has two tau isolations!'%(cuts))
        isomatch    = isomatch[0]
        cuts        = cuts.replace(isomatch,"iso_2_vloose==1 && iso_2!=1")
        weight      = combineWeights(weightFR,weight)
        weight_data = weightFR
        
        # HISTOGRAMS
        histsD_JFR, histsB_JFR, _ = self.createHistograms2D(xvar,nxbins,xmin,xmax,yvar,nybins,ymin,ymax,cuts,xbins=xbins,ybins=ybins,weight=weight,weight_data=weight_data,append=append,
                                                            signal=False,QCD=False,task="calculating JFR",split=False,noJTF=True)
        
        # CHECK histograms
        if not histsD_JFR:
            LOG.warning("SampleSet::jetFakeRate: No data to make DATA driven JFR!")
            return None
        histD_JFR = histsD_JFR[0]
        if not histsB_JFR:
            LOG.warning("SampleSet::jetFakeRate: No MC to make JFR!")
            return None
        
        # JTF HIST
        histMC_JFR = histsB_JFR[0].Clone("MC_JFR")
        histMC_JFR.SetTitle("sum of all MC in JFR CR")
        for hist in histsB_JFR[1:]: histMC_JFR.Add(hist)
        histJTF = substractHistsFromData(histD_JFR,histMC_JFR,name=name,title=title)
        if not histJTF: LOG.warning("SampleSet::jetFakeRate: Could not make JTF! JTF histogram is none!", pre="  ")
        histJTF.SetOption("COLZ")
                
        # PRINT
        if verbosity>1:
          MC_JFR   = histMC_JFR.Integral()
          data_JFR = histD_JFR.Integral()
          JFR      = histJTF.Integral()
          print ">>> SampleSet::jetFakeRate: - data = %.1f, MC = %.1f, JFR = %.1f"%(data_JFR,MC_JFR,JFR)
        
        close(histsB_JFR+histsD_JFR+[histMC_JFR])
        return histJTF
    
        
    def QCD(self,*args,**kwargs):
        if self.isNanoAOD: return self.QCD_ABCD(*args,**kwargs)
        else:              return self.QCD_old(*args,**kwargs)
    
    def QCD_old(self,*args,**kwargs):
        """Substract MC from data with same sign (SS) selection of a lepton - tau pair
           and return a histogram of the difference."""
        
        verbosity       = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts0 = unwrapVariableSelection(*args)
        isJetCategory   = re.search(r"(nc?btag|n[cf]?jets)",cuts0)
        relax           = 'emu' in self.channel or isJetCategory
        if verbosity > 1:
            print header("estimating QCD for variable %s" % (var))
            #LOG.verbose("\n>>> estimating QCD for variable %s" % (self.var),verbosity,level=2)
        
        samples         = self.samples
        name            = kwargs.get('name',            makeHistName("QCD",var) )
        title           = kwargs.get('title',           "QCD multijet"          )
        append          = kwargs.get('append',          ""                      )+"_SS"
        ratio_WJ_QCD    = kwargs.get('ratio_WJ_QCD_SS', False                   )
        doRatio_WJ_QCD  = isinstance(ratio_WJ_QCD,      c_double                )
        weight          = kwargs.get('weight',          ""                      )
        weight_data     = kwargs.get('weight',          ""                      )
        shift           = kwargs.get('shift',           0.0                     ) + self.shiftQCD # for systematics
        #vetoRelax       = kwargs.get('vetoRelax',       relax                   )
        relax           = kwargs.get('relax',           relax                   ) #and not vetoRelax
        file            = kwargs.get('saveToFile',      None                    )
        
        if relax and re.search(r"(nc?btag|n[cf]?jets)",var):
          LOG.warning('SampleSet::QCD: not relaxing cuts in QCD CR for "%s"'%(var))
          relax = False
        
        scaleup         = 1.0 if "q_1*q_2>0" else 2.0 if "emu" in self.channel else OSSS_ratio
        scaleup         = kwargs.get('scaleup',         scaleup                 )
        LOG.verbose("   QCD: scaleup = %s, shift = %s, self.shiftQCD = %s"%(scaleup,shift,self.shiftQCD),verbosity,level=2)
        
        # CUTS: invert charge
        cuts            = invertCharge(cuts0,to='SS')
        
        # CUTS: relax cuts for QCD_SS_SB
        # https://indico.cern.ch/event/566854/contributions/2367198/attachments/1368758/2074844/QCDStudy_20161109_HTTMeeting.pdf
        QCD_OS_SR = 0
        if relax:
            
            # GET yield QCD_OS_SR = SF * QCD_SS_SR
            if 'emu' in self.channel: # use weight instead of scaleup
                scaleup     = 1.0
                weight      = combineWeights("getQCDWeight(pt_2, pt_1, dR_ll)",weight)
                weight_data = "getQCDWeight(pt_2, pt_1, dR_ll)" # SF ~ 2.4 average
            kwargs_SR       = kwargs.copy()
            kwargs_SR.update({ 'scaleup':scaleup, 'weight':weight, 'weight_data':weight_data, 'relax':False })
            histQCD_OS_SR   = self.QCD(*args,**kwargs_SR)
            QCD_OS_SR       = histQCD_OS_SR.Integral(1,N) # yield
            scaleup         = 1.0
            deleteHist(histQCD_OS_SR)
            if QCD_OS_SR < 10:
              LOG.warning('QCD: QCD_SR = %.1f < 10 for "%s"'%(QCD_OS_SR,cuts0))
            
            # RELAX cuts for QCD_OS_SB = SF * QCD_SS_SB
            append      = "_isorel" + append
            iso_relaxed = "iso_1>0.15 && iso_1<0.5 && iso_2_medium==1" #iso_2_medium
            if 'emu' in self.channel: iso_relaxed = "iso_1>0.20 && iso_1<0.5 && iso_2<0.5"
            elif isJetCategory: cuts = relaxJetSelection(cuts)
            cuts = invertIsolation(cuts,to=iso_relaxed)
            
            ## CHECK for 30 GeV jets
            #if "bpt_" in var and "btag" in cuts0 and "btag" not in cuts:
            #  btags_g  = re.findall(r"&*\ *nc?btag\ *>\ *(\d+)\ *",cuts0)
            #  btags_ge = re.findall(r"&*\ *nc?btag\ *>=\ *(\d+)\ *",cuts0)
            #  btags_e  = re.findall(r"&*\ *nc?btag\ *==\ *(\d+)\ *",cuts0)
            #  nbtags = 0
            #  if   btags_g:  nbtags = int(btags_g[0])+1
            #  elif btags_ge: nbtags = int(btags_ge[0])
            #  elif btags_e:  nbtags = int(btags_e[0])
            #  if nbtags>0:
            #    if "bpt_1" in var and nbtags>0:
            #      cuts+=" && bpt_1>30"
            #      LOG.warning("QCD: %s - added 30 GeV cut on b jets in \"%s\""%(var,cuts))
            #    if "bpt_2" in var and nbtags>1:
            #      cuts+=" && bpt_2>30"
            #      LOG.warning("QCD: %s - added 30 GeV cut on b jets in \"%s\""%(var,cuts))
        
        LOG.verbose("   QCD - cuts = %s %s"%(cuts,"(relaxed)" if relax else ""),verbosity,level=2)
        
        # HISTOGRAMS
        gROOT.cd()
        histD  = None
        histWJ = None
        histsD_SS, histsB_SS, _ = self.createHistograms(var,nbins,xmin,xmax,xbins,cuts,weight=weight,weight_data=weight_data,append=append,
                                                        signal=False,QCD=False,task="calculating QCD",split=False,blind=False,verbosity=verbosity-1)
        
        # GET WJ
        if doRatio_WJ_QCD:
          for hist in histsB_SS:
            if ("WJ" in hist.GetName() or re.findall(r"w.*jets",hist.GetName(),re.IGNORECASE)):
              if histWJ:
                LOG.warning("SampleSet::QCD: more than one W+jets sample in SS region, going with first instance!", pre="  ")
                break
              else: histWJ = hist
          if not histWJ:
            LOG.warning("SampleSet::QCD: Did not find W+jets sample!", pre="  ")
        
        # CHECK data
        if not histsD_SS:
            LOG.warning("SampleSet::QCD: No data to make DATA driven QCD!")
            return None
        histD_SS = histsD_SS[0]
        
        # QCD HIST
        histMC_SS  = histsB_SS[0].Clone("MC_SS")
        for hist in histsB_SS[1:]: histMC_SS.Add(hist)
        histQCD = substractHistsFromData(histsD_SS[0],histMC_SS,name=name+append,title=title)
        if not histQCD: LOG.warning("SampleSet::QCD: Could not make QCD! QCD histogram is none!", pre="  ")
        
        # SAVE histograms
        if file:
          dir = file.mkdir('QCD_relaxed' if relax else 'QCD')
          dir.cd()
          canvas, pave = canvasWithText(cuts)
          pave.AddText("weight: "+weight)
          canvas.Write("selections")
          for hist in histsB_SS+histsD_SS+[histMC_SS]:
            hist.GetXaxis().SetTitle(var)
            hist.Write(hist.GetName())
          gROOT.cd()
        
        # YIELD only
        if relax:
            QCD_SS = histQCD.Integral(1,N)
            if QCD_SS:
              scaleup = QCD_OS_SR/QCD_SS # normalizing to OS_SR
              LOG.verbose("   QCD - scaleup = QCD_OS_SR/QCD_SS_SB = %.1f/%.1f = %.3f"%(QCD_OS_SR,QCD_SS,scaleup),verbosity,level=2)
            else:
              LOG.warning("SampleSet::QCD: QCD_SS_SB.Integral() == 0!")
        scale   = scaleup*(1.0+shift) # scale up QCD 6% in OS region by default
        histQCD.Scale(scale)
        histQCD.SetFillColor(getColor('QCD'))
        histQCD.SetOption("HIST")
        MC_SS   = histMC_SS.Integral()
        data_SS = histD_SS.Integral()
        QCD_SS  = histQCD.Integral()
        
        # WJ/QCD ratio in SS
        if doRatio_WJ_QCD and histWJ:
            WJ_SS  = histWJ.Integral()
            if QCD_SS: ratio_WJ_QCD.value = WJ_SS/QCD_SS
            else: LOG.warning("SampleSet::QCD - QCD integral is 0!", pre="  ")
            LOG.verbose("   QCD - data_SS = %.1f, MC_SS = %.1f, QCD_SS = %.1f, scale=%.3f, WJ_SS = %.1f, ratio_WJ_QCD_SS = %.3f"%(data_SS,MC_SS,QCD_SS,scale,WJ_SS,ratio_WJ_QCD.value),verbosity,level=2)
        else:
            LOG.verbose("   QCD - data_SS = %.1f, MC_SS = %.1f, QCD_SS = %.1f, scale=%.3f"%(data_SS,MC_SS,QCD_SS,scale),verbosity,level=2)
        
        close(histsB_SS+histsD_SS+[histMC_SS])
        return histQCD
        
    
    
    def QCD_ABCD(self,*args,**kwargs):
        """Estimate the QCD in a data-driven way with the ABCD method:
        Substract MC from data in three different regions:
                           OS          SS
          isolated         A=SR        B
          anti-isolated    C=shape     D
        Get the shape from region C, get the yield as B*C/D, where C/D = OS/SS ratio.
        """
        
        verbosity       = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts0 = unwrapVariableSelection(*args)
        if verbosity > 1:
          print header("estimating QCD (ABCD) for variable %s" % (var))
          #LOG.verbose("\n>>> estimating QCD for variable %s" % (self.var),verbosity,level=2)
        
        samples         = self.samples
        name            = kwargs.get('name',            makeHistName("QCD",var) )
        title           = kwargs.get('title',           "QCD multijet"          )
        append          = kwargs.get('append',          ""                      )+"_SS"
        weight          = kwargs.get('weight',          ""                      )
        weight_data     = kwargs.get('weight',          ""                      )
        shift           = kwargs.get('shift',           0.0                     ) + self.shiftQCD # for systematics
        ratio_WJ_QCD    = kwargs.get('ratio_WJ_QCD_SS', False                   )
        doRatio_WJ_QCD  = isinstance(ratio_WJ_QCD,      c_double                )
        
        # SELECTIONS
        if 'tautau' in self.channel:
          yvar       = "isoRegion(idMVAoldDM2017v2_1,idMVAoldDM2017v2_2)"
          cuts_aniso = "((idMVAoldDM2017v2_1>=8 && idMVAoldDM2017v2_2<16 && idMVAoldDM2017v2_2>=4) || (idMVAoldDM2017v2_2>=8 && idMVAoldDM2017v2_1<16 && idMVAoldDM2017v2_1>=4))"
        else:
          LOG.warning('QCD_ABCD not implemented for %s channel!'%(self.channel))
          return None
        cuts_aniso = invertIsolationNanoAOD(cuts0,to=cuts_aniso,verbosity=verbosity)
        cuts_naked = invertIsolationNanoAOD(cuts0,to='',verbosity=verbosity)
        cuts_naked = invertCharge(cuts_naked,to='',verbosity=verbosity)
        
        # YIELDS
        xvar = "q_1*q_2" #"signRegion(q_1,q_2)"
        histsD_ABCD, histsB_ABCD, _ = self.createHistograms2D(xvar,2,-10,10,yvar,2,1,3,cuts_naked,weight=weight,weight_data=weight_data,append=append,
                                                              signal=False,QCD=False,JFR=False,blind=False,split=False,task="calculating QCD's ABCD yields")
        if not histsD_ABCD:
          LOG.warning("SampleSet::QCD_ABCD: No data to make DATA driven QCD!")
          return None
        histD_ABCD = histsD_ABCD[0]
        histQCD_ABCD = histsB_ABCD[0].Clone(name+"_ABCD")
        histQCD_ABCD.Reset()
        histQCD_ABCD.Add(histD_ABCD)
        for histB in histsB_ABCD:
          histQCD_ABCD.Add(histB,-1)
        N_OS_iso   = histQCD_ABCD.GetBinContent(1,2) # A
        N_SS_iso   = histQCD_ABCD.GetBinContent(2,2) # B
        N_OS_aniso = histQCD_ABCD.GetBinContent(1,1) # C
        N_SS_aniso = histQCD_ABCD.GetBinContent(2,1) # D
        if verbosity>1:
          print ">>>   total data = %.1f"%(histD_ABCD.Integral())
          print ">>>   ABCD yields:                %10s %10s"%('OS','SS')
          print ">>>                isolated       %10.1f %10.1f"%(N_OS_iso,  N_SS_iso  )
          print ">>>                anti-isolated  %10.1f %10.1f"%(N_OS_aniso,N_SS_aniso)
        scale  = N_SS_iso*N_OS_aniso/N_SS_aniso*(1.0+shift)
        close([histQCD_ABCD]+histsD_ABCD+histsB_ABCD)
        
        # HISTOGRAMS
        args_aniso = list(args[:-1])+[cuts_aniso]
        histsD_OS_aniso, histsB_OS_aniso, _ = self.createHistograms(*args_aniso,weight=weight,weight_data=weight_data,append=append,
                                                                    signal=False,QCD=False,JFR=False,split=False,blind=False,task="calculating QCD ABCD shape",verbosity=verbosity-1)
        if not histsD_OS_aniso:
          LOG.warning("SampleSet::QCD_ABCD: No data to make DATA driven QCD!")
          return None
        histD_OS_aniso = histsD_OS_aniso[0]

        
        # GET WJ
        histWJ = None
        if doRatio_WJ_QCD:
          for hist in histsB_OS_aniso:
            if ('WJ' in hist.GetName() or re.findall(r"w.*jets",hist.GetName(),re.IGNORECASE)):
              if histWJ_OS_aniso:
                LOG.warning("SampleSet::QCD_ABCD: more than one W+jets sample in SS region, going with first instance!", pre="  ")
                break
              else: histWJ_OS_aniso = hist
          if not histWJ_OS_aniso:
            LOG.warning("SampleSet::QCD_ABCD: Did not find W+jets sample!", pre="  ")
        
        histMC_OS_aniso = histsB_OS_aniso[0].Clone(name+"_MC_OS_aniso")
        histMC_OS_aniso.Reset()
        for histB in histsB_OS_aniso:
          histMC_OS_aniso.Add(histB)
        histQCD = histsB_OS_aniso[0].Clone(name)
        histQCD.SetTitle(title)
        histQCD.Reset()
        histQCD.Add(histD_OS_aniso)
        histQCD.Add(histMC_OS_aniso,-1)
        histQCD.SetFillColor(getColor('QCD'))
        histQCD.SetOption("HIST")
        
        MC_OS_aniso   = histMC_OS_aniso.Integral()
        data_OS_aniso = histD_OS_aniso.Integral()
        QCD_OS_aniso  = histQCD.Integral()
        
        # CHECK yield
        if verbosity>2:
          under, over = histQCD.GetBinContent(0), histQCD.GetBinContent(histQCD.GetXaxis().GetNbins()+1)
          print ">>> check: QCD_OS_aniso + under-/overflow = %.1f + %.1f + %.1f = %.1f  <->  %.1f"%(QCD_OS_aniso,under,over,QCD_OS_aniso+under+over,N_OS_aniso)
        
        # CHECK negative bins
        nNegBins = 0
        for i, bin in enumerate(histQCD):
          if bin<0:
            histQCD.SetBinContent(i,0)
            histQCD.SetBinError(i,1)
            nNegBins += 1
        LOG.warning("SampleSet::QCD_ABCD: %d/%d negative bins! Set to 0 +- 1"%(nNegBins,nbins), pre="  ")
        
        # CHECK integral
        if QCD_OS_aniso==0:
          LOG.warning("SampleSet::QCD_ABCD: QCD integral is 0!", pre="  ")
          return histQCD
        histQCD.Scale(scale/QCD_OS_aniso)
        
        if doRatio_WJ_QCD and histWJ_OS_aniso:
          WJ_OS_aniso        = histWJ_OS_aniso.Integral()
          ratio_WJ_QCD.value = WJ_OS_aniso/QCD_OS_aniso
          LOG.verbose("  QCD OS+aniso region: data = %.1f, MC = %.1f, QCD = %.1f, scale=%.3f, WJ = %.1f, ratio_WJ_QCD = %.3f"%(data_OS_aniso,MC_OS_aniso,QCD_OS_aniso,scale,WJ_OS_aniso,ratio_WJ_QCD.value),verbosity,level=2)
        else:
          LOG.verbose("  QCD OS+aniso region: data = %.1f, MC = %.1f, QCD = %.1f, scale=%.3f"%(data_OS_aniso,MC_OS_aniso,QCD_OS_aniso,scale),verbosity,level=2)
        
        close([histMC_OS_aniso]+histsD_OS_aniso+histsB_OS_aniso)
        return histQCD
    
    
       
    def renormalizeWJ(self,cuts,**kwargs):
        """Renormalize WJ by requireing that MC and data has the same number of events in
        the mt_1 > 80 GeV sideband.
        This method assume that the variable of this Plot object is a transverse mass and is plotted
        from 80 GeV to at least 100 GeV."""
        
        var, nbins, xmin, xmax = "pfmt_1", 200, 80, 200
        if isinstance(cuts,Selection): cuts = cuts.selection
        samples       = self.samples
        verbosity     = getVerbosity(kwargs,verbositySampleTools)
        shifts        = kwargs.get('shift',         False )
        weight        = kwargs.get('weight',        ""    )
        QCDshift      = kwargs.get('QCDshift',      0.0   )
        replaceweight = kwargs.get('replaceweight', None  )
        
        # SHIFT
        if shifts:
          var  = shift(var, shifts)
          cuts = shift(cuts,shifts)
        
        LOG.verbose("%srenormalizing WJ with mt > 80 GeV sideband for variable %s(%d,%d,%d) %s"%(kwargs.get('pre',"  "),var,nbins,xmin,xmax,("for %s"%self.name) if self.name else ""),True)
        
        # CHECK mt
        if not re.search(r"m_?t",var,re.IGNORECASE):
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: variable %s is not a transverse mass variable!"%(var), pre="  ")
            return
        
        # CHECK a, b (assume histogram range goes from 80 to >100 GeV)
        LOG.verbose("  nbins=%s, (a,b)=(%s,%s)"%(nbins,xmin,xmax), verbosity, level=2)
        LOG.verbose('  cuts = "%s"'%(cuts), verbosity, level=1)
        if xmin is not 80:
            LOG.warning("SampleSet::renormalizeWJ: renormalizing WJ with %s > %s GeV, instead of mt > 80 GeV!" % (var,xmin), pre="  ")
        if xmax < 150:
            LOG.warning("SampleSet::renormalizeWJ: renormalizing WJ with %s < %s GeV < 150 GeV!" % (var,xmax), pre="  ")
            return
        
        R       = c_double() # ratio_WJ_QCD_SS
        WJ      = None
        histD   = None
        histWJ  = None
        histsWJ = [ ]
        stack   = THStack("stack_QCD","stack_QCD")
        histsD, histsB, histsS = self.createHistograms(var,nbins,xmin,xmax,cuts,reset=True,signal=False,
                                                       QCD=True,QCDshift=QCDshift,QCDrelax=False,ratio_WJ_QCD_SS=R,
                                                       split=False,blind=False,weight=weight,replaceweight=replaceweight)
        
        # CHECK MC and DATA
        if not histsB:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: no MC!", pre="  ")
            return
        if not histsD:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: no data!", pre="  ")
            return
        histD  = histsD[0]
        
        # STACK
        QCD     = False
        e_QCD   = Double()
        I_QCD   = 0
        R       = R.value
        histsWJ = [ ]
        LOG.verbose(" ",verbosity,level=2)
        for hist in histsB:
            if hist.Integral(1,nbins)<=0:
                LOG.warning("SampleSet::renormalizeWJ: ignored %s with an integral of %s <= 0 !" % (hist.GetName(),hist.Integral()), pre="  ")
            if "WJ" in hist.GetName() or re.findall(r"w.jets",hist.GetName(),re.IGNORECASE):
                histsWJ.append(hist)
            if "QCD" in hist.GetName():
                QCD   = True
                I_QCD = hist.IntegralAndError(1,nbins,e_QCD)
            LOG.verbose("   adding to stack %s (%.1f events)" % (hist.GetName(),hist.Integral()),verbosity,level=2)
            stack.Add(hist)
        
        # CHECK WJ hist
        if len(histsWJ) > 1:
            namesWJ = ', '.join([h.GetName() for h in histsWJ])
            LOG.warning("SampleSet::renormalizeWJ: more than one WJ sample (%s), renormalizing with first instance (%s)!"%(namesWJ,histsWJ[0].GetName()), pre="  ")
        elif len(histsWJ) < 1:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: no WJ sample!", pre="  ")
            return 0.
        histWJ  = histsWJ[0]
        
        # GET WJ sample
        WJ      = self.get("WJ",unique=True)
        if not WJ:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: no WJ sample!", pre="  ")
            return 0.
        
        # INTEGRATE
        e_MC    = Double()
        e_D     = Double()
        e_WJ    = Double()
        I_MC    = stack.GetStack().Last().IntegralAndError(1,nbins,e_MC)
        I_D     = histD.IntegralAndError(1,nbins,e_D)
        I_WJ    = histWJ.IntegralAndError(1,nbins,e_WJ)
        purity  = 100.0*I_WJ/I_MC
        close(histsD+histsB+histsS+[stack])
        if I_MC < 10:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: integral of MC is %s < 10!" % I_MC, pre="  ")
            return 0.
        print ">>>    data: %.1f, MC: %.1f, WJ: %.1f, QCD: %.1f, R: %.3f, WJ purity: %.2f%%)" % (I_D,I_MC,I_WJ,I_QCD,R,purity)
        if I_D < 10:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: integral of data is %s < 10!" % I_D, pre="  ")
            return 0.
        if I_WJ < 10:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: integral of WJ is %s < 10!" % I_WJ, pre="  ")
            return 0.
        
        # SET WJ SCALE
        e_MC_noWJ = sqrt(e_MC**2 - e_WJ**2)
        I_MC_noWJ = I_MC - I_WJ
        scale     = ( I_D - I_MC + I_WJ - R*I_QCD ) / (I_WJ - R*I_QCD)
        err_scale = scale * sqrt( (e_D**2+e_MC_noWJ**2+e_QCD**2)/abs(I_D-I_MC_noWJ-R*I_QCD)**2 + (e_WJ**2+e_QCD**2)/(I_WJ-R*I_QCD)**2 )
        purity   *= scale
        
        if scale < 0:
            LOG.warning("SampleSet::renormalizeWJ: could not renormalize WJ: scale = %.2f < 0!" % scale, pre="  ")
            return scale
        WJ.resetScale(scale)
        print ">>>    WJ renormalization scale = %s (new total scale: %.3f, new WJ purity: %.2f%%)" % (color("%.3f"%scale,color='green'),WJ.scale,purity)
        return scale
        
    
    def renormalizeTT(self,cuts,**kwargs):
        """Renormalize TT by requireing that MC and data has the same number of events in some control region.
        ..."""
        
        var, nbins, xmin, xmax = 'pfmt_1', 100, 0, 400
        if isinstance(cuts,Selection): cuts = cuts.selection
        samples         = self.samples
        verbosity       = getVerbosity(kwargs,verbositySampleTools)
        save            = kwargs.get('save',     True                                          ) # save in dictionary for reuse
        revert          = kwargs.get('revert',   True                                          ) # revert to save SF if available
        apply           = kwargs.get('apply',    True                                          ) # apply to TT sample
        MET             = kwargs.get('MET',      60                                            )
        mT              = kwargs.get('mT',       60                                            )
        shifts          = kwargs.get('shift',    False                                         )
        weight          = kwargs.get('weight',   ""                                            )
        baseline        = kwargs.get('baseline', "iso_cuts==1 && lepton_vetos==0 && q_1*q_2<0" )
        LOG.verbose("%srenormalizing TT with %s"%(kwargs.get('pre',"  "),var),True)
        
        # SHIFT
        cuts_noShift = undoShift(cuts)
        if shifts:
          var  = shift(var, shifts)
          cuts = shift(cuts,shifts)
        
        # CATEGORY
        category    = None
        TTcuts1 = "%s && nbtag>0 && ncjets==1 && nfjets >0 && met>%s && pfmt_1>%s && jpt_1>30 && jpt_2>30"%(baseline,MET,mT)
        TTcuts2 = "%s && nbtag>0 && ncjets==2 && nfjets==0 && met>%s && pfmt_1>%s && jpt_1>30 && jpt_2>30"%(baseline,MET,mT)
        matchesb   = re.findall(r"nc?btag(?:20)?\ *>\ *[01]",      cuts_noShift)
        matchesf   = re.findall(r"nfjets(?:20)?\ *[>=]=?\ *[01]",  cuts_noShift)
        matchesnof = re.findall(r"nfjets(?:20)?\ *==\ *0",         cuts_noShift)
        matchesc   = re.findall(r"ncjets(?:20)?\ *[>=]=?\ *[0124]",cuts_noShift)
        if matchesb and matchesc and matchesf:
          category = self.channel+'-1b1f'
        if matchesb and matchesc and matchesnof:
          category = self.channel+'-1b1c'
        if not category:
          #LOG.warning("SampeSet::renormalizeTT: Did not recognize category for selections %s! Reverting to original scale (1)."%(cuts),pre="  ")
          LOG.verbose('SampeSet::renormalizeTT: did not recognize category for selections "%s"! Reverting to original scale (1).'%(cuts),1,pre="  ")
          TT = self.get('TT',unique=True)
          TT.resetScale()
          return 1.
        TTcuts = TTcuts1 if '1b1f' in category else TTcuts2
        LOG.verbose('SampeSet::renormalizeTT: found category "%s" in "%s"'%(category,cuts),1,pre="  ")
        LOG.verbose('                         using TT CR "%s"'%(TTcuts),verbosity,pre="  ")
        
        # PREVIOUS
        if revert and self.TTscale.get(category,1.0)!=1.:
          LOG.verbose('SampeSet::renormalizeTT: found previous scale %f!'%(self.TTscale[category]),1,pre="  ")
          return self.TTscale[category]
        
        # HISTS
        TT      = None
        histD   = None
        histTT  = None
        histsTT = [ ]
        stack   = THStack("stack_TT","stack_TT")
        histsD, histsB, histsS = self.createHistograms(var,nbins,xmin,xmax,TTcuts,reset=True,signal=False,QCD=True,split=False,blind=False)
        
        # CHECK MC and DATA
        if not histsB:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: no MC!", pre="  ")
            return
        if not histsD:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: no data!", pre="  ")
            return
        histD  = histsD[0]
        
        # STACK
        e_QCD   = Double()
        I_QCD   = 0
        histsTT = [ ]
        LOG.verbose(" ",verbosity,level=2)
        for hist in histsB:
            if hist.Integral(1,nbins)<=0:
                LOG.warning("SampleSet::renormalizeTT: ignored %s with an integral of %s <= 0 !" % (hist.GetName(),hist.Integral()), pre="  ")
            if "TT" in hist.GetName() or re.findall(r"ttbar",hist.GetName(),re.IGNORECASE):
                histsTT.append(hist)
            if "qcd" in hist.GetName().lower():
                I_QCD = hist.IntegralAndError(1,nbins,e_QCD)
            LOG.verbose("   adding to stack %s (%.1f events)" % (hist.GetName(),hist.Integral()),verbosity,level=2)
            stack.Add(hist)
        
        # CHECK TT hist
        if len(histsTT) > 1:
            namesTT = ', '.join([h.GetName() for h in histsTT])
            LOG.warning("SampleSet::renormalizeTT: core than one TT sample (%s), renormalizing with first instance (%s)!"%(namesTT,histsTT[0].GetName()), pre="  ")
        elif len(histsTT) < 1:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: no TT sample!", pre="  ")
            return 0.
        histTT  = histsTT[0]
        
        # GET TT sample
        TT      = self.get("TT",unique=True)
        if not TT:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: no TT sample!", pre="  ")
            return 0.
        
        # INTEGRATE
        e_MC    = Double()
        e_D     = Double()
        e_TT    = Double()
        I_MC    = stack.GetStack().Last().IntegralAndError(1,nbins,e_MC)
        I_D     = histD.IntegralAndError(1,nbins,e_D)
        I_TT    = histTT.IntegralAndError(1,nbins,e_TT)
        purity  = 100.0*I_TT/I_MC
        close(histsD+histsB+histsS,[stack])
        if I_MC < 10:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: integral of MC is %s < 10!" % I_MC, pre="  ")
            return 0.
        print ">>>    data: %.1f, MC: %.1f, TT: %.1f, QCD: %.1f, TT purity: %.3g%%)" % (I_D,I_MC,I_TT,I_QCD,purity)
        if I_D < 10:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: integral of data is %s < 10!" % I_D, pre="  ")
            return 0.
        if I_TT < 10:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: integral of TT is %s < 10!" % I_TT, pre="  ")
            return 0.
        
        # SET TT SCALE
        e_MC_noTT = sqrt(e_MC**2 - e_TT**2)
        I_MC_noTT = I_MC - I_TT
        scale     = ( I_D - I_MC + I_TT ) / (I_TT)
        err_scale = scale * sqrt( (e_D**2+e_MC_noTT**2)/abs(I_D-I_MC_noTT)**2 + (e_TT**2)/(I_TT)**2 )
        purity   *= scale
        
        if scale<0:
            LOG.warning("SampleSet::renormalizeTT: could not renormalize TT: scale = %.2f < 0!" % scale, pre="  ")
            return scale
        
        if save:
          self.TTscale[category] = scale
        TT.resetScale(scale)
        result = "%.3f +/- %.3f"%(scale,err_scale)
        print ">>>    TT renormalization scale = %s (new total scale: %.3f, TT purity: %.3g%%)" % (color(result,color='green'),TT.scale,purity)
        return scale, err_scale
    
    def measurePurityInSignalWindow(self, var, nbins, xmin0, xmax0, cuts, **kwargs):
        """Measure purity of processes in region."""
        print ">>> measurePurityInSignalWindow"
        
        filter     = kwargs.get('filter',  [ ]  )
        kwargs['signal'] = False
        
        for sample in self.samplesS:
          hist = sample.hist(var,nbins,xmin0,xmax0,cuts)
          mean = hist.GetMean()
          std  = hist.GetStdDev()
          xmin, xmax = mean-std, mean+std
          print ">>>   %s has mean %.1f with a window of [ %.1f, %.1f ]"%(sample.title,mean,xmin,xmax)
          self.measurePurity(var,nbins,xmin,xmax,cuts,**kwargs)
          #print ">>> "
    
    def measurePurity(self, *args, **kwargs):
        """Measure purity of processes in region."""
        
        verbosity = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts0 = unwrapVariableSelection(*args)
        kwargs['data'] = False 
        
        # HISTOGRAMS
        histsD, histsB, histsS = self.createHistograms(*args,**kwargs)
        
        # ORDER
        order     = [ "TT", "QCD", "DY", "WJ" ]
        index     = 0
        for name in order:
          hists = getHist(histsB,name)
          for hist in hists:
            histsB.insert(index, histsB.pop(histsB.index(hist)))
            index += 1
        
        # INTEGRALS
        integrals  = [ h.Integral() for h in histsB ]
        total      = sum(integrals)
        header     = ">>>   %8s %6s %6s"%("variable","xmin","xmax")
        row        = ">>>   %8s %6.1f %6.1f"%(var,xmin,xmax)
        
        for hist, integral in zip(histsB,integrals):
           purity  = integral/total*100.0
           name    = hist.GetName().replace("_merged","")
           if "_"+var in name: name = name[:name.index("_"+var)]
           header += " %18s"%(name)
           row    += " %10.2f (%4.1f%%)"%(integral,purity)
        
        print '>>> measuring purity for "%s" with cuts'%(var)
        print '>>>   "%s"'%(cuts0)
        print ">>> "
        print header
        print row
        print ">>> "
        
        close(histsS+histsB+histsD)
    
    def measureOSSSratio(self,*args,**kwargs):
        """Measure OS/SS ratio by substract non-QCD MC from data with opposite sign (OS) and same sign (SS)
        requirements of a lepton pair."""
        
        verbosity = getVerbosity(kwargs,verbositySampleTools)
        var, nbins, xmin, xmax, xbins, cuts = unwrapVariableSelection(*args)
        
        samples         = self.samples        
        name            = kwargs.get('name',    makeHistName("QCD",var) )
        weight          = kwargs.get('weight',  ""                      )
        relaxed         = kwargs.get('relaxed', True                    )
        
        # INVERT charge and isolation
        if relaxed:
          anti_iso = "iso_2==1 && iso_1>0.15 && iso_1<0.5" # iso_1<0.5 && 
          if 'emu' in self.channel:
            anti_iso = "iso_1<0.5 && iso_2<0.5 && iso_1>0.20" # ||iso_2>0.10
          cuts = invertIsolation(cuts,to=anti_iso)
        cutsOS = invertCharge(cuts,OS=True )
        cutsSS = invertCharge(cuts,OS=False)
        
        # HISTOGRAMS
        histsD_OS, histsMC_OS, histsS = self.createHistograms(var,nbins,xmin,xmax,cutsOS,weight=weight,append="_OS",signal=False,task="calculating QCD",QCD=False,split=False,verbosity=verbosity)
        histsD_SS, histsMC_SS, histsS = self.createHistograms(var,nbins,xmin,xmax,cutsSS,weight=weight,append="_SS",signal=False,task="calculating QCD",QCD=False,split=False,verbosity=verbosity)
        if not histsD_OS or not histsD_SS:
            print warning("No data to make DATA driven QCD!")
            return None
        #histsMC_OS = [ ]
        #histsMC_SS = [ ]
        #histsD_OS  = [ ]
        #histsD_SS  = [ ]
        #if self.loadingbar:
        #    bar = LoadingBar(len(samples),width=16,pre=">>> %s: calculating OS/SS: "%(var),counter=True,remove=True)
        #for sample in samples:
        #    if self.loadingbar: bar.count(sample.label)
        #    if sample.isPartOf('QCD'): continue
        #    name_OS = makeHistName(sample.label+"_SS", var)
        #    name_SS = makeHistName(sample.label+"_OS", var)
        #    if sample.isBackground:
        #        histOS = sample.hist(var, nbins, xmin, xmax, cutsOS, weight=weight, name=name_OS, verbosity=verbosity-1)
        #        histSS = sample.hist(var, nbins, xmin, xmax, cutsSS, weight=weight, name=name_SS, verbosity=verbosity-1)
        #        histsMC_OS.append(histOS)
        #        histsMC_SS.append(histSS)
        #    elif sample.isData:
        #        histsD_OS.append(sample.hist(var, nbins, xmin, xmax, cutsOS, name=name_OS, verbosity=verbosity-1))
        #        histsD_SS.append(sample.hist(var, nbins, xmin, xmax, cutsSS, name=name_SS, verbosity=verbosity-1))
        #    if self.loadingbar: bar.count("%s done"%sample.label)
        #if not histsD_OS or not histsD_SS:
        #    print warning("No data to make DATA driven QCD!")
        #    return None
        
        # STACK
        stack_OS = THStack("stack_OS","stack_OS")
        stack_SS = THStack("stack_SS","stack_SS")
        for hist in histsMC_OS: stack_OS.Add(hist)
        for hist in histsMC_SS: stack_SS.Add(hist)
        e_MC_OS,   e_MC_SS   = Double(), Double()
        e_data_OS, e_data_SS = Double(), Double()
        MC_OS   = stack_OS.GetStack().Last().IntegralAndError(1,nbins+1,e_MC_OS)
        MC_SS   = stack_SS.GetStack().Last().IntegralAndError(1,nbins+1,e_MC_SS)
        data_OS = histsD_OS[0].IntegralAndError(1,nbins+1,e_data_OS)
        data_SS = histsD_SS[0].IntegralAndError(1,nbins+1,e_data_SS)
        
        # CHECK
        if verbosity>1:
            print ">>>"
            print '>>>   "%s"'%(cutsOS)
            print '>>>   "%s"'%(cutsSS)
            print ">>> %8s %10s %10s"     % ("sample","OS",   "SS"   )
            print ">>> %8s %10.1f %10.1f" % ("MC",    MC_OS,  MC_SS  )
            print ">>> %8s %10.1f %10.1f" % ("data",  data_OS,data_SS)
        
        # YIELD
        OSSS     = -1
        QCD_OS   = data_OS-MC_OS
        QCD_SS   = data_SS-MC_SS
        e_QCD_OS = sqrt(e_data_OS**2+e_MC_OS**2)
        e_QCD_SS = sqrt(e_data_SS**2+e_MC_SS**2)
        if QCD_SS:
            OSSS = QCD_OS/QCD_SS
            e_OSSSS = OSSS*sqrt( (e_data_OS**2+e_MC_OS**2)/QCD_OS**2 + (e_data_SS**2+e_MC_SS**2)/QCD_SS**2)
            if verbosity > 0:
              result = color("%.3f +/-%.3f"%(OSSS,e_OSSSS),color='grey')
              print ">>>   QCD_OS/QCD_SS = ( %.1f +/-%.1f ) / ( %.1f +/-%.1f ) = %s %s" % (QCD_OS,e_QCD_OS,QCD_SS,e_QCD_SS,result,"(anti-isolated)" if relaxed else "")
        else:
            LOG.warning("measureOSSSratio: denominator QCD_SS is zero: %.1f/%.1f"% (QCD_OS,QCD_SS))
        
        close(histsMC_OS+histsMC_SS+histsD_OS+histsD_SS)
        return OSSS
        
#     def includeShiftInErrorband(self.hist0,histsDown0,histsCentral0,histsUp0,hist_staterror,**kwargs):
#         """Create asymmetric error from combining up and down shifts. Also include statistical
#            error, if present. Formula:
#               sqrt( (nominal - up shift)^2 + (nominal - down shift)^2 + statistical^2 )"""
#     
#         # CHECKS
#         histsDown       = histsDown0[:]
#         histsCentral    = histsCentral0[:]
#         histsUp         = histsUp0[:]
#         if isinstance(hist0,THStack):           hist0           = hist0.GetStack().Last()
#         if not isList(histsDown):               histsDown       = [histsDown]
#         if not isList(histsCentral):            histsCentral    = [histsCentral]
#         if not isList(histsUp):                 histsUp         = [histsUp]
#         for i, hist in enumerate(histsDown0):
#           if isinstance(hist,THStack):        histsDown[i]    = hist.GetStack().Last()
#         for i, hist in enumerate(histsCentral0):
#           if isinstance(hist,THStack):        histsCentral[i] = hist.GetStack().Last()
#         for i, hist in enumerate(histsUp0):
#           if isinstance(hist,THStack):        histsUp[i]      = hist.GetStack().Last()
#         if len(histsUp) != len(histsDown):
#           LOG.warning("makeAsymmErrorFromShifts: len(histsUp) != len(histsDown)")
#           exit(1)
#         elif len(histsCentral) != len(histsUp):
#           if len(histsCentral) == 1: histsCentral = [histsCentral]*len(histsUp)
#           else:
#              LOG.warning("makeAsymmErrorFromShifts: 1 != len(histsCentral) != len(histsUp) == len(histsDown)")
#              exit(1)
#     
#         # SETTINGS
#         verbosity       = kwargs.get('verbosity',0)
#         (N,a,b)         = (hist0.GetNbinsX(), hist0.GetXaxis().GetXmin(),hist0.GetXaxis().GetXmax())
#         errors          = TGraphAsymmErrors()
#     
#         # CHECK BINNING
#         check = histsUp+histsCentral+histsDown+[hist_staterror]
#         if hist_JERCentral: check.append(hist_JERCentral)
#         for hist in check:
#             if verbosity>0: print ">>> makeAsymmErrorFromShifts: name = %s"%(hist.GetName())
#             (N1,a1,b1) = (hist.GetNbinsX(),hist.GetXaxis().GetXmin(),hist.GetXaxis().GetXmax())
#             if N != N1 or a != a1 or b != b1 :
#                 LOG.warning("makeRatio: Binning between data (%d,%.1f,%.1f) and error (%s,%d,%.1f,%.1f) histogram is not the same!"%\
#                       (N,a,b,N1,a1,b1,hist.GetTitle()))
#     
#         # CALCULATE BINNING
#         if verbosity>0: printRow("bin","type","errDown2","errUp2","errDown_tot2","errUp_tot2","errDown_tot","errUp_tot",widths=[3,8,18,14],line="abovebelow")
#         for i in range(0,N+2):
#             biny = hist0.GetBinContent(i)
#             binx = hist0.GetXaxis().GetBinCenter(i)
#             errors.SetPoint(i,binx,biny)
#             errorUp2   = 0
#             errorDown2 = 0
#             if hist_staterror:
#                 biny1 = hist_staterror.GetBinContent(i)
#                 if biny != biny1:
#                     LOG.warning("makeAsymmErrorFromShifts: "+\
#                           "Bincontent hist0 (%.1f) and hist_staterror (%.1f) are not the same!" % (biny,biny1))
#                 errorUp2   += hist_staterror.GetBinError(i)**2
#                 errorDown2 += hist_staterror.GetBinError(i)**2
#                 if verbosity>0: printRow(i,"stat",hist_staterror.GetBinError(i),hist_staterror.GetBinError(i),errorDown2,errorUp2,widths=[3,8,18,14])
#             for histUp, histCentral, histDown in zip(histsUp,histsCentral,histsDown):
#                 binyCentral = histCentral.GetBinContent(i)
#                 errorDown   = binyCentral-histDown.GetBinContent(i)
#                 errorUp     = binyCentral-histUp.GetBinContent(i)
#                 if binyCentral and 'nom' in histCentral.GetName().lower() and\
#                                    'jes' in histUp.GetName().lower() and 'jes' in histDown.GetName().lower(): #'jpt' in histCentral.GetName()    and
#                     ratioJERToNom = hist_JERCentral.GetBinContent(i)/binyCentral
#                     if verbosity>0: print ">>>   %12s scaling JES shift: JER pt / nominal pt = %.3f"%("",ratioJERToNom)
#                     errorDown = errorDown*ratioJERToNom
#                     errorUp   = errorUp  *ratioJERToNom
#             
#                 if errorDown<0: errorUp2   += (errorDown)**2
#                 else:           errorDown2 += (errorDown)**2
#                 if errorUp<0:   errorUp2   += (errorUp)**2
#                 else:           errorDown2 += (errorUp)**2
#                 if verbosity>0: printRow("","shift",(errorDown)**2,(errorUp)**2,errorDown2,errorUp2,widths=[3,8,18,14])
#                 if verbosity>0: print ">>>   %12s %.2f=(%.4f-%.4f), %.2f=(%.4f-%.4f)" % ("",errorDown,binyCentral,histDown.GetBinContent(i),errorUp,binyCentral,histUp.GetBinContent(i))
#         
#             width = hist0.GetXaxis().GetBinWidth(i)/2
#             if verbosity>0: printRow("","total","","",errorDown2,errorUp2,sqrt(errorDown2),sqrt(errorUp2),widths=[3,8,18,14],line="below")
#             errors.SetPointError(i,width,width,sqrt(errorDown2),sqrt(errorUp2))
#     
#         setErrorBandStyle(errors)
#         errors.SetFillStyle(3004)
#         errors.SetLineColor(hist0.GetLineColor())
#         errors.SetFillColor(hist0.GetLineColor())
#         errors.SetLineWidth(hist0.GetLineWidth())
#         # Draw('2 SAME')
#     
#         return errors
        
    def significanceScan(self,*args,**kwargs):
        """Scan cut on a range of some variable, integrating the signal and background histograms,
           calculating the S/(1+sqrt(B)) and finally drawing a histogram with these values."""
    
    def measureSFFromVar(self,var,nbins,a,b,**kwargs):
        """Method to create a SF for a given var, s.t. the data and MC agree."""
    
    def resetScales(self,*searchterms,**kwargs):
        """Reset scale of sample."""
        scale = kwargs.get('scale',1)
        samples = self.get(*searchterms,**kwargs)
        if isList(samples):
          for sample in samples:
            sample.resetScale(scale=scale)
        elif isinstance(samples,Sample):
          samples.resetScale(scale=scale)
        else:
          LOG.ERROR("SampleSet::resetScales: Found sample is not a list or Sample or list object!")
        return samples
    
    def has(self,*searchterms,**kwargs):
        """Return true if sample set contains a sample corresponding to given searchterms."""
        kwargs.set_default('nowarning',True)
        results = self.get(*searchterms,**kwargs)
        found = isinstance(results,Sample) or len(results)!=0
        return found
    
    def remove(self,*searchterms,**kwargs):
        samples = self.get(*searchterms,**kwargs)
        for sample in samples:
          self.samples.remove(sample)
    
    def get(self,*searchterms,**kwargs):
        return getSample(self.samples,*searchterms,**kwargs)
    
    def getSignal(self,*searchterms,**kwargs):
        return getSignal(self.samplesS,*searchterms,**kwargs)
    
    def getBackground(self,*searchterms,**kwargs):
        return getBackground(self.samplesB,*searchterms,**kwargs)
    
    def getMC(self,*searchterms,**kwargs):
        return getMC(self.samplesMC,*searchterms,**kwargs)
    
    def getData(self,*searchterms,**kwargs):
        return getData(self.samplesD,*searchterms,**kwargs)
    
    def merge(self,*searchterms,**kwargs):
        self.samplesMC = merge(self.samplesMC,*searchterms,**kwargs)
    
    def stitch(self,*searchterms,**kwargs):
        self.samplesMC = stitch(self.samplesMC,*searchterms,**kwargs)
    
    def replaceMergedSamples(self,mergedsample):
        """Help function to replace merged samples with their MergedSample object in the same position."""
        index0 = len(self.samples)
        for sample in mergedsample:
            index = self.samples.index(sample)
            if index<index0: index0 = index
            self.samples.remove(sample)
        self.samples.insert(index0,mergedsample)
    
    def split(self,*args,**kwargs):
        """Split sample for some dictionairy of cuts."""
        searchterms      = [ arg for arg in args if isinstance(arg,str)  ]
        splitlist        = [ arg for arg in args if isList(arg)          ][0]
        kwargs['unique'] = True
        sample           = self.get(*searchterms,**kwargs)
        if sample:
          sample.split(splitlist,**kwargs)
        else:
          LOG.warning('SampleSet::splitSample - Could not find sample with searchterms "%s"'%('", "').join(searchterms))
          
    def shift(self,searchterms,file_app,title_app,**kwargs):
        """Shift samples in samples set by creating new samples with new filename/titlename."""
        filter          = kwargs.get('filter',      False       ) # filter other samples
        share           = kwargs.get('share',       False       ) # share other samples (as opposed to cloning them)
        title_tag       = kwargs.get('title_tag',   False       )
        title_veto      = kwargs.get('title_veto',  False       )
        close           = kwargs.get('close',       False       )
        kwargs.setdefault('name',      file_app.lstrip('_')     )
        kwargs.setdefault('label',     file_app                 )
        kwargs.setdefault('isNanoAOD', self.isNanoAOD           )
        
        searchterms     = ensureList(searchterms)
        all             = searchterms==['*']
        samplesD        = { }
        samplesB        = [ ]
        samplesS        = [ ]
        sharedsamples   = [ ]
        for sample in self.samplesB:
          if all or sample.isPartOf(*searchterms,exclusive=False):
            newsample = sample.clone(samename=True,deep=True)
            newsample.appendFileName(file_app,title_app=title_app,title_veto=title_veto)
            if close: newsample.close()
            samplesB.append(newsample)
          elif not filter:
            newsample = sample if share else sample.clone(samename=True,deep=True,close=True)
            samplesB.append(newsample)
            if share: sharedsamples.append(newsample)
        for sample in self.samplesS:
          if all or sample.isPartOf(*searchterms,exclusive=False):
            newsample = sample.clone(samename=True,deep=True)
            newsample.appendFileName(file_app,title_app=title_app,title_veto=title_veto)
            if close: newsample.close()
            samplesS.append(newsample)
          elif not filter:
            newsample = sample if share else sample.clone(samename=True,deep=True,close=True)
            samplesS.append(newsample)
            if share: sharedsamples.append(newsample)
        if not filter:
            samplesD = self._samplesD
            sharedsamples.append(samplesD)
        
        kwargs['shared'] = sharedsamples
        newset = SampleSet(samplesD,samplesB,samplesS,**kwargs)
        newset.closed = close
        return newset
          
    def shiftWeight(self,searchterms,newweight,title_app,**kwargs):
        """Shift samples in samples set by creating new samples with new weight."""
        filter          = kwargs.get('filter',      False       ) # filter other samples
        share           = kwargs.get('share',       False       ) # share other samples (as opposed to cloning them)
        extra           = kwargs.get('extra',       True        ) # replace extra weight
        kwargs.setdefault('isNanoAOD', self.isNanoAOD           )
        
        if not isList(searchterms): searchterms = [ searchterms ]
        samplesD        = { }
        samplesB        = [ ]
        samplesS        = [ ]
        for sample in self.samplesB:
          if sample.isPartOf(*searchterms,exclusive=False):
            newsample = sample.clone(samename=True,deep=True)
            #LOG.verbose('SampleSet::shiftWeight: "%s" - weight "%s", extra weight "%s"'%(newsample.name,newsample.weight,newsample.extraweight),1)
            if extra:
              newsample.setExtraWeight(newweight)
            else:
              newsample.addWeight(newweight)
            #LOG.verbose('SampleSet::shiftWeight: "%s" - weight "%s", extra weight "%s"'%(newsample.name,newsample.weight,newsample.extraweight),1)
            samplesB.append(newsample)
          elif not filter:
            newsample = sample if share else sample.clone(samename=True,deep=True)
            samplesB.append(newsample)
        for sample in self.samplesS:
          if sample.isPartOf(*searchterms,exclusive=False):
            newsample = sample.clone(samename=True,deep=True)
            if extra:
              newsample.setExtraWeight(newweight)
            else:
              newsample.addWeight(newweight)
            samplesS.append(newsample)
          elif not filter:
            newsample = sample if share else sample.clone(samename=True,deep=True)
            samplesS.append(newsample)
        if not filter:
            samplesD = self._samplesD
        
        return SampleSet(samplesD,samplesB,samplesS,**kwargs)
        


    #############
    # getSample #
    #############

def getSample(samples,*searchterms,**kwargs):
    """Help function to get all samples corresponding to some name and optional label."""
    verbosity   = getVerbosity(kwargs,verbositySampleTools)
    filename    = kwargs.get('filename',        ""          )
    unique      = kwargs.get('unique',          False       )
    nowarning   = kwargs.get('nowarning',       False       )
    matches     = [ ]
    for sample in samples:
        if sample.isPartOf(*searchterms) and filename in sample.filename:
            matches.append(sample)
    if not matches and not nowarning:
        LOG.warning("getSample - Could not find a sample with search terms %s..." % (', '.join(searchterms+(filename,))))
    elif unique:
        if len(matches)>1: LOG.warning("getSample - Found more than one match to %s. Using first match only: %s" % (", ".join(searchterms),", ".join([s.name for s in matches])))
        return matches[0]
    return matches

def getData(samples,**kwargs):
    return getSampleWithAttribute(samples,'isData',**kwargs)

def getBackground(samples,**kwargs):
    """Help function to get background from a list of samples."""
    return getSampleWithAttribute(samples,'isBackground',**kwargs)

def getSignal(samples,**kwargs):
    """Help function to get signal from a list of samples."""
    return getSampleWithAttribute(samples,'isSignal',**kwargs)

def getSampleWithAttribute(samples,attribute,**kwargs):
    """Help function to get sample with some attribute from a list of samples."""
    matches = [ ]
    unique  = kwargs.get('unique',False)
    for sample in samples:
        if hasattr(sample,attribute): matches.append(sample)
    if not matches:
        LOG.warning("Could not find a signal sample...")
    elif unique:
        if len(matches)>1: LOG.warning("Found more than one signal sample. Using first match only: %s" % (", ".join([s.name for s in matches])))
        return matches[0]
    return matches
    




    ###########
    # Merging #
    ###########

def merge(sampleList,*searchterms,**kwargs):
    """Merge samples from a sample list, that match a set of search terms."""
    
    verbosity = getVerbosity(kwargs,verbositySampleTools,1)
    name0     = kwargs.get('name',  searchterms[0] )
    title0    = kwargs.get('title', name0          )
    color0    = kwargs.get('color', None           )
    LOG.verbose("",verbosity,level=2)
    LOG.verbose(" merging %s"%(name0),verbosity,level=1)
    
    # GET samples containing names and searchterm
    mergeList = [ s for s in sampleList if s.isPartOf(*searchterms,exclusive=False) ]
    if len(mergeList) < 2:
        LOG.warning('Could not merge "%s": less than two "%s" samples (%d)'%(name0,name0,len(mergeList)))
        return sampleList
    fill = max([ len(s.name) for s in mergeList ])+2 # number of spaces
    
    # ADD samples with name0 and searchterm
    mergedsample = MergedSample(name0,title0,color=color0)
    for sample in mergeList:
        samplename = ('"%s"'%(sample.name)).ljust(fill)
        LOG.verbose("   merging %s to %s: %s"%(samplename,name0,sample.filenameshort),verbosity,level=2)
        mergedsample.add(sample)
    
    # REMOVE replace merged samples from sampleList, preserving the order
    if mergedsample.samples and sampleList:
      if isinstance(sampleList,SampleSet):
        sampleList.replaceMergedSamples(mergedsample)
      else:
        index0 = len(sampleList)
        for sample in mergedsample.samples:
            index = sampleList.index(sample)
            if index<index0: index0 = index
            sampleList.remove(sample)
        sampleList.insert(index,mergedsample)
    return sampleList
    



    #############
    # Stitching #
    #############

def stitch(sampleList,*searchterms,**kwargs):
    """Stitching samples: merge samples and reweight inclusive sample and rescale jet-binned
    samples."""
    
    verbosity         = getVerbosity(kwargs,verbositySampleTools,1)
    name0             = kwargs.get('name',      searchterms[0]  )
    title0            = kwargs.get('title',     ""              )
    name_incl         = kwargs.get('name_incl', name0           )
    LOG.verbose("",verbosity,level=2)
    LOG.verbose(" stiching %s: rescale, reweight and merge samples" % (name0),verbosity,level=1)
    
    # CHECK if sample list of contains to-be-stitched-sample
    stitchList = sampleList.samples if isinstance(sampleList,SampleSet) else sampleList
    stitchList = [ s for s in stitchList if s.isPartOf(*searchterms) ]
    if len(stitchList) < 2:
        LOG.warning("stitch: Could not stitch %s: less than two %s samples (%d)" % (name0,name0,len(stitchList)))
        for s in stitchList: print ">>>   %s" % s.name
        if len(stitchList)==0: return sampleList
    fill       = max([ len(s.name) for s in stitchList ])+2
    name       = kwargs.get('name',stitchList[0].name)
    
    # FIND inclusive sample
    sample_incls = [s for s in stitchList if s.isPartOf(name_incl)]
    if len(sample_incls)==0: LOG.error('stitch: Could not find inclusive sample "%s"!'%(name0))
    if len(sample_incls) >1: LOG.error('stitch: Found more than one inclusive sample "%s"!'%(name0))
    sample_incl = sample_incls[0]
    
    # k-factor
    N_incl            = sample_incl.N
    weights           = [ ]
    sigma_incl_LO     = sample_incl.sigma
    sigma_incl_NLO    = crossSectionsNLO(name0,*searchterms)
    kfactor           = sigma_incl_NLO / sigma_incl_LO
    norm0             = -1
    maxNUP            = -1
    LOG.verbose("   %s k-factor = %.2f = %.2f / %.2f" % (name0,kfactor,sigma_incl_NLO,sigma_incl_LO),verbosity,level=2)
    
    # SET renormalization scales with effective luminosity
    # assume first sample in the list s the inclusive sample
    for sample in stitchList:
        
        N_tot = sample.N
        N_eff = N_tot
        sigma = sample.sigma # inclusive or jet-binned cross section
        
        if sample.isPartOf(name_incl):
          NUP = 0
        else:
          N_eff = N_tot + N_incl*sigma/sigma_incl_LO # effective luminosity    
          matches = re.findall("(\d+)Jets",sample.filenameshort)
          LOG.verbose('   %s: N_eff = N_tot + N_incl * sigma / sigma_incl_LO = %.1f + %.1f * %.2f / %.2f = %.2f'%\
                         (sample.name,N_tot,N_incl,sigma,sigma_incl_LO,N_eff),verbosity,4)
          if len(matches)==0: LOG.error('stitch: Could not stitch "%s": could not find right NUP for "%s"!'%(name0,sample.name))
          if len(matches)>1:  LOG.warning('stitch: More than one "\\d+Jets" match for "%s"! matches = %s'%(sample.name,matches))
          NUP = int(matches[0])
        
        norm = luminosity * kfactor * sigma * 1000 / N_eff
        if NUP==0:     norm0 = norm
        if NUP>maxNUP: maxNUP = NUP
        weights.append("(NUP==%i ? %s : 1)"%(NUP,norm))
        LOG.verbose('   %s, NUP==%d: norm = luminosity * kfactor * sigma * 1000 / N_eff = %.2f * %.2f * %.2f * 1000 / %.2f = %.2f'%\
                        (name0,NUP,luminosity,kfactor,sigma,N_eff,norm),verbosity,4)
        LOG.verbose("   stitching %s with normalization %7.3f and cross section %8.2f pb"%(sample.name.ljust(fill), norm, sigma),verbosity,2)
        #print ">>> weight.append(%s)" % weights[-1]
        
        sample.norm = norm # apply lumi-cross section normalization
        if len(stitchList)==1: return sampleList
    
    # ADD weights for NUP > maxNUP
    if norm0>0 and maxNUP>0:
      weights.append("(NUP>%i ? %s : 1)"%(maxNUP,norm0))
    else:
      LOG.warning("   found no weight for NUP==0 (%.1f) or no maximum NUP (%d)..."%(norm0,maxNUP))
    
    # SET weight of inclusive sample
    sample_incl.norm = 1.0 # apply lumi-cross section normalization via weights
    stitchweights    = '*'.join(weights)
    if sample_incl.isNanoAOD:
      stitchweights  = stitchweights.replace('NUP','LHE_Njets')
    LOG.verbose("   stitch weights = %s"%(stitchweights),verbosity,4)
    sample_incl.addWeight(stitchweights)
    if not title0: title0 = sample_incl.title
    
    # MERGE
    merge(sampleList,name0,*searchterms,title=title0,verbosity=verbosity)
    return sampleList


def crossSectionsNLO(*searchterms,**kwargs):
    """Returns inclusive (N)NLO cross section for stitching og DY and WJ."""
    # see /shome/ytakahas/work/TauTau/SFrameAnalysis/TauTauResonances/plot/config.py
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV#List_of_processes
    # https://ineuteli.web.cern.ch/ineuteli/crosssections/2017/FEWZ/
    # DY cross sections  5765.4 [  4954.0, 1012.5,  332.8, 101.8,  54.8 ]
    # WJ cross sections 61526.7 [ 50380.0, 9644.5, 3144.5, 954.8, 485.6 ]
    
    isDY          = False
    isDY_M10to50  = ""
    isDY_M50      = ""
    isWJ          = False
    
    sigmasNLO     = { 'DY': { 'M-50':      5765.4,
                              'M-10to50': 21658.0 }, # WRONG !!! 18610.0 is already NLO
                      'WJ':               61526.7 }
    
    for searchterm in searchterms:
        searchterm = searchterm.replace('*','')
        if "DY" in searchterm:
            isDY = True
        if "10to50" in searchterm:
            isDY_M10to50 = "M-10to50"
        if "50" in searchterm and not "10" in searchterm:
            isDY_M50 = "M-50"
        if "WJ" in searchterm:
            isWJ = True
        
    if isDY_M50 and "2017" in globalTag:
      LOG.warning("crossSectionsNLO: changing NNLO cross section for DY")
      sigmasNLO['DY']['M-50'] = 3*2077.85
      sigmasNLO['DY']['M-10to50'] = 18610.0 #(3*2065.75/5343.0)*25296
    
    if isDY and isWJ:
        LOG.error("crossSections - Detected both isDY and isWJ!")
        exit(1)
    elif isWJ:
        return sigmasNLO['WJ']
    elif isDY:
        if isDY_M10to50 and isDY_M50:
            LOG.error('crossSections - Matched to both "M-10to50" and "M-50"!')
            exit(1)
        if not (isDY_M10to50 or isDY_M50):
            LOG.error('crossSections - Did not match to either "M-10to50" or "M-50" for DY!')
            exit(1)
        return sigmasNLO['DY'][isDY_M10to50+isDY_M50]
    else:
        LOG.error("crossSections - Did not find a DY or WJ match!")
        exit(1)


import PlotTools
from PlotTools      import *
from SelectionTools import *
from VariableTools  import *
from PrintTools     import *
