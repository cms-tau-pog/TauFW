'''
\package dataset
Dataset utilities and classes

This package contains classes and utilities for dataset management.
There are also some functions and classes not directly related to
dataset management, but are placed here due to some dependencies.
'''
# Author: Konstantinos Christoforou (Feb 2022)

#================================================================================================
# Import modules
#================================================================================================
import glob, os, sys, re
import math
import copy
import time
import StringIO
import hashlib
import array
import socket
from collections import OrderedDict

import ROOT
#import HiggsAnalysis.NtupleAnalysis.tools.multicrab as multicrab
#import HiggsAnalysis.NtupleAnalysis.tools.histogramsExtras as histogramsExtras
#import HiggsAnalysis.NtupleAnalysis.tools.aux as aux
#import HiggsAnalysis.NtupleAnalysis.tools.pileupReweightedAllEvents as pileupReweightedAllEvents
#import HiggsAnalysis.NtupleAnalysis.tools.crosssection as crosssection
import ShellStyles as ShellStyles

from sys import platform as _platform

#================================================================================================
# Shell Types
#================================================================================================
sh_e = ShellStyles.ErrorStyle()
sh_s = ShellStyles.SuccessStyle()
sh_h = ShellStyles.HighlightStyle()
sh_a = ShellStyles.HighlightAltStyle()
sh_t = ShellStyles.NoteStyle()
sh_n = ShellStyles.NormalStyle()
sh_w = ShellStyles.WarningStyle()


#================================================================================================
# Global Definitions
#================================================================================================
DEBUG = False
_debugNAllEvents = False
_debugCounters = False

# era name -> list of era parts in data dataset names
_dataEras = {
    "Run2015C": ["_Run2015C"],
    "Run2015D": ["_Run2015D"],
    "Run2015CD": ["_Run2015C", "_Run2015D"],
    "Run2015": ["_Run2015C", "_Run2015D"],
    "Run2016BCD": ["_Run2016B", "_Run2016C", "_Run2016D"],
    "Run2016D": ["_Run2016D"],
    "Run2016E": ["_Run2016E"],
    "Run2016F": ["_Run2016F"],
    "Run2016": ["_Run2016B", "_Run2016C", "_Run2016D","_Run2016E","_Run2016F", "_Run2016G", "_Run2016H"],
    "Run2016ULAPV": ["_Run2016B", "_Run2016C", "_Run2016D","_Run2016E","_Run2016F"],
    "Run2016UL": ["_Run2016F", "_Run2016G", "_Run2016H"],
    "Run2017": ["_Run2017B", "_Run2017C", "_Run2017D","_Run2017E","_Run2017F"],
    "Run2017UL": ["_Run2017B", "_Run2017C", "_Run2017D","_Run2017E","_Run2017F"],
    "Run2018": ["_Run2018A", "_Run2018B", "_Run2018C","_Run2018D"],
    "Run2018UL": ["_Run2018A", "_Run2018B", "_Run2018C","_Run2018D"]
}


#================================================================================================
# Function Definition
#================================================================================================
def Verbose(msg, printHeader=False):
    '''
    Calls Print() only if verbose options is set to true.                                                                                                                     
    '''
    if not DEBUG:
        return
    Print(msg, printHeader)
    return


def Print(msg, printHeader=True):
    '''
    Simple print function. If verbose option is enabled prints, otherwise does nothing.
    '''
    fName = __file__.split("/")[-1]
    if printHeader==True:
        print "=== ", fName
        print "\t", msg
    else:
        print "\t", msg
    return


def PrintFlushed(msg, printHeader=True):
    '''
    Useful when printing progress in a loop
    '''
    msg = "\r\t" + msg
    ERASE_LINE = '\x1b[2K'
    if printHeader:
        print "=== " + GetSelfName()
    sys.stdout.write(ERASE_LINE)
    sys.stdout.write(msg)
    sys.stdout.flush()
    return

def GetSelfName():
    return __file__.split("/")[-1].replace(".pyc", ".py")


def getDatasetsFromMulticrabDirs(multiDirs, **kwargs):
    '''
    Construct DatasetManager from a list of MultiCRAB directory names.
    
    \param multiDirs:  List of strings or pairs of strings of the MultiCRAB
    directories (relative to the working directory). If the item of the list
    is pair of strings, the first element is the directory, and the second 
    element is the postfix for the dataset names from that directory.

    \param kwargs: Keyword arguments (forwarded to getDatasetsFromMulticrabCfg())
    
    \return DatasetManager object
    '''
    Verbose("getDatasetsFromMulticrabDirs()", True)
    
    if "cfgfile" in kwargs:
        raise Exception("'cfgfile' keyword argument not allowed")
    if "namePostfix" in kwargs:
        raise Exception("'namePostfix' keyword argument not allowed")

    datasets = DatasetManager()
    # For-loop: All multicrab directories
    for d in multiDirs:
        if isinstance(d, str):
            dset = getDatasetsFromMulticrabCfg(directory=d, **kwargs)
        else:
            dset = getDatasetsFromMulticrabCfg(directory=d[0], namePostfix=d[1], **kwargs)
        datasets.extend(dset)

    return datasets


def getDatasetsFromMulticrabCfg(**kwargs):
    '''
    Construct DatasetManager from a multicrab.cfg.
    
    \param kwargs: Keyword arguments (see below) 
    
    All keyword arguments are forwarded to readFromMulticrabCfg.
    
    All keyword arguments <b>except</b> the ones below are forwarded to
    DatasetManagerCreator.createDatasetManager()
    \li \a directory
    \li \a cfgfile
    \li \a excludeTasks
    \li \a includeOnlyTasks
    \li \a namePostfix
    \return DatasetManager object

    \see dataset.readFromMulticrabCfg 
    '''
    Verbose("getDatasetsFromMulticrabCfg()", True)

    _args = copy.copy(kwargs)
    for argName in ["directory", "cfgfile", "excludeTasks", "includeOnlyTasks", "namePostfix"]:
        try:
            del _args[argName]
        except KeyError:
            pass

    managerCreator = readFromMulticrabCfg(**kwargs)
    return managerCreator.createDatasetManager(**_args)


def readFromMulticrabCfg(**kwargs):
    '''
    Construct DatasetManagerConstructor from a multicrab.cfg.

    \param kwargs:   Keyword arguments (see below) 
    
    <b>Keyword arguments</b>
    \li \a opts              Optional OptionParser object. Should have options added with addOptions() and multicrab.addOptions().
    
    \li \a directory         Directory where to look for \a cfgfile.
    
    \li \a cfgfile           Path to the multicrab.cfg file (for default, see multicrab.getTaskDirectories())
    
    \li \a excludeTasks      String, or list of strings, to specify regexps. If a dataset name matches to any of the 
    regexps, Dataset object is not constructed for that. Conflicts with \a includeOnlyTasks

    \li \a includeOnlyTasks  String, or list of strings, to specify regexps. Only datasets whose name matches
    to any of the regexps are kept. Conflicts with \a excludeTasks.

    \li Rest are forwarded to readFromCrabDirs()
    
    \return DatasetManagerCreator object
 
    The section names in multicrab.cfg are taken as the dataset names
    in the DatasetManager object.
    '''
    Verbose("readFromMulticrabCfg()", True)

    opts     = kwargs.get("opts", None)
    taskDirs = []
    dirname  = ""
    if "directory" in kwargs or "cfgfile" in kwargs:
        _args = {}
        if "directory" in kwargs:
            dirname = kwargs["directory"]
            _args["directory"] = dirname
        if "cfgfile" in kwargs:
            _args["filename"] = kwargs["cfgfile"]
            dirname = os.path.dirname(os.path.join(dirname, kwargs["cfgfile"]))
        taskDirs = multicrab.getTaskDirectories(opts, **_args)
    else:
        taskDirs = multicrab.getTaskDirectories(opts)

    Verbose("Found the following task directories:\n\t%s" % ("\n\t".join(taskDirs) ) )
    taskDirs = aux.includeExcludeTasks(taskDirs, **kwargs)
    taskDirs.sort()
    managerCreator = readFromCrabDirs(taskDirs, baseDirectory=dirname, **kwargs)
    return managerCreator


def getDatasetsFromCrabDirs(taskdirs, **kwargs):
    '''
    Construct DatasetManager from a list of CRAB task directory names.
 
    \param taskdirs     List of strings for the CRAB task directories (relative
    to the working directory), forwarded to readFromCrabDirs()

    \param kwargs       Keyword arguments (see below)

    All keyword arguments are forwarded to readFromCrabDirs().
    
    All keyword arguments <b>except</b> the ones below are forwarded to
    DatasetManagerCreator.createDatasetManager()
    
    \li \a namePostfix

    \see readFromCrabDirs()
    '''
    Verbose("getDatasetsFromCrabDirs()", True)

    _args = copy.copy(kwargs)
    for argName in ["namePostfix"]:
        try:
            del _args[argName]
        except KeyError:
            pass
    
    managerCreator = readFromCrabDirs(taskdirs, **kwargs)
    return managerCreator.createDatasetManager(**_args)


def readFromCrabDirs(taskdirs, emptyDatasetsAsNone=False, **kwargs):
    '''
    Construct DatasetManagerCreator from a list of CRAB task directory names.
 
    \param taskdirs     List of strings for the CRAB task directories (relative
    to the working directory)

    \param emptyDatasetsAsNone  If true, in case of no datasets return None instead 
    of raising an Exception (default False)

    \param kwargs       Keyword arguments (see below) 
 
    <b>Keyword arguments</b>, all are also forwarded to readFromRootFiles()

    \li \a opts         Optional OptionParser object. Should have options added with addOptions().

    \li \a namePostfix  Postfix for the dataset names (default: '')

    \return DatasetManagerCreator object
 
    The basename of the task directories are taken as the dataset names
    in the DatasetManagerCreator object (e.g. for directory '../Foo',
    'Foo' will be the dataset name)
    '''
    Verbose("readFromCrabDirs()", True)

    inputFile = None
    if "opts" in kwargs:
        opts = kwargs["opts"]
        inputFile = opts.input
    else:
        inputFile = _optionDefaults["input"]
    postfix = kwargs.get("namePostfix", "")

    dlist = []
    noFiles = False
    for d in taskdirs:
        # crab2
        resdir = os.path.join(d, "res")
        name = os.path.basename(d)
        if os.path.exists(resdir):
            files = glob.glob(os.path.join(resdir, inputFile))
        else:
            # crab3
            files = glob.glob(os.path.join(d, "results", inputFile))        
            name = name.replace("crab_", "")
        if len(files) == 0:
            print >> sys.stderr, "Ignoring dataset %s: no files matched to '%s' in task directory %s" % (d, inputFile, os.path.join(d, "res"))
            noFiles = True
            continue
        
        # If the files are symbolic links store the target path. Otherwise leave unchanged
        files = ConvertSymLinks(files)
        dlist.append( (name+postfix, files) )

    if noFiles:
        print >> sys.stderr, ""
        print >> sys.stderr, "  There were datasets without files. Have you merged the files with hplusMergeHistograms.py?"
        print >> sys.stderr, ""
        if len(dlist) == 0:
            raise Exception("No datasets. Have you merged the files with hplusMergeHistograms.py?")

    if len(dlist) == 0:
        if emptyDatasetsAsNone:
            return None
        raise Exception("No datasets from CRAB task directories %s" % ", ".join(taskdirs))
    return readFromRootFiles(dlist, **kwargs)


def ConvertSymLinks(fileList):
    '''
    '''
    Verbose("ConvertSymLinks()", True)
    HOST = socket.gethostname()
    bUseSymLinks = False

    if "fnal" in HOST:
        prefix = "root://cmseos.fnal.gov//"
    elif "lxplus" in HOST:
        prefix = "root://eoscms.cern.ch/"
    else:
        prefix = ""

    # If the file is symbolic link store the target path
    for i, f in enumerate(fileList):
        if not os.path.islink(f):
            continue
        bUseSymLinks = True
        fileList[i] = prefix + os.path.realpath(f)

    if bUseSymLinks:
        Verbose("SymLinks detected. Appended the prefix \"%s\" to all ROOT file paths" % (prefix) )
    return fileList


def getDatasetsFromRootFiles(rootFileList, **kwargs):
    '''
    Construct DatasetManager from a list of CRAB task directory names.
    
    \param rootFileList  List of (\a name, \a filenames) pairs (\a name should be string, 
    \a filenames can be string or  list of strings). \a name is taken as the  dataset name,
    and \a filenames as the path(s)  to the ROOT file(s).
    
    \param kwargs        Keyword arguments, forwarded to readFromRootFiles() and dataset.Dataset.__init__()

    \return DatasetManager object
    '''
    Verbose("getDatasetsFromRootFiles()", True)

    managerCreator = readFromRootFiles(rootFileList, **kwargs)
    return managerCreator.createDatasetManager(**kwargs)


def readFromRootFiles(rootFileList, **kwargs):
    '''
    Construct DatasetManagerCreator from a list of CRAB task directory names.
 
    \param rootFileList  List of (\a name, \a filenames) pairs (\a name
    should be string, \a filenames can be string or list of strings). \a name is taken as the
    dataset name, and \a filenames as the path(s) to the ROOT file(s). 
    Forwarded to DatasetManagerCreator.__init__()
    
    \param kwargs        Keyword arguments (see below), all forwarded to DatasetManagerCreator.__init__()
    
    <b>Keyword arguments</b>
    \li \a opts          Optional OptionParser object. Should have options added with addOptions().

    \return DatasetManagerCreator object

    If \a opts exists, and the \a opts.listAnalyses is set to True, list
    all available analyses (with DatasetManagerCreator.printAnalyses()),
    and exit.
    '''
    Verbose("readFromRootFiles()", True)
    
    creator = DatasetManagerCreator(rootFileList, **kwargs)
    if "opts" in kwargs and kwargs["opts"].listAnalyses:
        creator.printAnalyses()
        sys.exit(0)
    return creator
        

## Default command line options
_optionDefaults = {
    "input": "histograms-*.root",
}

## Add common dataset options to OptionParser object.
#
# \param parser   OptionParser object
def addOptions(parser, analysisName=None, searchMode=None, dataEra=None, optimizationMode=None, systematicVariation=None):
    parser.add_option("-i", dest="input", type="string", default=_optionDefaults["input"],
                      help="Pattern for input root files (note: remember to escape * and ? !) (default: '%s')" % _optionDefaults["input"])
    parser.add_option("-f", dest="files", type="string", action="append", default=[],
                      help="Give input ROOT files explicitly, if these are given, multicrab.cfg is not read and -d/-i parameters are ignored")
    parser.add_option("--analysisName", dest="analysisName", type="string", default=analysisName,
                      help="Override default analysisName (%s, plot script specific)" % analysisName)
    parser.add_option("--searchMode", dest="searchMode", type="string", default=searchMode,
                      help="Override default searchMode (%s, plot script specific)" % searchMode)
    parser.add_option("--dataEra", dest="dataEra", type="string", default=dataEra,
                      help="Override default dataEra (%s, plot script specific)" % dataEra)
    parser.add_option("--optimizationMode", dest="optimizationMode", type="string", default=optimizationMode,
                      help="Override default optimizationMode (%s, plot script specific)" % optimizationMode)
    parser.add_option("--systematicVariation", dest="systematicVariation", type="string", default=systematicVariation,
                      help="Override default systematicVariation (%s, plot script specific)" % systematicVariation)
    parser.add_option("--list", dest="listAnalyses", action="store_true", default=False,
                      help="List available analysis name information, and quit.")
    parser.add_option("--counterDir", "-c", dest="counterDir", type="string", default=None,
                      help="TDirectory name containing the counters, relative to the analysis directory (default: analysisDirectory+'/counters')")
    return


#================================================================================================
# Class Definition
#================================================================================================
class Settings:
    '''
    Generic settings class
    '''
    def __init__(self, **defaults):
        self.data = copy.deepcopy(defaults)

    def set(self, **kwargs):
        for key, value in kwargs.iteritems():
            if not key in self.data:
                raise Exception("Not allowed to insert '%s', available settings: %s" % (key, ", ".join(self.data.keys())))
            self.data[key] = value

    def append(self, **kwargs):
        for key, value in kwargs.iteritems():
            if not key in self.data:
                raise Exception("Not allowed to insert '%s', available settings: %s" % (key, ", ".join(self.data.keys())))
            try:
                self.data[key].append(value)
            except AttributeError:
                try:
                    self.data[key].update(value)
                except AttributeError:
                    raise Exception("Trying to append to '%s', but it does not have 'append' method (assuming list) nor 'update' method (assuming dictionary). Its type is %s." % (key, type(self.data[key]).__name__))

    def get(self, key, args=None):
        if args is None:
            return self.data[key]
        else:
            return args.get(key, self.data[key])

    def clone(self, **kwargs):
        return copy.deepcopy(self)


#================================================================================================
# Class Definition
#================================================================================================
class Count:
    '''
    Represents counter count value with uncertainty.
    '''
    ## Constructor
    def __init__(self, value, uncertainty=0.0, systUncertainty=0.0):        
        self._value = value
        self._uncertainty = uncertainty
        self._systUncertainty = systUncertainty

    def copy(self):
        return Count(self._value, self._uncertainty, self._systUncertainty)

    def clone(self):
        return self.copy()

    def value(self):
        return self._value

    def uncertainty(self):
        return self._uncertainty

    def uncertaintyLow(self):
        return self.uncertainty()

    def uncertaintyHigh(self):
        return self.uncertainty()

    def systUncertainty(self):
        return self._systUncertainty

    ## self = self + count
    def add(self, count):
        self._value += count._value
        self._uncertainty = math.sqrt(self._uncertainty**2 + count._uncertainty**2)
        self._systUncertainty = math.sqrt(self._systUncertainty**2 + count._systUncertainty**2)

    ## self = self - count
    def subtract(self, count):
        self.add(Count(-count._value, count._uncertainty, count._systUncertainty))

    ## self = self * count
    def multiply(self, count):
        self._systUncertainty = math.sqrt( (count._value * self._systUncertainty)**2 +
                                       (self._value  * count._systUncertainty)**2 )
        self._uncertainty = math.sqrt( (count._value * self._uncertainty)**2 +
                                       (self._value  * count._uncertainty)**2 )
        self._value = self._value * count._value

    ## self = self / count
    def divide(self, count):
        self._systUncertainty = math.sqrt( (self._systUncertainty / count._value)**2 +
                                       (self._value*count._systUncertainty / (count._value**2) )**2 )
        self._uncertainty = math.sqrt( (self._uncertainty / count._value)**2 +
                                       (self._value*count._uncertainty / (count._value**2) )**2 )
        self._value = self._value / count._value

    ## \var _value
    # Value of the count
    ## \var _uncertainty
    # Statistical uncertainty of the count
    ## \var _systUncertainty
    # Systematic uncertainty of the count


#================================================================================================
# Class Definition
#================================================================================================
class CountAsymmetric:
    '''
    Represents counter count value with asymmetric uncertainties.
    '''
    def __init__(self, value, uncertaintyLow, uncertaintyHigh):
        self._value = value
        self._uncertaintyLow = uncertaintyLow
        self._uncertaintyHigh = uncertaintyHigh

    def clone(self):
        return CountAsymmetric(self._value, self._uncertaintyLow, self._uncertaintyHigh)

    def value(self):
        return self._value

    def uncertainty(self):
        return max(self._uncertaintyLow, self._uncertaintyHigh)

    def uncertaintyLow(self):
        return self._uncertaintyLow

    def uncertaintyHigh(self):
        return self._uncertaintyHigh

    def multiply(self, count):
        value = count.value()
        if count.uncertainty() != 0:
            raise Exception("Can't multiply CountAsymmetric (%f, %f, %f) with Count (%f, %f) with non-zero uncertainty" % (self._value, self._uncertaintyLow, self._uncertaintyHigh, count.value(), count.uncertainty()))
        self._value *= value
        self._uncertaintyLow *= value
        self._uncertaintyHigh *= value

    ## \var _value
    # Value of the count
    ## \var _uncertaintyLow
    # Lower uncertainty of the count (-)
    ## \var _uncertaintyHigh
    # Upper uncertainty of the count (+)

def divideBinomial(countPassed, countTotal):
    p = countPassed.value()
    t = countTotal.value()
    value = p / float(t)
    p = int(p)
    t = int(t)
    errUp = ROOT.TEfficiency.ClopperPearson(t, p, 0.683, True)
    errDown = ROOT.TEfficiency.ClopperPearson(t, p, 0.683, False)
    return CountAsymmetric(value, value-errDown, errUp-value)

## Transform histogram (TH1) to a list of (name, Count) pairs.
#
# The name is taken from the x axis label and the count is Count
# object with value and (statistical) uncertainty.
def _histoToCounter(histo):
    ret = []

    for bin in xrange(1, histo.GetNbinsX()+1):
        ret.append( (histo.GetXaxis().GetBinLabel(bin),
                     Count(float(histo.GetBinContent(bin)),
                           float(histo.GetBinError(bin)))) )

    return ret

## Transform a list of (name, Count) pairs to a histogram (TH1)
def _counterToHisto(name, counter):
    histo = ROOT.TH1F(name, name, len(counter), 0, len(counter))
    histo.Sumw2()

    bin = 1
    for name, count in counter:
        histo.GetXaxis().SetBinLabel(bin, name)
        histo.SetBinContent(bin, count.value())
        histo.SetBinError(bin, count.uncertainty())
        bin += 1

    return histo

## Transform histogram (TH1) to a list of values
def histoToList(histo):
    return [histo.GetBinContent(bin) for bin in xrange(1, histo.GetNbinsX()+1)]


## Transform histogram (TH1) to a dictionary.
#
# The key is taken from the x axis label, and the value is the bin
# content.
def _histoToDict(histo):
    ret = {}

    for bin in xrange(1, histo.GetNbinsX()+1):
        ret[histo.GetXaxis().GetBinLabel(bin)] = histo.GetBinContent(bin)

    return ret

## Integrate TH1 to a Count
def histoIntegrateToCount(histo):
    count = Count(0, 0)
    if histo is None:
        return count

    for bin in xrange(0, histo.GetNbinsX()+2):
        count.add(Count(histo.GetBinContent(bin), histo.GetBinError(bin)))
    return count

## Rescales info dictionary.
# 
# Assumes that d has a 'control' key for a numeric value, and then
# normalizes all items in the dictionary such that the 'control'
# becomes one.
# 
# The use case is to have a dictionary from _histoToDict() function,
# where the original histogram is merged from multiple jobs. It is
# assumed that each histogram as a one bin with 'control' label, and
# the value of this bin is 1 for each job. Then the bin value for
# the merged histogram tells the number of jobs. Naturally the
# scheme works correctly only if the histograms from jobs are
# identical, and hence is appropriate only for dataset-like
# information.
def _rescaleInfo(d):
    factor = 1/d["control"]

    ret = {}
    for k, v in d.iteritems():
        if k in ["isPileupReweighted","isTopPtReweighted"]:
            ret[k] = v
        else:
            ret[k] = v*factor

    return ret


## Normalize TH1/TH2/TH3 to unit area.
# 
# \param h   RootHistoWithUncertainties object, or TH1/TH2/TH3 histogram
# 
# \return Normalized histogram (same as the argument object, i.e. no copy is made).
def _normalizeToOne(h):
    if isinstance(h, RootHistoWithUncertainties):
        integral = h.integral()
    elif isinstance(h, ROOT.TH3):
        integral = h.Integral(0, h.GetNbinsX()+1, 0, h.GetNbinsY()+1, 0, h.GetNbinsZ()+1)
    elif isinstance(h, ROOT.TH2):
        integral = h.Integral(0, h.GetNbinsX()+1, 0, h.GetNbinsY()+1)
    else:
        integral = h.Integral(0, h.GetNbinsX()+1)
    if integral == 0:
        return h
    else:
        return _normalizeToFactor(h, 1.0/integral)

## Scale TH1 with a given factor.
# 
# \param h   TH1 histogram
# \param f   Scale factor
# 
# TH1.Sumw2() is called before the TH1.Scale() in order to scale the
# histogram errors correctly.
def _normalizeToFactor(h, f):
    backup = ROOT.gErrorIgnoreLevel
    ROOT.gErrorIgnoreLevel = ROOT.kError
    h.Sumw2() # errors are also scaled after this call 
    ROOT.gErrorIgnoreLevel = backup
    h.Scale(f)
    return h


## Helper function for merging/stacking a set of datasets.
# 
# \param datasetList  List of all Dataset objects to consider
# \param nameList     List of the names of Dataset objects to merge/stack
# \param task         String to identify merge/stack task (can be 'stack' or 'merge')
# \param allowMissingDatasets  If True, ignore error from missing dataset (warning is nevertheless printed)
# 
# \return a triple of:
# - list of selected Dataset objects
# - list of non-selected Dataset objects
# - index of the first selected Dataset object in the original list
#   of all Datasets
# 
# The Datasets to merge/stack are selected from the list of all
# Datasets, and it is checked that all of them are either data or MC
# (i.e. merging/stacking of data and MC datasets is forbidden).
# """
def _mergeStackHelper(datasetList, nameList, task, allowMissingDatasets=False):
    if not task in ["stack", "merge"]:
        raise Exception("Task can be either 'stack' or 'merge', was '%s'" % task)

    selected = []
    notSelected = []
    firstIndex = None
    dataCount = 0
    mcCount = 0
    pseudoCount = 0

    for i, d in enumerate(datasetList):
        if d.getName() in nameList:
            selected.append(d)
            if firstIndex == None:
                firstIndex = i
            if d.isData():
                dataCount += 1
            elif d.isMC():
                mcCount += 1
            elif hasattr(d, "isPseudo") and d.isPseudo():
                pseudoCount += 1
            else:
                raise Exception("Internal error!")
        else:
            notSelected.append(d)

    if dataCount > 0 and mcCount > 0:
        raise Exception("Can not %s data and MC datasets!" % task)
    if dataCount > 0 and pseudoCount > 0:
        raise Exception("Can not %s data and pseudo datasets!" % task)
    if pseudoCount > 0 and mcCount > 0:
        raise Exception("Can not %s pseudo and MC datasets!" % task)

    if len(selected) != len(nameList):
        dlist = nameList[:]
        for d in selected:
            ind = dlist.index(d.getName())
            del dlist[ind]
        message = "Tried to %s '"%task + ", ".join(dlist) +"' which don't exist"
        if allowMissingDatasets:
            print >> sys.stderr, "WARNING: "+message
        else:
            raise Exception(message)

    return (selected, notSelected, firstIndex)


#================================================================================================
# Class Definition
#================================================================================================
class TreeDraw:
    '''
    Helper class for obtaining histograms from TTree

    This class provides an easy way to get a histogram from a TTree. It
    is inteded to be used with dataset.Dataset.getDatasetRootHisto()
    such that instead of giving the name of the histogram, an object of
    this class is given instead. dataset.Dataset.getDatasetRootHisto()
    will then call the draw() method of this class for actually
    producing the histogram.
    
    TreeDraw objects can easily be cloned from existing TreeDraw object
    with the clone() method. This method allows overriding the
    parameters given in constructor.
    
    Note that TreeDraw does not hold any results or TTree objects, only
    the recipe to produce a histogram from a TTree.
    '''
    def __init__(self, tree, varexp="", selection="", weight="", binLabelsX=None, binLabelsY=None, binLabelsZ=None):
        '''
        Constructor
        
        \param tree       Path to the TTree object in a file

        \param varexp     Expression for the variable, if given it should
        also include the histogram name and binning explicitly.

        \param selection  Draw only those entries passing this selection

        \param weight     Weight the entries with this weight

        \param binLabelsX X-axis bin labels (optional)

        \param binLabelsY Y-axis bin labels (optional)

        \param binLabelsZ Z-axis bin labels (optional)
        
        If varexp is not given, the number of entries passing selection
        is counted (ignoring weight). In this case the returned TH1 has
        1 bin, which contains the event count and the uncertainty of the
        event count (calculated as sqrt(N)).
        '''
        self.tree = tree
        self.varexp = varexp
        self.selection = selection
        self.weight = weight

        self.binLabelsX = binLabelsX
        self.binLabelsY = binLabelsY
        self.binLabelsZ = binLabelsZ

    ## Clone a TreeDraw
    #
    # <b>Keyword arguments</b> are the same as for the constructor (__init__())
    #
    # If any of the values of the keyword arguments is a function (has
    # attribute __call__), the function is called with the current
    # value as an argument, and the return value is assigned to the
    # corresponding name.
    def clone(self, **kwargs):
        args = {"tree": self.tree,
                "varexp": self.varexp,
                "selection": self.selection,
                "weight": self.weight,
                "binLabelsX": self.binLabelsX,
                "binLabelsY": self.binLabelsY,
                "binLabelsZ": self.binLabelsZ,
                }
        args.update(kwargs)

        # Allow modification functions
        for name, value in args.items():
            if hasattr(value, "__call__"):
                args[name] = value(getattr(self, name))

        return TreeDraw(**args)

    ## Prodouce TH1 from a file
    #
    # \param dataset      Dataset, the output TH1 contains the dataset name
    #                     in the histogram name. Mainly needed for compatible interface with
    #                     dataset.TreeDrawCompound
    def draw(self, dataset):
        if self.varexp != "" and not ">>" in self.varexp:
            raise Exception("varexp should include explicitly the histogram binning (%s)"%self.varexp)

        selection = self.selection
        if len(self.weight) > 0:
            if len(selection) > 0:
                selection = "%s * (%s)" % (self.weight, selection)
            else:
                selection = self.weight

        (tree, treeName) = dataset.createRootChain(self.tree)
        if tree == None:
            raise Exception("No TTree '%s' in file %s" % (treeName, dataset.getRootFile().GetName()))

        if self.varexp == "":
            nentries = tree.GetEntries(selection)
            h = ROOT.TH1F("nentries", "Number of entries by selection %s"%selection, 1, 0, 1)
            h.SetDirectory(0)
            if len(self.weight) > 0:
                h.Sumw2()
            h.SetBinContent(1, nentries)
            h.SetBinError(1, math.sqrt(nentries))
            return h

        varexp = self.varexp
        
        # e to have TH1.Sumw2() to be called before filling the histogram
        # goff to not to draw anything on the screen
        opt = ""
        if len(self.weight) > 0:
            opt = "e "
        option = opt+"goff"
        nentries = tree.Draw(varexp, selection, option)
        if nentries < 0:
            raise Exception("Error when calling TTree.Draw with the following parameters for dataset %s, nentries=%d\ntree:       %s\nvarexp:     %s\nselection:  %s\noption:     %s" % (dataset.getName(), nentries, treeName, varexp, selection, option))
        h = tree.GetHistogram()
        if h == None: # need '==' to compare null TH1
            print >>sys.stderr, "WARNING: TTree.Draw with the following parameters returned null histogram for dataset %s (%d entries)\ntree:       %s\nvarexp:     %s\nselection:  %s\noption:     %s" % (dataset.getName(), nentries, treeName, varexp, selection, option)
            return None

        h.SetName(dataset.getName()+"_"+h.GetName())
        h.SetDirectory(0)

        for axis in ["X", "Y", "Z"]:
            if getattr(self, "binLabels"+axis) is not None:
                labels = getattr(self, "binLabels"+axis)
                nlabels = len(labels)
                nbins = getattr(h, "GetNbins"+axis)()
                if nlabels != nbins:
                    raise Exception("Trying to set %s bin labels, bot %d labels, histogram has %d bins. \ntree:       %s\nvarexp:     %s\nselection:  %s\noption:     %s" %
                                    (axis, nlabels, nbins, self.tree, varexp, selection, option))
                axisObj = getattr(h, "Get"+axis+"axis")()
                for i, label in enumerate(labels):
                    axisObj.SetBinLabel(i+1, label)

        return h


    ## \var tree
    # Path to the TTree object in a file
    ## \var varexp
    # Expression for the variable
    ## \var selection
    # Draw only those entries passing this selection
    ## \var weight
    # Weight the entries with this weight

#================================================================================================
# Class Definition
#================================================================================================
class TreeScan:
    '''
    Helper class for running code for selected TTree entries

    A function is given to the constructor, the function is called for
    each TTree entry passing the selection. The TTree object is given as
    a parameter, leaf/branch data can then be read from it.
    
    Main use case: producing pickEvents list from a TTree
    '''
    def __init__(self, tree, function, selection=""):
        '''
        Constructor
        
        \param tree       Path to the TTree object in a file
        \param function   Function to call for each TTree entry
        \param selection  Select only these TTree entries
        '''
        self.tree = tree
        self.function = function
        self.selection = selection

    def clone(self, **kwargs):
        args = {"tree": self.tree,
                "function": self.function,
                "selection": self.selection}
        args.update(kwargs)
        return TreeScan(**args)


    def draw(self, dataset):
        '''
        Process TTree
        
        \param datasetName  Dataset object. Only needed for compatible interface with
        dataset.TreeDrawCompound
        '''
        rootFile = dataset.getRootFile()
        tree = rootFile.Get(self.tree)
        if tree == None:
            raise Exception("No TTree '%s' in file %s" % (self.tree, rootFile.GetName()))

        tree.Draw(">>elist", self.selection)
        elist = ROOT.gDirectory.Get("elist")
        for ientry in xrange(elist.GetN()):
            tree.GetEntry(elist.GetEntry(ientry))
            self.function(tree)

    ## \var tree
    # Path to the TTree object in a file
    ## \var function
    # Function to call for each TTree entry
    ## \var selection
    # Select only these TTree entries

#================================================================================================
# Class Definition
#================================================================================================
class TreeDrawCompound:
    '''
    Provides ability to have separate dataset.TreeDraws for different datasets
    
    One specifies a default dataset.TreeDraw, and the exceptions for that with a
    map from string to dataset.TreeDraw.
    '''
    def __init__(self, default, datasetMap={}):
        '''
        Constructor
    
        \param default     Default dataset.TreeDraw
        \param datasetMap  Dictionary for the overriding dataset.TreeDraw objects
        containing dataset names as keys, and TreeDraws as values.        
        '''
        self.default = default
        self.datasetMap = datasetMap

    ## Add a new dataset specific dataset.TreeDraw
    #
    # \param datasetName  Name of the dataset
    # \param treeDraw     dataset.TreeDraw object to add
    def add(self, datasetName, treeDraw):
        self.datasetMap[datasetName] = treeDraw

    ## Produce TH1
    #
    # \param datasetName  Dataset object
    #
    # The dataset.TreeDraw for which the call is forwarded is searched from
    # the datasetMap with the datasetName. If found, that object is
    # used. If not found, the default TreeDraw is used.
    def draw(self, dataset):
        h = None
        datasetName = dataset.getName()
        if datasetName in self.datasetMap:
            #print "Dataset %s in datasetMap" % datasetName, self.datasetMap[datasetName].selection
            h = self.datasetMap[datasetName].draw(dataset)
        else:
            #print "Dataset %s with default" % datasetName, self.default.selection
            h = self.default.draw(dataset)
        return h

    ## Clone
    #
    # <b>Keyword arguments</b> are the same as for the clone() method
    # of the contained TreeDraw objects. The new TreeDrawCompoung is
    # constructed such that the default and dataset-specific TreeDraws
    # are cloned with the given keyword arguments.
    def clone(self, **kwargs):
        ret = TreeDrawCompound(self.default.clone(**kwargs))
        for name, td in self.datasetMap.iteritems():
            ret.datasetMap[name] = td.clone(**kwargs)
        return ret

    ## \var default
    # Default dataset.TreeDraw
    ## \var datasetMap
    # Dictionary for the overriding dataset.TreeDraw objects
    # containing dataset names as keys, and TreeDraws as values.

def _treeDrawToNumEntriesSingle(treeDraw):
    var = treeDraw.weight
    if var == "":
        var = treeDraw.selection
    if var != "":
        var += ">>dist(1,0,2)" # the binning is arbitrary, as the under/overflow bins are counted too
    # if selection and weight are "", TreeDraw.draw() returns a histogram with the number of entries
    return treeDraw.clone(varexp=var)

## Maybe unnecessary function?
#
# Seems to be used only from DatasetQCDData class, which was never
# finished.
def treeDrawToNumEntries(treeDraw):
    if isinstance(treeDraw, TreeDrawCompound):
        td = TreeDrawCompound(_treeDrawToNumEntriesSingle(treeDraw.default))
        for name, td2 in treeDraw.datasetMap.iteritems():
            td.add(name, _treeDrawToNumEntriesSingle(td2))
        return td
    else:
        return _treeDrawToNumEntriesSingle(treeDraw)


#================================================================================================
# Class Definition
#================================================================================================
class Systematics:
    '''
    Class to encapsulate shape/normalization systematics for plot creation
    '''
    class OnlyForMC:
        pass
    class OnlyForPseudo:
        pass
    class OnlyForPseudoAndMC:
        pass
    class All:
        pass

    ## Constructor
    #
    # \param kwargs   Keyword arguments, see below
    #
    # <b>Keyword arguments</b>
    # \li\a allShapes                 If True, use all available shape variation uncertainties
    # \li\a shapes                    List of strings for explicit list of shape
    #                                 variations (e.g. ['SystVarJES',
    #                                 'SystVarJER'])
    # \li\a normalizationSelections   List of strings for the selections
    #                                 used up to this point for
    #                                 normalization uncertainties (not
    #                                 used yet)
    # \li\a additionalNormalizations  Dictionary (name (string) ->
    #                                 value (float)) for addititional
    #                                 normalization uncertainties. The
    #                                 uncertainties are supposed to be
    #                                 relative.
    # \li\a additionalDatasetNormalizations Dictionary (name (string)
    #                                 -> function (string -> float)) for
    #                                 additional dataset-specific
    #                                 uncertainties. The uncertainties are
    #                                 supposed to be relative.
    # \li\a additionalShapes          Dictionary (name (string) -> (th1up,
    #                                 th1down)) for additional shape
    #                                 variation uncertainties.
    #                                 th1up/th1down can be either
    #                                 TH1s, or strings for paths of
    #                                 histograms in the analysis
    #                                 directory (or ROOT file)
    # \li\a additionalShapesRelative  Dictionary (name (string) -> th1)
    #                                 for additional bin-wise relative
    #                                 uncertainties. Each bin of TH1
    #                                 should have the relative
    #                                 uncertainty of that bin.
    # \li\a applyToDatasets           Datasets to which the systematic uncertainties are applied (one of the tag classes OnlyForMC, OnlyForPseudo, OnlyForPseudoAndMC, All)
    # \li\a verbose                   If True, print the applied uncertainties
    def __init__(self, **kwargs):
        self.settings = Settings(allShapes=False,
                                 shapes=[],
                                 normalizationSelections=[],
                                 additionalNormalizations={},
                                 additionalDatasetNormalizations={},
                                 additionalShapes={},
                                 additionalShapesRelative={},
                                 applyToDatasets=Systematics.OnlyForPseudoAndMC,
                                 verbose=False,
                                 )
        self.settings.set(**kwargs)

    ## Set systematics parameters
    #
    # \param kwargs  Keyword arguments, see __init__()
    def set(self, **kwargs):
        self.settings.set(**kwargs)

    ## Append to systematic parameters
    #
    # \param kwargs   Keyword arguments, see __init__()
    #
    # Appending works only for those parameters, whose type is list or
    # dictionary.
    def append(self, **kwargs):
        self.settings.append(**kwargs)

    ## Clone Systematics recipe
    #
    # \param kwargs  Keyword arguments for overriding parameters, see __init__()
    def clone(self, **kwargs):
        cl = copy.deepcopy(self)
        cl.set(**kwargs)
        return cl

    ## Create SystematicsHelper for Dataset.getDatasetRootHisto()
    #
    # \param name    Path to the histogram in the analysis TDirectory
    # \param kwargs  Keyword arguments for overriding parameters, see __init__()
    def histogram(self, name, **kwargs):
        settings = self.settings
        if len(kwargs) > 0:
            settings = settings.clone(**kwargs)
        return SystematicsHelper(name, settings)

#================================================================================================
# Class Definition
#================================================================================================
class SystematicsHelper:
    '''
    Helper class to do the work for obtaining uncertainties from their 
    sources for a requested histogram
    
    The object should be created with Systematics.histogram(), i.e. not
    directly.
    '''
    def __init__(self, histoName, settings):
        '''
        Constructor
        
        \param histoName   Name of the histogram to read
        \param settings    Settings object for systematic recipe
        '''
        self._histoName = histoName
        self._settings = settings

    ## Read the histogram for a dataset
    #
    # \param dset  Dataset object
    def draw(self, dset):
        (th1, realName) = dset.getRootHisto(self._histoName)
        return th1

    ## Add uncertainties to RootHistoWithUncertainties object
    #
    # \param dset                         Dataset object
    # \param rootHistoWithUncertainties   RootHistoWithUncertainties object
    # \param modify                       Optional modification function, see Dataset.getDatasetRootHisto()
    def addUncertainties(self, dset, rootHistoWithUncertainties, modify=None):
        verbose = self._settings.get("verbose")
        if verbose:
            print "Adding uncertainties to histogram '%s' of dataset '%s'" % (self._histoName, dset.getName())

        onlyFor = self._settings.get("applyToDatasets")
        if dset.isMC():
            if onlyFor is Systematics.OnlyForPseudo:
                if verbose:
                    print "  Dataset is MC, no systematics considered (Systematics(..., onlyForMC=%s))" % onlyFor.__name__
                return
        elif dset.isPseudo():
            if onlyFor is Systematics.OnlyForMC:
                if verbose:
                    print "  Dataset is pseudo, no systematics considered (Systematics(..., onlyForMC=%s))" % onlyFor.__name__
                return
        elif dset.isData():
            if onlyFor is not Systematics.All:
                if verbose:
                    print "  Dataset is data, no systematics considered (Systematics(..., onlyForMC=%s))" % onlyFor.__name__
                return
        else:
            raise Exception("Internal error (unknown dataset type)")

        # Read the shape variations from the Dataset
        shapes = []
        allShapes = dset.getAvailableSystematicVariationSources()
        if self._settings.get("allShapes"):
            shapes = allShapes
            if verbose:
                print "  Using all available shape variations (%s)" % ",".join(shapes)
        else:
            shapes = self._settings.get("shapes")
            #for s in self._settings.get("shapes"):
            #    if s in allShapes:
            #        shapes.append(s)
            if verbose:
                print "  Using explicitly specified shape variations (%s)" % ",".join(shapes)
        for source in shapes:
            plus = None
            minus = None
            # Need to do the check, because of QCD shape uncertainty
            if dset.hasRootHisto(self._histoName, analysisPostfix="_"+source+"Plus"):
                (plus, realName) = dset.getRootHisto(self._histoName, analysisPostfix="_"+source+"Plus")
                (minus, realName) = dset.getRootHisto(self._histoName, analysisPostfix="_"+source+"Minus")
                if modify is not None:
                    modify(plus)
                    modify(minus)
                rootHistoWithUncertainties.addShapeUncertaintyFromVariation(source, plus, minus)

        # Add any additional shape variation histograms supplied by the user
        additShapes = self._settings.get("additionalShapes")
        if len(additShapes) > 0:
            if verbose:
                print "  Adding additional shape variations %s" % ",".join(additShapes.keys())
            for source, (th1plus, th1minus) in additShapes.iteritems():
                hp = th1plus
                hm = th1minus
                if not isinstance(th1plus, ROOT.TH1):
                    (hp, realName) = dset.getRootHisto(th1plus)
                    if modify is not None:
                        modify(hp)
                if not isinstance(th1minus, ROOT.TH1):
                    (hm, realName) = dset.getRootHisto(th1minus)
                    if modify is not None:
                        modify(hm)
                rootHistoWithUncertainties.addShapeUncertaintyFromVariation(source, hp, hm)

        # Add any bin-wise relative uncertainties supplied by the user
        relShapes = self._settings.get("additionalShapesRelative")
        if len(relShapes) > 0:
            if verbose:
                print "  Adding additional bin-wise relative uncertainties %s" % ",".join(relShapes.keys())
            for source, th1 in relShapes.iteritems():
                rootHistoWithUncertainties.addShapeUncertaintyFromVariationRelative(source, th1)

        # Add normalization uncertainties given the selection step
        normSel = self._settings.get("normalizationSelections")
        if len(normSel) > 0:
            if verbose:
                print "  Adding normalization uncertainties after selections %s" % ",".join(normSel)
            raise Exception("Normalization uncertainties given the set of selections is not supported yet")

        # Add any user-supplied normalization uncertainties
        additNorm = self._settings.get("additionalNormalizations")
        if len(additNorm) > 0:
            if verbose:
                print "  Adding additional relative normalization uncertainties %s" % ",".join(additNorm.keys())
            for source, value in additNorm.iteritems():
                rootHistoWithUncertainties.addNormalizationUncertaintyRelative(source, value)

        # Add any user-supplied dataset-specific normalization uncertainties
        additNorm = self._settings.get("additionalDatasetNormalizations")
        if len(additNorm) > 0:
            if verbose:
                print "  Adding additional dataset-specific (for %s) relative normalization uncertainties %s" % (dset.getName(), ",".join(additNorm.keys()))
            for source, func in additNorm.iteritems():
                value = func(dset.getName())
                rootHistoWithUncertainties.addNormalizationUncertaintyRelative(source, value)

        if verbose:
            print "  Below is the final set of uncertainties for this histogram"
            rootHistoWithUncertainties.printUncertainties()

        
#================================================================================================ 
# Class Definition
#================================================================================================ 
class RootHistoWithUncertainties:
    '''
    Class to encapsulate a ROOT histogram with a bunch of uncertainties
    
    Looks almost as TH1, except holds bunch of uncertainties; the histograms contained are clones and therefore owned by the class
    '''
    def __init__(self, rootHisto, verbose=False):
        ''' 
        The constructor
        '''
        self._rootHisto = None
        self._verbose   = verbose

        # dictionary of name -> (th1Plus, th1Minus)
        # This dictionary contains the variation uncertainties
        # Laterally (i.e. for combining same uncertainty between bins or samples, i.e. relative uncertainty is constant), linear sum is used
        # Vertically (i.e. for different source of uncertainties), quadratic sum is used
        # The numbers are stored into the bin content as absolute uncertainties
        self._shapeUncertainties = {}

        self.setRootHisto(rootHisto)

        # Treat these shape uncertainties as statistical uncertainties in getSystematicUncertaintyGraph()
        self._treatShapesAsStat = set() # use set to avoid duplicates

        # Boolean to save the status if the under- and overflow bins have been made visible (i.e. summed to the first and last bin)
        self._flowBinsVisibleStatus = False
        return

    def Print(self, msg, printHeader=True):
        '''
        Simple print function. If verbose option is enabled prints, otherwise does nothing
        '''
        fName = __file__.split("/")[-1]
        fName = fName.replace(".pyc", ".py")
        if printHeader:
            print "=== ", fName
        print "\t", msg
        return

    def _checkConsistency(self, name, th1):
        # I can't use this since it's private/protected :(
        #if not ROOT.TH1.CheckConsistency(self._rootHisto, th1):
        #    raise Exception("Adding uncertainty %s, histogram consistency check fails (ROOT.TH1.CheckConsistency())" % name)
        if self._rootHisto.GetDimension() != th1.GetDimension():
            raise Exception("Adding uncertainty %s, histograms have different dimension (%d != %d)" % (name, self._rootHisto.GetDimension(), th1.GetDimension()))
        if self._rootHisto.GetNbinsX() != th1.GetNbinsX():
            raise Exception("Adding uncertainty %s, histograms have different number of X bins (%d != %d)" % (name, self._rootHisto.GetNbinsX(), th1.GetNbinsX()))

    def delete(self):
        if self._rootHisto != None:
            self._rootHisto.Delete()
            self._rootHisto = None
        for k in self._shapeUncertainties.keys():
            (u,d) = self._shapeUncertainties[k]
            u.Delete()
            d.Delete()
        self._shapeUncertainties = {}

    ## Set the ROOT histogram object
    #
    # \param newRootHisto   ROOT histogram object
    #
    # This method can be called only in absence of shape variation uncertainties
    def setRootHisto(self, newRootHisto):
        if len(self._shapeUncertainties.keys()) != 0 or self._rootHisto != None:
            raise Exception("There are shape uncertanties, you should not set the original histogram (call delete() before)!")
        self._rootHisto = Clone(newRootHisto)

    ## Get the ROOT histogram object
    def getRootHisto(self):
        return self._rootHisto

    ## Get the event rate, i.e. integral of the root histo object (usually at this point the under and overflow bins are already merged to actual bins)
    def getRate(self):
        if not self._flowBinsVisibleStatus:
            raise Exception("getRate(): The under/overflow bins might not be not empty! Did you forget to call makeFlowBinsVisible() before getRate()?")
        myRate = self._rootHisto.Integral()
        myRateIncludingOverflow = self.integral()
        if abs(myRate - myRateIncludingOverflow) > 0.00001:
            raise Exception("getRate(): Weird, the under/overflow should be empty at this point, but apparantly they are not?!")
        return myRate

    ## Get the stat. uncertainty of the root histo object
    def getRateStatUncertainty(self):
        if not self._flowBinsVisibleStatus:
            raise Exception("getRate(): The under/overflow bins might not be not empty! Did you forget to call makeFlowBinsVisible() before getRate()?")
        if len(self._treatShapesAsStat) > 0:
            print "WARNING: some shapes are treated as statistical uncertainty, but they have not been implemented yet to getRateStatUncertainty()!"
        mySum = 0.0
        if isinstance(self._rootHisto, ROOT.TH2):
            raise Exception("getRateStatUncertainty() supported currently only for TH1!")
        for i in range(1, self._rootHisto.GetNbinsX()+1):
            mySum += self._rootHisto.GetBinError(i)**2
        return math.sqrt(mySum)

    ## Get the syst. uncertainty of the root histo object
    def getRateSystUncertainty(self):
        if not self._flowBinsVisibleStatus:
            raise Exception("getRate(): The under/overflow bins might not be not empty! Did you forget to call makeFlowBinsVisible() before getRate()?")
        if isinstance(self._rootHisto, ROOT.TH2):
            raise Exception("getRateSystUncertainty() supported currently only for TH1!")
        # Integrate first over distribution, then sum
        myClone = self.Clone()
        myClone.Rebin(self._rootHisto.GetNbinsX())
        g = myClone.getSystematicUncertaintyGraph()
        myClone.Delete()
        myResult = (g.GetErrorYhigh(0),g.GetErrorYlow(0))
        g.Delete()
        return myResult

    ## Adds the underflow and overflow bins to the first and last bins, respectively
    def makeFlowBinsVisible(self):
        #if self._flowBinsVisibleStatus:
        #    return
        self._flowBinsVisibleStatus = True
        # Update systematics histograms first
        for key, (hPlus, hMinus) in self._shapeUncertainties.iteritems():
            histogramsExtras.makeFlowBinsVisible(hPlus)
            histogramsExtras.makeFlowBinsVisible(hMinus)
        # Update nominal histogram
        histogramsExtras.makeFlowBinsVisible(self._rootHisto)

    ## Sets negative bins to zero events
    def treatNegativeBins(self, minimumStatUncertainty):
        def treatBins(h):
            for i in range(h.GetNbinsX()):
                if h.GetBinContent(i+1) < 0.0:
                    h.SetBinContent(i+1, 0.0)
        # Treat negative bins in rate histo
        treatBins(self._rootHisto)
        for i in range(self._rootHisto.GetNbinsX()):
            if self._rootHisto.GetBinError(i+1) < minimumStatUncertainty:
                self._rootHisto.SetBinError(i+1, minimumStatUncertainty)
        # Treat negative bins in variations
        for key, (hPlus, hMinus) in self._shapeUncertainties.iteritems():
            treatBins(hPlus)
            treatBins(hMinus)

    ## Add shape variation uncertainty (Note that the nominal value is subtracted from the variations to obtain absolute uncert.)
    #
    # \param name     Name of the uncertainty
    # \param th1Plus  TH1 for the 'plus' variation
    # \param th1Minus TH1 for the 'minus' variation
    def addShapeUncertaintyFromVariation(self, name, th1Plus, th1Minus):
        if self._flowBinsVisibleStatus:
            # Check if flow bins have entries
            myStatus = abs(th1Plus.GetBinContent(th1Plus.GetNbinsX()+1)) < 0.00001
            myStatus &= abs(th1Minus.GetBinContent(th1Minus.GetNbinsX()+1)) < 0.00001
            myStatus &= abs(th1Plus.GetBinContent(0)) < 0.00001
            myStatus &= abs(th1Minus.GetBinContent(0)) < 0.00001
            if not myStatus:
                raise Exception("addShapeUncertaintyFromVariation(): result could be ambiguous, because under/overflow bins have already been moved to visible bins")
        plusClone = aux.Clone(th1Plus)
        minusClone = aux.Clone(th1Minus)
        self._checkConsistency(name, plusClone)
        self._checkConsistency(name, minusClone)
        # Subtract nominal to get absolute uncertainty (except for source histograms)
        if name in self._shapeUncertainties.keys():
            raise Exception("Uncertainty '%s' has already been added!"%name)
        plusClone.Add(self._rootHisto, -1.0)
        minusClone.Add(self._rootHisto, -1.0) # is this really correct? or should we have 'minusClone.Scale(-1)' afterwards to get this as "rootHisto - minus_band"?
        # Store
        self._shapeUncertainties[name] = (plusClone, minusClone)

    def addAbsoluteShapeUncertainty(self, name, th1Plus, th1Minus):
        if name in self._shapeUncertainties.keys():
            raise Exception("Uncertainty '%s' has already been added!"%name)
        plusClone = aux.Clone(th1Plus)
        minusClone = aux.Clone(th1Minus)
        self._checkConsistency(name, plusClone)
        self._checkConsistency(name, minusClone)
        self._shapeUncertainties[name] = (plusClone, minusClone)

    ## Remove superfluous shape variation uncertainties
    #
    # \param keepList  List of variation names to keep
    #
    # The normalization relative uncertainties are summed quadratically
    def keepOnlySpecifiedShapeUncertainties(self, keepList):
        dropList = []
        for key in self._shapeUncertainties.keys():
            if not key in keepList:
                dropList.append(key)
        for key in dropList:
            (hplus,hminus) = self._shapeUncertainties[key]
            hplus.Delete()
            hminus.Delete()
            del self._shapeUncertainties[key]

    ## Remove shape variation uncertainties for a key
    #
    # \param name   String of key to be removed
    #
    # The normalization relative uncertainties are summed quadratically
    def removeShapeUncertainty(self, name):
        myKey = None
        if name in self._shapeUncertainties.keys():
            myKey = name
        elif "SystVar"+name in self._shapeUncertainties.keys():
            myKey = "SystVar"+name
        else:
            raise Exception("Could not find key '%s' in syst. var.! (list = %s)"%(name,", ".join(map(str,self._shapeUncertainties.keys()))))
        (hplus,hminus) = self._shapeUncertainties[myKey]
        hplus.Delete()
        hminus.Delete()
        del self._shapeUncertainties[myKey]

    ## Add bin-wise relative uncertainty
    #
    # \param name     Name of the uncertainty
    # \param th1Plus  TH1 holding the relative uncertainties (e.g. 0.2 for 20 %)
    # \param th1Minus TH1 holding the relative uncertainties (e.g. 0.2 for 20 %); if None, then th1Plus values are used
    def addShapeUncertaintyRelative(self, name, th1Plus, th1Minus=None):
        if name in self._shapeUncertainties.keys():
            raise Exception("addShapeUncertaintyRelative(): Uncertainty '%s' already exists (did you add it twice?)!"%name)
        if self._flowBinsVisibleStatus:
            raise Exception("addShapeUncertaintyRelative(): result could be ambiguous, because under/overflow bins have already been moved to visible bins")
        if isinstance(th1Plus, ROOT.TH2) or isinstance(th1Minus, ROOT.TH2):
            raise Exception("So far only TH1's are supported (and not TH2/TH3).")

        self._checkConsistency(name, th1Plus)
        hplus = aux.Clone(th1Plus)

        hminus = None
        if th1Minus != None:
            self._checkConsistency(name, th1Minus)
            hminus = aux.Clone(th1Minus)
        else:
            hminus = aux.Clone(th1Plus)
            hminus.Scale(-1)

        for bin in xrange(1, self._rootHisto.GetNbinsX()+1):
            myRate = self._rootHisto.GetBinContent(bin)
            hplus.SetBinContent(bin, myRate * hplus.GetBinContent(bin))
            hminus.SetBinContent(bin, myRate * hminus.GetBinContent(bin))

        self._shapeUncertainties[name] = (hplus, hminus)


    ## Add normalization relative uncertainty
    #
    # \param name             Name of the uncertainty
    # \param uncertaintyPlus  Float for the value (e.g. 0.2 for 20 %)
    # \param uncertaintyMinus  Float for the value (e.g. 0.2 for 20 %); if None, then uncertaintyPlus value is used
    #
    # The normalization relative uncertainties are summed quadratically
    def addNormalizationUncertaintyRelative(self, name, uncertaintyPlus, uncertaintyMinus=None):
        if name in self._shapeUncertainties.keys():
            raise Exception("addShapeUncertaintyRelative(): Uncertainty '%s' already exists (did you add it twice?)!"%name)

        hplus = aux.Clone(self._rootHisto)
        hplus.Reset()
        hminus = aux.Clone(hplus)
        for bin in xrange(1, self._rootHisto.GetNbinsX()+1):
            myRate = self._rootHisto.GetBinContent(bin)
            hplus.SetBinContent(bin, myRate * uncertaintyPlus)
            if uncertaintyMinus == None:
                hminus.SetBinContent(bin, -myRate * uncertaintyPlus)
            else:
                hminus.SetBinContent(bin, -abs(myRate * uncertaintyMinus))

        self._shapeUncertainties[name] = (hplus, hminus)

    ## Get the dictionary of shape variation uncertainties
    def getShapeUncertainties(self):
        return self._shapeUncertainties

    def getShapeUncertaintyNames(self):
        return self._shapeUncertainties.keys()

    ## Return True if this histogram has any systematic uncertainties associated to it
    def hasSystematicUncertainties(self):
        return len(self._shapeUncertainties) > 0

    ## Set the list of shape uncertainty names that should be treated as statistical uncertainties
    def setShapeUncertaintiesAsStatistical(self, names):
        self._treatShapesAsStat = set(names)

    ## Add a shape uncertainty name to the list of that should be treated as statistical uncertainties
    def addShapeUncertaintiesAsStatistical(self, name):
        self._treatShapesAsStat.add(name)

    ## Get the set of shape uncertainty names that should be treated as statistical uncertainties
    def getShapeUncertaintiesAsStatistical(self):
        return self._treatShapesAsStat

    ## Create TGraphAsymmErrors for the sum of uncertainties
    #
    # \param addStatistical   If true, also statistical uncertainties are added
    # \param addSystematic    If False, don't include systematic uncertainties
    #
    # Statistical uncertainties are taken via _rootHisto.GetBinError().
    #
    # All uncertainties are summed in quadrature for each bin.
    #
    # For asymmetric uncertainties the sum is done separately for both
    # sides (this is a rather crude approximation, since in these
    # cases the uncertainties are probably not Gaussian).
    #
    # With shape variation uncertainties it can happen that both
    # variations yield value larger or smaller than the nominal. If
    # this happens, only the variation with larger absolute difference
    # from the nominal value is considered, and only in the difference
    # direction (i.e. asymmetrically). Again, a rather crude
    # approximation.
    def getSystematicUncertaintyGraph(self, addStatistical=False, addSystematic=True):
        xvalues = []
        xerrhigh = []
        xerrlow = []
        yvalues = []
        yerrhigh = []
        yerrlow = []

        class WrapTH1:
            def __init__(self, th1):
                self._th1 = th1
            def begin(self):
                return 1
            def end(self):
                return self._th1.GetNbinsX()+1
            def xvalues(self, i):
                xval = self._th1.GetBinCenter(i)
                xlow = xval-self._th1.GetXaxis().GetBinLowEdge(i)
                xhigh = self._th1.GetXaxis().GetBinUpEdge(i)-xval
                return (xval, xlow, xhigh)
            def y(self, i):
                return self._th1.GetBinContent(i)
            def statErrors(self, i):
                stat = self._th1.GetBinError(i)
                return (stat, stat)
        class WrapTGraph:
            def __init__(self, gr):
                self._gr = gr
            def begin(self):
                return 0
            def end(self):
                return self._gr.GetN()
            def xvalues(self, i):
                return (self._gr.GetX()[i], self._gr.GetErrorXlow(i), self._gr.GetErrorXhigh(i))
            def y(self, i):
                return self._gr.GetY()[i]
            def statErrors(self, i):
                return (self._gr.GetErrorYlow(i), self._gr.GetErrorYhigh(i))

        if isinstance(self._rootHisto, ROOT.TGraph):
            wrapper = WrapTGraph(self._rootHisto)
        else:
            wrapper = WrapTH1(self._rootHisto)

        # Set shapes to stat, syst, or stat+syst according to what was
        # requested
        shapes = []
        if addStatistical and len(self._treatShapesAsStat) > 0:
            if addSystematic:
                # stat+syst, so we can just add all shape uncertainties
                shapes = self._shapeUncertainties.values()
            else:
                # only stat, so get only them
                for name in self._treatShapesAsStat:
                    shapes.append(self._shapeUncertainties[name])
        elif addSystematic:
            # in this case all shapes are syst
            shapes = self._shapeUncertainties.values()

        #shapes.sort()
        #print addStatistical, addSystematic, "\n  ".join([x[0].GetName() for x in shapes])

        for i in xrange(wrapper.begin(), wrapper.end()):
            (xval, xlow, xhigh) = wrapper.xvalues(i)

            yval = wrapper.y(i)
            yhighSquareSum = 0.0
            ylowSquareSum = 0.0

            if addStatistical:
                (statLow, statHigh) = wrapper.statErrors(i)
                yhighSquareSum += statHigh**2
                ylowSquareSum += statLow**2

            if len(shapes) > 0:
                for shapePlus, shapeMinus in shapes:
                    diffPlus = shapePlus.GetBinContent(i) # Note that this could have + or - sign
                    diffMinus = shapeMinus.GetBinContent(i) # Note that this could have + or - sign
                    (addPlus, addMinus) = aux.getProperAdditivesForVariationUncertainties(diffPlus, diffMinus)
                    yhighSquareSum += addPlus
                    ylowSquareSum += addMinus

            xvalues.append(xval)
            xerrhigh.append(xhigh)
            xerrlow.append(xlow)
            yvalues.append(yval)
            yerrhigh.append(math.sqrt(yhighSquareSum))
            yerrlow.append(math.sqrt(ylowSquareSum))

        return ROOT.TGraphAsymmErrors(len(xvalues), array.array("d", xvalues), array.array("d", yvalues),
                                      array.array("d", xerrlow), array.array("d", xerrhigh),
                                      array.array("d", yerrlow), array.array("d", yerrhigh))

    def printUncertainties(self):
        '''
        Print associated systematic uncertainties
        '''
        print "Shape uncertainties (%d):" % len(self._shapeUncertainties)
        keys = self._shapeUncertainties.keys()
        keys.sort()
        for key in keys:
            print "  %s" % key

    #### Below are methods for "better" implementation for some ROOT TH1 methods
    def integral(self):
        '''
        Calculate integral including under/overflow bins
        '''
        if isinstance(self._rootHisto, ROOT.TH3):
            return self._rootHisto.Integral(0, self._rootHisto.GetNbinsX()+2, 0, self._rootHisto.GetNbinsY()+2, 0, self._rootHisto.GetNbinsZ()+2)
        elif isinstance(self._rootHisto, ROOT.TH2):
            return self._rootHisto.Integral(0, self._rootHisto.GetNbinsX()+2, 0, self._rootHisto.GetNbinsY()+2)
        else:
            return self._rootHisto.Integral(0, self._rootHisto.GetNbinsX()+2)

    def getXmin(self):
        '''
         Get minimum of X axis
         '''
        return aux.th1Xmin(self._rootHisto)

    def getXmax(self):
        '''
        Get maximum of X axis
        '''
        return aux.th1Xmax(self._rootHisto)

    def getYmin(self):
        '''
        Get minimum if Y axis
        '''
        if self._rootHisto is None:
            return None
        if isinstance(self._rootHisto, ROOT.TH2):
            return aux.th2Ymin(self._rootHisto)
        else:
            return self._rootHisto.GetMinimum()

    def getYmax(self):
        '''
        Get maximum of Y axis
        '''
        if self._rootHisto is None:
            return None
        if isinstance(self._rootHisto, ROOT.TH2):
            return aux.th2Ymax(self._rootHisto)
        else:
            return self._rootHisto.GetMaximum()

    def getXtitle(self):
        '''
        Get X axis title
        '''
        if self._rootHisto is None:
            return None
        return self._rootHisto.GetXaxis().GetTitle()

    def getYtitle(self):
        '''
        Get Y axis title
        '''
        if self._rootHisto is None:
            return None
        return self._rootHisto.GetYaxis().GetTitle()

    def getBinWidth(self, bin):
        '''
        Get the width of a bin
        
        \param bin  Bin number
        '''
        if self._rootHisto is None:
            return None
        return self._rootHisto.GetBinWidth(bin)

    def getBinWidths(self):
        '''
        Get list of bin widths
        '''
        if self._rootHisto is None:
            return None
        return [self._rootHisto.GetBinWidth(i) for i in xrange(1, self._rootHisto.GetNbinsX()+1)]

    #### Below are methods for ROOT TH1 compatibility (only selected methods are implemented)
    def GetNbinsX(self):
        '''
        Get the number of X axis bins
        '''
        return self._rootHisto.GetNbinsX()

    def GetName(self):
        '''
        Get the name
        '''
        return self._rootHisto.GetName()

    def SetName(self, *args):
        '''
        Set the name
        
         \param args   Positional arguments, forwarded to TH1.SetName()
        '''
        self._rootHisto.SetName(*args)

    def Sumw2(self):
        '''
        Sumw2
        
        It is enough to propagate the call rot self._rootHisto, because
        from the uncertainty histograms we are only interested of the values
        '''
        self._rootHisto.Sumw2()
        return

    def Rebin(self, *args):
        '''
        Rebin histogram
        
        \param args  Positional arguments, forwarded to TH1.Rebin()
        '''
        if self._rootHisto == None:
            raise Exception("Tried to call Rebin for a histogram which has been deleted")
        htmp = self._rootHisto.Rebin(*args)
        if htmp == None:
            raise Exception("Something went wrong with the rebinning (%s)!"%self._rootHisto.GetName())
        if htmp.GetBinContent(htmp.GetNbinsX()) == float('Inf'):
            raise Exception("Check the rebin range, it produces infinity!")
        if len(args) > 1: # If more than 1 argument is given, ROOT creates a clone of the histogram
            self._rootHisto.Delete()
        ROOT.SetOwnership(htmp, True)
        htmp.SetDirectory(0)
        self._rootHisto = htmp
        keys = self._shapeUncertainties.keys()
        for key in keys:
            (plus, minus) = self._shapeUncertainties[key]
            plustmp = plus.Rebin(*args)
            minustmp = minus.Rebin(*args)
            if plustmp.GetBinContent(htmp.GetNbinsX()) == float('Inf') or minustmp.GetBinContent(htmp.GetNbinsX()) == float('Inf'):
                raise Exception("Check the rebin range, it produces infinity!")
            if len(args) > 1: # If more than 1 argument is given, ROOT creates a clone of the histogram
                plus.Delete()
                minus.Delete()
            ROOT.SetOwnership(plustmp, True)
            ROOT.SetOwnership(minustmp, True)
            plustmp.SetDirectory(0)
            minustmp.SetDirectory(0)
            self._shapeUncertainties[key] = (plustmp, minustmp)
        self.makeFlowBinsVisible()
        return

    def Rebin2D(self, *args):
        '''
        Rebin histogram
        
         \param args  Positional arguments, forwarded to TH1.Rebin()
        '''
        htmp = self._rootHisto.Rebin2D(*args)
        if len(args) > 2: # If more than 2 arguments are given, ROOT creates a clone of the histogram
            self._rootHisto.Delete()
        ROOT.SetOwnership(htmp, True)
        htmp.SetDirectory(0)
        self._rootHisto = htmp
        keys = self._shapeUncertainties.keys()
        for key in keys:
            (plus, minus) = self._shapeUncertainties[key]
            plustmp = plus.Rebin2D(*args)
            minustmp = minus.Rebin2D(*args)
            if len(args) > 2: # If more than 2 arguments are given, ROOT creates a clone of the histogram
                plus.Delete()
                minus.Delete()
            ROOT.SetOwnership(plustmp, True)
            ROOT.SetOwnership(minustmp, True)
            plustmp.SetDirectory(0)
            minustmp.SetDirectory(0)
            self._shapeUncertainties[key] = (plustmp, minustmp)
        self.makeFlowBinsVisible()
        return

    def Add(self, other, *args):
        '''
        Add another RootHistoWithUncertainties object
        
        \param other   RootHistoWithUncertainties object
        \param args  Positional arguments, forwarded to TH1.Add()
        '''
        # Make sure the flow bins are handled in the same way before adding
        if self._flowBinsVisibleStatus and not other._flowBinsVisibleStatus:
            other.makeFlowBinsVisible()
        if not self._flowBinsVisibleStatus and other._flowBinsVisibleStatus:
            self.makeFlowBinsVisible()

        keys1 = self._shapeUncertainties.keys()
        keys2 = other._shapeUncertainties.keys()
        #keys1.sort()
        #keys2.sort()
        for key in keys1:
            if key in keys2:
                (plus, minus) = self._shapeUncertainties[key]
                (otherPlus, otherMinus) = other._shapeUncertainties[key]
                plus.Add(otherPlus, *args)
                minus.Add(otherMinus, *args)
            #else:
                # key is not in other, keep it like it is
        for key in keys2:
            if not key in keys1:
                # Add those histograms, which so far did not exist
                (plus, minus) = other._shapeUncertainties[key]
                newPlus = aux.Clone(plus)
                newMinus = aux.Clone(minus)
                if len(args) > 0:
                    newPlus.Scale(args[0])
                    newMinus.Scale(args[0])
                self._shapeUncertainties[key] = (newPlus, newMinus)

        # Add histo
        self._rootHisto.Add(other._rootHisto, *args)

        # Add shape uncertainties treated as stat
        self._treatShapesAsStat.update(other._treatShapesAsStat)
        return
    
    def Scale(self, *args):
        '''
        Scale the histogram
    
        It is enough to forward the call to self._rootHisto and
        self._shapeUncertainties, because it does not affect the
        relative uncertainties.
        '''
        self._rootHisto.Scale(*args)
        i = 0
        for (plus, minus) in self._shapeUncertainties.itervalues():
            plus.Scale(*args)
            minus.Scale(*args)
            i += 1
        return

    def ScaleVariationUncertainty(self, name, value):
        '''
        Scale a variation uncertainty
        
        It is enough to forward the call to self._rootHisto and
        self._shapeUncertainties, because it does not affect the
        relative uncertainties.
        '''
        if name not in self._shapeUncertainties.keys():
            raise Exception("Error: Cannot find '%s' in list of variation uncertainties (%s)!"%(name, ", ".join(map(str, self._shapeUncertainties.keys()))))
        (plus, minus) = self._shapeUncertainties[name]
        plus.Scale(value)
        minus.Scale(value)
        #for i in xrange(0, self._rootHisto.GetNbinsX()+2):
            #if abs(self._rootHisto.GetBinContent(i)) > 0.0:
                #oldValue = (plus.GetBinContent(i),self._rootHisto.GetBinContent(i))
                #plus.SetBinContent(i, plus.GetBinContent(i)*value)
                #minus.SetBinContent(i, minus.GetBinContent(i)*value)
                #print oldValue, plus.GetBinContent(i)
        self._shapeUncertainties[name] = (plus, minus)

    def Clone(self):
        '''
        Clone the histogram
    
        All contained histograms are also cloned. For all cloned
        histograms, th1.SetDirectory(0) is called.
        '''
        clone = RootHistoWithUncertainties(aux.Clone(self._rootHisto))
        for key, value in self._shapeUncertainties.iteritems():
            (plus, minus) = (aux.Clone(value[0]), aux.Clone(value[1]))
            clone._shapeUncertainties[key] = (plus, minus)
        clone._treatShapesAsStat = set(self._treatShapesAsStat)
        clone._flowBinsVisibleStatus = self._flowBinsVisibleStatus
        return clone

    def Delete(self):
        '''
        Delete all contained histograms
        '''
        if self._rootHisto != None:
            self._rootHisto.Delete()
        if self._shapeUncertainties != None:
            for (plus, minus) in self._shapeUncertainties.itervalues():
                plus.Delete()
                minus.Delete()
        self._rootHisto = None
        self._shapeUncertainties = None
        return

    def SetDirectory(self, *args):
        '''
        "Eats" SetDirectory() call for interface compatibility, i.e. do nothing
        '''
        pass


    def Debug(self):
        '''
        Print a lot information  for this RootHistoWithUncertainties object.
        Extremely useful for debugging
        '''
        def histoContents(h,):
            cList = []
            for i in range(0, h.GetNbinsX()+2):
                num = "%.2f" %  h.GetBinContent(i)
                if num.startswith("-"):
                    cList.append(num)
                else:
                    cList.append("+" +  num) #to help with aligning columns in table!
            return cList

        def graphErrors(g, High=False):
            eList = []

            # For-loop: All TGraph entries
            for i in range(0, g.GetN()):
                if High:
                    num = "%.2f" % g.GetErrorYhigh(i)
                else:
                    num = "%.2f" % g.GetErrorYlow(i)
                if num.startswith("-"):
                    eList.append(num)
                else:
                    eList.append("+" + num) #to help with aligning columns in table!
            return eList

        def histoErrors(h):
            eList = []
            for i in range(0, h.GetNbinsX()+2):
                num = "%.2f" %  h.GetBinError(i)
                if num.startswith("-"):
                    eList.append(nu,)
                else:
                    eList.append("+" + num) #to help with aligning columns in table!
            return eList

        
        # Definitions
        rows  = []
        align = "{:<40} {:<100}"
        hLine = 140*"="
        rows.append(hLine)
        rows.append( "{:^140}".format( sh_h + self.GetName() + sh_n) )
        rows.append(hLine)
        rows.append( align.format("Rate", "%.2f" % (self.getRate()) ) )
        rows.append( align.format("Rate_stat_uncert", "%.2f" % self.getRateStatUncertainty()) )
        rows.append( align.format("Rate_syst_uncert", "+%.2f -%.2f" % self.getRateSystUncertainty()) )
        rows.append( align.format("Nominal", histoContents(self._rootHisto)) )
        rows.append( align.format("Nominal_Error", histoErrors(self._rootHisto)) )
        
        # For-loop: All nuisances
        for key in self._shapeUncertainties.keys():
            (hPlus, hMinus) = self._shapeUncertainties[key]
            nuisUp   = "Uncert_%s_up"  % (key)
            contUp   = histoContents(hPlus)
            nuisDown = "Uncert_%s_down"% (key, )
            contDown = histoContents(hMinus)
            rows.append( align.format("%s" % (nuisUp), "%s" % (contUp)) )
            rows.append( align.format("%s" % (nuisDown), "%s" % (contDown)) )

#         # Now get the systematics
#         g     = graphErrors(self.getSystematicUncertaintyGraph())
#         sUp   = []
#         sDown = []
#         # For-loop: All TGraph entries
#         for i in range(0, g.GetN()):
#             sUp.append("%.2f" % g.GetErrorYhigh(i))
#             sDown.append("%.2f" % g.GetErrorYlow(i))
        rows.append( align.format("Rate_syst_uncert_up"  , graphErrors(self.getSystematicUncertaintyGraph(), True)) )
        rows.append( align.format("Rate_syst_uncert_down", graphErrors(self.getSystematicUncertaintyGraph(), False)) )

        #print ",%s"%sUp
        #print "rate_syst_uncert_down,%s\n"%sDown

        # Print all rows in a loop to get the table
        rows.append(hLine)
        for i, r in enumerate(rows, 1):
            self.Print(r, i==1)

        return

#================================================================================================ 
# Class Definition
#================================================================================================ 
class DatasetRootHistoBase:
    '''
    Base class for DatasetRootHisto classes (wrapper for TH1 histogram and the originating Dataset)
    
    The derived class must implement
    _normalizedHistogram()
    which should return the cloned and normalized TH1
    
    The wrapper holds the normalization of the histogram. User should
    set the current normalization scheme with the normalize* methods,
    and then get a clone of the original histogram, which is then
    normalized according to the current scheme.
    
    This makes the class very flexible with respect to the many
    possible normalizations user could want to apply within a plot
    script. The first use case was MC counters, which could be printed
    first normalized to the luminosity of the data, and also
    normalized to the cross section.
    
    The histogram wrapper classes also abstract the signel histogram, and
    mergeddata and MC histograms behind a common interface.
    '''
    def __init__(self, dataset):
        self.dataset = dataset
        self.name = dataset.getName()
        self.multiplication = None

    def getDataset(self):
        return self.dataset

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def isData(self):
        return self.dataset.isData()

    def isMC(self):
        return self.dataset.isMC()

    def isPseudo(self):
        return self.dataset.isPseudo()

    def isTH1(self):
        if isinstance(self, DatasetRootHisto):
            return self.histo.getRootHisto().InheritsFrom("TH1")
        elif isinstance(self, DatasetRootHistoMergedMC):
            return self._getSumHistogram().getRootHisto().InheritsFrom("TH1")
        elif isinstance(self, DatasetRootHistoMergedData):
            return self._getSumHistogram().getRootHisto().InheritsFrom("TH1")
        else:
            raise Exception("isTH1: Histogram has none of the types [DatasetRootHisto, DatasetRootHistoMergedMC, DatasetRootHistoMergedData]")
            
    def isTH2(self):
        if isinstance(self, DatasetRootHisto):
            return self.histo.getRootHisto().InheritsFrom("TH2")
        elif isinstance(self, DatasetRootHistoMergedMC):
            return self._getSumHistogram().getRootHisto().InheritsFrom("TH2")
        elif isinstance(self, DatasetRootHistoMergedData):
            return self._getSumHistogram().getRootHisto().InheritsFrom("TH2")
        else:
            raise Exception("isTH2: Histogram has none of the types [DatasetRootHisto, DatasetRootHistoMergedMC, DatasetRootHistoMergedData]")

    ## Get a clone of the wrapped histogram (TH1) normalized as requested.
    def getHistogram(self):
        h = self.getHistogramWithUncertainties()
        return h.getRootHisto()

    ## Get a clone of the wrapped histogram (RootHistoWithUncertainties) normalized as requested.
    def getHistogramWithUncertainties(self):
        h = self._normalizedHistogram()
        if h is None:
            return h

        if self.multiplication != None:
            h = _normalizeToFactor(h, self.multiplication)

        return h

    ## Scale the histogram bin values with a value.
    # 
    # \param value    Value to multiply with
    # 
    # h = h*value
    def scale(self, value):
        if self.multiplication == None:
            self.multiplication = value
        else:
            self.multiplication *= value

    ## \var dataset
    # dataset.Dataset object where the histogram originates
    ## \var name
    # Name of the histogram (default is dataset name)
    ## \var multiplication
    # Multiplication factor to be applied after normalization (if None, not applied)

## Wrapper for a single TH1 histogram and the corresponding Dataset.
class DatasetRootHisto(DatasetRootHistoBase):
    ## Constructor.
    # 
    # \param histo    RootHistoWithUncertainty wrapper object
    # \param dataset  Corresponding Dataset object
    # 
    # Sets the initial normalization to 'none'
    def __init__(self, histo, dataset):
        DatasetRootHistoBase.__init__(self, dataset)
        self.histo = histo
        self.normalization = "none"

    ## Get list of the bin labels of the histogram.
    def getBinLabels(self):
        if self.histo is None:
            return None
        return [x[0] for x in _histoToCounter(self.histo.getRootHisto())]

    def forEach(self, function, datasetRootHisto1=None):
        if datasetRootHisto1 != None:
            if not isinstance(datasetRootHisto1, DatasetRootHisto):
                raise Exception("datasetRootHisto1 must be of the type DatasetRootHisto")
            return [function(self, datasetRootHisto1)]
        else:
            return [function(self)]

    ## Modify the TH1 with a function
    #
    # \param function              Function taking the original TH1, and returning a new TH1. If newDatasetRootHisto is specified, function must take some other DatasetRootHisto object as an input too
    # \param newDatasetRootHisto   Optional, the other DatasetRootHisto object
    #
    # Needed for appending rows to counters from TTree, and for embedding normalization
    def modifyRootHisto(self, function, newDatasetRootHisto=None):
        if newDatasetRootHisto != None:
            if not isinstance(newDatasetRootHisto, DatasetRootHisto):
                raise Exception("newDatasetRootHisto must be of the type DatasetRootHisto")
            self.histo.setRootHisto(function(self.histo.getRootHisto(), newDatasetRootHisto.histo.getRootHisto()))
        else:
            self.histo.setRootHisto(function(self.histo.getRootHisto()))

    ## Return normalized clone of the original TH1
    def _normalizedHistogram(self):
        if self.histo is None:
            return None

        # Always return a clone of the original
        h = self.histo.Clone()
        #h.SetDirectory(0) # not needed anymore for RootHistoWithUncertainties
        h.SetName(h.GetName()+"_cloned")
        if self.normalization == "none":
            return h
        elif self.normalization == "toOne":
            return _normalizeToOne(h)

        # We have to normalize to cross section in any case
        h = _normalizeToFactor(h, self.dataset.getNormFactor())
        if self.normalization == "byCrossSection":
            return h
        elif self.normalization == "toLuminosity":
                return _normalizeToFactor(h, self.luminosity)
        else:
            raise Exception("Internal error")

    ## Set the normalization scheme to 'to one'.
    #
    # The histogram is normalized to unit area.
    def normalizeToOne(self):
        self.normalization = "toOne"

    ## Set the current normalization scheme to 'by cross section'.
    #
    # The histogram is normalized to the cross section of the
    # corresponding dataset. The normalization can be applied only
    # to MC histograms.
    def normalizeByCrossSection(self):
        if not self.dataset.isMC():
            raise Exception("Can't normalize non-MC histogram by cross section")
        self.normalization = "byCrossSection"

    ## Set the current normalization scheme to 'to luminosity'.
    #
    # \param lumi   Integrated luminosity in pb^-1 to normalize to
    #
    # The histogram is normalized first normalized to the cross
    # section of the corresponding dataset, and then to a given
    # luminosity. The normalization can be applied only to MC
    # histograms.
    def normalizeToLuminosity(self, lumi):
        if not self.dataset.isMC():
            raise Exception("Can't normalize non-MC histogram to luminosity")
        self.normalization = "toLuminosity"
        self.luminosity = lumi
    
    ## \var histo
    # Holds the unnormalized ROOT histogram (TH1)
    ## \var normalization
    # String representing the current normalization scheme


## Base class for merged data/Mc histograms and the corresponding datasets
class DatasetRootHistoCompoundBase(DatasetRootHistoBase):
    ## Constructor.
    # 
    # \param histoWrappers   List of dataset.DatasetRootHisto objects to merge
    # \param mergedDataset   The corresponding dataset.DatasetMerged object
    def __init__(self, histoWrappers, mergedDataset):
        DatasetRootHistoBase.__init__(self, mergedDataset)
        self.histoWrappers = histoWrappers
        self.normalization = "none"

    ## Get list of the bin labels of the first of the merged histogram.
    def getBinLabels(self):
        for drh in self.histoWrappers:
            ret = drh.getBinLabels()
            if ret is not None:
                return ret
        return None

   ## Calculate the sum of the histograms (i.e. merge).
   # 
   # Intended to be called from the deriving classes
    def _getSumHistogram(self):
        # Loop until we have a real RootHistoWithUncertainties (not None)
        hsum = None
        for i, drh in enumerate(self.histoWrappers):
            hsum = drh.getHistogramWithUncertainties() # we get a clone
            if hsum is not None:
                break

        for h in self.histoWrappers[i+1:]:
            histo = h.getHistogramWithUncertainties()
            if histo.GetNbinsX() != hsum.GetNbinsX():
                hh = nSuccess = 0
                if len(hsum.getRootHisto().GetXaxis().GetBinLabel(1)) > 0:
                    # Try to recover for histograms with bin labels, i.e. counters
                    for i in range(1,hsum.getRootHisto().GetNbinsX()+1):
                        for j in range(1,histo.getRootHisto().GetNbinsX()+1):
                            if len(hsum.getRootHisto().GetXaxis().GetBinLabel(i)) > 0:
                                if hsum.getRootHisto().GetXaxis().GetBinLabel(i) == histo.getRootHisto().GetXaxis().GetBinLabel(j):
                                    nSuccess += 1
                                    hsum.getRootHisto().SetBinContent(i, hsum.getRootHisto().GetBinContent(i) + histo.getRootHisto().GetBinContent(j));
                                    # Ignore uncertainties
                if nSuccess == 0:
                    raise Exception("Histogram '%s' from datasets '%s' and '%s' have different binnings: %d vs. %d" % (hsum.GetName(), self.histoWrappers[i].getDataset().getName(), h.getDataset().getName(), hsum.GetNbinsX(), histo.GetNbinsX()))
            else:
                hsum.Add(histo)
            histo.Delete()
        return hsum

    ## \var histoWrappers
    # List of underlying dataset.DatasetRootHisto objects
    ## \var normalization
    # String representing the current normalization scheme


## Wrapper for a merged TH1 histograms from data and the corresponding Datasets.
#
# The merged data histograms can only be normalized 'to one'.
#
# \see dataset.DatasetRootHisto class.
class DatasetRootHistoMergedData(DatasetRootHistoCompoundBase):
    ## Constructor.
    # 
    # \param histoWrappers   List of dataset.DatasetRootHisto objects to merge
    # \param mergedDataset   The corresponding dataset.DatasetMerged object
    # 
    # The constructor checks that all histoWrappers are data, and
    # are not yet normalized.
    def __init__(self, histoWrappers, mergedDataset):
        DatasetRootHistoCompoundBase.__init__(self, histoWrappers, mergedDataset)
        for h in self.histoWrappers:
            if not h.isData():
                raise Exception("Histograms to be merged must come from data (%s is not data)" % h.getDataset().getName())
            if h.normalization != "none":
                raise Exception("Histograms to be merged must not be normalized at this stage")
            if h.multiplication != None:
                raise Exception("Histograms to be merged must not be multiplied at this stage")

    def forEach(self, function, datasetRootHisto1=None):
        ret = []
        if datasetRootHisto1 != None:
            if not isinstance(datasetRootHisto1, DatasetRootHistoMergedData):
                raise Exception("datasetRootHisto1 must be of the type DatasetRootHistoMergedData")
            if not len(self.histoWrappers) == len(datasetRootHisto1.histoWrappers):
                raise Exception("len(self.histoWrappers) != len(datasetrootHisto1.histoWrappers), %d != %d" % len(self.histoWrappers), len(datasetRootHisto1.histoWrappers))
            
            for i, drh in enumerate(self.histoWrappers):
                ret.extend(drh.forEach(function, datasetRootHisto1.histoWrappers[i]))
        else:
            for drh in self.histoWrappers:
                ret.extend(drh.forEach(function))
        return ret
        

    ## Modify the TH1 with a function
    #
    # \param function             Function taking the original TH1, and returning a new TH1. If newDatasetRootHisto is specified, function must take some other DatasetRootHisto object as an input too
    # \param newDatasetRootHisto  Optional, the other DatasetRootHisto object, must be the same type and contain same number of DatasetRootHisto objects
    #
    # Needed for appending rows to counters from TTree, and for embedding normalization
    def modifyRootHisto(self, function, newDatasetRootHisto=None):
        if newDatasetRootHisto != None:
            if not isinstance(newDatasetRootHisto, DatasetRootHistoMergedData):
                raise Exception("newDatasetRootHisto must be of the type DatasetRootHistoMergedData")
            if not len(self.histoWrappers) == len(newDatasetRootHisto.histoWrappers):
                raise Exception("len(self.histoWrappers) != len(newDatasetrootHisto.histoWrappers), %d != %d" % len(self.histoWrappers), len(newDatasetRootHisto.histoWrappers))
            
            for i, drh in enumerate(self.histoWrappers):
                drh.modifyRootHisto(function, newDatasetRootHisto.histoWrappers[i])
        else:
            for i, drh in enumerate(self.histoWrappers):
                drh.modifyRootHisto(function)

    ## Set the current normalization scheme to 'to one'.
    #
    # The histogram is normalized to unit area.
    def normalizeToOne(self):
        self.normalization = "toOne"

    ## Merge the histograms and apply the current normalization.
    # 
    # The returned histogram is a clone, so client code can do
    # anything it wishes with it.
    def _normalizedHistogram(self):
        hsum = self._getSumHistogram()
        if hsum is None:
            return None

        if self.normalization == "toOne":
            return _normalizeToOne(hsum)
        else:
            return hsum

## Wrapper for a merged TH1 histograms from pseudo and the corresponding Datasets.
#
# The merged pseudo histogramgs can only be normalized 'to one'.
#
# Works as DatasetRootHistoMergedData, except can be constructed only
# from pseudo datasets.
#
# \see dataset.DatasetRootHisto class.
class DatasetRootHistoMergedPseudo(DatasetRootHistoMergedData):
    ## Constructor.
    #
    # \param histoWrappers   List of dataset.DatasetRootHisto objects to merge
    # \param mergedDataset   The corresponding dataset.DatasetMerged object
    #
    # The constructor checks that all histoWrappers are data, and
    # are not yet normalized.
    def __init__(self, histoWrappers, mergedDataset):
        DatasetRootHistoCompoundBase.__init__(self, histoWrappers, mergedDataset)
        for h in self.histoWrappers:
            if not h.isPseudo():
                raise Exception("Histograms to be merged must come from pseudo (%s is not pseudo)" % h.getDataset().getName())
            if h.normalization != "none":
                raise Exception("Histograms to be merged must not be normalized at this stage")
            if h.multiplication != None:
                raise Exception("Histograms to be merged must not be multiplied at this stage")

## Wrapper for a merged TH1 histograms from MC and the corresponding Datasets.
# 
# See also the documentation of DatasetRootHisto class.
class DatasetRootHistoMergedMC(DatasetRootHistoCompoundBase):
    ## Constructor.
    # 
    # \param histoWrappers   List of dataset.DatasetRootHisto objects to merge
    # \param mergedDataset   The corresponding dataset.DatasetMerged object
    # 
    # The constructor checks that all histoWrappers are MC, and are
    # not yet normalized.
    def __init__(self, histoWrappers, mergedDataset):
        DatasetRootHistoCompoundBase.__init__(self, histoWrappers, mergedDataset)
        for h in self.histoWrappers:
            if not h.isMC():
                raise Exception("Histograms to be merged must come from MC")
            if h.normalization != "none":
                raise Exception("Histograms to be merged must not be normalized at this stage")
            if h.multiplication != None:
                raise Exception("Histograms to be merged must not be multiplied at this stage")

    def forEach(self, function, datasetRootHisto1=None):
        ret = []
        if datasetRootHisto1 != None:
            if not isinstance(datasetRootHisto1, DatasetRootHistoMergedMC):
                raise Exception("datasetRootHisto1 must be of the type DatasetRootHistoMergedMC")
            if not len(self.histoWrappers) == len(datasetRootHisto1.histoWrappers):
                raise Exception("len(self.histoWrappers) != len(datasetrootHisto1.histoWrappers), %d != %d" % len(self.histoWrappers), len(datasetRootHisto1.histoWrappers))
            
            for i, drh in enumerate(self.histoWrappers):
                ret.extend(drh.forEach(function, datasetRootHisto1.histoWrappers[i]))
        else:
            for drh in self.histoWrappers:
                ret.extend(drh.forEach(function))
        return ret

    ## Modify the TH1 with a function
    #
    # \param function             Function taking the original TH1, and returning a new TH1. If newDatasetRootHisto is specified, function must take some other DatasetRootHisto object as an input too
    # \param newDatasetRootHisto  Optional, the other DatasetRootHisto object, must be the same type and contain same number of DatasetRootHisto objects
    #
    # Needed for appending rows to counters from TTree, and for embedding normalization
    def modifyRootHisto(self, function, newDatasetRootHisto=None):
        if newDatasetRootHisto != None:
            if not isinstance(newDatasetRootHisto, DatasetRootHistoMergedMC):
                raise Exception("newDatasetRootHisto must be of the type DatasetRootHistoMergedMC")
            if not len(self.histoWrappers) == len(newDatasetRootHisto.histoWrappers):
                raise Exception("len(self.histoWrappers) != len(newDatasetrootHisto.histoWrappers), %d != %d" % len(self.histoWrappers), len(newDatasetRootHisto.histoWrappers))
            
            for i, drh in enumerate(self.histoWrappers):
                drh.modifyRootHisto(function, newDatasetRootHisto.histoWrappers[i])
        else:
            for i, drh in enumerate(self.histoWrappers):
                drh.modifyRootHisto(function)

    ## Set the current normalization scheme to 'to one'.
    # 
    # The histogram is normalized to unit area.
    # 
    # Sets the normalization of the underlying
    # dataset.DatasetRootHisto objects to 'by cross section' in order
    # to be able to sum them. The normalization 'to one' is then done
    # for the summed histogram.
    def normalizeToOne(self):
        self.normalization = "toOne"
        for h in self.histoWrappers:
            h.normalizeByCrossSection()

    ## Set the current normalization scheme to 'by cross section'.
    # 
    # The histogram is normalized to the cross section of the
    # corresponding dataset.
    # 
    # Sets the normalization of the underlying
    # dataset.DatasetRootHisto objects to 'by cross section'. Then
    # they can be summed directly, and the summed histogram is
    # automatically correctly normalized to the total cross section of
    # the merged dataset.Dataset objects.
    def normalizeByCrossSection(self):
        self.normalization = "byCrossSection"
        for h in self.histoWrappers:
            h.normalizeByCrossSection()

    ## Set the current normalization scheme to 'to luminosity'.
    # 
    # \param lumi   Integrated luminosity in pb^-1 to normalize to
    # 
    # The histogram is normalized first normalized to the cross
    # section of the corresponding dataset, and then to a given
    # luminosity.
    # 
    # Sets the normalization of the underlying
    # dataset.DatasetRootHisto objects to 'to luminosity'. Then they
    # can be summed directly, and the summed histogram is
    # automatically correctly normalized to the given integrated
    # luminosity. """
    def normalizeToLuminosity(self, lumi):
        self.normalization = "toLuminosity"
        for h in self.histoWrappers:
            h.normalizeToLuminosity(lumi)

    ## Merge the histograms and apply the current normalization.
    # 
    # The returned histogram is a clone, so client code can do
    # anything it wishes with it.
    # 
    # The merged MC histograms must be normalized in some way,
    # otherwise they can not be summed (or they can be, but the
    # contents of the summed histogram doesn't make any sense as it
    # is just the sum of the MC events of the separate datasets
    # which in general have different cross sections).
    def _normalizedHistogram(self):
        if self.normalization == "none":
            raise Exception("Merged MC histograms must be normalized to something!")

        hsum = self._getSumHistogram()
        if hsum is None:
            return hsum

        if self.normalization == "toOne":
            return _normalizeToOne(hsum)
        else:
            return hsum

    ## \var histoWrappers
    # List of underlying dataset.DatasetRootHisto objects
    ## \var normalization
    # String representing the current normalization scheme


## Wrapper for a added TH1 histograms from MC and the corresponding Datasets.
#
# Here "Adding" is like merging, but for datasets which have the same
# cross section, and are split to two datasets just for increased
# statistics. Use case is inclusive W+jets in Summer12, which is split
# into two datasets.
# 
# See also the documentation of DatasetRootHisto class.
class DatasetRootHistoAddedMC(DatasetRootHistoCompoundBase):
    ## Constructor.
    # 
    # \param histoWrappers   List of dataset.DatasetRootHisto objects to merge
    # \param addedDataset   The corresponding dataset.DatasetMerged object
    # 
    # The constructor checks that all histoWrappers are MC, and are
    # not yet normalized.
    def __init__(self, histoWrappers, addedDataset):
        DatasetRootHistoBase.__init__(self, addedDataset)
        self.histoWrappers = histoWrappers
        self.normalization = "none"
        for h in self.histoWrappers:
            if not h.isMC():
                raise Exception("Histograms to be added must come from MC")
            if h.normalization != "none":
                raise Exception("Histograms to be added must not be normalized at this stage")
            if h.multiplication != None:
                raise Exception("Histograms to be added must not be multiplied at this stage")

    def isData(self):
        return False

    def isMC(self):
        return True

    def forEach(self, function, datasetRootHisto1=None):
        ret = []
        if datasetRootHisto1 != None:
            if not isinstance(datasetRootHisto1, DatasetRootHistoAddedMC):
                raise Exception("datasetRootHisto1 must be of the type DatasetRootHistoAddedMC")
            if not len(self.histoWrappers) == len(datasetRootHisto1.histoWrappers):
                raise Exception("len(self.histoWrappers) != len(datasetrootHisto1.histoWrappers), %d != %d" % len(self.histoWrappers), len(datasetRootHisto1.histoWrappers))
            
            for i, drh in enumerate(self.histoWrappers):
                ret.extend(drh.forEach(function, datasetRootHisto1.histoWrappers[i]))
        else:
            for drh in self.histoWrappers:
                ret.extend(drh.forEach(function))
        return ret

    ## Modify the TH1 with a function
    #
    # \param function             Function taking the original TH1, and returning a new TH1. If newDatasetRootHisto is specified, function must take some other DatasetRootHisto object as an input too
    # \param newDatasetRootHisto  Optional, the other DatasetRootHisto object, must be the same type and contain same number of DatasetRootHisto objects
    #
    # Needed for appending rows to counters from TTree, and for embedding normalization
    def modifyRootHisto(self, function, newDatasetRootHisto=None):
        if newDatasetRootHisto != None:
            if not isinstance(newDatasetRootHisto, DatasetRootHistoAddedMC):
                raise Exception("newDatasetRootHisto must be of the type DatasetRootHistoAddedMC")
            if not len(self.histoWrappers) == len(newDatasetRootHisto.histoWrappers):
                raise Exception("len(self.histoWrappers) != len(newDatasetrootHisto.histoWrappers), %d != %d" % len(self.histoWrappers), len(newDatasetRootHisto.histoWrappers))
            
            for i, drh in enumerate(self.histoWrappers):
                drh.modifyRootHisto(function, newDatasetRootHisto.histoWrappers[i])
        else:
            for i, drh in enumerate(self.histoWrappers):
                drh.modifyRootHisto(function)

    ## Set the current normalization scheme to 'to one'.
    # 
    # The histogram is normalized to unit area.
    # 
    # Sets the normalization of the underlying
    # dataset.DatasetRootHisto objects to 'by cross section' in order
    # to be able to sum them. The normalization 'to one' is then done
    # for the summed histogram.
    def normalizeToOne(self):
        self.normalization = "toOne"

    ## Set the current normalization scheme to 'by cross section'.
    # 
    # The histogram is normalized to the cross section of the
    # corresponding dataset.
    # 
    # Sets the normalization of the underlying
    # dataset.DatasetRootHisto objects to 'by cross section'. Then
    # they can be summed directly, and the summed histogram is
    # automatically correctly normalized to the total cross section of
    # the merged dataset.Dataset objects.
    def normalizeByCrossSection(self):
        self.normalization = "byCrossSection"

    ## Set the current normalization scheme to 'to luminosity'.
    # 
    # \param lumi   Integrated luminosity in pb^-1 to normalize to
    # 
    # The histogram is normalized first normalized to the cross
    # section of the corresponding dataset, and then to a given
    # luminosity.
    # 
    # Sets the normalization of the underlying
    # dataset.DatasetRootHisto objects to 'to luminosity'. Then they
    # can be summed directly, and the summed histogram is
    # automatically correctly normalized to the given integrated
    # luminosity. """
    def normalizeToLuminosity(self, lumi):
        self.normalization = "toLuminosity"
        self.luminosity = lumi

    ## Merge the histograms and apply the current normalization.
    # 
    # The returned histogram is a clone, so client code can do
    # anything it wishes with it.
    # 
    # The merged MC histograms must be normalized in some way,
    # otherwise they can not be summed (or they can be, but the
    # contents of the summed histogram doesn't make any sense as it
    # is just the sum of the MC events of the separate datasets
    # which in general have different cross sections).
    def _normalizedHistogram(self):
        hsum = self._getSumHistogram()

        if self.normalization == "none":
            return hsum
        elif self.normalization == "toOne":
            return _normalizeToOne(hsum)

        # We have to normalize to cross section in any case
        hsum = _normalizeToFactor(hsum, self.dataset.getNormFactor())
        if self.normalization == "byCrossSection":
            return hsum
        elif self.normalization == "toLuminosity":
                return _normalizeToFactor(hsum, self.luminosity)
        else:
            raise Exception("Internal error, got normalization %s" % self.normalization)

    ## \var histoWrappers
    # List of underlying dataset.DatasetRootHisto objects
    ## \var normalization
    # String representing the current normalization scheme

class AnalysisNotFoundException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class HistogramNotFoundException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

## Dataset class for histogram access from one ROOT file.
# 
# The default values for cross section/luminosity are read from
# 'configInfo/configInfo' histogram (if it exists). The data/MC
# datasets are differentiated by the existence of 'crossSection'
# (for MC) and 'luminosity' (for data) keys in the histogram. Reads
# the dataVersion from 'configInfo/dataVersion' and deduces whether
# the dataset is data/MC from it.
#
# \see dataset.DatasetMerged for merging multiple Dataset objects
# (either data or MC) to one logical dataset (e.g. all data datasets
# to one dataset, all QCD pThat bins to one dataset)
class Dataset:
    ## Constructor.
    # 
    # \param name              Name of the dataset (can be anything)
    # \param tfiles            List of ROOT.TFile objects for the dataset
    # \param analysisName      Base part of the analysis directory name
    # \param searchMode        String for search mode
    # \param dataEra           String for data era
    # \param optimizationMode  String for optimization mode (optional)
    # \param systematicVariation String for systematic variation (optional)
    # \param weightedCounters  If True, pick the counters from the 'weighted' subdirectory
    # \param counterDir        Name of the directory in the ROOT file for
    #                          event counter histograms. If None is given,
    #                          is assumed that the dataset has no counters.
    #                          This also means that the histograms from this
    #                          dataset can not be normalized unless the
    #                          number of all events is explictly set with
    #                          setNAllEvents() method. Note that this
    #                          directory should *not* point to the 'weighted'
    #                          subdirectory, but to the top-level counter
    #                          directory. The weighted counters are taken
    #                          into account with \a useWeightedCounters
    #                          argument
    # \param useAnalysisNameOnly Should the analysis directory be
    #                            inferred only from analysisName?
    # \param availableSystematicVariationSources List of strings of the systematic variations
    #                                      available on the ROOT file (without the "Plus"/"Minus" postfix)
    # \param enableSystematicVariationForData Add \a systematicVariation to directory name also for data (needed for embedding)
    # \param setCrossSectionAutomatically Try to set cross section automatically if the dataset is MC (default True)
    #
    # 
    # Opens the ROOT file, reads 'configInfo/configInfo' histogram
    # (if it exists), and reads the main event counter
    # ('counterDir/counters') if counterDir is not None. Reads also
    # 'configInfo/dataVersion' TNamed.
    #
    # With the v44_4 pattuples we improved the "Run2011 A vs. B vs AB"
    # workflow such that for MC we run analyzers for all data eras.
    # This means that the TDirectory names will be different for data
    # and MC, such that in MC the era name is appended to the
    # directory name. 
    #
    # The final directory name is (if \a useAnalysisNameOnly is False)
    # data: analysisName+searchMode+optimizationMode(+systematicVariation)
    # MC:   analysisName+searchMode+dataEra+optimizationMode+systematicVariation
    # For data, \a systematicVariation is added only if \a enableSystematicVariationForData is True
    #
    # The \a useAnalysisNameOnly parameter is needed e.g. for ntuples
    # which store the era-specific weights to the tree itself, and
    # therefore the 
    def __init__(self, name, tfiles, analysisName,
                 searchMode=None, dataEra=None, optimizationMode=None, systematicVariation=None,
                 weightedCounters=True, counterDir="counters", useAnalysisNameOnly=False, availableSystematicVariationSources=[], enableSystematicVariationForData=False, setCrossSectionAutomatically=True):
        self.rawName = name
        self.name = name
        self.files = tfiles
        if len(self.files) == 0:
            raise Exception("Expecting at least one TFile, jot 0")

        # Now this is really an uhly hack
        self._setBaseDirectory(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(self.files[0].GetName())))))
        # Extract configInfo and dataVersion, check for consistency
        # that all files have the same values
        self.info = None
        self.dataVersion = None
        def assertInfo(refInfo, newInfo, refFile, newFile, name):
            for key, value in refInfo.iteritems():
                valnew = info[key]
                if isinstance(value, basestring):
                    if value == valnew:
                        continue
                    raise Exception("Mismatched values in %s, label %s, got %s from file %s, and %s from file %s" % (name, key, value, refFile.GetName(), valnew, newFile.GetName()))
                if valnew == 0 and value == 0:
                    return
                if abs(value-valnew)/max(value, valnew) > 0.001:
                    raise Exception("Mismatched values in %s, label %s, got %f from file %s, and %f from file %s" % (name, key, value, refFile.GetName(), valnew, newFile.GetName()))
        def addDirContentsToDict(tdirectory, dictionary):
            content = aux.listDirectoryContent(tdirectory, lambda key: key.GetClassName() == "TNamed" and key.GetName() not in ["dataVersion", "parameterSet"])
            for name in content:
                if name not in dictionary:
                    dictionary[name] = aux.Get(tdirectory, name).GetTitle()
        
        for f in self.files:
            if not f.IsOpen():
                raise Exception("File %s of dataset %s has been closed! Maybe this Dataset has been removed without 'close=False'?" % (f.GetName(), self.name))
            configInfo = aux.Get(f, "configInfo")
            if configInfo == None:
                raise Exception("configInfo directory is missing from file %s" % f.GetName())

            info = aux.Get(configInfo, "configinfo")
            if info != None:
                info = _rescaleInfo(_histoToDict(info))
                if "energy" in info:
                    info["energy"] = str(int(round(info["energy"])))
                addDirContentsToDict(configInfo, info)
            else:
                info = {}
            if self.info is None:
                self.info = info
            else:
                assertInfo(self.info, info, self.files[0], f, "configInfo/configinfo")

            dataVersion = aux.Get(configInfo, "dataVersion")
            if dataVersion == None:
                raise Exception("Unable to determine dataVersion for dataset %s from file %s" % (name, f.GetName()))
            if self.dataVersion is None:
                self.dataVersion = dataVersion.GetTitle()
            else:
                if self.dataVersion != dataVersion.GetTitle():
                    raise Exception("Mismatched values in configInfo/dataVersion, got %s from file %s, and %s from file %s" % (self.dataVersion, self.files[0].GetName(), dataVersion.GetTitle(), f.GetName()))

        self._isData = "data" in self.dataVersion
        self._is2017 = "2017" in self.dataVersion
        self._is2016 = "2016" in self.dataVersion or "80X" in self.dataVersion
        self._is2018 = "2018" in self.dataVersion
        self._isPseudo = "pseudo" in self.dataVersion
        self._isMC = not (self._isData or self._isPseudo)
        self._weightedCounters = weightedCounters

        self._analysisName = analysisName
        self._searchMode = searchMode
        self._dataEra = dataEra
        self._optimizationMode = optimizationMode
        self._systematicVariation = systematicVariation
        self._useAnalysisNameOnly = useAnalysisNameOnly
        self._availableSystematicVariationSources = availableSystematicVariationSources
        self._enableSystematicVariationForData = enableSystematicVariationForData
        self._setCrossSectionAutomatically = setCrossSectionAutomatically

        self._analysisDirectoryName = self._analysisName
        if not self._useAnalysisNameOnly:
            if self._searchMode is not None:
                self._analysisDirectoryName += "_"+self._searchMode
            #if (self.isMC() or self.isPseudo()) and self._dataEra is not None:
            if self._dataEra is not None:
                self._analysisDirectoryName += "_"+self._dataEra
            if self._optimizationMode is not None:
                self._analysisDirectoryName += "_"+self._optimizationMode
            if (((self.isMC() or self.isPseudo()) or (self.isData() and enableSystematicVariationForData)) and
                self._systematicVariation is not None):
                self._analysisDirectoryName += "_"+self._systematicVariation

        # Convert to string (otherwise causes problems in certain PYTHON/ROOT envs)
        self._analysisDirectoryName = str(self._analysisDirectoryName)

        # Check that analysis directory exists
        for f in self.files:
            if aux.Get(f, self._analysisDirectoryName) == None:
                raise AnalysisNotFoundException("Analysis directory '%s' does not exist in file '%s'" % (self._analysisDirectoryName, f.GetName()))
        self._analysisDirectoryName += "/"

        # Update info from analysis directory specific histogram, if one exists
        realDirName = self._translateName("configInfo")
        if aux.Get(self.files[0], realDirName) != None: # important to use !=
            updateInfo = None
            for f in self.files:
                d = aux.Get(f, realDirName)
                if d == None:
                    raise Exception("%s directory is missing from file %s, it was in %s" % (realDirName, f.GetName(), self.files[0].GetName()))
                info = {}
                h = aux.Get(d, "configinfo")
                if h != None:
                    info = _rescaleInfo(_histoToDict(aux.Get(d, "configinfo")))
                addDirContentsToDict(aux.Get(f, realDirName), info)
                if updateInfo == None:
                    updateInfo = info
                else:
                    assertInfo(updateInfo, info, self.files[0], f, realDirName+"/configinfo")
            if "energy" in updateInfo:
                #raise Exception("You may not set 'energy' in analysis directory specific configinfo histogram. Please fix %s." % realName)
                print "WARNING: 'energy' has been set in analysis directory specific configinfo histogram (%s), it will be ignored. Please fix your pseudomulticrab code." % (realName+"/configinfo")
                del updateInfo["energy"]
            self.info.update(updateInfo)

        self._unweightedCounterDir = counterDir
        if counterDir is not None:
            self._weightedCounterDir = counterDir + "/weighted"
            self._readCounters()

        # Update Nallevents to weighted one
        if "isPileupReweighted" in self.info and self.info["isPileupReweighted"]:
            #print "%s: is pileup-reweighted, calling updateNAllEventsToPUWeighted()" % self.name
            self.updateNAllEventsToPUWeighted()

        # Set cross section, if MC and we know the energy
        if self.isMC() and setCrossSectionAutomatically:
            if "energy" in self.info:
                crosssection.setBackgroundCrossSectionForDataset(self, quietMode=(self._systematicVariation != None or self._optimizationMode != None))
            else:
                print "%s is MC but has no energy set in configInfo/configinfo, not setting its cross section automatically" % self.name

        # For some reason clearing the in-memory representations of
        # the files increases the reading (object lookup?) performance
        # when reading from many analysis directories in a single
        # script.
        for f in self.files:
            # Skip this step if on OS X (crashes)
            if _platform == "darwin":
                #print "=== dataset.py: Skip the clearing the in-memory representations of the files in macOS (causes crash)"
                continue
#            else:
#                f.Clear() # uncommented by Santeri in order to avoid segmentation faults

    ## Close the files
    #
    # Can be useful when opening very many files in order to reduce
    # the memory footprint and not hit the limit of number of open
    # files
    def close(self):
        for f in self.files:
            f.Close("R")
            f.Delete()
        self.files = []

    ## Clone the Dataset object
    # 
    # Nothing is shared between the returned copy and this object,
    # except the ROOT file object
    #
    # Use case is creative dataset manipulations, e.g. copying ttbar
    # to another name and scaling the cross section by the BR(t->H+)
    # while also keeping the original ttbar with the original SM cross
    # section.
    def deepCopy(self):
        d = Dataset(self.rawName, self.files, self._analysisName, self._searchMode, self._dataEra, self._optimizationMode, self._systematicVariation, self._weightedCounters, self._unweightedCounterDir, self._useAnalysisNameOnly, self._availableSystematicVariationSources, self._enableSystematicVariationForData, self._setCrossSectionAutomatically)
        d.info.update(self.info)
        d.nAllEvents = self.nAllEvents
        d.name = self.name
        return d

    def getAnalysisName(self):
        return self._analysisName

    def getSearchMode(self):
        if self._searchMode is None:
            return ""
        return self._searchMode

    def getDataEra(self):
        if self._dataEra is None:
            return ""
        return self._dataEra

    def getOptimizationMode(self):
        if self._optimizationMode is None:
            return ""
        return self._optimizationMode

    def getSystematicVariation(self):
        if self._systematicVariation is None:
            return ""
        return self._systematicVariation

    ## Translate a logical name to a physical name in the file
    #
    # \param name            Name to translate
    # \param analysisPostfix Postfix to the current analysis directory
    #                        name to read the objects from. You better
    #                        know what you're doing.
    #
    # If name starts with slash ('/'), it is interpreted as a absolute
    # path within the ROOT file.
    def _translateName(self, name, analysisPostfix=""):
        if len(name) > 0 and name[0] == '/':
            return name[1:]
        else:
            ret = self._analysisDirectoryName
            if analysisPostfix != "":
                ret = ret.replace("/", analysisPostfix+"/")
            ret += name
            if ret[-1] == "/":
                return ret[0:-1]
            return ret

    ## Get the ParameterSet stored in the ROOT file
    def getParameterSet(self):
        # (objs, realNames) = self.getRootObjects("configInfo/parameterSet") #obsolete? alexandros 12/07/2017
        (objs, realNames) = self.getRootObjects("config")
        return objs[0].GetTitle()        

    def getDataVersion(self):
        return self.dataVersion

    def getAvailableSystematicVariationSources(self):
        return self._availableSystematicVariationSources

    ## Get ROOT histogram
    #
    # \param name    Path of the ROOT histogram relative to the analysis
    #                root directory
    # \param kwargs  Keyword arguments, forwarded to getRootObjects()
    #
    # \return pair (\a histogram, \a realName)
    #
    # If name starts with slash ('/'), it is interpreted as a absolute
    # path within the ROOT file.
    #
    # If dataset consists of multiple files, the histograms are added
    # with the ROOT.TH1.Add() method.
    # 
    # If dataset.TreeDraw object is given (or actually anything with
    # draw() method), the draw() method is called by giving the
    # Dataset object as parameters. The draw() method is expected to
    # return a TH1 which is then returned.
    def getRootHisto(self, name, **kwargs):
        if hasattr(name, "draw"):
            if len(kwargs) > 0:
                print >>sys.stderr, "WARNING: You gave keyword arguments to getDatasetRootHisto() together with object with draw() method. The keyword arguments are not passed to the draw() call. This may or may not be what you want."
            h = name.draw(self)
            realName = None
        else:
            (histos, realName) = self.getRootObjects(name, **kwargs)
            if len(histos) == 1:
                h = histos[0]
            else:
                h = histos[0]
                h = aux.Clone(h, h.GetName()+"_cloned")
                for h2 in histos[1:]:
                    h.Add(h2)
    
        return (h, realName)

    ## Create ROOT TChain
    # 
    # \param name    Path of the ROOT TTree relative to the analysis
    #                root directory
    # \param kwargs  Keyword arguments, forwarded to _translateName()
    #
    # \return pair (ROOT.TChain, \a realName)
    #
    # If name starts with slash ('/'), it is interpreted as a absolute
    # path within the ROOT file.
    def createRootChain(self, treeName, **kwargs):
        realName = self._translateName(treeName, **kwargs)
        chain = ROOT.TChain(realName)
        for f in self.files:
            chain.Add(f.GetName())
        return (chain, realName)

    ## Get arbitrary ROOT object from the file
    #
    # \param name    Path of the ROOT object relative to the analysis
    #                root directory
    # \param kwargs  Keyword arguments, forwarded to getRootObjects()
    #
    # \return pair (\a object, \a realName)
    #
    # If name starts with slash ('/'), it is interpreted as a absolute
    # path within the ROOT file.
    #
    # If the dataset consists of multiple files, raise an Exception.
    # User should use getRootObjects() method instead.
    def getRootObject(self, name, **kwargs):
        if len(self.files) > 1:
            raise Exception("You asked for a single ROOT object, but the Dataset %s consists of multiple ROOT files. You should call getRootObjects() instead, and deal with the multiple objects by yourself.")
        (lst, realName) = self.getRootObjects(name, **kwargs)
        return (lst[0], realName)

    ## Get list of arbitrary ROOT objects from the file
    #
    # \param name    Path of the ROOT object relative to the analysis
    #                root directory
    # \param kwargs  Keyword arguments, forwarded to _translateName()
    #
    # \return pair (\a list, \a realName), where \a list is the list
    #         of ROOT objects, one per file, and \a realName is the
    #         physical name of the objects
    #
    # If name starts with slash ('/'), it is interpreted as a absolute
    # path within the ROOT file.
    def getRootObjects(self, name, **kwargs):
        realName = self._translateName(name, **kwargs)
        ret = []
        if len(self.files) == 0:
            raise Exception("Trying to read object %s from dataset %s, but the file is already closed!" % (name, self.name))

        for f in self.files:
            # Convert to string (otherwise causes problems in certain PYTHON/ROOT envs)
            o = aux.Get(f, str(realName))
            # below it is important to use '==' instead of 'is',
            # because null TObject == None, but is not None
            if o == None:
                raise HistogramNotFoundException("Unable to find object '%s' (requested '%s') from file '%s'" % (realName, name, self.files[0].GetName()))

            ret.append(o)
        return (ret, realName)

    ## Read counters
    def _readCounters(self):
        self.counterDir = self._unweightedCounterDir
        self.nAllEventsWeighted = None # value to be read from counters (if possible)
        self.nAllEventsUnweighted = None  # value to be read from counters (if possible)

        # Initialize for normalization check based on weighted counters
        normalizationCheckStatus = True
        nAllEvts  = 0
        nPUReEvts = 0

        # Try to read unweighted counters
        try:
            (counter, realName) = self.getRootHisto(self.counterDir+"/counter") #unweighted
            ctr = _histoToCounter(counter)
            self.nAllEventsUnweighted = ctr[0][1].value() # first counter, second element of the tuple, corresponds to ttree: skimCounterAll
            if _debugCounters: # Debug print
                print "DEBUG: Unweighted counters, Dataset name: "+self.getName()
                for i in range(counter.GetNbinsX()+1):
                    if counter.GetXaxis().GetBinLabel(i) == "Base::AllEvents":
                        allEventsBin = i
                    print "bin %d, label: %s, content: = %s"%(i, counter.GetXaxis().GetBinLabel(i), counter.GetBinContent(i))
                print "\n\n"
            # Normalization check (to spot e.g. PROOF problems), based on weighted counters
            (counter, realName) = self.getRootHisto(self.counterDir+"/weighted/counter") # weighted
            allEventsBin = None
            for i in range(counter.GetNbinsX()+1):
                if counter.GetXaxis().GetBinLabel(i) == "Base::AllEvents":
                    allEventsBin = i
            if allEventsBin != None and allEventsBin > 0:
                if counter.GetBinContent(allEventsBin) < counter.GetBinContent(allEventsBin+1):
                    nAllEvts  = counter.GetBinContent(allEventsBin)
                    nPUReEvts = counter.GetBinContent(allEventsBin+1)
                    normalizationCheckStatus = False
            if _debugNAllEvents: # Debug print
                print "DEBUG: self.nAllEventsUnweighted = "+str(self.nAllEventsUnweighted)
        # If reading unweighted counters fail
        except HistogramNotFoundException, e:
            if not self._weightedCounters:
                raise Exception("Could not find counter histogram, message: %s" % str(e))
            self.nAllEventsUnweighted = -1
        # If normalization problem is spotted
        if not normalizationCheckStatus:
            msg  = "ERROR! dset=%s\n\tBase::AllEvents counter (=%s) is smaller than the Base::PUReweighting counter (=%s)" % (self.name, nAllEvts, nPUReEvts)
            # Known issue which was thoroughly tested. Fraction events are inform user difference is 1 event or more
            if (nAllEvts-nPUReEvts) >= 1.0:
                raise Exception(msg)
 
        # Try to read weighted counters
        if self._weightedCounters:
            self.counterDir = self._weightedCounterDir
            try:
                (counter, realName) = self.getRootHisto(self.counterDir+"/counter") # weighted
                ctr = _histoToCounter(counter)
                self.nAllEventsWeighted = ctr[0][1].value() # first counter, second element of the tuple, corresponds to ttree: skimCounterAll
            except HistogramNotFoundException, e:
                raise Exception("Could not find counter histogram, message: %s" % str(e))
            if _debugNAllEvents: # Debug print
                print "DEBUG: self.nAllEventsWeighted = "+str(self.nAllEventsWeighted)


        # Set nAllEvents to unweighted value (corresponding to ttree: skimCounterAll)  
        # The corresponding value in the weighted counter is 0, so we don't want to use that
        self.nAllEvents = self.nAllEventsUnweighted
        if _debugNAllEvents: # Debug print
            print "DEBUG: self.nAllEvents = "+str(self.nAllEvents)

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

    def forEach(self, function):
        return [function(self)]

    ## Set the centre-of-mass energy (in TeV) as string
    def setEnergy(self, energy):
        if not isinstance(energy, basestring):
            raise Exception("The energy must be set as string")
        self.info["energy"] = energy

    ## Get the centre-of-mass energy (in TeV) as string
    def getEnergy(self):
        return self.info.get("energy", "0")

    ## Set cross section of MC dataset (in pb).
    def setCrossSection(self, value):
        if not self.isMC():
            raise Exception("Should not set cross section for non-MC dataset %s" % self.name)
        self.info["crossSection"] = value

    ## Get cross section of MC dataset (in pb).
    def getCrossSection(self):
        if not self.isMC():
            raise Exception("Dataset %s is not MC, no cross section available" % self.name)
        try:
            return self.info["crossSection"]
        except KeyError:
            raise Exception("Dataset %s is MC, but cross section has not been set. You have to either add the cross section for this dataset and energy of %s TeV to NtupleAnalysis/python/tools/crosssection.py, or set it for this Dataset object with setCrossSection() method." % (self.name, self.getEnergy()))

    ## Set the integrated luminosity of data dataset (in pb^-1).
    def setLuminosity(self, value):
        if not self.isData():
            raise Exception("Should not set luminosity for MC dataset %s" % self.name)
        self.info["luminosity"] = value

    ## Get the integrated luminosity of data dataset (in pb^-1).
    def getLuminosity(self):
        if not (self.isData() or self.isPseudo()):
            raise Exception("Dataset %s is not data nor pseudo, no luminosity available" % self.name)
        try:
            return self.info["luminosity"]
        except KeyError:
            raise Exception("Dataset %s is %s, but luminosity has not been set yet. You have to explicitly set the luminosity with setLuminosity() method." % (self.name, self.getDataType()))

    def setProperty(self, key, value):
        self.info[key] = value

    def getProperty(self, key):
        return self.info[key]

    def isData(self):
        return self._isData

    def isPseudo(self):
        return self._isPseudo

    def isMC(self):
        return self._isMC

    def is2016(self):
        return self._is2016
    
    def is2017(self):
        return self._is2017
    
    def is2018(self):
        return self._is2018
    
    def getDataType(self):
        if self.isData():
            return "data"
        if self.isMC():
            return "MC"
        if self.isPseudo:
            return "pseudo"
        raise Exception("I don't know what I am, sorry.")

    def getCounterDirectory(self):
        return self.counterDir

    def getRootFile(self):
        if len(self.files) > 1:
            raise Exception("Dataset %s consists of %d files, you should use getRootFiles() method instead." % (self.getName(), len(self.files)))
        return self.files[0]

    def getRootFiles(self):
        return self.files

    ## Set the number of all events (for normalization).
    #
    # This allows both overriding the value read from the event
    # counter, or creating a dataset without event counter at all.
    def setNAllEvents(self, nAllEvents):
        self.nAllEvents = nAllEvents
        
        
    ## Update number of all events (for normalization) to a pileup-reweighted value.
    #
    # \param era     Data era to use to pick the pile-up-reweighted all
    #                event number (optional, if not given a default
    #                value read from the configinfo is used)
    # \param kwargs  Keyword arguments (forwarded to pileupReweightedAllEvents.WeightedAllEvents.getWeighted())
    #
    # If \a topPtWeightType is not given in \a kwargs, read the value
    # from analysis directory -specific configInfo
    def updateNAllEventsToPUWeighted(self, era=None, **kwargs):
        # Ignore if not MC
        if not self.isMC():
            return

        # Look at configInfo
        if not "isPileupReweighted" in self.info.keys():
            raise Exception("Key 'isPileupReweighted' missing in configinfo histogram!")
        ratio = 1.0
        if self.info["isPileupReweighted"] > 0.0:
            delta = 0.0
            if(self.nAllEvents > 0.0): 
                delta = (self.info["isPileupReweighted"] - self.nAllEvents) / self.nAllEvents
                ratio = ratio * self.info["isPileupReweighted"] / self.nAllEvents
            if _debugNAllEvents and abs(delta) > 0.00001:
                print "dataset (%s): Updated NAllEvents to pileUpReweighted NAllEvents, change: %0.6f %%"%(self.getName(), delta*100.0)
        if not "isTopPtReweighted" in self.info.keys():
            raise Exception("Key 'isTopPtReweighted' missing in configinfo histogram!")
        if self.info["isTopPtReweighted"] > 0.0:
            delta = 0.0
            if(self.nAllEvents > 0.0):
                delta = (self.info["isTopPtReweighted"] - self.nAllEvents) / self.nAllEvents
                ratio = ratio * self.info["isTopPtReweighted"] / self.nAllEvents
            if _debugNAllEvents and abs(delta) > 0.00001:
                print "dataset (%s): Updated NAllEvents to isTopPtReweighted NAllEvents, change: %0.6f %%"%(self.getName(), delta*100.0)
        self.nAllEvents = ratio * self.nAllEvents

    def getNAllEvents(self):
        if not hasattr(self, "nAllEvents"):
            raise Exception("Number of all events is not set for dataset %s! The counter directory was not given, and setNallEvents() was not called." % self.name)
        return self.nAllEvents

    def getNAllUnweightedEvents(self):
        if not hasattr(self, "nAllEventsUnweighted"):
            raise Exception("Number of all unweighted events is not set for dataset %s! The counter directory was not given, and setNallEvents() was not called." % self.name)
        return self.nAllEventsUnweighted

    def getNormFactor(self):
        '''
        Get the cross section normalization factor.
       
        The normalization factor is defined as:
        crossSection/N(all events)
        so by multiplying the number of MC events with the 
        factor one gets the corresponding cross section.
        '''
        nAllEvents = self.getNAllUnweightedEvents()
        if nAllEvents == 0:
            Print("WARNING! nAllEvents = %s" % (nAllEvents), True)
            return 0
            return self.getCrossSection() / nAllEvents

    def hasRootHisto(self, name, **kwargs):
        '''
        Check if a ROOT histogram exists in this dataset
        
        \param name  Name (path) of the ROOT histogram
        
        If dataset.TreeDraw object is given, it is considered to always
        exist.
        '''
        realName = self._translateName(name, **kwargs)
        if hasattr(realName, "draw"):
            return True

        for f in self.files:
            o = aux.Get(f, realName)
            if o != None:
                status = False
                if isinstance(o, ROOT.TDirectoryFile):
                    status = len(o.GetListOfKeys()) > 0
                else:
                    status = isinstance(o, ROOT.TH1)
                o.Delete()
                return status
        return False

    def getDatasetRootHisto(self, name, modify=None, **kwargs):
        '''
        Get the dataset.DatasetRootHisto object for a named histogram.
        
        \param name   Path of the histogram in the ROOT file
        \param modify Function to modify the histogram (use case is e.g. obtaining a slice of TH2 as TH1)
        \param kwargs Keyword arguments, forwarded to getRootHisto()
        
        \return dataset.DatasetRootHisto object containing the (unnormalized) TH1 and this Dataset
        
        If dataset.TreeDraw object is given (or actually anything with
        draw() method), the draw() method is called by giving the
        Dataset object as parameters. The draw() method is expected to
        return a TH1 which is then returned.
        
        If dataset.SystematicsHelper object is given (or actually
        anything with addUncertainties() method), the addUncertainties()
        method of it is called with the Dataset and
        RootHistoWithUncertainties objects, and the modify function.
         '''
        #h = None
        # if hasattr(name, "draw"):
        #     if len(kwargs) > 0:
        #         print >>sys.stderr, "WARNING: You gave keyword arguments to getDatasetRootHisto() together with object with draw() method. The keyword arguments are not passed to the draw() call. This may or may not be what you want."
        #     h = name.draw(self)
        # else:
        (h, realName) = self.getRootHisto(name, **kwargs)
        name2 = h.GetName()+"_"+self.name
        h.SetName(name2.translate(None, "-+.:;"))

        if modify is not None:
            h = modify(h)

        wrapper = RootHistoWithUncertainties(h)
        if hasattr(name, "addUncertainties"):
            name.addUncertainties(self, wrapper, modify)
        return DatasetRootHisto(wrapper, self) 

    def getDirectoryContent(self, directory, predicate=None):
        '''
        Get the directory content of a given directory in the ROOT file.
        
        \param directory   Path of the directory in the ROOT file

        \param predicate   Append the directory name to the return list only if
        predicate returns true for the name. Predicate
        should be a function taking an object in the directory as an
        argument and returning a boolean.
    
        \return List of names in the directory.
        
        If the dataset consists of multiple files, the listing of the
        first file is given.
        '''
        (dirs, realDir) = self.getRootObjects(directory)

        # wrap the predicate
        wrapped = None
        if predicate is not None:
            wrapped = lambda key: predicate(key.ReadObj())

        return aux.listDirectoryContent(dirs[0], wrapped)

    def _setBaseDirectory(self,base):
        self.basedir = base
        
    def getBaseDirectory(self):
        '''
        Get the path of the multicrab directory where this dataset originates
        '''
        return self.basedir

    def formatDatasetTree(self, indent):
        return '%sDataset("%s", %s, ...),\n' % (indent, self.getName(), ", ".join(['"%s"' % f.GetName() for f in self.files]))

    def setAnalysisDirectoryName(self, analysisDirectoryName):
        self._analysisDirectoryName = analysisDirectoryName
        if not self._analysisDirectoryName.endswith('/'):
            self._analysisDirectoryName += "/"

    ## \var name
    # Name of the dataset
    ## \var files
    # List of TFile objects of the dataset
    ## \var info
    # Dictionary containing the configInfo histogram
    ## \var dataVersion
    # dataVersion string of the dataset (from TFile)
    ## \var era
    # Era of the data (used in the analysis for pile-up reweighting,
    # trigger efficiencies etc). Is None if corresponding TNamed
    # doesn't exist in configinfo directory
    ## \var nAllEvents
    # Number of all MC events, used in MC normalization
    ## \var nAllEventsUnweighted
    # Number of all MC events as read from the unweighted counter.
    # This should always be a non-zero number
    ## \var nAllEventsWeighted
    # Number of all MC events as read from the weighted counter. This
    # can be None (if weightedCounters was False in __init__()), zero
    # (if the input for the analysis job was a skim), or a non-zero
    # number (if the input for the anlysis job was not a skim)
    ## \var counterDir
    # Name of TDirectory containing the main event counter
    ## \var _origCounterDir
    # Name of the counter directory as given for __init__(), needed for deepCopy()
    ## \var _isData
    # If true, dataset is from data, if false, from MC


## Dataset class for histogram access for a dataset merged from Dataset objects.
# 
# The merged datasets are required to be either MC, data, or pseudo
class DatasetMerged:
    ## Constructor.
    # 
    # \param name      Name of the merged dataset
    # \param datasets  List of dataset.Dataset objects to merge
    # 
    # Calculates the total cross section (luminosity) for MC (data or pseudo)
    # datasets.
    def __init__(self, name, datasets):
        self.name = name
        #self.stacked = stacked
        self.datasets = datasets
        if len(datasets) == 0:
            raise Exception("Can't create a DatasetMerged from 0 datasets")

        self.info = {}

        energy = self.datasets[0].getEnergy()
        for d in self.datasets[1:]:
            if energy != d.getEnergy():
                raise Exception("Can't merge datasets with different centre-of-mass energies (%s: %d TeV, %s: %d TeV)" % (self.datasets[0].getName(), energy, d.getName(), d.getEnergy()))

        if self.datasets[0].isMC():
            crossSum = 0.0
            for d in self.datasets:
                if not d.isMC():
                    raise Exception("Can't merge non-MC dataset %s with MC datasets, it is %s" % (d.getName(), d.getDataType()))
                crossSum += d.getCrossSection()
            self.info["crossSection"] = crossSum
        else:
            reft = self.datasets[0].getDataType()
            lumiSum = 0.0
            for d in self.datasets:
                lumiSum += d.getLuminosity()
                t = d.getDataType()
                if reft != t:
                    raise Exception("Can't merge non-%s datasets %s with %s datasets, it is %s" % (reft, d.getName(), t))
            self.info["luminosity"] = lumiSum

    ## Close TFiles in the contained dataset.Dataset objects
    def close(self):
        for d in self.datasets:
            d.close()

    ## Make a deep copy of a DatasetMerged object.
    #
    # Nothing is shared between the returned copy and this object.
    #
    # \see dataset.Dataset.deepCopy()
    def deepCopy(self):
        dm = DatasetMerged(self.name, [d.deepCopy() for d in self.datasets])
        dm.info.update(self.info)
        return dm

    def setDirectoryPostfix(self, postfix):
        for d in self.datasets:
            d.setDirectoryPostfix(postfix)

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

    def forEach(self, function):
        ret = []
        for d in self.datasets:
            ret.extend(d.forEach(function))
        return ret

    def setEnergy(self, energy):
        for d in self.datasets:
            d.setEnergy(energy)

    def getEnergy(self):
        return self.datasets[0].getEnergy()

    def setCrossSection(self, value):
        if not self.isMC():
            raise Exception("Should not set cross section for non-MC dataset %s (has luminosity)" % self.name)
        raise Exception("Setting cross section for merged dataset is meaningless (it has no real effect, and hence is misleading")

    ## Get cross section of MC dataset (in pb).
    def getCrossSection(self):
        if not self.isMC():
            raise Exception("Dataset %s is not MC, no cross section available" % self.name)
        return self.info["crossSection"]

    def setLuminosity(self, value):
        if self.isMC():
            raise Exception("Should not set luminosity for MC dataset %s (has crossSection)" % self.name)
        raise Exception("Setting luminosity for merged dataset is meaningless (it has no real effect, and hence is misleading")

    ## Get the integrated luminosity of data dataset (in pb^-1).
    def getLuminosity(self):
        if self.isMC():
            raise Exception("Dataset %s is MC, no luminosity available" % self.name)
        return self.info["luminosity"]

    def setProperty(self, key, value):
        self.info[key] = value

    def getProperty(self, key):
        return self.info[key]

    def isData(self):
        return self.datasets[0].isData()

    def isPseudo(self):
        return self.datasets[0].isPseudo()

    def isMC(self):
        return self.datasets[0].isMC()

    def getCounterDirectory(self):
        countDir = self.datasets[0].getCounterDirectory()
        for d in self.datasets[1:]:
            if countDir != d.getCounterDirectory():
                raise Exception("Error: merged datasets have different counter directories")
        return countDir

    def getNormFactor(self):
        return None

    ## Check if a ROOT histogram exists in this dataset
    #
    # \param name  Name (path) of the ROOT histogram
    #
    # The ROOT histogram is expected to exist in all underlying
    # dataset.Dataset objects.
    def hasRootHisto(self, name):
        has = True
        for d in self.datasets:
            has = has and d.hasRootHisto(name)
        return has

    ## Get the DatasetRootHistoMergedMC/DatasetRootHistoMergedData object for a named histogram.
    #
    # \param name   Path of the histogram in the ROOT file
    # \param kwargs Keyword arguments, forwarder to get
    #               getDatasetRootHisto() of the contained
    #               Dataset objects
    #
    # DatasetRootHistoMergedData works also for pseudo
    def getDatasetRootHisto(self, name, **kwargs):
        wrappers = [d.getDatasetRootHisto(name, **kwargs) for d in self.datasets]
        if self.isMC():
            return DatasetRootHistoMergedMC(wrappers, self)
        elif self.isData():
            return DatasetRootHistoMergedData(wrappers, self)
        elif self.isPseudo():
            return DatasetRootHistoMergedPseudo(wrappers, self)
        else:
            raise Exception("Internal error (unknown dataset type)")

    ## Get ROOT histogram
    #
    # \param name    Path of the ROOT histogram relative to the analysis
    #                root directory
    # \param kwargs  Keyword arguments, forwarded to getRootObjects()
    #
    # \return pair (\a first histogram, \a realName)
    #
    # If name starts with slash ('/'), it is interpreted as a absolute
    # path within the ROOT file.
    #
    # If dataset.TreeDraw object is given (or actually anything with
    # draw() method), the draw() method is called by giving the
    # Dataset object as parameters. The draw() method is expected to
    # return a TH1 which is then returned.
    def getFirstRootHisto(self, name, **kwargs):
        if hasattr(self.datasets[0], "getFirstRootHisto"):
            content = self.datasets[0].getFirstRootHisto(name, **kwargs)
        else:
            content = self.datasets[0].getRootHisto(name, **kwargs)
        return content

    ## Get the directory content of a given directory in the ROOT file.
    # 
    # \param directory   Path of the directory in the ROOT file
    # \param predicate   Append the directory name to the return list only if
    #                    predicate returns true for the name. Predicate
    #                    should be a function taking a string as an
    #                    argument and returning a boolean.
    # 
    # Returns a list of names in the directory. The contents of the
    # directories of the merged datasets are required to be identical.
    def getDirectoryContent(self, directory, predicate=lambda x: True):
        content = self.datasets[0].getDirectoryContent(directory, predicate)
        for d in self.datasets[1:]:
            if content != d.getDirectoryContent(directory, predicate):
                raise Exception("Error: merged datasets have different contents in directory '%s'" % directory)
        return content

    def formatDatasetTree(self, indent):
        ret = '%sDatasetMerged("%s", [\n' % (indent, self.getName())
        for dataset in self.datasets:
            ret += dataset.formatDatasetTree(indent+"  ")
        ret += "%s]),\n" % indent
        return ret

    ## \var name
    # Name of the merged dataset
    ## \var datasets
    # List of merged dataset.Dataset objects
    ## \var info
    # Dictionary containing total cross section (MC) or integrated luminosity (data)

## Dataset class for histogram access for a dataset added from Dataset objects.
# 
# The added datasets are required to be MC
class DatasetAddedMC(DatasetMerged):
    ## Constructor.
    # 
    # \param name      Name of the merged dataset
    # \param datasets  List of dataset.Dataset objects to add
    #
    # The cross section of the added datasets must be the same
    def __init__(self, name, datasets):
        self.name = name
        #self.stacked = stacked
        self.datasets = datasets
        if len(datasets) == 0:
            raise Exception("Can't create a DatasetAddedMC from 0 datasets")

        self.info = {}

        energy = self.datasets[0].getEnergy()
        for d in self.datasets[1:]:
            if energy != d.getEnergy():
                raise Exception("Can't merge datasets with different centre-of-mass energies (%s: %d TeV, %s: %d TeV)" % self.datasets[0].getName(), energy, d.getName(), d.getEnergy())

        crossSection = self.datasets[0].getCrossSection()
        for d in self.datasets:
            if not d.isMC():
                raise Exception("Datasets must be MC, got %s which is data" % d.getName())
            xs2 = d.getCrossSection()
            if abs((xs2-crossSection)/crossSection) > 1e-6:
                raise Exception("Datasets must have the same cross section, got %f from %s and %f from %s" % (crossSection, self.datasets[0].getName(), xs2, d.getName()))

        self.info["crossSection"] = crossSection

    ## Make a deep copy of a DatasetMerged object.
    #
    # Nothing is shared between the returned copy and this object.
    #
    # \see dataset.Dataset.deepCopy()
    def deepCopy(self):
        dm = DatasetAddedMC(self.name, [d.deepCopy() for d in self.datasets])
        dm.info.update(self.info)
        return dm

    ## Set cross section of MC dataset (in pb).
    def setCrossSection(self, value):
        if not self.isMC():
            raise Exception("Should not set cross section for data dataset %s" % self.name)
        self.info["crossSection"] = value
        for d in self.datasets:
            d.setCrossSection(value)

    def setProperty(self, key, value):
        for d in self.datasets:
            d.setProperty(key, value)

    ## Get the DatasetRootHistoMergedMC/DatasetRootHistoMergedData object for a named histogram.
    #
    # \param name   Path of the histogram in the ROOT file
    # \param kwargs Keyword arguments, forwarder to get
    #               getDatasetRootHisto() of the contained
    #               Dataset objects
    def getDatasetRootHisto(self, name, **kwargs):
        wrappers = [d.getDatasetRootHisto(name, **kwargs) for d in self.datasets]
        return DatasetRootHistoAddedMC(wrappers, self)


    ## Get the cross section normalization factor.
    #
    # The normalization factor is defined as crossSection/N(all
    # events), so by multiplying the number of MC events with the
    # factor one gets the corresponding cross section.
    #
    # Implementation is close to dataset.Dataset.getNormFactor()
    def getNormFactor(self):
        nAllEvents = sum([d.getNAllUnweightedEvents() for d in self.datasets])
        if nAllEvents == 0:
            raise Exception("%s: Number of all events is 0.\nProbable cause is that the counters are weighted, the analysis job input was a skim, and the updateAllEventsToPUWeighted() has not been called." % self.name)

        return self.getCrossSection() / nAllEvents

    def formatDatasetTree(self, indent):
        ret = '%sDatasetAddedMC("%s", [\n' % (indent, self.getName())
        for dataset in self.datasets:
            ret += dataset.formatDatasetTree(indent+"  ")
        ret += "%s]),\n" % indent
        return ret


class DatasetManager:
    '''
    Collection of Dataset objects which are managed together.
    
    Holds both an ordered list of Dataset objects, and a name->object
    map for convenient access by dataset name.
    
    \todo The code structure could be simplified by getting rid of
    dataset.DatasetRootHisto. This would mean that the MC normalisation
    should be handled in dataset.DatasetManagager and dataset.Dataset,
    with an interface similar to what dataset.DatasetRootHisto and
    histograms.HistoManager provide now (i.e. user first sets the
    normalisation scheme, and then asks histograms which are then
    normalised as requested). dataset.Dataset and dataset.DatasetManager
    should then return ROOT TH1s, with which user is free to do what
    (s)he wants. histograms.HistoManager and histograms.HistoManagerImpl
    could be merged, as it would take already-normalized histograms as
    input (the input should still be histograms.Histo classes in order
    to give user freedom to provide fully customized version of such
    wrapper class if necessary). The interface of plots.PlotBase would
    still accept TH1/TGraph, so no additional burden would appear for
    the usual use cases with plots. The information of a histogram being
    data/MC in histograms.Histo could also be removed (as it is
    sometimes too restrictive), and the use in plots.PlotBase (and
    deriving classes) could be transformed to identify the data/MC
    datasets (for default formatting purposes) by the name of the
    histograms (in the usual workflow the histograms have the dataset
    name), with the possibility that user can easily modify the names of
    data/MC histograms. This would bring more flexibility on that front,
    and easier customization when necessary.
    '''    
    def __init__(self, base="", label=""):
        '''
        Constructor
        
         \param base    Directory (absolute/relative to current working
         directory) where the luminosity JSON file is located (see loadLuminosities() )
         
         DatasetManager is constructed as empty
         '''
        Verbose("__init__()", True)
        self.label      = label
        self.datasets   = []
        self.datasetMap = {}
        self._setBaseDirectory(base)
        return

    def setLabel(self, label):
        '''
        Unique label for handling multiple dataset managers

        Recommended to use the pseudomulticrab directory as label for each manager
        '''
        self.label = label
        return

    def getLabel(self):
        return self.label

    def _populateMap(self):
        '''
        Populate the datasetMap member from the datasets list.
        
        Intended only for internal use.
        '''
        Verbose("_populateMap", True)

        self.datasetMap = {}
        for d in self.datasets:
            Verbose("Adding %s to datasetMap" % (d.getName()), False)
            self.datasetMap[d.getName()] = d
        return

    def _setBaseDirectory(self, base):
        Verbose("_setBaseDirectory()", True)
        for d in self.datasets:
            d._setBaseDirectory(base)
        return
          
  
    def close(self):
        '''
        Close all TFiles of the contained dataset.Dataset objects
        
        \see dataset.Dataset.close()
        '''
        Verbose("close()", True)

        for d in self.datasets:
            d.close()
        return


    def append(self, dataset):
        '''
        Append a Dataset object to the set.
        
        \param dataset    Dataset object
        
        The new Dataset must have a different name than the already existing ones.
        '''
        Verbose("append()", True)

        if dataset.getName() in self.datasetMap:
            raise Exception("Dataset '%s' already exists in this DatasetManager" % dataset.getName())

        self.datasets.append(dataset)
        self.datasetMap[dataset.getName()] = dataset
        return


    def extend(self, datasetmgr):
        '''
        Extend the set of Datasets from another DatasetManager object.
        
        \param datasetmgr   DatasetManager object
        
        Note that the dataset.Dataset objects of datasetmgr are appended to
        self by reference, i.e. the Dataset objects will be shared
        between them.
        '''
        Verbose("extend()", True)

        for d in datasetmgr.datasets:
            Verbose("Appending %s to list of datasets" % (d.getName()), False)
            self.append(d)
        return


    def shallowCopy(self):
        '''
        Make a shallow copy of the DatasetManager object.
        
        The dataset.Dataset objects are shared between the DatasetManagers.
        
        Useful e.g. if you want to have a subset of the dataset.Dataset objects
        '''
        Verbose("shallowCopy()", True)

        copy = DatasetManager()
        copy.extend(self)
        return copy


    def deepCopy(self):
        '''
        Make a deep copy of the DatasetManager object.
        
        Nothing is shared between the DatasetManagers.
        
        Useful e.g. if you want to have two sets of same datasets, but
        others are somehow modified (e.g. cross section)
        '''
        Verbose("deepCopy()", True)

        copy = DatasetManager()
        for d in self.datasets:
            copy.append(d.deepCopy())
        return copy


    def setEnergy(self, energy):
        '''
        Set the centre-of-mass energy for all datasets
        '''
        Verbose("setEnergy()", True)

        for d in self.datasets:
            d.setEnergy(energy)
        return
            

    def getEnergies(self):
        '''
        Get a list of centre-of-mass energies of the datasets
        '''
        Verbose("getEnergies()", True)

        tmp = {}
        for d in self.datasets:
            tmp[d.getEnergy()] = 1
        energies = tmp.keys()
        energies.sort()
        return energies


    def hasDataset(self, name):
        return name in self.datasetMap


    def getDataset(self, name):
        return self.datasetMap[name]

    ## Get a list of dataset.DatasetRootHisto objects for a given name.
    # 
    # \param histoName   Path to the histogram in each ROOT file.
    # \param kwargs      Keyword arguments, forwarder to get
    #                    getDatasetRootHisto() of the contained
    #                    Dataset objects
    #
    # \see dataset.Dataset.getDatasetRootHisto()
    def getDatasetRootHistos(self, histoName, **kwargs):
        return [d.getDatasetRootHisto(histoName, **kwargs) for d in self.datasets]

    ## Get a list of all dataset.Dataset objects.
    def getAllDatasets(self):
        return self.datasets

    ## Get a list of MC dataset.Dataset objects.
    #
    # \todo Implementation would be simpler with filter() method
    def getMCDatasets(self):
        ret = []
        for d in self.datasets:
            if d.isMC():
                ret.append(d)
        return ret

    ## Get a list of data dataset.Dataset objects.
    #
    # \todo Implementation would be simpler with filter() method
    def getDataDatasets(self):
        ret = []
        for d in self.datasets:
            if d.isData():
                ret.append(d)
        return ret

    ## Get a list of pseudo dataset.Dataset objects.
    def getPseudoDatasets(self):
        return filter(lambda d: d.isPseudo(), self.datasets)

    ## Get a list of names of all dataset.Dataset objects.
    def getAllDatasetNames(self):
        return [x.getName() for x in self.getAllDatasets()]

    ## Get a list of names of MC dataset.Dataset objects."""
    def getMCDatasetNames(self):
        return [x.getName() for x in self.getMCDatasets()]

    ## Get a list of names of data dataset.Dataset objects.
    def getDataDatasetNames(self):
        return [x.getName() for x in self.getDataDatasets()]

    ## Get a list of names of pseudo dataset.Dataset objects.
    def getPseudoDatasetNames(self):
        return [x.getName() for x in self.getPseudoDatasets()]

    ## Select and reorder Datasets.
    # 
    # \param nameList   Ordered list of Dataset names to select
    # 
    # This method can be used to either select a set of
    # dataset.Dataset objects. reorder them, or both.
    def selectAndReorder(self, nameList):
        selected = []
        for name in nameList:
            try:
                selected.append(self.datasetMap[name])
            except KeyError:
                print >> sys.stderr, "WARNING: Dataset selectAndReorder: dataset %s doesn't exist" % name

        self.datasets = selected
        self._populateMap()

    ## Remove dataset.Dataset objects
    # 
    # \param nameList    List of dataset.Dataset names to remove
    # \param close       If true, close the removed dataset.Dataset objects
    def remove(self, nameList, close=True):
        if isinstance(nameList, basestring):
            nameList = [nameList]

        selected = []
        for d in self.datasets:
            if not d.getName() in nameList:
                selected.append(d)
            elif close:
                d.close()
        self.datasets = selected
        self._populateMap()

    ## Rename a Dataset.
    # 
    # \param oldName   The current name of a dataset.Dataset
    # \param newName   The new name of a dataset.Dataset
    def rename(self, oldName, newName):
        if oldName == newName:
            return

        if newName in self.datasetMap:
            raise Exception("Trying to rename datasets '%s' to '%s', but a dataset with the new name already exists!" % (oldName, newName))
        self.datasetMap[oldName].setName(newName)
        self._populateMap()

    ## Rename many dataset.Dataset objects
    # 
    # \param nameMap   Dictionary containing oldName->newName mapping
    # \param silent    If true, don't raise Exception if source dataset doesn't exist
    #
    # \see rename()
    def renameMany(self, nameMap, silent=False):
        for oldName, newName in nameMap.iteritems():
            if oldName == newName:
                continue

            if newName in self.datasetMap:
                raise Exception("Trying to rename datasets '%s' to '%s', but a dataset with the new name already exists!" % (oldName, newName))

            try:
                self.datasetMap[oldName].setName(newName)
            except KeyError, e:
                if not silent:
                    raise Exception("Trying to rename dataset '%s' to '%s', but '%s' doesn't exist!" % (oldName, newName, oldName))
        self._populateMap()

    ## Merge all data dataset.Dataset objects to one with a name 'Data'.
    #
    # \param args    Positional arguments (forwarded to merge())
    # \param kwargs  Keyword arguments (forwarded to merge())
    def mergeData(self, *args, **kwargs):
        self.merge("Data", self.getDataDatasetNames(), *args, **kwargs)
        
    ## Merge all primary datasets available
    #
    # \param args    Positional arguments (forwarded to merge())
    # \param kwargs  Keyword arguments (forwarded to merge())
    def mergePrimaryDatasets(self, *args, **kwargs):
        
        # Get a dictionary of all the primary datasets available
        primaryDatasets = {}
                
        for x in self.getDataDatasetNames():
            if x.split("_")[0] not in primaryDatasets.keys():
                primaryDatasets[x.split("_")[0]] = [x]
            else:
                primaryDatasets[x.split("_")[0]].append(x)
            
        for i in primaryDatasets.keys():
            self.merge(i, primaryDatasets.get(i), *args, **kwargs)
        return

    ## Merge all MC dataset.Datasetobjects to one with a name 'MC'.
    #
    # \param args    Positional arguments (forwarded to merge())
    # \param kwargs  Keyword arguments (forwarded to merge())
    def mergeMC(self, *args, **kwargs):
        self.merge("MC", self.getMCDatasetNames(), *args, **kwargs)

    ## Merge datasets according to the mapping.
    #
    # \param mapping Dictionary of oldName->mergedName mapping. The
    #                dataset.Dataset objects having the same mergedName are merged
    # \param args    Positional arguments (forwarded to merge())
    # \param kwargs  Keyword arguments (forwarded to merge())
    def mergeMany(self, mapping, *args, **kwargs):
        toMerge = {}
        for d in self.datasets:
            if d.getName() in mapping:
                newName = mapping[d.getName()]
                if newName in toMerge:
                    toMerge[newName].append(d.getName())
                else:
                    toMerge[newName] = [d.getName()]

        for newName, nameList in toMerge.iteritems():
            self.merge(newName, nameList, *args, **kwargs)
        return


    def merge(self, newName, nameList, keepSources=False, addition=False, silent=True, allowMissingDatasets=False):
        '''
        Merge dataset.Dataset objects.
    
        \param newName      Name of the merged dataset.DatasetMerged

        \param nameList     List of dataset.Dataset names to merge
        
        \param keepSources  If true, keep the original dataset.Dataset objects in the list of datasets. Otherwise
        they are removed, as they are now contained in the dataset.DatasetMerged object

        \param addition     Creates DatasetAddedMC instead of DatasetMerged

        \param allowMissingDatasets  If True, ignore error from missing dataset (warning is nevertheless printed)
    
        If nameList translates to only one dataset.Dataset, the  dataset.Dataset object is renamed
        (i.e. dataset.DatasetMerged object is not created)
        '''
        Verbose("merge()", True)

        (selected, notSelected, firstIndex) = _mergeStackHelper(self.datasets, nameList, "merge", allowMissingDatasets)
        if len(selected) == 0:
            message = "Dataset merge, no datasets '" +", ".join(nameList) + "' found. Not doing anything"

            if allowMissingDatasets:
                if not silent:
                    print >> sys.stderr, message
                    #Print(message, True)
            else:
                raise Exception(message)
            return
        elif len(selected) == 1 and not keepSources:
            if not silent:
                message = "Dataset merge, one dataset '" + selected[0].getName() + "' found from list '" + ", ".join(nameList)+"'. Renaming it to '%s'" % newName
                print >> sys.stderr, message
                #Print(message, True)
            self.rename(selected[0].getName(), newName)
            return

        if not keepSources:
            self.datasets = notSelected

        if addition:
            newDataset = DatasetAddedMC(newName, selected)
        else:
            newDataset = DatasetMerged(newName, selected)

        self.datasets.insert(firstIndex, newDataset)
        self._populateMap()


    def loadLuminosities(self, fname="lumi.json"):
        '''
        Load integrated luminosities from a JSON file.
    
        \param fname   Path to the file (default: 'lumi.json'). If the
        directory part of the path is empty, the file is looked from the base
        directory (which defaults to current directory)
    
        The JSON file should be formatted like this:
        \verbatim
        '{
        "dataset_name": value_in_pb,
        "Mu_135821-144114": 2.863224758
        }'
        \endverbatim

        Note: as setting the integrated luminosity for a merged dataset
        will fail (see dataset.DatasetMerged.setLuminosity()), loading
        luminosities must be done before merging the data datasets to
        one.
        '''
        Verbose("loadLuminosities()", True)

        import json
        
        #For-loop: All datasets
        for d in self.datasets:
            jsonname = os.path.join(d.basedir, fname)
            if not os.path.exists(jsonname):
                raise Exception("Luminosity JSON file '%s' does not exist. Have you run 'hplusLumiCalc.py' in your multicrab directory?" % jsonname)
                for name in self.getDataDatasetNames():
                    self.getDataset(name).setLuminosity(1)
            else:
                Verbose("Loading JSON file %s" % (jsonname), False)
                data = json.load(open(jsonname))

### Alexandros: Needs to be nested?
#                # For-loop: All Dataset-Lumi pairs in dictionary
#                for name, value in data.iteritems():
#                    Print("%s has %s pb"  % (name, value), False)
#                    if self.hasDataset(name):
#                        Print("%s, setting lumi to %s" % (name, value), False)
#                        self.getDataset(name).setLuminosity(value)
#                    else:
#                        Verbose("%s not in dataset map. Skipping ..." % (name), False)
### Alexandros: Needs to be nested?

        # For-loop: All Dataset-Lumi pairs in dictionary
        for name, value in data.iteritems():
            Verbose("%s has %s pb"  % (name, value), False)
            if self.hasDataset(name):
                Verbose("%s, setting lumi to %s" % (name, value), False)
                self.getDataset(name).setLuminosity(value)
            else:
                Verbose("%s not in dataset map. Skipping ..." % (name), False)

####        if len(os.path.dirname(fname)) == 0:
####            fname = os.path.join(self.basedir, fname)
####
####        if not os.path.exists(fname):
####            print >> sys.stderr, "WARNING: luminosity json file '%s' doesn't exist!" % fname
####
####        data = json.load(open(fname))
####        for name, value in data.iteritems():
####            if self.hasDataset(name):
####                self.getDataset(name).setLuminosity(value)
        return


    def loadLumi(self, fname="lumi.json"):
        '''
        '''
        Verbose("loadLumi()", True)

        import json
        jsonname = os.path.join(self.datasets[0].basedir, fname)
        if not os.path.exists(jsonname):
            raise Exception("Lumi JSON file '%s' does not exist. Have you set runMin/runMax and lumi in the analyzer?" % jsonname)
        data = json.load(open(jsonname))
        if self.datasets[0].getAnalysisName() in data:
            return data[self.datasets[0].getAnalysisName()]
        else:
            lumi = 0
            for ds in data.keys():
                lumi += data[ds]
            return lumi
        return -1


    def loadRunRange(self, fname="runrange.json"):
        '''
        '''
        Verbose("loadRunRangei()", True)

        import json
        jsonname = os.path.join(self.datasets[0].basedir, fname)
        if not os.path.exists(jsonname):
            raise Exception("RunRange JSON file '%s' does not exist. Have you set runMin/runMax in the analyzer?" % jsonname)
        data = json.load(open(jsonname))
        return data[self.datasets[0].getAnalysisName()]


    def updateNAllEventsToPUWeighted(self, **kwargs):
        '''
        Update all event counts to the ones taking into account the pile-up reweighting
        
        \param kwargs     Keyword arguments (forwarded to dataset.Dataset.updateAllEventsToWeighted)
        
         Uses the table pileupReweightedAllEvents._weightedAllEvents
        '''
        Verbose("updateNAllEventsToPUWeighted()", True)

        # For-loop: All datasets
        for dataset in self.datasets:
            dataset.updateNAllEventsToPUWeighted(**kwargs)
        #self.printInfo()
        return


    def PrintInfo(self):
        '''
        Alternativ to printInfo. 
        Print a table with all datasets and their corresponding
        cross-sections (MC) or luminosity (data)
        '''
        Verbose("PrintInfo()", True)

        # Table setup
        table   = []
        table.append("")
        align   = "{:<3} {:<50} {:>20} {:<3} {:>20} {:>15} {:<3}"
        hLine   = "="*122
        header  = align.format("#", "Dataset", "Cross Section", "", "Norm. Factor",  "Int. Lumi", "")
        if len(self.getLabel()) >0:
            table.append("{:^122}".format(self.getLabel()))
        table.append(hLine)
        table.append(header)
        table.append(hLine)

        # For-loop: All datasets
        for index, d in enumerate(self.datasets):

            name     = d.getName()
            lumi     = ""
            xs       = ""
            normF    = ""
            lumiUnit = ""
            xsUnit   = ""

            if d.isMC():
                xsUnit = "pb"
                xs     = d.getCrossSection()
                normF  = d.getNormFactor()
            else:
                lumiUnit = "pb^-1"
                lumi = d.getLuminosity()

            line = align.format(index, name, xs, xsUnit, normF, lumi, lumiUnit)
            table.append(line)

        # Finalise the table
        table.append(hLine)
        table.append("")

        # For loop: All rows
        for row in table:
            Print(row, False)
        return


    def PrintLuminosities(self):
        '''
        Print the luminosities of all datasets, in alphabetical order
        in a nice formated table.
        '''
        Verbose("PrintLuminosities()", True)

        table   = []
        table.append("")
        align   = "{:<3} {:<17} {:<45} {:>20} {:<7}"

        header  = align.format("#", "Primary Dataset",  "Dataset", "Luminosity", "")
        hLine   = "="*95
        table.append(hLine)
        table.append(header)
        table.append(hLine)
        
        lumiUnit = "pb-1"
        
        # Check if more than one primary dataset is present
        primDatasets = []
        for d in self.datasets:
            if d.isMC():
                continue
            
            if d.getName().split("_")[0] not in primDatasets:
                primDatasets.append(d.getName().split("_")[0])
        
        for p in primDatasets:
            index    = 0
            intLumi  = 0
            
            # For-loop: All datasets
            for d in self.datasets:
                if d.isMC():
                    continue
                if d.getName().split("_")[0] not in p:
                    continue

                index += 1
                
                name = d.getName()
                lumi = d.getLuminosity()
                line = align.format(index, p, name, "%.3f"%lumi, lumiUnit) 
                table.append(line)
                intLumi+= lumi

            # Finalise the table
            lastLine = align.format("", p, "", "%.3f"%intLumi, lumiUnit) 
            table.append(hLine)
            table.append(lastLine)
            table.append("")
                
        # For loop: All rows
        for row in table:
            Print(row, False)
        return


    def PrintCrossSections(self):
        '''
        Print the cross-section of all datasets, in descending order
        in a nice formated table.
        '''
        Verbose("PrintCrossSections()")
        align  = "{:<3} {:<50} {:>24} {:>3} "
        header = align.format("#", "Dataset", "Cross Section", "")
        hLine  = "="*len(header)
        table  = []
        table.append(hLine)
        table.append(header)            
        table.append(hLine)

        # For-loop: All datasets
        myDatasets = {}
        for d in self.datasets:
            if d.isMC():
                myDatasets[d.getName()] = d.getCrossSection()
            else:
                pass
            # print d.getLuminosity()

        index = 0
        # For-loop: All keys in dataset-xsection map (sorted by descending xsection value)
        for d in sorted(myDatasets, key=myDatasets.get, reverse=True):
            xs = myDatasets[d]
            index += 1
            line = align.format(index, d, "%3f" % (xs), "pb")
            table.append(line)
        table.append(hLine)

        # For-loop: All rows
        for r in table:
            Print(r, False)
        return


    ## Format dataset information
    def formatInfo(self):
        out = StringIO.StringIO()
        col1hdr = "Dataset"
        col2hdr = "Cross section (pb)"
        col3hdr = "Norm. factor"
        col4hdr = "Int. lumi (pb^-1)" 

        maxlen = max([len(x.getName()) for x in self.datasets]+[len(col1hdr)])
        c1fmt = "%%-%ds" % (maxlen+2)
        c2fmt = "%%%d.4g" % (len(col2hdr)+2)
        c3fmt = "%%%d.4g" % (len(col3hdr)+2)
        c4fmt = "%%%d.10g" % (len(col4hdr)+2)

        c2skip = " "*(len(col2hdr)+2)
        c3skip = " "*(len(col3hdr)+2)
        c4skip = " "*(len(col4hdr)+2)

        out.write((c1fmt%col1hdr)+"  "+col2hdr+"  "+col3hdr+"  "+col4hdr+"\n")
        
        # For-loop: All datasets
        for dataset in self.datasets:
            line = (c1fmt % dataset.getName())
            if dataset.isMC():
                line += c2fmt % dataset.getCrossSection()
                normFactor = dataset.getNormFactor()
                if normFactor != None:
                    line += c3fmt % normFactor
                else:
                    line += c3skip
            else:
                line += c2skip+c3skip + c4fmt%dataset.getLuminosity()
            out.write(line)
            out.write("\n")

        ret = out.getvalue()
        out.close()
        return ret

    ## Print dataset information.
    def printInfo(self):
        print self.formatInfo()


    def formatDatasetTree(self):
        ret = "DatasetManager.datasets = [\n"
        for dataset in self.datasets:
            ret += dataset.formatDatasetTree(indent="  ")
        ret += "]"
        return ret


    def printDatasetTree(self):
        print self.formatDatasetTree()

    ## Prints the parameterSet of some Dataset
    #
    # Absolutely no guarantees of which Dataset the parameterSet is
    # from will not be given.
    def printSelections(self):
        namePSets = self.datasets[0].forEach(lambda d: (d.getName(), d.getParameterSet()))
        print "ParameterSet for dataset", namePSets[0][0]
        print namePSets[0][1]

    def getSelections(self):
        namePSets = self.datasets[0].forEach(lambda d: (d.getName(), d.getParameterSet()))
        #print "ParameterSet for dataset", namePSets[0][0]
        return namePSets[0][1]

    ## \var datasets
    # List of dataset.Dataset (or dataset.DatasetMerged) objects to manage
    ## \var datasetMap
    # Dictionary from dataset names to dataset.Dataset objects, for
    # more straightforward accessing of dataset.Dataset objects by
    # their name.
    ## \var basedir
    # Directory (absolute/relative to current working directory) where
    # the luminosity JSON file is located (see loadLuminosities())

    def setAnalysisDirectoryName(self,analysisDirectoryName):
        for d in self.datasets:
            d.setAnalysisDirectoryName(analysisDirectoryName)

class DatasetPrecursor:
    '''
    Precursor dataset, helper class for DatasetManagerCreator
    
    This holds the name, ROOT file, and data/MC status of a dataset.
    '''
    def __init__(self, name, filenames):
        Verbose("__init__", True)
        self._name = name
        self._rootFiles = []
        self._dataVersion = None
        self._pileup = None
        self._pileup_up = None
        self._pileup_down = None
        self._nAllEvents = 0.0

        if isinstance(filenames, basestring):
            self._filenames = [filenames]
            pudir = os.path.dirname(filenames)
            pufile = os.path.join(pudir,"PileUp.root")
            rf = ROOT.TFile.Open(pufile)
            self._pileup = aux.Get(rf, "pileup")
            self._pileup_up = aux.Get(rf, "pileup_up")
            self._pileup_down = aux.Get(rf, "pileup_down")
            rf.Close()
        else:
            #for i, f in enumerate(filenames, 1):
            #    fNameShort = f.split("/crab_")[0].split("/")[-1]
            #    PrintFlushed("Processing %s files (%d/%d)" % (fNameShort, i, len(filenames)), False)
            self._filenames = filenames

        # For-loop: All ROOT files
        for i, name in enumerate(self._filenames, 1):
            
            # For fast/quick testing!
            #if i > 1:
            #    continue

            shortName = name.split("/crab_")[0].split("/")[-1]
            PrintFlushed("%s (%d/%d)" % (shortName, i, len(self._filenames)), False)
            rf = ROOT.TFile.Open(name)

            # Below is important to use '==' instead of 'is' to check for
            # null file
            if rf == None:
                raise Exception("Unable to open ROOT file '%s' for dataset '%s'" % (name, self._name))

            self._rootFiles.append(rf)

            # Get the data version (e.g. 80Xdata or 80Xmc)
            dv = aux.Get(rf, "configInfo/dataVersion")
            if dv == None:
                print "Unable to find 'configInfo/dataVersion' from ROOT file '%s', I have no idea if this file is data, MC, or pseudo" % name
                continue                
            if self._dataVersion is None:
                self._dataVersion = dv.GetTitle()
            else:
                if self._dataVersion != dv.GetTitle():
                    raise Exception("Mismatch in dataVersion when creating multi-file DatasetPrecursor, got %s from file %s, and %s from %s" % (dataVersion, self._filenames[0], dv.GetTitle(), name))

            # Get the TTree
            isTree = aux.Get(rf, "Events") != None
            if isTree:

                if self._pileup == None:
                    # Get the "pileup" histogram under folder "configInfo"
                    puName = "configInfo/pileup"
                    pileup = aux.Get(rf, puName)

                    # Sanity checks
                    if pileup == None:
                        Print("Unable to find 'configInfo/pileup' from ROOT file '%s'" % name, True)
                        sys.exit()
                    if (pileup.Integral() == 0):
                        raise Exception("Empty pileup histogram \"%s\" in ROOT file \"%s\". Entries = \"%s\"." % (puName, rf.GetName(), pileup.GetEntries()) )

                    if self._pileup is None:
                        if pileup != None:
                            self._pileup = pileup
                        else:
                            self._pileup.Add(pileup)
                    if ("data" in self._dataVersion):
                        # pileup (up)
                        pileup_up = aux.Get(rf, "configInfo/pileup_up")
                        if pileup_up == None:
                            print "Unable to find 'configInfo/pileup_up' from ROOT file '%s'" % name
                        if self._pileup_up is None:
                            if pileup_up != None:
                                self._pileup_up = pileup_up
                        else:
                            self._pileup_up.Add(pileup_up)
                        # pileup (down)
                        pileup_down = aux.Get(rf, "configInfo/pileup_down")
                        if pileup_down == None:
                            print "Unable to find 'configInfo/pileup_down' from ROOT file '%s'" % name
                        if self._pileup_down is None:
                            if pileup_down != None:
                                self._pileup_down = pileup_down
                        else:
                            self._pileup_down.Add(pileup_down)
            
            # Obtain nAllEvents
            if isTree:
                counters = aux.Get(rf, "configInfo/SkimCounter")
                if counters != None:
                    if counters.GetNbinsX() > 0:
                        if not "All" in counters.GetXaxis().GetBinLabel(1):
                            raise Exception("Error: The first bin of the counters histogram should be the all events bin!")
                        self._nAllEvents += counters.GetBinContent(1)
                if self._nAllEvents == 0.0:
                    print "Warning (DatasetPrecursor): N(allEvents) = 0 !!!"

#            rf.Close()

        if self._dataVersion is None:
            self._isData = False
            self._isPseudo = False
            self._isMC = False
        else:
            self._isData = "data" in self._dataVersion
            self._isPseudo = "pseudo" in self._dataVersion
            self._isMC = not (self._isData or self._isPseudo)


    def getName(self):
        return self._name

    def getFiles(self):
        return self._rootFiles

    def getFileNames(self):
        return self._filenames

    def isData(self):
        return self._isData

    def isPseudo(self):
        return self._isPseudo

    def isMC(self):
        return self._isMC

    def getDataVersion(self):
        return self._dataVersion

    def getPileUp(self, direction):
        hDict = {}
        hDict["nominal"] = self._pileup
        hDict["up"]      = self._pileup_up
        hDict["plus"]    = self._pileup_up
        hDict["down"]    = self._pileup_down
        hDict["minus"]   = self._pileup_down
        
        if direction not in hDict.keys():
            msg = "Invalid dictionary key '%s'. Please choose from: %s" % (direction, ", ".join(hDict.keys()))
            raise Exception(sh_e + msg + sh_n)
        else:
            return hDict[direction]

    def getNAllEvents(self):
        return self._nAllEvents

    ## Close the ROOT files
    def close(self):
        for f in self._rootFiles:
            f.Close("R")
            f.Delete()
        self._rootFiles = []

_analysisNameSkipList = [re.compile("^SystVar"), re.compile("configInfo"), re.compile("PUWeightProducer")]
_analysisSearchModes = re.compile("_\d+to\d+_")
_dataDataEra_re = re.compile("_Run201\d\S_")


class DatasetManagerCreator:
    '''
    Class for listing contents of multicrab dirs, dataset ROOT files, and creating DatasetManager
    The mai is to first create an object of this class to represent a
    multicrab directory, and then create one or many DatasetManagers,
    which then correspond to a single analysis directory within the ROOT
    files.
    '''
    def __init__(self, rootFileList, **kwargs):
        '''
        Constructor
        
        \param rootFileList  List of (\a name, \a filenames) pairs (\a
        name should be string, \a filenames can be string or list of strings). 
        \a name is taken as the dataset name, and \a filenames as the
        path(s) to the ROOT file(s).

        \param kwargs        Keyword arguments (see below)
        
        <b>Keyword arguments</b>
        \li \a baseDirectory    Base directory of the datasets (delivered later to DatasetManager._setBaseDirectory())
    
        Creates DatasetPrecursor objects for each ROOT file, reads the
        contents of first MC file to get list of available analyses.
        '''
        self._label = None
        self._precursors = [DatasetPrecursor(name, filenames) for name, filenames in rootFileList]
        self._baseDirectory = kwargs.get("baseDirectory", "")
        mcRead = False
        for d in self._precursors:
            #if d.isMC() or d.isPseudo():
            self._readAnalysisContent(d)
            mcRead = True
            break

        if not mcRead:
            for d in self._precursors:
                if d.isData():
                    self._readAnalysisContent(d)
                    break
        dataEras = {}
        for d in self._precursors:
            if d.isData():
                m = _dataDataEra_re.search(d.getName())
                if m:
                    dataEraName = d.getName()[m.span()[0]+1:m.span()[1]-1].split("_")
                    dataEras[dataEraName[0]] = 1

        self._dataDataEras = dataEras.keys()
        self._dataDataEras.sort()
        return

    def setLabel(self, label):
        self._label = label

    def getLabel(self):
        return self._label

    def _readAnalysisContent(self, precursor):
        Verbose("_readAnalysisContent()", True)
        contents = aux.listDirectoryContent(precursor.getFiles()[0], lambda key: key.IsFolder())

        def skipItem(name):
            for skip_re in _analysisNameSkipList:
                if skip_re.search(name):
                    return False
            return True
        contents = filter(skipItem, contents)
        if len(contents) == 0:
            raise Exception("No analysis TDirectories found")

        analyses = {}
        searchModes = {}
        dataEras = {}
        optimizationModes = {}
        systematicVariations = {}

        for d in contents:
            directoryName = d

            # Look for systematic variation
            start = directoryName.find("_SystVar")
            if start >= 0:
                if "SelectedTauForVariation" in directoryName[start:]:
                    continue
                systematicVariations[directoryName[start+1:]] = 1
                directoryName = directoryName[:start]

            # Look for optimization mode
            start = directoryName.find("_Opt")
            if start >= 0:
                optimizationModes[directoryName[start+1:]] = 1
                directoryName = directoryName[:start]

            # Look for data era
            if precursor.isMC() or precursor.isPseudo():
                start = directoryName.find("Run")
                if start >= 0:
                    dataEras[directoryName[start:]] = 1
                    directoryName = directoryName[:start]
            
            # Look for search mode
            m = None
            if start >= 0:
                m = _analysisSearchModes.search(directoryName[:start])
            else:
                m = _analysisSearchModes.search(directoryName)
            if m:
                smname = directoryName[m.span()[0]+1:m.span()[1]-1]
                searchModes[smname] = 1
                directoryName = directoryName[:m.span()[0]]
                #break
            # Whatever is left in directoryName, is our analysis name
            analyses[directoryName] = 1

        self._analyses =  analyses.keys()
        self._searchModes = searchModes.keys()
        self._mcDataEras = dataEras.keys()
        self._optimizationModes = optimizationModes.keys()
        self._systematicVariations = systematicVariations.keys()

        self._analyses.sort()
        self._searchModes.sort()
        self._mcDataEras.sort()
        self._optimizationModes.sort()
        self._systematicVariations.sort()

        # Obtain the "base" names of systematic variations (i.e.
        # without the "Plus"/"Minus" postfix)
        systTmp = {}
        for sv in self._systematicVariations:
#            systTmp[sv.replace("Plus", "").replace("Minus", "")] = 1
            systTmp[sv.replace("Plus", "").replace("Minus", "").replace("Up", "").replace("Down", "")] = 1
        self._systematicVariationSources = systTmp.keys()
        self._systematicVariationSources.sort()

    def getBaseDirectory(self):
        return self._baseDirectory

    def getLumiFile(self):
        return os.path.join(self._baseDirectory, "lumi.json")

    ## Create DatasetManager
    #
    # \param kwargs   Keyword arguments (see below)
    #
    # <b>Keyword arguments</b>
    # \li \a analysisName      Base part of the analysis directory name
    # \li \a searchMode        String for search mode
    # \li \a dataEra           String for data era
    # \li \a optimizationMode  String for optimization mode (optional)
    # \li \a systematicVariation String for systematic variation (optional)
    # \li \a opts              Optional OptionParser object. Should have options added with addOptions().
    #
    # The values of \a analysisName, \a searchMode, \a dataEra, and \a
    # optimizationMode are overridden from \a opts, if they are set
    # (i.e. are non-None). Also, if any of these is not specified
    # either explicitly or via \a opts, the value is inferred from the
    # contents, if there exists only one of it.
    def createDatasetManager(self, **kwargs):
        _args = {}
        _args.update(kwargs)
        # First check that if some of these is not given, if there is
        # exactly one it available, use that.
        for arg, attr in [("analysisName", "getAnalyses"),
                          ("searchMode", "getSearchModes"),
                          ("dataEra", "getMCDataEras"),
                          ("optimizationMode", "getOptimizationModes"),
                          ("systematicVariation", "getSystematicVariations")]:
            lst = getattr(self, attr)()
            if (arg not in _args or _args[arg] is None) and len(lst) == 1:
                _args[arg] = lst[0]

        # Then override from command line options
        opts = kwargs.get("opts", None)
        if opts is not None:
            for arg in ["analysisName", "searchMode", "dataEra", "optimizationMode", "systematicVariation", "counterDir"]:
                o = getattr(opts, arg)
                if o is not None:
                    _args[arg] = o
            del _args["opts"]

        if not "analysisName" in _args:
            raise Exception("You did not specify AnalysisName, and it was not automatically detected from ROOT file")

        # Print the configuration
        parameters = []
        for name in ["analysisName", "searchMode", "dataEra", "optimizationMode", "systematicVariation"]:
            if name in _args:
                value = _args[name]
                if value is not None:
                    parameters.append("%s='%s'" % (name, value))
        Verbose("Creating DatasetManager with %s" % (", ".join(parameters)), True )

        # Create manager and datasets
        dataEra = _args.get("dataEra", None)
        precursors = self._precursors[:]
        if dataEra is not None:
            def isInEra(eras, precursor):
                if precursor.isMC() or precursor.isPseudo():
                    return True
                if isinstance(eras, basestring):
                    eras = [eras]
                for e in eras:
                    if e in precursor.getName():
                        return True
                return False

            try:
                lst = _dataEras[dataEra]
            except KeyError:
                eras = _dataEras.keys()
                eras.sort()
                raise Exception("Unknown data era '%s', known are %s" % (dataEra, ", ".join(eras)))

            precursors = filter(lambda p: isInEra(lst, p), precursors)
        manager = DatasetManager()
        for precursor in precursors:
            if "optimizationMode" in _args.keys() and _args["optimizationMode"] == "":
                del _args["optimizationMode"]

            try:
                if precursor.isData():
                    dset = Dataset(precursor.getName(), precursor.getFiles(), **_args)
                else:
                    dset = Dataset(precursor.getName(), precursor.getFiles(), availableSystematicVariationSources=self._systematicVariationSources, **_args)
            except AnalysisNotFoundException, e:
                msg = str(e)+"\n"
                helpFound = False
                for arg, attr in [("analysisName", "getAnalyses"),
                                  ("searchMode", "getSearchModes"),
                                  ("dataEra", "getMCDataEras"),
                                  ("optimizationMode", "getOptimizationModes"),
                                  ("systematicVariation", "getSystematicVariations")]:
                    lst = getattr(self, attr)()
                    if (arg not in _args or _args[arg] is None) and len(lst) > 1:
                        msg += "You did not specify %s, while ROOT file contains %s\n" % (arg, ", ".join(lst))
                        helpFound = True
                    if arg in _args and _args[arg] is not None and len(lst) == 0:
                        msg += "You specified %s, while ROOT file apparently has none of them\n" % arg
                        helpFound = True
                if not helpFound:
                    raise e
                raise Exception(msg)
            manager.append(dset)

        if len(self._baseDirectory) > 0:
            manager._setBaseDirectory(self._baseDirectory)

        # Load luminosity automatically if the file exists
        lumiPath = self.getLumiFile()
        if os.path.exists(lumiPath):
            Verbose("Loading data luminosities from %s" % (lumiPath), True)
            manager.loadLuminosities()
        return manager

    def getDatasetPrecursors(self):
        return self._precursors

    def getDatasetNames(self):
        return [d.getName() for d in self._precursors]

    def getAnalyses(self):
        return self._analyses

    def getSearchModes(self):
        return self._searchModes

    def getMCDataEras(self):
        return self._mcDataEras

    def getDataDataEras(self):
        return self._dataDataEras

    ## Return MC data eras, or data data eras if MC data era list is empty
    #
    # This is probably the typical use case when user wants "just the
    # list of available data eras".
    def getDataEras(self):
        if len(self._mcDataEras) > 0:
            return self._mcDataEras
        else:
            return self._dataDataEras

    def getOptimizationModes(self):
        return self._optimizationModes

    def getSystematicVariations(self):
        return self._systematicVariations

    def getSystematicVariationSources(self):
        return self._systematicVariationSources

    def printAnalyses(self):
        print "Analyses (analysisName):"
        for a in self._analyses:
            print "  "+a
        print

        if len(self._searchModes) == 0:
            print "No search modes"
        else:
            print "Search modes (searchMode):"
            for s in self._searchModes:
                print "  "+s
        print
        
        if len(self._mcDataEras) == 0:
            print "No data eras in MC"
        else:
            print "Data eras (in MC) (dataEra):"
            for d in self._mcDataEras:
                print "  "+d
        print

        if len(self._dataDataEras) == 0:
            print "No data eras in data"
        else:
            print "Data eras (in data, the letters can be combined in almost any way) (dataEra):"
            for d in self._dataDataEras:
                print "  "+d
        print

        if len(self._optimizationModes) == 0:
            print "No optimization modes"
        else:
            print "Optimization modes (optimizationMode):"
            for o in self._optimizationModes:
                print "  "+o
        print

        if len(self._systematicVariations) == 0:
            print "No systematic variations"
        else:
            print "Systematic variations (systematicVariation):"
            for s in self._systematicVariations:
                print "  "+s
        print

    ## Close the ROOT files
    def close(self):
        for precursor in self._precursors:
            precursor.close()

## Helper class to plug NtupleCache to the existing framework
#
# User should not construct an object by herself, but use
# NtupleCahce.histogram()
class NtupleCacheDrawer:
    ## Constructor
    #
    # \param ntupleCache   NtupleCache object
    # \param histoName     Name of the histogram to obtain
    # \param selectorName  Name of the selector
    def __init__(self, ntupleCache, histoName, selectorName):
        self.ntupleCache = ntupleCache
        self.histoName = histoName
        self.selectorName = selectorName

    ## "Draw"
    #
    # \param datasetName  Dataset object
    #
    # This method exploits the infrastucture we have for TreeDraw.
    def draw(self, dataset):
        self.ntupleCache.process(dataset)
        return self.ntupleCache.getRootHisto(dataset, self.histoName, self.selectorName)

## Ntuple processing with C macro and caching the result histograms
#
# 
class NtupleCache:
    ## Constructor
    #
    # \param treeName       Path to the TTree inside a ROOT file
    # \param selector       Name of the selector class, should also correspond a .C file in \a test/ntuple
    # \param selectorArgs   Optional arguments to the selector
    #                       constructor, can be a list of arguments,
    #                       or a function returning a list of
    #                       arguments
    # \param process        Should the ntuple be processed? (if False, results are read from the cache file)
    # \param cacheFileName  Path to the cache file
    # \param maxEvents      Maximum number of events to process (-1 for all events)
    # \param printStatus    Print processing status information
    # \param macros         Additional macro files to compile and load
    #
    # I would like to make \a process redundant, but so far I haven't
    # figured out a bullet-proof method for that.
    def __init__(self, treeName, selector, selectorArgs=[], process=True, cacheFileName="histogramCache.root", maxEvents=-1, printStatus=True, macros=[]):
        self.treeName = treeName
        self.cacheFileName = cacheFileName
        self.selectorName = selector
        self.selectorArgs = selectorArgs
        self.doProcess = process
        self.maxEvents = maxEvents
        self.printStatus = printStatus

        self.additionalSelectors = {}
        self.datasetSelectorArgs = {}

        self.macrosLoaded = False
        self.processedDatasets = {}

        self.macros = [
            "BaseSelector.C",
            "Branches.C"
            ] + macros + [
            self.selectorName+".C"
            ]
        self.cacheFile = None

    ## Compile and load the macros
    def _loadMacros(self):
        base = os.path.join(aux.higgsAnalysisPath(), "NtupleAnalysis", "test", "ntuple")
        macros = [os.path.join(base, x) for x in self.macros]

        for m in macros:
            ret = ROOT.gROOT.LoadMacro(m+"+g")
            if ret != 0:
                raise Exception("Failed to load "+m)

    def addSelector(self, name, selector, selectorArgs):
        self.additionalSelectors[name] = (selector, selectorArgs)
        macro = selector+".C"
        if not macro in self.macros:
            self.macros.append(macro)

    def setDatasetSelectorArgs(self, dictionary, selectorName=None):
        if not selectorName in self.datasetSelectorArgs:
            self.datasetSelectorArgs[selectorName] = {}
        self.datasetSelectorArgs[selectorName].update(dictionary)

    # def _isMacroNewerThanCacheFile(self):
    #     latestMacroTime = max([os.path.getmtime(m) for m in self.macros])
    #     cacheTime = 0
    #     if os.path.exists(self.cacheFileName):
    #         cacheTime = os.path.getmtime(self.cacheFileName)
    #     return latestMacroTime > cacheTime

    ## Process selector for a dataset
    #
    # \param dataset  Dataset object
    def process(self, dataset):
        #if not self.forceProcess and not self._isMacroNewerThanCacheFile():
        #    return
        if not self.doProcess:
            return

        datasetName = dataset.getName()

        pathDigest = hashlib.sha1(dataset.getBaseDirectory()).hexdigest() # I hope this is good-enough
        procName = pathDigest+"_"+datasetName
        if procName in self.processedDatasets:
            return
        self.processedDatasets[procName] = 1

        if not self.macrosLoaded:
            self._loadMacros()
            self.macrosLoaded = True
        
        if self.cacheFile == None:
            self.cacheFile = ROOT.TFile.Open(self.cacheFileName, "RECREATE")
            self.cacheFile.cd()

        rootDirectory = self.cacheFile.Get(pathDigest)
        if rootDirectory == None:
            rootDirectory = self.cacheFile.mkdir(pathDigest)
            rootDirectory.cd()
            tmp = ROOT.TNamed("originalPath", dataset.getBaseDirectory())
            tmp.Write()

        # Create selector args
        def getSelectorArgs(selectorName, selectorArgsObj):
            ret = []
            d = self.datasetSelectorArgs.get(selectorName, None)
            if isinstance(selectorArgsObj, list):
                ret = selectorArgsObj[:]
                if d is not None and dataset.getName() in d:
                    ret.extend(d[dataset.getName()])
            else:
                # assume we have an object making a keyword->positional mapping
                sa = selectorArgsObj.clone()
                if d is not None and dataset.getName() in d:
                    sa.update(d[dataset.getName()])
                ret = sa.createArgs()
            return ret

        selectorArgs = getSelectorArgs(None, self.selectorArgs)
        (tree, realTreeName) = dataset.createRootChain(self.treeName)

        N = tree.GetEntries()
        useMaxEvents = False
        if self.maxEvents >= 0 and N > self.maxEvents:
            useMaxEvents = True
            N = self.maxEvents

        def getSelectorDir(name_):
            d = rootDirectory.Get(name_)
            if d == None:
                d = rootDirectory.mkdir(name_)
            return d
            
        directory = getSelectorDir("mainSelector").mkdir(datasetName)
        directory.cd()
        argsNamed = ROOT.TNamed("selectorArgs", str(selectorArgs))
        argsNamed.Write()

        selector = ROOT.SelectorImp(N, dataset.isMC(), getattr(ROOT, self.selectorName)(*selectorArgs), directory)
        selector.setPrintStatus(self.printStatus)
        directories = [directory]

        for name, (selecName, selecArgs) in self.additionalSelectors.iteritems():
            directory = getSelectorDir(name).mkdir(datasetName)
            directory.cd()
            argsNamed = ROOT.TNamed("selectorArgs", str(selectorArgs))
            argsNamed.Write()
            selectorArgs = getSelectorArgs(name, selecArgs)
            selector.addSelector(name, getattr(ROOT, selecName)(*selectorArgs), directory)
            directories.append(directory)

        print "Processing dataset", datasetName
        
        # Setup cache
        useCache = True
        if useCache:
            tree.SetCacheSize(1024*1024) # 10 MB
            tree.SetCacheLearnEntries(100);

        readBytesStart = ROOT.TFile.GetFileBytesRead()
        readCallsStart = ROOT.TFile.GetFileReadCalls()
        timeStart = time.time()
        clockStart = time.clock()
        if useMaxEvents:
            if useCache:
                tree.SetCacheEntryRange(0, N)
            tree.Process(selector, "", N)
        else:
            tree.Process(selector)
        timeStop = time.time()
        clockStop = time.clock()
        readCallsStop = ROOT.TFile.GetFileReadCalls()
        readBytesStop = ROOT.TFile.GetFileBytesRead()
        cpuTime = clockStop-clockStart
        realTime = timeStop-timeStart
        readMbytes = float(readBytesStop-readBytesStart)/1024/1024
        print "Real time %.2f, CPU time %.2f (%.1f %%), read %.2f MB (%d calls), read speed %.2f MB/s" % (realTime, cpuTime, cpuTime/realTime*100, readMbytes, readCallsStop-readCallsStart, readMbytes/realTime)
        for d in directories:
            d.Write()

    ## Get a histogram from the cache file
    #
    # \param Datase        Dataset object for which histogram is to be obtained
    # \param histoName     Histogram name
    # \param selectorName  Selector name
    def getRootHisto(self, dataset, histoName, selectorName):
        if self.cacheFile == None:
            if not os.path.exists(self.cacheFileName):
                raise Exception("Assert: for some reason the cache file %s does not exist yet. Did you set 'process=True' in the constructor of NtupleCache?" % self.cacheFileName)
            self.cacheFile = ROOT.TFile.Open(self.cacheFileName)

        if selectorName is None:
            selectorName = "mainSelector"

        path = "%s/%s/%s/%s" % (hashlib.sha1(dataset.getBaseDirectory()).hexdigest(), selectorName, dataset.getName(), histoName)
        h = self.cacheFile.Get(path)
        if not h:
            raise Exception("Histogram '%s' not found from %s" % (path, self.cacheFile.GetName()))
        return h

    ## Create NtupleCacheDrawer for Dataset.getDatasetRootHisto()
    #
    # \param histoName   Histogram name to obtain
    # \param selectorName  Name of selector from which to read the histogram (None for the main selector)
    def histogram(self, histoName, selectorName=None):
        return NtupleCacheDrawer(self, histoName, selectorName)


class SelectorArgs:
    def __init__(self, optionsDefaultValues, **kwargs):
        self.optionsDefaultValues = optionsDefaultValues

        args = {}
        args.update(kwargs)
        for option, defaultValue in self.optionsDefaultValues:
            value = None
            if option in args:
                value = args[option]
                del args[option]
            setattr(self, option, value)

        # Any remaining argument is an error
        if len(args) >= 1:
            raise Exception("Incorrect arguments for SelectorArgs.__init__(): %s" % ", ".join(args.keys()))

    def clone(self, **kwargs):
        c = copy.deepcopy(self)
        c.set(**kwargs)
        return c

    def set(self, **kwargs):
        for key, value in kwargs.iteritems():
            if not hasattr(self, key):
                raise Exception("This SelectorArgs does not have property %s" % key)
            setattr(self, key, value)

    def update(self, selectorArgs):
        for a, dv in self.optionsDefaultValues:
            val = getattr(selectorArgs, a)
            if val is not None:
                setattr(self, a, val)

    def createArgs(self):
        args = []
        for option, defaultValue in self.optionsDefaultValues:
            value = getattr(self, option)
            if value is None:
                value = defaultValue
            args.append(value)
        return args

## added from H2HW aux
def Clone(obj, *args):
    cl = obj.Clone(*args)
    ROOT.SetOwnership(cl, True)
    if hasattr(cl, "SetDirectory"):
        cl.SetDirectory(0)
    return cl

