#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (2017)
# SettingsTools.py - Script containing the global variables as settings for all modules

import os, re
from PrintTools import *
from ROOT import TFile

# PATHS
globalTag  = ""
SAMPLE_DIR = os.path.expandvars("/scratch/ineuteli/SFrameAnalysis/AnalysisOutput/")

# PLOT OPTIONS
era                     = ""
year                    = 0
luminosity              = 0 # set in plot.py
OSSS_ratio              = 0.5
useCutTree              = True #and False
colorset                = 'HTT'
loadMacros              = False

# VERBOSITY
LOG                     = Logger("global")
verbositySampleTools    = 2
verbosityPlotTools      = 1
verbosityVariableTools  = 1
verbositySelectionTools = 1
verbosityWJ             = 1
blind_dict              = { }
doFakeRate              = False
doFakeFactor            = False
doQCD                   = False
# ROOT.gROOT.SetBatch(ROOT.kTRUE)
# gErrorIgnoreLevel = kInfo;


def isNumber(arg):
  return isinstance(arg,float) or isinstance(arg,int)
  
def isList(arg):
  return isinstance(arg,list) or isinstance(arg,tuple)
  
def ensureList(arg):
  return arg if (isinstance(arg,list) or isinstance(arg,tuple)) else [arg]
  
def ensureTFile(filename,option='READ',**kwargs):
  pre  = kwargs.get('pre',  ""   )
  stop = kwargs.get('exit', True )
  if not os.path.isfile(filename):
    LOG.fatal('File in path "%s" does not exist'%(filename),pre=pre)
  file = TFile(filename,option)
  if not file or file.IsZombie():
    if stop:
      LOG.fatal('Could not open file by name "%s"'%(filename),pre=pre)
    else:
      LOG.warning('Could not open file by name "%s"'%(filename),pre=pre)
  return file
  
def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
      os.makedirs(dirname)
      print '>>> made directory "%s"'%(dirname)
      if not os.path.exists(dirname):
        print '>>> failed to make directory "%s"'%(dirname)
    return dirname

def getKey(kwargs,key,default=None):
  """Get the key from a dictionary, return default if the value is None."""
  value = kwarg.get(key,default)
  if value==None:
    return default
  return value


def setVerbose(*args,**kwargs):
    """Set verbosity level of each module."""
    verbose = args[0] if args else True
    if verbose:
        verbositySampleTools    = 2
        verbosityPlotTools      = 2
        verbosityVariableTools  = 2
        verbositySelectionTools = 2
        verbosityWJ             = 2
    
def getVerbosity(*args):
    """Set verbosity level of each module."""
    verbosities = [ ]
    for arg in args:
      if isinstance(arg,dict):
        verbosities.append(arg.get('verbosity',False))
      else:
        verbosities.append(arg)
    return max(verbosities)
    


def loadConfigurationFromFile(configFileName,**kwargs):
    """
    Load configuration file.
    Returns one string containing settings (global variable definitions)
    and one string containging other commands for setup.
    """
    # print ">>> loading configuration file %s"%(configFileName)
    # exec(open(configFileName).read(), globals())
    configurationSettings = ""
    configurationCommands = "from PlotTools.SampleTools    import *\n"+\
                            "from PlotTools.SelectionTools import *\n"+\
                            "from PlotTools.VariableTools  import *\n"+\
                            "#from PlotTools.PlotTools      import *\n"+\
                            "from PlotTools.PrintTools     import *\n"
    with open(configFileName, 'r') as configFile:
        for line in configFile:
            if re.search(r"#\ *END SETTINGS\ *#",line): break
            if '#' in line[0]: continue
            configurationSettings += line
        for line in configFile:
            if '#' in line[0]: continue
            configurationCommands += line
    return configurationSettings, configurationCommands
    


def loadSettings(globalsDict,*args,**kwargs):
    """Load settings as global variables from a given dictionary."""
    #print ">>> loadSettings"
    verbose = kwargs.get('verbose', None )
    pattern = ""
    if args: pattern = args[0]
    for variable, value in globalsDict.items():
        if variable.count('__')>1: continue
        if hasattr(value,'__call__'): continue
        if hasattr(value,'read') and hasattr(value,'write'): continue
        if pattern and variable not in pattern: continue
        if verbose and "verbosity" in variable:
          value = 2; globalsDict[variable] = value
        globals()[variable] = value
        #print ">>>   %-15s = %s"%(variable,globals()[variable])
    


def printSettings():
    """Print all global variables set in SettingsTools.py"""
    print ">>>\n>>> SettingsTool: global variables:"
    for variable, value in globals().items():
        if variable.count('__')>1: continue
        print ">>>   %-16s =   %s"%(variable,value)
    print ">>>"
    


