# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (June 2020)
import re
from TauFW.common.tools.utils import isnumber, islist, ensurelist, unwraplistargs
from TauFW.common.tools.file import ensuredir, ensureTFile
from TauFW.common.tools.log import Logger, color
from TauFW.Plotter.plot.Variable import Variable, ensurevar
import TauFW.Plotter.plot.CMSStyle as CMSStyle
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gDirectory, gROOT, TH1, THStack, kDotted, kBlack, kWhite
gROOT.SetBatch(True)
LOG = Logger('Sample')
xsecsNLO = {
  'DYJetsToLL_M-50':     3*2025.74,
  'DYJetsToLL_M-10to50':  18610.0,
  'WJetsToLL':            61526.7,
}

def unwrap_MergedSamples_args(*args,**kwargs):
  """Help function to unwrap arguments for MergedSamples."""
  strings = [ ]
  name    = "noname"
  title   = "No title"
  samples = [ ]
  #args    = unwraplistargs(args)
  for arg in args:
    if isinstance(arg,str):
      strings.append(arg)
    elif isinstance(arg,Sample):
      samples.append(arg)
    elif islist(arg) and all(isinstance(s,Sample) for s in arg):
      for sample in arg:
        samples.append(sample)
  if len(strings)==1:
    name, title = strings[0], strings[0]
  elif len(strings)>1:
    name, title = strings[:2]
  elif len(samples)>1:
    name, title = '-'.join([s.name for s in samples]), ', '.join([s.title for s in samples])
  LOG.verb("unwrap_MergedSamples_args: name=%r, title=%r, samples=%s"%(name,title,samples),level=3)
  return name, title, samples
  

def unwrap_gethist_args(*args,**kwargs):
  """Help function to unwrap argument list that contain variable(s) and selection:
     - variable, cuts
     - varlist, cuts
     where variable can be
     - xvar, nxbins, xmin, xmax (str, int, float, float)
     - xvar, xbins (str, list)
     - var (Variable)
     or valist is a list of such variables.
  """
  vars   = None  # list of Variable objects
  sel    = None  # selection (string)
  single = False # only one Variable passed
  if len(args)==2:
    vars   = args[0]
    sel    = args[1]
    if isinstance(vars,Variable):
      vars   = [vars]
      single = True
    elif islist(args[0]):
      vars = [ensurevar(v) for v in args[0]]
  elif len(args) in [3,5]:
    vars   = [Variable(*args[len(args)-1])]
    sel    = args[-1]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  LOG.verb("unwrap_gethist_args: vars=%s, sel=%r, single=%r"%(vars,sel,single),level=3)
  return vars, sel, single
  

def unwrap_gethist_args_2D(*args,**kwargs):
  """Help function to unwrap argument list that contain variable(s) and selection:
     - xvar, yvar, cuts
     - xvarlist, yvarlist, cuts
     - (xvar,yvar), cuts
     - varlist, cuts
     - xvar, nxbins, xmin, xmax, yvar, nybins, ymin, ymax, cuts
     where xvar and yvar are Variable objects or arguments, and [xy]varlist is a list of such pairs.
  """
  vars   = None  # list of Variable objects
  sel    = None  # selection (string)
  single = False # only one pair of Variable objects passed
  if len(args)==2:
    vars, sel = args
    single = len(vars)==2 and islist(vars) and isinstance(vars[0],Variable) and isinstance(vars[1],Variable)
    if single:
      vars = [vars]
  elif len(args)==3:
    xvars, yvars, sel = args
    if isinstance(xvars,Variable) and isinstance(yvars,Variable):
      vars = [(xvars,yvars)]
      single = True
    elif all(isinstance(v,Variable) for v in xvars+yvars):
      vars = zip(xvars,yvars)
    elif len(xvars) in [3,5] and len(yvars) in [3,5]:
      vars = [Variable(*xvars),Variable(*yvars)]
      single = True
  elif len(args)==9:
    vars   = [Variable(*args[0:4]),Variable(*args[4:8])]
    sel    = args[-1]
    single = True
  if vars==None or sel==None:
    LOG.throw(IOError,'unwrap_gethist_args_2D: Could not unwrap arguments %s, len(args)=%d, vars=%s, sel=%s.'%(args,len(args),vars,sel))
  LOG.verb("unwrap_gethist_args_2D: vars=%s, sel=%r, single=%r"%(vars,sel,single),level=3)
  return vars, sel, single
  

#def join(sampleList,*searchterms,**kwargs):
#  """Merge samples from a sample list, that match a set of search terms."""
#  from Sample import MergedSample, SampleSet
#  
#  verbosity = LOG.getverbosity(kwargs,1)
#  name0     = kwargs.get('name',  searchterms[0] )
#  title0    = kwargs.get('title', name0          )
#  color0    = kwargs.get('color', None           )
#  LOG.verbose("",verbosity,level=2)
#  LOG.verbose(" merging %s"%(name0),verbosity,level=1)
#  
#  # GET samples containing names and searchterm
#  mergeList = [ s for s in sampleList if s.isPartOf(*searchterms,exclusive=False) ]
#  if len(mergeList) < 2:
#    LOG.warning('Could not merge "%s": less than two "%s" samples (%d)'%(name0,name0,len(mergeList)))
#    return sampleList
#  fill = max([ len(s.name) for s in mergeList ])+2 # number of spaces
#  
#  # ADD samples with name0 and searchterm
#  mergedsample = MergedSample(name0,title0,color=color0)
#  for sample in mergeList:
#    samplename = ('"%s"'%(sample.name)).ljust(fill)
#    LOG.verbose("   merging %s to %s: %s"%(samplename,name0,sample.filenameshort),verbosity,level=2)
#    mergedsample.add(sample)
#  
#  # REMOVE replace merged samples from sampleList, preserving the order
#  if mergedsample.samples and sampleList:
#    if isinstance(sampleList,SampleSet):
#      sampleList.replaceMergedSamples(mergedsample)
#    else:
#      index0 = len(sampleList)
#      for sample in mergedsample.samples:
#        index = sampleList.index(sample)
#        if index<index0: index0 = index
#        sampleList.remove(sample)
#      sampleList.insert(index,mergedsample)
#  return sampleList
  

#def stitch(sampleList,*searchterms,**kwargs):
#  """Stitching samples: merge samples and reweight inclusive
#  sample and rescale jet-binned samples."""
#  verbosity         = LOG.getverbosity(kwargs,1)
#  name0             = kwargs.get('name',      searchterms[0]  )
#  title0            = kwargs.get('title',     ""              )
#  name_incl         = kwargs.get('name_incl', name0           )
#  npartons          = kwargs.get('npartons',  'NUP'           ) # variable name of number of partons
#  LOG.verbose("",verbosity,level=2)
#  LOG.verbose(" stiching %s: rescale, reweight and merge samples"%(name0),verbosity,level=1)
#  
#  # CHECK if sample list of contains to-be-stitched-sample
#  stitchList = sampleList.samples if isinstance(sampleList,SampleSet) else sampleList
#  stitchList = [ s for s in stitchList if s.isPartOf(*searchterms) ]
#  if len(stitchList) < 2:
#    LOG.warning("stitch: Could not stitch %s: less than two %s samples (%d)"%(name0,name0,len(stitchList)))
#    for s in stitchList: print ">>>   %s"%s.name
#    if len(stitchList)==0: return sampleList
#  fill = max([ len(s.name) for s in stitchList ])+2
#  name = kwargs.get('name',stitchList[0].name)
#  
#  # FIND inclusive sample
#  sample_incls = [s for s in stitchList if s.isPartOf(name_incl)]
#  if len(sample_incls)==0: LOG.error('stitch: Could not find inclusive sample "%s"!'%(name0))
#  if len(sample_incls) >1: LOG.error('stitch: Found more than one inclusive sample "%s"!'%(name0))
#  sample_incl = sample_incls[0]
#  
#  # k-factor
#  N_incl         = sample_incl.sumweights
#  weights        = [ ]
#  xsec_incl_LO  = sample_incl.xsec
#  xsec_incl_NLO = crossSectionsNLO(name0,*searchterms)
#  kfactor        = xsec_incl_NLO / xsec_incl_LO
#  norm0          = -1
#  maxNUP         = -1
#  LOG.verbose("   %s k-factor = %.2f = %.2f / %.2f"%(name0,kfactor,xsec_incl_NLO,xsec_incl_LO),verbosity,level=2)
#  
#  # SET renormalization scales with effective luminosity
#  # assume first sample in the list s the inclusive sample
#  for sample in stitchList:
#    N_tot = sample.sumweights
#    N_eff = N_tot
#    xsec = sample.xsec # inclusive or jet-binned cross section
#    if sample.isPartOf(name_incl):
#      NUP = 0
#    else:
#      N_eff = N_tot + N_incl*xsec/xsec_incl_LO # effective luminosity    
#      matches = re.findall("(\d+)Jets",sample.filenameshort)
#      LOG.verbose('   %s: N_eff = N_tot + N_incl * xsec / xsec_incl_LO = %.1f + %.1f * %.2f / %.2f = %.2f'%\
#                     (sample.name,N_tot,N_incl,xsec,xsec_incl_LO,N_eff),verbosity,2)
#      if len(matches)==0: LOG.error('stitch: Could not stitch "%s": could not find right NUP for "%s"!'%(name0,sample.name))
#      if len(matches)>1:  LOG.warning('stitch: More than one "\\d+Jets" match for "%s"! matches = %s'%(sample.name,matches))
#      NUP = int(matches[0])
#    norm = sample.lumi * kfactor * xsec * 1000 / N_eff
#    if NUP==0:     norm0 = norm
#    if NUP>maxNUP: maxNUP = NUP
#    weights.append("(NUP==%i ? %s : 1)"%(NUP,norm))
#    LOG.verbose('   %s, NUP==%d: norm = luminosity * kfactor * xsec * 1000 / N_eff = %.2f * %.2f * %.2f * 1000 / %.2f = %.2f'%\
#                    (name0,NUP,sample.lumi,kfactor,xsec,N_eff,norm),verbosity,2)
#    LOG.verbose("   stitching %s with normalization %7.3f and cross section %8.2f pb"%(sample.name.ljust(fill), norm, xsec),verbosity,2)
#    #print ">>> weight.append(%s)"%weights[-1]
#    sample.norm = norm # apply lumi-cross section normalization
#    if len(stitchList)==1: return sampleList
#  
#  # ADD weights for NUP > maxNUP
#  if norm0>0 and maxNUP>0:
#    weights.append("(NUP>%i ? %s : 1)"%(maxNUP,norm0))
#  else:
#    LOG.warning("   found no weight for NUP==0 (%.1f) or no maximum NUP (%d)..."%(norm0,maxNUP))
#  
#  # SET weight of inclusive sample
#  sample_incl.norm = 1.0 # apply lumi-cross section normalization via weights
#  stitchweights    = '*'.join(weights)
#  if npartons!='NUP':
#    stitchweights  = stitchweights.replace('NUP',npartons)
#  LOG.verbose("   stitch weights = %s"%(stitchweights),verbosity,4)
#  sample_incl.addWeight(stitchweights)
#  if not title0: title0 = sample_incl.title
#  
#  # MERGE
#  join(sampleList,name0,*searchterms,title=title0,verbosity=verbosity)
#  return sampleList
  

#def crossSectionsNLO(*searchterms,**kwargs):
#  """Returns inclusive (N)NLO cross section for stitching og DY and WJ."""
#  # see /shome/ytakahas/work/TauTau/SFrameAnalysis/TauTauResonances/plot/config.py
#  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV#List_of_processes
#  # https://ineuteli.web.cern.ch/ineuteli/crosssections/2017/FEWZ/
#  # DY cross sections  5765.4 [  4954.0, 1012.5,  332.8, 101.8,  54.8 ]
#  # WJ cross sections 61526.7 [ 50380.0, 9644.5, 3144.5, 954.8, 485.6 ]
#  from Sample import Sample
#  isDY          = False
#  isDY_M10to50  = ""
#  isDY_M50      = ""
#  isWJ          = False
#  for searchterm in searchterms:
#    searchterm = searchterm.replace('*','')
#    if "DY" in searchterm:
#      isDY = True
#    if "10to50" in searchterm:
#      isDY_M10to50 = "M-10to50"
#    if "50" in searchterm and not "10" in searchterm:
#      isDY_M50 = "M-50"
#    if "WJ" in searchterm:
#      isWJ = True
#  if isDY and isWJ:
#    LOG.error("crossSections - Detected both isDY and isWJ!")
#    exit(1)
#  elif isWJ:
#    return xsecsNLO['WJ']
#  elif isDY:
#    if isDY_M10to50 and isDY_M50:
#      LOG.error('crossSections - Matched to both "M-10to50" and "M-50"!')
#      exit(1)
#    if not (isDY_M10to50 or isDY_M50):
#      LOG.error('crossSections - Did not match to either "M-10to50" or "M-50" for DY!')
#      exit(1)
#    return xsecsNLO['DY'][isDY_M10to50+isDY_M50]
#  else:
#    LOG.error("crossSections - Did not find a DY or WJ match!")
#    exit(1)
  

from TauFW.Plotter.sample.Sample import *
from TauFW.Plotter.sample.MergedSample import MergedSample
from TauFW.Plotter.sample.SampleSet import SampleSet
import TauFW.Plotter.sample.SampleStyle as STYLE
